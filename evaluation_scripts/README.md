# Kintsugi Experimental Evaluation Scripts


This directory contains all necessary scripts to reproduce the experiments from our paper.
Experiments that measure performance: `micro-benchmarks.sh`, `context-switch.sh`, `resource-utilization.sh` and `scalability.sh` store their results in the `measurement_results` directory. This folder contains the raw measurements as well as the produced outputs, i.e., table ans figures that are shown in the paper. Each script has a minimal explanation of what it will do and which tables or figures from the paper it will generate.

All of these experiment scripts are designed to be executed from **outside** of the docker container and once executed they will guide through the experimental process.

Each experiment has their own README that includes additional details:
- [Performance Measurements](../experiments/performance/README.md)
- [Real-World CVE Hotpatching](../experiments/realworld_cves/README.md)
- [Security Experiments](../experiments/security/README.md)
- [Case Study on Crazyflie 2.0](../experiments/case_study/README.md)
