
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

// PicoTCP
#include "pico_protocol.h"
#include "pico_stack.h"
#include "pico_socket.h"
#include "pico_ipv6.h"
#include "pico_frame.h"
#include "pico_icmp6.h"

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

#include "hp_freertos_mpu.h"
#include "hp_manager.h"
#include "hp_code_data.h"


#ifndef __ramfunc
    #define __ramfunc __attribute__((section(".ramfunc")))
#endif

#define TASK_DELAY        200           /**< Task delay. Delays a LED0 task for 200 ms */
#define TIMER_PERIOD      1000          /**< Timer period. LED1 timer will expire after 1000 ms */

TaskHandle_t hp_manager_task_handle;
TaskHandle_t picotcp_task_handle;

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
// ---- PicoTCP
volatile uint32_t pico_ms_tick;
void picotcp_task(void *parameter) {
    
    struct pico_frame *echo;
    struct pico_ipv6_hdr *net_hdr;
    struct pico_icmp6_hdr *transport_hdr;
    
    unsigned char payload[] = { 0xAA, 0xBB, 0xCC, 0xDD };

    int flip = 0;
    int cnt = 0;
    while (true) {
        printf("Flip: %d\r\n", flip);
        net_hdr = (struct pico_ipv6_hdr *)pvPortMalloc(sizeof(struct pico_ipv6_hdr));
        memset(net_hdr, 0, sizeof(struct pico_ipv6_hdr));

        transport_hdr = (struct pico_icmp6_hdr *)pvPortMalloc(sizeof(struct pico_icmp6_hdr));
        memset(transport_hdr, 0, sizeof(struct pico_icmp6_hdr));

        echo = (struct pico_frame *)pvPortMalloc(sizeof(struct pico_frame));
        memset(echo, 0, sizeof(struct pico_frame));
        
        echo->payload_len = sizeof(payload);
        echo->payload = payload;

        echo->net_hdr = (uint8_t*)net_hdr;
        echo->transport_hdr = (uint8_t*)transport_hdr;

        if (flip == 0) {
            echo->transport_len = PICO_ICMP6HDR_ECHO_REQUEST_SIZE + sizeof(payload);
        } else {
            echo->transport_len = PICO_ICMP6HDR_ECHO_REQUEST_SIZE - 1;
        }

        if (cnt > 5) {
            flip ^= 1;
        } else {
            cnt++;
        }
        int result = wrapper_pico_icmp6_send_echoreply(echo);

        vPortFree(net_hdr);
        vPortFree(transport_hdr);
        vPortFree(echo);

        printf("Echo Result: %d\r\n", result);
        vTaskDelay(1000);
    }
}

void
hp_manager_task(void *parameters) {

    uint32_t identifier = 0;
    printf("Starting Kintsugi Hotpatch Manager Task\r\n");

    hp_manager(HOTPATCH_CODE, sizeof(HOTPATCH_CODE), &identifier);

    while (1) {
        vTaskDelay(10);
    }
    vTaskDelete(NULL);
}

int main(void)
{
    hp_mpu_init();

    hp_manager_init();

    ret_code_t err_code;

    /* Initialize clock driver for better time accuracy in FREERTOS */
    err_code = nrf_drv_clock_init();
    APP_ERROR_CHECK(err_code);

    
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

    DEBUG_LOG("CVE-2020-17443\r\n");

    printf("Task Manager: %d\r\n", xTaskCreate(hp_manager_task, configHP_TASK_NAME, configMINIMAL_STACK_SIZE, NULL, 1, &hp_manager_task_handle));
    printf("Task PicoTCP: %d\r\n", xTaskCreate(picotcp_task, "PICO", configMINIMAL_STACK_SIZE, NULL, 2, &picotcp_task_handle));


    /* Activate deep sleep mode */
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;

    /* Start FreeRTOS scheduler. */
    vTaskStartScheduler();

    while (true)
    {
        /* FreeRTOS should not be here... FreeRTOS goes back to the start of stack
         * in vTaskStartScheduler function. */
    }
}

/**
 *@}
 **/
