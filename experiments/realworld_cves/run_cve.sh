#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 {clear|build|debug|flash} {freertos|zephyr} <cve>"
    exit 1
fi

COMMAND=$1
RTOS=$2
CVE=$3

CURR_DIR=$(dirname "$0")
RTOS_DIR=${CURR_DIR}/${RTOS}

# verify that the directory of the cve exists
if [ ! -d "${RTOS_DIR}/${CVE}" ]; then
    echo "Error: '$CVE' is not a valid cve project to run."
    echo "${RTOS_DIR}/${CVE}"
    exit 1
fi

# execute the RTOS script
case "$RTOS" in
    freertos)
        ${RTOS_DIR}/run_freertos.sh ${COMMAND} ${CVE}
        ;;

    zephyr)
        ${RTOS_DIR}/run_zephyr.sh ${COMMAND} ${CVE}
        ;;

    *)
        echo "[Error]: Unknown RTOS: $RTOS"
        exit 1
        ;;
esac