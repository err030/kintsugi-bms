#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <before|during|after>"
    echo "Optional env: PORT, BAUD, REPEAT, DELAY, CAPTURE_SECONDS, OUT_DIR"
    exit 1
fi

PHASE="$1"
case "$PHASE" in
    before|during|after) ;;
    *)
        echo "Invalid phase: $PHASE (expected before|during|after)"
        exit 1
        ;;
esac

PORT="${PORT:-/dev/ttyACM0}"
BAUD="${BAUD:-115200}"
REPEAT="${REPEAT:-100}"
DELAY="${DELAY:-0.05}"
PAD_BYTES="${PAD_BYTES:-16}"
STATE_VALUE="${STATE_VALUE:-999}"
CALIB_VALUE="${CALIB_VALUE:-10}"
REPLAY_SEQ="${REPLAY_SEQ:-7}"
OUT_DIR="${OUT_DIR:-bms_measurement_results/uart_attack_logs}"
NO_DTR="${NO_DTR:-1}"

if [[ ! -e "$PORT" ]]; then
    echo "Serial port not found: $PORT"
    echo "Available ACM devices:"
    ls /dev/ttyACM* 2>/dev/null || echo "(none)"
    exit 1
fi

mkdir -p "$OUT_DIR"

if [[ -n "${CAPTURE_SECONDS:-}" ]]; then
    CAPTURE="$CAPTURE_SECONDS"
else
    CAPTURE="$(LC_ALL=C awk -v r="$REPEAT" -v d="$DELAY" 'BEGIN { c = r*d + 8; if (c < 12) c = 12; printf "%.2f", c }')"
fi

COMMON_ARGS=(
    --port "$PORT"
    --baud "$BAUD"
    --repeat "$REPEAT"
    --delay "$DELAY"
    --capture-seconds "$CAPTURE"
)
if [[ "$NO_DTR" == "1" ]]; then
    COMMON_ARGS+=(--no-dtr)
fi

echo "[collect] phase=$PHASE port=$PORT repeat=$REPEAT delay=$DELAY capture=${CAPTURE}s"

python3 bms_threads_scripts/send_bms_uart_attack.py \
    "${COMMON_ARGS[@]}" \
    --attack overflow \
    --pad-bytes "$PAD_BYTES" \
    --log "$OUT_DIR/${PHASE}_overflow.log"

python3 bms_threads_scripts/send_bms_uart_attack.py \
    "${COMMON_ARGS[@]}" \
    --attack state \
    --field state_voltage \
    --value "$STATE_VALUE" \
    --log "$OUT_DIR/${PHASE}_state.log"

python3 bms_threads_scripts/send_bms_uart_attack.py \
    "${COMMON_ARGS[@]}" \
    --attack replay \
    --field calib_voff \
    --value "$CALIB_VALUE" \
    --seq "$REPLAY_SEQ" \
    --log "$OUT_DIR/${PHASE}_replay.log"

python3 bms_measurement_results/plot_uart_attack_summary.py
python3 bms_measurement_results/plot_uart_attack_heatmap.py

echo "[done] logs updated under $OUT_DIR for phase=$PHASE"
echo "[done] figures refreshed: bms_measurement_results/uart_attack_summary.pdf and bms_measurement_results/uart_attack_heatmap.pdf"
