---
doc_type: codex-ssot
title: System Topology DAG
summary:
  Redirect stub — the system topology DAG moved to unified-trading-pm/TOPOLOGY-DAG.md, co-located with
  workspace-manifest.json (the machine-readable tier DAG SSOT); one PR updates both diagram and manifest.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [topology, ssot, refactor, infrastructure]
related: [/codex/04-architecture/tier-and-import-architecture.md, /codex/04-architecture/runtime-deployment-topology.md]
created: 2026-03-27
authoritative_for: []
referenced_by: [/codex/05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# System Topology DAG

> **MOVED.** Canonical location: `unified-trading-pm/TOPOLOGY-DAG.md`
>
> The topology DAG is co-located with `workspace-manifest.json` (the machine-readable DAG SSOT) in `unified-trading-pm`.
> When tiers or services change, one PR in one repo updates both the manifest and this diagram. Codex owns architectural
> narrative and contracts, not living diagrams.
>
> **Direct link:** [unified-trading-pm/TOPOLOGY-DAG.md](../../unified-trading-pm/TOPOLOGY-DAG.md)

## What lives where

| Artifact                    | Location                                                                   | Purpose                                         |
| --------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------- |
| Human-readable tier diagram | `unified-trading-pm/TOPOLOGY-DAG.md`                                       | Full Mermaid flowchart — T0→services→UIs→infra  |
| Code DAG (machine-readable) | `unified-trading-pm/workspace-manifest.json`                               | Tier membership, version pins, merge order      |
| Runtime wiring              | `deployment-service/configs/runtime-topology.yaml`                         | Topics, storage, co-location rules per service  |
| Tier architecture narrative | `unified-trading-pm/codex/04-architecture/tier-and-import-architecture.md` | Why the tiers exist; import rules; enforcement  |
| Protocol injection contract | `unified-trading-pm/codex/04-architecture/tier-and-import-architecture.md` | How libraries resolve live vs batch, GCP vs AWS |
