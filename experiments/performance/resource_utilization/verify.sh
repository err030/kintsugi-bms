#!/bin/bash
CURR_DIR=$(pwd)

function print_information() {
    echo    "================================================================"
    echo    "  Resource Utilization / Memory Overhead Experiments (C4 - E4)  "
    echo    "================================================================"
    echo    "Verification..."
}

function build_experiment() {

    # build the firmware (the build for this is a dummy command to verify that it is working in general)
    echo "Building Micro-Benchmark - Resource Utilization / Memory Overhead ..."
    make clean > /dev/null 2>&1
    make FRAMEWORK=1 SLOT_COUNT=10 MAX_CODE_SIZE=48 > /dev/null 2>&1

    # verify that the binary exists
    if [ -f "build/nrf52840_xxaa.bin" ]; then
        echo "[Success]: Sucecssfully verified ${EXPERIMENT}"
    else
        echo "[Failure]: Could not verify ${EXPERIMENT} please check!"
    fi

    make clean > /dev/null 2>&1
}

print_information
build_experiment
