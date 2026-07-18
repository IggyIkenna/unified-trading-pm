#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Evidence-backed-completion gate — a checked-off runtime claim must cite a VERIFIED build.

The recurring failure class this closes: an agent flips a plan todo to `- [x]` claiming a
Cloud Build / deploy / promote went "green" from its own self-report, when the OVERALL build
was actually FAILURE. Every such over-claim in the CI/CD effort was caught ONLY by an
independent Cloud Build API check. This gate makes that check structural, so over-claims
cannot survive a quality-gate regardless of which model wrote the todo.

The `Evidence:` convention (SSOT: plans/PLAN_FORMAT.md § Evidence-backed completion):
  Any `- [x]` todo whose completion is a RUNTIME claim (a Cloud Build / deploy / promote went
  green) MUST cite structured evidence on the checkbox line or its continuation lines:
      Evidence: cloudbuild=<build-id>[,<build-id> ...]
  Multiple build-ids and additional token kinds (e.g. `gha=<run-url>`) are allowed; this gate
  VERIFIES every `cloudbuild=<id>` resolves SUCCESS in the Cloud Build API.

Two sub-rules:
  - **A (strict, baseline 0): cited build must be SUCCESS.** Every `cloudbuild=<id>` in a `- [x]`
    todo is resolved via `gcloud builds describe`. A build whose OVERALL status is a terminal
    NON-success (FAILURE / TIMEOUT / CANCELLED / INTERNAL_ERROR / EXPIRED) is a HARD violation —
    this is the over-claim catch and must always be zero. A build that cannot be resolved
    (no gcloud / no auth / NOT_FOUND / still WORKING|QUEUED) is "unverifiable" → not a violation
    here (we never fail on an inability to PROVE non-success); pass --require-verification to
    treat unverifiable cited builds as violations (used by the review agent, which has auth).
  - **B (ratchet, baselined): runtime-green claim without any Evidence ref.** A `- [x]` todo that
    makes a build/deploy/promote-green claim but cites NO `Evidence:` ref is flagged. Baselined
    so legacy plans ratchet down; new over-claims without evidence push the count up → regression.

Exit-code semantics: 0 = clean (sub-rule A) and at/below baseline (sub-rule B); 1 = violation;
2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # invokes the gcloud CLI for the Cloud Build API (fixed argv, no shell=True)
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import yaml

DEFAULT_BASELINE_PATH = Path(__file__).parent / "evidence_backed_completion_baseline.yaml"
DEFAULT_REGION = "asia-northeast1"
DEFAULT_PROJECT = "central-element-323112"

# A checked-off todo line: `- [x] ...` (case-insensitive x).
_CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s")
# Any checkbox-shaped line ends the previous block's continuation — not just `[ ]`/`[x]`/`[X]`.
# Some active plans use an informal `[~]` (in-progress) marker; treating only the canonical
# states as boundaries let a `[~]` line be swallowed as "continuation text" of the PRIOR `- [x]`
# block, merging an unrelated next-todo's language (e.g. "redeploy"/"green") into it and
# producing false sub-rule-B violations (found 2026-07-18, bucket_fold_features_2026_07_17.md:95).
_UNCHECKED_OR_CHECKED_RE = re.compile(r"^\s*-\s*\[.\]\s")

# A structured Evidence ref carrying one or more cloudbuild ids.
_EVIDENCE_LINE_RE = re.compile(r"Evidence:\s*(?P<body>.+)", re.IGNORECASE)
_CLOUDBUILD_TOKEN_RE = re.compile(r"cloudbuild=\s*([0-9a-fA-F][0-9a-fA-F-]{7,39})")

# A runtime INFRA build/deploy/promote "went green" claim (sub-rule B trigger). Scoped tightly to
# the over-claim class this gate exists for — a Cloud Build / image build / cloud deploy / LDR→main
# promote asserted GREEN — and deliberately NOT to code-ship claims (a `<repo>@<sha>` commit + "QG
# green"/"tests passing"), which are evidenced by the commit + local QG sentinel, not a build-id.
# Requires BOTH an infra-runtime verb AND a green/success token in the same `- [x]` block.
_RUNTIME_VERB_RE = re.compile(
    r"\b(cloud[\s-]?build|cloudbuild|build[\s-]?id|build-wheel|image[\s-]?build|docker\s+build|"
    r"redeploy(?:ed)?|deployed\s+to|cloud\s+run\s+deploy|promote(?:d)?\s+to\s+main|"
    r"ldr[\s/→-]+main\s+promot|promotion[\s-]?(?:lag|pr|gate))\b",
    re.IGNORECASE,
)
_GREEN_TOKEN_RE = re.compile(r"\b(green|SUCCESS|succeeded)\b", re.IGNORECASE)

# Terminal Cloud Build statuses that are NOT success → an over-claim if cited on a `- [x]` todo.
_TERMINAL_NONSUCCESS = {"FAILURE", "TIMEOUT", "CANCELLED", "INTERNAL_ERROR", "EXPIRED"}


@dataclass
class TodoBlock:
    path: Path
    line_no: int
    text: str  # the checkbox line + its continuation lines, joined
    cloudbuild_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceViolation:
    rule: str  # "A-cited-build-not-success" | "A-unverifiable" | "B-claim-without-evidence"
    path: Path
    line_no: int
    detail: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.path}:{self.line_no}: {self.detail}"


def _iter_todo_blocks(text: str, path: Path) -> list[TodoBlock]:
    """Split a plan body into todo blocks: each `- [x]`/`- [ ]` line plus its continuation lines
    (more-indented or non-list-item lines) up to the next list item or blank line."""
    blocks: list[TodoBlock] = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if _CHECKED_RE.match(line):
            buf = [line]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if _UNCHECKED_OR_CHECKED_RE.match(nxt):
                    break
                if not nxt.strip():
                    break
                buf.append(nxt)
                j += 1
            block = TodoBlock(path=path, line_no=i + 1, text="\n".join(buf))
            # Scan the WHOLE block for cloudbuild=<id> citations — an `Evidence:` block routinely wraps
            # many ids across continuation lines, so a single-line scan would miss all but the first.
            for cb in _CLOUDBUILD_TOKEN_RE.finditer(block.text):
                block.cloudbuild_ids.append(cb.group(1))
            blocks.append(block)
            i = j
        else:
            i += 1
    return blocks


def _describe_build_status(build_id: str, region: str, project: str) -> str | None:
    """Return the OVERALL Cloud Build status string, or None if unresolvable (no gcloud / no auth /
    NOT_FOUND / network). Never raises."""
    try:
        proc = subprocess.run(  # fixed argv, no shell=True
            [
                "gcloud",
                "builds",
                "describe",
                build_id,
                f"--region={region}",
                f"--project={project}",
                "--format=value(status)",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    status = proc.stdout.strip()
    return status or None


def _check_builds(
    blocks: list[TodoBlock],
    region: str,
    project: str,
    require_verification: bool,
) -> list[EvidenceViolation]:
    """Sub-rule A: every cited cloudbuild id must resolve SUCCESS."""
    out: list[EvidenceViolation] = []
    cache: dict[str, str | None] = {}
    for b in blocks:
        for bid in b.cloudbuild_ids:
            if bid not in cache:
                cache[bid] = _describe_build_status(bid, region, project)
            status = cache[bid]
            if status is None:
                if require_verification:
                    out.append(
                        EvidenceViolation(
                            rule="A-unverifiable",
                            path=b.path,
                            line_no=b.line_no,
                            detail=f"cited cloudbuild={bid} could not be resolved (no gcloud/auth or NOT_FOUND)",
                        )
                    )
                continue
            if status == "SUCCESS":
                continue
            if status in _TERMINAL_NONSUCCESS:
                out.append(
                    EvidenceViolation(
                        rule="A-cited-build-not-success",
                        path=b.path,
                        line_no=b.line_no,
                        detail=f"OVER-CLAIM: cited cloudbuild={bid} is {status}, not SUCCESS",
                    )
                )
            elif require_verification:
                # WORKING / QUEUED / unknown — not terminal; only a violation under strict verify.
                out.append(
                    EvidenceViolation(
                        rule="A-unverifiable",
                        path=b.path,
                        line_no=b.line_no,
                        detail=f"cited cloudbuild={bid} is {status} (not yet terminal-SUCCESS)",
                    )
                )
    return out


def _check_claims_without_evidence(blocks: list[TodoBlock]) -> list[EvidenceViolation]:
    """Sub-rule B: a `- [x]` runtime-green claim with no Evidence/cloudbuild ref."""
    out: list[EvidenceViolation] = []
    for b in blocks:
        if b.cloudbuild_ids:
            continue
        has_evidence = bool(_EVIDENCE_LINE_RE.search(b.text))
        if has_evidence:
            continue
        if _RUNTIME_VERB_RE.search(b.text) and _GREEN_TOKEN_RE.search(b.text):
            first = b.text.splitlines()[0].strip()
            out.append(
                EvidenceViolation(
                    rule="B-claim-without-evidence",
                    path=b.path,
                    line_no=b.line_no,
                    detail=f"runtime-green claim without `Evidence: cloudbuild=<id>`: {first[:120]}",
                )
            )
    return out


def _load_baseline(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get("claim_without_evidence_baseline")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, rule_b: list[EvidenceViolation]) -> None:
    payload: dict[str, object] = {
        "claim_without_evidence_baseline": len(rule_b),
        "rule": "evidence-backed-completion (sub-rule B only; sub-rule A is strict-0)",
        "source": "plans/PLAN_FORMAT.md § Evidence-backed completion",
        "baseline_files": [{"path": str(v.path), "line": v.line_no} for v in rule_b],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evidence-backed-completion check (cited builds must be SUCCESS).")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
    )
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--include-issues", action="store_true", help="also scan plans/active/issues/*.md")
    parser.add_argument(
        "--require-verification",
        action="store_true",
        help="treat an UNVERIFIABLE cited build (no auth / NOT_FOUND / non-terminal) as a violation",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    region: str = cast(str, ns.region)
    project: str = cast(str, ns.project)
    include_issues: bool = cast(bool, ns.include_issues)
    require_verification: bool = cast(bool, ns.require_verification)

    active_dir = workspace_root / "unified-trading-pm" / "plans" / "active"
    if not active_dir.is_dir():
        print(f"ERROR: plans/active not found at {active_dir}", file=sys.stderr)
        return 2

    plan_files = sorted(active_dir.glob("*.md"))
    if include_issues:
        issues_dir = active_dir / "issues"
        if issues_dir.is_dir():
            plan_files.extend(sorted(issues_dir.glob("*.md")))

    blocks: list[TodoBlock] = []
    for p in plan_files:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        blocks.extend(_iter_todo_blocks(text, p))

    cited = sum(len(b.cloudbuild_ids) for b in blocks)
    rule_a = _check_builds(blocks, region, project, require_verification)
    rule_b = _check_claims_without_evidence(blocks)

    print(
        f"Scanned {len(plan_files)} plan(s), {len(blocks)} checked todo(s), "
        f"{cited} cited cloudbuild id(s) — sub-rule A: {len(rule_a)} violation(s); "
        f"sub-rule B: {len(rule_b)} claim(s)-without-evidence."
    )

    if baseline_write:
        _write_baseline(baseline_path, rule_b)
        print(f"✅ Wrote baseline (sub-rule B = {len(rule_b)}) to {baseline_path}")
        return 0

    # Sub-rule A: strict-0 — any cited build that is terminal-non-SUCCESS (or unverifiable under
    # --require-verification) fails the gate.
    if rule_a:
        print("\n❌ Sub-rule A — cited builds not verified SUCCESS (OVER-CLAIM):")
        for v in rule_a:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - [{v.rule}] {rel}:{v.line_no}: {v.detail}")

    # Sub-rule B: ratchet against baseline.
    baseline = _load_baseline(baseline_path)
    rule_b_regression = len(rule_b) > baseline
    if rule_b:
        print(f"\nSub-rule B — runtime-green claims without Evidence: {len(rule_b)} (baseline {baseline}).")
        for v in rule_b[:20]:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - {rel}:{v.line_no}: {v.detail}")
        if len(rule_b) > 20:
            print(f"  ... + {len(rule_b) - 20} more")

    failed = bool(rule_a) or rule_b_regression
    if rule_b_regression:
        print(
            f"\n❌ Sub-rule B regression: {len(rule_b)} > baseline {baseline}. "
            f"Add `Evidence: cloudbuild=<id>` to the new claim, or re-baseline with --baseline-write."
        )
    if not failed:
        if len(rule_b) < baseline:
            print(f"\n⚠️  Sub-rule B improvement: {len(rule_b)} < baseline {baseline}. Re-baseline to codify.")
        print("\n✅ Evidence-backed-completion: no over-claims; sub-rule B at/below baseline.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
