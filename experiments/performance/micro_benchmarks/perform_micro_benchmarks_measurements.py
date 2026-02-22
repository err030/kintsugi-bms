import serial
import subprocess
import os
import re
import argparse

import numpy as np

from datetime import datetime

NUM_ITERATIONS = 100

HOTPATCH_SIZES_RAPIDPATCH = sorted(list({56, 48, 260, 68, 48, 232, 188, 56+68, 52, 48, 48, 156, 131}))
HOTPATCH_SIZES_RAPIDPATCH_MAIN_BODY = sorted([48, 131, 260])

HOTPATCH_SIZES_AUTOPATCH = sorted(list({528, 504, 392, 400, 780, 400, 400, 548, 468+476, 516, 380, 476, 560}))
HOTPATCH_SIZES_AUTOPATCH_MAIN_BODY = sorted([380, 548, 944])

HOTPATCH_SIZES_KINTSUGI = sorted(list({104, 40, 24, 144, 122, 100, 60, 64, 56, 76}))
HOTPATCH_SIZES_KINTSUGI_MAIN_BODY = []

FRAMEWORKS = [ "Kintsugi", "RapidPatch", "AutoPatch" ]
COMPONENTS = [ "Manager", "Validation", "Storing", "Scheduling" ]

def get_measurement_string(measurement : str):
    m_manager = 0
    m_s_validating = 0
    m_s_storing = 0
    m_s_scheduling = 0

    if measurement == "Manager":
        m_manager = 1
    elif measurement == "Validation":
        m_s_validating = 1
    elif measurement == "Storing":
        m_s_storing = 1
    elif measurement == "Scheduling":
        m_s_scheduling = 1

    return f"M_MANAGER={m_manager} M_S_VALIDATING={m_s_validating} M_S_STORING={m_s_storing} M_S_SCHEDULING={m_s_scheduling}"

def get_framework_sizes(framework : str, main_body : bool):
    if framework == "RapidPatch":
        return HOTPATCH_SIZES_RAPIDPATCH_MAIN_BODY if main_body == True else HOTPATCH_SIZES_RAPIDPATCH
    elif framework == "AutoPatch":
        return HOTPATCH_SIZES_AUTOPATCH_MAIN_BODY if main_body == True else HOTPATCH_SIZES_AUTOPATCH
    elif framework == "Kintsugi":
        return HOTPATCH_SIZES_KINTSUGI_MAIN_BODY if main_body == True else HOTPATCH_SIZES_KINTSUGI
    return []

def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result.stdout, result.returncode

def create_directory(directory_path):
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"Directory created: {directory_path}")
        else:
            print(f"Directory already exists: {directory_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser("Kintsugi Micro-Benchmark Experiments")
    parser.add_argument("--out-dir", required=True, type=str, help="Output directory for the measurements.")
    parser.add_argument("--framework", required=True, type=str, help="Framework to indicate hoptatch sizes (Kintsugi|RapidPatch|AutoPatch|RPAP|All)")
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
        
    # check if it's main-body only
    mb_str = "_MainBody" if args.main_body == True else ""

    # get the interval
    interval = args.interval

    start_time = datetime.now()
    for framework in frameworks:

        # obtain the hotpatch sizes
        hotpatch_sizes = get_framework_sizes(framework, args.main_body)
        
        for component in components:

            measurement_str = get_measurement_string(component)

            # create the directory
            CURRENT_MEASURE_NAME = f"{framework}_{component}{mb_str}"
            directory_name = f"{args.out_dir}/micro_benchmark_measurement_{interval}_{CURRENT_MEASURE_NAME}"
            create_directory(directory_name)

            # perform the experiment for each of the provided hotpatch sizes
            for code_size in hotpatch_sizes:
                print(f"===[Experiment for {framework} with Hotpatch Size {code_size}]===")

                # building the firmware
                make = f"make FRAMEWORK=1 CODE_SIZE={code_size} NUM_ITERATIONS={NUM_ITERATIONS} INTERVAL={interval} {measurement_str}"
                command = f"make clean && {make}"
                
                print(f"Building with command {make}")
                output, returncode = run_command(command)

                # Check for errors in the command output
                if returncode != 0:
                    print(f"Error found: {output}")
                    continue

                # establish a connection to the serial output
                try:
                    ser = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=5000)
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                except serial.SerialException as e:
                    print(f"Failed to open serial port: {e}")
                    return

                # flash the application onto the board
                print(f"Flashing application") 
                flash_output, flash_returncode = run_command("make flash")
                if flash_returncode != 0 or 'error' in flash_output.lower():
                    print(f"Error during flashing: {flash_output}")
                    break
                
                # read from UART and store output into a file
                filename = f"{directory_name}/{CURRENT_MEASURE_NAME}_s{code_size}.txt"
                print(f"Reading UART output and saving to {filename}")
                try:
                    measurement = list()

                    while True:
                        # read line
                        line_data = ser.readline()
                        if not line_data:
                            print(f"[error]: no data received from UART.")
                            return
                        line = line_data.decode('utf-8').strip()
                        # if we encounter the "done" string, stop the measurement
                        if line == "done":
                            print("done!")
                            break

                        # ensure that the read line is only an integer and nothing else
                        try:
                            pattern = r"(\d+)"
                            match = re.match(pattern, line)
                            if not match:
                                print(line)
                                continue
                        except Exception as e:
                            print("[error]: output is not a number: ", line, line_data)
                            continue

                        # add the line to the measurements
                        measurement.append(line)
                    
                    # write the measurement to the file
                    with open(filename, "w") as f:
                        for line in measurement:
                            f.write(f"{line}\n")

                except Exception as e:
                    print(f"Failed to read from UART or write to file: {e}")

                # close serial port
                ser.close()

    end_time = datetime.now()
    elapsed_time = end_time - start_time

    total_seconds = int(elapsed_time.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    print(f"[info]: elapsed time {hours}:{minutes}:{seconds}")

if __name__ == "__main__":
    main()
