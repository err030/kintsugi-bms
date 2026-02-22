# Kintsugi Experiments: Hotpatching Real-World CVEs (C5)
---

In these experiments, we demonstrate Kintsugi's ability to hotpatch real-world CVEs, as described in *Section 6.4* in the paper. To accomplish this, we considered 10 CVEs that affect Zephyr, FreeRTOS, mbedTLS, and AMNESIA:33. We provide details on each CVE below, showing the expected behavior. The corresponding source for each hotpatch can be found in the `hotpatches` directory in the main folder.

How to perform measurements:
1. Connect to UART of the board using, for instance, `screen /dev/ttyACM0 115200`.
2. Run the experiment script `bash ./run.sh`.
3. Select a CVE to run (1 to 10).
4. Compare UART output to expected output listed below (*Output could vary slightly*). 

*Note: MbedTLS and AMNESIA:33 CVEs are implemented under FreeRTOS*

## Zephyr
---

#### CVE-2020-10021
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-10021)
- Hotpatch: `hotpatches/zephyr/cve_2020_10021.c` ([Source](../../hotpatches/zephyr/cve_2020_10021.c))

**Expected Output:**
```
*** Booting Zephyr OS build v3.7.0-1377-ge60da1bd640a ***
[00:00:00.429,473] <inf> flashdisk: Initialize device NAND
[00:00:00.429,504] <inf> flashdisk: offset 0, sector size 512, page size 4096, volume size 131072
[00:00:00.429,718] <inf> main: CVE-2020-10021

Area 0 at 0x0 on mx25r6435f@0 for 131072 bytes
[00:00:00.429,779] <inf> main: No file system selected
[00:00:00.429,870] <inf> main: The device is put in USB mass storage mode.

Starting Kintsugi Hotpatch Manager Task
Address &fail: 000029A1
[00:00:02.003,540] <err> usb_msc: usb write failure
[00:00:02.007,354] <err> usb_msc: usb write failure
[00:00:02.009,521] <err> usb_msc: usb write failure
[00:00:02.010,650] <err> usb_msc: usb write failure
[00:00:02.011,779] <err> usb_msc: usb write failure
[00:00:02.012,847] <err> usb_msc: usb write failure
[00:00:02.013,916] <err> usb_msc: usb write failure
[00:00:02.015,136] <err> usb_msc: usb write failure
[00:00:02.016,357] <err> usb_msc: usb write failure
[00:00:02.017,486] <err> usb_msc: usb write failure
[00:00:02.018,524] <err> usb_msc: usb write failure
[00:00:02.019,622] <err> usb_msc: usb write failure
[00:00:02.020,721] <err> usb_msc: usb write failure
[00:00:02.021,636] <err> usb_msc: usb write failure
[00:00:02.176,818] <err> usb_msc: usb write failure
[00:00:02.185,943] <err> usb_msc: usb write failure
[00:00:02.186,859] <err> usb_msc: usb write failure
[00:00:02.187,713] <err> usb_msc: usb write failure
[00:00:02.188,659] <err> usb_msc: usb write failure
[00:00:02.189,727] <err> usb_msc: usb write failure
[00:00:02.190,643] <err> usb_msc: usb write failure
[00:00:02.342,681] <err> usb_msc: usb write failure
```

#### CVE-2020-10023
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-10023)
- Hotpatch: `hotpatches/zephyr/cve_2020_10023.c` ([Source](../../hotpatches/zephyr/cve_2020_10023.c))

**Expected Output:**
```
*** Booting Zephyr OS build v3.7.0-1377-ge60da1bd640a ***
Start
aabaaaa c | aabaaaa c
aab aa aa c | ab aa  aa c
aab aa aa c => ab aa  aa c
-1 - Unexepected value

----------------------
Starting Kintsugi Hotpatch Manager Task
Start
aabaaaa c | aabaaaa c
aab aa aa c | aab aa aa c
Start
aabaaaa c | aabaaaa c
aab aa aa c | aab aa aa c
Start
aabaaaa c | aabaaaa c
aab aa aa c | aab aa aa c
```

#### CVE-2020-10024
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-10024)
- Hotpatch: `hotpatches/zephyr/cve_2020_10024.c` ([Source](../../hotpatches/zephyr/cve_2020_10024.c))

**Expected Output:**
```
*** Booting Zephyr OS build v3.7.0-1377-ge60da1bd640a ***
Caught system error -- reason 35
Wrong fault reason, expecting 3
Starting Kintsugi Hotpatch Manager Task
Caught system error -- reason 3
System error was expected
Caught system error -- reason 3
System error was expected
Caught system error -- reason 3
System error was expected
Caught system error -- reason 3
System error was expected
```

#### CVE-2020-10062
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-10062)
- Hotpatch: `hotpatches/zephyr/cve_2020_10062.c` ([Source](../../hotpatches/zephyr/cve_2020_10062.c))

**Expected Output:**
```
*** Booting Zephyr OS build v3.7.0-1377-ge60da1bd640a ***
0 - Result: 00000000
Starting Kintsugi Hotpatch Manager Task
1 - Result: FFFFFFEA
2 - Result: FFFFFFEA
3 - Result: FFFFFFEA
4 - Result: FFFFFFEA
5 - Result: FFFFFFEA
6 - Result: FFFFFFEA
7 - Result: FFFFFFEA
8 - Result: FFFFFFEA
9 - Result: FFFFFFEA
```

#### CVE-2020-10063
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-10063)
- Hotpatch: `hotpatches/zephyr/cve_2020_10063.c` ([Source](../../hotpatches/zephyr/cve_2020_10063.c))

**Expected Output:**
```
*** Booting Zephyr OS build v3.7.0-1377-ge60da1bd640a ***
Starting Kintsugi Hotpatch Manager Task
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
Result: FFFFFF76
```


## FreeRTOS
---
#### CVE-2017-2784
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2017-2784)
- Hotpatch: `hotpatches/freertos/cve_2020_17445.c` ([Source](../../hotpatches/freertos/cve_2017_2784.c))

**Expected Output:**
```
CVE-2017-2784
Task Main: 1
Task Manager: 1
Starting Kintsugi Hotpatch Manager Task
Import Failed -> Other Error: FFFFB380
Import Failed -> Other Error: FFFFB380
Import Failed -> Hotpatch Succeeded!
Import Failed -> Hotpatch Succeeded!
Import Failed -> Hotpatch Succeeded!
Import Failed -> Hotpatch Succeeded!
Import Failed -> Hotpatch Succeeded!
```

#### CVE-2018-16524
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2018-16524)
- Hotpatch: `hotpatches/freertos/cve_2018_16524.c` ([Source](../../hotpatches/freertos/cve_2018_16524.c))

**Expected Output:**
```
Task Main: 1
Task Manager: 1

Started
flip: 0, result: 0, offset: 000000FF, len: 34
Starting Kintsugi Hotpatch Manager Task
flip: 1, result: 0, offset: 00000000, len: 34
flip: 0, result: 0, offset: 000000FF, len: 34
flip: 1, result: 0, offset: 00000000, len: 34
flip: 0, result: 0, offset: 000000FF, len: 34
flip: 1, result: 0, offset: 00000000, len: 34
flip: 0, result: 0, offset: 000000FF, len: 34
```

#### CVE-2018-16603
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2018-16603)
- Hotpatch: `hotpatches/freertos/cve_2018_16603.c` ([Source](../../hotpatches/freertos/cve_2018_16603.c))

**Expected Output:**
```
CVE-2018-16603
IP Init: 1
Task Main: 1
Task Manager: 1
Starting Kintsugi Hotpatch Manager Task
Socket: 0x2000e1f8
Post-xProcessReceivedTCPPacket (0): 0
Post-xProcessReceivedTCPPacket (1): -1
Post-xProcessReceivedTCPPacket (0): 0
Post-xProcessReceivedTCPPacket (1): -1
Post-xProcessReceivedTCPPacket (0): 0
Post-xProcessReceivedTCPPacket (1): -1
Post-xProcessReceivedTCPPacket (0): 0
```

#### CVE-2020-17443
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-17443)
- Hotpatch: `hotpatches/freertos/cve_2020_17443.c` ([Source](../../hotpatches/freertos/cve_2020_17443.c))

**Expected Output:**
```
Task Manager: 1
Task PicoTCP: 1
Flip: 0
Echo Result: 0
Starting Kintsugi Hotpatch Manager Task
Flip: 0
Echo Result: 0
Flip: 0
Echo Result: 0
Flip: 0
Echo Result: 0
Flip: 0
Echo Result: 0
Flip: 0
Echo Result: 0
Flip: 0
Echo Result: 0
Flip: 1
Echo Result: 2
Flip: 0
Echo Result: 0
Flip: 1
Echo Result: 2
Flip: 0
Echo Result: 0
```

#### CVE-2020-17445
- Details: [Link](https://nvd.nist.gov/vuln/detail/CVE-2020-17445)
- Hotpatch: `hotpatches/freertos/cve_2020_17445.c` ([Source](../../hotpatches/freertos/cve_2020_17445.c))

**Expected Output:**
```
Task Manager: 1
Task PicoTCP: 1
Destopt Result: 0
Starting Kintsugi Hotpatch Manager Task
Destopt Result: 0
Destopt Result: 0
Destopt Result: 2
Destopt Result: 2
Destopt Result: 2
Destopt Result: 2
```

