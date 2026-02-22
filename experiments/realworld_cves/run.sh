#!/bin/bash
CURR_DIR=$(dirname "$0")

PROJ_DIR=${CURR_DIR}/../..
HP_GEN_DIR=${PROJ_DIR}/hotpatch_generator
HP_DIR=${PROJ_DIR}/hotpatches

function print_information() {
    echo    "========================================"
    echo    "  Real-World CVE Experiments (C5 - E5)  "
    echo    "========================================"
    echo    ""
    echo    "Reproduction of the experimental results from:"
    echo -e "\t Section 6.4"
    echo    ""
    echo    "This script will perform the following tasks:"
    echo -e "\t 1) Build the CVE firmware to be able to generate a hotpatch"
    echo -e "\t 1) Generate a hotpatch for a specified CVE"
    echo -e "\t 2) Build the corresponding firmware image to trigger the CVE including the hotpatch code"
    echo -e "\t 3) Run the CVE on the connected board which outputs the result"
}

function select_cve() {
    echo -e "[info]: you can choose one of the following CVEs to test:"
    echo -e "\t  1) [ZephyrOS ]: CVE-2020-10021"
    echo -e "\t  2) [ZephyrOS ]: CVE-2020-10023"
    echo -e "\t  3) [ZephyrOS ]: CVE-2020-10024"
    echo -e "\t  4) [ZephyrOS ]: CVE-2020-10062"
    echo -e "\t  5) [ZephyrOS ]: CVE-2020-10063"
    echo -e "\t  6) [FreeRTOS ]: CVE-2018-16524"
    echo -e "\t  7) [FreeRTOS ]: CVE-2018-16603"
    echo -e "\t  8) [mbedTLS  ]: CVE-2017-2784"
    echo -e "\t  9) [AMNESIA33]: CVE-2020-17443"
    echo -e "\t 10) [AMNESIA33]: CVE-2020-17445"
    read -p "Please select a CVE [1-10]:" CVE_INDEX

    case $CVE_INDEX in
        1)
            RTOS=zephyr
            CVE=cve_2020_10021
            BINARY=zephyr
            ;;

        2)
            RTOS=zephyr
            CVE=cve_2020_10023
            BINARY=zephyr
            ;;

        3)
            RTOS=zephyr
            CVE=cve_2020_10024
            BINARY=zephyr
            ;;
        
        4)
            RTOS=zephyr
            CVE=cve_2020_10062
            BINARY=zephyr
            ;;

        5)
            RTOS=zephyr
            CVE=cve_2020_10063
            BINARY=zephyr
            ;;

        6)
            RTOS=freertos
            CVE=cve_2018_16524
            BINARY=nrf52840_xxaa
            ;;

        7)
            RTOS=freertos
            CVE=cve_2018_16603
            BINARY=nrf52840_xxaa
            ;;

        8)
            RTOS=freertos
            CVE=cve_2017_2784
            BINARY=nrf52840_xxaa
            ;;

        9)
            RTOS=freertos
            CVE=cve_2020_17443
            BINARY=nrf52840_xxaa
            ;;

        10)
            RTOS=freertos
            CVE=cve_2020_17445
            BINARY=nrf52840_xxaa
            ;;

        *)
            echo "[error]: invalid index, please run this script again."
            exit 1
            ;;
    esac

    # get the dir of the cve
    RTOS_DIR=${CURR_DIR}/${RTOS}
    CVE_DIR=${RTOS_DIR}/${CVE}

    # copy the code data template if necessary
    if [ ! -f "${CVE_DIR}/include/hp_code_data.h" ]; then
        cp ${HP_DIR}/hp_code_data_template.h ${CVE_DIR}/include/hp_code_data.h
    fi

    # clean everything
    echo "[info]: Cleaning CVE firmware"
    bash ${CURR_DIR}/run_cve.sh clear ${RTOS} ${CVE}

    # compile the firmware
    echo "[info]: Compiling CVE firmware"
    bash ${CURR_DIR}/run_cve.sh build ${RTOS} ${CVE}
    echo "[info]: done!"

    # generate the hotpatch
    echo "[info]: Generating hotpatch for ${CVE}"
    python3 ${HP_GEN_DIR}/hotpatch_generator.py --project_path ${RTOS_DIR} --binary ${BINARY} --cve ${CVE}
    echo "[info]: done!"

    # compile the firmware with hotpatch
    touch ${CVE_DIR}/include/hp_code_data.h
    echo "[info]: Compiling CVE firmware"
    bash ${CURR_DIR}/run_cve.sh build ${RTOS} ${CVE}
    echo "[info]: done!"

    # flash the firmware onto the board
    echo "[info]: Flashing firmware onto the board"
    ${CURR_DIR}/run_cve.sh flash ${RTOS} ${CVE}
    echo "[info]: done!"
}

print_information
select_cve