#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Strict-quickmerge guard — reject a CODE commit on the integration branch that bypassed quickmerge.

HARD RULE (codified 2026-06-08, CLAUDE.md + SUB_AGENT + codex/08-workflows/ci-cd-flow.md §
strict-quickmerge): CODE reaches `live-defi-rollout`/`staging`/`main` ONLY via
`quickmerge --agent --files`. A direct `git push` of code dodges the dep gates and silently
piles behind main with no staging PR. This guard catches the bypass: quickmerge stamps a
`Quickmerge:` trailer on its commits; a commit that changes SOURCE (`*.py`/`*.ts`/`*.tsx`
outside tests/.github and outside the gate-infra subset of scripts/) without that trailer, and
is not a carve-out, is a violation.

**Closed carve-out set** (the only sanctioned direct pushes — allowed without the trailer):
  - docs / plans / codex / markdown / config: `*.md`, `*.mdc`, `plans/**`, `codex/**`, `docs/**`,
    `*.yaml|yml|json|toml` (non-source)
  - CI/infra: `.github/**` (any repo's workflow files) + the GATE-INFRA subset of `scripts/`
    only — `scripts/quality_gates/**`, `scripts/quality-gates-base/**`, `scripts/hooks/**`,
    `scripts/cicd/**`, `scripts/quality-gates*.sh`. This is the chicken-and-egg case the carve
    exists for: a corrected gate can't pass through the gate it is fixing.
    NARROWED 2026-08-10 (operator ruling) from D16's blanket `scripts/**`, which let a
    production backfill script reach live-defi-rollout ungated and redden the fleet's promote
    gate — see GATE_INFRA_PREFIX below for the full incident rationale. Everything else under
    `scripts/` is production code by consequence and is gated like any other source.
  - merge/reconcile commits + `[skip ci]` automation (ci_status / manifest writes) + bot authors
    (this covers `_backmerge` merges too — e.g. "Merge remote-tracking branch 'origin/main' into
    _backmerge" is a genuine 2-parent merge commit and needs no separate special-casing; see
    `test_backmerge_merge_commit_is_exempt`)
  - already-promoted content (reachable from `origin/main`/`origin/staging`): a backmerged
    `promote(...)` squash / drift-tick merge that already cleared the v2 gate — exempt so the
    promote bot stops perpetually re-flagging it (provenance_gate_backmerge_already_promoted_2026_06_24)

WARN by default; set `STRICT_QUICKMERGE_BLOCK=1` (or `--block`) to hard-fail (exit 1). Intended
as a `pre-push` hook on the integration branch + an ad-hoc audit tool. An unresolvable/invalid
`--range` is a DIFFERENT, always-hard-fail case (fail CLOSED, unconditional of --block): it means
the scan could not run at all, so it must never be reported as "0 bypassed code commits".

Usage:
    check_strict_quickmerge.py --range origin/live-defi-rollout..HEAD [--block]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import cast

# GitHub's CI-skip literal — the literal [skip ci] or [ci skip] ANYWHERE in a commit message
# (including the body, even when only describing it) causes GitHub to skip ALL required checks
# on any PR whose head commit contains it. The safe alternative is "skip-ci" (no brackets).
# CLAUDE.md: "write `skip-ci`; recovery `gh workflow run quality-gates-v2.yml --ref <branch>`".
_SKIP_CI_RE = re.compile(r"\[(?:skip[ _-]?ci|ci[ _-]?skip)\]", re.IGNORECASE)

SOURCE_EXT = (".py", ".ts", ".tsx")
CARVE_PREFIX = (".github/", "plans/", "codex/", "docs/")
CARVE_EXT = (".md", ".mdc", ".yaml", ".yml", ".json", ".toml", ".txt", ".cfg", ".ini", ".lock")
NONSOURCE_DIR = ("tests/", "test/", ".github/")

# The CHICKEN-AND-EGG subset of `scripts/` — the only part still carved out (operator ruling
# 2026-08-10, NARROWING D16's blanket all-repos `scripts/**` carve of 2026-08-08).
#
# WHY THE BLANKET CARVE WAS WRONG: D16's stated rationale is real but narrow — "a corrected gate
# can't pass through the gate it is fixing". That justifies exempting the gate machinery itself.
# It does NOT justify exempting every `scripts/*.py`, and the asymmetry it created was
# load-bearing in two same-day incidents on 2026-08-10:
#   1. market-tick-data-service `scripts/restamp_tradfi_cme_future_blank_instrument_id_...py`
#      reached live-defi-rollout with a `gsutil ls` call and NO quality gate, then reddened
#      LDR + a promote PR for the whole fleet via QG STEP 5.105.
#   2. The push guard exempted `scripts/**` while QG STEP 5.105 SCANS `scripts/**`. One surface
#      waved the path through; the other policed it. Files that are structurally allowed to skip
#      the gate still break the gate for everyone else.
# Scripts under `scripts/` run against PRODUCTION data (backfills, migrations, restamps) — they
# are production code by consequence, whatever directory they live in.
#
# Anything matched here stays exempt; every other `scripts/**` `.py`/`.ts`/`.tsx` is now normal
# gated source and needs a `Quickmerge:` trailer like any other code.
GATE_INFRA_PREFIX = (
    "scripts/quality_gates/",  # the ratchet checkers themselves
    "scripts/quality-gates-base/",  # base-service.sh + its step library
    "scripts/hooks/",  # pre-push / commit-msg guards, incl. THIS check's own hook
    "scripts/cicd/",  # this file, quickmerge provenance, promote-gate machinery
)
# Bare-file forms that carry no directory of their own (`scripts/quality-gates.sh`, and any
# `scripts/quality-gates*.sh` variant) — same chicken-and-egg argument.
GATE_INFRA_FILE_PREFIX = ("scripts/quality-gates",)
# Promoted projections (provenance_gate_backmerge_already_promoted_2026_06_24): a commit on the
# integration branch that is ALSO reachable from one of these arrived via a BACKMERGE of
# already-promoted content — a `promote(staging->main)` squash drift-ticked back to LDR, or a
# main/staging->LDR backmerge — NOT a fresh direct-push bypass. It already cleared the v2 gate on
# its way to that projection, so re-flagging it perpetually BLOCKS the drain (the recurring
# "Provenance gate BLOCKED" on a backmerged promote-squash, e.g. UTL 28072bc). Exempt it.
PROMOTED_REFS = ("origin/main", "origin/staging")


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _git(*args: str) -> str:
    return _run_git(*args).stdout


def _on_promoted_tip(sha: str) -> bool:
    """True iff ``sha`` is already reachable from a promoted projection (origin/main|staging).

    Fail-safe: a missing/unfetched ref (or invalid sha) → ``merge-base --is-ancestor`` returns
    non-zero → treated as NOT promoted → the commit stays subject to the normal violation check.
    So a ref the workflow forgot to fetch can only OVER-flag (the prior false-positive), never
    under-flag a genuine bypass.
    """
    return any(
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, ref], capture_output=True).returncode == 0
        for ref in PROMOTED_REFS
    )


def _is_gate_infra(path: str) -> bool:
    """True for the chicken-and-egg `scripts/` subset that stays carved out.

    Anchored with ``startswith`` (not the substring test ``NONSOURCE_DIR`` uses): a repo-relative
    path is what git hands us, so a real `scripts/cicd/x.py` matches while an unrelated
    `src/vendor/scripts/cicd/x.py` does not silently inherit the exemption.
    """
    return path.startswith(GATE_INFRA_PREFIX) or path.startswith(GATE_INFRA_FILE_PREFIX)


def _is_source(path: str) -> bool:
    if not path.endswith(SOURCE_EXT):
        return False
    if _is_gate_infra(path):
        return False
    return not any(seg in path for seg in NONSOURCE_DIR)


def _is_carveout_file(path: str) -> bool:
    return path.startswith(CARVE_PREFIX) or path.endswith(CARVE_EXT) or _is_gate_infra(path)


def _has_skip_ci_literal(sha: str) -> tuple[bool, str]:
    """Return (True, label) if a non-bot commit body contains a [skip ci]/[ci skip] literal.

    Bot commits use the literal intentionally (e.g. manifest/version-bump automation), so they
    are exempt. Human/agent commits that DESCRIBE the pattern accidentally trigger GitHub's CI-skip
    on every PR whose head commit is this SHA → required checks never appear → PR permanently
    BLOCKED (the recurring "#559 / #575" footgun class). The safe form is "skip-ci" (no brackets).
    """
    author = _git("show", "-s", "--format=%an", sha).strip()
    if "github-actions" in author.lower() or "[bot]" in author.lower():
        return False, ""
    msg = _git("show", "-s", "--format=%B", sha)
    m = _SKIP_CI_RE.search(msg)
    if m:
        subj = _git("show", "-s", "--format=%h %s", sha).strip()
        return True, f"{subj}  [message contains '{m.group()}' — GitHub will skip required checks]"
    return False, ""


_REPROVENANCE_RE = re.compile(r"^Reprovenance:\s*([0-9a-fA-F]{8,40})\s*$", re.MULTILINE)


def _collect_reprovenanced(shas: list[str]) -> set[str]:
    """Full SHAs forgiven by a `Reprovenance: <sha>` trailer in a PROVENANCED commit in the range.

    The self-service escape for a MID-HISTORY bypass (2026-07-17). A trailer-less source commit
    that is not the branch tip cannot be given a `Quickmerge:` trailer without rewriting shared
    history (banned), and it never becomes `_on_promoted_tip` because the promote it would ride is
    itself BLOCKED by it — a genuine deadlock (proven: revert leaves the sha in-range and only ADDS
    a violation; a content-identical re-ship is a no-op). So neither remedy the alert used to name
    ("re-ship via quickmerge" / "revert") could clear it.

    A re-provenance commit closes that: an EMPTY commit that (a) is itself provenanced (carries a
    `Quickmerge:` trailer, or is a bot/[skip ci] commit) and (b) carries `Reprovenance: <sha>`
    naming the bypass. It is created by scripts/cicd/reprovenance_bypass.sh AFTER that script runs
    the dep-alignment gate — i.e. the same dep-provenance guarantee a fresh quickmerge gives, applied
    to content that is already on LDR and green. The blessing is explicit and auditable: the commit
    names exactly the sha it forgives, and only a provenanced commit can bless (a bare bypass cannot
    self-forgive without ALSO going through quickmerge/being a carve-out empty commit).

    Match is prefix-based (the trailer may carry a short sha), ≥8 hex, against the range's full shas.
    """
    blessed: set[str] = set()
    prefixes: set[str] = set()
    for sha in shas:
        msg = _git("show", "-s", "--format=%B", sha)
        author = _git("show", "-s", "--format=%an", sha).strip()
        is_provenanced = (
            "Quickmerge:" in msg
            or "[skip ci]" in msg
            or "github-actions" in author.lower()
            or "[bot]" in author.lower()
        )
        if not is_provenanced:
            continue  # only a provenanced commit may bless — no self-forgiveness by a bare bypass
        for m in _REPROVENANCE_RE.finditer(msg):
            prefixes.add(m.group(1).lower())
    if not prefixes:
        return blessed
    for sha in shas:
        low = sha.lower()
        if any(low.startswith(p) for p in prefixes):
            blessed.add(sha)
    return blessed


def commit_violates(sha: str, reprovenanced: set[str] | None = None) -> tuple[bool, str]:
    msg = _git("show", "-s", "--format=%B", sha)
    author = _git("show", "-s", "--format=%an", sha).strip()
    parents = _git("show", "-s", "--format=%P", sha).split()
    if len(parents) > 1:
        return False, "merge/reconcile commit"
    if _on_promoted_tip(sha):
        return False, "already promoted (reachable from origin/main|staging — backmerge, not a fresh bypass)"
    if reprovenanced and sha in reprovenanced:
        return False, "re-provenanced (a later Quickmerge-provenanced commit carries Reprovenance: <sha>)"
    if "[skip ci]" in msg or "github-actions" in author.lower() or "[bot]" in author.lower():
        return False, "automation/[skip ci]/bot"
    if "Quickmerge:" in msg:
        return False, "passed through quickmerge"
    files = [f for f in _git("show", "--name-only", "--format=", sha).splitlines() if f.strip()]
    source = [f for f in files if _is_source(f)]
    if not source:
        return False, "carve-out (no source changed)"
    # a source change WITHOUT a quickmerge trailer and not a carve-out-only commit
    return True, f"source changed without quickmerge: {source[:5]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default="origin/live-defi-rollout..HEAD")
    ap.add_argument("--block", action="store_true")
    args = ap.parse_args()
    rng = cast(str, args.range)
    block = cast(bool, args.block) or os.environ.get("STRICT_QUICKMERGE_BLOCK") == "1"

    rev_list = _run_git("rev-list", rng)
    if rev_list.returncode != 0:
        # FAIL CLOSED (2026-07-26): an unresolvable/invalid --range (typo'd ref, unfetched branch)
        # must never read as "0 bypassed code commits" — `git rev-list` on a bad range prints an
        # error to stderr and empty stdout, which previously fell straight through to the ✅ path.
        # This is a hard usage/config error, not a "no violations found" verdict, so it exits
        # non-zero UNCONDITIONALLY (independent of --block / STRICT_QUICKMERGE_BLOCK — those only
        # gate the warn-vs-block choice for a REAL scan result, not "the scan could not run").
        print(f"❌ strict-quickmerge: could not resolve range {rng!r} — git rev-list failed:")
        print(f"   {rev_list.stderr.strip()}")
        return 1
    shas = [s for s in rev_list.stdout.splitlines() if s.strip()]
    reprovenanced = _collect_reprovenanced(shas)
    violations: list[str] = []
    for sha in shas:
        bad, why = commit_violates(sha, reprovenanced)
        if bad:
            subj = _git("show", "-s", "--format=%h %s", sha).strip()
            violations.append(f"{subj}  [{why}]")

    skip_ci_hits: list[str] = []
    for sha in shas:
        hit, label = _has_skip_ci_literal(sha)
        if hit:
            skip_ci_hits.append(label)

    rc = 0
    if violations:
        print(f"{'❌' if block else '⚠️ '} strict-quickmerge: {len(violations)} code commit(s) bypassed quickmerge:")
        for v in violations:
            print(f"  - {v}")
        print("   Ship code via `quickmerge --agent --files '<paths>'` (NOT a direct push). Carve-out: dirty-deps,")
        print("   FF-pull-in + PM docs(plans) flip, PM scripts/.github + any .github/workflows that must reach main.")
        if block:
            rc = 1
        else:
            print("   (WARN only — set STRICT_QUICKMERGE_BLOCK=1 to enforce.)")

    if skip_ci_hits:
        marker = "❌" if block else "⚠️ "
        n = len(skip_ci_hits)
        print(f"{marker} [skip ci] literal in {n} commit(s) — GitHub skips required checks → PR BLOCKED:")
        for s in skip_ci_hits:
            print(f"  - {s}")
        print("   Replace '[skip ci]' with 'skip-ci' (no brackets) in the message, even in prose descriptions.")
        print("   Recovery: `gh workflow run quality-gates-v2.yml --ref <branch>`")
        if block:
            rc = 1
        else:
            print("   (WARN only — set STRICT_QUICKMERGE_BLOCK=1 to enforce.)")

    if not violations and not skip_ci_hits:
        print(f"✅ strict-quickmerge: no bypassed code commits in {rng}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
