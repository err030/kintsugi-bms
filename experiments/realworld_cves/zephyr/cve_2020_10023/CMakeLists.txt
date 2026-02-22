# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(cve_2020_10023)

FILE(GLOB app_sources src/*.c)
target_sources(app PRIVATE ${app_sources})
zephyr_include_directories(include)
include_directories_ifdef(CONFIG_HOTPATCH ../../../../hotpatches/include)
target_sources_ifdef(CONFIG_HOTPATCH app PRIVATE ../../../../hotpatches/zephyr/cve_2020_10023.c)

if(CONFIG_BUILD_WITH_TFM)
  target_include_directories(app PRIVATE
    $<TARGET_PROPERTY:tfm,TFM_BINARY_DIR>/install/interface/include
  )
endif()