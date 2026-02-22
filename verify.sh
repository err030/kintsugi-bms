#!/bin/bash

PROJ_DIR=$(dirname "$0")
CONTAINER_NAME="kintsugi-artifact"

# verify that the container exists
bash ${PROJ_DIR}/build.sh

# print the information about this evaluation script
function print_information() {
    echo    "========================================"
    echo    "  Experimental Verification (Building)  "
    echo    "========================================"
    echo    "Verification..."
}

# verify that it is possible to build each experiment
function verify () {
    docker  run -it \
                -v ${PROJ_DIR}/../measurement_results/:/app/ \
                --entrypoint bash \
                ${CONTAINER_NAME} \
                -c "cd /usr/workdir/experiments/$1 && bash verify.sh"
}

verify performance/micro_benchmarks
verify performance/context_switch
verify performance/resource_utilization
verify performance/scalability
verify realworld_cves
verify security

