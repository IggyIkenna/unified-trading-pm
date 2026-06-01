"""Orchestrate the 4 engine paths, each in its own subprocess.

Each subprocess gets a fresh address space (no cross-path arena pollution).
Within one subprocess, the runner iterates all 9 instrument parquets so
cumulative arena retention shows up in the rss_retention_mb metric.

Output: per-path JSON results captured; final markdown summary written to
results.md in the same directory.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
DATA = Path("/tmp/mdps_bench_data")
RUNNER = HERE / "path_runner.py"
OUT_ROOT = Path(tempfile.mkdtemp(prefix="mdps_bench_out_"))
PATHS = ["A", "B", "C", "D"]


def run_one(path_id: str) -> dict:
    out_dir = OUT_ROOT / path_id
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["uv", "run", "python", str(RUNNER), path_id, str(DATA), str(out_dir)]
    print(f"\n=== PATH {path_id} ===", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    if proc.returncode != 0:
        print(f"PATH {path_id} failed exit={proc.returncode}\nstderr:\n{proc.stderr}", file=sys.stderr)
        sys.exit(proc.returncode)
    return json.loads(proc.stdout.strip().splitlines()[-1])


def summarize(results: dict[str, dict]) -> str:
    lines = []
    lines.append("# MDPS engine benchmark - results")
    lines.append("")
    lines.append("Versions (same across all paths):")
    a = next(iter(results.values()))
    lines.append(f"  polars  {a['polars']}")
    lines.append(f"  pandas  {a['pandas']}")
    lines.append(f"  pyarrow {a['pyarrow']}")
    lines.append(f"  python  {a['python']}")
    lines.append("")
    lines.append(f"Data: {a['n_instruments']} BINANCE-FUTURES perp trades parquets for 2026-04-15.")
    lines.append("Each path processes ALL N instruments in a single Python process,")
    lines.append("running each in its own subprocess to isolate cross-path arena retention.")
    lines.append("")

    lines.append("## Aggregate per path")
    lines.append("")
    lines.append(
        "| Path | Label | Total wall (s) | Mean wall/instr (s) | Mean peak RSS (MB) | "
        "Final RSS (MB) | Retention vs warmup (MB) |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for pid in PATHS:
        r = results[pid]
        mean_wall = sum(x["wall_clock_s"] for x in r["per_instrument"]) / r["n_instruments"]
        mean_peak = sum(x["peak_rss_mb"] for x in r["per_instrument"]) / r["n_instruments"]
        lines.append(
            f"| {pid} | {r['label']} | {r['total_wall_s']:.1f} | {mean_wall:.2f} | "
            f"{mean_peak:.0f} | {r['rss_final_mb']:.0f} | {r['rss_retention_mb']:.0f} |"
        )
    lines.append("")

    lines.append("## RSS trajectory across instruments (MB)")
    lines.append("")
    lines.append("Each row shows the RSS measurement AFTER each instrument completes,")
    lines.append("post `gc.collect()`. Rising numbers = cumulative arena retention.")
    lines.append("")
    files = [Path(x["file"]).stem.replace("binance-futures-perp-", "") for x in a["per_instrument"]]
    header = "| # | Instrument |" + "".join(f" {pid} ({results[pid]['label']}) |" for pid in PATHS)
    sep = "|---|---|" + "".join("---|" for _ in PATHS)
    lines.append(header)
    lines.append(sep)
    for i, inst in enumerate(files):
        cells = " | ".join(f"{results[pid]['cumulative_rss_after_each_mb'][i]:.0f}" for pid in PATHS)
        lines.append(f"| {i + 1} | {inst} | {cells} |")
    lines.append("")

    lines.append("## Per-instrument wall-clock (s) and peak RSS (MB)")
    lines.append("")
    for pid in PATHS:
        r = results[pid]
        lines.append(f"### Path {pid} - {r['label']}")
        lines.append("")
        lines.append("| Instrument | Size (MB) | Wall (s) | Peak RSS (MB) | RSS after (MB) |")
        lines.append("|---|---|---|---|---|")
        for x in r["per_instrument"]:
            lines.append(
                f"| {x['file'].replace('binance-futures-perp-', '').replace('.parquet', '')} | "
                f"{x['file_size_mb']:.1f} | {x['wall_clock_s']:.2f} | "
                f"{x['peak_rss_mb']:.0f} | {x['rss_after_mb']:.0f} |"
            )
        lines.append("")

    # Headline interpretation
    lines.append("## Headline comparison")
    lines.append("")
    a_total = results["A"]["total_wall_s"]
    b_total = results["B"]["total_wall_s"]
    c_total = results["C"]["total_wall_s"]
    d_total = results["D"]["total_wall_s"]
    a_ret = results["A"]["rss_retention_mb"]
    b_ret = results["B"]["rss_retention_mb"]
    c_ret = results["C"]["rss_retention_mb"]
    d_ret = results["D"]["rss_retention_mb"]
    lines.append(
        f"- **A pure-polars-lazy** vs **C current-mdps-mixed**: "
        f"{a_total / c_total:.2f}x wall, {a_ret - c_ret:+.0f} MB retention delta"
    )
    lines.append(
        f"- **B pandas-pyarrow** vs **C current-mdps-mixed**: "
        f"{b_total / c_total:.2f}x wall, {b_ret - c_ret:+.0f} MB retention delta"
    )
    lines.append(
        f"- **D polars-eager** vs **C current-mdps-mixed**: "
        f"{d_total / c_total:.2f}x wall, {d_ret - c_ret:+.0f} MB retention delta"
    )
    lines.append(
        f"- **A pure-polars-lazy** vs **B pandas-pyarrow**: "
        f"{a_total / b_total:.2f}x wall, {a_ret - b_ret:+.0f} MB retention delta"
    )
    lines.append("")

    return "\n".join(lines)


def main():
    results = {}
    for pid in PATHS:
        results[pid] = run_one(pid)
        print(
            f"  total {results[pid]['total_wall_s']:.1f}s  retention {results[pid]['rss_retention_mb']:.0f}MB",
            flush=True,
        )

    md = summarize(results)
    out_md = HERE / "results.md"
    out_md.write_text(md)
    print(f"\nSummary written to {out_md}")

    out_json = HERE / "results.json"
    out_json.write_text(json.dumps(results, indent=2))
    print(f"Raw JSON at {out_json}")


if __name__ == "__main__":
    main()
