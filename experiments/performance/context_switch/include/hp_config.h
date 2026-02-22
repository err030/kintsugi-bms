#ifndef HP_CONFIG_H_
#define HP_CONFIG_H_

#include "hp_def.h"

// measurement configurations
#define HP_PERFORMANCE_MEASURE                  1
//#define HP_PERFORMANCE_MEASURE_MANAGER          0
#define HP_PERFORMANCE_MEASURE_APPLICATOR       1
//#define HP_PERFORMANCE_MEASURE_GUARD            0
//#define HP_PERFORMANCE_MEASURE_STABILITY        0
#define HP_PERFORMANCE_MEASURE_CONTEXT_SWITCH   0

#define HP_CONFIG_FREERTOS  1
#define HP_CONFIG_LOG       0

#define HP_SLOT_COUNT         10
#define HP_MAX_CODE_SIZE      512  

// memory configuartions
#define HP_CODE_MEMORY_SIZE         (HP_SLOT_COUNT * HP_MAX_CODE_SIZE)
#define HP_CODE_MEMORY_MAX_ALLOC    (HP_MAX_CODE_SIZE)

// hotpatch guard configurations
// frequency of the board (in MHz)
#define HP_BOARD_FREQUENCY_NRF52    64
#define HP_BOARD_FREQUENCY          HP_BOARD_FREQUENCY_NRF52



#endif // HP_CONFIG_H_