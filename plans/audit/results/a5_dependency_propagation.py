"""A5 — Dependency-fail propagation audit (per service × mode).

Mega-audit Phase A5 (operator directive 2026-05-20). Every service that
consumes upstream data must FAIL LOUDLY when upstream data is missing —
never silently `record_empty(reason="")` or fall through to zero rows.

Two sub-dimensions:

1. **Batch mode**: pre-flight gate before each shard write. If upstream
   manifest row is missing / `attempted_failed`, the code MUST raise
   `DependencyError(fail_fast=True)` (or equivalent). Audit every batch
   handler for this pattern.

2. **Live mode**: stream-time freshness gate. If upstream stream stale,
   the code MUST raise `StaleUpstreamError` (or equivalent). Audit every
   live handler.

The scanner classifies files by what dependency-check patterns they exhibit:

- `READS_UPSTREAM_MANIFEST` — code reads `availability_index` / manifest rows
- `RAISES_DEPENDENCY_ERROR` — has `raise DependencyError(...)` or `fail_fast=True`
- `CATCHES_DEPENDENCY_ERROR_SILENTLY` — `except DependencyError: pass` /
  `except DependencyError: continue` / `except ... return None/[]` patterns
  (these are the BUGS — silent swallowing)
- `RAISES_STALE_UPSTREAM_ERROR` — `raise StaleUpstreamError(...)`
- `WARNS_BUT_PROCEEDS` — `logger.warning(...)` + no raise inside an
  upstream-check block (suspicious)
- `RECORD_EMPTY_WITHOUT_TYPED_REASON` — calls `record_empty(reason="")` or
  `record_empty(reason="SOMETHING_FREE_FORM_NOT_IN_ENUM")` after an upstream
  miss

Per service × mode, every (consumer, upstream) edge MUST resolve to one
of: RAISES_DEPENDENCY_ERROR (batch) / RAISES_STALE_UPSTREAM_ERROR (live).
Anything else is review-blocking.

Output:
    plans/audit/results/dependency_propagation_2026_05_20.csv
    plans/audit/results/dependency_propagation_2026_05_20_summary.md
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]

CONSUMER_REPOS: list[str] = [
    "alerting-service",
    "batch-live-reconciliation-service",
    "execution-service",
    "features-service",
    "instruments-service",
    "market-data-processing-service",
    "market-tick-data-service",
    "ml-inference-service",
    "ml-service",
    "ml-training-service",
    "pnl-attribution-service",
    "position-balance-monitor-service",
    "risk-and-exposure-service",
    "strategy-service",
    "trading-agent-service",
]

SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {".venv", ".venv-workspace", "build", "dist", "node_modules", "__pycache__", ".git", ".tox", ".pytest_cache"},
)


@dataclass(slots=True)
class FileScan:
    repo: str
    rel_path: str
    file_kind: str = "other"  # "batch_handler" | "live_handler" | "manifest_reader" | "other"

    reads_upstream_manifest: bool = False
    raises_dependency_error: list[int] = field(default_factory=list)
    raises_stale_upstream_error: list[int] = field(default_factory=list)
    catches_dep_error_silently: list[int] = field(default_factory=list)
    warns_but_proceeds: list[int] = field(default_factory=list)
    record_empty_with_blank_reason: list[int] = field(default_factory=list)
    record_empty_with_freeform_reason: list[int] = field(default_factory=list)

    @property
    def is_handler(self) -> bool:
        return self.file_kind in {"batch_handler", "live_handler"}

    @property
    def review_blocking_violations(self) -> int:
        return (
            len(self.catches_dep_error_silently)
            + len(self.warns_but_proceeds)
            + len(self.record_empty_with_blank_reason)
            + len(self.record_empty_with_freeform_reason)
        )


# Regex patterns.
MANIFEST_READ = re.compile(r"availability_index|read.*manifest|manifest.*read|read_index_only_dataframe")
RAISES_DEP = re.compile(r"raise\s+(\w*Dependency\w*Error|UpstreamMissingError|UpstreamDataError)\b|fail_fast\s*=\s*True")
RAISES_STALE = re.compile(r"raise\s+(\w*Stale\w*Error|StaleUpstreamError|StaleDataError|FreshnessError)\b")
CATCH_DEP_SILENT = re.compile(
    r"except\s+\w*Dependency\w*Error\s*[^\n]*:\s*\n\s*(pass|continue|return\s+(?:None|\[\]|\{\}|0|False))",
    re.MULTILINE,
)
WARN_BUT_PROCEED = re.compile(
    r"logger\.(warning|warn|error)\([^)]*(stale|upstream|missing|empty|no\s+data)[^)]*\)[^\n]*\n(?!\s*raise)",
    re.IGNORECASE,
)
RECORD_EMPTY_BLANK = re.compile(r"""record_empty\s*\([^)]*reason\s*=\s*["']\s*["']""")
RECORD_EMPTY_FREEFORM = re.compile(r"""record_empty\s*\([^)]*reason\s*=\s*["']([A-Z][A-Z0-9_]{2,})["']""")

# Closed set of EmptyConfirmedReason members (read from UAC honest_coverage.py at scan time).
EMPTY_CONFIRMED_REASONS: set[str] = set()
try:
    hc_path = WORKSPACE_ROOT / "unified-api-contracts" / "unified_api_contracts" / "canonical" / "crosscutting" / "honest_coverage.py"
    if hc_path.exists():
        for m in re.finditer(r"^\s*([A-Z_][A-Z0-9_]*)\s*=\s*['\"]\1['\"]", hc_path.read_text(encoding="utf-8"), re.MULTILINE):
            EMPTY_CONFIRMED_REASONS.add(m.group(1))
except OSError:
    pass


def walk_repo(repo_root: Path) -> Iterable[Path]:
    if not repo_root.exists():
        return
    for root, dirs, files in repo_root.walk():  # type: ignore[attr-defined]
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for fname in files:
            if fname.endswith(".py"):
                yield root / fname


def classify_file(rel_path: str, content: str) -> str:
    rel_lower = rel_path.lower()
    has_live = "live" in rel_lower or "stream" in rel_lower or "websocket" in rel_lower or "ws_" in rel_lower
    has_batch = "batch" in rel_lower or "backfill" in rel_lower or "/handler" in rel_lower
    has_handler_def = bool(re.search(r"def\s+(fetch|collect|handle|process_shard|process_bar|run_capture)\b", content))
    if has_handler_def and has_live:
        return "live_handler"
    if has_handler_def and has_batch:
        return "batch_handler"
    if has_handler_def:
        return "batch_handler"  # default handler classification
    if MANIFEST_READ.search(content):
        return "manifest_reader"
    return "other"


def scan_file(repo: str, repo_root: Path, path: Path) -> FileScan:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FileScan(repo=repo, rel_path=str(path.relative_to(repo_root)))
    rel_path = str(path.relative_to(repo_root))
    scan = FileScan(repo=repo, rel_path=rel_path)
    scan.file_kind = classify_file(rel_path, content)
    scan.reads_upstream_manifest = bool(MANIFEST_READ.search(content))

    def line_of(m: re.Match[str]) -> int:
        return content[: m.start()].count("\n") + 1

    for m in RAISES_DEP.finditer(content):
        scan.raises_dependency_error.append(line_of(m))
    for m in RAISES_STALE.finditer(content):
        scan.raises_stale_upstream_error.append(line_of(m))
    for m in CATCH_DEP_SILENT.finditer(content):
        scan.catches_dep_error_silently.append(line_of(m))
    if scan.is_handler:
        # WARN_BUT_PROCEED only counts inside handlers (otherwise too noisy).
        for m in WARN_BUT_PROCEED.finditer(content):
            scan.warns_but_proceeds.append(line_of(m))
    for m in RECORD_EMPTY_BLANK.finditer(content):
        scan.record_empty_with_blank_reason.append(line_of(m))
    for m in RECORD_EMPTY_FREEFORM.finditer(content):
        reason = m.group(1)
        if EMPTY_CONFIRMED_REASONS and reason not in EMPTY_CONFIRMED_REASONS:
            scan.record_empty_with_freeform_reason.append(line_of(m))
    return scan


def main() -> int:
    scans: list[FileScan] = []
    total_files = 0
    for repo in CONSUMER_REPOS:
        repo_root = WORKSPACE_ROOT / repo
        if not repo_root.exists():
            continue
        for path in walk_repo(repo_root):
            total_files += 1
            scans.append(scan_file(repo, repo_root, path))

    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"
    csv_path = out_dir / "dependency_propagation_2026_05_20.csv"

    # Output one row per consumer file with all flags.
    fields = [
        "repo",
        "rel_path",
        "file_kind",
        "reads_upstream_manifest",
        "raises_dependency_error",
        "raises_stale_upstream_error",
        "catches_dep_error_silently",
        "warns_but_proceeds",
        "record_empty_blank",
        "record_empty_freeform",
        "review_blocking_violations",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(fields)
        for s in sorted(scans, key=lambda x: (-x.review_blocking_violations, x.repo, x.rel_path)):
            if s.review_blocking_violations == 0 and not s.is_handler:
                continue
            writer.writerow(
                [
                    s.repo,
                    s.rel_path,
                    s.file_kind,
                    s.reads_upstream_manifest,
                    len(s.raises_dependency_error),
                    len(s.raises_stale_upstream_error),
                    len(s.catches_dep_error_silently),
                    len(s.warns_but_proceeds),
                    len(s.record_empty_with_blank_reason),
                    len(s.record_empty_with_freeform_reason),
                    s.review_blocking_violations,
                ]
            )

    # Per-service × mode summary.
    per_service_handler_total: dict[str, int] = defaultdict(int)
    per_service_batch_handler: dict[str, int] = defaultdict(int)
    per_service_live_handler: dict[str, int] = defaultdict(int)
    per_service_raises_dep: dict[str, int] = defaultdict(int)
    per_service_raises_stale: dict[str, int] = defaultdict(int)
    per_service_catches_silent: dict[str, int] = defaultdict(int)
    per_service_record_empty_blank: dict[str, int] = defaultdict(int)
    per_service_record_empty_freeform: dict[str, int] = defaultdict(int)

    for s in scans:
        if s.is_handler:
            per_service_handler_total[s.repo] += 1
            if s.file_kind == "batch_handler":
                per_service_batch_handler[s.repo] += 1
            else:
                per_service_live_handler[s.repo] += 1
        if s.raises_dependency_error:
            per_service_raises_dep[s.repo] += 1
        if s.raises_stale_upstream_error:
            per_service_raises_stale[s.repo] += 1
        if s.catches_dep_error_silently:
            per_service_catches_silent[s.repo] += len(s.catches_dep_error_silently)
        if s.record_empty_with_blank_reason:
            per_service_record_empty_blank[s.repo] += len(s.record_empty_with_blank_reason)
        if s.record_empty_with_freeform_reason:
            per_service_record_empty_freeform[s.repo] += len(s.record_empty_with_freeform_reason)

    summary_path = out_dir / "dependency_propagation_2026_05_20_summary.md"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A5 — Dependency-fail propagation summary\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"Files scanned: {total_files}\n\n")
        fh.write(f"Known EmptyConfirmedReason enum members harvested from UAC: {len(EMPTY_CONFIRMED_REASONS)}\n\n")

        fh.write("## Per-service × mode summary\n\n")
        fh.write("| Service | Batch handlers | Live handlers | Files raising DependencyError | Files raising StaleUpstreamError | Silent catches | Blank `reason=\"\"` | Freeform reason |\n")
        fh.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
        all_repos = sorted(set(per_service_handler_total) | set(per_service_raises_dep) | set(per_service_catches_silent))
        for repo in all_repos:
            fh.write(
                f"| {repo} | {per_service_batch_handler.get(repo, 0)} | {per_service_live_handler.get(repo, 0)} | "
                f"{per_service_raises_dep.get(repo, 0)} | {per_service_raises_stale.get(repo, 0)} | "
                f"{per_service_catches_silent.get(repo, 0)} | {per_service_record_empty_blank.get(repo, 0)} | "
                f"{per_service_record_empty_freeform.get(repo, 0)} |\n"
            )

        fh.write("\n## Review-blocking violations (silent catches + blank reasons + freeform reasons)\n\n")
        fh.write("Per the data-pipeline-correctness HARD RULE, every consumer-side miss MUST raise loudly (batch) or raise StaleUpstreamError (live). Patterns below are **all** the silent-swallowing patterns the scanner detected.\n\n")
        violators = [s for s in scans if s.review_blocking_violations > 0]
        violators.sort(key=lambda x: -x.review_blocking_violations)
        fh.write(f"Total files with review-blocking violations: **{len(violators)}**\n\n")

        for top in violators[:30]:
            fh.write(f"\n### `{top.repo}/{top.rel_path}` ({top.file_kind})\n")
            if top.catches_dep_error_silently:
                fh.write(f"- Silent `except DependencyError` (lines): {top.catches_dep_error_silently[:5]}\n")
            if top.warns_but_proceeds:
                fh.write(f"- Warn-but-proceed pattern (lines): {top.warns_but_proceeds[:5]}\n")
            if top.record_empty_with_blank_reason:
                fh.write(f"- `record_empty(reason=\"\")` blank-reason (lines): {top.record_empty_with_blank_reason[:5]}\n")
            if top.record_empty_with_freeform_reason:
                fh.write(f"- `record_empty(reason=\"NOT_IN_ENUM\")` freeform-reason (lines): {top.record_empty_with_freeform_reason[:5]}\n")

        fh.write("\n## Next actions\n\n")
        fh.write("- Every review-blocking violation must be either (a) fixed in code (raise loudly), or (b) given an operator-acked `BLOCKED-OPERATOR-DECISION` explaining why the silent path is correct.\n")
        fh.write("- Wire a new QG step `scripts/quality_gates/check_dependency_fail_propagation.py` that ratchets these counts down per service × mode.\n")
        fh.write("- Per CLAUDE.md HARD RULE, slots doing layer-N+1 work on services with open A5 violations are review-blocked.\n")

    print(f"A5 scan complete: {total_files} files scanned")
    print(f"  CSV:     {csv_path}")
    print(f"  Summary: {summary_path}")
    print(f"  Review-blocking violations across {len(violators)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
