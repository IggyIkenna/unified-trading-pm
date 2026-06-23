#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""audit_model_tier.py — audit Sonnet-vs-Opus tier assignment across active plans.

SSOT: codex/06-coding-standards/model-tier-selection.md. That doc says every plan
should carry a `model_tier: sonnet-doable | opus-required` frontmatter field (added
on next substantive touch, NOT mass-swept), and the decision rule escalates to Opus
only for: main/master-orchestrator work, cross-repo architecture, large-migration
pre-audit, trading-judgment, or provably >200k context.

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
import re
import sys
from pathlib import Path

# Heuristic opus signals — title/name keywords that correlate with the SSOT's
# opus-required criteria (cross-repo architecture / large migration / trading
# judgment / master-orchestrator). Presence is a FLAG for human review, not a verdict.
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
    "consolidat",
    "shard",
    "pnl",
    "attribution",
)
# estimate_class values that lean opus (design/research = synthesis-heavy).
OPUS_ESTIMATE_CLASSES = ("design", "research")
SIZE_OPUS_BYTES = 50_000  # SSOT: ">50KB + multiple full files" is an opus signal


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
    reasons: list[str] = []
    hay = f"{name} {title}".lower()
    hits = sorted({k for k in OPUS_KEYWORDS if k in hay})
    if hits:
        reasons.append(f"keywords:{','.join(hits)}")
    if fm.get("estimate_class") in OPUS_ESTIMATE_CLASSES:
        reasons.append(f"estimate_class={fm.get('estimate_class')}")
    if size > SIZE_OPUS_BYTES:
        reasons.append(f"size={size // 1000}KB>50KB")
    if name.startswith("master_") or fm.get("type") == "epic":
        reasons.append("master/epic plan")
    return (len(reasons) > 0, reasons)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plans-dir", default="plans/active")
    args = ap.parse_args()

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
    print("\nNOTE: heuristic is advisory. The SSOT decision rule (context-size + cross-repo synthesis)")
    print("needs human judgment. Set model_tier on a plan's NEXT substantive touch (do not mass-sweep).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
