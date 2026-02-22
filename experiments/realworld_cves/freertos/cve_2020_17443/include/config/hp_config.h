#ifndef HP_CONFIG_H_
#define HP_CONFIG_H_

#include "hp_def.h"

#define HP_CONFIG_FREERTOS          1

#define HP_MAX_CODE_SIZE            256
#define HP_SLOT_COUNT               3

#define HP_APPLICATOR_ENTRY_COUNT   5

// memory configuartions
#define HP_CODE_MEMORY_SIZE         (HP_SLOT_COUNT * HP_MAX_CODE_SIZE)
#define HP_CODE_MEMORY_MAX_ALLOC    (HP_MAX_CODE_SIZE)

// hotpatch guard configurations
#define HP_GUARD_LOWEST_PRIORITY    1

// frequency of the board (in MHz)
#define HP_BOARD_FREQUENCY_NRF52    64
#define HP_BOARD_FREQUENCY          HP_BOARD_FREQUENCY_NRF52

#endif // HP_CONFIG_H_