import argparse
import os
import re
import numpy as np

from tabulate import tabulate

def parse_filename(filename):
    pattern = r"context_switch_measurement_e(\d)_tp(\d)_tn(\d)_s(\d).txt"
    match = re.match(pattern, filename)
    if not match:
        return None
    return {
        "framework_enabled": int(match.group(1)),
        "task_previous_manager": int(match.group(3)),
        "task_next_manager": int(match.group(2)),
        "hotpatch_scheduled": int(match.group(4))
    }

def read_cycle_counts(filename):
    try:
        with open(filename, "r") as file:
            return np.array([int(line.strip()) for line in file.readlines()])
    except Exception as e:
        print(f"[error]: reading cycle count from '{filename}': {e}")
        return None

def cycles_to_microseconds(cycle_counts, frequency_mhz):
    return cycle_counts / (frequency_mhz)

def main():
    parser = argparse.ArgumentParser("Kintsugi Context-Switch Experiments")
    parser.add_argument("--dir", required=True, type=str, help="Directory where the measurements are stored in.")
    parser.add_argument("--out", required=True, type=str, help="Output file for the results.")

    args = parser.parse_args()
    directory = args.dir

    filenames = [f for f in os.listdir(directory) if f.endswith('.txt')]
    all_data = []

    for filename in filenames:
        filepath = os.path.join(directory, filename)

        # get the parameter from the filename
        params = parse_filename(filename)
        if not params:
            print(f"Skipping file with invalid format: {filename}")
            continue

        # read in the measurement data
        cycle_counts = read_cycle_counts(filepath)
        if cycle_counts is not None:
            all_data.append({
                "params": params,
                "cycle_counts": cycle_counts
            })

    # organize data for analysis
    data_dict = {}
    for data in all_data:
        key = (
            data['params']['task_previous_manager'],
            data['params']['task_next_manager'],
            data['params']['hotpatch_scheduled'],
            data['params']['framework_enabled']
        )
        if key not in data_dict:
            data_dict[key] = []
        data_dict[key].extend(data['cycle_counts'])

    # Subtract e=0 data from e=1 data
    results = {}
    for key, counts in data_dict.items():
        tp, tn, hs, e = key
        mean_value = int(np.average(counts))
        base_key = (tp, tn, hs)
        if base_key not in results:
            results[base_key] = {0: None, 1: None}
        results[base_key][e] = mean_value

    # prepare the results
    prepared_results = list()
    for (tp, tn, hs), values in results.items():
        if values[0] is not None and values[1] is not None:
            diff = int(values[1] - values[0])
            prepared_results.append((tp, tn, hs, diff))

    # sort by manager previous, manager next and hotpath scheduled
    prepared_results = sorted(prepared_results, key = lambda x: (x[2], x[1], x[0]))

    # prepare the results for the guard
    headers = [ "Component", "Manager Previous" , "Manager Next", "Hotpatch Scheduled", "Cycle Count", "Time (us)" ]
    table_entries = []
    for (tp, tn, hs, cycles) in prepared_results:
        table_entries.append([ "Guard", tp, tn, hs, cycles, f"{cycles_to_microseconds(cycles, 64):.2f}" ])

    # extraploate the results for the applicator
    applicator_cycles = (results[(0, 1, 1)][1] - results[(0, 1, 1)][0]) - (results[(0, 1, 0)][1] - results[(0, 1, 0)][0])
    table_entries.append(["Applicator", 0, 1, 1, applicator_cycles, f"{cycles_to_microseconds(applicator_cycles, 64):.2f}"])

    measurement_table = tabulate(table_entries, headers=headers, tablefmt="grid")
    
    with open(args.out, "w") as f:
        f.write(measurement_table)

    print(measurement_table)

if __name__ == "__main__":
    main()
