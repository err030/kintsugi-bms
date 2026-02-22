# MiniBMS Artifact Notes

This project is based on the original `kintsugi_artifact_zenodo`, with added MiniBMS-related experiment code, attack scripts, and result data. To avoid mixing the original Kintsugi content and the MiniBMS content, this file explains where the MiniBMS-related parts are.

## Where the `minibms/` framework is

MiniBMS is placed inside Kintsugi's `security` experiment structure:
- `experiments/security/before_patching/`
- `experiments/security/during_patching/`
- `experiments/security/after_patching/`

### MiniBMS experiment code (code, config, and build outputs for the three stages)
- `experiments/security/{before_patching,during_patching,after_patching}/`

### MiniBMS attack scripts (threshold / calibration / replay / state forging)
- `bms_threads_scripts/`

### 3. MiniBMS attack results and data
- `bms_measurement_results/`

This folder includes:
- raw UART attack logs
- result CSV files (summary / heatmap / timeline / latency)
- result figures (PDF / SVG)
- plotting/statistics scripts used to generate the results

## BMS-related files modified from the original Kintsugi Artifact

The following files were modified from the original `kintsugi_artifact_zenodo` to support the MiniBMS experiments:
- `Dockerfile`
- `experiments/security/before_patching/src/main.c`
- `experiments/security/before_patching/include/config/FreeRTOSConfig.h`
- `experiments/security/before_patching/Makefile`

- `experiments/security/during_patching/src/main.c`
- `experiments/security/during_patching/include/config/FreeRTOSConfig.h`

- `experiments/security/after_patching/src/main.c`
- `experiments/security/after_patching/include/config/FreeRTOSConfig.h`
- `experiments/security/after_patching/Makefile`

- `kintsugi/src/hp_exception.c`
  - Added diagnostic variables and logging logic for MemManage fault observation/verification
- `kintsugi/src/hp_freertos_mpu.c`
  - Adjusted MPU region settings to cover hotpatch-related regions
