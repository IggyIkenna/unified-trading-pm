---
doc_type: plan
title: Walkthrough remediation — session checkpoint and artifact registry
summary: >-
  Pre-compact checkpoint for the 2026-08-21 walkthrough-feedback coordinator session: the published artifact URLs,
  the in-flight sub-agent lane table, the operator's content-additions todo, and the session lessons. Split from
  walkthrough_feedback_remediation_2026_08_21.md (at its 1000-line hard cap). That plan remains the todo SSOT for
  everything except the items tracked here.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [walkthrough, checkpoint, artifacts, client-artefact]
related: [/plans/active/walkthrough_feedback_remediation_2026_08_21.md]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
locked_by:
locked_since:
context_scope: [/plans/active/walkthrough_feedback_remediation_2026_08_21.md]
supersedes:
superseded_by:
depends_on: [walkthrough_feedback_remediation_2026_08_21]
source: Pre-compact checkpoint, coordinator session 2026-08-21.
assigned_role: project_management
effort: low
drift_direction: advance-code
---

# Session checkpoint — 2026-08-21 walkthrough coordinator

**Published artifacts (STABLE URLs — republish the same file path, or pass `url` from another session):**
API Reference → https://claude.ai/code/artifact/ccc4566d-4560-4153-9eaf-fe17100c02ad ·
Integration Guide → https://claude.ai/code/artifact/952680c2-2bda-4735-b298-8e99988896f6

## In-flight lane table (state at checkpoint)

| Item | State | Blocked on |
| --- | --- | --- |
| Rate limits + pagination build (MTDS+IS) + docs rewrite | agent in flight | — |
| DeFi smoke one-block dumps → walkthrough tree badges | agent in flight (test buckets only) | — |
| Walkthrough voice/parity/completion pass | agent in flight | — |
| ControlInstruction wiring 16/16 + FLAT-error + QUOTE note reword | agent in flight | — |
| Signal-leasing verify/build + api-reference §06 onboarding framing | agent in flight | — |
| 12-unresolved-pairs registry fix (chain grains; zero Unclassified) | agent in flight (UAC) | — |
| BLRS recon_excluded ship (QG-green, sentinel 0a6553da) | landing UNCONFIRMED — verify on origin, re-run its recorded quickmerge if absent, flip todo | verify |
| Republish BOTH artifacts once lanes land | not done (same paths/URLs) | lanes above |
| BETMGM/BETWAY historical rows disposition | operator-owned (delete-safety) | operator |
| Kalshi perps TRADING integration (DATA landed instruments-service@2dcee7e149) | operator-owned (venue rights) | venue |

## Todos

- [ ] [DOC] P0. **Operator content additions 2026-08-21 (both docs; light in api-reference, verbose in the
      walkthrough)** — reconciliation prominence; WebSocket rotations; the strategy↔execution POSITION HANDSHAKE;
      inter-service SLAs, disaster recovery, kill-switching, escalation paths incl. the agentic-DevOps workflow;
      CONTINUOUS T+1 BACKFILL keeping the pipeline current; INTRADAY REPLAY (in development — customers replay
      their data intraday; key for exchange-outage recovery; summary + detailed section); the CREDIT /
      reference-price / adjustment-matrix fast path (spec: the delta-proxy issue doc +
      /codex/04-architecture/cross-domain-state-fabric.md — factor-driven approximation from position enabling
      HFT-grade execution, co-located or cross-region engines; local + exchange timestamps); CLOUD-AGNOSTIC
      framework (AWS + GCP today, IONOS integration in progress — cite the IONOS plan; Azure on request; regions
      near the client; cross-cloud same-region streaming into the client's own account to cut streaming cost).
      Verify every claim's code/plan basis before writing.
- [ ] [BACKEND] P2. UAC `PortfolioPnLAttribution.staking_pnl` first-class field — drop the documented carry fold
      (strategy-service@21937bb2cf).
- [ ] [AGENT] P1. Verify BLRS recon_excluded landed on origin; if absent re-run its recorded quickmerge, flip its
      todo in the main plan.
- [ ] [AGENT] P0. Republish both artifacts (same file paths) after the in-flight lanes land; relay landed shas.

## Lessons

safe-doc-push exit 15 = its own stash-replay race, retry ONCE; exit 6 = deterministic, read the printed hook.
`ahead=0` ≠ landed — verify merge-base + origin content (two silent clobbers caught this session). Entity deletion
needs the CROSS-REPO consumer sweep (4f25d5f0 missed four downstream consumers). Operator rulings belong in an
agent's FOUNDING prompt with verify-then-write discipline — mid-flight messages get refused as unverifiable. Seed
claim-ownership baselines against FULL artefacts or the escalation path deletes content (cef0bcfa8e). Condensing a
Progress Log entry that EMBEDS todos trips todo-regression — split history, never delete todo lines.
