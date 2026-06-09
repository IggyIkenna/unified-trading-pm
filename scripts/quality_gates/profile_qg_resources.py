#!/usr/bin/env python3
"""Profile quality-gates.sh per-phase WALL-TIME + RAM (peak/mean RSS).

Dependency-free (Linux /proc only). Drives a FULL, no-skip run by setting QG_PROFILE=1
(which base-service.sh honours: it overrides every bypass flag --no-fix/--quick/--skip-*,
disables the green sentinel, and relaxes only the <MAX_DURATION> meta-gate). The run is
pinned to a single core with single-core thread/worker caps so the numbers reflect one core.

Two data sources, both reported:
  - spans  : precise per-phase/per-check timing from the qg_prof markers base-service emits
             to $QG_PROFILE_FILE (authoritative; decomposes the codex block into pip-audit /
             bandit / size-checks / removed-symbols, and measures auto-fix).
  - phases : coarse timeline parsed from stdout [N/6] / STEP headers (full list incl. the
             uninstrumented bits: env, import-patterns, workflow-lint, IS-MTDS, duration).

RAM: a sampler thread sums RSS across the run's process tree (process group) via /proc at
~5 Hz; each sample is bucketed into the span/phase whose [start,end] window contains it.

Usage
-----
    python3 scripts/quality_gates/profile_qg_resources.py --repo instruments-service --core 2
    python3 scripts/quality_gates/profile_qg_resources.py --repo X --outdir <dir>   # share via --outdir

Output defaults to .qg_profile/ (gitignored). Pass --outdir to write somewhere shareable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
PAGE = os.sysconf("SC_PAGE_SIZE")

SECTION_RE = re.compile(r"(?:\[(?:[0-9]+(?:\.[0-9]+)?|ACT)/6\]|STEP [0-9]+\.[0-9]+|\[ACT\])")
FAIL_RE = re.compile(r"❌|✗| FAIL|ERROR")
WARN_RE = re.compile(r"⚠|WARN|warning")
PASS_RE = re.compile(r"✅|✓| PASS")

# Single-core measurement policy. QG_PROFILE=1 also makes base-service.sh force a complete,
# no-skip run (auto-fix + lint + tests + typecheck + codex), disable the green sentinel, and
# relax the duration meta-gate — so the profile always measures the WHOLE gate.
MEASURE_ENV = {
    "QG_PROFILE": "1",
    "QG_GOVERNOR_DISABLE": "true",  # don't serialize parallel measurement on the flock tokens
    "QG_THREAD_CAP": "1",  # single-core: OMP/BLAS/MKL = 1
    "PYTEST_WORKERS": "1",  # single-core: no xdist
    "QG_MEM_CAP": "0",  # no cgroup wrap -> tree RSS stays visible + no SIGKILL skew
    "PYTHONUNBUFFERED": "1",  # prompt child-stdout flush
}


def pgid_tree_rss(pgid: int) -> int:
    total = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as f:
                stat = f.read()
            after = stat[stat.rindex(")") + 2 :].split()
            if int(after[2]) != pgid:  # pgrp
                continue
            with open(f"/proc/{entry}/statm") as f:
                total += int(f.read().split()[1]) * PAGE
        except (FileNotFoundError, ProcessLookupError, ValueError, IndexError):
            continue
    return total


def _status_of(line: str) -> str:
    if FAIL_RE.search(line):
        return "fail"
    if WARN_RE.search(line):
        return "warn"
    if PASS_RE.search(line):
        return "pass"
    return "unknown"


def _bucket(start: float, end: float, samples: list[tuple[float, int]]) -> tuple[int, float, int]:
    peak = 0
    vals: list[int] = []
    for ts, rss in samples:
        if start <= ts < end:
            vals.append(rss)
            peak = max(peak, rss)
    mean = sum(vals) / len(vals) if vals else 0.0
    return peak, mean, len(vals)


@dataclass
class Phase:
    name: str
    start: float
    end: float = 0.0
    status: str = "unknown"
    peak_rss: int = 0
    rss_samples: list[int] = field(default_factory=list[int])

    def to_dict(self) -> dict[str, object]:
        mean = sum(self.rss_samples) / len(self.rss_samples) if self.rss_samples else 0
        return {
            "name": self.name,
            "wall_s": round(self.end - self.start, 2),
            "peak_rss_mb": round(self.peak_rss / 1024 / 1024, 1),
            "mean_rss_mb": round(mean / 1024 / 1024, 1),
            "samples": len(self.rss_samples),
            "status": self.status,
        }


def git_sha(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], text=True).strip()
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def _spans_from_markers(markers_path: Path, samples: list[tuple[float, int]]) -> list[dict[str, object]]:
    """Pair qg_prof start/end markers (epoch ts) into named spans + bucket RSS. Overlap/nesting OK."""
    if not markers_path.exists():
        return []
    open_starts: dict[str, float] = {}
    spans: list[dict[str, object]] = []
    for ln in markers_path.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
            ts, ev, name = float(d["ts"]), str(d["event"]), str(d["name"])
        except (ValueError, KeyError):
            continue
        if ev == "start":
            open_starts[name] = ts
        elif ev == "end" and name in open_starts:
            st = open_starts.pop(name)
            peak, mean, n = _bucket(st, ts, samples)
            spans.append(
                {
                    "name": name,
                    "wall_s": round(ts - st, 2),
                    "peak_rss_mb": round(peak / 1024 / 1024, 1),
                    "mean_rss_mb": round(mean / 1024 / 1024, 1),
                    "samples": n,
                }
            )
    return spans


def profile(repo: Path, core: int, markers_path: Path) -> dict[str, object]:
    qg = repo / "scripts" / "quality-gates.sh"
    if not qg.exists():
        raise SystemExit(f"no quality-gates.sh at {qg}")

    markers_path.parent.mkdir(parents=True, exist_ok=True)
    if markers_path.exists():
        markers_path.unlink()
    env = {**os.environ, **MEASURE_ENV, "QG_PROFILE_FILE": str(markers_path)}
    cmd = ["taskset", "-c", str(core), "stdbuf", "-oL", "-eL", "bash", str(qg)]  # NO --no-fix: full run

    samples: list[tuple[float, int]] = []  # (epoch_ts, rss_bytes) — epoch so it aligns with qg_prof markers
    stdout_markers: list[tuple[float, str, str, str]] = []  # (ts, token, kind, status)
    stop = threading.Event()

    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,  # pgid == proc.pid
    )
    pgid = proc.pid

    def sampler() -> None:
        while not stop.is_set():
            rss = pgid_tree_rss(pgid)
            if rss:
                samples.append((time.time(), rss))
            time.sleep(0.2)

    st = threading.Thread(target=sampler, daemon=True)
    st.start()

    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        m = SECTION_RE.search(line)
        if m:
            token = m.group(0)
            kind = "start" if token.startswith("[") else "end"
            stdout_markers.append((time.time(), token, kind, _status_of(line)))

    proc.wait()
    t_end = time.time()
    stop.set()
    st.join(timeout=2)

    # coarse phases from stdout (attribute each segment exactly once; see prior validation)
    phases: list[Phase] = []
    seg_start, cur_label, cur_status = t0, "(_preamble)", "pass"
    for ts, token, kind, status in stdout_markers:
        if kind == "end":
            phases.append(Phase(name=token, start=seg_start, end=ts, status=status))
        else:
            phases.append(Phase(name=cur_label, start=seg_start, end=ts, status=cur_status))
            cur_label, cur_status = token, status
        seg_start = ts
    phases.append(Phase(name=cur_label, start=seg_start, end=t_end, status=cur_status))
    for ph in phases:
        ph.peak_rss, _, _ = _bucket(ph.start, ph.end, samples)
        ph.rss_samples = [rss for ts, rss in samples if ph.start <= ts < ph.end]

    spans = _spans_from_markers(markers_path, samples)
    overall_peak = max((rss for _, rss in samples), default=0)
    return {
        "repo": repo.name,
        "sha": git_sha(repo),
        "core": core,
        "exit_code": proc.returncode,
        "total_wall_s": round(t_end - t0, 2),
        "overall_peak_rss_mb": round(overall_peak / 1024 / 1024, 1),
        "rss_samples": len(samples),
        "spans": spans,  # qg_prof-instrumented (authoritative for the heavies)
        "phases": [p.to_dict() for p in phases],  # coarse stdout timeline (full list)
    }


def render(report: dict[str, object]) -> str:
    total = report["total_wall_s"] or 1  # type: ignore[index]
    out = [
        f"\nQG profile — {report['repo']} @ {report['sha']}  (core {report['core']}, exit {report['exit_code']})",
        f"total wall {report['total_wall_s']}s   overall peak RSS {report['overall_peak_rss_mb']} MB   "
        f"({report['rss_samples']} samples)",
    ]
    spans = report["spans"]  # type: ignore[index]
    if spans:
        out += [
            "",
            "── qg_prof spans (instrumented; nested spans overlap) ──",
            f"{'span':<18}{'wall_s':>9}{'%':>6}{'peak_MB':>10}{'mean_MB':>10}",
        ]
        for s in sorted(spans, key=lambda x: x["wall_s"], reverse=True):  # type: ignore[index,return-value]
            pct = s["wall_s"] / total * 100  # type: ignore[index,operator]
            out.append(f"{s['name']:<18}{s['wall_s']:>9}{pct:>5.0f}%{s['peak_rss_mb']:>10}{s['mean_rss_mb']:>10}")  # type: ignore[index]
    out += [
        "",
        "── coarse stdout phases (full timeline) ──",
        f"{'phase':<26}{'wall_s':>9}{'%':>6}{'peak_MB':>10}{'status':>9}",
    ]
    for p in sorted(report["phases"], key=lambda x: x["wall_s"], reverse=True):  # type: ignore[index,arg-type]
        if p["wall_s"] < 0.05:  # hide the negligible sub-second STEP rows
            continue
        pct = p["wall_s"] / total * 100  # type: ignore[index,operator]
        out.append(f"{p['name']:<26}{p['wall_s']:>9}{pct:>5.0f}%{p['peak_rss_mb']:>10}{p['status']:>9}")  # type: ignore[index]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--core", type=int, default=2)
    ap.add_argument("--outdir", type=Path, default=PM_ROOT / ".qg_profile")  # gitignored by default
    args = ap.parse_args()

    repo = WORKSPACE_ROOT / args.repo
    args.outdir.mkdir(parents=True, exist_ok=True)
    markers_path = args.outdir / f"{args.repo}.markers.jsonl"
    report = profile(repo, args.core, markers_path)
    table = render(report)
    print(table)
    (args.outdir / f"{args.repo}.json").write_text(json.dumps(report, indent=2))
    (args.outdir / f"{args.repo}.txt").write_text(table + "\n")
    print(f"\nwrote {args.outdir / (args.repo + '.json')}")


if __name__ == "__main__":
    main()
