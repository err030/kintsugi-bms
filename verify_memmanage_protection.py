#!/usr/bin/env python3
"""
验证 Kintsugi MemManage 保护是否正在工作。
通过读取 SCB 故障寄存器来检测是否发生了 MemManage 异常。
"""

import subprocess
import sys
import struct

def run_nrfjprog(cmd):
    """运行 nrfjprog 命令并返回结果"""
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout, result.stderr, result.returncode

def parse_memrd_output(output):
    """
    解析 nrfjprog --memrd 输出，格式例如：
    0xE000ED28: 00000082                              |....|
    返回解析后的值或 None
    """
    lines = output.strip().split('\n')
    for line in lines:
        if ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                hex_part = parts[1].split()[0] 
                try:
                    return int(hex_part, 16)
                except:
                    pass
    return None

def main():
    print("[*] 验证 Kintsugi MemManage 故障保护...")
    print()
    
    # SCB 寄存器地址
    CFSR_ADDR = "0xE000ED28"  
    MMFAR_ADDR = "0xE000ED34" 
    
    # Hotpatch 保护区域范围
    HP_SLOT_START = 0x20000020
    HP_SLOT_END = 0x200000f8
    HP_CODE_START = 0x20000148
    HP_CODE_END = 0x20000800
    HP_CONTEXT_START = 0x20000000
    HP_CONTEXT_END = 0x20000020
    
    print(f"[*] 读取 CFSR (0x{CFSR_ADDR[2:]})...")
    stdout, stderr, rc = run_nrfjprog(f"nrfjprog --family nrf52 --memrd {CFSR_ADDR} --n 4")
    
    if rc != 0:
        print(f"[!] 失败读取 CFSR: {stderr}")
        return 1
    
    cfsr = parse_memrd_output(stdout)
    print(f"    CFSR = 0x{cfsr:08X}")
    print()
    
    # 检查 DACCVIOL (bit 7) 和 MMARVALID (bit 1)
    DACCVIOL = (cfsr >> 7) & 1
    MMARVALID = (cfsr >> 1) & 1
    
    print(f"    DACCVIOL (bit 7) = {DACCVIOL}")
    print(f"    MMARVALID (bit 1) = {MMARVALID}")
    print()
    
    if DACCVIOL and MMARVALID:
        print("[+] 检测到 MemManage 数据访问违规！故障地址有效。")
        
        # 读取 MMFAR
        print(f"[*] 读取 MMFAR (0x{MMFAR_ADDR[2:]})...")
        stdout, stderr, rc = run_nrfjprog(f"nrfjprog --family nrf52 --memrd {MMFAR_ADDR} --n 4")
        
        if rc != 0:
            print(f"[!] 失败读取 MMFAR: {stderr}")
            return 1
        
        mmfar = parse_memrd_output(stdout)
        print(f"    MMFAR = 0x{mmfar:08X}")
        print()
        
        # 检查故障地址是否在 hotpatch 保护区域内
        in_slot = HP_SLOT_START <= mmfar < HP_SLOT_END
        in_code = HP_CODE_START <= mmfar < HP_CODE_END
        in_context = HP_CONTEXT_START <= mmfar < HP_CONTEXT_END
        
        if in_slot:
            region_name = "hotpatch_slots"
        elif in_code:
            region_name = "hotpatch_code"
        elif in_context:
            region_name = "hotpatch_context"
        else:
            region_name = "unknown"
        
        print(f"[*] 故障地址在保护区域内吗？")
        print(f"    - hotpatch_slots (0x{HP_SLOT_START:08X}..0x{HP_SLOT_END:08X})? {in_slot}")
        print(f"    - hotpatch_code (0x{HP_CODE_START:08X}..0x{HP_CODE_END:08X})? {in_code}")
        print(f"    - hotpatch_context (0x{HP_CONTEXT_START:08X}..0x{HP_CONTEXT_END:08X})? {in_context}")
        print()
        
        if in_slot or in_code or in_context:
            print("[+] ✓ 成功！Kintsugi MemManage 保护工作正常！")
            print("[+] 攻击对 hotpatch 保护区域的写入被拦截并产生了故障。")
            return 0
        else:
            print("[!] 故障地址不在任何 hotpatch 保护区域。")
            print("[!] 这可能是其他原因导致的故障。")
            return 1
    else:
        print("[!] 未检测到 MemManage 数据访问违规。")
        print("[!] MemManage 保护可能未被触发。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
