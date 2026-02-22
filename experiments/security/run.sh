#!/bin/bash
CURR_DIR=$(dirname "$0")
HP_GEN_DIR=${CURR_DIR}/../../../hotpatch_generator

function print_information() {
    echo    "============================================"
    echo    "  Practical Security Experiments (C6 - E6)  "
    echo    "============================================"
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 8"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Compile the corresponding binary with the security measures"
    echo -e "\t 2) Flash the firmware onto the board"
    echo -e "\t 3) Output the results in a UART terminal (manually connect to it using, e.g., screen)"
}

function select_experiment() {
    echo    "[info]: you can choose one of the following security experiments to test:"
    echo -e "\t 1) Before Patching"
    echo -e "\t 2) During Patching"
    echo -e "\t 3) After Patching"
    read -p "Please select an experiment [1-3]:" EXP_IND

    case $EXP_IND in
        1)
            EXPERIMENT=before_patching
            ;;
        2)
            EXPERIMENT=during_patching
            ;;
        3)
            EXPERIMENT=after_patching
            ;;
        *)
            echo "[info]: invalid security experiment! Please run this script again."
            exit 1
            ;;
    esac

    cd ${CURR_DIR}/${EXPERIMENT}
    
    # build the firmware
    echo "Building Firmware..."
    make clean
    make 

    # flash the firmware
    make flash
}

print_information
select_experiment