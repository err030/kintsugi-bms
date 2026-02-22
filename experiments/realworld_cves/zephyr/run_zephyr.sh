#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 {clear|build|debug|flash} <cve>"
    exit 1
fi

COMMAND=$1
CVE=$2

CURR_DIR=$(dirname "$0")

# verify that the directory of the cve exists
if [ ! -d "${CURR_DIR}/${CVE}" ]; then
    echo "Error: '${CVE}' is not a valid cve project to run."
    exit 1
fi

# get the zephyr directory relative from the script's execution point
ZEPHYR_DIR=${CURR_DIR}/../../../external/rtos/zephyr/zephyrproject

# get the cve path relative from the zephyr directory
CVE_DIR=../../../../experiments/realworld_cves/zephyr/${CVE}

# change directory to zephyr
cd ${ZEPHYR_DIR}

# activate the zephyr venv
source .venv/bin/activate

clear() {
    rm -rf ${CVE_DIR}/build
}

build() {
    # build the firmware
    west build -p -b nrf52840dk_nrf52840 ${CVE_DIR} --build-dir ${CVE_DIR}/build
}

flash() {
    # flash the firmware onto the board
    west flash --recover --build-dir ${CVE_DIR}/build
}

debug() {
    # flash the firmware onto the board
    west debug --build-dir ${CURR_DIR}/build
}

case "$COMMAND" in
    clear)
        echo "Clearing: $NAME"
        clear
        ;;
    build)
        echo "Building: $NAME"
        build
        ;;
    flash)
        echo "Flashing: $CVE"
        flash
        ;;
    debug)
        echo "Debugging $CVE"
        debug
        ;;
    *)
        echo "[Error]: Unknown command: $COMMAND"
        exit 1
        ;;
esac

