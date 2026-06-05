#!/usr/bin/env python3
"""Unified flow-health computation for the CI/CD observability surface.

Today only `main`→LDR drift is watched (main-backmerge-to-ldr.yml opens a PR on
conflict). `staging`↔LDR + `main`↔`staging` drift is invisible, and there is no
single "is everything flowing" surface. This module is the pure compute core for
`flow-health-reporter.yml`: it ingests per-repo branch-compare facts (gathered by
the workflow via `gh api .../compare`) and the workspace manifest, and decides a
single firm-wide flow-health verdict — `flow-blocked` (🔴) or `flow-flowing` (🟢)
— with a per-repo breakdown of WHY.

It is deliberately I/O-free + side-effect-free (mirrors tier_c_promotion_gate.py):
the workflow does the `gh api` calls + the transition-gated Slack ping; this file
only turns facts into a verdict so it is hermetically testable.

A repo is "flow-blocked" when ANY of:
  - its LDR CI is red                       (manifest ci_status == FAILING)
  - main↔staging drift exceeds the cap      (either side ahead by > DRIFT_CAP)
  - main↔LDR drift exceeds the cap
  - staging↔LDR drift exceeds the cap
  - it has an open PR stuck >  STUCK_PR_HOURS

Drift "ahead/behind" is the `git rev-list` count from `gh api compare`; a branch
that does not exist in a repo (main-only repo, no staging) contributes no drift
for the pairs involving it. Fail-open on missing data: an absent compare fact or
an unparseable manifest entry never marks a repo blocked.

CLI:
    python3 scripts/cicd/flow_health.py --facts facts.json [--manifest PATH] [--json]
    exit 0 = FLOWING, exit 1 = BLOCKED (human-readable summary on stdout)

`facts.json` shape (produced by flow-health-reporter.yml):
    {
      "repos": {
        "<repo>": {
          "branches": {"main": true, "staging": true, "live-defi-rollout": true},
          "compare": {
            "main_vs_staging":  {"ahead_by": 0, "behind_by": 0},
            "main_vs_ldr":      {"ahead_by": 3, "behind_by": 0},
            "staging_vs_ldr":   {"ahead_by": 1, "behind_by": 0}
          },
          "oldest_open_pr_age_hours": 12.5
        }
      }
    }
`ahead_by`/`behind_by` are relative to the FIRST branch named in the pair key
(github compare semantics: compare(base=A, head=B) → ahead_by = commits on B not
on A). Either being over the cap = drift, since the goal is "the two are level".
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

# A repo's LDR CI is red (per workspace-manifest.json ci_status).
LDR_RED_STATUS = "FAILING"

# Max allowed ahead/behind between any branch pair before it counts as drift.
# 0 would be too strict (a back-merge commit briefly shows ahead-by-1); a small
# cap tolerates in-flight propagation but catches a real dam.
DRIFT_CAP = 5

# An open PR older than this is "stuck" (the conflict PR sat unresolved / a
# promotion PR never merged). Mirrors the spirit of the main→LDR conflict PR.
STUCK_PR_HOURS = 24.0

# The three branch-pair compare keys, with the human label for each.
PAIR_LABELS: dict[str, str] = {
    "main_vs_staging": "main↔staging",
    "main_vs_ldr": "main↔LDR",
    "staging_vs_ldr": "staging↔LDR",
}

DEFAULT_MANIFEST = "workspace-manifest.json"


@dataclass(frozen=True)
class RepoFlow:
    """Flow-health verdict for a single repo."""

    repo: str
    blocked: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class FlowReport:
    """Firm-wide flow-health verdict + per-repo breakdown."""

    blocked: bool
    blocked_repos: tuple[RepoFlow, ...]
    ok_repos: tuple[str, ...]

    def state(self) -> str:
        """Stable state token used for the transition gate (see is_transition)."""
        return "flow-blocked" if self.blocked else "flow-flowing"

    def summary(self) -> str:
        """Human-readable multi-line summary for stdout + the Slack body."""
        if not self.blocked:
            n = len(self.ok_repos)
            return f"🟢 flow-flowing — all {n} active repo(s) level + LDR-green, no stuck PRs"
        lines = [f"🔴 flow-blocked — {len(self.blocked_repos)} repo(s) jammed:"]
        for rf in self.blocked_repos:
            lines.append(f"  • {rf.repo}: {'; '.join(rf.reasons)}")
        return "\n".join(lines)


@dataclass
class _Pair:
    ahead: int = 0
    behind: int = 0


@dataclass
class _RepoFacts:
    branches: dict[str, bool] = field(default_factory=dict)
    pairs: dict[str, _Pair] = field(default_factory=dict)
    oldest_open_pr_age_hours: float | None = None


def _as_int(value: object) -> int:
    """Best-effort non-negative int (fail-open: junk → 0 → no drift)."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value if value > 0 else 0
    if isinstance(value, float):
        return int(value) if value > 0 else 0
    return 0


def _as_float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _parse_repo_facts(raw: object) -> _RepoFacts:
    """Normalise one repo's facts dict; tolerant of missing/malformed fields."""
    facts = _RepoFacts()
    if not isinstance(raw, dict):
        return facts
    raw_d = cast("dict[str, object]", raw)

    branches_obj = raw_d.get("branches")
    if isinstance(branches_obj, dict):
        for name, present in cast("dict[str, object]", branches_obj).items():
            facts.branches[name] = bool(present)

    compare_obj = raw_d.get("compare")
    if isinstance(compare_obj, dict):
        for key, pair_obj in cast("dict[str, object]", compare_obj).items():
            if not isinstance(pair_obj, dict):
                continue
            pd = cast("dict[str, object]", pair_obj)
            facts.pairs[key] = _Pair(ahead=_as_int(pd.get("ahead_by")), behind=_as_int(pd.get("behind_by")))

    facts.oldest_open_pr_age_hours = _as_float_or_none(raw_d.get("oldest_open_pr_age_hours"))
    return facts


def _ci_status(manifest: dict[str, object], repo: str) -> str | None:
    repos_obj = manifest.get("repositories", {})
    if not isinstance(repos_obj, dict):
        return None
    repos = cast("dict[str, object]", repos_obj)
    info = repos.get(repo)
    if not isinstance(info, dict):
        return None
    status = cast("dict[str, object]", info).get("ci_status")
    return str(status) if status else None


def evaluate_repo(
    repo: str,
    facts: _RepoFacts,
    ci_status: str | None,
    *,
    drift_cap: int = DRIFT_CAP,
    stuck_pr_hours: float = STUCK_PR_HOURS,
) -> RepoFlow:
    """Decide whether `repo` is flow-blocked. Pure; fail-open on absent data."""
    reasons: list[str] = []

    if ci_status == LDR_RED_STATUS:
        reasons.append(f"LDR CI {LDR_RED_STATUS}")

    for key, label in PAIR_LABELS.items():
        pair = facts.pairs.get(key)
        if pair is None:
            continue  # no compare fact (branch missing / not gathered) → no drift
        if pair.ahead > drift_cap or pair.behind > drift_cap:
            reasons.append(f"{label} drift (ahead {pair.ahead} / behind {pair.behind} > {drift_cap})")

    age = facts.oldest_open_pr_age_hours
    if age is not None and age > stuck_pr_hours:
        reasons.append(f"stuck PR open {age:.0f}h (> {stuck_pr_hours:.0f}h)")

    return RepoFlow(repo=repo, blocked=bool(reasons), reasons=tuple(reasons))


def evaluate(
    facts_doc: dict[str, object],
    manifest: dict[str, object],
    *,
    drift_cap: int = DRIFT_CAP,
    stuck_pr_hours: float = STUCK_PR_HOURS,
) -> FlowReport:
    """Compute the firm-wide flow-health report from gathered facts + manifest."""
    repos_obj = facts_doc.get("repos", {})
    repos_facts = cast("dict[str, object]", repos_obj) if isinstance(repos_obj, dict) else {}

    blocked: list[RepoFlow] = []
    ok: list[str] = []
    for repo in sorted(repos_facts.keys()):
        rf = evaluate_repo(
            repo,
            _parse_repo_facts(repos_facts[repo]),
            _ci_status(manifest, repo),
            drift_cap=drift_cap,
            stuck_pr_hours=stuck_pr_hours,
        )
        if rf.blocked:
            blocked.append(rf)
        else:
            ok.append(repo)

    return FlowReport(blocked=bool(blocked), blocked_repos=tuple(blocked), ok_repos=tuple(ok))


def is_transition(prev_state: str | None, new_state: str) -> bool:
    """Transition gate (mirror of ci-status-update.yml notify_worthy anti-spam).

    Only a CHANGE between flow-blocked and flow-flowing is notify-worthy. The very
    first observation (prev_state None) is announced only when blocked — a fresh
    🟢 on boot would be noise.
    """
    if prev_state is None:
        return new_state == "flow-blocked"
    return prev_state != new_state


def load_json(path: str | Path) -> dict[str, object]:
    """Load a JSON object; raise to caller on missing/invalid."""
    with open(path) as fh:
        data = cast("object", json.load(fh))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return cast("dict[str, object]", data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unified CI/CD flow-health reporter (compute core)")
    parser.add_argument("--facts", required=True, help="path to gathered per-repo compare facts JSON")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="path to workspace-manifest.json")
    parser.add_argument("--drift-cap", type=int, default=DRIFT_CAP, help="max ahead/behind before drift")
    parser.add_argument("--stuck-pr-hours", type=float, default=STUCK_PR_HOURS, help="open-PR age = stuck")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of text")
    args = parser.parse_args(argv)
    facts_path = cast("str", args.facts)
    manifest_path = cast("str", args.manifest)
    drift_cap = cast("int", args.drift_cap)
    stuck_pr_hours = cast("float", args.stuck_pr_hours)
    emit_json = cast("bool", args.json)

    try:
        facts_doc = load_json(facts_path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        # Fail-open: no facts → flowing (never invent a block on absent signal).
        print(f"🟢 flow-flowing — facts unreadable ({exc}); gate skipped (safe-default)")
        return 0

    try:
        manifest = load_json(manifest_path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        manifest = {}

    report = evaluate(facts_doc, manifest, drift_cap=drift_cap, stuck_pr_hours=stuck_pr_hours)

    if emit_json:
        out: dict[str, object] = {
            "state": report.state(),
            "blocked": report.blocked,
            "blocked_repos": [{"repo": rf.repo, "reasons": list(rf.reasons)} for rf in report.blocked_repos],
            "ok_repos": list(report.ok_repos),
            "summary": report.summary(),
        }
        print(json.dumps(out, indent=2))
    else:
        print(report.summary())

    return 1 if report.blocked else 0


if __name__ == "__main__":
    sys.exit(main())
