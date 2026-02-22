
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
#include <string.h>
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
#include "hp_manager.h"
#include "hp_config.h"

#define MAX_TEST_DATA_BYTES     (15U)                
#define UART_TX_BUF_SIZE 2048                         
#define UART_RX_BUF_SIZE 2048                         
#define UART_HWFC APP_UART_FLOW_CONTROL_DISABLED
#define ENABLE_BMS_THRESHOLD_ATTACK 0
#define ENABLE_BMS_CALIB_ATTACK 0
#define ENABLE_HOTPATCH_CODE_ATTACK 0
#define ENABLE_UART_RX_ATTACK 1

#define BMS_UART_PREAMBLE 0xAA
#define BMS_UART_MAX_PAYLOAD 64
#define BMS_CMD_WRITEALL 0x02
#define BMS_CMD_WRITEDEVICE 0x04
#define BMS_CMD_SET_THRESH BMS_CMD_WRITEALL

#define BMS_REG_STATE_VOLT 0x20
#define BMS_REG_STATE_CURR 0x21
#define BMS_REG_STATE_TEMP 0x22
#define BMS_REG_CALIB_VOFF 0x30
#define BMS_REG_CALIB_IGAIN 0x31
#define BMS_REG_CALIB_TOFF 0x32

typedef struct {
    float pack_voltage;    
    float pack_current;    
    float pack_temp;       
    float soc;             
    float soh;             
} bms_state_t;

typedef struct {
    bool  ovp;     
    bool  uvp;     
    bool  ocp;     
    bool  otp;     
    bool  utp;     
} bms_fault_flags_t;

// BMS 关键阈值
typedef struct {
    float ovp;
    float uvp;
    float ocp;
    float otp;
    float utp;
} bms_thresholds_t;

typedef struct {
    float voltage_offset;
    float current_gain;
    float temp_offset;
} bms_calibration_t;

//全局状态
static bms_state_t       g_bms_state;
static bms_fault_flags_t g_bms_faults; 
volatile bms_thresholds_t  g_bms_thresholds __attribute__((used, section(".data.g_bms_thresh"), aligned(4))) = {
    .ovp = 420.0f,
    .uvp = 300.0f,
    .ocp = 80.0f,
    .otp = 60.0f,
    .utp = 0.0f,
};
static bms_calibration_t g_bms_calibration = {
    .voltage_offset = 0.0f,
    .current_gain = 1.0f,
    .temp_offset = 0.0f,
};
static uint8_t g_bms_last_seq;

//传感器状态
static void simulate_pack_voltage_current_temp(bms_state_t * s);

void bms_uart_rx_task(void *pv) __attribute__((used));

//Monitoring
static void bms_monitor_task(void *pv) {
    (void)pv;
    for (;;) {
        simulate_pack_voltage_current_temp(&g_bms_state);

        printf("[BMS][MON] V=%.1fV I=%.1fA T=%.1fC\r\n",
               g_bms_state.pack_voltage,
               g_bms_state.pack_current,
               g_bms_state.pack_temp);

        vTaskDelay(pdMS_TO_TICKS(100));  
    }
}

//Estimation - 简化版库伦计数+线形退化
//soc根据电流积分更新 soh每过一段时间略微下降，模拟容量衰减
static void bms_estimation_task(void *pv) {
    (void)pv;
    const float nominal_capacity_Ah = 50.0f;     
    const float dt_s = 0.1f;                    
    for (;;) {
        float i = g_bms_state.pack_current;     
        float delta_soc = -(i * dt_s) / (nominal_capacity_Ah * 3600.0f) * 100.0f;
        g_bms_state.soc += delta_soc;

        if (g_bms_state.soc > 100.0f) g_bms_state.soc = 100.0f;
        if (g_bms_state.soc < 0.0f)   g_bms_state.soc = 0.0f;

        static float cycle_counter = 0.0f;
        cycle_counter += dt_s;
        if (cycle_counter > 60.0f) {
            cycle_counter = 0.0f;
            g_bms_state.soh -= 0.01f;   
            if (g_bms_state.soh < 80.0f) {
                g_bms_state.soh = 80.0f;
            }
        }

        printf("[BMS][EST] SoC=%.2f%% SoH=%.2f%%\r\n",
               g_bms_state.soc,
               g_bms_state.soh);

        vTaskDelay(pdMS_TO_TICKS(100)); // 和 monitor 同步
    }
}

//Protection
static void bms_protection_task(void *pv) {
    (void)pv;
    for (;;) {
        float v = g_bms_state.pack_voltage;
        float i = g_bms_state.pack_current;
        float t = g_bms_state.pack_temp;

        // 简单的阈值比较
        g_bms_faults.ovp = (v > g_bms_thresholds.ovp);
        g_bms_faults.uvp = (v < g_bms_thresholds.uvp);
        g_bms_faults.ocp = (i > g_bms_thresholds.ocp);
        g_bms_faults.otp = (t > g_bms_thresholds.otp);
        g_bms_faults.utp = (t < g_bms_thresholds.utp);

        if (g_bms_faults.ovp || g_bms_faults.uvp ||
            g_bms_faults.ocp || g_bms_faults.otp || g_bms_faults.utp) {

            printf("[BMS][PROT] FAULT! V=%.1f I=%.1f T=%.1f"
                   " (OVP=%d UVP=%d OCP=%d OTP=%d UTP=%d)\r\n",
                   v, i, t,
                   g_bms_faults.ovp,
                   g_bms_faults.uvp,
                   g_bms_faults.ocp,
                   g_bms_faults.otp,
                   g_bms_faults.utp);

        }

        vTaskDelay(pdMS_TO_TICKS(50)); 
    }
}

//Communication - 虚拟CAN帧
static void bms_comm_task(void *pv) {
    (void)pv;
    for (;;) {
        printf("[BMS][COMM] TX frame: V=%.1f SoC=%.1f%% SoH=%.1f%% FAULT=%d\r\n",
               g_bms_state.pack_voltage,
               g_bms_state.soc,
               g_bms_state.soh,
               (int)(g_bms_faults.ovp || g_bms_faults.uvp ||
                     g_bms_faults.ocp || g_bms_faults.otp ||
                     g_bms_faults.utp));
        vTaskDelay(pdMS_TO_TICKS(500)); 
    }
}

static uint8_t bms_crc8_mxm(const uint8_t *data, uint8_t len) {
    static const uint8_t table[256] = {
        0x00u, 0x3Eu, 0x7Cu, 0x42u, 0xF8u, 0xC6u, 0x84u, 0xBAu, 0x95u, 0xABu, 0xE9u, 0xD7u, 0x6Du, 0x53u,
        0x11u, 0x2Fu, 0x4Fu, 0x71u, 0x33u, 0x0Du, 0xB7u, 0x89u, 0xCBu, 0xF5u, 0xDAu, 0xE4u, 0xA6u, 0x98u,
        0x22u, 0x1Cu, 0x5Eu, 0x60u, 0x9Eu, 0xA0u, 0xE2u, 0xDCu, 0x66u, 0x58u, 0x1Au, 0x24u, 0x0Bu, 0x35u,
        0x77u, 0x49u, 0xF3u, 0xCDu, 0x8Fu, 0xB1u, 0xD1u, 0xEFu, 0xADu, 0x93u, 0x29u, 0x17u, 0x55u, 0x6Bu,
        0x44u, 0x7Au, 0x38u, 0x06u, 0xBCu, 0x82u, 0xC0u, 0xFEu, 0x59u, 0x67u, 0x25u, 0x1Bu, 0xA1u, 0x9Fu,
        0xDDu, 0xE3u, 0xCCu, 0xF2u, 0xB0u, 0x8Eu, 0x34u, 0x0Au, 0x48u, 0x76u, 0x16u, 0x28u, 0x6Au, 0x54u,
        0xEEu, 0xD0u, 0x92u, 0xACu, 0x83u, 0xBDu, 0xFFu, 0xC1u, 0x7Bu, 0x45u, 0x07u, 0x39u, 0xC7u, 0xF9u,
        0xBBu, 0x85u, 0x3Fu, 0x01u, 0x43u, 0x7Du, 0x52u, 0x6Cu, 0x2Eu, 0x10u, 0xAAu, 0x94u, 0xD6u, 0xE8u,
        0x88u, 0xB6u, 0xF4u, 0xCAu, 0x70u, 0x4Eu, 0x0Cu, 0x32u, 0x1Du, 0x23u, 0x61u, 0x5Fu, 0xE5u, 0xDBu,
        0x99u, 0xA7u, 0xB2u, 0x8Cu, 0xCEu, 0xF0u, 0x4Au, 0x74u, 0x36u, 0x08u, 0x27u, 0x19u, 0x5Bu, 0x65u,
        0xDFu, 0xE1u, 0xA3u, 0x9Du, 0xFDu, 0xC3u, 0x81u, 0xBFu, 0x05u, 0x3Bu, 0x79u, 0x47u, 0x68u, 0x56u,
        0x14u, 0x2Au, 0x90u, 0xAEu, 0xECu, 0xD2u, 0x2Cu, 0x12u, 0x50u, 0x6Eu, 0xD4u, 0xEAu, 0xA8u, 0x96u,
        0xB9u, 0x87u, 0xC5u, 0xFBu, 0x41u, 0x7Fu, 0x3Du, 0x03u, 0x63u, 0x5Du, 0x1Fu, 0x21u, 0x9Bu, 0xA5u,
        0xE7u, 0xD9u, 0xF6u, 0xC8u, 0x8Au, 0xB4u, 0x0Eu, 0x30u, 0x72u, 0x4Cu, 0xEBu, 0xD5u, 0x97u, 0xA9u,
        0x13u, 0x2Du, 0x6Fu, 0x51u, 0x7Eu, 0x40u, 0x02u, 0x3Cu, 0x86u, 0xB8u, 0xFAu, 0xC4u, 0xA4u, 0x9Au,
        0xD8u, 0xE6u, 0x5Cu, 0x62u, 0x20u, 0x1Eu, 0x31u, 0x0Fu, 0x4Du, 0x73u, 0xC9u, 0xF7u, 0xB5u, 0x8Bu,
        0x75u, 0x4Bu, 0x09u, 0x37u, 0x8Du, 0xB3u, 0xF1u, 0xCFu, 0xE0u, 0xDEu, 0x9Cu, 0xA2u, 0x18u, 0x26u,
        0x64u, 0x5Au, 0x3Au, 0x04u, 0x46u, 0x78u, 0xC2u, 0xFCu, 0xBEu, 0x80u, 0xAFu, 0x91u, 0xD3u, 0xEDu,
        0x57u, 0x69u, 0x2Bu, 0x15u,
    };
    uint8_t crc = 0;
    while (len > 0) {
        crc = table[*data ^ crc];
        data++;
        len--;
    }
    return crc;
}

__attribute__((used))
static void bms_uart_apply_thresholds_unsafe(const uint8_t *payload, uint8_t payload_len) {
    printf("[BMS-RX] CMD=WRITEALL len=%u (expected %u)\r\n",
           payload_len, (unsigned)sizeof(bms_thresholds_t));
    memcpy((void *)&g_bms_thresholds, payload, payload_len);
    printf("[BMS-RX] Thresholds now: OVP=%.1f UVP=%.1f OCP=%.1f OTP=%.1f UTP=%.1f\r\n",
           g_bms_thresholds.ovp, g_bms_thresholds.uvp,
           g_bms_thresholds.ocp, g_bms_thresholds.otp,
           g_bms_thresholds.utp);
}

__attribute__((used))
static void bms_uart_apply_write_device(const uint8_t *payload, uint8_t payload_len) {
    if (payload_len < 4) {
        printf("[BMS-RX] WRITEDEVICE short len=%u\r\n", payload_len);
        return;
    }

    uint8_t reg = payload[0];
    uint8_t lsb = payload[1];
    uint8_t msb = payload[2];
    uint8_t crc = payload[3];
    uint8_t seq = (payload_len > 4) ? payload[4] : 0xFFu;

    uint8_t crc_data[4] = {BMS_CMD_WRITEDEVICE, reg, lsb, msb};
    uint8_t crc_calc = bms_crc8_mxm(crc_data, 4);
    if (crc_calc != crc) {
        printf("[BMS-RX] WRITEDEVICE bad CRC calc=0x%02X got=0x%02X\r\n", crc_calc, crc);
        return;
    }

    if (payload_len > 4) {
        if (seq == g_bms_last_seq) {
            printf("[BMS-RX] WRITEDEVICE replay seq=%u (no anti-replay)\r\n", seq);
        }
        g_bms_last_seq = seq;
    }

    uint16_t raw_u = (uint16_t)lsb | ((uint16_t)msb << 8);
    int16_t raw = (int16_t)raw_u;

    switch (reg) {
        case BMS_REG_STATE_VOLT:
            g_bms_state.pack_voltage = (float)raw / 10.0f;
            printf("[BMS-RX] STATE pack_voltage=%.1fV\r\n", g_bms_state.pack_voltage);
            break;
        case BMS_REG_STATE_CURR:
            g_bms_state.pack_current = (float)raw / 10.0f;
            printf("[BMS-RX] STATE pack_current=%.1fA\r\n", g_bms_state.pack_current);
            break;
        case BMS_REG_STATE_TEMP:
            g_bms_state.pack_temp = (float)raw / 10.0f;
            printf("[BMS-RX] STATE pack_temp=%.1fC\r\n", g_bms_state.pack_temp);
            break;
        case BMS_REG_CALIB_VOFF:
            g_bms_calibration.voltage_offset = (float)raw / 10.0f;
            printf("[BMS-RX] CALIB voltage_offset=%.1fV\r\n", g_bms_calibration.voltage_offset);
            break;
        case BMS_REG_CALIB_IGAIN:
            g_bms_calibration.current_gain = (float)raw / 100.0f;
            printf("[BMS-RX] CALIB current_gain=%.2f\r\n", g_bms_calibration.current_gain);
            break;
        case BMS_REG_CALIB_TOFF:
            g_bms_calibration.temp_offset = (float)raw / 10.0f;
            printf("[BMS-RX] CALIB temp_offset=%.1fC\r\n", g_bms_calibration.temp_offset);
            break;
        default:
            printf("[BMS-RX] WRITEDEVICE unknown reg=0x%02X raw=0x%04X\r\n", reg, raw_u);
            break;
    }
}

__attribute__((used))
static void bms_uart_handle_frame(uint8_t *frame, uint8_t frame_len) {
    if (frame_len < 1) { printf("[BMS-RX] Drop empty frame\r\n"); return; }
    uint8_t cmd = frame[0];
    uint8_t *payload = &frame[1];
    uint8_t payload_len = frame_len - 1;
    switch (cmd) {
        case BMS_CMD_WRITEALL:
            bms_uart_apply_thresholds_unsafe(payload, payload_len);
            break;
        case BMS_CMD_WRITEDEVICE:
            bms_uart_apply_write_device(payload, payload_len);
            break;
        default:
            printf("[BMS-RX] Unknown cmd=0x%02X len=%u\r\n", cmd, payload_len);
            break;
    }
}

__attribute__((used))
void bms_uart_rx_task(void *pv) {
    (void)pv;
    printf("[BMS-RX] task online\r\n");
    uint8_t frame[BMS_UART_MAX_PAYLOAD];
    uint8_t frame_len = 0;
    uint8_t idx = 0;
    uint8_t checksum = 0;
    enum { RX_WAIT_PREAMBLE=0, RX_WAIT_LEN, RX_WAIT_DATA, RX_WAIT_CHECKSUM } state = RX_WAIT_PREAMBLE;
    for (;;) {
        uint8_t byte;
        if (app_uart_get(&byte) != NRF_SUCCESS) { vTaskDelay(pdMS_TO_TICKS(20)); continue; }
        switch (state) {
            case RX_WAIT_PREAMBLE: if (byte == BMS_UART_PREAMBLE) state = RX_WAIT_LEN; break;
            case RX_WAIT_LEN: frame_len = byte; idx=0; checksum=0; if (frame_len==0 || frame_len> BMS_UART_MAX_PAYLOAD) { printf("[BMS-RX] Drop length=%u\r\n", frame_len); state = RX_WAIT_PREAMBLE; } else { state = RX_WAIT_DATA; } break;
            case RX_WAIT_DATA: frame[idx++] = byte; checksum = (uint8_t)(checksum + byte); if (idx>=frame_len) state = RX_WAIT_CHECKSUM; break;
            case RX_WAIT_CHECKSUM: if (checksum == byte) { bms_uart_handle_frame(frame, frame_len); } else { printf("[BMS-RX] Bad checksum calc=0x%02X got=0x%02X\r\n", checksum, byte); } state = RX_WAIT_PREAMBLE; break;
            default: state = RX_WAIT_PREAMBLE; break;
        }
    }
}


//模拟传感器
static void simulate_pack_voltage_current_temp(bms_state_t * s) {
    static bool init = false;
    static float raw_v = 0.0f;
    static float raw_i = 0.0f;
    static float raw_t = 0.0f;

    if (!init) {
        raw_v = s->pack_voltage;
        raw_i = s->pack_current;
        raw_t = s->pack_temp;
        init = true;
    }

    //电压
    raw_v += 0.5f;
    if (raw_v > 430.0f) {
        raw_v = 340.0f;
    }

    //电流
    raw_i += 0.2f;
    if (raw_i > 90.0f) {
        raw_i = -10.0f;
    }
    //温度
    raw_t += 0.1f;
    if (raw_t > 65.0f) {
        raw_t = -5.0f;
    }

    s->pack_voltage = raw_v + g_bms_calibration.voltage_offset;
    s->pack_current = raw_i * g_bms_calibration.current_gain;
    s->pack_temp = raw_t + g_bms_calibration.temp_offset;
}

//kintsigi原始代码
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

void
__attribute__((optimize("O0")))
malicious_task(void* param) { 
    /*
     * This task tries to modify a hotpatch that has been stored in memory
     */
    volatile uint32_t data;
    (void)param;  
    (void)data;   
    for (uint32_t i = 0; i < 3; i++) {
        printf("Waiting...\r\n");
        vTaskDelay(1000);
    }

    while (true) {
        printf("Attacking!\r\n");
        vTaskDelay(2000);
    }
}

uint32_t
__ramfunc
__attribute__((noinline, used, optimize("O0"), aligned(8)))
target_ram_function() {
    volatile uint32_t result;
    result = 0;
    __asm volatile( "nop\n"
                    "nop\n"
                    "nop\n"
                    "nop\n");
    return result;
}

volatile uint32_t k = 0;
void workload_task(void *param) {
    (void)param; 
    while (true) {
        for (uint32_t i = 0; i < 100000; i++) {
            k += i;
        }
        printf("Workload Task running, k=%u\r\n", k);
        vTaskDelay(1000);
    }
}


#define HP_SIZE (sizeof(struct hp_header) + 20)
volatile uint8_t hotpatch_code[1 * HP_SIZE] = { 0 };

void reset_hotpatch(void) {
     
    volatile struct hp_header *hotpatch_header;
    hotpatch_header = (struct hp_header*)((uint32_t)(&hotpatch_code));
    hotpatch_header->type = HP_TYPE_REPLACEMENT;
    hotpatch_header->target_address = (uint32_t)&target_ram_function;
    hotpatch_header->code_size = 4;
    hotpatch_header->code_ptr = (uint8_t*)(NULL);
    (void)hotpatch_header;  // Suppress unused variable warning
}

void parse_result(enum hp_manager_result manager_result) {
    if (manager_result != HP_MANAGER_SUCCESS) {
        printf("\t=> [Success]: Obtained error code: %d\r\n", manager_result);
    } else {
        printf("\t=> [Failure]: Manager did not validate the hotpatch correctly.\r\n");
    }
    printf("\r\n");
}

void
task_hp_manager(void *parameters) {
    volatile struct hp_header *hotpatch_header;
    enum hp_manager_result manager_result;
    uint32_t identifier = 0;
    (void)parameters;  
    printf("[MANAGER] Task started!\r\n");
    printf("Starting Hotpatch Task\r\n");

    /*
     * invalid hotpatch type
     * ---------------------
     * the manager must reject the hotpatch because the provided hotpatch type is not supported.
     */
    printf("[ Invalid Hotpatch Type ]\r\n");
    reset_hotpatch();
    hotpatch_header = (struct hp_header*)((uint32_t)(&hotpatch_code));
    hotpatch_header->type = 5;
    manager_result = hp_manager(hotpatch_code, sizeof(hotpatch_code), &identifier);
    parse_result(manager_result);

    /*
     * invalid target address
     * ----------------------
     * the manager must reject the hotpatch because the target address (workload_task) is not a valid patchable address.
     */
    printf("[ Invalid Target Address ]\r\n");
    reset_hotpatch();
    hotpatch_header = (struct hp_header*)((uint32_t)(&hotpatch_code));
    hotpatch_header->target_address = (uint32_t)&workload_task;
    manager_result = hp_manager(hotpatch_code, sizeof(hotpatch_code), &identifier);
    parse_result(manager_result);

    /*
     * invalid size
     * -----------------
     * the manager must reject the hotpatch because the size of the hotpatch exceeds the allowed limit.
     */
    printf("[ Invalid Code Size ]\r\n");
    reset_hotpatch();
    hotpatch_header = (struct hp_header*)((uint32_t)(&hotpatch_code));
    hotpatch_header->type = HP_TYPE_REDIRECT;
    hotpatch_header->code_size = HP_MAX_CODE_SIZE + 1;
    manager_result = hp_manager(hotpatch_code, sizeof(struct hp_header) + HP_MAX_CODE_SIZE + 1, &identifier);
    parse_result(manager_result);

    while (1) {
        vTaskDelay(10);
    }
    vTaskDelete(NULL);
}

#define WORK_TASKS  1
TaskHandle_t malicious_task_handle;
TaskHandle_t workload_task_handle[WORK_TASKS];
TaskHandle_t hp_manager_task_handle;


uint8_t hotpatch_code_bytes[8] = { 0 };

int main(void)
{
    //1. 初始化
    hp_manager_init();

    hp_mpu_init();

    ret_code_t err_code;
    err_code = nrf_drv_clock_init();
    APP_ERROR_CHECK(err_code);
    nrf_drv_clock_lfclk_request(NULL);

    //2 日志
    APP_ERROR_CHECK(NRF_LOG_INIT(NULL));
    NRF_LOG_DEFAULT_BACKENDS_INIT();
    //3. UART
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

    printf("[BMS-DEMO] Firmware booted. \r\n");
    //4. 初始化 BMS 全局状态
    g_bms_state.pack_voltage = 350.0f;
    g_bms_state.pack_current = 10.0f;
    g_bms_state.pack_temp    = 25.0f;
    g_bms_state.soc          = 80.0f;
    g_bms_state.soh          = 100.0f;
    memset(&g_bms_faults, 0, sizeof(g_bms_faults));

    //5. 创建 BMS 相关任务
    BaseType_t res;

    res = xTaskCreate(bms_monitor_task,
                      "BMS_MON",
                      configMINIMAL_STACK_SIZE + 128,
                      NULL,
                      2,
                      NULL);
    printf("BMS Monitor Task: %ld\r\n", (long)res);

    res = xTaskCreate(bms_estimation_task,
                      "BMS_EST",
                      configMINIMAL_STACK_SIZE + 128,
                      NULL,
                      2,
                      NULL);
    printf("BMS Estimation Task: %ld\r\n", (long)res);

    res = xTaskCreate(bms_protection_task,
                      "BMS_PROT",
                      configMINIMAL_STACK_SIZE + 128,
                      NULL,
                      3,      
                      NULL);
    printf("BMS Protection Task: %ld\r\n", (long)res);

    res = xTaskCreate(bms_comm_task,
                      "BMS_COMM",
                      configMINIMAL_STACK_SIZE + 128,
                      NULL,
                      1,
                      NULL);
    printf("BMS Comm Task: %ld\r\n", (long)res);

#if ENABLE_UART_RX_ATTACK
    printf("Task BMS_UART_RX: %ld\r\n",
           (long)xTaskCreate(bms_uart_rx_task,
                             "BMS_UART_RX",
                             configMINIMAL_STACK_SIZE + 256,
                             NULL,
                             4,
                             NULL));
#endif


    //6. 创建 Kintsugi 管理任务
    res = xTaskCreate(task_hp_manager, 
        configHP_TASK_NAME, 
        configMINIMAL_STACK_SIZE, 
        NULL, 
        1, 
        &hp_manager_task_handle); 
    printf("HP Manager Task: %ld\r\n", (long)res); 
    
    //7. 启动调度器
    vTaskStartScheduler();
    
    // vTaskStartScheduler() never returns
    return 0;
}
