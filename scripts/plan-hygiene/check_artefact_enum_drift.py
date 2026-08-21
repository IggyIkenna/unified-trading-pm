#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Enum-drift checker: validates artefact-quoted enum COUNTS against the real UAC enum
they claim to describe, across the client artefacts under
codex/14-customer-journeys/commercial-model/*.html.

Root cause (client_artefact_remediation_2026_08_18.md § E, operator ruling): enum
contents are hand-transcribed into client HTMLs, so one concern (does the artefact
still agree with the UAC source) lives in seven places. Proven to recur, not
hypothetical -- both tracked targets below are real, independently re-verified 2026-08-18
drifts:
  - strategy-service-walkthrough.html said "9 Instruction types" / "the nine action
    types"; unified-api-contracts' StrategyInstructionEnvelope has 11 subclasses.
  - the same artefact (and two siblings) listed 5 StrategyFamily members including an
    invented "Liquidity provision" entry; the real enum has 9 members, and
    /codex/04-architecture/strategy-execution-protocol.md had the correct count (11
    actions) the whole time -- the drift was in the artefact, not the SSOT.

Ground truth is parsed via AST (no import of unified_api_contracts -- this repo does not
depend on that package, and AST parsing is exactly as reliable for a StrEnum member list /
subclass count without needing it installed). A target's `kind` says what's counted:
  - "enum_members": number of StrEnum member assignments in a `class <name>(...)` body.
  - "subclass_count": number of top-level `class X(<name>):` definitions in the file.

For each artefact and each target, this scans for the target's anchor phrase, then looks
for a small integer immediately adjacent to a counting word ("types", "actions",
"families", "members") within a short window of the anchor. A stated count that doesn't
match the real count is a violation. This is deliberately a COUNT check, not a per-member
name check -- catches both proven precedents exactly (a stated total that disagrees with
the source), while avoiding the false-positive risk of fuzzy-matching prose family labels
("ML directional") against enum member spelling (`ML_DIRECTIONAL`). Per-member name
validation is a documented, not silently dropped, future extension -- add a target's
member-name list here once a normalisation rule is agreed, rather than guessing one now.

Shrinking ratchet, same shape as check_reference_paths.py: a live count above the
baseline fails (a NEW drift landed); lower the baseline as drifts get fixed.

Usage:
  python3 scripts/plan-hygiene/check_artefact_enum_drift.py [--quiet] [--update-baseline]
Exit 0 if violation count <= baseline. NEVER hand-raise the baseline.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PM_DIR.parent
ARTEFACT_DIR = PM_DIR / "codex" / "14-customer-journeys" / "commercial-model"
BASELINE_PATH = Path(__file__).resolve().parent / "artefact_enum_drift_baseline.yaml"

UAC_ARCH_V2 = WORKSPACE_ROOT / "unified-api-contracts" / "unified_api_contracts" / "internal" / "architecture_v2"

# Each target: ground truth enum/base class, where an artefact's claim about it is
# expected to be phrased, and which counting words to look for nearby.
TARGETS = [
    {
        "id": "strategy_family",
        "uac_file": UAC_ARCH_V2 / "enums.py",
        "class_name": "StrategyFamily",
        "kind": "enum_members",
        "anchor_re": re.compile(r"strategy famil(?:y|ies)", re.IGNORECASE),
        "count_words": ("famil",),
    },
    {
        "id": "strategy_instruction_envelope",
        "uac_file": UAC_ARCH_V2 / "schemas.py",
        "class_name": "StrategyInstructionEnvelope",
        "kind": "subclass_count",
        "anchor_re": re.compile(r"instruction type|action type|StrategyInstructionEnvelope", re.IGNORECASE),
        "count_words": ("type", "action"),
    },
]

# A count claim near an anchor: an integer immediately preceding a counting word,
# within ~60 characters of the anchor match.
WINDOW = 60
COUNT_NEAR_RE = re.compile(r"\b(\d{1,2})\b[^.\d]{0,20}?(famil|type|action|member|subclass)", re.IGNORECASE)


@dataclass(frozen=True)
class Baseline:
    violation_count: int = 0
    note: str = ""


def load_baseline() -> Baseline:
    if not BASELINE_PATH.exists():
        return Baseline()
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return Baseline(violation_count=int(raw.get("violation_count", 0)), note=str(raw.get("note") or ""))


def write_baseline(violation_count: int, existing: Baseline) -> None:
    new_count = min(violation_count, existing.violation_count) if existing.violation_count else violation_count
    BASELINE_PATH.write_text(
        "# Baseline for check_artefact_enum_drift.py -- stated enum counts in the six\n"
        "# client artefacts vs the real UAC enum/subclass count (operator ruling,\n"
        "# client_artefact_remediation_2026_08_18.md § E). Shrinking ratchet: a live count\n"
        "# ABOVE this fails (a NEW drift landed); lower it (--update-baseline) once drifts\n"
        "# are fixed. NEVER hand-raise.\n"
        "#\n"
        "# SSOT for the ground-truth enums: unified-api-contracts/unified_api_contracts/\n"
        "# internal/architecture_v2/{enums,schemas}.py.\n"
        f"note: Seeded 2026-08-18 alongside the checker.\n"
        f"violation_count: {new_count}\n",
        encoding="utf-8",
    )


def target_files() -> list[Path]:
    if not ARTEFACT_DIR.exists():
        return []
    return sorted(ARTEFACT_DIR.glob("*.html"))


def _real_count(target: dict) -> int | None:
    """Ground-truth count via AST. None if the source file/class can't be found --
    treated as unmeasurable (skip, never fabricate a count), never as zero."""
    uac_file = target["uac_file"]
    if not uac_file.is_file():
        return None
    try:
        tree = ast.parse(uac_file.read_text(encoding="utf-8"), filename=str(uac_file))
    except SyntaxError:
        return None

    if target["kind"] == "enum_members":
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == target["class_name"]:
                return sum(
                    1
                    for stmt in node.body
                    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)
                )
        return None

    if target["kind"] == "subclass_count":
        count = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = [b.id for b in node.bases if isinstance(b, ast.Name)]
            if target["class_name"] in base_names:
                count += 1
        return count

    return None


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


OTHER_PREFIX_RE = re.compile(r"\bother\b\s*$", re.IGNORECASE)
SUBSET_STATUS_RE = re.compile(
    r"\b(?:still\s+)?(?:coming\s+soon|not\s+(?:yet\s+)?wired|unsupported)\b",
    re.IGNORECASE,
)


def _claims_near_anchor(text: str, target: dict) -> list[tuple[int, int]]:
    """[(position, stated_count), ...] for every count claim found within WINDOW chars
    of an anchor match for this target.

    Skips a "the other N <word>" phrasing ("the other 10 action types return HTTP
    501") -- that states total-minus-something, not the enum's total count, and is a
    real, correct sentence shape in these artefacts (TRADE is live; "the other 10"
    correctly means 11 total minus the 1 already named). Only a bare "N <word>" is
    treated as a total-count claim.
    """
    claims: list[tuple[int, int]] = []
    for anchor in target["anchor_re"].finditer(text):
        lo = max(0, anchor.start() - WINDOW)
        hi = min(len(text), anchor.end() + WINDOW)
        window_text = text[lo:hi]
        for m in COUNT_NEAR_RE.finditer(window_text):
            word = m.group(2).lower()
            if not any(word.startswith(cw) for cw in target["count_words"]):
                continue
            if OTHER_PREFIX_RE.search(window_text[: m.start(1)]):
                continue
            if SUBSET_STATUS_RE.search(window_text[m.end(2) :]):
                continue
            claims.append((lo + m.start(), int(m.group(1))))
    return claims


def scan_file(p: Path, real_counts: dict[str, int | None]) -> list[str]:
    text = p.read_text(encoding="utf-8")
    rel = p.relative_to(PM_DIR).as_posix()
    violations: list[str] = []

    for target in TARGETS:
        real = real_counts.get(target["id"])
        if real is None:
            continue  # unmeasurable ground truth -- never guess, never flag
        for pos, stated in _claims_near_anchor(text, target):
            if stated != real:
                violations.append(
                    f"{rel}:{_line_of(text, pos)}: states {stated} for {target['class_name']} "
                    f"({target['id']}), real count is {real}"
                )

    return violations


def main() -> int:
    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv

    real_counts = {t["id"]: _real_count(t) for t in TARGETS}
    files = target_files()

    violations: list[str] = []
    for p in files:
        violations.extend(scan_file(p, real_counts))

    baseline = load_baseline()

    if not quiet:
        print(f"Artefact enum-drift check ({len(files)} file(s), {len(TARGETS)} tracked enum(s)):")
        for t in TARGETS:
            rc = real_counts.get(t["id"])
            print(f"  {t['id']}: real count = {rc if rc is not None else 'UNMEASURABLE (source not found)'}")
        print()
        for v in violations:
            print(f"  DRIFT  {v}")
        print()

    n = len(violations)
    ok = n <= baseline.violation_count

    print(f"{'✅' if ok else '❌'} check_artefact_enum_drift: {n} violation(s) (baseline {baseline.violation_count})")

    if update:
        write_baseline(n, baseline)
        print(f"Baseline updated: violation_count={min(n, baseline.violation_count or n)}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
