
// FreeRTOS
#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "nordic_common.h"
#include "nrf_drv_clock.h"
#include "sdk_errors.h"


#include "nrf_log.h" 
#include "nrf_log_ctrl.h"
#include "nrf_log_default_backends.h"

// Example
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include <time.h>
#include "app_uart.h"
#include "app_error.h"
#include "nrf_delay.h"
#include "nrf.h"
#include "bsp.h"
#include "semphr.h"
#include "message_buffer.h"
#if defined (UART_PRESENT)
#include "nrf_uart.h"
#endif
#if defined (UARTE_PRESENT)
#include "nrf_uarte.h"
#endif

#include "nrf_soc.h"

#include "hp_freertos_mpu.h"
#include "hp_guard.h"
#include "hp_def.h"
#include "hp_manager.h"
#include "hp_slot.h"
#include "hp_measure.h"

#define MAX_TEST_DATA_BYTES     (15U)                /**< max number of test bytes to be used for tx and rx. */
#define UART_TX_BUF_SIZE 256                         /**< UART TX buffer size. */
#define UART_RX_BUF_SIZE 256                        /**< UART RX buffer size. */
#define UART_HWFC APP_UART_FLOW_CONTROL_DISABLED


TaskHandle_t dummy_task_handle;
TaskHandle_t performance_task_handle;

void uart_error_handle(app_uart_evt_t * p_event)
{
    if (p_event->evt_type == APP_UART_COMMUNICATION_ERROR)
    {
        APP_ERROR_HANDLER(p_event->data.error_communication);
    }
    else if (p_event->evt_type == APP_UART_FIFO_ERROR)
    {
        APP_ERROR_HANDLER(p_event->data.error_code);
    }
    else if (p_event->evt_type == APP_UART_TX_EMPTY) {
        UART_PRINT_FLAG = 0;
    }
}

static UBaseType_t ulNextRand;
UBaseType_t uxRand( void )
{
    const uint32_t ulMultiplier = 0x015a4e35UL, ulIncrement = 1UL;

	/* Utility function to generate a pseudo random number. */

	ulNextRand = ( ulMultiplier * ulNextRand ) + ulIncrement;
	return( ( int ) ( ulNextRand >> 16UL ) & 0x7fffUL );
}

static void prvSRand( UBaseType_t ulSeed )
{
	/* Utility function to seed the pseudo random number generator. */
    ulNextRand = ulSeed;
}


void __ramfunc __attribute__((noinline, used, optimize("O0"), aligned(8), optimize("unroll-loops"))) target_ram_function() {
    #pragma GCC unroll 64
    for (int i = 0; i < HP_SLOT_COUNT; i++) {
        __asm volatile( "nop\n"
                        "nop\n"
                        "nop\n"
                        "nop\n");
    }
}


#define HP_SIZE (sizeof(struct hp_header) + HP_MAX_CODE_SIZE)
volatile uint8_t hotpatch_code[HP_SIZE * HP_SLOT_COUNT] = { 0 };


#define INF_LOOP    while(1) { vTaskDelay(1); }
static void
__attribute__((optimize("O0")))
perform_measurement(void* data) {
    
    volatile uint32_t start, end;
    volatile uint32_t addr;

    volatile struct hp_header *hotpatch_header;
    volatile uint32_t identifier;
    volatile uint32_t result;

    struct hp_slot *slot;

    slot = NULL;

    for (uint32_t i = 0; i < HP_MEASURE_NUM_ITERATIONS; i++) {
        hp_measure_list[i] = 0;
    }

    for (uint32_t i = 0; i < HP_SLOT_COUNT; i++) {
        hotpatch_header = (struct hp_header*)((uint32_t)(&hotpatch_code) + i * HP_SIZE);
        hotpatch_header->type = HP_TYPE_REDIRECT;
        hotpatch_header->target_address = (uint32_t)&target_ram_function + (i * sizeof(uint32_t));
        hotpatch_header->code_size = HP_MAX_CODE_SIZE;
        hotpatch_header->code_ptr = (uint8_t *)NULL;
    }

    hp_measure_reset();


    
    result = 0;
    uint32_t id_list[HP_MEASURE_NUM_HOTPATCHES] = { 0 };
    for (uint32_t i = 0; i < HP_MEASURE_NUM_ITERATIONS; i++) {

        identifier = 1;
        
        // erase the identifies
        for(uint32_t j = 0; j < HP_MEASURE_NUM_HOTPATCHES; j++)
            id_list[j] = 0;

        #if (HP_PERFORMANCE_MEASURE_MANAGER == 1)
        hp_measure_start_irq();
        hotpatch_header = (struct hp_header *)((uint32_t)&hotpatch_code);
        for (uint32_t j = 0; j < HP_MEASURE_NUM_HOTPATCHES; j++) {
            hotpatch_header = (struct hp_header*)((uint32_t)(&hotpatch_code) + j * HP_SIZE);
            result = hp_manager((const uint8_t*)hotpatch_header, HP_MAX_CODE_SIZE + sizeof(struct hp_header), &identifier);
            id_list[j] = identifier;
        }
        hp_measure_stop_irq();
        #else
        result = hp_manager(hotpatch_code, HP_MAX_CODE_SIZE + sizeof(struct hp_header), &identifier);
        #endif

        // remove the hotpatches after measurement
        for (uint32_t j = 0; j < HP_MEASURE_NUM_HOTPATCHES; j++) {
            hp_slot_get(id_list[j], &slot);
            uint32_t res = hp_slot_remove_hotpatch(slot);
        }
    }

    for (uint32_t i = 0; i < HP_MEASURE_NUM_ITERATIONS; i++) {
        printf("%d\r\n", hp_measure_list[i]);
        nrf_delay_ms(10);
    }

    printf("done\n");

    while (true) {
        taskYIELD();
    }
}

static void 
__attribute__((optimize("O0")))
dummy_task(void *parameter) {
    volatile uint32_t counter = 0;
    while (1) {
        // simulate workload
        for (uint32_t i = 0; i < 100; i++) {
            counter += 1;
        }
        vTaskDelay(1);
    }
}


int main(void)
{
    hp_mpu_init();

    hp_manager_init();

    ret_code_t err_code;

    /* Initialize clock driver for better time accuracy in FREERTOS */
    err_code = nrf_drv_clock_init();
    APP_ERROR_CHECK(err_code);
    nrf_drv_clock_lfclk_request(NULL);
    
    APP_ERROR_CHECK(NRF_LOG_INIT(NULL));
    NRF_LOG_DEFAULT_BACKENDS_INIT();

    const app_uart_comm_params_t comm_params =
      {
          RX_PIN_NUMBER,
          TX_PIN_NUMBER,
          RTS_PIN_NUMBER,
          CTS_PIN_NUMBER,
          UART_HWFC,
          false,
#if defined (UART_PRESENT)
          NRF_UART_BAUDRATE_115200
#else
          NRF_UARTE_BAUDRATE_115200
#endif
      };

    APP_UART_FIFO_INIT(&comm_params,
                         UART_RX_BUF_SIZE,
                         UART_TX_BUF_SIZE,
                         uart_error_handle,
                         APP_IRQ_PRIORITY_LOWEST,
                         err_code);

    APP_ERROR_CHECK(err_code);

    xTaskCreate(dummy_task, "DUMMY1", configMINIMAL_STACK_SIZE, NULL, 2, NULL);
    xTaskCreate(dummy_task, "DUMMY2", configMINIMAL_STACK_SIZE, NULL, 2, NULL);
    xTaskCreate(perform_measurement, configHP_TASK_NAME, configMINIMAL_STACK_SIZE*2, NULL, 1, &performance_task_handle);
    
    vTaskStartScheduler();
}
