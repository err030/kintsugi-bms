#!/bin/bash

CURR_DIR=$(dirname "$0")

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

PROJ_DIR=/app/micro-benchmarks/manager-${TIMESTAMP}
MEAS_DIR=${PROJ_DIR}/measurements
OUT_DIR=${PROJ_DIR}/output

function create_dirs() {
    mkdir -p ${MEAS_DIR}
    mkdir -p ${OUT_DIR}
}

function print_information() {
    echo    "====================================================="
    echo    "  Micro-Benchmark - Manager - Experiments (C1 - E1)  "
    echo    "====================================================="
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 6.1, 'Manager', Table 2 (main-body version)"
    echo -e "\t Section 6.1, 'Manager', Appendix D, Table 5 (full version)"
    echo -e "\t Section 6.4, Appendix E, Table 6"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Run the micro-benchmark measurements for the Manager for chosen hotpatch sizes"
    echo -e "\t 2) Output the measurements as a table representing the results from the paper."
}


function perform_measurement() {
    echo "[info]: performing measurement with for $1 and storing it to ${MEAS_DIR}."

    # perform the measurement with an interval of 1000ms
    python3 ${CURR_DIR}/perform_micro_benchmarks_measurements.py \
            --out-dir ${MEAS_DIR} \
            --framework $1 \
            --component All \
            --interval 10

    echo "[info]: measurement done!"
}

function output_measurement() {
    echo "[info]: producing output for measurement for $1 and storing it to ${OUT_DIR}/$2."

    # output the measurement
    python3 ${CURR_DIR}/output_micro_benchmarks_measurements.py \
            --dir ${MEAS_DIR} \
            --out ${OUT_DIR}/$2 \
            --framework $1 \
            --component All \
            --interval 10 \
            $3

    echo "[info]: producing output done!"
}

function micro_benchmarking_manager() {
    echo    "[info]: you can choose between the following hotpatch size sources for the measurement:"
    echo -e "\t 1) RapidPatch and AutoPatch"
    echo -e "\t 2) Kintsugi"
    read -p "Please select a variant [1-2]:" FRAMEWORK

    case $FRAMEWORK in
        1)
            FRAMEWORK_NAME="RPAP"
            ;;
        2)
            FRAMEWORK_NAME="Kintsugi"
            ;;
        *)
            echo "[error]: invalid selection, please run this script again."
            exit 1
            ;;
    esac

    perform_measurement $FRAMEWORK_NAME

    case $FRAMEWORK in
        1)
            echo "[info]: Producing output Section 6.1, 'Manager', Table 2"
            output_measurement $FRAMEWORK_NAME "Table_Section_6_1_Table_2.txt" --main-body
            echo "[info]: done!"
            echo "[info]: Producing output Section 6.1, 'Manager', Appendix D, Table 5"
            output_measurement $FRAMEWORK_NAME "Table_Section_6_1_Appendix_D_Table_5.txt"
            ;;
        2)
            echo "[info]: Producing output Section 6.4, Appendix E, Table 6"
            output_measurement $FRAMEWORK_NAME "Table_Section_6_4_Appendix_E_Table_6.txt"
            ;;
        *)  
            echo "[error]: invalid selection, please run this script again."
            exit 1
            ;;
    esac

    echo "[info]: done!"
}

print_information
create_dirs
micro_benchmarking_manager