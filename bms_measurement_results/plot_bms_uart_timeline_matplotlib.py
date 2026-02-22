#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys


def read_csv_points(path):
    xs = []
    ys = []
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            xs.append(float(row["x"]))
            ys.append(float(row["y"]))
    return xs, ys


def read_optional_csv(path):
    if not os.path.exists(path):
        return [], []
    return read_csv_points(path)


def read_meta(path):
    keys = [
        "TimelineBeforeStart",
        "TimelineBeforeEnd",
        "TimelineDuringStart",
        "TimelineDuringEnd",
        "TimelineAfterStart",
        "TimelineAfterEnd",
    ]
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    values = {}
    for key in keys:
        match = re.search(r"\\def\\%s\{([^}]+)\}" % key, text)
        if not match:
            raise ValueError("Missing %s in %s" % (key, path))
        values[key] = float(match.group(1))
    return values


def main():
    parser = argparse.ArgumentParser(
        description="Plot BMS UART attack timeline in a case-study style."
    )
    parser.add_argument("--attack", default="overflow", help="Attack name prefix.")
    parser.add_argument(
        "--style",
        choices=["lanes", "tracks"],
        default="lanes",
        help="visual style for the timeline",
    )
    parser.add_argument(
        "--input-dir", default="bms_measurement_results", help="Timeline data directory."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output PDF path (default: bms_measurement_results/bms_uart_timeline_case_study_matplotlib.pdf).",
    )
    args = parser.parse_args()

    base = os.path.join(args.input_dir, "uart_attack_timeline_%s" % args.attack)
    rx_path = base + "_rx.csv"
    blocked_path = base + "_blocked.csv"
    mon_path = base + "_mon.csv"
    est_path = base + "_est.csv"
    comm_path = base + "_comm.csv"
    meta_path = base + "_meta.tex"

    for path in (rx_path, blocked_path, meta_path):
        if not os.path.exists(path):
            sys.exit("Missing required file: %s" % path)

    rx_x, _ = read_csv_points(rx_path)
    blocked_x, _ = read_csv_points(blocked_path)
    mon_x, _ = read_optional_csv(mon_path)
    est_x, _ = read_optional_csv(est_path)
    comm_x, _ = read_optional_csv(comm_path)
    meta = read_meta(meta_path)

    before_mid = 0.5 * (meta["TimelineBeforeStart"] + meta["TimelineBeforeEnd"])
    during_mid = 0.5 * (meta["TimelineDuringStart"] + meta["TimelineDuringEnd"])
    after_mid = 0.5 * (meta["TimelineAfterStart"] + meta["TimelineAfterEnd"])

    all_x = rx_x + blocked_x + mon_x + est_x + comm_x
    x_min = min([meta["TimelineBeforeStart"]] + (all_x if all_x else []))
    x_max = max([meta["TimelineAfterEnd"]] + (all_x if all_x else []))

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(8.6, 3.4))

    colors = {
        "before": "#C9C1B8",
        "during": "#7BAE94",
        "after": "#A9CDB8",
        "rx": "#666666",
        "blocked": "#4C78A8",
        "mon": "#90959B",
        "est": "#7A7A7A",
        "comm": "#5C5C5C",
        "boundary": "#3A3A3A",
        "grid": "#E6E6E6",
    }

    ax.set_facecolor("#FFFFFF")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#9A9A9A")

    phase_ranges = [
        ("before", meta["TimelineBeforeStart"], meta["TimelineBeforeEnd"]),
        ("during", meta["TimelineDuringStart"], meta["TimelineDuringEnd"]),
        ("after", meta["TimelineAfterStart"], meta["TimelineAfterEnd"]),
    ]

    def phase_has_points(xs, start, end):
        return any(start <= x <= end for x in xs)

    if args.style == "tracks":
        y_levels = {
            "phase": 6.0,
            "rx": 4.8,
            "blocked": 4.0,
            "mon": 2.8,
            "est": 2.0,
            "comm": 1.2,
        }
        margin = max(6.0, (x_max - x_min) * 0.04)
        ax.set_xlim(x_min - margin, x_max)
        ax.set_ylim(0.6, 6.9)
        ax.set_yticks([])
        ax.set_xlabel("Log index (pseudo-time, left → right)")
        ax.tick_params(labelsize=9, colors="#555555")
        ax.grid(axis="x", linestyle="--", linewidth=0.5, color=colors["grid"])

        def downsample(xs, max_points=140):
            if len(xs) <= max_points:
                return xs
            step = max(1, len(xs) // max_points)
            return xs[::step]

        phase_h = 0.36
        for phase, start, end in phase_ranges:
            ax.add_patch(
                mpatches.Rectangle(
                    (start, y_levels["phase"] - phase_h / 2),
                    end - start,
                    phase_h,
                    facecolor=colors[phase],
                    edgecolor="none",
                    alpha=0.95,
                    zorder=1,
                )
            )
        ax.axvline(meta["TimelineDuringStart"], color=colors["boundary"], linestyle="--", linewidth=0.9)
        ax.axvline(meta["TimelineAfterStart"], color=colors["boundary"], linestyle="--", linewidth=0.9)

        def draw_status(xs, lane, color):
            bar_h = 0.28
            for _, start, end in phase_ranges:
                if phase_has_points(xs, start, end):
                    ax.add_patch(
                        mpatches.Rectangle(
                            (start, lane - bar_h / 2),
                            end - start,
                            bar_h,
                            facecolor=color,
                            edgecolor="none",
                            alpha=0.22,
                            zorder=1,
                        )
                    )
            ticks = downsample(xs, max_points=160)
            ax.vlines(
                ticks,
                lane - 0.14,
                lane + 0.14,
                color=color,
                linewidth=0.6,
                alpha=0.6,
                zorder=2,
            )

        draw_status(mon_x, y_levels["mon"], colors["mon"])
        draw_status(est_x, y_levels["est"], colors["est"])
        draw_status(comm_x, y_levels["comm"], colors["comm"])

        rx_ticks = downsample(rx_x, max_points=200)
        ax.vlines(rx_ticks, y_levels["rx"] - 0.16, y_levels["rx"] + 0.16, color=colors["rx"], linewidth=0.9, zorder=3)

        blocked_ticks = downsample(blocked_x, max_points=200)
        ax.vlines(blocked_ticks, y_levels["blocked"] - 0.18, y_levels["blocked"] + 0.18, color=colors["blocked"], linewidth=1.1, zorder=3)
        ax.scatter(blocked_ticks, [y_levels["blocked"]] * len(blocked_ticks), marker="x", s=20, color=colors["blocked"], zorder=4)

        if blocked_x:
            burst_start = min(blocked_x)
            burst_end = max(blocked_x)
            ax.add_patch(
                mpatches.Rectangle(
                    (burst_start, y_levels["blocked"] - 0.22),
                    max(1.0, burst_end - burst_start),
                    0.44,
                    facecolor=colors["blocked"],
                    edgecolor="none",
                    alpha=0.08,
                    zorder=1,
                )
            )
            ax.annotate(
                "blocked burst",
                xy=(burst_start, y_levels["blocked"] + 0.22),
                xytext=(burst_start + 18, y_levels["blocked"] + 0.7),
                fontsize=7,
                color=colors["blocked"],
                arrowprops=dict(arrowstyle="->", color=colors["blocked"], linewidth=0.8),
            )

        label_x = x_min - margin * 0.7
        group_label_x = x_min - margin * 0.95
        ax.text(label_x, y_levels["rx"], "BMS-RX", ha="right", va="center", fontsize=8.5, color="#333333")
        ax.text(label_x, y_levels["blocked"], "Blocked", ha="right", va="center", fontsize=8.5, color="#333333")
        ax.text(label_x, y_levels["mon"], "MON", ha="right", va="center", fontsize=8.5, color="#333333")
        ax.text(label_x, y_levels["est"], "EST", ha="right", va="center", fontsize=8.5, color="#333333")
        ax.text(label_x, y_levels["comm"], "COMM", ha="right", va="center", fontsize=8.5, color="#333333")
        ax.text(group_label_x, y_levels["rx"] + 0.45, "Events", ha="right", va="center", fontsize=7.5, color="#777777")
        ax.text(group_label_x, y_levels["mon"] + 0.35, "Tasks", ha="right", va="center", fontsize=7.5, color="#777777")

        ax.text(before_mid, y_levels["phase"] + 0.45, "before", ha="center", va="bottom", fontsize=8.2)
        ax.text(during_mid, y_levels["phase"] + 0.45, "during", ha="center", va="bottom", fontsize=8.2)
        ax.text(after_mid, y_levels["phase"] + 0.45, "after", ha="center", va="bottom", fontsize=8.2)
        ax.text(
            meta["TimelineDuringStart"],
            y_levels["phase"] + 0.12,
            "patch start",
            ha="right",
            va="bottom",
            fontsize=7,
            rotation=90,
            color="#333333",
        )
        ax.text(
            meta["TimelineAfterStart"],
            y_levels["phase"] + 0.12,
            "patch complete",
            ha="right",
            va="bottom",
            fontsize=7,
            rotation=90,
            color="#333333",
        )

        fig.tight_layout(pad=0.4)
        out_path = args.out or os.path.join(
            args.input_dir, "bms_uart_timeline_case_study_tracks.pdf"
        )
        fig.savefig(out_path)
        return

    y_levels = {
        "mon": 4.2,
        "est": 3.4,
        "comm": 2.6,
        "rx": 1.6,
        "blocked": 0.8,
        "phase": 5.1,
    }

    for phase, start, end in phase_ranges:
        ax.hlines(
            y_levels["phase"],
            start,
            end,
            color=colors[phase],
            linewidth=6.0,
            alpha=0.95,
            zorder=1,
        )
        if phase_has_points(mon_x, start, end):
            ax.hlines(
                y_levels["mon"],
                start,
                end,
                color=colors["mon"],
                linewidth=1.3,
                alpha=0.45,
            )
        if phase_has_points(est_x, start, end):
            ax.hlines(
                y_levels["est"],
                start,
                end,
                color=colors["est"],
                linewidth=1.3,
                alpha=0.45,
            )
        if phase_has_points(comm_x, start, end):
            ax.hlines(
                y_levels["comm"],
                start,
                end,
                color=colors["comm"],
                linewidth=1.3,
                alpha=0.45,
            )

    lane_order = ["mon", "est", "comm", "rx", "blocked"]
    for lane in lane_order:
        ax.hlines(
            y_levels[lane],
            x_min,
            x_max,
            color=colors["grid"],
            linewidth=0.6,
            zorder=0,
        )

    rx_y = [y_levels["rx"]] * len(rx_x)
    blocked_y = [y_levels["blocked"]] * len(blocked_x)
    ax.scatter(rx_x, rx_y, s=18, color=colors["rx"], zorder=4)
    ax.scatter(blocked_x, blocked_y, s=26, marker="x", color=colors["blocked"], zorder=4)

    ax.axvline(meta["TimelineDuringStart"], color=colors["boundary"], linestyle="--", linewidth=0.9)
    ax.axvline(meta["TimelineAfterStart"], color=colors["boundary"], linestyle="--", linewidth=0.9)

    margin = max(6.0, (x_max - x_min) * 0.04)
    ax.set_xlim(x_min - margin, x_max)
    ax.set_ylim(0.2, 5.6)
    ax.set_yticks([])
    ax.set_xlabel("Log index (pseudo-time)")
    ax.tick_params(labelsize=9, colors="#555555")
    ax.grid(axis="x", linestyle="--", linewidth=0.5, color=colors["grid"])
    ax.margins(x=0, y=0)

    ax.text(before_mid, y_levels["phase"] + 0.25, "before", ha="center", va="bottom", fontsize=8.5)
    ax.text(during_mid, y_levels["phase"] + 0.25, "during", ha="center", va="bottom", fontsize=8.5)
    ax.text(after_mid, y_levels["phase"] + 0.25, "after", ha="center", va="bottom", fontsize=8.5)
    ax.text(
        meta["TimelineDuringStart"],
        y_levels["phase"] + 0.05,
        "patch start",
        ha="right",
        va="bottom",
        fontsize=7,
        rotation=90,
        color="#333333",
    )
    ax.text(
        meta["TimelineAfterStart"],
        y_levels["phase"] + 0.05,
        "patch complete",
        ha="right",
        va="bottom",
        fontsize=7,
        rotation=90,
        color="#333333",
    )

    if blocked_x:
        first_blocked = blocked_x[0]
        ax.annotate(
            "blocked burst",
            xy=(first_blocked, y_levels["blocked"]),
            xytext=(first_blocked + 18, y_levels["blocked"] + 0.4),
            fontsize=7,
            color=colors["blocked"],
            arrowprops=dict(arrowstyle="->", color=colors["blocked"], linewidth=0.8),
        )

    label_x = x_min - margin * 0.55
    ax.text(label_x, y_levels["mon"], "MON", ha="right", va="center", fontsize=9, color="#333333")
    ax.text(label_x, y_levels["est"], "EST", ha="right", va="center", fontsize=9, color="#333333")
    ax.text(label_x, y_levels["comm"], "COMM", ha="right", va="center", fontsize=9, color="#333333")
    ax.text(label_x, y_levels["rx"], "BMS-RX", ha="right", va="center", fontsize=9, color="#333333")
    ax.text(label_x, y_levels["blocked"], "Blocked", ha="right", va="center", fontsize=9, color="#333333")

    phase_handles = [
        mpatches.Patch(color=colors["before"], label="before"),
        mpatches.Patch(color=colors["during"], label="during"),
        mpatches.Patch(color=colors["after"], label="after"),
    ]
    ax.legend(
        handles=phase_handles,
        loc="upper left",
        frameon=False,
        fontsize=8,
        handlelength=1.6,
        borderpad=0.2,
        bbox_to_anchor=(0.01, 0.98),
    )

    fig.tight_layout(pad=0.4)
    out_path = args.out or os.path.join(
        args.input_dir, "bms_uart_timeline_case_study_matplotlib.pdf"
    )
    fig.savefig(out_path)


if __name__ == "__main__":
    main()
