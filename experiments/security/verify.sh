#!/bin/bash
CURR_DIR=$(pwd)

function print_information() {
    echo    "============================================"
    echo    "  Practical Security Experiments (C6 - E6)  "
    echo    "============================================"
    echo    "Verification..."
}

function build_experiment() {
    EXPERIMENT=$1

    cd ${CURR_DIR}/${EXPERIMENT}

    # build the firmware
    echo "Building ${EXPERIMENT}..."
    make clean > /dev/null 2>&1
    make > /dev/null 2>&1

    # verify that the binary exists
    if [ -f "build/nrf52840_xxaa.bin" ]; then
        echo "[Success]: Sucecssfully verified ${EXPERIMENT}"
    else
        echo "[Failure]: Could not verify ${EXPERIMENT} please check!"
    fi

    #make clean > /dev/null 2>&1
}

print_information
build_experiment before_patching
build_experiment during_patching
build_experiment after_patching