#ifndef HP_CONFIG_H_
#define HP_CONFIG_H_

#include "hp_def.h"

// measurement configurations
#define HP_PERFORMANCE_MEASURE                  0
//#define HP_PERFORMANCE_MEASURE_MANAGER          0
#define HP_PERFORMANCE_MEASURE_APPLICATOR       0
//#define HP_PERFORMANCE_MEASURE_GUARD            0
//#define HP_PERFORMANCE_MEASURE_STABILITY        0
#define HP_PERFORMANCE_MEASURE_CONTEXT_SWITCH   0

#define HP_CONFIG_FREERTOS      1
#define HP_CONFIG_LOG           0
#define HP_CONFIG_USE_FRAMEWORK 1
#define HP_TARGET_CRAZYFLY      1

#define HP_SLOT_COUNT     1

#if (HP_PERFORMANCE_MEASURE == 1)
#define HP_APPLICATOR_ENTRY_COUNT   HP_MEASURE_NUM_HOTPATCHES
#else
#define HP_APPLICATOR_ENTRY_COUNT   1
#endif

// memory configuartions
#define HP_MAX_CODE_SIZE            160
#define HP_CODE_MEMORY_SIZE         (HP_SLOT_COUNT * HP_MAX_CODE_SIZE)
#define HP_CODE_MEMORY_MAX_ALLOC    (HP_MAX_CODE_SIZE)


#define HP_MANAGER_TASK_STACK_SIZE  2048
#define HP_MANAGER_TASK_NAME        "HPM"
#define HP_MANAGER_TASK_PRIORITY    1


extern volatile uint32_t hp_manager_patch_go;

#endif // HP_CONFIG_H_