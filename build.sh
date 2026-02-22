#!/bin/bash

CURR_DIR=$(dirname "$0")

# build the kintsugi artifact docker image if it does not exists already
if ! docker image inspect kintsugi-artifact > /dev/null 2>&1; then
    docker build ${CURR_DIR} -t kintsugi-artifact
fi