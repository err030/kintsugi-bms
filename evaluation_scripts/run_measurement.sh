#!/bin/bash

PROJ_DIR=$(dirname "$0")
CONTAINER_NAME="kintsugi-artifact"

# verify that the container exists
bash ${PROJ_DIR}/../build.sh

# make the directory for the measurement files
mkdir -p ${PROJ_DIR}/measurement_results

# run the docker image with the corresponding script
docker  run -it \
            --device=/dev/ttyACM0 \
            --device=/dev/ttyACM1 \
            --privileged \
            -v /dev/bus/usb/:/dev/bus/usb \
            -v ${PROJ_DIR}/../measurement_results/:/app/ \
            --entrypoint bash \
            ${CONTAINER_NAME} \
            -c "cd /usr/workdir/experiments/$1 && bash run.sh"