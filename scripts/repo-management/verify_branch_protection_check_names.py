#!/usr/bin/env python3
"""Verify branch-protection ruleset required-status-check contexts match each repo's
emitted Quality Gates check-run name (require-quality-gates on main, require-staging-lock-check
on staging). Read-only. See plans/active/issues/ci_v2_ruleset_check_name_drift_2026_05_30.md.

Usage: python3 scripts/repo-management/verify_branch_protection_check_names.py
Prints per-repo MAIN/STAGING required contexts + 'ALL RULESETS CONSISTENT: True/False'.
Exit code: 0 when all consistent, 1 when any drift is detected (so CI / the
ruleset-drift-alert workflow can gate + alert on the exit status).

Companion: pin_branch_protection_rulesets.py applies the fix; both are SSOT-linked
to the issue doc above.
"""

import json
import subprocess
from pathlib import Path

# Source the active-repo list from the canonical workspace manifest so this fleet
# check can never silently miss a repo (incident 2026-06-03: the two repos that had
# default_branch drift — unified-trading-api + greeks-service — were absent from the
# old hardcoded list, so the drift was invisible to this verifier). The manifest's
# `repositories` dict is the single source of truth for active repos.
_MANIFEST = Path(__file__).resolve().parents[2] / "workspace-manifest.json"


def _active_repos() -> list[str]:
    data = json.loads(_MANIFEST.read_text())
    repos = data["repositories"]
    # `unified-trading-codex` is archived/folded into PM and never has its own GitHub
    # rules; exclude any entry explicitly marked archived/removed if present.
    return sorted(name for name, meta in repos.items() if not (isinstance(meta, dict) and meta.get("archived")))


REPOS = _active_repos()


def gh(args):
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def contexts_for(repo, rsname):
    r = gh(["api", f"repos/IggyIkenna/{repo}/rulesets"])
    if r.returncode != 0:
        return None
    for rs in json.loads(r.stdout):
        if rs.get("name") == rsname and rs.get("target") == "branch":
            d = gh(["api", f"repos/IggyIkenna/{repo}/rulesets/{rs['id']}"])
            if d.returncode != 0:
                return None
            for rule in json.loads(d.stdout).get("rules", []):  # noqa: qg-empty-fallback
                if rule.get("type") == "required_status_checks":
                    return [c["context"] for c in rule["parameters"]["required_status_checks"]]
            return []
    return None


def main():
    allok = True
    drift = []
    print(f"{'REPO':<32} {'DEFBR':<6} {'MAIN required':<55} {'STAGING required'}")
    print("-" * 138)
    for repo in REPOS:
        m = contexts_for(repo, "require-quality-gates")
        s = contexts_for(repo, "require-staging-lock-check")
        # default_branch MUST be main for EVERY active repo (fleet-wide assertion):
        # require-quality-gates targets ~DEFAULT_BRANCH, so a non-main default (e.g.
        # live-defi-rollout) mislocates the required check onto the integration axis and
        # blocks raw/FF pushes to LDR (GH013). LDR is the unprotected integration axis by
        # design (ci-cd-flow.md); the required check belongs on main (+ staging-lock on
        # staging). Incident 2026-06-03: unified-trading-api + greeks-service had
        # default=live-defi-rollout. Fix = `gh api -X PATCH repos/IggyIkenna/<repo> -f default_branch=main`.
        db = gh(["api", f"repos/IggyIkenna/{repo}", "--jq", ".default_branch"]).stdout.strip()
        db_ok = db == "main"
        # Ruleset-name consistency is only asserted for repos that actually HAVE the
        # require-quality-gates ruleset (m is not None). A repo with no ruleset yet
        # (e.g. agent-orchestrator mid-staging-migration, e2e-testing) is not a failure
        # here — its default-branch is still asserted == main above.
        # M2: assert the FULL derived context, not just the "Quality Gates (<repo>)" PREFIX —
        # a prefix match passes a DEAD "… / quality-gates" (retired workspace-qg) suffix, which
        # blocks merges (no run emits it). The live context is "Quality Gates (<repo>) / quality-gates-v2"
        # fleet-wide (workspace-qg retired 2026-05-29; verified against live rulesets 2026-06-07).
        expected_ctx = f"Quality Gates ({repo}) / quality-gates-v2"
        m_ok = (m is None) or (len(m) == 1 and m[0] == expected_ctx)
        # Staging requires qg + check-staging-lock, PLUS an optional `AWS CodeBuild <region> (<repo>)`
        # cloud-symmetry gate for repos that build an AWS image (pin_branch_protection_rulesets.py
        # derives it). Any extra context must be that CodeBuild status — nothing else.
        s_ok = (s is None) or (
            "check-staging-lock" in s
            and expected_ctx in s
            and all(c in ("check-staging-lock", expected_ctx) or c.startswith("AWS CodeBuild") for c in s)
        )
        flag = "" if (m_ok and s_ok and db_ok) else "  <-- CHECK" + ("" if db_ok else f" [default_branch={db}!=main]")
        if flag:
            allok = False
        if not db_ok:
            drift.append((repo, db))
        print(f"{repo:<32} {db:<6} {m!s:<55} {s!s}{flag}")
    if drift:
        print("\nDEFAULT-BRANCH DRIFT (must be `main`):")
        for repo, db in drift:
            print(f"  {repo}: default_branch={db}  →  gh api -X PATCH repos/IggyIkenna/{repo} -f default_branch=main")
    print("\nALL RULESETS CONSISTENT:", allok)
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
