#!/bin/bash

CURR_DIR=$(dirname "$0")

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

PROJ_DIR=/app/micro-benchmarks/context-switch-${TIMESTAMP}
MEAS_DIR=${PROJ_DIR}/measurements
OUT_DIR=${PROJ_DIR}/output


function create_dirs() {
    mkdir -p ${MEAS_DIR}
    mkdir -p ${OUT_DIR}
}

function print_information() {
    echo    "============================================================"
    echo    "  Micro-Benchmark - Context Switch - Experiments (C2 - E2)  "
    echo    "============================================================"
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 6.1, 'Guard & Applicator', Table 3"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Run the micro-benchmark measurements for the Guard & Applicator"
    echo -e "\t 2) Output the measurements as a table representing the results from the paper."
}

function perform_measurement() {
    echo "[info]: performing measurement for micro-benchmarks context switch experiments"

    # perform the measurement
    python3 ${CURR_DIR}/perform_context_switch_measurements.py \
            --out-dir ${MEAS_DIR}

    echo "[info]: measurement done!"
}

function output_measurement() {
    echo "[info]: producing output for measurement for micro-benchmarks context switch experiments"

    # output the measurement
    python3 ${CURR_DIR}/output_context_switch_measurements.py \
            --dir ${MEAS_DIR} \
            --out ${OUT_DIR}/Table_Section_6_1_Table_3.txt

    echo "[info]: producing output done!"
}

print_information
create_dirs
perform_measurement
output_measurement