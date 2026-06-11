"""Guard 1 — single-writer enforcement for manifest ``ci_status``.

``repositories.*.ci_status`` is **bot-written state**: only ``ci-status-update[bot]``
(driven by ``quality-gates-v2`` → ``ci-status-update.yml``) may change it. A slot /
Prettier / manual edit forking the value is exactly how the 2026-06-03 staging dam
arose — LDR read ``FEATURE_GREEN`` while main read ``FAILING`` (two independently
edited copies), and the promoter (reading main) dep-blocked the whole fleet behind a
phantom-red base. This guard REJECTS any change to ``ci_status`` not made by the bot.

Comparison is **change-set relative** (working-tree / PR-head vs a baseline ref),
NOT an absolute "LDR == main" check — so a pre-existing fork never blocks unrelated
work; only a commit that *itself* mutates ``ci_status`` is rejected.

CLI:
    python3 scripts/cicd/check_ci_status_bot_only.py
        [--manifest workspace-manifest.json] [--baseline-ref HEAD] [--actor LOGIN]
    exit 0 = OK (no non-bot ci_status change), exit 1 = BLOCK (offenders on stdout)

Fail-OPEN on a missing/unreadable baseline (never block on absent signal) — mirrors
the tier_c_promotion_gate / readiness-gate safe-default convention.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ci_status_store.py is in the same directory; add it to the path for direct-script invocation
# (Python only adds the script's own dir to sys.path for file-based runs, not for stdin/module).
sys.path.insert(0, str(Path(__file__).parent))
from ci_status_store import manifest_ci_status_map as ci_status_map

# Logins permitted to change ci_status (the automated writer + its actions identity).
BOT_ACTORS: frozenset[str] = frozenset({"ci-status-update[bot]", "github-actions[bot]"})
DEFAULT_MANIFEST = "workspace-manifest.json"
DEFAULT_BASELINE_REF = "HEAD"


def diff_ci_status(
    current: dict[str, object],
    baseline: dict[str, object],
) -> dict[str, tuple[str | None, str | None]]:
    """Return {repo: (baseline_status, current_status)} for repos whose ci_status changed.

    ``ci_status_map`` (aliased from ``manifest_ci_status_map``) omits repos with a blank or
    absent ci_status, so ``cur.get(name)`` / ``base.get(name)`` return ``None`` for those —
    identical semantics to the prior inline implementation.
    """
    cur = ci_status_map(current)
    base = ci_status_map(baseline)
    changed: dict[str, tuple[str | None, str | None]] = {}
    for name in cur.keys() | base.keys():
        if cur.get(name) != base.get(name):
            changed[name] = (base.get(name), cur.get(name))
    return changed


def _load_ref_manifest(ref: str, path: str) -> dict[str, object] | None:
    """Load the manifest as committed at ``ref`` (git show). None if unreadable."""
    try:
        out = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        loaded = json.loads(out)
        return loaded if isinstance(loaded, dict) else None
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guard: ci_status is bot-written-only.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--baseline-ref",
        default=DEFAULT_BASELINE_REF,
        help="Git ref to compare against (HEAD locally; origin/<base> in a PR).",
    )
    parser.add_argument("--actor", default="", help="The committing actor login (CI: GITHUB_ACTOR).")
    args = parser.parse_args(argv)

    if args.actor in BOT_ACTORS:
        print(f"OK: actor '{args.actor}' is the ci_status writer — allowed.")
        return 0

    baseline = _load_ref_manifest(args.baseline_ref, args.manifest)
    if baseline is None:
        print(f"OK (fail-open): baseline '{args.baseline_ref}:{args.manifest}' unreadable — not blocking.")
        return 0

    try:
        current = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"OK (fail-open): current manifest unreadable ({exc}) — not blocking.")
        return 0

    changed = diff_ci_status(current, baseline)
    if not changed:
        print("OK: no ci_status changes vs baseline.")
        return 0

    print(f"BLOCK: ci_status is bot-written-only — {len(changed)} field(s) changed vs {args.baseline_ref}:")
    for name, (old, new) in sorted(changed.items()):
        print(f"  {name}: {old} -> {new}")
    print(
        "Revert these — only ci-status-update[bot] may change ci_status "
        "(SSOT: cicd_contract_hardening Guard 1). A manual/Prettier edit forks the value."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
