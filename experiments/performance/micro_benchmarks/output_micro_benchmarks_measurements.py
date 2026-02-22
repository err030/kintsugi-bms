import argparse
import os
import re
import numpy as np

from tabulate import tabulate

ITER_COUNT = 100
NUM_ITERATIONS = ITER_COUNT

HOTPATCH_SIZES_RAPIDPATCH = sorted(list({56, 48, 260, 68, 48, 232, 188, 56+68, 52, 48, 48, 156, 131}))
HOTPATCH_SIZES_RAPIDPATCH_MAIN_BODY = sorted([48, 131, 260])

HOTPATCH_SIZES_AUTOPATCH = sorted(list({528, 504, 392, 400, 780, 400, 400, 548, 468+476, 516, 380, 476, 560}))
HOTPATCH_SIZES_AUTOPATCH_MAIN_BODY = sorted([380, 548, 944])

HOTPATCH_SIZES_KINTSUGI = [ 104, 40, 24, 144, 122, 100, 60, 64, 56, 76 ]
HOTPATCH_SIZES_KINTSUGI_MAIN_BODY = []

HOTPATCH_SIZES_KINTUSIG_CVE_MAPPING = {
    104 : ("CVE-2020-10021"),
    40  : ("CVE-2020-10023"),
    24  : ("CVE-2020-10024"),
    144 : ("CVE-2020-10062"),
    122 : ("CVE-2020-10063"),
    100 : ("CVE-2018-16524"),
    60  : ("CVE-2018-16603"),
    64  : ("CVE-2017-2784"),
    56  : ("CVE-2020-17443"),
    76  : ("CVE-2020-17445")
}

FRAMEWORKS = [ "Kintsugi", "RapidPatch", "AutoPatch" ]
COMPONENTS = [ "Manager", "Validation", "Storing", "Scheduling" ]

# Frequency of the board in MHz
BOARD_FREQUENCY = 64

def get_framework_sizes(framework : str, main_body : bool):
    if framework == "RapidPatch":
        return HOTPATCH_SIZES_RAPIDPATCH_MAIN_BODY if main_body == True else HOTPATCH_SIZES_RAPIDPATCH
    elif framework == "AutoPatch":
        return HOTPATCH_SIZES_AUTOPATCH_MAIN_BODY if main_body == True else HOTPATCH_SIZES_AUTOPATCH
    elif framework == "Kintsugi":
        return HOTPATCH_SIZES_KINTSUGI_MAIN_BODY if main_body == True else HOTPATCH_SIZES_KINTSUGI
    return []

def parse_file(filename : str):
    result = list()
    
    with open(filename, "r") as f:
        result = [ int(x) for x in f.readlines() ]

    return result

def gather_files(directory : str, framework : str, component : str, interval : int):
    dir_identifier = rf"micro_benchmark_measurement_{interval}_{framework}_{component}" 
    file_identifier = f"{framework}_{component}"

    found = False
    for dirname in os.listdir(directory):
        m = re.match(dir_identifier, dirname)
        if m:
            found = True
            break
    
    if found == False:
        print(f"[error]: could not find directory for {framework} with {component} and an interval of {interval}")
        return []

    full_dir = os.path.join(directory, dirname)
    result = dict()
    for filename in os.listdir(full_dir):
        m = re.match(file_identifier + r"_s(\d+)\.txt$", filename)
        if m:
            size = int(m.group(1))
            result[size] = {
                "filename" : filename,
                "measurement" : parse_file(os.path.join(full_dir, filename))
            }

    return result

def cycles_to_microseconds(cycle_counts, frequency_mhz):
    return cycle_counts / frequency_mhz

def main():
    parser = argparse.ArgumentParser("Kintsugi Micro-Benchmark Experiments")
    parser.add_argument("--dir", required=True, type=str, help="Directory where the measurements are stored in.")
    parser.add_argument("--out", required=True, type=str, help="Output file for the results.")
    parser.add_argument("--framework", required=True, type=str, help="Framework to indicate hoptatch sizes (Kintsugi|RapidPatch|AutoPatch|RPAP||All)")
    parser.add_argument("--component", required=True, type=str, help="Component to perform the measurement on (Manager|Validation|Storing|Scheduling)")
    parser.add_argument("--main-body", required=False, action="store_true", help="Use only the sizes presented in the main body.")
    parser.add_argument("--interval", required=False, type=int, default=1000, help="Interval in microseconds for the timer to give the manager a signal.")

    args = parser.parse_args()

    # parse the framework to measure
    frameworks = FRAMEWORKS
    framework = args.framework
    if framework != "All":
        if framework == "RPAP":
            frameworks = [ "RapidPatch", "AutoPatch" ]
        else:
            if framework not in FRAMEWORKS:
                print("[error]: invalid framework name.")
                return
            frameworks = [ framework ]

    # get the measurement type from the component
    components = COMPONENTS
    component = args.component
    if component != "All":
        if component not in COMPONENTS:
            print("[error]: invalid component.")
            return
        components = [ component ]

    interval = args.interval

    table_entries = list()
    for framework in frameworks:
        all_sizes = get_framework_sizes(framework, args.main_body)
        all_measurements = dict()
        for component in components:
            all_measurements[component] = gather_files(args.dir, framework, component, interval)

        for size in all_sizes:
            entry = [ framework, str(size) ]

            if framework == "Kintsugi":
                entry = [ str(HOTPATCH_SIZES_KINTUSIG_CVE_MAPPING[size]) ] + entry

            for component in components:
                item = all_measurements[component][size]
                measurement = item["measurement"]
                cycles = int(np.average(measurement))
                entry_str = f"{cycles} ({cycles_to_microseconds(cycles, BOARD_FREQUENCY):.2f} us)"
                entry.append(entry_str)
            table_entries.append(entry)
        
    header = ["Framework", "Hotpatch Size"] + components

    if framework == "Kintsugi":
        header = ["CVE-ID"] + header
        
    measurement_table = tabulate(table_entries, headers=header, tablefmt="grid")
        
    with open(args.out, "w") as f:
        f.write(measurement_table)

    print(measurement_table)

if __name__ == "__main__":
    main()
