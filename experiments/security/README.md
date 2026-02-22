# Kintsugi Experiments: Security Tests (C6)

In this series of experiments, we demonstrate Kintsugi's ability to prevent tampering attacks, as described in *Section 8* of the paper. Specifically, we show that Kintsugi protects itself from adversaries *before*, *during*, and *after* the hotpatching process. Below, we provide the expected outputs from each experiment.

How to perform experiments:
1. Connect to UART of the board using, for instance, `screen /dev/ttyACM0 115200`.
2. Run the experiment script `bash ./run.sh`.
3. Select a security experiment (1 to 3).
4. Compare UART output to expected output listed below (*Output could vary slightly*). 


#### Before Patching

**Expected Output:**
```
Starting Hotpatch Task
[ Invalid Hotpatch Type ]
[error]: invalid hotpatch type 5
[error]: could not parse hotpatch: 13
        => [Success]: Obtained error code: 13

[ Invalid Target Address ]
[error]: target address for hotpatch is invalid
[error]: could not parse hotpatch: 12
        => [Success]: Obtained error code: 12

[ Invalid Code Size ]
[error]: size of hotpatch exceeds quarantine size.
        => [Success]: Obtained error code: 3
```

#### During Patching

**Expected Output:**
```

Task Malicious: 1
Task Manager: 1
Task Workload 0: 1
Waiting...
Workload Task 704982704
Starting Hotpatch Task
Waiting...
Workload Task 1409965408
Waiting...
Workload Task 2114948112
Attacking!
[IMPORTANT]: Kintsugi prevented write at address 0x20000000
Attack FAILED
Workload Task -1475036480
Workload Task -770053776
Attacking!
[IMPORTANT]: Kintsugi prevented write at address 0x20000000
Attack FAILED
Workload Task -65071072
Workload Task 639911632
Attacking!
[IMPORTANT]: Kintsugi prevented write at address 0x20000000
Attack FAILED
```

#### After Patching

**Expected Output:**
```
Attack FAILED
Workload Task -1865462912
Task Malicious: 1
Task Manager: 1
Task Workload 0: 1
Starting Hotpatch Task
Done
Read (0x20000408): F000F8DF
[IMPORTANT]: Kintsugi prevented write at address 0x20000408
Malicious Attack Failed!
Read (0x20000408): F000F8DF
[IMPORTANT]: Kintsugi prevented write at address 0x20000408
Malicious Attack Failed!
Read (0x20000408): F000F8DF
[IMPORTANT]: Kintsugi prevented write at address 0x20000408
Malicious Attack Failed!
Read (0x20000408): F000F8DF
```