#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Group C architectural ratchets (ST-19 + PB-19 + UI-18).

Generic ratchet helper that walks per-rule target globs + flags banned
substrings / regex patterns. Each rule is declared in
`architectural_ratchets.yaml`:

    ratchets:
      - name: ST-19-no-standalone-backtest
        target_glob: "strategy-service/strategy_service/engine/backtest/**/*.py"
        banned_unless_contains: V2EngineOrchestrator
        condition_pattern: 'class\\s+\\w*[Bb]acktest\\w*'
        ...

Three semantics supported:
  - `banned_substring`: ALL matches flagged
  - `banned_unless_contains`: matches flagged ONLY if file lacks the required substring
  - `banned_pattern` (regex): matches flagged

SSOT: CLAUDE.md § "Findings Triage Discipline (HARD RULE)" + per-rule codex anchors.
Origin: governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group C.

Exit-code semantics: 0 = at/below baseline; 1 = regression; 2 = arg/IO/yaml error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

DEFAULT_BASELINE_PATH = Path(__file__).parent / "architectural_ratchets_baseline.yaml"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "architectural_ratchets.yaml"


@dataclass(frozen=True)
class RatchetViolation:
    rule_name: str
    path: Path
    detail: str


@dataclass(frozen=True)
class Ratchet:
    name: str
    target_glob: str
    owner: str
    rule_doc: str
    banned_substring: str | None = None
    banned_unless_contains: str | None = None
    banned_pattern: str | None = None
    condition_pattern: str | None = None  # only check files containing this


def _load_config(path: Path) -> list[Ratchet]:
    raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")))
    if not isinstance(raw, dict):
        raise ValueError("config root must be a dict")
    ratchets_raw = cast(dict[str, object], raw).get("ratchets")
    if not isinstance(ratchets_raw, list):
        raise ValueError("config.ratchets must be a list")
    out: list[Ratchet] = []
    for r in cast(list[object], ratchets_raw):
        if not isinstance(r, dict):
            continue
        rd = cast(dict[str, object], r)
        out.append(
            Ratchet(
                name=str(rd.get("name", "")),
                target_glob=str(rd.get("target_glob", "")),
                owner=str(rd.get("owner", "")),
                rule_doc=str(rd.get("rule_doc", "")),
                banned_substring=cast(str | None, rd.get("banned_substring")),
                banned_unless_contains=cast(str | None, rd.get("banned_unless_contains")),
                banned_pattern=cast(str | None, rd.get("banned_pattern")),
                condition_pattern=cast(str | None, rd.get("condition_pattern")),
            )
        )
    return out


def _iter_target_files(workspace_root: Path, glob_pattern: str) -> list[Path]:
    """Resolve glob relative to workspace_root."""
    matches: list[Path] = []
    for p in workspace_root.glob(glob_pattern):
        if p.is_file():
            matches.append(p)
    return sorted(matches)


def _check_file(file_path: Path, ratchet: Ratchet) -> RatchetViolation | None:
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    # Apply condition_pattern: only check files that contain the condition
    if ratchet.condition_pattern is not None and not re.search(ratchet.condition_pattern, text):
        return None

    if ratchet.banned_substring is not None and ratchet.banned_substring in text:
        return RatchetViolation(
            rule_name=ratchet.name,
            path=file_path,
            detail=f"contains banned substring: {ratchet.banned_substring!r}",
        )

    if ratchet.banned_pattern is not None:
        m = re.search(ratchet.banned_pattern, text)
        if m:
            return RatchetViolation(
                rule_name=ratchet.name,
                path=file_path,
                detail=f"matches banned pattern: {m.group(0)[:80]}",
            )

    if ratchet.banned_unless_contains is not None and ratchet.banned_unless_contains not in text:
        return RatchetViolation(
            rule_name=ratchet.name,
            path=file_path,
            detail=f"matches condition but lacks required substring {ratchet.banned_unless_contains!r}",
        )

    return None


def _load_baseline(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get("violation_count")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, violations: list[RatchetViolation]) -> None:
    payload: dict[str, object] = {
        "violation_count": len(violations),
        "rule": "architectural-ratchets",
        "source": "governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group C",
        "baseline_files": [{"rule": v.rule_name, "path": str(v.path), "detail": v.detail} for v in violations],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Architectural ratchet check.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2].parent)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    config_path: Path = cast(Path, ns.config)
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)

    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        ratchets = _load_config(config_path)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: config parse failed: {exc}", file=sys.stderr)
        return 2

    all_violations: list[RatchetViolation] = []
    files_scanned = 0
    for ratchet in ratchets:
        files = _iter_target_files(workspace_root, ratchet.target_glob)
        files_scanned += len(files)
        for f in files:
            v = _check_file(f, ratchet)
            if v is not None:
                all_violations.append(v)

    print(f"Ran {len(ratchets)} ratchet(s) across {files_scanned} target file(s); {len(all_violations)} violation(s).")

    if baseline_write:
        _write_baseline(baseline_path, all_violations)
        print(f"✅ Wrote baseline ({len(all_violations)} violations) to {baseline_path}")
        return 0

    if all_violations:
        print("\nViolations:")
        for v in all_violations[:20]:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - [{v.rule_name}] {rel}: {v.detail}")
        if len(all_violations) > 20:
            print(f"  ... + {len(all_violations) - 20} more")

    if strict:
        if all_violations:
            print(f"\n❌ STRICT mode: {len(all_violations)} violation(s).")
            return 1
        return 0

    baseline = _load_baseline(baseline_path)
    if len(all_violations) > baseline:
        print(f"\n❌ Regression: {len(all_violations)} > baseline {baseline}.")
        return 1
    if len(all_violations) < baseline:
        print(f"\n⚠️  Improvement: {len(all_violations)} < baseline {baseline}. Re-baseline to codify.")
        return 0
    print(f"\n✅ At baseline ({baseline}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
