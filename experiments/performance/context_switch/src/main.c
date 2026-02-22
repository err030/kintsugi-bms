
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
#include "portmacro.h"

#include "nrf_soc.h"

#include "hp_freertos_mpu.h"
#include "hp_guard.h"
#include "hp_manager.h"
//#include "hp_measure.h"
#include "hp_slot.h"
#include "hp_config.h"

#define MAX_TEST_DATA_BYTES     (15U)                /**< max number of test bytes to be used for tx and rx. */
#define UART_TX_BUF_SIZE 2048                         /**< UART TX buffer size. */
#define UART_RX_BUF_SIZE 2048                         /**< UART RX buffer size. */
#define UART_HWFC APP_UART_FLOW_CONTROL_DISABLED

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


uint32_t __ramfunc __attribute__((noinline, used, optimize("O0"), aligned(8))) target_ram_function() {
    volatile uint32_t result;

    result = 0;
	// 1
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 2
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 3
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 4
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 5
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 6
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 7
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 8
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 9
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
	// 10
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
                    	// 10
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
                    	// 10
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
                    	// 10
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
                    	// 10
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
                    	// 10
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
    return result;
}

static volatile uint32_t __attribute__((aligned(8))) measured_cycles[HP_MEASURE_NUM_ITERATIONS];

__attribute__( ( always_inline ) ) static inline void __ENABLE_IRQ(void)
{
  __asm__ volatile ("cpsie i");
}


/** \brief  Disable IRQ Interrupts

  This function disables IRQ interrupts by setting the I-bit in the CPSR.
  Can only be executed in Privileged modes.
 */
__attribute__( ( always_inline ) ) static inline void __DISABLE_IRQ(void)
{
  __asm__ volatile ("cpsid i");
}

void
hp_measure_start(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0; 
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

    __DISABLE_IRQ();
}

void
hp_measure_stop(void) {
    //hp_measure_cycles_stop = DWT->CYCCNT;
    DWT->CTRL &= ~DWT_CTRL_CYCCNTENA_Msk;
    CoreDebug->DEMCR &= ~CoreDebug_DEMCR_TRCENA_Msk;

    __ENABLE_IRQ();
}

uint32_t
hp_measure_get(void) {
    return DWT->CYCCNT;
}


#define log(...) { \
UART_PRINT_FLAG = 1;\
printf(__VA_ARGS__);\
while (UART_PRINT_FLAG != 0) {\
    nrf_delay_ms(5);\
}\
}\
while(0)

uint32_t get_control_register(void) {
    uint32_t control;
    __asm__ volatile("MRS %0, CONTROL" : "=r" (control));
    return control;
}

void check_privilege_level(void) {
    uint32_t ctrl = get_control_register();

    if (ctrl & 1) {
        log("currently in unprivileged mode.\r\n");
    } else {
        log("currently in privileged mode.\r\n");
    }
}


static void
__ramfunc
__attribute__((optimize("O0")))
perform_measurement(void) {
    uint32_t start, end;
    uint32_t addr;

    addr = 0;
    start = 0;
    end = 0;

    for (volatile uint32_t task_prev = 0; task_prev < 2; task_prev++) {
        for (volatile uint32_t task_next = 0; task_next < 2; task_next++) {

            if (task_prev == 1 && task_next == 1) {
                // this is a special case that can never occur.
                continue;
            }

            for (volatile uint32_t scheduled = 0; scheduled < 2; scheduled++) {
                for (uint32_t i = 0; i < HP_MEASURE_NUM_ITERATIONS; i++) {
                    measured_cycles[i] = 0;
                }

                for (uint32_t i = 0; i < HP_MEASURE_NUM_ITERATIONS; i++) {
                    if (scheduled == 1) {
                        #if (configUSE_HP_FRAMEWORK == 1)
                        addr = ((uint32_t)&target_ram_function) & ~1;
                        hp_applicator_setup_measurement(addr);
                        #endif
                    }

                    hp_measure_start();

                    start = hp_measure_get();
                    #if (configUSE_HP_FRAMEWORK == 1)
                    hp_guard_applicator(task_next, task_prev);
                    #endif
                    end = hp_measure_get();
                    hp_measure_stop();

                    measured_cycles[i] = end - start;
                    
                }

                for (uint32_t i = 0; i < HP_MEASURE_NUM_ITERATIONS; i++) {
                    printf("%d\n", measured_cycles[i]);
                    nrf_delay_ms(10);
                }

                printf("done\n");
            }
        }
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
    perform_measurement();
}
