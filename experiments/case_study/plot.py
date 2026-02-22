import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import re

# File path
file_path = "/app/case-study/measurements.txt"

# Initialize lists for timestamps and yaw values
timestamps = []
yaw_values = []
patch_stamps = []
tick_values = []

# Define a regex pattern to extract the timestamp, yaw value, and patch values
pattern = r"\[(\d+)\]: \{'stabilizer\.yaw': ([\-\d\.e]+)\, 'hotpatch\.patch\_go': ([\-\d\.e]+)\, 'hotpatch\.tick\_active': ([\-\d\.e]+)\, 'hotpatch.prev\_manager': ([\-\d\.e]+)\, 'hotpatch.context\_switches': ([\-\d\.e]+)\, 'hotpatch.measure\_time': ([\-\d\.e]+)\}"

# Read and parse the file
with open(file_path, "r") as file:
    for line in file:
        match = re.match(pattern, line.strip())
        if match:
            timestamp = int(match.group(1)) 
            yaw = float(match.group(2))
            patch_go = float(match.group(3))
            tick_value = float(match.group(4))
            timestamps.append(timestamp)
            yaw_values.append(yaw)
            patch_stamps.append(patch_go)
            tick_values.append(tick_value)
        else:
            print(f"Skipping malformed line: {line.strip()}")

# Check if data was successfully parsed
if not timestamps or not yaw_values:
    print("No valid data found in the file.")
else:
    # Convert to numpy arrays for easier processing
    timestamps = np.array(timestamps)
    yaw_values = np.array(yaw_values)
    patch_values = np.array(patch_stamps)
    tick_values = np.abs(np.array(tick_values))

    # Ignore the first part as calibration
    calibration_cutoff = np.where(yaw_values != 0)[0][0]  
    timestamps = timestamps[calibration_cutoff:]
    yaw_values = yaw_values[calibration_cutoff:]
    patch_values = patch_values[calibration_cutoff:]
    tick_values = tick_values[calibration_cutoff:]


    # Convert timestamps to seconds relative to the start
    timestamps = (timestamps - timestamps[0]) / 1000.0

    # Create the plot
    plt.figure(figsize=(6, 2))

    # Identify continuous sections of zeros
    zero_sections = np.where(tick_values == 0.0)[0]
    if len(zero_sections) > 0:
        zero_ranges = []
        start = zero_sections[0]
        for i in range(1, len(zero_sections)):
            if zero_sections[i] != zero_sections[i - 1] + 1:
                zero_ranges.append((timestamps[start], timestamps[zero_sections[i - 1]]))
                start = zero_sections[i]
        zero_ranges.append((timestamps[start], timestamps[zero_sections[-1]]))

        # Add shaded red regions for continuous zero sections
        for start, end in zero_ranges:
            plt.axvspan(start, end, color='lightgray')#, alpha=0.5)

    # Identify sections where patch_values are 1
    patch_indices = np.where(patch_values == 1)[0]
    if len(patch_indices) > 0:
        patch_ranges = []
        start = patch_indices[0]
        for i in range(1, len(patch_indices)):
            if patch_indices[i] != patch_indices[i - 1] + 1:
                patch_ranges.append((timestamps[start], timestamps[patch_indices[i - 1]]))
                start = patch_indices[i]
        patch_ranges.append((timestamps[start], timestamps[patch_indices[-1]]))

        start, end = patch_ranges[0]
        # Add shaded red region for non-patch section
        plt.axvspan(0, start, color='#AA4499', alpha = 0.3)
        # Add shaded green region for patch section
        plt.axvspan(start, end, color='#117733', alpha=0.5)

    # Create custom legend
    red_patch = mpatches.Patch(color='gray', alpha=0.3, label='Vulnerability')
    green_patch = mpatches.Patch(color='orange', alpha=0.3, label='Patch Applied')

    fs = 12

    # Finalize the plot
    plt.xlabel("Time (s)", fontsize=fs)
    plt.ylabel("Yaw Value", fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    #plt.grid(True)
    plt.margins(x=0, y=0)
    plt.tight_layout()
    plt.savefig("/app/case-study/case_study.pdf")
