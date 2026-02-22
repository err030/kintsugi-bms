# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(coap)

FILE(GLOB app_sources src/*.c)
zephyr_include_directories(include)
target_sources(app PRIVATE ${app_sources})
target_include_directories(app PRIVATE ${ZEPHYR_BASE}/subsys/net/ip)

include_directories_ifdef(CONFIG_HOTPATCH ../../../../hotpatches/include)
target_sources_ifdef(CONFIG_HOTPATCH app PRIVATE ../../../../hotpatches/zephyr/cve_2020_10063.c)