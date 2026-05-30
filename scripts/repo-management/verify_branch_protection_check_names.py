#!/usr/bin/env python3
"""Verify branch-protection ruleset required-status-check contexts match each repo's
emitted Quality Gates check-run name (require-quality-gates on main, require-staging-lock-check
on staging). Read-only. See plans/active/issues/ci_v2_ruleset_check_name_drift_2026_05_30.md.

Usage: python3 scripts/repo-management/verify_branch_protection_check_names.py
Prints per-repo MAIN/STAGING required contexts + 'ALL RULESETS CONSISTENT: True/False'.
"""

import json, subprocess

REPOS = ["alerting-service","batch-live-reconciliation-service","client-reporting-api",
"deployment-api","deployment-service","deployment-ui","execution-service","ibkr-gateway-infra",
"instruments-service","market-data-processing-service","market-tick-data-service","strategy-service",
"system-integration-tests","trading-agent-service","unified-api-contracts","unified-trading-library",
"unified-trading-pm"]

def gh(args):
    return subprocess.run(["gh"]+args, capture_output=True, text=True)

def contexts_for(repo, rsname):
    r=gh(["api",f"repos/IggyIkenna/{repo}/rulesets"])
    if r.returncode!=0: return None
    for rs in json.loads(r.stdout):
        if rs.get("name")==rsname and rs.get("target")=="branch":
            d=gh(["api",f"repos/IggyIkenna/{repo}/rulesets/{rs['id']}"])
            if d.returncode!=0: return None
            for rule in json.loads(d.stdout).get("rules",[]):
                if rule.get("type")=="required_status_checks":
                    return [c["context"] for c in rule["parameters"]["required_status_checks"]]
            return []
    return None

allok=True
print(f"{'REPO':<32} {'MAIN required':<55} {'STAGING required'}")
print("-"*130)
for repo in REPOS:
    m=contexts_for(repo,"require-quality-gates")
    s=contexts_for(repo,"require-staging-lock-check")
    # validation: main must be exactly [QG]; staging must be [QG, check-staging-lock]
    m_ok = m is not None and len(m)==1 and m[0].startswith("Quality Gates ("+repo+")")
    s_ok = (s is None) or (len(s)==2 and "check-staging-lock" in s and any(c.startswith("Quality Gates ("+repo+")") for c in s))
    flag = "" if (m_ok and s_ok) else "  <-- CHECK"
    if flag: allok=False
    print(f"{repo:<32} {str(m):<55} {str(s)}{flag}")
print("\nALL RULESETS CONSISTENT:", allok)
