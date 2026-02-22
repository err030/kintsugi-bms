import argparse
import os
import re
import serial
import subprocess

from datetime import datetime

NUM_ITERATIONS=100
HOTPATCH_SIZES_RAPIDPATCH = sorted(list({56, 48, 260, 68, 48, 232, 188, 56+68, 52, 48, 48, 156, 131}))
HOTPATCH_SIZES_AUTOPATCH = sorted(list({528, 504, 392, 400, 780, 400, 400, 548, 468+476, 516, 380, 476, 560}))

FRAMEWORKS = [ "RapidPatch", "AutoPatch" ]

def get_framework_sizes(framework : str):
    if framework == "RapidPatch":
        return HOTPATCH_SIZES_RAPIDPATCH
    elif framework == "AutoPatch":
        return HOTPATCH_SIZES_AUTOPATCH
    return []

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


def main():
    parser = argparse.ArgumentParser("Kintsugi Resource Utilization Experiments")
    parser.add_argument("--out-dir", required=True, type=str, help="Path to the output directory.")
    parser.add_argument("--framework", required=True, type=str, help="Framework to indicate hoptatch sizes (RapidPatch|AutoPatch|RPAP|All)")
    parser.add_argument("--count", required=False, type=int, default=64, help="Maximum hotpatch slot count.")
    parser.add_argument("--steps", required=False, type=int, default=4, help="Number of steps between measurements.")

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

        print(framework)
        print("-" * len(framework))

        for hotpatch_size in hotpatch_sizes:
            print("Hotpatch Size:", hotpatch_size)
            
            for hotpatch_count in count_range:
                print("Slot Count:", hotpatch_count)

                make = f"make FRAMEWORK=1 CODE_SIZE={hotpatch_size} NUM_ITERATIONS={NUM_ITERATIONS} NUM_HOTPATCHES={hotpatch_count}"
                command = f"make clean && {make}"

                print(f"Building with command {make}")
                output, returncode = run_command(command)

                try:
                    ser = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=500)
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                except serial.SerialException as e:
                    print(f"Failed to open serial port: {e}")
                    return

                # Check for errors in the command output
                if returncode != 0 or 'error' in output.lower():
                    print(f"Error found: {output}")
                    continue

                print(f"Flashing application") 
                flash_output, flash_returncode = run_command("make flash")
                if flash_returncode != 0 or 'error' in flash_output.lower():
                    print(f"Error during flashing: {flash_output}")
                    break
                
                # Read from UART and store output into a file
                filename = f"{directory_name}/{framework}_s{hotpatch_size}_c{hotpatch_count}.txt"
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

                    with open(filename, 'w') as f:
                        for line in measurement:
                            f.write(f"{line}\n")

                except Exception as e:
                    print(f"Failed to read from UART or write to file: {e}")

                # Close serial port
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
