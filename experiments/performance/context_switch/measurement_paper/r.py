import os
import re

# Define the directory and the new prefix
directory = '.'  # current directory; change as needed
new_prefix = 'context_switch_measurement'  # change to whatever prefix you want

# Regular expression to match the pattern "_s<number>.txt"
pattern = re.compile(r'^.*_e(\d+)_tn(\d+)_tp(\d+)_s(\d+)\.txt$')

# Iterate over files in the directory
for filename in os.listdir(directory):
    match = pattern.match(filename)
    if match:
        old_path = os.path.join(directory, filename)
        new_filename = new_prefix + f"_e{match.group(1)}_tp{match.group(3)}_tn{match.group(2)}_s{match.group(4)}.txt"
        new_path = os.path.join(directory, new_filename)
        os.rename(old_path, new_path)
        print(f'Renamed: {filename} -> {new_filename}')
