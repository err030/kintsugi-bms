#!/bin/bash
CURR_DIR=$(pwd)

PROJ_DIR=${CURR_DIR}/../..
HP_GEN_DIR=${PROJ_DIR}/hotpatch_generator
HP_DIR=${PROJ_DIR}/hotpatches
CRAZYFLIE_DIR=${CURR_DIR}/crazyflie-firmware

function print_information() {
    echo    "========================================="
    echo    "  Case-Study: Crazyflie 2.0 Hotpatching  "
    echo    "========================================="
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 8"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Build the firmware for the crazyflie drone"
    echo -e "\t 2) Generate the corresponding hotpatch"
    echo -e "\t 3) Re-build the firmware with the hotpatch"
    echo -e "\t 4) Flash the firmware onto the crazyflie done"
    echo    ""
    echo    "To actually log the data you might need to run the crazyflie GUI and run the logger script on your own as well as the overhead measurement."
    echo    "Running the GUI is possible through the crazyflie-clients-python"
}

function perform_experiment() {
    
    # copy the code data template if necessary
    if [ ! -f "${CRAZYFLIE_DIR}/src/config/hp_code_data.h" ]; then
        cp ${HP_DIR}/hp_code_data_template.h ${CRAZYFLIE_DIR}/src/config/hp_code_data.h
    fi

    # compile the firmware
    echo "[info]: Compiling Crazyflie firmware"
    cd ${CRAZYFLIE_DIR}
    make PLATFORM=cf2 DEBUG=1
    echo "[info]: done!"

    # generate the hotpatch
    echo "[info]: Generating hotpatch for Crazyflie"
    python3 ${HP_GEN_DIR}/hotpatch_generator.py --project_path ${CRAZYFLIE_DIR} --binary cf2 --cve crazyflie-firmware --out-dir /src/config
    echo "[info]: done!"

    # compile the firmware with the hotpatch
    echo "[info]: Compiling Crazyflie firmware together with the hotpatch"
    cd ${CRAZYFLIE_DIR}
    make PLATFORM=cf2 DEBUG=1
    echo "[info]: done!"

    # flash the firmware onto the device
    echo "[info]: Compiling Crazyflie firmware"
    cd ${CRAZYFLIE_DIR}
    make flash
    echo "[info]: done!"

    # start the headless client
    echo "[info]: Starting headless client"
    cfheadless -u usb://0 &
    echo "[info]: done!"

    # start logging
    echo "[info]: Starting logging of the data"
    python3 logger.py
    echo "[info]: done!"

    # plot the data
    echo "[info]: Plotting the data"
    python3 plot.py
    echo "[info]: done!"
}

print_information
perform_experiment