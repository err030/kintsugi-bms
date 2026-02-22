/*
 * Copyright (c) 2016 Intel Corporation.
 * Copyright (c) 2019-2020 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/internal/syscall_handler.h>
#include <zephyr/app_memory/app_memdomain.h>
#include <zephyr/sys/util.h>
#include <zephyr/kernel_structs.h>

#include <stdio.h>
#include "hp_code_data.h"



LOG_MODULE_REGISTER(main);


K_APPMEM_PARTITION_DEFINE(user_partition);
K_APP_DMEM(user_partition) unsigned int expect_fault = false;
K_APP_DMEM(user_partition) unsigned int expected_reason = 0;

void clear_fault(void)
{
	expect_fault = false;
	expected_reason = 0;
}

void set_fault(unsigned int reason)
{
	expect_fault = true;
	expected_reason = reason;
}

void k_sys_fatal_error_handler(unsigned int reason, const z_arch_esf_t *pEsf)
{
	printk("Caught system error -- reason %d\n", reason);

	if (expect_fault) {
		if (expected_reason == reason) {
			printk("System error was expected\n");
			clear_fault();
		} else {
			printk("Wrong fault reason, expecting %d\n",
			       expected_reason);
			clear_fault();
		}
	} else {
		printk("Unexpected fault during test\n");
		clear_fault();
	}
}

void __attribute__((optimize("O0"))) thread_uint_max_fault(void *p1, void *p2, void *p3)
{
	set_fault(K_ERR_KERNEL_OOPS);
	int call_id = UINT_MAX;
	int result = arch_syscall_invoke0(call_id);
}

void
hp_manager_task(void *parameters) {

    uint32_t identifier = 0;
    printk("Starting Kintsugi Hotpatch Manager Task\r\n");

    hp_manager(HOTPATCH_CODE, sizeof(HOTPATCH_CODE), &identifier);

    while (1) {
		k_msleep(50);
    }
}



#define THREAD_STACKSIZE (512)

K_THREAD_STACK_DEFINE(dyn_thread_stack, THREAD_STACKSIZE);
struct k_thread dyn_thread;

void create_dynamic_thread()
{
	k_tid_t tid;


	tid = k_thread_create(&dyn_thread, dyn_thread_stack, THREAD_STACKSIZE,
			      &thread_uint_max_fault, NULL, NULL, NULL,
			    	CONFIG_NUM_PREEMPT_PRIORITIES - 2, K_USER, K_NO_WAIT);
	k_thread_join(&dyn_thread, K_FOREVER);
}

int main_task(void) {

    k_mem_domain_add_partition(&k_mem_domain_default, &user_partition);

	k_thread_system_pool_assign(k_current_get());
	
	while (true) {
		clear_fault();
		create_dynamic_thread();
		k_msleep(1000);
	}
	return 0;
}

K_THREAD_DEFINE(main_id, 2028, 
				main_task, NULL, NULL, NULL,
				-2, 0, 0);

#define STACKSIZE (512 * 4)
#define PRIORITY  CONFIG_NUM_PREEMPT_PRIORITIES - 1
K_THREAD_DEFINE(HP_TASK, STACKSIZE, hp_manager_task, NULL, NULL, NULL, PRIORITY, 0, 0);