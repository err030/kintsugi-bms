#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/send_bms_uart_attack.py" \
  --attack state \
  --field state_voltage \
  --value 999 \
  "$@"
