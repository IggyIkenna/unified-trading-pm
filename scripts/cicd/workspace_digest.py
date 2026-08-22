#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Workspace combination fingerprint — SHA-256 of all ldr_main repos' LDR tree SHAs.

WHY (WS-L SIT-rehome HIGH-combo, cicd_sit_full_coverage_handoff_2026_06_27.md § Phase 2):
the per-repo ``sit_validated_tree`` proves repo R's content passed SIT, but NOT which version of
its siblings were assembled. Repo R validated against UAC v1 can still pass the promote gate after
UAC v2 (breaking) lands — the per-repo tree fingerprint doesn't capture the cross-repo COMBINATION.

The workspace digest fixes this: a SHA-256 of the JSON-serialised sorted mapping
``{repo: LDR_tree_sha for repo in all_ldr_main_repos}`` computed at SIT time. Any change to ANY
assembled repo's LDR tree changes the digest → a stored digest mismatch in the consume gate means
"a dependency changed after SIT ran, re-validate before promoting".

Usage (from shell):
    python3 scripts/cicd/workspace_digest.py <repo1>=<tree1> <repo2>=<tree2> ...
    → prints the digest to stdout

SSOT: plans/active/cicd_sit_full_coverage_handoff_2026_06_27.md Phase 2 HIGH-1.
"""

from __future__ import annotations

import hashlib
import json


def compute_workspace_digest(repo_trees: dict[str, str]) -> str:
    """Compute the workspace digest from a ``{repo: LDR_tree_sha}`` mapping.

    Deterministic: SHA-256 of the UTF-8-encoded canonical JSON (keys sorted, no extra whitespace).
    Empty mapping → deterministic but vacuous digest (no repos assembled = no combination).
    """
    payload = json.dumps(repo_trees, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


if __name__ == "__main__":
    import sys

    # CLI: workspace_digest.py repo1=tree1 repo2=tree2 ...
    trees: dict[str, str] = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            repo, _, tree = arg.partition("=")
            if repo and tree:
                trees[repo] = tree
    print(compute_workspace_digest(trees))
