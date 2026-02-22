#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 {clear|build|debug|flash} <cve>"
    exit 1
fi

COMMAND=$1
CVE=$2

CURR_DIR=$(dirname "$0")
CVE_DIR=${CURR_DIR}/${CVE}

# verify that the directory of the cve exists
if [ ! -d "${CURR_DIR}/${CVE}" ]; then
    echo "Error: '${CVE}' is not a valid cve project to run."
    exit 1
fi

cd ${CVE_DIR}

clear() {
    # clean up everything
    make clean
}

build() {
    # build the firmware
    make
}

flash() {
    # flash the firmware onto the board
    make flash
}

debug() {

    # flash the firmware onto the board
    make flash

    # start a jlink gdb server
    JLinkGDBServer -device nrf52840_xxaa -if swd -port 3333 > /dev/null 2>&1 &

    # start a gdb instance
    arm-none-eabi-gdb ${CVE_DIR}/_build/nrf52840_xxaa.out -ex "target extended-remote :3333" -ex "load"
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
        echo "Unknown command: $COMMAND"
        exit 1
        ;;
esac