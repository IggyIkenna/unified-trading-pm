#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
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
Staging additionally always requires the context ``check-staging-lock`` — the BARE job name
emitted by staging-lock-check.yml. (Unlike quality-gates-v2, which is a *reusable-workflow*
call → GitHub prefixes its check with the caller job name "Quality Gates (<repo>) / …", the
staging-lock job is a DIRECT job, so its check-run context is just the job name, no prefix.
Requiring the prefixed "Staging Lock Check / check-staging-lock" leaves the required check
permanently un-reported → PR stuck BLOCKED. Incident: deployment-api #56, 2026-06-11.)

Cloud symmetry: a repo that builds a container image on AWS CodeBuild emits an
``AWS CodeBuild <region> (<repo>)`` commit status on the LDR head; that build MUST gate the
LDR→staging promotion exactly as quality-gates-v2 does. The context is DERIVED from the live
status (no hardcoded region), and added to the STAGING ruleset only — the staging PR head is
the LDR commit that carries the status, whereas a staging→main PR head can be a post-squash
SHA the build never ran on (requiring it on `main` would dead-block promotions).

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
import binascii
import json
import subprocess
import sys

ORG = "IggyIkenna"
WORKFLOW_REF_DEFAULT = "live-defi-rollout"
STAGING_LOCK_CONTEXT = "check-staging-lock"  # BARE job name (direct job, not a reusable-wf call — see docstring)

# SIT-fleet-green required check (operator ruling 2026-07-12, finding 78; plan
# cicd_mvp_ldr_to_main_pipeline_2026_06_30.md). Posted by ldr-to-main-promote-fleet.yml on every
# LDR->main promote PR head, UNCONDITIONALLY (not gated on breaking-ness) — a red or missing status
# now blocks auto-merge fleet-wide, closing the 2026-07-07/08 gap where a promote sailed through
# while cross-repo SIT was red. Required ONLY for ldr_main repos (the ones the fleet promoter
# manages and therefore the only ones that ever get this status posted) — NEVER added to a
# non-ldr_main repo's ruleset (unified-trading-pm / system-integration-tests), whose main-bound
# path is a different workflow that does not post this context; requiring it there would deadlock
# every merge to their main with a permanently-missing check.
SIT_FLEET_CONTEXT = "sit-gate/fleet-green"
# Both ruleset names are seen live across the fleet (naming drift — some repos were provisioned as
# "require-quality-gates", others as "require-quality-gates-main"; functionally identical, both
# target=branch/main). Match either so every ldr_main repo is actually reachable, not just the
# majority-name ones.
MAIN_QG_RULESET_NAMES = ("require-quality-gates", "require-quality-gates-main")

# semver-agent stamps the post-QG `chore(release)` bump by DIRECT-PUSHing to `staging` (as the
# admin GH_PAT, after quality-gates-v2 already passed pre-SIT). The staging required-checks would
# reject a direct push (no PR / no check run on the pushed commit), so the bump bot must BYPASS.
# A ruleset bypass is by ROLE/App/Team — never an individual user — so we bypass the **Repository
# admin role** (actor_id 5). Only admins (IggyIkenna / the GH_PAT) bypass; `write` collaborators
# (e.g. CosmicTrader) stay fully gated by quality-gates-v2 + check-staging-lock. A ruleset bypass
# does NOT bypass CLASSIC protection, so staging classic `enforce_admins` must also be OFF (admins
# bypass classic; non-admins are unaffected by enforce_admins and stay gated). SSOT:
# plans/active/cicd_contract_hardening_2026_06_01.md § "semver-agent can no longer stamp versions".
STAGING_BYPASS_ACTORS = [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]
# Only the staging ruleset gets the bypass — `require-quality-gates` (main) stays strict.
STAGING_BYPASS_RULESET = "require-staging-lock-check"

# Repos that carry the two managed rulesets. Keep in sync with
# verify_branch_protection_check_names.py.
# Extended 2026-07-12 (SIT-fleet-green rollout, finding 78) to the FULL workspace-manifest repo set
# (25 = the 23 ldr_main repos + unified-trading-pm + system-integration-tests) — the prior 17-repo
# list predates several repos (agent-orchestrator, e2e-testing, features-service,
# fund-administration-service, greeks-service, ml-service, unified-trading-api,
# unified-trading-system-ui) that already carry the SAME managed ruleset live (verified via
# `gh api repos/<repo>/rulesets` 2026-07-12) but were never added here — a pre-existing drift gap,
# not something this change introduces. `unified-trading-pm` / `system-integration-tests` are the
# only non-ldr_main repos and get NO SIT context (see ldr_main_repos() below).
REPOS = [
    "agent-orchestrator",
    "alerting-service",
    "batch-live-reconciliation-service",
    "client-reporting-api",
    "deployment-api",
    "deployment-service",
    "deployment-ui",
    "e2e-testing",
    "execution-service",
    "features-service",
    "fund-administration-service",
    "greeks-service",
    "ibkr-gateway-infra",
    "instruments-service",
    "market-data-processing-service",
    "market-tick-data-service",
    "ml-service",
    "strategy-service",
    "system-integration-tests",
    "trading-agent-service",
    "unified-api-contracts",
    "unified-trading-api",
    "unified-trading-library",
    "unified-trading-pm",
    "unified-trading-system-ui",
]


def ldr_main_repos(manifest_path: str = "workspace-manifest.json") -> set[str]:
    """Repos with promotion_model == "ldr_main" in the manifest — the ONLY repos whose LDR->main
    promote PR head ever receives the sit-gate/fleet-green status (posted by
    ldr-to-main-promote-fleet.yml). Read fresh each run (no hardcoded duplicate list) so a manifest
    opt-in/opt-out is picked up automatically on the next --apply."""
    try:
        with open(manifest_path) as f:
            m = json.load(f)
    except OSError:
        return set()
    repos = m.get("repositories", {})
    return {r for r, v in repos.items() if not r.startswith("_") and v.get("promotion_model") == "ldr_main"}


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
    except (json.JSONDecodeError, KeyError, binascii.Error, UnicodeDecodeError):
        return None


def _qg_job_name_line(content: str) -> str | None:
    """Return the 'name: Quality Gates (...)' display name from a workflow file, or None."""
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("name: Quality Gates"):
            return s[len("name:") :].strip()
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
    """Return the ruleset matching `name`, or — for the main QG ruleset — any name in
    MAIN_QG_RULESET_NAMES (naming drift: some repos are provisioned as "require-quality-gates",
    others as "require-quality-gates-main"; both target=branch/main, functionally identical)."""
    names = MAIN_QG_RULESET_NAMES if name == "require-quality-gates" else (name,)
    r = gh(["api", f"repos/{ORG}/{repo}/rulesets"])
    if r.returncode != 0:
        return None
    for rs in json.loads(r.stdout):
        if rs.get("name") in names and rs.get("target") == "branch":
            d = gh(["api", f"repos/{ORG}/{repo}/rulesets/{rs['id']}"])
            if d.returncode == 0:
                return json.loads(d.stdout)
    return None


def current_contexts(rs: dict) -> list[str]:
    for rule in rs.get("rules", []):  # noqa: qg-empty-fallback
        if rule.get("type") == "required_status_checks":
            return [c["context"] for c in rule["parameters"]["required_status_checks"]]
    return []


def current_bypass(rs: dict) -> list[dict]:
    """The ruleset's bypass_actors, normalised to (actor_type, actor_id) for comparison."""
    return [
        {"actor_id": a.get("actor_id"), "actor_type": a.get("actor_type")}
        for a in rs.get("bypass_actors", [])  # noqa: qg-empty-fallback
    ]


def _bypass_matches(rs: dict, desired: list[dict]) -> bool:
    want = sorted((a["actor_type"], a["actor_id"]) for a in desired)
    have = sorted((a["actor_type"], a["actor_id"]) for a in current_bypass(rs))
    return want == have


def build_put_body(rs: dict, contexts: list[str], bypass_actors: list[dict] | None = None) -> dict:
    """Rebuild a ruleset PUT body, replacing the required_status_checks contexts.

    Preserves enforcement, conditions, and non-status-check rules. ``bypass_actors`` overrides the
    ruleset's bypass list when provided (used to grant the staging admin bypass); otherwise the
    existing list is preserved.
    """
    body: dict = {
        "name": rs["name"],
        "target": rs["target"],
        "enforcement": rs["enforcement"],
        "bypass_actors": bypass_actors if bypass_actors is not None else rs.get("bypass_actors", []),  # noqa: qg-empty-fallback
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


def put_ruleset(
    repo: str, rs: dict, contexts: list[str], bypass_actors: list[dict] | None = None
) -> tuple[bool, list[str]]:
    body = build_put_body(rs, contexts, bypass_actors)
    p = gh(["api", "-X", "PUT", f"repos/{ORG}/{repo}/rulesets/{rs['id']}", "--input", "-"], inp=json.dumps(body))
    if p.returncode != 0:
        sys.stderr.write(f"    PUT failed [{repo}/{rs['name']}]: {p.stderr.strip()[:200]}\n")
        return False, []
    return True, current_contexts(json.loads(p.stdout))


def derive_codebuild_context(repo: str, ref: str) -> str | None:
    """Return the ``AWS CodeBuild <region> (<repo>)`` status context this repo emits on ``ref``'s
    HEAD, or None if the repo builds no AWS image (libraries / PM emit no such status). Cloud
    symmetry: a repo that builds a container image on AWS must gate its LDR→staging promotion on
    that build, exactly as it gates on quality-gates-v2. Derived from the live commit status (no
    hardcoded region/name) so a region change auto-re-pins on the next run."""
    r = gh(["api", f"repos/{ORG}/{repo}/commits/{ref}/statuses"])
    if r.returncode != 0:
        return None
    try:
        for s in json.loads(r.stdout):
            ctx = s.get("context")
            if isinstance(ctx, str) and ctx.startswith("AWS CodeBuild"):
                return ctx
    except (json.JSONDecodeError, AttributeError):
        return None
    return None


def classic_enforce_admins(repo: str, branch: str = "staging") -> bool | None:
    """True/False if staging classic protection has enforce_admins on/off; None if no protection."""
    r = gh(["api", f"repos/{ORG}/{repo}/branches/{branch}/protection/enforce_admins"])
    if r.returncode != 0:
        return None
    try:
        return bool(json.loads(r.stdout).get("enabled"))
    except (json.JSONDecodeError, AttributeError):
        return None


def disable_classic_enforce_admins(repo: str, branch: str = "staging") -> bool:
    """DELETE staging classic enforce_admins so admins (the semver GH_PAT) bypass classic too."""
    r = gh(["api", "-X", "DELETE", f"repos/{ORG}/{repo}/branches/{branch}/protection/enforce_admins"])
    if r.returncode != 0:
        sys.stderr.write(f"    enforce_admins DELETE failed [{repo}]: {r.stderr.strip()[:160]}\n")
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="perform the PUT writes (default: dry-run)")
    ap.add_argument("--repo", help="limit to a single repo")
    ap.add_argument(
        "--ref",
        default=WORKFLOW_REF_DEFAULT,
        help=f"branch to read workflow files from (default: {WORKFLOW_REF_DEFAULT})",
    )
    args = ap.parse_args()

    repos = [args.repo] if args.repo else REPOS
    ldr_main = ldr_main_repos()
    # (repo, ruleset, cur_contexts, desired_contexts, desired_bypass|None)
    planned: list[tuple[str, dict, list[str], list[str], list[dict] | None]] = []
    classic_planned: list[str] = []  # repos whose staging classic enforce_admins must be disabled
    warnings: list[str] = []

    for repo in repos:
        qg, name_ok = derive_qg_context(repo, args.ref)
        if qg is None:
            warnings.append(f"{repo}: no QG workflow file found on {args.ref} — SKIPPED")
            continue
        if not name_ok:
            warnings.append(
                f"{repo}: workflow job name is not 'Quality Gates ({repo})' "
                f"→ derived context '{qg}' (workflow-name bug? fix the workflow, not the ruleset)"
            )
        # AWS-image-build gating on staging is DISABLED (2026-06-15). The AWS CodeBuild LDR build is
        # opt-in + unreliable on the LDR head (gated to opt-in via `quickmerge --build`, Gap 5), so a
        # FAILING required `AWS CodeBuild …` context deadlocked EVERY LDR→staging drain on the 8 repos
        # that emit it — main fell ~5 days behind LDR fleet-wide and the deploy-UI Image column went
        # stale. quality-gates-v2 is the real promotion gate; the image build must NOT block the drain
        # off a flaky LDR-head status. Re-introduce image-build gating only via a build that runs GREEN
        # on the PR head pre-merge (the gap5 "PR-head image-build gate" todo), never the LDR-head status.
        # `derive_codebuild_context` is retained for that future PR-head gate. SSOTs:
        # ci_pipeline_self_healing_gaps_2026_06_11.md §Gap5 + github_actions_billing_wall_2026_06_11.md.
        staging_ctx = [qg, STAGING_LOCK_CONTEXT]
        # SIT-fleet-green (finding 78): required on the MAIN ruleset ONLY for ldr_main repos — the
        # only repos ldr-to-main-promote-fleet.yml ever posts this status for. A non-ldr_main repo
        # (unified-trading-pm / system-integration-tests) gets [qg] unchanged; adding the SIT
        # context there would require a status nothing ever posts → permanent block.
        main_ctx = [qg, SIT_FLEET_CONTEXT] if repo in ldr_main else [qg]
        targets = [
            ("require-quality-gates", main_ctx),
            ("require-staging-lock-check", staging_ctx),
        ]
        for rsname, desired in targets:
            rs = get_ruleset(repo, rsname)
            if rs is None:
                continue  # repo doesn't carry this ruleset (e.g. PM has no staging ruleset)
            # The staging ruleset must carry the admin bypass; the main ruleset stays strict.
            desired_bypass = STAGING_BYPASS_ACTORS if rsname == STAGING_BYPASS_RULESET else None
            ctx_drift = sorted(current_contexts(rs)) != sorted(desired)
            bypass_drift = desired_bypass is not None and not _bypass_matches(rs, desired_bypass)
            if ctx_drift or bypass_drift:
                planned.append((repo, rs, current_contexts(rs), desired, desired_bypass))
            # Staging ruleset present → also ensure classic enforce_admins is OFF (so the admin
            # bypass actually works; a ruleset bypass does not bypass classic protection).
            if rsname == STAGING_BYPASS_RULESET and classic_enforce_admins(repo) is True:
                classic_planned.append(repo)

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}  |  ref={args.ref}  |  repos={len(repos)}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ! {w}")
    print(f"\nRuleset changes needed: {len(planned)}")
    for repo, rs, cur, desired, desired_bypass in planned:
        print(f"  [{repo}] {rs['name']} id={rs['id']}")
        print(f"      contexts: {cur}  ->  {desired}")
        if desired_bypass is not None:
            print(f"      bypass:   {current_bypass(rs)}  ->  {desired_bypass}")
    print(f"\nClassic staging enforce_admins to DISABLE: {len(classic_planned)} -> {classic_planned}")

    if not args.apply:
        print("\n(dry-run — pass --apply to write)")
        return 0

    if not planned and not classic_planned:
        print("\nNothing to apply — already consistent.")
        return 0

    print("\nApplying...")
    failures = 0
    for repo, rs, _cur, desired, desired_bypass in planned:
        ok, got = put_ruleset(repo, rs, desired, desired_bypass)
        if ok and sorted(got) == sorted(desired):
            print(f"  OK   [{repo}] {rs['name']} -> {got}")
        else:
            failures += 1
            print(f"  FAIL [{repo}] {rs['name']} (got {got})")
    for repo in classic_planned:
        if disable_classic_enforce_admins(repo):
            print(f"  OK   [{repo}] staging classic enforce_admins -> disabled")
        else:
            failures += 1
            print(f"  FAIL [{repo}] staging classic enforce_admins")
    total = len(planned) + len(classic_planned)
    print(f"\nDone. {total - failures}/{total} applied; {failures} failures.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
