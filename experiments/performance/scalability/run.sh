#!/bin/bash#!/bin/bash

CURR_DIR=$(dirname "$0")

PROJ_DIR=/app/scalability
MEAS_DIR=${PROJ_DIR}/measurements
OUT_DIR=${PROJ_DIR}/output

function create_dirs() {
    mkdir -p ${MEAS_DIR}
    mkdir -p ${OUT_DIR}
}

function print_information() {
    echo    "================================================="
    echo    "  Hotpatching Scalability Experiments (C3 - E3)  "
    echo    "================================================="
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 6.2, Figure 5"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Run the the hotpatch scalability measurement experiments"
    echo -e "\t 2) Output the measurements as the heatmap plot with the linear scaling as shown in Figure 5."
}


function perform_measurement() {
    echo "[info]: performing measurement for hotpatch scalability experiments"

    # perform the measurement
    python3 perform_scalability_measurements.py \
            --out-dir ${MEAS_DIR} \
            --framework All \
            --count 64 \
            --steps 4

    echo "[info]: measurement done!"
}

function output_measurement() {
    echo "[info]: producing output for measurement for micro-benchmarks context switch experiments"

    # output the measurement
    python3 plot_scalability_measurements.py \
            --dir ${MEAS_DIR} \
            --out ${OUT_DIR}/Plot_Section_6_2_Figure_5.pdf \
            --framework All

    echo "[info]: producing output done!"
}

print_information
create_dirs
perform_measurement
output_measurement