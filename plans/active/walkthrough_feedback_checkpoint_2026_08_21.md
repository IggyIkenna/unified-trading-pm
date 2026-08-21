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
| MTDS `_write_prefix_candidates` multi-hyphen venue/chain defect fix (`SOLANA-NATIVE-SOLANA`→`venue=SOLANA-NATIVE/chain=SOLANA/`, root-caused to `mtds@06531f00`) | fix verified locally (target test 10/10; full isolated-worktree suite 11114 passed / 28 skipped / 1 xpass, only 1 unrelated collection error), NOT landed | `market_interface/sports/registry.py:67` raises `ValueError: Unknown sports venues in adapter registry: {'onexbet'}` at import — confirmed live on `origin/live-defi-rollout@1e2baca8` (not a local-tree artifact), blocking the FULL quality-gate for ANY MTDS quickmerge right now; tracked in `issues/sports_bookmaker_roster_classification_2026_08_21.md` (in-flight 6-bookmaker cross-repo removal) — retry once that lands |

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
- [x] [DOC] P0. **Operator content additions 2026-08-21, second tranche (both docs; compact in api-reference,
      fuller in the walkthrough) — About Us / engagement models / research-as-a-service / DART / security /
      DeFi LP** — About Odum Research (main site, who-we-are, tear sheet, the 1yr+ consultancy engagement, and
      the same client's separate bespoke-execution negotiations, DeFi today/CeFi planned); three engagement
      models (Allocate / Signals — cross-linked to the §06(api-ref)/§26(walkthrough) signal-leasing surface as
      its literal integration contract / Run in your ecosystem); research-and-backtest-as-a-service + the
      backtest mirror, citing `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`'s ε=0
      paper↔batch determinism proof; a new DART — Data Analytics Research Terminal section (walkthrough) +
      pointer (api-ref), grounded in `unified-trading-system-ui` + `codex/08-workflows/platform-walkthrough-and-
      demo-context.md` + `prospect-questionnaire-flow.md`; dual-authorization (tiered SMALL=1/MEDIUM=2/LARGE=3
      quorum withdrawal approval, `deployment-api/deployment_api/routes/client_treasury.py`) and custody-adapts-
      to-the-client (pluggable signing: CLOUD_KMS_ENCRYPTED shipped, Copper MPC production for DeFi +
      non-Binance CeFi) folded into walkthrough §15 + api-ref §04; DeFi LP marketing (Uniswap V3 mint/burn
      landed execution-service@0aa709f076 across 5 EVM chains, broader connector roster, "more on demand").
      This is a SEPARATE operator directive from the P0 item above — supersedes nothing there; reconciliation
      prominence / WebSocket rotations / position handshake / SLAs / disaster recovery / T+1 backfill / intraday
      replay / credit-reference-price / cloud-agnostic remain open in that item. Marker check re-verified
      202/247 (unchanged) post-ship. Evidence: unified-trading-pm@40ac124b0f (walkthrough),
      unified-trading-pm@b50711e8b7 (api-reference), both confirmed ancestors of origin/live-defi-rollout.
- [ ] [BACKEND] P2. UAC `PortfolioPnLAttribution.staking_pnl` first-class field — drop the documented carry fold
      (strategy-service@21937bb2cf).
- [ ] [AGENT] P1. Verify BLRS recon_excluded landed on origin; if absent re-run its recorded quickmerge, flip its
      todo in the main plan.
- [ ] [AGENT] P1. WATCH: platform-api-reference.html §01 states the MTDS entitlement seam as landed, but that
      code is still in its ship queue (rate-limits lane carries it). If the MTDS ship fails, correct §01 to
      origin truth; when it lands, the claim is true — verify and close.
- [ ] [DOC] P1. Walkthrough §16–§25/§27/§29: ~25 remaining `st-plan`/pending markers (wizard stages, archetype
      configs, algo-selection specifics) need per-service verification passes to reach zero-pending — the voice
      lane verified only today's landed fixes (its report, 2026-08-21).
- [ ] [AGENT] P0. Republish both artifacts (same file paths) after the in-flight lanes land; relay landed shas.

## Lessons

safe-doc-push exit 15 = its own stash-replay race, retry ONCE; exit 6 = deterministic, read the printed hook.
`ahead=0` ≠ landed — verify merge-base + origin content (two silent clobbers caught this session). Entity deletion
needs the CROSS-REPO consumer sweep (4f25d5f0 missed four downstream consumers). Operator rulings belong in an
agent's FOUNDING prompt with verify-then-write discipline — mid-flight messages get refused as unverifiable. Seed
claim-ownership baselines against FULL artefacts or the escalation path deletes content (cef0bcfa8e). Condensing a
Progress Log entry that EMBEDS todos trips todo-regression — split history, never delete todo lines.

**2026-08-21 (operator directive)**: Deleted walkthrough §14 "Readiness: batch, paper, live" entirely (nav entry +
all 9 cross-refs fixed/repointed to §16); its batch/paper/live same-code-path symmetry content relocated into §16
Integration path. Swept every literal `unverified` outside the DeFi coverage trees to real state (KALSHI-PERP/
POLYMARKET-PERP/PACIFICA-SOLANA → "coming soon (venue-side onboarding)"; 8 Unity child books → confirmed
NO_ADAPTER_YET; BETOPENLY/NOVIG/ONEXBET/PROPHETX → retired per 2026-08-21 ruling, `unified-api-contracts@710db834`);
re-homed the 3 non-DeFi "Unclassified" nodes (BINANCE-FUTURES, BYBIT, DERIBIT + FRED) per
`unified-api-contracts@f79cd936`. Marker check 200/247 (down from 202, deletions lowering it as expected). Evidence:
`unified-trading-pm@6c2b779de8`, confirmed ancestor of origin. Residual (not done here, flagged for the voice/
parity lane): CeFi/Sports header ready/not-ready/unverified tallies (25/39 totals) are the 2026-08-19 measured
snapshot and now read stale against today's per-cell wording/registry changes — needs a fresh `derive_readiness.py`
run, not a doc-text fix; BETMGM/BETWAY nodes still show real historical rows despite being in the same 6-venue
retirement ruling (their disposition is explicitly still operator-pending per this doc's own lane table).
