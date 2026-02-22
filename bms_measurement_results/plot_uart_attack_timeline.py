#!/usr/bin/env python3
"""Create a simple timeline plot dataset from UART logs (BMS case study).

This mirrors the drone case study idea: show when the system is vulnerable
or patched, and overlay event markers from UART logs.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv


PHASES = ["before", "during", "after"]
MARKS = {
    "rx": "[BMS-RX]",
    "blocked": "[IMPORTANT]",
    "mon": "[BMS][MON]",
    "est": "[BMS][EST]",
    "comm": "[BMS][COMM]",
}
Y_LEVELS = {
    "mon": 0.2,
    "est": 0.4,
    "comm": 0.6,
    "rx": 1.1,
    "blocked": 1.6,
}


def parse_log(path: Path) -> tuple[dict[str, list[int]], int]:
    markers = {key: [] for key in MARKS}
    if not path.exists():
        return markers, 0
    lines = path.read_text(errors="ignore").splitlines()
    for i, line in enumerate(lines):
        for key, token in MARKS.items():
            if token in line:
                markers[key].append(i)
    return markers, len(lines)


def write_points(path: Path, points: list[tuple[int, float]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x", "y"])
        for x, y in points:
            writer.writerow([x, y])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attack", default="overflow",
                        choices=["overflow", "state", "replay"],
                        help="attack log name to plot")
    parser.add_argument("--gap", type=int, default=20,
                        help="gap between phases on the timeline")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir / "uart_attack_logs"

    points = {key: [] for key in MARKS}
    meta = {}
    offset = 0

    for phase in PHASES:
        path = log_dir / f"{phase}_{args.attack}.log"
        markers, n_lines = parse_log(path)
        start = offset
        end = offset + max(n_lines - 1, 0)
        meta[phase] = (start, end)

        for key, indices in markers.items():
            y = Y_LEVELS[key]
            for idx in indices:
                points[key].append((offset + idx, y))

        offset = end + 1 + args.gap

    rx_csv = base_dir / f"uart_attack_timeline_{args.attack}_rx.csv"
    blocked_csv = base_dir / f"uart_attack_timeline_{args.attack}_blocked.csv"
    mon_csv = base_dir / f"uart_attack_timeline_{args.attack}_mon.csv"
    est_csv = base_dir / f"uart_attack_timeline_{args.attack}_est.csv"
    comm_csv = base_dir / f"uart_attack_timeline_{args.attack}_comm.csv"
    meta_tex = base_dir / f"uart_attack_timeline_{args.attack}_meta.tex"

    write_points(rx_csv, points["rx"])
    write_points(blocked_csv, points["blocked"])
    write_points(mon_csv, points["mon"])
    write_points(est_csv, points["est"])
    write_points(comm_csv, points["comm"])

    with meta_tex.open("w") as handle:
        handle.write(f"\\def\\TimelineBeforeStart{{{meta['before'][0]}}}\n")
        handle.write(f"\\def\\TimelineBeforeEnd{{{meta['before'][1]}}}\n")
        handle.write(f"\\def\\TimelineDuringStart{{{meta['during'][0]}}}\n")
        handle.write(f"\\def\\TimelineDuringEnd{{{meta['during'][1]}}}\n")
        handle.write(f"\\def\\TimelineAfterStart{{{meta['after'][0]}}}\n")
        handle.write(f"\\def\\TimelineAfterEnd{{{meta['after'][1]}}}\n")

    print(f"Wrote {rx_csv}")
    print(f"Wrote {blocked_csv}")
    print(f"Wrote {mon_csv}")
    print(f"Wrote {est_csv}")
    print(f"Wrote {comm_csv}")
    print(f"Wrote {meta_tex}")


if __name__ == "__main__":
    main()
