/*
 * Copyright (c) 2016 Intel Corporation.
 * Copyright (c) 2019-2020 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/coap.h>
#include <stdio.h>
#include "hp_code_data.h"


LOG_MODULE_REGISTER(main);

#define STACKSIZE (256 + 4096)
#define PRIORITY  -2
static K_THREAD_STACK_DEFINE(dyn_thread_stack, STACKSIZE);
static struct k_thread *dyn_thread;

// len + opt_len -> overflow
// 0x0E => 0: delta, E: len
uint8_t vuln_len_opt_len_overflow[] = {
	0x00, 0x00, 0x00, 0x00, 0x0E, 0xFE, 0xF2, 0x01, 0x00
};

// delta + opt_delta -> overflow
// 0xE0 => E: delta, 0: len
uint8_t vuln_delta_opt_delta_overflow[] = {
	0x00, 0x00, 0x00, 0x00, 0xE0, 0xFE, 0xF2, 0x10, 0x00
};

void
hp_manager_task(void *parameters) {

    uint32_t identifier = 0;
    printf("Starting Kintsugi Hotpatch Manager Task\r\n");

    hp_manager(HOTPATCH_CODE, sizeof(HOTPATCH_CODE), &identifier);

    while (1) {
        k_sleep(K_MSEC(10));
    }
}

unsigned char testcase[] = {
	0, 0, 0, 0,
	0x0E, /* delta = 0, length = 14 */
	0xFE, 0xF2, /* First option */
	0x10 /* More data following the option to skip the "if (r == 0) {" case */
};

static void main_task(void) {
	int ret;
	k_msleep(1000);
	for (int i = 0; i < 10; i++) {
		struct coap_packet pkt;

		//ret = coap_packet_parse(&pkt, vuln_len_opt_len_overflow, sizeof(vuln_len_opt_len_overflow), NULL, 0);
		//printk("Result: %08X\r\n", ret);
	 	ret = coap_packet_parse(&pkt, vuln_delta_opt_delta_overflow, sizeof(vuln_delta_opt_delta_overflow), NULL, 0);
		printk("Result: %08X\r\n", ret);

		k_msleep(100);
	}
}

K_THREAD_DEFINE(main_id, STACKSIZE, 
				main_task, NULL, NULL, NULL,
				PRIORITY, 0, 0);


#define STACKSIZE (512 * 4)
#define PRIORITY  CONFIG_NUM_PREEMPT_PRIORITIES - 1
K_THREAD_DEFINE(HP_TASK, STACKSIZE, hp_manager_task, NULL, NULL, NULL, PRIORITY, 0, 0);