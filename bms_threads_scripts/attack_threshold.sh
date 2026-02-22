#!/usr/bin/env bash
set -euo pipefail

# 阈值写入溢出攻击（WRITEALL + padding）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/send_bms_uart_attack.py" \
  --attack overflow \
  --pad-bytes 16 \
  "$@"
