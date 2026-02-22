import argparse
import os
import pickle
import re

import numpy as np
import matplotlib.pyplot as plt

HOTPATCH_SIZES_RAPIDPATCH = sorted(list({56, 48, 260, 68, 48, 232, 188, 56+68, 52, 48, 48, 156, 131}))
HOTPATCH_SIZES_AUTOPATCH = sorted(list({528, 504, 392, 400, 780, 400, 400, 548, 468+476, 516, 380, 476, 560, 944}))
FRAMEWORKS = [ "RapidPatch", "AutoPatch"]
HP_SLOT_COUNT_MAX = 64

def get_framework_sizes(framework : str):
    if framework == "RapidPatch":
        return HOTPATCH_SIZES_RAPIDPATCH

    return HOTPATCH_SIZES_AUTOPATCH

def load_measurement(directory : str, framework : str, slot_count : int, steps : int):
    file_identifier = rf"{framework}_c{slot_count}_s{steps}"

    for filename in os.listdir(directory):
        m = re.match(rf"{file_identifier}.pkl$", filename)

        if m:
            measurements = None
            with open(os.path.join(directory, filename), "rb") as f:
                measurements = pickle.load(f)
            return measurements
    return None

def main():
    parser = argparse.ArgumentParser("Kintsugi Resource Utilization Experiments")
    parser.add_argument("--dir", required=True, type=str, help="Path to the measurement directory.")
    parser.add_argument("--out", required=True, type=str, help="Output file for the results.")
    parser.add_argument("--framework", required=True, type=str, help="Framework to indicate hoptatch sizes (RapidPatch|AutoPatch||All)")
    parser.add_argument("--count", required=False, type=int, default=64, help="Maximum hotpatch slot count.")
    parser.add_argument("--steps", required=False, type=int, default=4, help="Number of steps between measurements.")

    args = parser.parse_args()

    # parse the framework names
    frameworks = FRAMEWORKS
    framework = args.framework
    if framework != "All":
        if framework not in FRAMEWORKS:
            print("[error]: invalid framework name.")
            return
        frameworks = [ framework ]

    slot_count = args.count
    steps = args.steps
    directory = args.dir
    hotpatch_counts = [ 1 ] + list(range(0, slot_count + 1, steps))[1:]

    meas_dict = dict()
    total_sizes = []
    for framework in frameworks:

        measurements = load_measurement(directory, framework, slot_count, steps)
        hotpatch_sizes = get_framework_sizes(framework)

        total_sizes += hotpatch_sizes

        framework_dict = dict()
        for measurement in measurements:
            framework_dict[measurement[0]] = sum([ x for _, x in measurement[1].items() ])

        meas_dict.update(framework_dict)


    resource_measurements = dict()
    for hp_size in total_sizes:
        sorted_measurements = list()
        for hp_count in hotpatch_counts:
            sorted_measurements.append((hp_count, meas_dict[(hp_count, hp_size)]))

        sorted_measurements = sorted(sorted_measurements, key = lambda x : x[0])
        resource_measurements[hp_size] = sorted_measurements

    # Prepare grid data
    X, Y = np.meshgrid(hotpatch_counts, total_sizes)
    Z = np.zeros_like(X, dtype=float)

    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            count = X[i, j]
            size = Y[i, j]
            Z[i, j] = meas_dict[(count, size)]

    fs = 14
    plt.rcParams.update({
        "font.size" : fs,
        "axes.labelsize": fs,
        "xtick.labelsize": fs,
        "ytick.labelsize": fs,
        "legend.fontsize": fs,
        "figure.titlesize": fs
    })
    plt.figure(figsize = (6, 3))

    Z = Z / 1024 # scale to kilo bytes

    contour = plt.imshow(
        Z,
        origin='lower',
        aspect='auto',
        extent=[
            hotpatch_counts[0], hotpatch_counts[-1],
            total_sizes[0], total_sizes[-1]
        ],
        cmap='viridis'
    )
    cbar = plt.colorbar(contour)
    cbar.set_label("Memory Overhead\n(Kilo Bytes)")


    plt.xlabel('Hotpatch Slot Count')
    plt.ylabel('Hotpatch Size\n(Bytes)')
    
    plt.xticks([ 1 ] + list(range(0, max(hotpatch_counts) + 1, 8))[1:])

    plt.tight_layout()
    plt.margins(0,0)
    plt.savefig(args.out, bbox_inches='tight', pad_inches=0)
    #plt.show()

if __name__ == "__main__":
    main()

# 1:04:47