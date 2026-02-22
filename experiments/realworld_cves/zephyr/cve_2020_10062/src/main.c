/*
 * Copyright (c) 2016 Intel Corporation.
 * Copyright (c) 2019-2020 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <mqtt_internal.h>

#include <stdio.h>

#include "hp_code_data.h"


LOG_MODULE_REGISTER(main);

void
hp_manager_task(void *parameters) {

    uint32_t identifier = 0;
    printf("Starting Kintsugi Hotpatch Manager Task\r\n");

    hp_manager(HOTPATCH_CODE, sizeof(HOTPATCH_CODE), &identifier);

    while (1) {
        k_sleep(K_MSEC(10));
    }
}


int main_task(void)
{
	/*
	k_sched_lock();
	for (int i = 0; i < 10000; i++) {
		hotpatch_measurement_encapsulation();
	}
	k_sched_unlock();
	*/
	for (int i = 0; i < 10; i++) {
		int rc;
		uint8_t flags;
		uint32_t length;

		uint8_t corrupted_pkt_len[] = {0x30, 0xff, 0xff, 0xff, 0xff, 0x01};
		struct buf_ctx corrupted_pkt_len_buf = {
			.cur = corrupted_pkt_len,
			.end = corrupted_pkt_len + sizeof(corrupted_pkt_len)
		};
		rc = fixed_header_decode(&corrupted_pkt_len_buf, &flags, &length);
		printk("%d - Result: %08X\r\n", i, rc);
		k_msleep(1000);
	}

	while (1) {
		k_msleep(1000);
	}
}




#define STACKSIZE 512
#define PRIORITY  2
K_THREAD_DEFINE(main_id, STACKSIZE, 
				main_task, NULL, NULL, NULL,
				PRIORITY, 0, 0);

#define STACKSIZE (512 * 4)
#define PRIORITY  CONFIG_NUM_PREEMPT_PRIORITIES - 1
K_THREAD_DEFINE(HP_TASK, STACKSIZE, hp_manager_task, NULL, NULL, NULL, PRIORITY, 0, 0);