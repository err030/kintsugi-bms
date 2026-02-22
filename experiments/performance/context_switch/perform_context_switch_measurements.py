import argparse
import os
import re
import serial
import subprocess

from datetime import datetime

ITER_COUNT = 100
NUM_ITERATIONS = ITER_COUNT


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
    parser = argparse.ArgumentParser("Kintsugi Context-Switch Experiments")
    parser.add_argument("--out-dir", required=True, type=str, help="Output directory to store the measurement results in.")
    
    args = parser.parse_args()

    directory = args.out_dir

    create_directory(directory)

    start_time = datetime.now()
    for framework_enabled in [1, 0]:

        p_str = f"Framework Enabled: {framework_enabled}"
        print(p_str)
        print("-" * len(p_str))

        make = f"make FRAMEWORK={framework_enabled} NUM_ITERATIONS={NUM_ITERATIONS}"
        command = f"make clean && {make}"

        # build the firmware binary
        print(f"Building with command {make}")
        output, returncode = run_command(command)

        # Check for errors in the command output
        if 'error' in output.lower():
            print(f"Error found ({returncode}): {output}")
            continue
        

        # establish a connection to the serial output
        try:
            ser = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=50)
        except serial.SerialException as e:
            print(f"Failed to open serial port: {e}")
            return

        # flash the application onto the board
        print(f"Flashing application") 
        flash_output, flash_returncode = run_command("make flash")
        if flash_returncode != 0 or 'error' in flash_output.lower():
            print(f"Error during flashing: {flash_output}")
            break
        
        # previous task has been manager
        for task_prev in [0, 1]:
            # next task will be manager
            for task_next in [0, 1]:     

                # this is a special case that can never occur
                if task_prev == 1 and task_next == 1:
                    continue

                # hotpatch is scheduled   
                for scheduled in [0, 1]:    
                    # Read from UART and store output into a file
                    filename = f"{directory}/context_switch_measurement_e{framework_enabled}_tp{task_next}_tn{task_prev}_s{scheduled}.txt"
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
