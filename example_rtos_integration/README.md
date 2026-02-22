# Integrating Kintsugi into Real-Time Operating Systems

In general, integrating Kintsugi into any RTOS requires adding the `Guard` and `Applicator` to the context switch within the kernel. Additionally, one might need to modify the task structures to allow for efficient differentiation between a regular and the hotpatching task. However, this implementation is up to the developers, but we provide for FreeRTOS and Zephyr examples on how to accomplish this.

While we provide instructions on how to manually setup Kintsugi but also provide example files, for the C-files, that already contain the necessary changes to clearly showcase these changes. We have marked the changes introduced by Kintsugi with `==> Kintsugi Start <==` and `==> Kintsugi End <==`.

## FreeRTOS Guide

To integrate Kintsugi into FreeRTOS, one has to perform the following changes to their FreeRTOS, specifically FreeRTOS-Kernel.

### Context Switch Integration
**Edit `FreeRTOS-Kernel/tasks.c`**:
1) Add the includes `hp_config.h`, `hp_guard.h`, and `hp_measure.h`. 
2) Extend the `tskTaskControlBlock` structure with a field `BaseType_t uxHPManager`:
```C
#if ( configUSE_HP_FRAMEWORK == 1 )
BaseType_t uxHPManager;
#endif

```
3) Add the task identifier recognition into `prvInitialiseNewTask` **after** storing the task name:
```C
#if ( configUSE_HP_FRAMEWORK == 1 ) 
if (strcmp(pcName, configHP_TASK_NAME) == 0) {
    pxNewTCB->uxHPManager = 1;
} else {
    pxNewTCB->uxHPManager = 0;
}
#endif
```

4) Extend the `vTaskSwitchContext` function a variable storing the `prev_task_hp`:
```C
#if ( configUSE_HP_FRAMEWORK == 1 ) 
uint32_t prev_task_hp = 0;
#endif
```

5) Before the call to `taskSELECT_HIGHEST_PRIORITY_TASK`, update the `prev_task_hp` which will be passed to the `Guard`:
```C
#if ( configUSE_HP_FRAMEWORK == 1 )
prev_task_hp = pxCurrentTCB->uxHPManager;
#endif
```

6) After the call of `taskSELECT_HIGHEST_PRIORITY_TASK`, call the `Guard` for hotpatch application:
```C
#if ( configUSE_HP_FRAMEWORK == 1 )
hp_guard_applicator(pxCurrentTCB->uxHPManager, prev_task_hp);
#endif
```

---

#### Performance Measurement for Context Switch

- *Performance Measurement - Start*: At the beginning of the `vTaskSwitchContext` function, add the following to start the measurement:
```C
#if ( HP_PERFORMANCE_MEASURE_CONTEXT_SWITCH == 1 )
hp_measure_start();
#endif
``` 

- *Performance Measurement - End*: At the end of the `vTaskSwitchContext`, add the following to end the measurement:
```C
#if ( HP_PERFORMANCE_MEASURE_CONTEXT_SWITCH == 1 )
hp_measure_stop();
hp_measure_output();
#endif
``` 

---

### CMake Integration
To be able to compile a binary that includes Kintsugi, we have to make the following changes to the Makefile.

1) Add a path to the directory of Kintsugi: `HP_DIR := $(HP_PROJ_DIR)/kintsugi` where `HP_PROJ_DIR` is the project directory.
2) Include the Makefile from Kintsugi `include $(HP_DIR)/Makefile`.
    - This makefile contains all the necessary files to properly integrate Kintsugi into an RTOS.

**Adding Hotpatches**
These changes are mandatory if a hotpatch should be *statically* added to the firmware (i.e., for experimental purposes).
1) Add a path to the directory of the hotpatches for Kintsug: `PATCH_DIR := $(HP_PROJ_DIR)/hotpatches`.
2) For hotpatches, add the include folder: `INC_FOLDERS += $(PATCH_DIR)/include`.
3) Add the hotpatch for the specific binary: `SRC_FILES += $(PATCH_DIR)/freertos/cve_2021_31572.c`.

## Zephyr Guide

To integrate Kintsugi into a project that uses Zephyr, one has to perform the following changes.

### Context Switch Integration
**Edit `zephyr/kernel/init.c`**:
- Add the following code to initialize the hotpatch manager of Kintsugi:
```C
#ifdef CONFIG_HOTPATCH
hp_manager_init();
#endif
```

**Edit `zephyr/arch/arm/core/cortex_m/swap.c`**:
- Before restoring the mode of the task, add the following code to call the `Guard`:
```C
#ifdef CONFIG_HOTPATCH
hp_guard_applicator(current->hp_manager, previous->hp_manager);
#endif
```

**Edit `zephyr/include/zephyr/kernel/thread.h`**:
- Add the following field to the `k_thread` structure:
```C
#ifdef CONFIG_HOTPATCH
uint32_t  hp_manager;
#endif
```

**Edit `zephyr/kernel/thread.c`**:
- In the function `z_setup_new_thread` add this code as an identifier to the manager thread, the name can also be adapted:
```C
#ifdef CONFIG_HOTPATCH
new_thread->hp_manager = strcmp(name, "HP_TASK") == 0;
#endif
```

### Kintsugi Driver Integration
**Edit `zephyr/drivers/CMakeLists.txt`**:
- At the very end of the file, add the following, and adjust it to the path of Kintsugi:
```
add_subdirectory_ifdef(CONFIG_HOTPATCH ${ZEPHYR_BASE}/../../../../kintsugi kintsugi)
```

**Edit `zephyr/drivers/Kconfig`**:
- Add the following to the list of Kconfig sources to add Kintsugi as a driver config:
```
source "$srctree/../../../../kintsugi/Kconfig"
```
