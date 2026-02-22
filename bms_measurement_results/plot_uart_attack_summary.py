#!/usr/bin/env python3
"""Summarize UART attack logs and generate compact summary figures."""
from __future__ import annotations

from pathlib import Path
import csv
import os

import matplotlib.pyplot as plt
import numpy as np


PHASES = ["before", "during", "after"]
# Number of injected frames per phase in our collection runs.
TOTAL_FRAMES = int(os.environ.get("UART_ATTACK_TOTAL_FRAMES", "100"))
ATTACKS = [
    ("overflow", "overflow", "CMD=WRITEALL"),
    ("state", "state", "[BMS-RX] STATE"),
    ("replay", "replay", "WRITEDEVICE replay"),
    ("calib", "replay", "[BMS-RX] CALIB"),
]


def count_markers(text: str, accept_token: str) -> tuple[int, int, int]:
    """Return (accepted_count, blocked_frames, raw_blocked_lines)."""
    accepted = 0
    raw_blocked = 0
    for line in text.splitlines():
        if accept_token in line:
            accepted += 1
        if "[IMPORTANT]" in line:
            raw_blocked += 1

    # We visualize "blocked vs unblocked" as a per-frame outcome.
    blocked_frames = min(TOTAL_FRAMES, raw_blocked)
    return accepted, blocked_frames, raw_blocked


def load_counts(log_dir: Path) -> dict[tuple[str, str], tuple[int, int, int]]:
    counts: dict[tuple[str, str], tuple[int, int, int]] = {}
    for attack, log_suffix, accept_token in ATTACKS:
        for phase in PHASES:
            path = log_dir / f"{phase}_{log_suffix}.log"
            if not path.exists():
                counts[(phase, attack)] = (0, 0, 0)
                continue
            text = path.read_text(errors="ignore")
            counts[(phase, attack)] = count_markers(text, accept_token)
    return counts


def write_csv(counts: dict[tuple[str, str], tuple[int, int, int]], out_path: Path) -> None:
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "phase",
                "attack",
                "total_frames",
                "blocked_frames",
                "unblocked_frames",
                "accepted_markers",
                "raw_blocked_lines",
            ]
        )
        for phase in PHASES:
            for attack, _, _ in ATTACKS:
                accepted, blocked_frames, raw_blocked = counts[(phase, attack)]
                unblocked_frames = TOTAL_FRAMES - blocked_frames
                writer.writerow(
                    [
                        phase,
                        attack,
                        TOTAL_FRAMES,
                        blocked_frames,
                        unblocked_frames,
                        accepted,
                        raw_blocked,
                    ]
                )


def plot_summary(counts: dict[tuple[str, str], tuple[int, int, int]], out_path: Path) -> None:
    fig, axes = plt.subplots(1, len(ATTACKS), figsize=(16, 4), sharey=False)
    width = 0.32
    colors = {
        "blocked": "#4C78A8",    # blue = good direction
        "unblocked": "#F58518",  # orange = bad direction
    }

    for ax, (attack, _, _) in zip(axes, ATTACKS):
        x = np.arange(len(PHASES))
        blocked_vals = [counts[(phase, attack)][1] for phase in PHASES]
        unblocked_vals = [TOTAL_FRAMES - b for b in blocked_vals]

        bars_blocked = ax.bar(x - width / 2, blocked_vals, width, label="Blocked", color=colors["blocked"])
        bars_unblocked = ax.bar(x + width / 2, unblocked_vals, width, label="Unblocked", color=colors["unblocked"])

        # Label bars with counts only (no per-phase Total labels).
        ax.bar_label(bars_blocked, padding=2, fontsize=9)
        ax.bar_label(bars_unblocked, padding=2, fontsize=9)

        ax.set_xticks(x)
        ax.set_xticklabels([p.capitalize() for p in PHASES])
        ax.set_title(f"{attack.capitalize()} attack")
        ax.set_ylabel("Frames")
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        ax.set_ylim(0, TOTAL_FRAMES + 10)

    fig.suptitle("UART attack outcomes (counts per phase)", fontsize=12, y=0.995)
    fig.text(0.99, 0.995, f"N={TOTAL_FRAMES} frames/phase", ha="right", va="top", fontsize=9)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.955))
    fig.text(0.5, 0.02,
             "Blocked/Unblocked are derived from firmware UART logs ([IMPORTANT]) and capped to N frames.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=[0.02, 0.08, 0.98, 0.9])
    fig.savefig(out_path)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir / "uart_attack_logs"
    counts = load_counts(log_dir)
    try:
        write_csv(counts, base_dir / "uart_attack_summary.csv")
    except PermissionError:
        write_csv(counts, base_dir / "uart_attack_summary_matplotlib.csv")
    try:
        plot_summary(counts, base_dir / "uart_attack_summary.svg")
    except PermissionError:
        plot_summary(counts, base_dir / "uart_attack_summary_matplotlib.svg")
    try:
        plot_summary(counts, base_dir / "uart_attack_summary.pdf")
    except PermissionError:
        plot_summary(counts, base_dir / "uart_attack_summary_matplotlib.pdf")


if __name__ == "__main__":
    main()
