# Kintsugi: Secure Hotpatching for Code-Shadowing Real-Time Embedded Systems

This is the artifact for the paper "*Kintsugi: Secure Hotpatching for Code-Shadowing Real-Time Embedded Systems*" which is accepted at the 34th USENIX Security Symposium.


## Artifact Description & Prerequisites

All experiments have been conducted on the Nordic *nRF52840-DK* ([link](https://www.nordicsemi.com/Products/Development-hardware/nRF52840-DK)) and all scripts (except those in `evaluation_scripts`) are meant to be run inside of a docker container.
For this, we provide a Dockerfile to build an image that already installs all necessary software prerequisities including the necessary dependencies to run the artifacts and build Kintsugi for FreeRTOS and Zephyr.


### Software Requirements
We recommend using a Linux distribution, preferably Ubuntu-based, as all experiments have been successfully tested on this distribution. We have also verified that the experiments work on a virtual machine running Ubuntu 22.04 LTS. Additionally, it is necessary to have bash installed (which comes standard with Linux) and Docker, which will handle the installation of all other prerequisites.


#### Setting up the nRF52840-DK
To set up the nRF52840-DK board, it is advised to have the [nRF Command Line Tools](https://www.nordicsemi.com/Products/Development-tools/nRF-Command-Line-Tools/Download) together with the [JLinkGDBServer](https://www.segger.com/products/debug-probes/j-link/tools/j-link-gdb-server/about-j-link-gdb-server/) to be able to debug the board outside of the docker image.


### Basic Test
To verify that Docker can successfully build every experiment, please run the `verify.sh` script. This script will check that all experiments are built correctly; if the Docker image is missing, it will build it as well. For each experiment, the script will output whether the build was successful or not. It takes approximately 8 min to verify everything.

Note, that this test does not require the existence of the hardware as this is a pure software test.

## Experimental Evaluation

### Major Claims

- **(C1) - Micro-Benchmarks (Manager)**: Kintsugi introduces minimal performance overhead across the hotpatching process. Validation and scheduling have consistent measurement times, independent of hotpatch sizes. This was proven by experiment (**E1**) and explained in *Section 6.1*, "Manager" (Table 2), for hotpatch sizes based on `RapidPatch` and `AutoPatch`. An extended version is provided in *Appendix D* (*Table 5*), and hotpatch sizes from Kintsugi are discussed in *Section 6.4*, with results in *Appendix E* (*Table 6*).

- **(C2) - Micro-Benchmarks (Context Switch / Guard & Applicator)**: The performance overhead introduced by Kintsugi into the context switch of an RTOS is minimal. This is proven by experiment (**E2**) and described in *Section 6.1*, "*Guard & Applicator*" *Table 3*.

- **(C3) - Hotpatching Scalability**: Successively processing and applying hotpatches scales linearly with the number of hotpatches, as demonstrated with up to 64 hotpatches. This was proven by experiment (**E3**) and is described in *Section 6.2*, with the results shown in *Figure 5*.

- **(C4) - Memory Overhead / Resource Utilization**: The memory overhead introduced by Kintsugi grows predictably with the maximum hotpatch size and slot count. The overhead ranges from an average of 3.5KB to 42KB. This is proven by experiment (**E4**) and described in *Section 6.3*, with the shown in *Figure 6*.

- **(C5) - Real-World CVE Hotpatching**: Kintsugi is capable of hotpatch real-world vulnerabilities as we demonstrated with 10 CVEs. This is proven by experiment (**E5**) and is described in *Section 6.4*. Resulting hotpatch sizes are shown in *Table 4*.

- **(C6) - Security Experiments**: Kintsugi is able to prevent tampering attacks from an adversary before, during and after the hotpatching process. This is proven by experiment (**E6**) and is described in *Section 8*.


### Experiments
We provide evaluation scripts in the directory `evaluation_scripts` which are interactive and include descriptions of their working and how to correctly use them. If a script automatically produces outputs (i.e., the performance experiments) they will be stored in the folder `measurement_results` under their corresponding subdirectories. We clearly mark experiments that do *not* automatically produce outputs. Those experiments require access to the UART of the board through, e.g., `screen`, `minicom` or `puTTY` with a baudrate of 115200.


- **(E1) `micro-benchmarks.sh` [ ~ 6 computer-hours ]**: Execute the *Micro-Benchmarking* experiments of the *Manager* to prove (**C1**), measuring how each component inside of the *Manager* takes to execute.
    - **Automatic Output**: *Yes.*
    - **Execution**: The measurement does not require user interaction.
    - **Results**: Upon execution, the user will be asked to select the hotpatch sizes to measure. They can choose between *RapidPatch & AutoPatch* (Section 6.1) or *Kintsugi* (Section 6.4). Measuring a single configuration takes approximately 100 seconds, hence why the script will stay at "*Reading UART output*" for a while. All results will be stored in `micro-benchmarks/manager` with raw measurements being stored in `measurements` and the resulting tables in `output`. The measurements in the table should be as close as possible to those claimed in (**C1**). See [experiments/performance/README.md](./experiments/performance/README.md) for more details on the expected results.

- **(E2): `context-switch.sh` [ ~ 2 computer-minutes ]**: Execute the *Micro-Benchmarking* experiments of the *Guard & Applicator* focusing on the *Context-Switch* of the RTOS to prove (**C2**), demonstrating how much time Kintsugi adds to the context-switch of the RTOS.
    - **Automatic Output**: *Yes.*
    - **Execution**: The measurement does not require user interaction.
    - **Results**: All results will be stored in `micro-benchmarks/context-switch` with raw measurements being stored in `measurements` and the resulting tables in `output`. The measurements in the table should be as close as possible to those claimed in (**C2**). See [experiments/performance/README.md](./experiments/performance/README.md) for more details on the expected results.

- **(E3): `scalability.sh` [ ~ 4 computer-hours ]**: Execute the *Hotpatching Scalability* experiments to prove (**C3**), measuring Kintsugi's performance when applying multiple consecutive hotpatches, demonstrating that it grows linearly in the number of hotpatches.
    - **Automatic Output**: *Yes.*
    - **Execution**: The measurement does not require user interaction.
    - **Results**: All results will be stored in `scalability` with raw measurements being stored in `measurements` and the resulting plot will be stored in `output`. The plot should show linear growth in the dimension of number of hotpatches and be as close as possible to the results claimed in (**C3**). See [experiments/performance/README.md](./experiments/performance/README.md) for more details on the expected results.

- **(E4): `resource-utilization.sh` [ ~ 3 computer-hours ]**: Execute the *Resource Utilization* / *Memory Overhead* experiments to prove (**C4**), measuring the memory overhead introduced by Kintsugi under different parameter configurations of hotpatch counts and sizes.
    - **Automatic Output**: *Yes.*
    - **Execution**: The measurement does not require user interaction.
    - **Results**: All results will be stored in `resource-utilization` with raw measurements being stored in `measurements` and the resulting plot will be stored in `output`. The plot should show an increase in memory overhead in both dimensions and be as close as possible to the results claimed in (**C4**). See [experiments/performance/README.md](./experiments/performance/README.md) for more details on the expected results.

- **(E5): `realworld-cves.sh` [ ~ 30 minutes total ]**: Perform the *Real-World Hotpatching* experiments to prove (**C5**), demonstrating that Kintsugi is capable in hotpatching real-world CVEs.
    - **Automatic Output**: *No.*
    - **Preparation**: Connect to the device's UART as described above. Typically the access will be over `ttyACM0` or `ttyACM1`.
    - **Execution**: Upon executing the script the user will be asked to input a number between 1 and 10 to decide which CVE to execute on the board.
    - **Results**: The results differ for each CVE experiment. We provide details about expected outputs in [experiments/realworld_cves/README.md](./experiments/realworld_cves/README.md). This file also reflects all the outputs that we have obtained during our experimental evaluation.

- **(E6): `security.sh` [ ~ 10 minutes total ]**: Perform the *Security* experiments to prove (**C6**), demonstrating that Kintsugi is resistant against adversaries *before*, *during* and *after* the hotpatching process.
    - **Automatic Output**: *No.*
    - **Preparation**: Connect to the device's UART as described above. Typically the access will be over `ttyACM0` or `ttyACM1`.
    - **Execution**: Upon executing the script the user will be asked to input a number between 1 and 3 to decide which of the three security experiments to run.
    - **Results**: The results differ for each security experiment. We provide details about expected outputs in [experiments/security/README.md](./experiments/security/README.md). This file also reflects all the outputs that we have obtained during our experimental evaluation.


## Reusability
We provide additional details on how to properly integrate the tool into the `Zephyr` and `FreeRTOS` RTOSes in the [example_rtos_integration](./example_rtos_integration) folder. We provide the necessary files that must be adapted to the respective RTOS and instructions on how to do so manually. In our Docker, we require patches to modify the corresponding Git repositories. Therefore, the git-patches for the RTOSes can potentially be used immediately.

Integrating Kintsugi into an RTOS should be straightforward. To do this, create a task for the *Manager* and modify the context switch to check if the *previous* or *next* task is the *Manager*. Additionally, call the *Guard & Applicator* before restoring the execution context of the next task.

## Repository Structure
```bash
.
├── evaluation_scripts/             # Bash scripts to perform experiments (all executed from _outside_ the docker)
│   ├── context-switch.sh           # Script to perform the micro-benchmark measurements for the Guard & Applicator (Context Switch)
│   ├── micro-benchmarks.sh         # Script to perform the micro-benchmark measurements for the Manager
│   ├── realworld-cves.sh           # Script to perform the real-world CVE experiments
│   ├── resource-utiliuation.sh     # Script to perform the resource utilization / memory overhead experiments
│   ├── scalability.sh              # Script to perform the hotpatching scalability experiments
│   └── security.sh                 # Script to perform the security experiments (before, during, after hotpatching)
├── example_rtos_integration/       # Details on how to integrate Kintsugi into FreeRTOS and Zephyr
├── experiments/                    # Source code files for all experiments (also contains the measurement results for the paper)
│   ├── case_study/                 # Code for the Crazyflie 2.0 Case Study
│   ├── performance/                # All performance related experimenets
│   │   ├── context_switch/         # Source code for the micro-benchmark measurements for the Guard & Applicator
│   │   ├── micro_benchmarks/       # Source code for the micro-benchmark measurements for the Manager
│   │   ├── resource_utilization/   # Source code for the resource utilization / memory overhead experiments
│   │   └── scalability/            # Source code the hotpatching scalability experiments
│   ├── realworld_cves/             # Source code files for the 10 real-world CVEs
│   └── security/                   # Source code files for the security experiments (before, during, after hotpatching)
├── external/                       # Any external source files are stored here (RTOS, Libs, SDK, etc.)
│   ├── lib/                        # Picotcp
│   ├── patches/                    # Patches for all the external sources
│   ├── rtos/                       # Zephyr and FreeRTOS
│   ├── sdk/                        # nRF52 and Zephyr SDK
│   └── tools/                      # JLink
├── hotpatches/                     # Source code files for all hotpatches regarding the real-world CVEs and case study
├── hotpatch_generator/             # Source code for the hotpatch generator to automatically generate hotpatches from source
├── kintsugi/                       # Source code for the Kintsugi framework
└─ measurement_results/             # Folder to store measurement results from the Docker image
```