# Kintsugi Experiments: Performance Measurements

This directory contains all experiments to measure the performance of Kintsugi, as shown in *Section 6* of the paper. For each experiment, we give a short description for each of the experiments.

**Important: Do NOT connect using `screen` or anything to the UART, the scripts take care of this.**

How to perform measurements:
- Run the experiment script `bash ./run.sh` from the corresponding experiment folder.
- Follow the instructions.
- Results will be stored in `/evaluation_scripts/measurement_results`.

## Micro-Benchmarks (C1 - E1)

- [Source Folder](./micro_benchmarks/)

- Paper References:
    - Section 6.1, 'Manager', Table 2 (main-body version)
    - Section 6.1, 'Manager', Appendix D, Table 5 (full version)
    - Section 6.4, Appendix E, Table 6

### Description
Experiments to measure the performance overhead introduced by the *Manager* of Kintsugi. This experiment executes the *Manager* and its sub-stages such as *Validation*, *Storing* and *Scheduling* of hotpatches, measuring their execution times and storing those in text files that can then be used to derive the tables from within the paper.

## Context-Switch (C2 - E2)

- [Source Folder](./context_switch/)

- Paper References:
    - Section 6.1, 'Guard & Applicator', Table 3

### Description
Experiemnts to measure the overhead introduced by the context switch, split into the *Guard* and *Applicator* for the different possible execution states considering whether the *previous task* was the *Manager* or the *next task* is the *Manager*. Measurements are stored in text files that can be used to derive the tables from within the paper.

## Hotpatch Scalability (C3 - E3)

- [Source Folder](./scalability/)

- Paper References:
    - Section 6.2, Figure 5

### Description
Experiments to measure the scalability of Kintsugi when applying multiple consecutive hotpatches to the system for increasing number of hotpatches and hotpatch sizes. Measurement results are stored in text files that can be used to plot the figures from within the paper.

## Resource Utilization / Memory Overhead (C4 - E4)

- [Source Folder](./resource_utilization/)

- Paper References:
    - Section 6.3, Figure 6
    
### Description
Experiments to measure the memory overhead introduced by Kintsugi for increasing numbers of hotpatches and hotpatch sizes. Measurement results are stored in text files that can be used to plot the figures form within the paper.