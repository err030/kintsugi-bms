#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/shell/shell.h>
#include <zephyr/shell/shell_dummy.h>
#include <zephyr/random/rand32.h>
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

	while(1) {
		char str1[] = "aabaaaa  c";
		char exp1[] = "aabaaaa c";
		char str2[] = "aab  aa   aa  c";
		char exp2[] = "aab aa aa c";
		int rv;

		printk("Start\r\n");

		int line = 0;
		z_shell_spaces_trim(str1);
		printk("%s | %s\r\n", str1, exp1);
		rv = strcmp(str1, exp1);
		if (rv != 0) {
			printk("%s => %s\n", str1, exp1);
			printk("%d - %s\n", rv, "Unexepected value");
			line = 1;
		}

		z_shell_spaces_trim(str2);
		printk("%s | %s\r\n", str2, exp2);
		rv = strcmp(str2, exp2);
		if (rv != 0) {

			printk("%s => %s\n", str2, exp2);
			printk("%d - %s\n", rv, "Unexepected value");
			line = 1;
		}

		if (line == 1) {
			printk("\n----------------------\n");
		}
		k_msleep(5000);
	}
	return 0;
}


#define STACKSIZE 2028
#define PRIORITY  -2
K_THREAD_DEFINE(main_id, STACKSIZE, 
				main_task, NULL, NULL, NULL,
				PRIORITY, 0, 0);

				#define STACKSIZE (512 * 4)
#define PRIORITY  CONFIG_NUM_PREEMPT_PRIORITIES - 1
K_THREAD_DEFINE(HP_TASK, STACKSIZE, hp_manager_task, NULL, NULL, NULL, PRIORITY, 0, 0);