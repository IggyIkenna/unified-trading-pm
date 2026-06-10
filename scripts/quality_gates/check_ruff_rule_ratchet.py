#!/usr/bin/env python3
"""QG STEP 5.95 — ruff DTZ (UTC-datetime ban) + TID251 (cloud-SDK ban) count ratchet.

Hardens two grep-able CLAUDE.md rules into CI
(``plans/active/harden_grepable_rules_into_ci_gates_2026_06_02.md`` Phase 3,
ratchet-baseline mode per the recorded Phase-2 decision):

1. **DTZ — UTC datetimes always** (`datetime.now(timezone.utc)`; never the
   naive now/utcnow/today calls or zone-less `strptime` — the exact-call
   greps live in the QG codex slice, not here).
   Pinned code set: DTZ001-007, DTZ011, DTZ012, DTZ901.
2. **TID251 — no direct cloud SDK** (direct `google.cloud` / `boto3` imports
   banned; use `get_storage_client()` / `get_secret_client()`
   from `unified_trading_library.cloud_interface`). The UTL `cloud_interface/`
   wrapper internals are the sanctioned exemption (excluded by path — there is
   no separate unified-cloud-interface repo; the wrapper lives inside UTL).

Why a COUNT ratchet and not plain `ruff check`: the 2026-06-10 audit measured
121 DTZ + 264 real TID251 pre-existing sites fleet-wide — a hard gate would
redden every green repo (forbidden). So the canonical `[tool.ruff]` template
(`scripts/pyproject-templates/canonical-tool-sections.toml`) carries the rules
as the config SSOT, while THIS check enforces them fleet-wide today as a
per-repo shrinking baseline (`ruff_rule_ratchet_baseline.yaml`): a NEW
violation fails the PR; the grandfathered set only shrinks.

Mechanics: runs ``ruff check --isolated`` with an explicit ``--select`` per
rule group (so it works uniformly regardless of each repo's own pyproject
state) and, for TID251, a SINGLE combined ``--config`` banned-api override
(NOTE: ruff replaces — does not merge — the banned-api table across multiple
``--config`` flags, so the two bans MUST ride one flag). tests/ excluded
(matches the Phase-1 audit scope).

Per-line opt-out: standard ruff ``# noqa: DTZ005`` / ``# noqa: TID251`` with a
one-line reason.

Usage::

    # per-repo (run by base-service.sh / base-library.sh STEP 5.95):
    python check_ruff_rule_ratchet.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_ruff_rule_ratchet.py --workspace-root <ws>

    # ratchet the baseline DOWN after fixing violations:
    python check_ruff_rule_ratchet.py --workspace-root <ws> --update-baseline

Exit codes: 0 = at-or-below baseline; 1 = over baseline; 2 = arg/IO/ruff error.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Rule groups ──────────────────────────────────────────────────────────────

#: Pinned DTZ code set (CLAUDE.md "UTC datetimes always"). Do NOT widen/narrow
#: ad hoc — mirrors the canonical-tool-sections.toml template select.
DTZ_CODES: Final[tuple[str, ...]] = (
    "DTZ001",
    "DTZ002",
    "DTZ003",
    "DTZ004",
    "DTZ005",
    "DTZ006",
    "DTZ007",
    "DTZ011",
    "DTZ012",
    "DTZ901",
)

#: Single combined banned-api override — MUST be one --config flag (ruff
#: replaces, not merges, the table across multiple flags).
TID251_BANNED_API_CONFIG: Final[str] = (
    "lint.flake8-tidy-imports.banned-api = {"
    '"google.cloud" = {msg = "Direct cloud SDK banned - use get_storage_client()/get_secret_client() '
    "from unified_trading_library.cloud_interface (CLAUDE.md 'Cloud-agnostic I/O')\"}, "
    '"boto3" = {msg = "Direct cloud SDK banned - use get_storage_client()/get_secret_client() '
    "from unified_trading_library.cloud_interface (CLAUDE.md 'Cloud-agnostic I/O')\"}}"
)

#: Sanctioned cloud-wrapper internals — the ONLY path allowed to import the SDKs.
TID251_EXEMPT_PATH: Final[str] = "unified_trading_library/cloud_interface"

#: Dirs excluded from the scan (ruff's defaults already cover .git/.venv/venv/
#: build/dist/node_modules; these are workspace-specific additions).
EXTEND_EXCLUDES: Final[tuple[str, ...]] = (".venv-workspace", "tests", ".cursor")

#: Rule-group ids (baseline yaml keys).
RULE_GROUPS: Final[tuple[str, ...]] = ("dtz", "tid251")


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "ruff_rule_ratchet_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts per rule group: ``{repo: {dtz: N, tid251: N}}``."""

    counts: dict[str, dict[str, int]] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str, group: str) -> int:
        return int(self.counts.get(repo, {}).get(group, 0))


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, dict[str, int]] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = {g: int(val.get(g, 0)) for g in RULE_GROUPS}
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(observed: dict[str, dict[str, int]], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline, clamping counts DOWN — never raised."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(observed) | set(existing.counts)
    for repo in sorted(all_repos):
        row: dict[str, int] = {}
        for group in RULE_GROUPS:
            seen = int(observed.get(repo, {}).get(group, 0))
            prior = existing.allowed(repo, group)
            row[group] = min(seen, prior) if repo in existing.counts else seen
        merged[repo] = row
    header = (
        "# Baseline for QG STEP 5.95 — ruff DTZ (UTC-datetime) + TID251 (cloud-SDK) count ratchet.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].{dtz,tid251}` is the number of\n"
        "# ruff violations (tests/ excluded; UTL cloud_interface/ exempt for tid251)\n"
        "# the gate tolerates in that repo. A repo whose live count EXCEEDS its\n"
        "# baseline fails CI — a NEW naive-datetime / direct-SDK site landed; fix it\n"
        "# (`datetime.now(timezone.utc)` / `get_storage_client()`), or add a ruff\n"
        "# `# noqa: DTZ00x` / `# noqa: TID251` with a one-line reason.\n"
        "#\n"
        "# LOWER counts (re-run `--update-baseline`) as violations are fixed.\n"
        "# NEVER raise a count. Repos not listed default to 0.\n"
        "#\n"
        "# SSOT: CLAUDE.md 'UTC datetimes always' + 'Cloud-agnostic I/O' +\n"
        "# plans/active/harden_grepable_rules_into_ci_gates_2026_06_02.md. Config SSOT:\n"
        "# scripts/pyproject-templates/canonical-tool-sections.toml ([tool.ruff.lint]).\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-06-10 — harden_grepable_rules_into_ci_gates Phase 3 (QG STEP 5.95).",
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


# ── ruff invocation ──────────────────────────────────────────────────────────


def _ruff_cmd() -> list[str]:
    """Locate ruff: same-interpreter module first, PATH binary as fallback."""
    probe = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    binary = shutil.which("ruff")
    if binary:
        return [binary]
    raise FileNotFoundError("ruff not found (neither `python -m ruff` nor a PATH binary)")


def run_ruff_count(scan_root: Path, group: str) -> list[tuple[str, int, str]]:
    """Run ruff for one rule group; return [(file, line, code)] violations."""
    cmd = [*_ruff_cmd(), "check", "--isolated", "--exit-zero", "--output-format", "json", "--no-cache"]
    for pattern in EXTEND_EXCLUDES:
        cmd += ["--extend-exclude", pattern]
    if group == "dtz":
        for code in DTZ_CODES:
            cmd += ["--select", code]
    elif group == "tid251":
        cmd += ["--select", "TID251", "--config", TID251_BANNED_API_CONFIG]
        # Ruff anchors RELATIVE multi-segment exclude globs to the CWD (the
        # "project root"), NOT the scanned path — so pass ABSOLUTE paths
        # (verified ruff 0.15.0). Cover both shapes: scan_root == repo root
        # (…/unified_trading_library/cloud_interface) and scan_root == the
        # package dir itself (…/cloud_interface). Non-existent paths are inert.
        cmd += ["--extend-exclude", str(scan_root / TID251_EXEMPT_PATH)]
        cmd += ["--extend-exclude", str(scan_root / "cloud_interface")]
    else:  # pragma: no cover — closed set
        raise ValueError(f"unknown rule group: {group}")
    cmd.append(str(scan_root))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ruff failed for {scan_root} ({group}): {result.stderr.strip()[:500]}")
    rows = json.loads(result.stdout or "[]")
    out: list[tuple[str, int, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        filename = str(row.get("filename", "?"))
        location = row.get("location")
        line = int(location.get("row", 0)) if isinstance(location, dict) else 0
        out.append((filename, line, str(row.get("code", "?"))))
    return sorted(out)


# ── Scope resolution (mirrors check_no_fallback_imports.py) ──────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None, source_dir: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(f"[check_ruff_rule_ratchet] --scope {scope!r} not a dir under {workspace_root}", file=sys.stderr)
            return []
        scan_root = repo_root / source_dir if source_dir else repo_root
        if not scan_root.exists():
            scan_root = repo_root
        return [(scope, scan_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / ".git").exists():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ruff DTZ + TID251 per-repo count ratchet (QG STEP 5.95).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo QG mode).")
    parser.add_argument(
        "--source-dir", default=None, help="Sub-dir under --scope to narrow the scan to (e.g. the package dir)."
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        help="Override the baseline yaml path (unit tests only).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_file: Path | None = args.baseline_file
    baseline = load_baseline(baseline_file)
    scopes = _resolve_scopes(workspace_root, args.scope, args.source_dir)
    if not scopes:
        print("[check_ruff_rule_ratchet] no repos in scope.", file=sys.stderr)
        return 0

    observed: dict[str, dict[str, int]] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, scan_root in scopes:
        observed[repo_name] = {}
        for group in RULE_GROUPS:
            try:
                sites = run_ruff_count(scan_root, group)
            except (RuntimeError, FileNotFoundError, json.JSONDecodeError) as err:
                print(f"[check_ruff_rule_ratchet] ERROR {repo_name}/{group}: {err}", file=sys.stderr)
                return 2
            count = len(sites)
            observed[repo_name][group] = count
            allowed = baseline.allowed(repo_name, group)
            if count > allowed:
                over = sites[allowed:] if allowed < len(sites) else sites
                sites_str = "; ".join(f"{Path(f).name}:{ln} {code}" for f, ln, code in over[:15])
                failures.append(
                    f"[FAIL] {repo_name}/{group}: {count} violation(s) > baseline {allowed}. "
                    f"New/over-baseline site(s): {sites_str}" + (" ..." if len(over) > 15 else "")
                )
            elif count < allowed:
                info_lines.append(
                    f"[WARN] {repo_name}/{group}: {count} < baseline {allowed} — ratchet DOWN "
                    f"(re-run `--update-baseline`)."
                )
            else:
                info_lines.append(f"[OK]   {repo_name}/{group}: {count} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file)
        print(f"[check_ruff_rule_ratchet] baseline updated at {baseline_file or _baseline_path()}")
        for repo in sorted(observed):
            print(f"  {repo}: {observed[repo]}")
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ dtz: use `datetime.now(timezone.utc)` — never naive now()/utcnow()/today()/zone-less "
            "strptime (CLAUDE.md 'UTC datetimes always'). tid251: use get_storage_client()/"
            "get_secret_client() from unified_trading_library.cloud_interface — never google.cloud/boto3 "
            "directly (CLAUDE.md 'Cloud-agnostic I/O'). Per-line opt-out: ruff `# noqa: <code>` with a "
            "one-line reason. Baseline: unified-trading-pm/scripts/quality_gates/"
            "ruff_rule_ratchet_baseline.yaml (NEVER raise a count). SSOT: "
            "harden_grepable_rules_into_ci_gates_2026_06_02.md.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
