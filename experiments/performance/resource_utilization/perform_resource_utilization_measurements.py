import argparse
import os
import pickle
import subprocess

from datetime import datetime

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

ITER_COUNT = 100
NUM_ITERATIONS = ITER_COUNT
HOTPATCH_SIZES_RAPIDPATCH = sorted(list({56, 48, 260, 68, 48, 232, 188, 56+68, 52, 48, 48, 156, 131}))
HOTPATCH_SIZES_AUTOPATCH = sorted(list({528, 504, 392, 400, 780, 400, 400, 548, 468+476, 516, 380, 476, 560, 944}))
FRAMEWORKS = [ "RapidPatch", "AutoPatch" ]

HP_SLOT_COUNT_MAX = 64

def get_framework_sizes(framework : str):
    if framework == "RapidPatch":
        return HOTPATCH_SIZES_RAPIDPATCH
    
    return HOTPATCH_SIZES_AUTOPATCH

def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    return "", result.returncode

def create_directory(directory_path):
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"Directory created: {directory_path}")
        else:
            print(f"Directory already exists: {directory_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_symbol_address(elf, symbol_name):
    for section in elf.iter_sections():
        if isinstance(section, SymbolTableSection):
            for symbol in section.iter_symbols():
                if symbol.name == symbol_name:
                    return symbol.entry['st_value']
    return None

def get_region_size_by_symbols(file_path, start_sym, end_sym):
    try:
        with open(file_path, 'rb') as f:
            elf = ELFFile(f)
            start_addr = get_symbol_address(elf, start_sym)
            end_addr = get_symbol_address(elf, end_sym)

            if start_addr is None or end_addr is None:
                print(f"Could not find symbols: {start_sym}, {end_sym}")
                return None

            return end_addr - start_addr
    except Exception as e:
        print(f"Error reading ELF: {e}")
        return None

def get_section_sizes(file_path, section_names):
    try:
        with open(file_path, 'rb') as f:
            elf = ELFFile(f)

            result = dict()
            for section_name in section_names:
                section = elf.get_section_by_name(section_name)
                if section:
                    result[section_name] = section['sh_size']
                else:
                    print(f"Section '{section_name}' not found.")
                    return None
            
            return result
    except Exception as e:
        print(f"Error while reading ELF file: {e}")
        return None
    
def get_symbol_values(file_path, symbol_names):
    sizes = dict()
    with open(file_path, 'rb') as f:
        elf = ELFFile(f)
        for symbol_name in symbol_names:
            for section in elf.iter_sections():
                if isinstance(section, SymbolTableSection):
                    for symbol in section.iter_symbols():
                        if symbol.name == symbol_name:
                            sizes[symbol_name] = symbol.entry["st_value"]
    return sizes

def perform_measurement(hp_slot_count, max_code_size, framework_enabled = 1):
    make = f"make clean && make FRAMEWORK={framework_enabled} SLOT_COUNT={hp_slot_count} MAX_CODE_SIZE={max_code_size}"
    command = f"{make}"
    print(f"Building with command {make}")
    output, returncode = run_command("rm -rf ./build")
    output, returncode = run_command(command)

    # Check for errors in the command output
    if 'error' in output.lower():
        print(f"Error found ({returncode}): {output}")
        return None
    
    symbols = [ "__hotpatch_slots_quarantine_size", "__hotpatch_context_size", "__hotpatch_code_size"]

    section_sizes = get_symbol_values("build/nrf52840_xxaa.out", symbols)
    file_size = os.path.getsize("build/nrf52840_xxaa.out")

    return ((hp_slot_count, max_code_size), section_sizes, file_size) 

def main():
    parser = argparse.ArgumentParser("Kintsugi Resource Utilization Experiments")
    parser.add_argument("--out-dir", required=True, type=str, help="Path to the output directory.")
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
    directory_name = args.out_dir

    if steps > slot_count:
        print("[error]: steps cannot be as big as slot count.")
        return 
    
    count_range = [1] +  list(range(0, slot_count + 1, steps))[1:]

    start_time = datetime.now()
    for framework in frameworks:
        create_directory(directory_name)

        hotpatch_sizes = get_framework_sizes(framework)

        results = [ ]

        print(framework)
        print("-" * len(framework))

        for hp_slot_count in count_range:
            if hp_slot_count == 0:
                hp_slot_count = 1

            print("Slot Count:", hp_slot_count)
            for max_code_size in hotpatch_sizes:
                print("Size:", max_code_size)
                result = perform_measurement(hp_slot_count, max_code_size, 1)
                if result is None:
                    print("[error]")
                    return
                
                results.append(result)

        with open(directory_name + f"/{framework}_c{slot_count}_s{steps}.pkl", "wb") as f:
            pickle.dump(results, f)

    end_time = datetime.now()
    elapsed_time = end_time - start_time

    total_seconds = int(elapsed_time.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    print(f"[info]: elapsed time {hours}:{minutes}:{seconds}")

if __name__ == "__main__":
    main()
