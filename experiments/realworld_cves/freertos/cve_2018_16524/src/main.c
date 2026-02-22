
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

// FreeRTOS + TCP
#include "FreeRTOS_IP.h"
#include "FreeRTOS_Sockets.h"
#include "FreeRTOS_IP_Private.h"

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
#if defined (UART_PRESENT)
#include "nrf_uart.h"
#endif
#if defined (UARTE_PRESENT)
#include "nrf_uarte.h"
#endif

#include "hp_freertos_mpu.h"
#include "hp_manager.h"
#include "hp_code_data.h"

#define TASK_DELAY        2000 
#define TIMER_PERIOD      1000

TaskHandle_t main_task_handle;
TaskHandle_t hp_manager_task_handle;

//#define ENABLE_LOOPBACK_TEST  /**< if defined, then this example will be a loopback test, which means that TX should be connected to RX to get data loopback. */

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

void vLoggingPrintf( const char * pcFormat,
                     ... )
{
    va_list arg;

    va_start( arg, pcFormat );
    vprintf( pcFormat, arg );
    va_end( arg );
}

static const uint8_t ucIPAddress[ 4 ] = { configIP_ADDR0, configIP_ADDR1, configIP_ADDR2, configIP_ADDR3 };
static const uint8_t ucNetMask[ 4 ] = { configNET_MASK0, configNET_MASK1, configNET_MASK2, configNET_MASK3 };
static const uint8_t ucGatewayAddress[ 4 ] = { configGATEWAY_ADDR0, configGATEWAY_ADDR1, configGATEWAY_ADDR2, configGATEWAY_ADDR3 };
static const uint8_t ucDNSServerAddress[ 4 ] = { configDNS_SERVER_ADDR0, configDNS_SERVER_ADDR1, configDNS_SERVER_ADDR2, configDNS_SERVER_ADDR3 };
const uint8_t ucMACAddress[ 6 ] = { configMAC_ADDR0, configMAC_ADDR1, configMAC_ADDR2, configMAC_ADDR3, configMAC_ADDR4, configMAC_ADDR5 };

#define mainHOST_NAME				"RTOSDemo"
#define mainDEVICE_NICK_NAME		"windows_demo"

const char *pcApplicationHostnameHook( void )
{
    /* Assign the name "FreeRTOS" to this network node.  This function will
    be called during the DHCP: the machine will be registered with an IP
    address plus this name. */
    return mainHOST_NAME;
}

BaseType_t xApplicationDNSQueryHook( const char *pcName )
{
    return pdTRUE;
}


void vApplicationIPNetworkEventHook( eIPCallbackEvent_t eNetworkEvent )
{

}


static void prvMiscInitialisation( void )
{
time_t xTimeNow;
uint32_t ulLoggingIPAddress;

	ulLoggingIPAddress = FreeRTOS_inet_addr_quick( configECHO_SERVER_ADDR0, configECHO_SERVER_ADDR1, configECHO_SERVER_ADDR2, configECHO_SERVER_ADDR3 );

	/* Seed the random number generator. */
	time( &xTimeNow );
	prvSRand( ( uint32_t ) xTimeNow );
}

const uint8_t test_buffer[] = { 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF };

#pragma GCC push_options
#pragma optimize("O0")
static void main_task(void * pvParameter) {
    FreeRTOS_Socket_t * xSocket;
    NetworkBufferDescriptor_t *xBuffer; 
    void *pxBuffer;
    TCPPacket_t *xTCPPacket;


    printf("\r\nStarted\r\n");

    // create a socket
    xSocket = (FreeRTOS_Socket_t *)FreeRTOS_socket( FREERTOS_AF_INET, FREERTOS_SOCK_STREAM, FREERTOS_IPPROTO_TCP );
    // create the TCP packet
    xTCPPacket = (TCPPacket_t *)pvPortMalloc(sizeof(TCPPacket_t));
    memcpy(&xTCPPacket->xIPHeader.ulDestinationIPAddress, ucIPAddress, 4);
    xTCPPacket->xTCPHeader.usDestinationPort = xSocket->usLocalPort;
    memcpy(&xTCPPacket->xIPHeader.ulSourceIPAddress, ucIPAddress, 4);
    xTCPPacket->xTCPHeader.usSourcePort = xSocket->usLocalPort;
    xTCPPacket->xTCPHeader.ucTCPOffset = 0;

    // create the buffer
    pxBuffer = pvPortMalloc(sizeof(NetworkBufferDescriptor_t));
    xBuffer = (NetworkBufferDescriptor_t *)pxBuffer;
    xBuffer->ulIPAddress = 0x11223344;
    xBuffer->pucEthernetBuffer = (void *)xTCPPacket;
    xBuffer->xDataLength = 34;
    xBuffer->usPort = 80;
    xBuffer->usBoundPort = 80;

    volatile uint32_t flip = 0;
    while (true)
    {   
        xBuffer->pucEthernetBuffer = (void *)xTCPPacket;
        if (flip == 0) {
            xTCPPacket->xTCPHeader.ucTCPOffset = 0xFF;
        } else {
            xTCPPacket->xTCPHeader.ucTCPOffset = 0;
        }

        int rc = prvCheckOptionsWrapper(xSocket, pxBuffer);

        printf("flip: %d, result: %d, offset: %08X, len: %d\r\n", flip, rc, xTCPPacket->xTCPHeader.ucTCPOffset, xBuffer->xDataLength);


        flip ^= 1;
        vTaskDelay(1000);
    }
}

void
hp_manager_task(void *parameters) {

    uint32_t identifier = 0;
    printf("Starting Kintsugi Hotpatch Manager Task\r\n");
    nrf_delay_ms(1000);

    hp_manager(HOTPATCH_CODE, sizeof(HOTPATCH_CODE), &identifier);

    while (1) {
        vTaskDelay(10);
    }
    vTaskDelete(NULL);
}

#pragma GCC pop_options
/**
 * @brief Function for main application entry.
 */
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

    prvMiscInitialisation();
    DEBUG_LOG("\r\nCVE-2018-16524\r\n");

	//printf("IP Init: %d\r\n", FreeRTOS_IPInit( ucIPAddress, ucNetMask, ucGatewayAddress, ucDNSServerAddress, ucMACAddress ));

    printf("Task Main: %d\r\n", xTaskCreate(main_task, "MAIN", configMINIMAL_STACK_SIZE, NULL, 2, &main_task_handle));
    printf("Task Manager: %d\r\n", xTaskCreate(hp_manager_task, configHP_TASK_NAME, configMINIMAL_STACK_SIZE, NULL, 1, &hp_manager_task_handle));
    vTaskStartScheduler();
    
    //prvCheckOptionsWrapper(0, 0);
}


/** @} */

