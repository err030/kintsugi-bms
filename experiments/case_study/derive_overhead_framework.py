import os
import re
from collections import defaultdict
import numpy as np


MEASUREMENT_FOLDER = "./measurements/"
pattern = r"\[(\d+)\]: \{'stabilizer\.yaw': ([\-\d\.e]+)\, 'hotpatch\.patch\_go': ([\-\d\.e]+)\, 'hotpatch\.tick\_active': ([\-\d\.e]+)\, 'hotpatch.prev\_manager': ([\-\d\.e]+)\, 'hotpatch.context\_switches': ([\-\d\.e]+)\, 'hotpatch.measure\_time': ([\-\d\.e]+)\}"

def load_measurements(prefix : str):
    measurements = dict()

    for i in range(10):
        folder = MEASUREMENT_FOLDER + f"measurement_{prefix}_framework_0{i}.txt"

        with open(folder, "r") as f:
            for line in f:
                match = re.match(pattern, line.strip())
                if match:
                    timestamp = int(match.group(1))
                    prev_manager = float(match.group(5))
                    context_switches = float(match.group(6))
                    measure_time = float(match.group(7))

                    if i not in measurements:
                        measurements[i] = list()

                    measurements[i].append((timestamp, prev_manager, context_switches, measure_time))

                else:
                    continue
    return measurements

def compute_average(measurements):
    result = list()
    for idx, m in measurements.items():
        for timestamp, _, context_switches, measure_time in m:
            if timestamp >= 60000:
                result.append(measure_time / context_switches)
                break
    result = np.array(result)
    return np.mean(result), np.var(result)

def compute_probability(measurements):
    result = list()
    result_applicator = list()
    for idx, m in measurements.items():
        for timestamp, prev_manager, context_switches, _ in m:
            if timestamp >= 60000:
                result.append(prev_manager / context_switches)
                result_applicator.append(1 / context_switches)
                break
    result = np.array(result)
    result_applicator = np.array(result_applicator)
    return np.mean(result) * 100, np.var(result), np.mean(result_applicator) * 100, np.var(result_applicator)

def main():
    m_with = load_measurements("with_new")
    m_without = load_measurements("without")

    print(compute_average(m_with))
    print(compute_average(m_without))

    print(compute_probability(m_with))

if __name__ == "__main__":
    main()