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

REPOS = [
    "alerting-service",
    "batch-live-reconciliation-service",
    "client-reporting-api",
    "deployment-api",
    "deployment-service",
    "deployment-ui",
    "execution-service",
    "ibkr-gateway-infra",
    "instruments-service",
    "market-data-processing-service",
    "market-tick-data-service",
    "strategy-service",
    "system-integration-tests",
    "trading-agent-service",
    "unified-api-contracts",
    "unified-trading-library",
    "unified-trading-pm",
]


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
    print(f"{'REPO':<32} {'MAIN required':<55} {'STAGING required'}")
    print("-" * 130)
    for repo in REPOS:
        m = contexts_for(repo, "require-quality-gates")
        s = contexts_for(repo, "require-staging-lock-check")
        # default_branch MUST be main: require-quality-gates targets ~DEFAULT_BRANCH, so a non-main
        # default (e.g. live-defi-rollout) mislocates the required check onto the integration axis and
        # blocks raw/FF pushes to LDR (GH013). LDR is the unprotected integration axis by design
        # (ci-cd-flow.md); the required check belongs on main (+ staging-lock on staging). Incident
        # 2026-06-03: unified-trading-api + greeks-service had default=live-defi-rollout. Fix = set default=main.
        db = gh(["api", f"repos/IggyIkenna/{repo}", "--jq", ".default_branch"]).stdout.strip()
        db_ok = db == "main"
        m_ok = m is not None and len(m) == 1 and m[0].startswith(f"Quality Gates ({repo})")
        s_ok = (s is None) or (
            len(s) == 2 and "check-staging-lock" in s and any(c.startswith(f"Quality Gates ({repo})") for c in s)
        )
        flag = "" if (m_ok and s_ok and db_ok) else "  <-- CHECK" + ("" if db_ok else f" [default_branch={db}!=main]")
        if flag:
            allok = False
        print(f"{repo:<32} {m!s:<55} {s!s}{flag}")
    print("\nALL RULESETS CONSISTENT:", allok)
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
