#!/usr/bin/env bash
set -euo pipefail

# 状态伪造攻击（WRITEDEVICE 写运行态字段）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/send_bms_uart_attack.py" \
  --attack state \
  --field state_voltage \
  --value 999 \
  "$@"
