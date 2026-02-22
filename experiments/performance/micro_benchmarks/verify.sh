#!/bin/bash
CURR_DIR=$(pwd)

function print_information() {
    echo    "====================================================="
    echo    "  Micro-Benchmark - Manager - Experiments (C1 - E1)  "
    echo    "====================================================="
    echo    "Verification..."
}

function build_experiment() {

    # build the firmware (the build for this is a dummy command to verify that it is working in general)
    echo "Building Micro-Benchmark - Manager ..."
    make clean > /dev/null 2>&1
    make FRAMEWORK=1 CODE_SIZE=48 NUM_ITERATIONS=100 INTERVAL=1000 M_MANAGER=1 M_S_VALIDATING=0 M_S_STORING=0 M_S_SCHEDULING=0 > /dev/null 2>&1

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
