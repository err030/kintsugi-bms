# Kintsugi Integration Guide for `Zephyr`

In the following, we present the path where each file is integrated. This is particular for Zephyr:
- `init.c` => `zephyr/kernel/init.c`.
- `swap.c` => `zephyr/arch/arm/core/cortex_m/swap.c`.
- `thread.h` => `zephyr/include/zephyr/kernel/thread.h`.
- `thread.c` => `zephyr/kernel/thread.c`.