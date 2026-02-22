#!/usr/bin/env python3
"""Collect MemManage latency samples for the BMS threshold attack."""

import argparse
import csv
import re
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "experiments/security/after_patching/build_user/nrf52840_xxaa.map"
OUT_CSV = ROOT / "bms_measurement_results/bms_latency.csv"
OUT_PNG = ROOT / "bms_measurement_results/bms_latency.png"
OUT_SVG = ROOT / "bms_measurement_results/bms_latency.svg"
OUT_PDF = ROOT / "bms_measurement_results/bms_latency.pdf"

CPU_HZ = 16_000_000
SAMPLES = 30
POLL_INTERVAL_S = 0.4
INTERVAL_S = 1.2
MAX_WAIT_S = 300
EXPECTED_BOOT_FLAG = 0xA5A5A5A5


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def memrd_word(addr):
    res = run(f"nrfjprog --family nrf52 --memrd 0x{addr:08X} --n 4")
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    for line in res.stdout.strip().splitlines():
        if ':' not in line:
            continue
        return int(line.split(':', 1)[1].strip().split()[0], 16)
    raise RuntimeError("No memrd output")


def resume_cpu():
    run("nrfjprog --family nrf52 --run")


def find_addr(symbol, map_path):
    text = Path(map_path).read_text()
    match = re.search(r"\s+0x([0-9a-fA-F]+)\s+" + re.escape(symbol) + r"\b", text)
    if match:
        return int(match.group(1), 16)

    sec_match = re.search(
        r"^\s*\.bss\." + re.escape(symbol) + r"\s*\n\s+0x([0-9a-fA-F]+)",
        text,
        re.MULTILINE,
    )
    if sec_match:
        return int(sec_match.group(1), 16)

    raise RuntimeError(f"Address not found for {symbol}")


def render_svg(xs, series, path):
    width, height = 920, 460
    pad_left, pad_right, pad_top, pad_bottom = 75, 30, 90, 80

    all_ys = []
    for item in series:
        all_ys.extend(item["ys"])
    min_y = min(all_ys)
    max_y = max(all_ys)
    if max_y == min_y:
        max_y = min_y + 1.0
    x_min = min(xs) if xs else 0
    x_max = max(xs) if xs else 1
    x_span = x_max - x_min if x_max != x_min else 1

    def sx(val):
        return pad_left + (val - x_min) / x_span * (width - pad_left - pad_right)

    def sy(val):
        return height - pad_bottom - (val - min_y) / (max_y - min_y) * (height - pad_top - pad_bottom)

    svg = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<rect width='100%' height='100%' fill='white' stroke='black'/>",
    ]

    # Grid + Y ticks
    y_ticks = 5
    for i in range(y_ticks + 1):
        y_val = min_y + (max_y - min_y) * i / y_ticks
        y_pos = sy(y_val)
        svg.append(
            f"<line x1='{pad_left}' y1='{y_pos:.1f}' x2='{width - pad_right}' y2='{y_pos:.1f}' stroke='#E0E0E0'/>"
        )
        svg.append(
            f"<text x='{pad_left - 6}' y='{y_pos + 4:.1f}' font-size='11' text-anchor='end'>{y_val:.2f}</text>"
        )

    # X ticks
    x_ticks = min(6, len(xs)) if xs else 1
    for i in range(x_ticks):
        x_val = x_min + x_span * i / max(1, x_ticks - 1)
        x_pos = sx(x_val)
        svg.append(
            f"<line x1='{x_pos:.1f}' y1='{pad_top}' x2='{x_pos:.1f}' y2='{height - pad_bottom}' stroke='#F0F0F0'/>"
        )
        svg.append(
            f"<text x='{x_pos:.1f}' y='{height - pad_bottom + 18}' font-size='11' text-anchor='middle'>{int(round(x_val))}</text>"
        )

    # Axes
    svg.append(
        f"<line x1='{pad_left}' y1='{height - pad_bottom}' x2='{width - pad_right}' y2='{height - pad_bottom}' stroke='black'/>"
    )
    svg.append(
        f"<line x1='{pad_left}' y1='{pad_top}' x2='{pad_left}' y2='{height - pad_bottom}' stroke='black'/>"
    )

    # Polylines + points
    for item in series:
        points = [f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, item["ys"])]
        svg.append(
            f"<polyline fill='none' stroke='{item['color']}' stroke-width='2' points='{' '.join(points)}'/>"
        )
        for x, y in zip(xs, item["ys"]):
            svg.append(
                f"<circle cx='{sx(x):.1f}' cy='{sy(y):.1f}' r='2.3' fill='{item['color']}'/>"
            )

    # Labels + title
    svg.append(
        f"<text x='{pad_left}' y='24' font-size='14' font-weight='bold'>BMS Threshold Tamper Protection Latency</text>"
    )
    svg.append(
        f"<text x='{pad_left}' y='42' font-size='11'>Attack: write g_bms_thresholds in hotpatch context</text>"
    )
    svg.append(
        f"<text x='{pad_left}' y='58' font-size='11'>Target: Kintsugi MemManage interception</text>"
    )
    svg.append(
        f"<text x='20' y='{(height - pad_bottom - pad_top) / 2 + pad_top:.1f}' font-size='11' text-anchor='middle' transform='rotate(-90 20 {(height - pad_bottom - pad_top) / 2 + pad_top:.1f})'>Latency (us)</text>"
    )
    svg.append(
        f"<text x='{width / 2:.1f}' y='{height - 40}' font-size='12' text-anchor='middle'>Sample</text>"
    )

    # Legend
    legend_x = width - pad_right - 260
    legend_y = 18
    legend_w = 240
    legend_h = 28 + len(series) * 16
    svg.append(
        f"<rect x='{legend_x - 10}' y='{legend_y - 12}' width='{legend_w}' height='{legend_h}' fill='white' stroke='#D0D0D0'/>"
    )
    for idx, item in enumerate(series):
        y = legend_y + idx * 16
        svg.append(
            f"<line x1='{legend_x}' y1='{y}' x2='{legend_x + 18}' y2='{y}' stroke='{item['color']}' stroke-width='3'/>"
        )
        svg.append(
            f"<text x='{legend_x + 24}' y='{y + 4}' font-size='11'>{item['label']}</text>"
        )

    # Summary lines
    summary_y = height - 20
    for idx, item in enumerate(series):
        stats = item["stats"]
        text = (
            f"{item['label']}: N={stats['n']} "
            f"min={stats['min']:.2f} "
            f"median={stats['median']:.2f} "
            f"mean={stats['mean']:.2f} "
            f"max={stats['max']:.2f}"
        )
        svg.append(
            f"<text x='{pad_left}' y='{summary_y + idx * 14}' font-size='11' fill='{item['color']}'>{text}</text>"
        )
    svg.append("</svg>")
    path.write_text("\n".join(svg))


def render_matplotlib(xs, series, path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    data = [item["ys"] for item in series]
    labels = ["Fault entry", "End-to-end"]
    colors = [item["color"] for item in series]
    bp = ax.boxplot(
        data,
        labels=labels,
        showmeans=True,
        meanline=True,
        patch_artist=True,
        whis=1.5,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.2)
        patch.set_edgecolor(color)
    for element in ("whiskers", "caps"):
        for line in bp[element]:
            line.set_color("#555555")
    for median in bp["medians"]:
        median.set_color("#222222")
    for mean_line in bp["means"]:
        mean_line.set_color("#222222")
    ax.set_ylabel("Latency (us)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(path)


def load_csv(csv_path):
    rows = []
    with Path(csv_path).open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    return rows


def compute_stats(ys):
    return {
        "n": len(ys),
        "min": min(ys),
        "max": max(ys),
        "mean": statistics.mean(ys),
        "median": statistics.median(ys),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Collect or render BMS latency samples.")
    parser.add_argument("--render-only", action="store_true", help="Render SVG from existing CSV without sampling.")
    parser.add_argument("--csv", default=str(OUT_CSV), help="CSV input/output path.")
    parser.add_argument("--svg", default=str(OUT_SVG), help="SVG output path.")
    parser.add_argument("--pdf", default=str(OUT_PDF), help="PDF output path.")
    parser.add_argument("--map", default=str(MAP_PATH), help="Map file path for symbol lookup.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.render_only:
        rows = load_csv(args.csv)
        if not rows:
            raise RuntimeError(f"No rows in CSV: {args.csv}")
        xs = [int(r.get("sample", i)) for i, r in enumerate(rows)]
        if "fault_entry_us" in rows[0]:
            fault_ys = [float(r["fault_entry_us"]) for r in rows]
            end_ys = [float(r["end_to_end_us"]) for r in rows]
        else:
            fault_ys = [float(r["latency_us"]) for r in rows]
            end_ys = [float(r["latency_us"]) for r in rows]
        series = [
            {
                "label": "Fault entry (attack → MemManage)",
                "ys": fault_ys,
                "color": "#1E6BD6",
                "stats": compute_stats(fault_ys),
            },
            {
                "label": "End-to-end (attack → task resumes)",
                "ys": end_ys,
                "color": "#D65A1E",
                "stats": compute_stats(end_ys),
            },
        ]
        try:
            render_matplotlib(xs, series, Path(args.pdf))
            render_matplotlib(xs, series, Path(args.svg))
            print(f"Wrote {args.pdf} and {args.svg} from {args.csv}")
        except Exception as exc:
            render_svg(xs, series, Path(args.svg))
            print(f"Wrote {args.svg} from {args.csv}. Matplotlib unavailable: {exc}")
        return

    addrs = {
        "attack_hb": find_addr("g_attack_heartbeat", args.map),
        "monitor_hb": find_addr("g_task_heartbeat", args.map),
        "progress": find_addr("g_progress_flags", args.map),
        "boot": find_addr("g_boot_flag", args.map),
        "attack_end": find_addr("g_attack_end_cyccnt", args.map),
        "attack_latency": find_addr("g_attack_latency_cycles", args.map),
        "attack_cyc": find_addr("kintsugi_attack_cyccnt", args.map),
        "fault_cyc": find_addr("kintsugi_fault_cyccnt", args.map),
        "count": find_addr("kintsugi_memmanage_count", args.map),
        "mmfar": find_addr("kintsugi_last_mmfaddr", args.map),
    }

    run("nrfjprog --family nrf52 --reset")
    time.sleep(1.5)

    rows = []
    boot_flag = memrd_word(addrs["boot"])
    if boot_flag != EXPECTED_BOOT_FLAG:
        print(
            f"Warning: boot flag 0x{boot_flag:08X} != expected 0x{EXPECTED_BOOT_FLAG:08X}. "
            "Firmware may not match the map file."
        )
        resume_cpu()
        time.sleep(0.5)
    prev_count = memrd_word(addrs["count"])
    prev_attack_cyc = memrd_word(addrs["attack_cyc"])
    resume_cpu()
    time.sleep(0.8)
    deadline = time.time() + MAX_WAIT_S

    while len(rows) < SAMPLES and time.time() < deadline:
        count = memrd_word(addrs["count"])
        attack_cyc = memrd_word(addrs["attack_cyc"])
        if attack_cyc == prev_attack_cyc:
            resume_cpu()
            time.sleep(POLL_INTERVAL_S)
            continue

        fault_cyc = memrd_word(addrs["fault_cyc"])
        fault_entry_cycles = (fault_cyc - attack_cyc) & 0xFFFFFFFF
        sample = {
            "sample": len(rows),
            "attack_hb": memrd_word(addrs["attack_hb"]),
            "monitor_hb": memrd_word(addrs["monitor_hb"]),
            "progress": memrd_word(addrs["progress"]),
            "boot": memrd_word(addrs["boot"]),
            "attack_cyc": attack_cyc,
            "fault_cyc": fault_cyc,
            "attack_end_cyc": memrd_word(addrs["attack_end"]),
            "attack_latency_cycles": memrd_word(addrs["attack_latency"]),
            "fault_entry_cycles": fault_entry_cycles,
            "memmanage_count": count,
            "mmfar": memrd_word(addrs["mmfar"]),
        }
        sample["end_to_end_us"] = sample["attack_latency_cycles"] / (CPU_HZ / 1_000_000)
        sample["fault_entry_us"] = fault_entry_cycles / (CPU_HZ / 1_000_000)
        sample["latency_us"] = sample["end_to_end_us"]
        rows.append(sample)
        prev_count = count
        prev_attack_cyc = attack_cyc

        resume_cpu()
        time.sleep(INTERVAL_S)

    if len(rows) < SAMPLES:
        print(f"Warning: collected {len(rows)} samples before timeout.")
    if not rows:
        raise RuntimeError("No latency samples collected. Check flashed firmware and map file.")

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    try:
        import matplotlib.pyplot as plt

        xs = [r["sample"] for r in rows]
        fault_ys = [r["fault_entry_us"] for r in rows]
        end_ys = [r["end_to_end_us"] for r in rows]
        series = [
            {
                "label": "Fault entry (attack → MemManage)",
                "ys": fault_ys,
                "color": "#1E6BD6",
                "stats": compute_stats(fault_ys),
            },
            {
                "label": "End-to-end (attack → task resumes)",
                "ys": end_ys,
                "color": "#D65A1E",
                "stats": compute_stats(end_ys),
            },
        ]
        render_matplotlib(xs, series, OUT_PDF)
        render_matplotlib(xs, series, OUT_SVG)
        print(f"Wrote {OUT_CSV}, {OUT_PDF}, and {OUT_SVG}")
    except Exception as exc:
        xs = [r["sample"] for r in rows]
        fault_ys = [r["fault_entry_us"] for r in rows]
        end_ys = [r["end_to_end_us"] for r in rows]
        series = [
            {
                "label": "Fault entry (attack → MemManage)",
                "ys": fault_ys,
                "color": "#1E6BD6",
                "stats": compute_stats(fault_ys),
            },
            {
                "label": "End-to-end (attack → task resumes)",
                "ys": end_ys,
                "color": "#D65A1E",
                "stats": compute_stats(end_ys),
            },
        ]
        render_svg(xs, series, OUT_SVG)
        print(f"Wrote {OUT_CSV} and {OUT_SVG}. Matplotlib unavailable: {exc}")


if __name__ == "__main__":
    main()
