#!/bin/bash

CURR_DIR=$(dirname "$0")
PROJ_DIR=/app/resource-utilization
MEAS_DIR=${PROJ_DIR}/measurements
OUT_DIR=${PROJ_DIR}/output

function create_dirs() {
    mkdir -p ${MEAS_DIR}
    mkdir -p ${OUT_DIR}
}

function print_information() {
    echo    "================================================================"
    echo    "  Resource Utilization / Memory Overhead Experiments (C4 - E4)  "
    echo    "================================================================"
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 6.3, Figure 6"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Run the the resource utilization measurements to measure all possible combinations for number of hotpatches and hotpatch sizes"
    echo -e "\t 2) Output the measurements as the heatmap plot shown in Figure 6."
}


function perform_measurement() {
    echo "[info]: performing measurement for resource utilization experiments"

    # perform the measurement
    python3 perform_resource_utilization_measurements.py \
            --out-dir ${MEAS_DIR} \
            --framework All \
            --count 64 \
            --steps 4

    echo "[info]: measurement done!"
}

function output_measurement() {
    echo "[info]: producing output for measurement for resource utilization experiments"

    # output the measurement
    python3 plot_resource_utilization_measurements.py \
            --dir ${MEAS_DIR} \
            --out ${OUT_DIR}/Plot_Section_6_3_Figure_6.pdf \
            --framework All

    echo "[info]: producing output done!"
}

print_information
create_dirs
perform_measurement
output_measurement