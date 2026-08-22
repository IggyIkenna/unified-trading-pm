#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Evidence-backed-completion gate — a checked-off runtime/data-mutation claim must cite
VERIFIED evidence.

The recurring failure class this closes: an agent flips a plan todo to `- [x]` claiming a
Cloud Build / deploy / promote went "green" from its own self-report, when the OVERALL build
was actually FAILURE. Every such over-claim in the CI/CD effort was caught ONLY by an
independent Cloud Build API check. This gate makes that check structural, so over-claims
cannot survive a quality-gate regardless of which model wrote the todo. Sub-rule C extends the
same discipline to prod DATA-mutation completions (restamp/backfill/purge row-counts, GCS
object rename/delete, tofu/terraform state ops) — see
plans/active/issues/prod_mutation_evidence_artifact_gap_2026_08_03.md for why: those claims had
no verifiable artifact analogous to a Cloud Build id, so completion rested on the worker's
self-report of running their own script.

The `Evidence:` convention (SSOT: plans/PLAN_FORMAT.md § Evidence-backed completion):
  Any `- [x]` todo whose completion is a RUNTIME claim (a Cloud Build / deploy / promote went
  green) MUST cite structured evidence on the checkbox line or its continuation lines:
      Evidence: cloudbuild=<build-id>[,<build-id> ...]
  Multiple build-ids and additional token kinds (e.g. `gha=<run-url>`) are allowed; this gate
  VERIFIES every `cloudbuild=<id>` resolves SUCCESS in the Cloud Build API.

  A `- [x]` todo whose completion is a prod DATA-MUTATION claim (a restamp/backfill/purge row
  or shard count, a GCS object rename/delete, a tofu/terraform state op) MUST similarly cite a
  verifiable artifact ref (plans/PLAN_FORMAT.md § 8d):
      Evidence: manifest-delta=<path> | vm-log=<path> | gcs-op=<id> | state-list=<before>,<after>

Three sub-rules:
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
  - **C (ratchet, baselined): prod data-mutation claim without a verifiable-artifact Evidence
    ref.** A `- [x]` todo that claims a restamp/backfill/purge row-count, a GCS object
    rename/delete, or a tofu/terraform state op but cites no `manifest-delta=`/`vm-log=`/
    `gcs-op=`/`state-list=` ref is flagged. Same ratchet discipline as sub-rule B: no live API
    call (there is no single "mutation API" to poll the way Cloud Build has one) — the artifact
    ref itself is the durable, independently-openable evidence a reviewer resolves by hand.

Exit-code semantics: 0 = clean (sub-rule A) and at/below baseline (sub-rules B, C); 1 = violation;
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


def _pm_root_or_legacy(workspace_root):
    """PM checkout root resolved by CONTENT, not by directory NAME (F7, 2026-08-10).

    See scripts/quality_gates/_pm_root.py for why. Behaviour-preserving in a canonically
    named checkout; fixes resolution when running from a git worktree."""
    import pathlib as _pathlib
    import sys as _sys

    _d = str(_pathlib.Path(__file__).resolve().parent)
    if _d not in _sys.path:
        _sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


DEFAULT_BASELINE_PATH = Path(__file__).parent / "evidence_backed_completion_baseline.yaml"
DEFAULT_REGION = "asia-northeast1"
DEFAULT_PROJECT = "central-element-323112"

# A checked-off todo line: `- [x] ...` (case-insensitive x).
_CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s")
_UNCHECKED_OR_CHECKED_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s")

# A structured Evidence ref carrying one or more cloudbuild ids.
_EVIDENCE_LINE_RE = re.compile(r"Evidence:\s*(?P<body>.+)", re.IGNORECASE)
_CLOUDBUILD_TOKEN_RE = re.compile(r"cloudbuild=\s*([0-9a-fA-F][0-9a-fA-F-]{7,39})")
# A REAL Cloud Build id is a UUID (36 chars, dashes at 8-4-4-4-12). An 8-char git short-hash
# also matches _CLOUDBUILD_TOKEN_RE's looser capture group, which is the actual defect this gate
# closes (cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md) — distinguishing
# the two matters because a well-formed UUID that fails to resolve is usually just a build whose
# record aged out of Cloud Build's retention window (not the citer's fault, shouldn't retroactively
# fail an already-shipped claim), whereas a malformed (non-UUID) citation could never have resolved
# and is a structurally bogus citation from the moment it was written.
_UUID_SHAPE_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

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
# Hyphen-guarded on both sides (not just `\b`, which treats `-` as a boundary) so a domain
# compound term like "success-reporting" (a named dispatch mechanism used throughout the
# ci_satellite_ao_dispatch_batchN_* corpus, never a claim that anything succeeded) doesn't match
# — confirmed false-positive, evidence_backed_completion_regression_24_vs_23_2026_08_09.md todo 1.
_GREEN_TOKEN_RE = re.compile(r"(?<!-)\b(?:green|SUCCESS|succeeded)\b(?!-)", re.IGNORECASE)

# Sub-rule C — prod DATA-mutation claims (restamp/backfill/purge row-counts, GCS object
# rename/delete, tofu/terraform state ops). Two shapes:
#   - COUNTED verbs (restamp/backfill/purge) only count as a completion claim alongside an
#     actual row/shard/object COUNT token in the same clause — a bare "we should backfill this
#     later" isn't a claim that anything ran.
#   - STANDALONE forms (renamed/deleted N GCS objects, tofu/terraform state rm) already embed
#     their own specificity (a count for rename/delete; the state-mutating verb itself for
#     tofu/terraform) and trigger on their own.
_MUTATION_COUNTED_VERB_RE = re.compile(r"\b(restamp(?:ed|ing)?|backfill(?:ed|ing)?|purg(?:ed|ing|e))\b", re.IGNORECASE)
_MUTATION_STANDALONE_RE = re.compile(
    r"\b(?:renam(?:ed?|ing)|delet(?:ed?|ing))\s+[\d][\d,]*\s+(?:gcs\s+)?objects?\b|"
    r"\b(?:tofu|terraform)\s+state\s+(?:rm|remove[ds]?|delete[ds]?)\b",
    re.IGNORECASE,
)
# Allows a few adjectives/qualifiers between the number and the unit noun (e.g. "124 lowercase
# duplicate rows"), not just a bare "12,006 rows" — real completion prose routinely qualifies
# the count.
_COUNT_TOKEN_RE = re.compile(
    r"\b[\d][\d,]*\b(?:\s+[\w-]+){0,3}\s+(?:rows?|shards?|objects?|cells?|records?)\b", re.IGNORECASE
)
_MUTATION_EVIDENCE_TOKEN_RE = re.compile(r"\b(?:manifest-delta|vm-log|gcs-op|state-list)=", re.IGNORECASE)

# Sentence/clause boundary for the same-clause proximity check below: a `.`/`!`/`?` followed by
# whitespace and then an uppercase letter or a backtick (prose/markdown convention — a new clause
# starts a fresh code-span or capitalized word). Deliberately does NOT split on a period with no
# following whitespace, so it never fires mid-filename/identifier (`cloud-build-router.yml`,
# `needs.route-build.outputs.repo`) — those periods are always followed immediately by another
# non-whitespace character, not a space.
_CLAUSE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`])")

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
    # "A-cited-build-not-success" | "A-unverifiable" | "B-claim-without-evidence" |
    # "C-mutation-claim-without-evidence"
    rule: str
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


def _describe_build_status(build_id: str, region: str, project: str) -> tuple[str | None, bool]:
    """Return (status_or_None, environment_available).

    environment_available=False means gcloud itself could not run at all (missing binary,
    timeout, OS error) — a genuine "cannot check from here" case, soft-skipped by default.
    environment_available=True with status=None means gcloud DID run and returned a non-zero
    result (e.g. NOT_FOUND) — the environment could check and the citation simply does not
    resolve to a real build. That is a structurally-unresolvable citation (a malformed id, e.g.
    an 8-char git short-hash instead of a Cloud Build UUID) and must always be a violation,
    independent of --require-verification, or the gate's whole "run it, don't read it" purpose
    is defeated whenever the checking environment happens to have gcloud/auth (see
    cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md — the original design
    conflated these two cases, so a bogus short-hash citation silently passed even when gcloud
    was available and confirmed it did not exist)."""
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
        return None, False
    if proc.returncode != 0:
        return None, True
    status = proc.stdout.strip()
    return (status or None), True


def _check_builds(
    blocks: list[TodoBlock],
    region: str,
    project: str,
    require_verification: bool,
) -> list[EvidenceViolation]:
    """Sub-rule A: every cited cloudbuild id must resolve SUCCESS."""
    out: list[EvidenceViolation] = []
    cache: dict[str, tuple[str | None, bool]] = {}
    for b in blocks:
        for bid in b.cloudbuild_ids:
            if bid not in cache:
                cache[bid] = _describe_build_status(bid, region, project)
            status, environment_available = cache[bid]
            if status is None:
                if not environment_available:
                    # gcloud itself couldn't run here (no binary/auth/network) — a genuine
                    # can't-check case, soft-skipped unless the caller opts into strict mode.
                    if require_verification:
                        out.append(
                            EvidenceViolation(
                                rule="A-unverifiable",
                                path=b.path,
                                line_no=b.line_no,
                                detail=f"cited cloudbuild={bid} could not be checked (no gcloud/auth/network here)",
                            )
                        )
                elif not _UUID_SHAPE_RE.match(bid):
                    # gcloud ran and this id doesn't resolve, AND it isn't even UUID-shaped — a
                    # structurally bogus citation (e.g. a git short-hash) that could never have
                    # been a real Cloud Build id. Always a violation, independent of
                    # --require-verification.
                    out.append(
                        EvidenceViolation(
                            rule="A-cited-build-not-found",
                            path=b.path,
                            line_no=b.line_no,
                            detail=f"cited cloudbuild={bid} is not a Cloud Build id (not UUID-shaped) "
                            "and does not resolve",
                        )
                    )
                elif require_verification:
                    # Well-formed UUID that doesn't resolve — most likely a genuine build whose
                    # Cloud Build record aged out of the API's retention window, not a bogus
                    # citation. Not the citer's fault and not a violation by default; only flagged
                    # under strict verify (same tier as the environment-unavailable case above).
                    out.append(
                        EvidenceViolation(
                            rule="A-unverifiable",
                            path=b.path,
                            line_no=b.line_no,
                            detail=f"cited cloudbuild={bid} is UUID-shaped but NOT_FOUND (likely aged out "
                            "of Cloud Build retention)",
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


def _split_into_clauses(text: str) -> list[str]:
    """Split a todo block into rough sentence/clause units. Collapses newlines/indentation to a
    single space first so a line-wrapped sentence isn't mistaken for two separate clauses, then
    splits on `_CLAUSE_BOUNDARY_RE`."""
    normalized = re.sub(r"\s+", " ", text).strip()
    return _CLAUSE_BOUNDARY_RE.split(normalized)


def _check_claims_without_evidence(blocks: list[TodoBlock]) -> list[EvidenceViolation]:
    """Sub-rule B: a `- [x]` runtime-green claim with no Evidence/cloudbuild ref.

    The runtime-verb and green-token must co-occur in the SAME clause, not just anywhere in a
    long multi-line block — a whole-block AND false-positives on prose that mentions an infra
    filename (e.g. `cloud-build-router.yml`, a GHA call-site) in one clause and an unrelated
    `quality-gates.sh` "green" mention in a later, unconnected clause of the same todo (see
    plans/active/issues/pm_evidence_backed_completion_false_positive_2026_07_21.md).
    """
    out: list[EvidenceViolation] = []
    for b in blocks:
        if b.cloudbuild_ids:
            continue
        has_evidence = bool(_EVIDENCE_LINE_RE.search(b.text))
        if has_evidence:
            continue
        for clause in _split_into_clauses(b.text):
            if _RUNTIME_VERB_RE.search(clause) and _GREEN_TOKEN_RE.search(clause):
                first = b.text.splitlines()[0].strip()
                out.append(
                    EvidenceViolation(
                        rule="B-claim-without-evidence",
                        path=b.path,
                        line_no=b.line_no,
                        detail=f"runtime-green claim without `Evidence: cloudbuild=<id>`: {first[:120]}",
                    )
                )
                break
    return out


def _check_mutation_claims_without_evidence(blocks: list[TodoBlock]) -> list[EvidenceViolation]:
    """Sub-rule C: a `- [x]` prod DATA-mutation claim (restamp/backfill/purge row-count, GCS
    object rename/delete, tofu/terraform state rm) with no verifiable-artifact Evidence ref.

    Same same-clause-proximity discipline as sub-rule B: a COUNTED verb only triggers alongside
    an actual row/shard/object count in the same clause, so a bare mention of "backfill" with no
    completed-count claim doesn't false-positive. STANDALONE forms already embed their own
    specificity in the regex and trigger on their own.
    """
    out: list[EvidenceViolation] = []
    for b in blocks:
        if _MUTATION_EVIDENCE_TOKEN_RE.search(b.text):
            continue
        for clause in _split_into_clauses(b.text):
            counted = bool(_MUTATION_COUNTED_VERB_RE.search(clause) and _COUNT_TOKEN_RE.search(clause))
            standalone = bool(_MUTATION_STANDALONE_RE.search(clause))
            if counted or standalone:
                first = b.text.splitlines()[0].strip()
                out.append(
                    EvidenceViolation(
                        rule="C-mutation-claim-without-evidence",
                        path=b.path,
                        line_no=b.line_no,
                        detail=f"prod data-mutation claim without a verifiable Evidence artifact ref "
                        f"(manifest-delta=/vm-log=/gcs-op=/state-list=): {first[:120]}",
                    )
                )
                break
    return out


def _rule_b_signatures_for_text(text: str, path: Path) -> set[str]:
    """Sub-rule B violation signatures for one file's TEXT — shared by the corpus-wide scan and
    ``--only`` mode's HEAD-vs-working-tree comparison so the two can never define "a claim
    without evidence" differently."""
    blocks = _iter_todo_blocks(text, path)
    return {v.detail for v in _check_claims_without_evidence(blocks)}


def _run_only(paths: list[str], quiet: bool) -> int:
    """Precommit-scoped mode (2026-08-09): checks ONLY the given staged files' sub-rule B —
    flags only a claim-without-evidence this commit INTRODUCES, never pre-existing debt in a
    plan the commit merely touches elsewhere. Same shape as check_effort_signal_ratchet.py
    --only: compare violation signatures at HEAD vs the current working-tree content, flag only
    what's new. Sub-rule A (Cloud Build API verification) is deliberately NOT run here — it
    needs `gcloud` + network + auth, incompatible with a <1s local precommit hook; it stays
    CI/full-sweep-only, same as it always has been. Sub-rule C (prod data-mutation claims) is
    likewise CI/full-sweep-only, same rationale as sub-rule A's exclusion doesn't apply here but
    keeping the precommit-scoped path narrow (sub-rule B only) matches how it was introduced and
    avoids widening this fast-path's surface without a live incident motivating it.

    Root-caused after this check's corpus-wide baseline (23->24) blocked an UNRELATED commit's
    quickmerge on `push to live-defi-rollout` (2026-08-09, sha 42c50b4b3) — a plan-doc `- [x]`
    claim added via safe-doc-push.sh (which never runs sub-rule B at all) sailed through clean
    and only surfaced on the next full CI run, misattributed to whichever unrelated commit
    happened to trigger it. Same fast-path-blind-to-full-gate pattern as the 6 checks migrated
    earlier tonight.
    """
    flagged: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_file() or p.suffix != ".md":
            continue
        try:
            current_text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        current_sigs = _rule_b_signatures_for_text(current_text, p)
        if not current_sigs:
            continue
        proc = subprocess.run(
            ["git", "show", f"HEAD:{_relpath_for_git(p)}"],
            capture_output=True,
            text=True,
            check=False,
        )
        head_sigs = _rule_b_signatures_for_text(proc.stdout, p) if proc.returncode == 0 else set()
        new_sigs = current_sigs - head_sigs
        for sig in sorted(new_sigs):
            flagged.append(f"{p.name}: {sig}")

    if not quiet:
        for line in flagged:
            print(f"  EVIDENCE-MISSING  {line}")
    n = len(flagged)
    print(f"{'✅' if n == 0 else '❌'} check_evidence_backed_completion (--only): {n} new violation(s) in staged files")
    return 0 if n == 0 else 1


def _relpath_for_git(p: Path) -> str:
    """Best-effort repo-relative path for a `git show HEAD:<path>` lookup — walks up to find the
    nearest ancestor directory containing `.git`, matching how the other --only checks in this
    corpus resolve staged paths without assuming a fixed cwd."""
    resolved = p.resolve()
    for parent in (resolved, *resolved.parents):
        if (parent / ".git").exists():
            return str(resolved.relative_to(parent))
    return p.name


def _load_baseline(baseline_path: Path, key: str = "claim_without_evidence_baseline") -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get(key)
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, rule_b: list[EvidenceViolation], rule_c: list[EvidenceViolation]) -> None:
    payload: dict[str, object] = {
        "claim_without_evidence_baseline": len(rule_b),
        "mutation_claim_without_evidence_baseline": len(rule_c),
        "rule": "evidence-backed-completion (sub-rules B, C; sub-rule A is strict-0)",
        "source": "plans/PLAN_FORMAT.md § Evidence-backed completion",
        "baseline_files": [{"path": str(v.path), "line": v.line_no} for v in rule_b],
        "mutation_baseline_files": [{"path": str(v.path), "line": v.line_no} for v in rule_c],
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
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        return _run_only(sys.argv[idx + 1 :], "--quiet" in sys.argv)
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    region: str = cast(str, ns.region)
    project: str = cast(str, ns.project)
    include_issues: bool = cast(bool, ns.include_issues)
    require_verification: bool = cast(bool, ns.require_verification)

    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
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
    rule_c = _check_mutation_claims_without_evidence(blocks)

    print(
        f"Scanned {len(plan_files)} plan(s), {len(blocks)} checked todo(s), "
        f"{cited} cited cloudbuild id(s) — sub-rule A: {len(rule_a)} violation(s); "
        f"sub-rule B: {len(rule_b)} claim(s)-without-evidence; "
        f"sub-rule C: {len(rule_c)} mutation-claim(s)-without-evidence."
    )

    if baseline_write:
        _write_baseline(baseline_path, rule_b, rule_c)
        print(f"✅ Wrote baseline (sub-rule B = {len(rule_b)}, sub-rule C = {len(rule_c)}) to {baseline_path}")
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
    baseline_b = _load_baseline(baseline_path, "claim_without_evidence_baseline")
    rule_b_regression = len(rule_b) > baseline_b
    if rule_b:
        print(f"\nSub-rule B — runtime-green claims without Evidence: {len(rule_b)} (baseline {baseline_b}).")
        for v in rule_b[:20]:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - {rel}:{v.line_no}: {v.detail}")
        if len(rule_b) > 20:
            print(f"  ... + {len(rule_b) - 20} more")

    # Sub-rule C: ratchet against its own (separate) baseline.
    baseline_c = _load_baseline(baseline_path, "mutation_claim_without_evidence_baseline")
    rule_c_regression = len(rule_c) > baseline_c
    if rule_c:
        print(f"\nSub-rule C — prod data-mutation claims without Evidence: {len(rule_c)} (baseline {baseline_c}).")
        for v in rule_c[:20]:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - {rel}:{v.line_no}: {v.detail}")
        if len(rule_c) > 20:
            print(f"  ... + {len(rule_c) - 20} more")

    failed = bool(rule_a) or rule_b_regression or rule_c_regression
    if rule_b_regression:
        print(
            f"\n❌ Sub-rule B regression: {len(rule_b)} > baseline {baseline_b}. "
            f"Add `Evidence: cloudbuild=<id>` to the new claim, or re-baseline with --baseline-write."
        )
    if rule_c_regression:
        print(
            f"\n❌ Sub-rule C regression: {len(rule_c)} > baseline {baseline_c}. "
            f"Add `Evidence: manifest-delta=<path>|vm-log=<path>|gcs-op=<id>|state-list=<before>,<after>` "
            f"to the new claim, or re-baseline with --baseline-write."
        )
    if not failed:
        if len(rule_b) < baseline_b:
            print(f"\n⚠️  Sub-rule B improvement: {len(rule_b)} < baseline {baseline_b}. Re-baseline to codify.")
        if len(rule_c) < baseline_c:
            print(f"\n⚠️  Sub-rule C improvement: {len(rule_c)} < baseline {baseline_c}. Re-baseline to codify.")
        print("\n✅ Evidence-backed-completion: no over-claims; sub-rules B, C at/below baseline.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
