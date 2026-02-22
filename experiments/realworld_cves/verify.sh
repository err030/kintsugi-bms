#!/bin/bash
CURR_DIR=$(pwd)

function print_information() {
    echo    "========================================"
    echo    "  Real-World CVE Experiments (C5 - E5)  "
    echo    "========================================"
    echo    "Verification..."
}

function build_experiment() {
    RTOS=$1
    CVE=$2
    CVE_DIR=${CURR_DIR}/${RTOS}/${CVE}

    # build the firmware
    echo "Building ${RTOS}/${CVE}..."
    bash ${CURR_DIR}/run_cve.sh clear ${RTOS} ${CVE} > /dev/null 2>&1
    bash ${CURR_DIR}/run_cve.sh build ${RTOS} ${CVE} > /dev/null 2>&1

    # verify that the binary exists
    if [ ${RTOS} = "freertos" ]; then
        if [ -f "${CVE_DIR}/build/nrf52840_xxaa.bin" ]; then
            echo "[Success]: Sucecssfully verified ${RTOS}/${CVE}"
        else
            echo "[Failure]: Could not verify ${RTOS}/${CVE} please check!"
        fi
    elif [ ${RTOS} = "zephyr" ]; then
        if [ -f "${CVE_DIR}/build/zephyr/zephyr.bin" ]; then
            echo "[Success]: Sucecssfully verified ${RTOS}/${CVE}"
        else
            echo "[Failure]: Could not verify ${RTOS}/${CVE} please check!"
        fi
    else
        echo "[Error]: Invalid RTOS"
        exit 1
    fi

    #bash ${CURR_DIR}/run_cve.sh clear ${RTOS} ${CVE} > /dev/null 2>&1
}

print_information

# build freertos
build_experiment freertos cve_2017_2784
build_experiment freertos cve_2018_16524
build_experiment freertos cve_2018_16603
build_experiment freertos cve_2020_17443
build_experiment freertos cve_2020_17445

# build zephyr
build_experiment zephyr cve_2020_10021
build_experiment zephyr cve_2020_10023
build_experiment zephyr cve_2020_10024
build_experiment zephyr cve_2020_10062
build_experiment zephyr cve_2020_10063