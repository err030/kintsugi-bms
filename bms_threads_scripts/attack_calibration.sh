#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/send_bms_uart_attack.py" \
  --attack calib \
  --field calib_voff \
  --value 10 \
  "$@"
