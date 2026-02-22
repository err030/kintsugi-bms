// CVE-2020-10024
#pragma GCC optimize ("O0")
HOTPATCH_FUNCTION_START_NAKED(_do_syscall, 0xE, replacement, 0) {
	__asm__ volatile(
		".short 0xD302\n"
	);
}
#pragma GCC