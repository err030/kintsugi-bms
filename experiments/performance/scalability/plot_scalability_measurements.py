import argparse
import os
import re

import numpy as np
import matplotlib.pyplot as plt

HOTPATCH_SIZES_RAPIDPATCH = sorted(list({56, 48, 260, 68, 48, 232, 188, 56+68, 52, 48, 48, 156}))
HOTPATCH_SIZES_AUTOPATCH = sorted(list({528, 504, 392, 400, 780, 400, 400, 548, 468+476, 516, 380, 476, 560}))

FRAMEWORKS = [ "RapidPatch", "AutoPatch" ]


def parse_filename(filename, framework):
    pattern = rf"{framework}_s(\d+)_c(\d+)\.txt"
    match = re.match(pattern, filename)
    if not match:
        return None, None
    return (int(match.group(1)), int(match.group(2)))

def read_cycle_counts(filename):
    result = list()
    try:
        with open(filename, "r") as f:
            pattern = "(\d+)"

            for line in f.readlines():
                match = re.match(pattern, line.strip())

                if not match:
                    print(f"[error]: parsing cycle count from '{filename}'")
                    return None

                cycle_count = int(match.group(1))

                result.append(cycle_count)

            return np.array(result)
    except Exception as e:
        print(f"[error]: reading cycle count from '{filename}': {e}")
        return None, None

def main():
    parser = argparse.ArgumentParser("Kintsugi Scalability Experiments")
    parser.add_argument("--dir", required=True, type=str, help="Path to the measurement directory.")
    parser.add_argument("--out", required=True, type=str, help="Output file for the results.")
    parser.add_argument("--framework", required=True, type=str, help="Framework to indicate hoptatch sizes (RapidPatch|AutoPatch|All)")
    parser.add_argument("--count", required=False, type=int, default=64, help="Maximum hotpatch slot count.")
    parser.add_argument("--steps", required=False, type=int, default=4, help="Number of steps between measurements.")

    args = parser.parse_args()

    # parse the framework to measure
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

    hotpatch_sizes = set()
    hotpatch_counts = set()
    meas_dict = dict()

    for framework in frameworks:

        for filename in os.listdir(directory):
            hotpatch_size, hotpatch_count = parse_filename(filename, framework)

            if hotpatch_size == None and hotpatch_count == None:
                continue

            hotpatch_sizes.add(hotpatch_size)
            hotpatch_counts.add(hotpatch_count)

            cycle_counts = list()
            with open(os.path.join(directory, filename), "r") as f:
                for line in f.readlines():
                    match = re.match("(\d+)", line.strip())

                    if not match:
                        print(f"[error]: parsing cycle count from {filename}")
                        return

                    cycles = int(match.group(1))

                    cycle_counts.append(cycles)

            meas_dict[(hotpatch_count, hotpatch_size)] = int(np.average(cycle_counts))

    hotpatch_sizes = sorted(list(hotpatch_sizes))
    hotpatch_counts = sorted(list(hotpatch_counts))

    meas_list = [ (key, value / (64 * 1e3)) for key, value in meas_dict.items() ]

    meas_slot = dict()
    for key, value in meas_dict.items():
        slot = key[0]
        if slot not in meas_slot:
            meas_slot[slot] = list()

        meas_slot[slot].append(value)

    meas_slot_list = [ (slot, np.average(values) / (64 * 1e3)) for slot, values in meas_slot.items()]
    meas_slot_list = sorted(meas_slot_list, key = lambda x : x[0])

    min_meas = min(meas_list, key = lambda x: x[1])
    max_meas = max(meas_list, key = lambda x: x[1])

    # plot the heatmap
    X, Y = np.meshgrid(hotpatch_counts, hotpatch_sizes)
    Z = np.zeros_like(X, dtype=float)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            count = X[i, j]
            size = Y[i, j]
            Z[i, j] = meas_dict[(count, size)]

    Z = Z / (64 * 1e3)

    fs = 14
    plt.rcParams.update({
        "font.size" : fs,
        "axes.labelsize": fs,    # Axis labels
        "xtick.labelsize": fs,   # Tick labels
        "ytick.labelsize": fs,
        "legend.fontsize": fs
    })

    _, ax1 = plt.subplots(figsize=(6, 3))

    heatmap = plt.imshow(
        Z,
        origin='lower',
        aspect='auto',
        extent=[
            hotpatch_counts[0], hotpatch_counts[-1],
            hotpatch_sizes[0], hotpatch_sizes[-1]
        ],
        vmin=int(np.floor(min_meas[1])),
        vmax=int(np.ceil(max_meas[1])),
        cmap='viridis'
    )
    cbar = plt.colorbar(heatmap, pad = 0.25)
    cbar.set_label("Execution Time\n(Milliseconds)")


    ax1.set_xlabel('Hotpatch Count')
    ax1.set_ylabel('Hotpatch Size\n(Bytes)')

    # plot the line
    plt.rcParams.update({
        "font.size" : fs,
        "axes.labelsize": fs,    # Axis labels
        "xtick.labelsize": fs,   # Tick labels
        "ytick.labelsize": fs,
        "legend.fontsize": fs
    })
    ax2 = ax1.twinx()
    y_values = []
    for i in range(len(hotpatch_counts) - 1):
        j = i + 1
        i_meas = np.average([ meas_dict[(hotpatch_counts[i], size)] for size in hotpatch_sizes])
        j_meas = np.average([ meas_dict[(hotpatch_counts[j], size)] for size in hotpatch_sizes])
        y_values.append(((j_meas - i_meas) / i_meas))

    y_values = []
    for count in hotpatch_counts:
        avg_time = np.average([meas_dict[(count, size)] for size in hotpatch_sizes])
        y_values.append(avg_time / count)

    y_values = np.array(y_values)
    y_values = y_values / (64*1e3)
    y_values = [ v for _, v in meas_slot_list]

    ax2.plot(hotpatch_counts, y_values, color="black", linewidth = "1", marker="o", label="increase")
    ax2.set_ylabel("Avg. Time per Count\n(Milliseconds)")

    y_min = min(y_values)
    y_max = max(y_values)

    # Add some padding to top and bottom
    padding = 0
    ax2.set_ylim(y_min - padding, y_max + padding)

    #plt.xticks(hotpatch_counts)
    plt.xticks([ 1 ] + list(range(0, max(hotpatch_counts) + 1, 8))[1:])
    plt.tight_layout()
    plt.margins(0,0)
    plt.savefig(args.out, bbox_inches='tight', pad_inches=0)
    #plt.show()


if __name__ == "__main__":
    main()
