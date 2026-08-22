#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""audit_model_tier.py — audit Sonnet-vs-Opus tier assignment across active plans.

SSOT: codex/06-coding-standards/model-tier-selection.md. That doc says every plan
should carry a `model_tier: sonnet-doable | opus-required` frontmatter field (added
on next substantive touch, NOT mass-swept), and the decision rule escalates to Opus
ONLY for three QUALITATIVE reasons: main/master-orchestrator role, genuine cross-repo
architecture DESIGN JUDGMENT, or trading judgment calls. Context/plan SIZE is NOT a
reason (operator ruling 2026-07-23 — Sonnet 5 has a 1M context window, same as Opus
4.8) — every AO planning-VM-eligible plan defaults to Sonnet 5 at effort:max
regardless of size.

Reality this audit surfaces:
  1. Which active plans DECLARE model_tier (vs the silent Sonnet default).
  2. Which plans the heuristic flags as likely opus-required (for human confirmation).
  3. Mismatches: declared sonnet-doable but heuristic says opus (or vice-versa).

This is read-only + advisory. It does NOT edit frontmatter (the SSOT forbids
mass-sweeping model_tier). It produces the candidate list a human/operator confirms.

Usage: python3 scripts/plans/audit_model_tier.py [--plans-dir plans/active]
Exit 0 always (advisory); prints a table + summary.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Heuristic opus signals — title/name keywords that correlate with the SSOT's 3 QUALITATIVE
# opus-required criteria (main-orchestrator role / cross-repo architecture JUDGMENT / trading
# judgment — never plan size, per the 2026-07-23 ruling). Presence is a FLAG for human review,
# not a verdict. "consolidat" REMOVED 2026-07-23: it matched every "*_consolidated_closeout"
# large-tracker plan (sports/defi/tradfi/cefi/prediction) purely by name pattern, which is
# exactly the size-driven false-positive class the ruling retired — a big tracker plan is a
# Sonnet-5-at-max-effort case, not an opus one, regardless of "consolidated" being in its title.
OPUS_KEYWORDS = (
    "master",
    "architecture",
    "topology",
    "migration",
    "archetype",
    "ledger",
    "regime",
    "allocator",
    "trading",
    "risk",
    "pre-audit",
    "cross-repo",
    "cross_repo",
    "shard",
    "pnl",
    "attribution",
)
# estimate_class values that lean opus (design/research = synthesis-heavy) — a SOFT signal for
# human review only, since design/research work is usually a genuine cross-repo-architecture
# judgment call, not (as of 2026-07-23) a context-size argument.
OPUS_ESTIMATE_CLASSES = ("design", "research")
# SIZE_OPUS_BYTES REMOVED (operator ruling 2026-07-23): Sonnet 5 has a 1M context window — the
# same size as Opus 4.8 — so plan/file SIZE is no longer a valid opus-escalation signal at all.
# The old ">50KB + multiple full files" SSOT trigger this constant implemented is RETIRED; see
# codex/06-coding-standards/model-tier-selection.md's 2026-07-23 ruling. Every AO planning-VM-
# eligible plan defaults to Sonnet 5 at effort:max regardless of size — do NOT reintroduce a size
# threshold here without a matching codex SSOT change.


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm: dict[str, str] = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def heuristic_opus(name: str, title: str, fm: dict[str, str], size: int) -> tuple[bool, list[str]]:
    """Advisory ONLY — per the 2026-07-23 ruling, `size` is accepted for signature
    compatibility but no longer used as an opus signal (kept as a param so callers don't need
    to change; intentionally unused below)."""
    del size  # no longer a signal — see the SIZE_OPUS_BYTES removal note above
    reasons: list[str] = []
    hay = f"{name} {title}".lower()
    hits = sorted({k for k in OPUS_KEYWORDS if k in hay})
    if hits:
        reasons.append(f"keywords:{','.join(hits)}")
    if fm.get("estimate_class") in OPUS_ESTIMATE_CLASSES:
        reasons.append(f"estimate_class={fm.get('estimate_class')}")
    if name.startswith("master_") or fm.get("type") == "epic":
        reasons.append("master/epic plan")
    return (len(reasons) > 0, reasons)


def _running_model_tier() -> str | None:
    """Best-effort detect the EXECUTING agent's model tier from env.

    The orchestrator spawns workers with the plan's declared tier (SSOT:
    model-tier-selection.md § Autonomous enforcement). These env vars carry it
    into the worker process. Returns ``opus`` | ``sonnet`` | ``haiku`` | None.
    """
    for var in ("AGENT_MODEL", "MODEL_TIER", "CLAUDE_MODEL", "ANTHROPIC_MODEL", "ORCHESTRATOR_MAIN_AGENT_MODEL"):
        raw = os.environ.get(var, "").strip().lower()
        if not raw:
            continue
        for tier in ("opus", "sonnet", "haiku"):
            if tier in raw:
                return tier
    return None


def assert_tier(plan_path: Path) -> int:
    """Hard-fail tier gate: STOP if a non-Opus agent runs an opus-required plan.

    Exit 1 = mismatch (the dangerous direction: Sonnet/Haiku on opus-required —
    SSOT "Sonnet on opus-required → STOP"). Exit 0 = match, an acceptable
    over-provision (Opus on sonnet-doable, wasteful not wrong, warned), or the
    running model is undetectable (UNVERIFIED — warned, never false-blocks).
    """
    if not plan_path.is_file():
        print(f"ERROR: plan not found: {plan_path}", file=sys.stderr)
        return 2
    fm = parse_frontmatter(plan_path.read_text(errors="replace"))
    declared = (fm.get("model_tier", "") or "sonnet-doable").strip()
    required = "opus" if declared == "opus-required" else "sonnet"
    running = _running_model_tier()

    if running is None:
        print(
            f"⚠️  model-tier UNVERIFIED for {plan_path.name}: required={required} but running model undetectable "
            f"(set AGENT_MODEL/MODEL_TIER). Not blocking.",
            file=sys.stderr,
        )
        return 0
    if required == "opus" and running != "opus":
        print(
            f"❌ MODEL-TIER MISMATCH — {plan_path.name} is model_tier:opus-required but the running agent is "
            f"'{running}'. STOP and respawn on Opus (SSOT: Sonnet on opus-required → STOP).",
            file=sys.stderr,
        )
        return 1
    if required == "sonnet" and running == "opus":
        print(
            f"⚠️  Opus running a sonnet-doable plan ({plan_path.name}) — allowed but wasteful (~5-10x cost).",
            file=sys.stderr,
        )
        return 0
    print(f"✅ model-tier OK — {plan_path.name}: required={required}, running={running}.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plans-dir", default="plans/active")
    ap.add_argument(
        "--assert",
        dest="assert_plan",
        metavar="PLAN",
        help="Hard-fail boot gate: exit 1 if the running agent's model does not satisfy PLAN's "
        "model_tier (Sonnet/Haiku on opus-required). Reads AGENT_MODEL/MODEL_TIER from env.",
    )
    args = ap.parse_args()

    if args.assert_plan:
        return assert_tier(Path(args.assert_plan))

    plans_dir = Path(args.plans_dir)
    if not plans_dir.is_dir():
        print(f"ERROR: {plans_dir} not found (run from unified-trading-pm root)", file=sys.stderr)
        return 2

    files = sorted(
        p for p in plans_dir.glob("*.md") if p.name not in ("INDEX.md", "_agent_pings.md", "task_template.md")
    )
    declared = 0
    opus_candidates: list[str] = []
    mismatches: list[str] = []
    rows: list[tuple[str, str, str, str]] = []

    for f in files:
        text = f.read_text(errors="replace")
        fm = parse_frontmatter(text)
        title = fm.get("title", "")
        mt = fm.get("model_tier", "")
        size = len(text.encode())
        is_opus, reasons = heuristic_opus(f.stem, title, fm, size)
        if mt:
            declared += 1
        suggest = "opus-required" if is_opus else "sonnet-doable"
        if is_opus:
            opus_candidates.append(f"{f.name}  ({'; '.join(reasons)})")
        # Mismatch = declared tier disagrees with heuristic suggestion.
        if mt and mt != suggest:
            mismatches.append(f"{f.name}: declared={mt} heuristic={suggest}")
        rows.append((f.name, mt or "—(default sonnet)", suggest, "; ".join(reasons) or "bounded"))

    print(f"=== model-tier audit — {len(files)} active plans in {plans_dir} ===\n")
    print(f"{'plan':<58} {'declared':<22} {'heuristic':<15} signals")
    print("-" * 130)
    for name, dec, sug, sig in rows:
        flag = "  ⬅ OPUS?" if sug == "opus-required" else ""
        print(f"{name:<58} {dec:<22} {sug:<15} {sig[:40]}{flag}")

    print("\n=== summary ===")
    print(f"  active plans:                {len(files)}")
    print(f"  declare model_tier:          {declared}  ({len(files) - declared} rely on the silent Sonnet default)")
    print(f"  heuristic opus-candidates:   {len(opus_candidates)}")
    print(f"  declared/heuristic mismatch: {len(mismatches)}")
    if opus_candidates:
        print("\n  --- opus-required candidates (CONFIRM with the SSOT decision rule before setting) ---")
        for c in opus_candidates:
            print(f"    • {c}")
    if mismatches:
        print("\n  --- declared-vs-heuristic mismatches ---")
        for m in mismatches:
            print(f"    • {m}")
    print("\nNOTE: heuristic is advisory. The SSOT decision rule is PURELY QUALITATIVE (main-orchestrator")
    print("role / cross-repo architecture judgment / trading judgment) — plan/context SIZE is never a reason")
    print("(2026-07-23 ruling: Sonnet 5 has 1M context, same as Opus). Set model_tier on a plan's NEXT")
    print("substantive touch (do not mass-sweep).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
