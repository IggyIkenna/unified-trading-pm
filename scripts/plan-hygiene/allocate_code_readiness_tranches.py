#!/usr/bin/env python3
"""Allocate every active plan/issue doc to exactly one code-readiness tranche.

# Epic: system_readiness_master
# Lifecycle: durable -- re-run whenever the active corpus changes to re-derive the allocation.
# Delete-when: the code-readiness push closes and all five tranche plans are archived.

Partition axis is the OWNING REPO, not `parent_epic` and not the raw `repos:` list:

* `parent_epic` is too coarse -- `security_and_cross_cutting_master` alone owns 240 docs.
* `repos:` lists DEPENDENCIES, so `unified-api-contracts` / `unified-trading-library` /
  `unified-trading-pm` appear on most docs and a naive first-match sends everything to one tranche.

So the primary repo is scored: filename and title tokens dominate, the `repos:` list only breaks
ties, and the three ubiquitous dependency repos are demoted unless they are clearly the subject.

Tranches are repo-disjoint so two agents never edit the same file -- the workspace's
"different repos safe; same file never" rule.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parents[2]
ACTIVE = PM_ROOT / "plans" / "active"

TRANCHES: dict[str, list[str]] = {
    "T1-contracts-library-externalapi": [
        "unified-api-contracts",
        "unified-trading-library",
        "unified-trading-api",
        "deployment-api",
        "deployment-ui",
        "unified-trading-system-ui",
    ],
    "T2-refdata-marketdata": [
        "instruments-service",
        "market-tick-data-service",
        "market-data-processing-service",
    ],
    "T3-features-ml-strategy": [
        "features-service",
        "ml-service",
        "strategy-service",
    ],
    "T4-execution-settlement": [
        "execution-service",
        "batch-live-reconciliation-service",
        "fund-administration-service",
        "greeks-service",
        "client-reporting-api",
        "trading-agent-service",
        "ibkr-gateway-infra",
    ],
    "T5-readiness-observability-presentations": [
        "deployment-service",
        "alerting-service",
        "e2e-testing",
        "system-integration-tests",
        "unified-trading-ci",
        "agent-orchestrator",
        "unified-trading-pm",
    ],
}

REPO_TO_TRANCHE: dict[str, str] = {repo: tranche for tranche, repos in TRANCHES.items() for repo in repos}

# Repos named on almost every doc as a dependency -- demoted so they never win by ubiquity.
UBIQUITOUS: frozenset[str] = frozenset({"unified-api-contracts", "unified-trading-library", "unified-trading-pm"})

# Filename/title tokens that identify a repo as the SUBJECT of the doc.
SUBJECT_TOKENS: dict[str, tuple[str, ...]] = {
    "unified-api-contracts": ("uac", "unified_api_contracts", "contracts_registry", "venue_capabilit"),
    "unified-trading-library": ("utl", "unified_trading_library", "path_registry", "cloud_interface"),
    "instruments-service": ("instrument", "^is_", "catalogue", "urdi"),
    "market-tick-data-service": ("mtds", "market_tick", "tardis"),
    "market-data-processing-service": ("mdps", "market_data_processing", "candle"),
    "features-service": ("feature", "^fs_"),
    "ml-service": ("ml_service", "^ml_", "model_registry"),
    "strategy-service": ("strategy", "archetype", "wizard", "allocator", "^ss_"),
    "execution-service": ("execution", "^exec_", "order_", "connector", "custody", "repricer"),
    "batch-live-reconciliation-service": ("batch_live", "reconciliation_service", "blrs"),
    "fund-administration-service": ("fund_admin", "nav_", "fund_administration"),
    "greeks-service": ("greeks",),
    "client-reporting-api": ("client_report",),
    "trading-agent-service": ("trading_agent",),
    "ibkr-gateway-infra": ("ibkr",),
    "unified-trading-api": ("unified_trading_api", "external_api", "public_api"),
    "deployment-api": ("deployment_api",),
    "deployment-service": ("deployment_service", "^deploy_"),
    "deployment-ui": ("deployment_ui",),
    "unified-trading-system-ui": ("system_ui", "dart_", "^ui_"),
    "alerting-service": ("alert",),
    "e2e-testing": ("e2e",),
    "system-integration-tests": ("^sit_", "system_integration"),
    "unified-trading-ci": ("^ci_", "quality_gate", "quickmerge", "workflow"),
    "agent-orchestrator": ("orchestrator", "^ao_", "escalation_queue", "agent_worker", "spawn"),
    "unified-trading-pm": ("presentation", "plan_hygiene", "plan_reconcile", "doc_frontmatter", "^epic_"),
}

# Docs whose ENTIRE subject is running data movement -- out of scope per operator ruling
# 2026-08-19 ("manifest migration and data backfills should not be tackled"). Code fixes in the
# manifest writer / path registry are NOT excluded here; only docs that exist to run or babysit a
# backfill, migration sweep or VM relaunch.
DATA_MOVEMENT = re.compile(
    r"(^dp_vm_\d+_)"
    r"|(_relaunch(_|$))|(relaunch_bound_page)"
    r"|(^.*_backfill_(vm|fleet|checkpoints|incomplete|never_relaunched))"
    r"|(preempted)|(_wedged_)|(_oom_)"
    r"|(content_migration_corpus)"
    r"|(legacy_canonical_backfill)|(legacy_fold_relaunch)"
    r"|(manifest_migration_scope)|(canonical_migration_)",
    re.IGNORECASE,
)


# parent_epic -> tranche hint. Asset-group epics (defi/cefi/tradfi/sports/predictions) and the
# 240-doc security_and_cross_cutting catch-all are deliberately ABSENT -- they span the whole
# pipeline, so those docs must win their tranche on repo signal alone.
EPIC_HINT: dict[str, str] = {
    "uac_master": "T1-contracts-library-externalapi",
    "instruments_master": "T2-refdata-marketdata",
    "mtds_mdps_master": "T2-refdata-marketdata",
    "manifest_master": "T2-refdata-marketdata",
    "features_and_ml_master": "T3-features-ml-strategy",
    "strategy_master": "T3-features-ml-strategy",
    "execution_master": "T4-execution-settlement",
    "client_isolation_and_governance_master": "T4-execution-settlement",
    "batch_live_symmetry_master": "T3-features-ml-strategy",
    "observability_master": "T5-readiness-observability-presentations",
    "ci_master": "T5-readiness-observability-presentations",
    "orchestrator_master": "T5-readiness-observability-presentations",
    "plan_hygiene_master": "T5-readiness-observability-presentations",
    "agent_operating_framework_master": "T5-readiness-observability-presentations",
    "deployment_and_user_management_master": "T5-readiness-observability-presentations",
    "infrastructure_master": "T5-readiness-observability-presentations",
    "system_readiness_master": "T5-readiness-observability-presentations",
}


SPINE_SOURCES: tuple[str, ...] = (
    "plans/epics/system_readiness_master.md",
    "plans/audit/results/code_completion_scope_2026_08_19.md",
    "codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html",
    "codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html",
    "codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html",
    "codex/14-customer-journeys/commercial-model/platform-architecture.html",
)


def load_spine_text() -> str:
    """Concatenated text of everything that makes a claim the presentations must stand behind."""
    parts: list[str] = []
    for rel in SPINE_SOURCES:
        fp = PM_ROOT / rel
        if fp.exists():
            parts.append(fp.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


# Hand-verified corrections where token scoring picks the wrong subject. Each entry was READ before
# being overridden -- never add one on a hunch.
OVERRIDES: dict[str, str] = {
    # UAC registry issues that scored to another tranche on an incidental repo mention.
    "three_chain_registries_disagree_none_authoritative_2026_08_19": "T1-contracts-library-externalapi",
    "registry_ssot_hardening_2026_08_16": "T1-contracts-library-externalapi",
    "uac_data_type_validity_combinator_fragmentation_2026_07_07": "T1-contracts-library-externalapi",
    "coverage_floor_registries_no_cross_propagation_2026_07_17": "T1-contracts-library-externalapi",
    # MDPS-owned, scored to instruments on a "catalogue"/"instrument" token.
    "mdps_multi_instrument_bundle_write_race_hypothesis_2026_08_09": "T2-refdata-marketdata",
}


@dataclass
class Doc:
    path: str
    name: str
    title: str
    repos: list[str]
    parent_epic: str
    open_todos: int
    tranche: str = ""
    primary_repo: str = ""
    excluded: bool = False
    spine: bool = False
    priority: str = ""
    scores: dict[str, int] = field(default_factory=dict)


def _front(text: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.*?)(?=^[a-z_]+:|^---)", text[:8000], re.S | re.M)
    return m.group(1).strip() if m else ""


def load_docs() -> list[Doc]:
    docs: list[Doc] = []
    paths = sorted(ACTIVE.glob("*.md")) + sorted((ACTIVE / "issues").glob("*.md"))
    for p in paths:
        if p.name in {"INDEX.md", "_agent_pings.md", "task_template.md"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        repos = [r for r in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", _front(text, "repos")) if r in REPO_TO_TRANCHE]
        docs.append(
            Doc(
                path=str(p.relative_to(PM_ROOT)),
                name=p.stem,
                title=_front(text, "title").replace("\n", " ")[:200],
                repos=repos,
                parent_epic=_front(text, "parent_epic").split()[0] if _front(text, "parent_epic") else "",
                open_todos=len(re.findall(r"^\s*-\s*\[ \]", text, re.M)),
                priority=(_front(text, "priority") or "P3").split()[0][:2],
            )
        )
    return docs


def score(doc: Doc) -> dict[str, int]:
    """Score TRANCHES, not repos -- subject tokens dominate, epic hints and repos: break ties."""
    hay = f"{doc.name} {doc.title}".lower()
    scores: Counter[str] = Counter()
    for repo, tokens in SUBJECT_TOKENS.items():
        for tok in tokens:
            pattern = tok if tok.startswith("^") else re.escape(tok)
            if re.search(pattern, hay):
                scores[REPO_TO_TRANCHE[repo]] += 10
                break
    if doc.parent_epic in EPIC_HINT:
        scores[EPIC_HINT[doc.parent_epic]] += 6
    for repo in doc.repos:
        scores[REPO_TO_TRANCHE[repo]] += 1 if repo in UBIQUITOUS else 4
    return dict(scores)


def _pick_repo(doc: Doc, tranche: str) -> str:
    """Within the winning tranche, name the most specific repo the doc actually cites."""
    hay = f"{doc.name} {doc.title}".lower()
    for repo in TRANCHES[tranche]:
        for tok in SUBJECT_TOKENS[repo]:
            pattern = tok if tok.startswith("^") else re.escape(tok)
            if re.search(pattern, hay):
                return repo
    for repo in doc.repos:
        if REPO_TO_TRANCHE[repo] == tranche and repo not in UBIQUITOUS:
            return repo
    for repo in doc.repos:
        if REPO_TO_TRANCHE[repo] == tranche:
            return repo
    return TRANCHES[tranche][0]


def allocate(docs: list[Doc], spine_text: str) -> None:
    for doc in docs:
        doc.spine = doc.name in spine_text
        doc.excluded = bool(DATA_MOVEMENT.search(doc.name))
        doc.scores = score(doc)
        if doc.name in OVERRIDES:
            doc.tranche = OVERRIDES[doc.name]
            doc.primary_repo = _pick_repo(doc, doc.tranche)
            continue
        if not doc.scores:
            doc.tranche = "T5-readiness-observability-presentations"
        else:
            best = max(doc.scores.values())
            doc.tranche = sorted(t for t, v in doc.scores.items() if v == best)[0]
        doc.primary_repo = _pick_repo(doc, doc.tranche)


def main() -> None:
    docs = load_docs()
    allocate(docs, load_spine_text())

    out = PM_ROOT / "plans" / "audit" / "results" / "code_readiness_allocation_2026_08_19.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated": "2026-08-19",
        "total_docs": len(docs),
        "tranches": {
            t: {
                "repos": TRANCHES[t],
                "docs": [
                    {
                        "path": d.path,
                        "primary_repo": d.primary_repo,
                        "open_todos": d.open_todos,
                        "excluded_data_movement": d.excluded,
                        "spine": d.spine,
                        "priority": d.priority,
                    }
                    for d in sorted(docs, key=lambda x: (not x.spine, x.priority, -x.open_todos, x.path))
                    if d.tranche == t
                ],
            }
            for t in TRANCHES
        },
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    hdr = f"{'tranche':44s} {'docs':>5s} {'open':>6s} {'spine':>6s} {'sp_open':>8s} {'excl':>5s}"
    print(hdr)
    for t in TRANCHES:
        sel = [d for d in docs if d.tranche == t]
        sp = [d for d in sel if d.spine and not d.excluded]
        ex = [d for d in sel if d.excluded]
        print(
            f"{t:44s} {len(sel):5d} {sum(d.open_todos for d in sel):6d} "
            f"{len(sp):6d} {sum(d.open_todos for d in sp):8d} {len(ex):5d}"
        )
    print(f"{'TOTAL':44s} {len(docs):5d} {sum(d.open_todos for d in docs):6d}")
    print(f"\nwrote {out.relative_to(PM_ROOT)}")


if __name__ == "__main__":
    main()
