#!/usr/bin/env python3
"""Generate UART attack outcome heatmap/table from log markers.

This heatmap is meant to match the per-frame semantics used by the summary plot:
for each (attack, phase) we injected N frames and visualize Blocked vs Unblocked.

Blocked/Unblocked are derived from firmware UART logs:
- "[IMPORTANT]" indicates a protected write was intercepted (MemManage path).
- The count is capped to N frames because one injected frame may trigger multiple
  protected write attempts and therefore multiple "[IMPORTANT]" lines.
"""
from __future__ import annotations

from pathlib import Path
import csv
import os

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm


PHASES = ["before", "during", "after"]
TOTAL_FRAMES = int(os.environ.get("UART_ATTACK_TOTAL_FRAMES", "100"))
ATTACKS = [
    ("overflow", "overflow", "CMD=WRITEALL"),
    ("state", "state", "[BMS-RX] STATE"),
    ("replay", "replay", "WRITEDEVICE replay"),
    ("calib", "replay", "[BMS-RX] CALIB"),
]
BLOCK_MARK = "[IMPORTANT]"


def count_markers(text: str, accept_token: str) -> tuple[int, int, int]:
    """Return (accepted_count, blocked_frames, raw_blocked_lines)."""
    accepted = 0
    raw_blocked = 0
    for line in text.splitlines():
        if accept_token in line:
            accepted += 1
        if BLOCK_MARK in line:
            raw_blocked += 1

    blocked_frames = min(TOTAL_FRAMES, raw_blocked)
    return accepted, blocked_frames, raw_blocked


def load_counts(log_dir: Path) -> dict[tuple[str, str], tuple[int, int, int]]:
    counts: dict[tuple[str, str], tuple[int, int, int]] = {}
    for attack, log_suffix, accept_token in ATTACKS:
        for phase in PHASES:
            path = log_dir / f"{phase}_{log_suffix}.log"
            if not path.exists():
                counts[(attack, phase)] = (0, 0, 0)
                continue
            text = path.read_text(errors="ignore")
            counts[(attack, phase)] = count_markers(text, accept_token)
    return counts


def write_csv(
    counts: dict[tuple[str, str], tuple[int, int, int]], out_path: Path
) -> None:
    with out_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "attack",
                "phase",
                "total_frames",
                "blocked_frames",
                "unblocked_frames",
                "accepted_markers",
                "raw_blocked_lines",
                "unblocked_rate",
            ]
        )
        for attack, _, _ in ATTACKS:
            for phase in PHASES:
                accepted, blocked_frames, raw_blocked = counts[(attack, phase)]
                unblocked_frames = TOTAL_FRAMES - blocked_frames
                unblocked_rate = 0.0 if TOTAL_FRAMES == 0 else 100.0 * unblocked_frames / TOTAL_FRAMES
                writer.writerow(
                    [
                        attack,
                        phase,
                        TOTAL_FRAMES,
                        blocked_frames,
                        unblocked_frames,
                        accepted,
                        raw_blocked,
                        f"{unblocked_rate:.1f}",
                    ]
                )


def plot_heatmap(
    counts: dict[tuple[str, str], tuple[int, int, int]], out_path: Path
) -> None:
    row_labels = [a[0] for a in ATTACKS]
    col_labels = [p.capitalize() for p in PHASES]

    cell_text = []
    unblocked_rates = []
    for attack, _, _ in ATTACKS:
        row_text = []
        row_unblocked = []
        for phase in PHASES:
            accepted, blocked_frames, raw_blocked = counts[(attack, phase)]
            unblocked_frames = TOTAL_FRAMES - blocked_frames
            unblocked_rate = 0.0 if TOTAL_FRAMES == 0 else 100.0 * unblocked_frames / TOTAL_FRAMES
            row_text.append(
                f"B={blocked_frames} U={unblocked_frames}\nRX={accepted}"
            )
            row_unblocked.append(unblocked_rate)
        cell_text.append(row_text)
        unblocked_rates.append(row_unblocked)

    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    ax.axis("off")

    table = ax.table(
        cellText=cell_text,
        rowLabels=row_labels,
        colLabels=col_labels,
        cellLoc="center",
        rowLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1.1, 1.4)

    cmap = cm.get_cmap("Reds")
    norm = colors.Normalize(vmin=0.0, vmax=100.0)

    for r in range(len(row_labels)):
        for c in range(len(col_labels)):
            cell = table[(r + 1, c)]
            cell.set_facecolor(cmap(norm(unblocked_rates[r][c])))
            cell.set_edgecolor("#666666")

    for c in range(len(col_labels)):
        header = table[(0, c)]
        header.set_facecolor("#F0F0F0")
        header.set_edgecolor("#666666")

    for r in range(1, len(row_labels) + 1):
        row_header = table[(r, -1)]
        row_header.set_facecolor("#F0F0F0")
        row_header.set_edgecolor("#666666")

    fig.tight_layout(pad=0.6)
    fig.savefig(out_path)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir / "uart_attack_logs"
    counts = load_counts(log_dir)
    write_csv(counts, base_dir / "uart_attack_heatmap.csv")
    plot_heatmap(counts, base_dir / "uart_attack_heatmap.pdf")
    plot_heatmap(counts, base_dir / "uart_attack_heatmap.svg")


if __name__ == "__main__":
    main()
