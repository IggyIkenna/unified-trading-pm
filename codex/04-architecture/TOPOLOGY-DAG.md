---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# System Topology DAG

> **MOVED.** Canonical location: `unified-trading-pm/TOPOLOGY-DAG.md`
>
> The topology DAG is co-located with `workspace-manifest.json` (the machine-readable DAG SSOT) in `unified-trading-pm`.
> When tiers or services change, one PR in one repo updates both the manifest and this diagram. Codex owns architectural
> narrative and contracts, not living diagrams.
>
> **Direct link:** [unified-trading-pm/TOPOLOGY-DAG.md](../../unified-trading-pm/TOPOLOGY-DAG.md)

## What lives where

| Artifact                    | Location                                                      | Purpose                                         |
| --------------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| Human-readable tier diagram | `unified-trading-pm/TOPOLOGY-DAG.md`                          | Full Mermaid flowchart — T0→services→UIs→infra  |
| Code DAG (machine-readable) | `unified-trading-pm/workspace-manifest.json`                  | Tier membership, version pins, merge order      |
| Runtime wiring              | `deployment-service/configs/runtime-topology.yaml`            | Topics, storage, co-location rules per service  |
| Tier architecture narrative | `unified-trading-codex/04-architecture/TIER-ARCHITECTURE.md`  | Why the tiers exist; import rules; enforcement  |
| Protocol injection contract | `unified-trading-codex/04-architecture/PROTOCOL-INJECTION.md` | How libraries resolve live vs batch, GCP vs AWS |
