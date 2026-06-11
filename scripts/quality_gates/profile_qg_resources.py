#!/usr/bin/env python3
"""Profile quality-gates.sh per-phase WALL-TIME + RAM (peak/mean RSS).

Dependency-free. Drives a FULL, no-skip run by setting QG_PROFILE=1 (which
base-service.sh AND base-library.sh honour: it overrides every bypass flag
--no-fix/--quick/--skip-*, disables the green sentinel, and relaxes only the
<MAX_DURATION> meta-gate). The run is pinned to a single core with single-core
thread/worker caps so the numbers reflect one core.

Two data sources, both reported:
  - spans  : precise per-phase/per-check timing from the qg_prof markers the bases emit
             to $QG_PROFILE_FILE (authoritative; decomposes the codex block into pip-audit /
             bandit / size-checks / removed-symbols, and measures auto-fix).
  - phases : coarse timeline parsed from stdout [N/6] / STEP headers (full list incl. the
             uninstrumented bits: env, import-patterns, workflow-lint, IS-MTDS, duration).

RAM: a sampler thread sums RSS across the run's process tree (process group) at ~5 Hz —
via /proc on Linux (canonical sweep host), via `ps -o pgid,rss` on macOS (portable
fallback; indicative only). Each sample is bucketed into the span/phase whose
[start,end] window contains it. Core pinning uses taskset when available (Linux);
on hosts without taskset the run is UNPINNED and the report says so — treat those
numbers as indicative, the canonical 22-repo sweep runs on a pinned Linux host.

Usage
-----
    python3 scripts/quality_gates/profile_qg_resources.py --repo instruments-service --core 2
    python3 scripts/quality_gates/profile_qg_resources.py --repos a,b,c          # SERIAL sweep
    python3 scripts/quality_gates/profile_qg_resources.py --repo X --outdir <dir>
    python3 scripts/quality_gates/profile_qg_resources.py --all --parallel       # PARALLEL-PINNED sweep
    python3 scripts/quality_gates/profile_qg_resources.py --repos a,b,c --parallel --ram-budget-gb 32

--repos / --repo runs SERIALLY by default (one full gate at a time — host-capacity safe).
--parallel turns on the pinned RAM-budget scheduler (Phase-0 plan item): each repo runs on
its OWN core (taskset) concurrently, gated by a RAM-token budget so the host never swaps and
the heavy libraries (UTL/UAC) don't pile together. Each concurrent run still measures TRUE
single-core wall-time (its own pinned core + single-core thread/worker caps). --all discovers
every sibling dir that has scripts/quality-gates.sh.

Both modes write per-repo JSON + .txt + the plan's combined CSV
(repo,phase,wall_s,peak_rss_mb,mean_rss_mb,status) and a cross-repo summary table.

Output ALWAYS lands in the gitignored .qg_profile/ scratch dir (these are large raw
intermediates, NOT committed — only an authored summary .md is). --outdir may override the
location but MUST be a gitignored / scratch path: the script refuses a git-tracked outdir so a
profile run can never dirty a repo (2026-06-11 — an earlier run wrote into a tracked plans/
dir + the gate's auto-fix reformatted 20+ repos; both are now structurally prevented).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
PAGE = os.sysconf("SC_PAGE_SIZE")

# Heavy libraries — measured ~5.3 GB peak RSS (UTL) — reserve more of the RAM budget so two
# never schedule together and the host never swaps (which would corrupt single-core wall-time).
HEAVY_REPOS = {"unified-trading-library", "unified-api-contracts"}

SECTION_RE = re.compile(r"(?:\[(?:[0-9]+(?:\.[0-9]+)?|ACT)/6\]|STEP [0-9]+\.[0-9]+|\[ACT\])")

# Human labels for the coarse stdout phase tokens (the authoritative timing is the qg_prof spans,
# which already carry clean names — this just makes the fallback timeline readable too).
PHASE_LABELS = {
    "[0/6]": "environment",
    "[1/6]": "auto-fix",
    "[2/6]": "lint",
    "[3/6]": "tests",
    "[3.5/6]": "coverage-report",
    "[4/6]": "typecheck",
    "[5/6]": "codex-compliance",
    "[ACT]": "actionlint",
}


def _label(token: str) -> str:
    """Map a coarse phase token to a human name; pass STEP x.y / unknowns through unchanged."""
    return PHASE_LABELS.get(token, token)


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


HAS_PROC = os.path.isdir("/proc")


def _pgid_tree_rss_proc(pgid: int) -> int:
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


def _pgid_tree_rss_ps(pgid: int) -> int:
    """macOS/BSD fallback: sum `ps` RSS (KiB) across the process group."""
    try:
        out = subprocess.run(
            ["ps", "-ax", "-o", "pgid=,rss="], capture_output=True, text=True, timeout=5, check=False
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return 0
    total = 0
    want = str(pgid)
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) == 2 and parts[0] == want:
            try:
                total += int(parts[1]) * 1024
            except ValueError:
                continue
    return total


def pgid_tree_rss(pgid: int) -> int:
    return _pgid_tree_rss_proc(pgid) if HAS_PROC else _pgid_tree_rss_ps(pgid)


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
            rec = cast("dict[str, object]", json.loads(ln))
            ts, ev, name = float(str(rec["ts"])), str(rec["event"]), str(rec["name"])
        except (ValueError, KeyError, TypeError):
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


def profile(
    repo: Path, core: int, markers_path: Path, *, quiet: bool = False, raw_log: Path | None = None
) -> dict[str, object]:
    qg = repo / "scripts" / "quality-gates.sh"
    if not qg.exists():
        raise SystemExit(f"no quality-gates.sh at {qg}")

    markers_path.parent.mkdir(parents=True, exist_ok=True)
    if markers_path.exists():
        markers_path.unlink()
    env = {**os.environ, **MEASURE_ENV, "QG_PROFILE_FILE": str(markers_path)}
    # taskset = Linux-only; without it (macOS) the run is UNPINNED (indicative numbers only).
    # stdbuf = GNU coreutils; optional — without it stdout phase timestamps are slightly coarser.
    pinned = shutil.which("taskset") is not None
    cmd: list[str] = ["taskset", "-c", str(core)] if pinned else []
    if shutil.which("stdbuf"):
        cmd += ["stdbuf", "-oL", "-eL"]
    cmd += ["bash", str(qg)]  # NO --no-fix: full run

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

    # In parallel mode many gates stream at once -> echoing to the shared terminal interleaves
    # into noise, so route each repo's raw gate stdout to its own <repo>.log instead. The
    # SECTION_RE phase-marker parsing happens regardless (it drives the coarse timeline).
    assert proc.stdout is not None
    with open(raw_log, "w") if raw_log is not None else contextlib.nullcontext(None) as log_fh:
        for line in proc.stdout:
            if log_fh is not None:
                log_fh.write(line)
            elif not quiet:
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
    # Completeness: did the two heavy, measure-critical phases actually run? A gate that early-bails
    # (e.g. missing pytest-timeout in the venv → exits at TESTS) yields PARTIAL timing that must NOT
    # be averaged in. "[N/6]" banners are the phase indices reached: [3/6]=TESTS, [4/6]=TYPE CHECK.
    idxs = {int(m[1][1]) for m in stdout_markers if m[1][:1] == "[" and m[1][1:2].isdigit()}
    ran_tests = 3 in idxs
    ran_typecheck = 4 in idxs
    return {
        "repo": repo.name,
        "sha": git_sha(repo),
        "core": core,
        "pinned": pinned,
        "exit_code": proc.returncode,
        "ran_tests": ran_tests,
        "ran_typecheck": ran_typecheck,
        "complete": ran_tests and ran_typecheck,  # both heavy phases executed → timing is usable
        "total_wall_s": round(t_end - t0, 2),
        "overall_peak_rss_mb": round(overall_peak / 1024 / 1024, 1),
        "rss_samples": len(samples),
        "spans": spans,  # qg_prof-instrumented (authoritative for the heavies)
        "phases": [p.to_dict() for p in phases],  # coarse stdout timeline (full list)
    }


def render(report: dict[str, object]) -> str:
    total = report["total_wall_s"] or 1  # type: ignore[index]
    pin = f"core {report['core']}" if report.get("pinned") else "UNPINNED (no taskset — indicative)"
    out = [
        f"\nQG profile — {report['repo']} @ {report['sha']}  ({pin}, exit {report['exit_code']})",
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
        label = _label(str(p["name"]))  # type: ignore[index]
        out.append(f"{label:<26}{p['wall_s']:>9}{pct:>5.0f}%{p['peak_rss_mb']:>10}{p['status']:>9}")  # type: ignore[index]
    return "\n".join(out)


def csv_rows(report: dict[str, object]) -> list[str]:
    """Plan-schema rows: repo,phase,wall_s,peak_rss_mb,mean_rss_mb,status.

    Span rows (authoritative, instrumented) are prefixed `span:`; coarse stdout
    phases keep their banner token as the phase name and carry the parsed status.
    """
    rows: list[str] = []
    repo = str(report["repo"])
    for s in report["spans"]:  # type: ignore[index,union-attr]
        rows.append(f"{repo},span:{s['name']},{s['wall_s']},{s['peak_rss_mb']},{s['mean_rss_mb']},-")  # type: ignore[index]
    for p in report["phases"]:  # type: ignore[index,union-attr]
        name = _label(str(p["name"])).replace(",", ";")  # type: ignore[index]
        rows.append(f"{repo},{name},{p['wall_s']},{p['peak_rss_mb']},{p['mean_rss_mb']},{p['status']}")  # type: ignore[index]
    return rows


def run_one(repo_name: str, core: int, outdir: Path, *, quiet: bool = False) -> dict[str, object]:
    repo = WORKSPACE_ROOT / repo_name
    markers_path = outdir / f"{repo_name}.markers.jsonl"
    raw_log = outdir / f"{repo_name}.log" if quiet else None
    report = profile(repo, core, markers_path, quiet=quiet, raw_log=raw_log)
    table = render(report)
    (outdir / f"{repo_name}.json").write_text(json.dumps(report, indent=2))
    (outdir / f"{repo_name}.txt").write_text(table + "\n")
    if not quiet:
        print(table)
        print(f"\nwrote {outdir / (repo_name + '.json')}")
    return report


def discover_repos() -> list[str]:
    """Every sibling dir under the workspace root that ships a quality-gates.sh (the 22-repo set)."""
    return sorted(
        p.name for p in WORKSPACE_ROOT.iterdir() if p.is_dir() and (p / "scripts" / "quality-gates.sh").is_file()
    )


def _is_git_tracked_dir(path: Path) -> bool:
    """True if path is inside a git work-tree AND not gitignored (writing there would dirty the repo)."""
    parent = path if path.exists() else path.parent
    try:
        inside = subprocess.run(
            ["git", "-C", str(parent), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return False  # not in a git repo → safe
        ign = subprocess.run(  # exits 0 iff the path IS ignored
            ["git", "-C", str(parent), "check-ignore", "-q", str(path)], capture_output=True, check=False
        )
        return ign.returncode != 0  # not ignored → would dirty the repo
    except (subprocess.SubprocessError, OSError):
        return False  # can't determine → don't block the run


def _mem_available_gb() -> float:
    """Best-effort free RAM (GiB). MemAvailable on Linux; conservative 16 GB fallback elsewhere."""
    try:
        for ln in Path("/proc/meminfo").read_text().splitlines():
            if ln.startswith("MemAvailable:"):
                return int(ln.split()[1]) / 1024 / 1024  # kB -> GiB
    except (OSError, ValueError, IndexError):
        pass
    return 16.0


def schedule_parallel(
    names: list[str],
    cores: list[int],
    outdir: Path,
    *,
    ram_budget_gb: float,
    per_repo_gb: float,
    heavy_gb: float,
    live_floor_gb: float,
) -> list[dict[str, object]]:
    """Run each repo on its OWN pinned core, concurrently, under a RAM-token budget.

    THREE limiters compose: (1) a free-core queue — at most len(cores) gates run at once, each on a
    distinct core; (2) a weighted RAM-TOKEN budget — a repo reserves `heavy_gb` (UTL/UAC) or
    `per_repo_gb` and blocks until that much budget is free, so two heavies never overlap; (3) a LIVE
    headroom gate — before launching a NEW gate while one is already running, ACTUAL `MemAvailable`
    must exceed `live_floor_gb`, so if the host's other apps grab RAM mid-sweep we stop adding load
    instead of swapping. The live gate never blocks the FIRST/only job (progress must be made).
    """
    core_q: queue.Queue[int] = queue.Queue()
    for c in cores:
        core_q.put(c)

    budget_lock = threading.Condition()
    budget = {"free": ram_budget_gb}
    running = {"n": 0}
    results: list[dict[str, object]] = []
    results_lock = threading.Lock()
    done = {"n": 0}
    total = len(names)

    def weight(name: str) -> float:
        return heavy_gb if name in HEAVY_REPOS else per_repo_gb

    def acquire(w: float) -> None:
        with budget_lock:
            # (2) RAM-token budget + (3) live headroom — but never block when nothing is running yet.
            while budget["free"] < w or (running["n"] > 0 and _mem_available_gb() < live_floor_gb):
                budget_lock.wait(timeout=3.0)  # timeout → re-poll live RAM even without a release
            budget["free"] -= w
            running["n"] += 1

    def release(w: float) -> None:
        with budget_lock:
            budget["free"] += w
            running["n"] -= 1
            budget_lock.notify_all()

    def worker(name: str) -> None:
        w = weight(name)
        acquire(w)
        core = core_q.get()
        print(f"[start] {name:<34} core {core:>2}  (weight {w:g}G, budget {budget['free']:g}G free)", flush=True)
        report: dict[str, object]
        try:
            report = run_one(name, core, outdir, quiet=True)
        except SystemExit as exc:  # no quality-gates.sh etc. — record + keep the sweep alive
            report = {
                "repo": name,
                "exit_code": -1,
                "total_wall_s": 0.0,
                "error": f"{exc!s}",
                "complete": False,
                "overall_peak_rss_mb": 0.0,
                "spans": [],
                "phases": [],
            }
        finally:
            core_q.put(core)
            release(w)
        with results_lock:
            results.append(report)
            done["n"] += 1
        print(
            f"[done ] {name:<34} core {core:>2}  wall {report.get('total_wall_s')}s  "
            f"peak {report.get('overall_peak_rss_mb')}MB  exit {report.get('exit_code')}  "
            f"({done['n']}/{total})",
            flush=True,
        )

    with ThreadPoolExecutor(max_workers=len(cores)) as pool:
        list(pool.map(worker, names))
    return results


def summary_table(reports: list[dict[str, object]]) -> str:
    """Cross-repo headline: total wall + peak RSS per repo, slowest first."""
    rows = sorted(reports, key=lambda r: cast("float", r.get("total_wall_s") or 0), reverse=True)
    out = [
        "",
        "── cross-repo summary (slowest first; ⚠=PARTIAL run, timing not usable) ──",
        f"{'repo':<36}{'wall_s':>9}{'peak_MB':>10}{'exit':>6}  run",
    ]
    grand = 0.0
    partial: list[str] = []
    for r in rows:
        wall = cast("float", r.get("total_wall_s") or 0)
        grand += wall
        complete = r.get("complete", True)
        flag = "full" if complete else "⚠PARTIAL"
        if not complete:
            partial.append(str(r.get("repo")))
        out.append(
            f"{r.get('repo')!s:<36}{wall:>9}{cast('float', r.get('overall_peak_rss_mb') or 0):>10}"
            f"{cast('int', r.get('exit_code')):>6}  {flag}"
        )
    out.append(f"{'TOTAL (serial-equivalent)':<36}{round(grand, 1):>9}")
    if partial:
        out.append(f"\n⚠ PARTIAL (early-bail, incomplete venv? — exclude from timing): {', '.join(partial)}")
    return "\n".join(out)


def write_outputs(reports: list[dict[str, object]], outdir: Path) -> None:
    all_rows: list[str] = []
    for r in reports:
        if r.get("phases") is not None:
            all_rows += csv_rows(r)
    csv_path = outdir / "combined.csv"
    csv_path.write_text("repo,phase,wall_s,peak_rss_mb,mean_rss_mb,status\n" + "\n".join(all_rows) + "\n")
    table = summary_table(reports)
    print(table)
    (outdir / "summary.txt").write_text(table + "\n")
    print(f"\nwrote {csv_path} ({len(all_rows)} rows, {len(reports)} repo(s)) + {outdir / 'summary.txt'}")
    failures = [str(r.get("repo")) for r in reports if r.get("exit_code") != 0]
    if failures:
        print(f"non-zero gate exit for: {', '.join(failures)} (profile still captured)")


class _Args(argparse.Namespace):
    repo: str | None = None
    repos: str | None = None
    all: bool = False
    parallel: bool = False
    core: int = 2
    cores: int | None = None
    ram_budget_gb: float | None = None
    per_repo_gb: float = 4.0
    heavy_gb: float = 6.5
    outdir: Path = PM_ROOT / ".qg_profile"  # gitignored by default


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--repo", help="single repo name (directory under the workspace root)")
    grp.add_argument("--repos", help="comma-separated repo names")
    grp.add_argument("--all", action="store_true", help="every sibling repo with a quality-gates.sh")
    ap.add_argument("--parallel", action="store_true", help="host-adaptive concurrent sweep (else serial)")
    ap.add_argument("--core", type=int, default=2, help="serial mode: the single core to pin to")
    ap.add_argument(
        "--cores", type=int, default=None, help="parallel: CAP on concurrent gates (default: host-derived, see below)"
    )
    ap.add_argument(
        "--ram-budget-gb", type=float, default=None, help="parallel: RAM budget (default 0.75 * live MemAvailable)"
    )
    ap.add_argument("--per-repo-gb", type=float, default=4.0, help="parallel: RAM reserved per normal repo")
    ap.add_argument(
        "--heavy-gb", type=float, default=6.5, help=f"parallel: RAM reserved per heavy repo {sorted(HEAVY_REPOS)}"
    )
    ap.add_argument("--outdir", "--output", dest="outdir", type=Path, default=PM_ROOT / ".qg_profile")
    args = ap.parse_args(namespace=_Args())

    # ABSOLUTE outdir: the gate subprocess runs with cwd=<repo>, so a RELATIVE marker path would
    # resolve inside each repo (pollutes the tree + the report can't read the spans back). Resolve once.
    args.outdir = args.outdir.resolve()
    # GUARD: refuse a git-TRACKED outdir — reports are gitignored scratch, never repo dirt.
    if _is_git_tracked_dir(args.outdir):
        sys.exit(
            f"refusing to write reports to a git-tracked path: {args.outdir}\n"
            f"reports are large scratch intermediates — point --outdir at a gitignored dir "
            f"(default: {PM_ROOT / '.qg_profile'})."
        )

    if args.all:
        names = discover_repos()
    else:
        raw = args.repos.split(",") if args.repos else [args.repo or ""]
        names = [n.strip() for n in raw if n.strip()]
    args.outdir.mkdir(parents=True, exist_ok=True)

    if args.parallel:
        # ── HOST-ADAPTIVE concurrency: derive from THIS machine, never assume a big host. ──
        cpu = os.cpu_count() or 2
        avail = _mem_available_gb()
        budget = args.ram_budget_gb if args.ram_budget_gb is not None else round(avail * 0.75, 1)
        # Reserve cores for the OS only when there are cores to spare (low-core PCs keep ~all).
        reserve = 2 if cpu > 4 else (1 if cpu > 2 else 0)
        max_by_cpu = max(1, cpu - reserve)
        max_by_ram = max(1, int(budget // args.per_repo_gb))  # how many normal gates fit the budget
        ncores = min(max_by_cpu, max_by_ram, args.cores if args.cores is not None else max_by_cpu)
        cores = list(range(reserve, reserve + ncores))  # valid indices on any core count
        # Live floor: don't START a new gate (while one runs) unless real free RAM clears one repo + margin.
        live_floor = round(args.per_repo_gb + 1.0, 1)
        mode = "SERIAL (host headroom only fits 1 gate)" if ncores == 1 else f"{ncores}-way PARALLEL"
        print(
            f"host: {cpu} cores / {avail:.1f}G MemAvailable -> {mode}\n"
            f"  cores {cores[0]}-{cores[-1]} | RAM budget {budget}G (per-repo {args.per_repo_gb}G / "
            f"heavy {args.heavy_gb}G) | live-floor {live_floor}G | outdir {args.outdir}\n"
        )
        reports = schedule_parallel(
            names,
            cores,
            args.outdir,
            ram_budget_gb=budget,
            per_repo_gb=args.per_repo_gb,
            heavy_gb=args.heavy_gb,
            live_floor_gb=live_floor,
        )
    else:
        reports = [run_one(name, args.core, args.outdir) for name in names]

    write_outputs(reports, args.outdir)


if __name__ == "__main__":
    main()
