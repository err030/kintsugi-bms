import os
import re

# Define the directory and the new prefix
directory = '/home/bolter/projects/hotpatching_2025/vm/artifact_clean/experiments/performance/micro_benchmarks/measurement_paper/realworld_cves/15_05_2025_11_01_58_micro_benchmark_measurement_1000_Kintsugi_Manager/'  # current directory; change as needed
new_prefix = 'Kintsugi_Manager'  # change to whatever prefix you want

# Regular expression to match the pattern "_s<number>.txt"
pattern = re.compile(r'^.*_s(\d+)\.txt$')

# Iterate over files in the directory
for filename in os.listdir(directory):
    match = pattern.match(filename)
    if match:
        old_path = os.path.join(directory, filename)
        new_filename = new_prefix + f"_s{match.group(1)}.txt"
        new_path = os.path.join(directory, new_filename)
        os.rename(old_path, new_path)
        print(f'Renamed: {filename} -> {new_filename}')
