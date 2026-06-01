"""A1 — Codified-shape compliance scanner (Phase A, mega-audit 2026-05-20).

Walks every Python file across the workspace's service repos and checks 10
codified shapes. Output: a CSV with one row per file + the violations across
the 10 checks + a markdown summary.

The 10 checks are workspace-canonical patterns (see CLAUDE.md + the master
tracker `plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`).
Each check is a static regex-based heuristic — it identifies candidate
violators, not perfect oracles. Files flagged here should be cross-checked
against the existing QG baseline files in `scripts/quality_gates/*.yaml`.

Usage (from workspace root):

    python3 unified-trading-pm/plans/audit/results/a1_scan_codified_shape_compliance.py

Output:
    - plans/audit/results/codified_shape_compliance_2026_05_20.csv
    - plans/audit/results/codified_shape_compliance_2026_05_20_summary.md
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

# Service repos to scan (the in-scope codebase per the workspace map).
# Excludes config-only repos + UI-only repos that won't have the patterns.
REPOS_TO_SCAN: list[str] = [
    "agent-orchestrator",
    "alerting-service",
    "batch-live-reconciliation-service",
    "client-reporting-api",
    "deployment-api",
    "deployment-service",
    "e2e-testing",
    "execution-service",
    "features-service",
    "fund-administration-service",
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
    "system-integration-tests",
    "trading-agent-service",
    "unified-api-contracts",
    "unified-trading-api",
    "unified-trading-library",
]

# Directories to skip when walking a repo.
SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "build",
        "dist",
        "node_modules",
        "__pycache__",
        ".git",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        "site-packages",
    }
)


@dataclass(slots=True)
class FileScan:
    """Per-file scan result. Each `*_violations` field is a list of (lineno, snippet) tuples."""

    repo: str
    rel_path: str

    has_log_upload_trap_violations: list[tuple[int, str]] = field(default_factory=list)
    manifest_v8_violations: list[tuple[int, str]] = field(default_factory=list)
    record_emission_violations: list[tuple[int, str]] = field(default_factory=list)
    typed_empty_reason_violations: list[tuple[int, str]] = field(default_factory=list)
    classify_venue_error_violations: list[tuple[int, str]] = field(default_factory=list)
    resolve_bucket_name_violations: list[tuple[int, str]] = field(default_factory=list)
    lifecycle_class_violations: list[tuple[int, str]] = field(default_factory=list)
    no_hardcoded_venue_urls_violations: list[tuple[int, str]] = field(default_factory=list)
    no_hardcoded_venue_universe_violations: list[tuple[int, str]] = field(default_factory=list)
    uac_import_surface_violations: list[tuple[int, str]] = field(default_factory=list)

    file_kind: str = "other"  # "launcher" | "manifest_writer" | "handler" | "adapter" | "gcs_user" | "other"

    @property
    def total_violations(self) -> int:
        return sum(
            len(v)
            for v in (
                self.has_log_upload_trap_violations,
                self.manifest_v8_violations,
                self.record_emission_violations,
                self.typed_empty_reason_violations,
                self.classify_venue_error_violations,
                self.resolve_bucket_name_violations,
                self.lifecycle_class_violations,
                self.no_hardcoded_venue_urls_violations,
                self.no_hardcoded_venue_universe_violations,
                self.uac_import_surface_violations,
            )
        )


# ────────────────────────────────────────────────────────────────────────────
# Regex patterns — compiled once, reused per file.
# Each `_BAD` regex MATCHES a violation. Each `_OK` regex (where present) MATCHES
# the conformant shape; presence-of-OK suppresses the BAD finding for that file.
# ────────────────────────────────────────────────────────────────────────────

# Check 1: Launchers must invoke lc_log_upload_trap_block.
# Heuristic: file is a launcher iff its filename or path contains "launch" or
# "vm/" or "scripts/cron". Inside such a file, look for `gcloud compute instances create`
# OR a shell-style trap; if found, require `lc_log_upload_trap_block` somewhere.
LAUNCHER_INDICATOR = re.compile(r"gcloud\s+compute\s+instances\s+create|gcloud\s+compute\s+ssh\s")
LC_LOG_UPLOAD_TRAP = re.compile(r"lc_log_upload_trap_block")

# Check 2: Manifest writers must declare schema_version=8 (not 4).
MANIFEST_V_OLD = re.compile(r"schema_version\s*=\s*[1-7]\b|MANIFEST_SCHEMA_VERSION\s*=\s*[1-7]\b")
MANIFEST_WRITER_INDICATOR = re.compile(
    r"record_captured\s*\(|record_empty\s*\(|record_failed\s*\(|manifest_writer\.\w+|ManifestWriter\("
)

# Check 3: Handlers MUST emit at least one record_captured|record_empty|record_failed.
# Heuristic: a "handler" is a file matching `handlers?/.*\.py` OR containing `def fetch(` /
# `def collect(` / `def handle(` / `def process_shard(`. If so, require at least one
# `record_*` callsite. Missing = violation.
HANDLER_INDICATOR = re.compile(
    r"def\s+(fetch|collect|handle|process_shard|run_capture|capture_shard)\s*\(|class\s+\w*Handler\b"
)
RECORD_EMISSION = re.compile(r"record_captured\s*\(|record_empty\s*\(|record_failed\s*\(")

# Check 4: record_empty(reason=...) must use EmptyConfirmedReason enum, not raw strings.
# BAD = `reason="..."` (string literal). OK = `reason=EmptyConfirmedReason.X` or `reason=X` (variable).
RECORD_EMPTY_RAW_STR = re.compile(r"""record_empty\s*\([^)]*reason\s*=\s*["']""")

# Check 5: Adapters MUST classify errors via classify_venue_error + emit ADAPTER_FETCH_FAILED.
# Heuristic: a file is an "adapter" if path contains `adapters/` OR `_adapter.py`. Inside,
# look for `except` blocks; if found, require `classify_venue_error` somewhere in the file.
ADAPTER_INDICATOR = re.compile(r"(?:^|/)adapters?/|_adapter\.py$")
CLASSIFY_VENUE_ERROR = re.compile(r"classify_venue_error\s*\(")
ADAPTER_FETCH_FAILED = re.compile(r"ADAPTER_FETCH_FAILED")

# Check 6: GCS access must use resolve_bucket_name(...) — never inline gs:// f-string.
INLINE_GS_URI = re.compile(r"""f["'][^"']*gs://[^"']*\{|["']gs://[^"']+["']""")
RESOLVE_BUCKET = re.compile(r"resolve_bucket_name\s*\(")
GCS_USER_INDICATOR = re.compile(r"gs://|google\.cloud\.storage|gcs_|cloud_interface")

# Check 7: VM_PREFIX_TO_BUCKET entries must set lifecycle_class to a LifecycleClass enum value.
VM_PREFIX_SPEC_BAD = re.compile(r"VmPrefixSpec\([^)]*lifecycle_class\s*=\s*None")
VM_PREFIX_TO_BUCKET_INDICATOR = re.compile(r"VM_PREFIX_TO_BUCKET\s*=|VmPrefixSpec\(")

# Check 8: No hardcoded venue URLs (handled by existing QG; A1 finds candidates).
# BAD = top-level constants like `_DRIFT_S3_BASE = "https://..."` or `BINANCE_REST_BASE = "..."` in handlers.
HARDCODED_VENUE_URL = re.compile(
    r"""(?m)^(?!\s*#)\s*_?[A-Z][A-Z0-9_]*(?:_URL|_BASE|_ENDPOINT|_REST|_WS|_ROUTE)\s*[:=].*?["'](?:https?://|wss?://|s3://)""",
)
# Skip if file is in instruments-service (URLs canonical there) or in UAC (config-only).
HARDCODED_URL_REPO_ALLOWLIST = frozenset({"instruments-service", "unified-api-contracts", "deployment-service"})

# Check 9: No hardcoded venue universe constants in MTDS/features/strategy.
# BAD = top-level constants like `SOLANA_LST_TOKENS = [...]` or `DRIFT_MARKETS = [...]`.
HARDCODED_VENUE_UNIVERSE = re.compile(
    r"""(?m)^(?!\s*#)\s*_?[A-Z][A-Z0-9_]*(?:_TOKENS|_MARKETS|_SYMBOLS|_INSTRUMENTS|_PAIRS|_VENUES|_UNIVERSE)\s*[:=]\s*\[""",
)
HARDCODED_UNIVERSE_REPO_ALLOWLIST = frozenset(
    {
        "instruments-service",
        "unified-api-contracts",
        "deployment-service",
        "unified-trading-library",  # config-side
    }
)

# Check 10: UAC imports must go through public surface (`from unified_api_contracts import X`
# OR `from unified_api_contracts.{domain} import X`), never deep paths.
UAC_DEEP_IMPORT = re.compile(
    r"""(?m)^\s*from\s+unified_api_contracts\.(?:canonical|registry|internal|normalize_utils|external)\.[^\s]+\s+import""",
)
# Allowlist: UAC itself can use deep imports internally; tests in UAC also.
UAC_DEEP_REPO_ALLOWLIST = frozenset({"unified-api-contracts"})


def is_python_file(path: Path) -> bool:
    return path.suffix == ".py" and path.is_file()


def walk_repo(repo_root: Path) -> Iterable[Path]:
    """Walk a repo, skipping known-noise directories."""
    if not repo_root.exists():
        return
    for root, dirs, files in repo_root.walk():  # type: ignore[attr-defined]
        # Mutate dirs in-place to prune.
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for fname in files:
            if fname.endswith(".py"):
                yield root / fname


def classify_file(rel_path: str, content: str) -> str:
    """Quick classification for grading."""
    rel_lower = rel_path.lower()
    if (
        "launch" in rel_lower
        or "/vm/" in rel_lower
        or "scripts/cron" in rel_lower
        or LAUNCHER_INDICATOR.search(content)
    ):
        return "launcher"
    if (
        "handlers" in rel_lower
        or "/adapters/" in rel_lower
        or rel_lower.endswith("_adapter.py")
        or HANDLER_INDICATOR.search(content)
    ):
        return "handler"
    if MANIFEST_WRITER_INDICATOR.search(content):
        return "manifest_writer"
    if ADAPTER_INDICATOR.search(rel_path):
        return "adapter"
    if GCS_USER_INDICATOR.search(content):
        return "gcs_user"
    return "other"


def scan_file(repo: str, repo_root: Path, path: Path) -> FileScan:
    """Run all 10 checks against a single file."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FileScan(repo=repo, rel_path=str(path.relative_to(repo_root)))

    rel_path = str(path.relative_to(repo_root))
    scan = FileScan(repo=repo, rel_path=rel_path)
    scan.file_kind = classify_file(rel_path, content)
    lines = content.splitlines()

    def add(lst: list[tuple[int, str]], match: re.Match[str]) -> None:
        lineno = content[: match.start()].count("\n") + 1
        snippet = lines[lineno - 1].strip()[:200] if 0 < lineno <= len(lines) else match.group(0)[:200]
        lst.append((lineno, snippet))

    # Check 1: launcher → log-upload trap required.
    is_launcher = scan.file_kind == "launcher" or LAUNCHER_INDICATOR.search(content)
    if is_launcher and "lc_log_upload_trap_block" not in content:
        # We can't pinpoint a single line — file-level violation.
        scan.has_log_upload_trap_violations.append((0, "(file lacks lc_log_upload_trap_block)"))

    # Check 2: schema_version of 1-7 (should be 8).
    for m in MANIFEST_V_OLD.finditer(content):
        add(scan.manifest_v8_violations, m)

    # Check 3: handler → must emit at least one record_*.
    is_handler = HANDLER_INDICATOR.search(content) is not None or "handlers" in rel_path.lower()
    if is_handler and not RECORD_EMISSION.search(content):
        # File-level violation.
        scan.record_emission_violations.append((0, "(handler file lacks record_captured/empty/failed emission)"))

    # Check 4: record_empty(reason="literal") — should use enum.
    for m in RECORD_EMPTY_RAW_STR.finditer(content):
        add(scan.typed_empty_reason_violations, m)

    # Check 5: adapter → classify_venue_error + ADAPTER_FETCH_FAILED required.
    is_adapter = bool(ADAPTER_INDICATOR.search(rel_path))
    if is_adapter and "except" in content:
        if not CLASSIFY_VENUE_ERROR.search(content):
            scan.classify_venue_error_violations.append((0, "(adapter has except blocks but no classify_venue_error)"))
        if not ADAPTER_FETCH_FAILED.search(content):
            scan.classify_venue_error_violations.append(
                (0, "(adapter has except blocks but no ADAPTER_FETCH_FAILED emit)")
            )

    # Check 6: inline gs:// f-string when file is a GCS user.
    is_gcs_user = GCS_USER_INDICATOR.search(content) is not None
    if is_gcs_user:
        for m in INLINE_GS_URI.finditer(content):
            # Suppress for the canonical resolve_bucket_name impl itself + tests.
            if "resolve_bucket_name" in path.name or "/tests/" in rel_path:
                continue
            add(scan.resolve_bucket_name_violations, m)

    # Check 7: VmPrefixSpec(lifecycle_class=None).
    for m in VM_PREFIX_SPEC_BAD.finditer(content):
        add(scan.lifecycle_class_violations, m)

    # Check 8: hardcoded venue URL constants (allowlisted repos exempt).
    if repo not in HARDCODED_URL_REPO_ALLOWLIST and "/tests/" not in rel_path:
        for m in HARDCODED_VENUE_URL.finditer(content):
            add(scan.no_hardcoded_venue_urls_violations, m)

    # Check 9: hardcoded venue universe constants (allowlisted repos exempt).
    if repo not in HARDCODED_UNIVERSE_REPO_ALLOWLIST and "/tests/" not in rel_path:
        for m in HARDCODED_VENUE_UNIVERSE.finditer(content):
            add(scan.no_hardcoded_venue_universe_violations, m)

    # Check 10: UAC deep import surface.
    if repo not in UAC_DEEP_REPO_ALLOWLIST and "/tests/" not in rel_path:
        for m in UAC_DEEP_IMPORT.finditer(content):
            add(scan.uac_import_surface_violations, m)

    return scan


def write_csv(scans: list[FileScan], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "repo",
        "rel_path",
        "file_kind",
        "total_violations",
        "has_log_upload_trap",
        "manifest_v8",
        "record_emission",
        "typed_empty_reason",
        "classify_venue_error",
        "resolve_bucket_name",
        "lifecycle_class",
        "no_hardcoded_venue_urls",
        "no_hardcoded_venue_universe",
        "uac_import_surface",
    ]
    # Sort by total_violations desc, then repo, then rel_path.
    scans_sorted = sorted(scans, key=lambda s: (-s.total_violations, s.repo, s.rel_path))
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(fields)
        for s in scans_sorted:
            if s.total_violations == 0:
                continue  # CSV only carries violators (matches the prompt's "sort by violations desc" intent)
            writer.writerow(
                [
                    s.repo,
                    s.rel_path,
                    s.file_kind,
                    s.total_violations,
                    len(s.has_log_upload_trap_violations),
                    len(s.manifest_v8_violations),
                    len(s.record_emission_violations),
                    len(s.typed_empty_reason_violations),
                    len(s.classify_venue_error_violations),
                    len(s.resolve_bucket_name_violations),
                    len(s.lifecycle_class_violations),
                    len(s.no_hardcoded_venue_urls_violations),
                    len(s.no_hardcoded_venue_universe_violations),
                    len(s.uac_import_surface_violations),
                ]
            )


def write_summary(scans: list[FileScan], out_path: Path, total_files: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    per_repo: dict[str, int] = defaultdict(int)
    per_repo_files_scanned: dict[str, int] = defaultdict(int)
    per_repo_files_violating: dict[str, int] = defaultdict(int)
    per_check: dict[str, int] = defaultdict(int)
    check_columns = (
        ("has_log_upload_trap", "has_log_upload_trap_violations"),
        ("manifest_v8", "manifest_v8_violations"),
        ("record_emission", "record_emission_violations"),
        ("typed_empty_reason", "typed_empty_reason_violations"),
        ("classify_venue_error", "classify_venue_error_violations"),
        ("resolve_bucket_name", "resolve_bucket_name_violations"),
        ("lifecycle_class", "lifecycle_class_violations"),
        ("no_hardcoded_venue_urls", "no_hardcoded_venue_urls_violations"),
        ("no_hardcoded_venue_universe", "no_hardcoded_venue_universe_violations"),
        ("uac_import_surface", "uac_import_surface_violations"),
    )
    for s in scans:
        per_repo_files_scanned[s.repo] += 1
        if s.total_violations > 0:
            per_repo[s.repo] += s.total_violations
            per_repo_files_violating[s.repo] += 1
            for check_name, attr in check_columns:
                per_check[check_name] += len(getattr(s, attr))

    top_violators = sorted(
        (s for s in scans if s.total_violations > 0),
        key=lambda x: -x.total_violations,
    )[:25]

    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("# A1 — Codified-shape compliance summary\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"Files scanned: {total_files}\n\n")
        fh.write(f"Files with at least one violation: {sum(1 for s in scans if s.total_violations > 0)}\n\n")
        fh.write(f"Total violations: {sum(s.total_violations for s in scans)}\n\n")

        fh.write("## Per-check totals (Phase A1)\n\n")
        fh.write("| Check | Total violations | Existing QG ratchet | Status |\n")
        fh.write("|---|---:|---|---|\n")
        # Map each A1 check to its existing QG step (or "GAP — needs QG step").
        qg_map = {
            "has_log_upload_trap": ("(deployment-service@6b4610c trap-fix bundled across 14 launchers)", "SHIPPED"),
            "manifest_v8": ("base-library.sh STEP 5.x manifest-schema-version", "PARTIAL — verify version pin"),
            "record_emission": (
                "scripts/qg/no_silent_absence_handlers.sh"
                " + scripts/quality_gates/check_emission_policy_paired_callsites.py",
                "SHIPPED",
            ),
            "typed_empty_reason": (
                "(no current QG — relies on LegacyBlankErrorReasonError at runtime)",
                "GAP — needs QG step",
            ),
            "classify_venue_error": (
                "scripts/qg/no_adapter_contract_regression.sh"
                " + scripts/quality_gates/check_adapter_contract_regression.py",
                "SHIPPED",
            ),
            "resolve_bucket_name": (
                "scripts/quality_gates/check_inline_bucket_uri.py + inline_bucket_uri_baseline.yaml",
                "SHIPPED — ratcheting",
            ),
            "lifecycle_class": (
                "(declared in vm_zombie_watchdog.py VM_PREFIX_TO_BUCKET — CLAUDE.md hard rule)",
                "PARTIAL — needs CI check",
            ),
            "no_hardcoded_venue_urls": ("scripts/qg/no_hardcoded_venue_urls.sh", "SHIPPED"),
            "no_hardcoded_venue_universe": ("scripts/qg/no_hardcoded_venue_universe.sh", "SHIPPED"),
            "uac_import_surface": (
                "imports/uac-import-surface-enforcement.mdc + (no enforcement script)",
                "GAP — cursor rule only",
            ),
        }
        for check_name, _ in check_columns:
            qg_step, status = qg_map[check_name]
            fh.write(f"| `{check_name}` | {per_check.get(check_name, 0)} | {qg_step} | {status} |\n")

        fh.write("\n## Per-repo totals\n\n")
        fh.write("| Repo | Files scanned | Files violating | Total violations |\n")
        fh.write("|---|---:|---:|---:|\n")
        for repo in sorted(per_repo_files_scanned, key=lambda r: -per_repo.get(r, 0)):
            fh.write(
                f"| {repo} | {per_repo_files_scanned[repo]} | "
                f"{per_repo_files_violating.get(repo, 0)} | {per_repo.get(repo, 0)} |\n",
            )

        fh.write("\n## Top 25 violating files\n\n")
        fh.write("| Rank | Repo | File | Kind | Total |\n")
        fh.write("|---:|---|---|---|---:|\n")
        for i, s in enumerate(top_violators, 1):
            fh.write(f"| {i} | {s.repo} | `{s.rel_path}` | {s.file_kind} | {s.total_violations} |\n")

        fh.write("\n## Gap analysis — checks lacking workspace-wide QG enforcement\n\n")
        fh.write(
            "The mega-audit Phase A1 promised 10 checks; below are the ones"
            " where existing QG enforcement is partial or absent. "
            "These slot into the **Cross-cutting QG ratchet plan** referenced from the mega-audit tracker"
            " (no new SSOT — extend existing plan).\n\n"
        )
        fh.write("| Check | Gap | Proposed remediation |\n")
        fh.write("|---|---|---|\n")
        fh.write(
            "| `typed_empty_reason` | Runtime-only via `LegacyBlankErrorReasonError`; no static catch."
            " | Add `scripts/quality_gates/check_typed_empty_reason.py` that scans for"
            ' `record_empty(reason="...")` string literals and asserts `EmptyConfirmedReason.X` usage. |\n'
        )
        fh.write(
            "| `uac_import_surface` | Cursor rule only (`imports/uac-import-surface-enforcement.mdc`)"
            " — not enforced in CI."
            " | Promote to `scripts/quality_gates/check_uac_import_surface.py` + per-repo wiring. |\n"
        )
        fh.write(
            "| `lifecycle_class` | Mandatory per CLAUDE.md but no CI checker."
            " | Add `scripts/quality_gates/check_vm_lifecycle_class.py` that parses `vm_zombie_watchdog.py`"
            " + asserts every entry has a typed `LifecycleClass`. |\n"
        )
        fh.write(
            "| `manifest_v8` | base-library.sh STEP enforces but A1 surfaces drift candidates."
            " | Cross-check `MANIFEST_SCHEMA_VERSION` constants workspace-wide; raise to ERROR in QG. |\n"
        )


def main() -> int:
    scans: list[FileScan] = []
    total_files = 0
    for repo in REPOS_TO_SCAN:
        repo_root = WORKSPACE_ROOT / repo
        if not repo_root.exists():
            continue
        for path in walk_repo(repo_root):
            total_files += 1
            scans.append(scan_file(repo, repo_root, path))

    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"
    csv_path = out_dir / "codified_shape_compliance_2026_05_20.csv"
    summary_path = out_dir / "codified_shape_compliance_2026_05_20_summary.md"
    write_csv(scans, csv_path)
    write_summary(scans, summary_path, total_files)

    violators = sum(1 for s in scans if s.total_violations > 0)
    total = sum(s.total_violations for s in scans)
    print(f"A1 scan complete: {total_files} files scanned, {violators} violating, {total} total violations")
    print(f"  CSV:     {csv_path}")
    print(f"  Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
