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

#define HP_CONFIG_FREERTOS  1

#define HP_SLOT_ENTRY_COUNT         10

#if (HP_PERFORMANCE_MEASURE == 1)
#define HP_APPLICATOR_ENTRY_COUNT   HP_MEASURE_NUM_HOTPATCHES
#else
#define HP_APPLICATOR_ENTRY_COUNT   5
#endif

// memory configuartions
#define HP_CODE_MEMORY_SIZE         (HP_SLOT_ENTRY_COUNT * HP_MAX_CODE_SIZE)
#define HP_CODE_MEMORY_MAX_ALLOC    (HP_MAX_CODE_SIZE)




#endif // HP_CONFIG_H_