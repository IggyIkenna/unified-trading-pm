#!/usr/bin/env python3
"""Pin each repo's branch-protection RULESET required-status-check contexts to the
check-run name that repo's CURRENT workflow file actually emits — so the gates never
drift when a Quality Gates workflow is renamed.

This is the apply-side companion to ``verify_branch_protection_check_names.py``.
SSOT for the contract + history: ``plans/active/issues/ci_v2_ruleset_check_name_drift_2026_05_30.md``.

NOTE: This manages the modern GitHub **rulesets** (``/repos/{repo}/rulesets``):
  - ``require-quality-gates``      (target ~DEFAULT_BRANCH / main)
  - ``require-staging-lock-check`` (target refs/heads/staging)
It is SEPARATE from the legacy *classic* branch-protection scripts
(``set-branch-protection.sh`` / ``propagation/apply-branch-protection.sh`` →
``/repos/{repo}/branches/{branch}/protection``). Do not conflate the two.

The required QG context is DERIVED from the repo's live workflow file (no hardcoded
check names), so re-running after a workflow migration auto-re-pins:
  - repo has ``.github/workflows/quality-gates-v2.yml`` →  ``<job name:> / quality-gates-v2``
  - else repo has ``.github/workflows/workspace-qg.yml``  →  ``<job name:> / quality-gates``
Staging additionally always requires the stable bare context ``check-staging-lock``.

Idempotent: only rulesets whose current contexts differ from the desired set are PUT.
Default is DRY-RUN. Pass ``--apply`` to perform the writes.

Usage:
  python3 scripts/repo-management/pin_branch_protection_rulesets.py            # dry-run, all repos
  python3 scripts/repo-management/pin_branch_protection_rulesets.py --apply    # apply, all repos
  python3 scripts/repo-management/pin_branch_protection_rulesets.py --repo strategy-service --apply
  python3 scripts/repo-management/pin_branch_protection_rulesets.py --ref staging   # use another branch

Requires: ``gh`` authenticated with admin on the IggyIkenna org repos.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

ORG = "IggyIkenna"
WORKFLOW_REF_DEFAULT = "live-defi-rollout"
STAGING_LOCK_CONTEXT = "check-staging-lock"

# Repos that carry the two managed rulesets. Keep in sync with
# verify_branch_protection_check_names.py.
REPOS = [
    "alerting-service", "batch-live-reconciliation-service", "client-reporting-api",
    "deployment-api", "deployment-service", "deployment-ui", "execution-service",
    "ibkr-gateway-infra", "instruments-service", "market-data-processing-service",
    "market-tick-data-service", "strategy-service", "system-integration-tests",
    "trading-agent-service", "unified-api-contracts", "unified-trading-library",
    "unified-trading-pm",
]

# (workflow file, reusable-job suffix appended to the job's display name)
QG_WORKFLOW_CANDIDATES = [
    (".github/workflows/quality-gates-v2.yml", "quality-gates-v2"),
    (".github/workflows/workspace-qg.yml", "quality-gates"),
]


def gh(args: list[str], inp: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], input=inp, capture_output=True, text=True)


def get_file(repo: str, path: str, ref: str) -> str | None:
    r = gh(["api", f"repos/{ORG}/{repo}/contents/{path}?ref={ref}"])
    if r.returncode != 0:
        return None
    try:
        return base64.b64decode(json.loads(r.stdout)["content"]).decode()
    except Exception:
        return None


def _qg_job_name_line(content: str) -> str | None:
    """Return the 'name: Quality Gates (...)' display name from a workflow file, or None."""
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("name: Quality Gates"):
            return s[len("name:"):].strip()
    return None


def derive_qg_context(repo: str, ref: str) -> tuple[str | None, bool]:
    """Return (emitted_qg_check_context, name_matches_repo).

    The check-run context GitHub records for a reusable-workflow job is
    ``<caller job display name> / <reusable job id>``.
    """
    for path, suffix in QG_WORKFLOW_CANDIDATES:
        content = get_file(repo, path, ref)
        if content is None:
            continue
        name = _qg_job_name_line(content)
        if name:
            return f"{name} / {suffix}", (name == f"Quality Gates ({repo})")
    return None, False


def get_ruleset(repo: str, name: str) -> dict | None:
    r = gh(["api", f"repos/{ORG}/{repo}/rulesets"])
    if r.returncode != 0:
        return None
    for rs in json.loads(r.stdout):
        if rs.get("name") == name and rs.get("target") == "branch":
            d = gh(["api", f"repos/{ORG}/{repo}/rulesets/{rs['id']}"])
            if d.returncode == 0:
                return json.loads(d.stdout)
    return None


def current_contexts(rs: dict) -> list[str]:
    for rule in rs.get("rules", []):
        if rule.get("type") == "required_status_checks":
            return [c["context"] for c in rule["parameters"]["required_status_checks"]]
    return []


def build_put_body(rs: dict, contexts: list[str]) -> dict:
    """Rebuild a ruleset PUT body, replacing only the required_status_checks contexts.

    Preserves enforcement, bypass_actors, conditions, and any non-status-check rules.
    """
    body: dict = {
        "name": rs["name"],
        "target": rs["target"],
        "enforcement": rs["enforcement"],
        "bypass_actors": rs.get("bypass_actors", []),
        "conditions": rs["conditions"],
        "rules": [],
    }
    for rule in rs["rules"]:
        if rule.get("type") == "required_status_checks":
            nr = json.loads(json.dumps(rule))
            nr["parameters"]["required_status_checks"] = [{"context": c} for c in contexts]
            body["rules"].append(nr)
        else:
            body["rules"].append(rule)
    return body


def put_ruleset(repo: str, rs: dict, contexts: list[str]) -> tuple[bool, list[str]]:
    body = build_put_body(rs, contexts)
    p = gh(["api", "-X", "PUT", f"repos/{ORG}/{repo}/rulesets/{rs['id']}", "--input", "-"],
           inp=json.dumps(body))
    if p.returncode != 0:
        sys.stderr.write(f"    PUT failed [{repo}/{rs['name']}]: {p.stderr.strip()[:200]}\n")
        return False, []
    return True, current_contexts(json.loads(p.stdout))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="perform the PUT writes (default: dry-run)")
    ap.add_argument("--repo", help="limit to a single repo")
    ap.add_argument("--ref", default=WORKFLOW_REF_DEFAULT,
                    help=f"branch to read workflow files from (default: {WORKFLOW_REF_DEFAULT})")
    args = ap.parse_args()

    repos = [args.repo] if args.repo else REPOS
    planned: list[tuple[str, dict, list[str], list[str]]] = []
    warnings: list[str] = []

    for repo in repos:
        qg, name_ok = derive_qg_context(repo, args.ref)
        if qg is None:
            warnings.append(f"{repo}: no QG workflow file found on {args.ref} — SKIPPED")
            continue
        if not name_ok:
            warnings.append(f"{repo}: workflow job name is not 'Quality Gates ({repo})' "
                            f"→ derived context '{qg}' (workflow-name bug? fix the workflow, not the ruleset)")
        targets = [
            ("require-quality-gates", [qg]),
            ("require-staging-lock-check", [qg, STAGING_LOCK_CONTEXT]),
        ]
        for rsname, desired in targets:
            rs = get_ruleset(repo, rsname)
            if rs is None:
                continue  # repo doesn't carry this ruleset (e.g. PM has no staging ruleset)
            cur = current_contexts(rs)
            if sorted(cur) != sorted(desired):
                planned.append((repo, rs, cur, desired))

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}  |  ref={args.ref}  |  repos={len(repos)}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ! {w}")
    print(f"\nRuleset changes needed: {len(planned)}")
    for repo, rs, cur, desired in planned:
        print(f"  [{repo}] {rs['name']} id={rs['id']}")
        print(f"      {cur}  ->  {desired}")

    if not args.apply:
        print("\n(dry-run — pass --apply to write)")
        return 0

    if not planned:
        print("\nNothing to apply — already consistent.")
        return 0

    print("\nApplying...")
    failures = 0
    for repo, rs, _cur, desired in planned:
        ok, got = put_ruleset(repo, rs, desired)
        if ok and sorted(got) == sorted(desired):
            print(f"  OK   [{repo}] {rs['name']} -> {got}")
        else:
            failures += 1
            print(f"  FAIL [{repo}] {rs['name']} (got {got})")
    print(f"\nDone. {len(planned) - failures}/{len(planned)} applied; {failures} failures.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
