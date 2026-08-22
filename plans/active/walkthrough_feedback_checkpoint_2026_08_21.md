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
API Reference → https://claude.ai/code/artifact/98ca8a91-7cd1-442c-aed6-532f3df701fc ·
Integration Guide → https://claude.ai/code/artifact/cfb54486-2ce1-4676-be29-443a968ff8d4

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
| MTDS `_write_prefix_candidates` multi-hyphen venue/chain defect fix (`SOLANA-NATIVE-SOLANA`→`venue=SOLANA-NATIVE/chain=SOLANA/`) | LANDED — `market-tick-data-service@b24b0d59`+`2f0a5369` (slot-31 AO worker; real bug was MTDS's own `_defi_partition_parts` naively `.upper()`-ing `parse_defi_venue`'s slug, `parse_defi_venue` itself was never broken — see `/plans/archive/issues/mtds_defi_prefix_parser_multi_hyphen_solana_native_2026_08_21.md`) | — |
| onexbet registry retirement (`market_interface/sports/registry.py` import-time `ValueError: Unknown sports venues in adapter registry: {'onexbet'}`) | LANDED — `market-tick-data-service@e106c1d8`+`b24b0d59` | — |
| MTDS 7-handler `IS_TEST_RUN`-unaware bucket routing (data-correctness, PROD writes during test runs) | LANDED — `market-tick-data-service@473c9c866c` (see `issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md`) | — |

## Todos

- [x] ✅ [DOC] P0. **Operator content additions 2026-08-21 (both docs; light in api-reference, verbose in the
      walkthrough)** — reconciliation prominence; WebSocket rotations; the strategy↔execution POSITION HANDSHAKE;
      inter-service SLAs, disaster recovery, kill-switching, escalation paths incl. the agentic-DevOps workflow;
      CONTINUOUS T+1 BACKFILL keeping the pipeline current; INTRADAY REPLAY (in development — customers replay
      their data intraday; key for exchange-outage recovery; summary + detailed section); the CREDIT /
      reference-price / adjustment-matrix fast path (spec: the delta-proxy issue doc +
      /codex/04-architecture/cross-domain-state-fabric.md — factor-driven approximation from position enabling
      HFT-grade execution, co-located or cross-region engines; local + exchange timestamps); CLOUD-AGNOSTIC
      framework (AWS + GCP today, IONOS integration in progress — cite the IONOS plan; Azure on request; regions
      near the client; cross-cloud same-region streaming into the client's own account to cut streaming cost).
      All 9 items landed as surgical extensions of EXISTING sections (no renumbering, no new Contents-nav entries
      needed — none of the 9 required a new top-level `<section>`): walkthrough §21 (recon_excluded landed —
      verified real on origin via `batch-live-reconciliation-service` commit `1ba1a62`, daily_determinism_stage.py),
      §06 (T+1 `cadence` manifest axis; WS reconnect/STALE-flagging + heartbeat watchdog + key-pool rotation, real
      code in `_ws_window_helpers.py`/`websocket_runner.py`/`thegraph_base_client.py`; intraday replay — in
      development, cites replay-subsystem.md + data_pipeline_completion_2026_08_21.md), §12 (position handshake +
      fast-path repricing — design-stage, cites the delta-proxy issue + cross-domain-state-fabric.md; dual-timestamp
      cites `unified_trading_library/domain_client/validation.py`'s `local_timestamp`/`timestamp` validation), §15
      (agentic-DevOps escalation paragraph — this session is the cited evidence; new SLA/disaster-recovery h3 citing
      the AWS DR-standby runbook; new cloud-agnostic h3 citing `resolve_bucket_name()` + the IONOS migration plan,
      status draft, described as "in progress" per the operator's own phrasing, not overclaimed as shipped), and
      engage §1 (SMA/fund-structure mirror of the api-reference capability-list bullet). API-reference got the LIGHT
      mirror: one new paragraph each in About (SLA/DR/kill-switch/escalation/cloud-agnostic, compact), §03 Market
      data (WS reconnect + T+1 + intraday replay), §04 Instructions (position handshake + fast-path repricing), §05
      Client Reporting (recon_excluded). Marker discipline: zero new `st-`/`ev-` marker tags added (verified by
      class-count diff before writing); `check_artefact_claim_ownership.py` reports 200 open markers post-edit
      (baseline 247, DOWN not up — other lanes' concurrent edits this session also lowered it) and 0
      ownership/owner-ref violations. Tag-balance sanity check clean on the walkthrough (div/details/p/h3/section
      all balanced); the api-reference's pre-existing `<div>` count skew (23, unrelated to any tag I touched — my 4
      edits added `<p>` blocks only, zero `<div>`) predates this change and is out of scope. Evidence: shipped via
      `safe-doc-push.sh` immediately following this edit — see this doc's own commit history for the landing sha.
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
- [x] ✅ [BACKEND] P2. UAC `PortfolioPnLAttribution.staking_pnl` first-class field — drop the documented carry fold
      (strategy-service@21937bb2cf) — **done**. UAC: added `staking_pnl: Decimal = Decimal("0")` to
      `PortfolioPnLAttribution` (12th dimension, docstring updated 11→12), extended
      `test_portfolio_pnl_attribution_round_trip` to cover it. Evidence: `unified-api-contracts@366b74ec08`
      (ancestor-verified on origin/live-defi-rollout). strategy-service: removed `_UAC_FOLD_TARGET` and the
      carry-fold branch in `pnl_attribution_aggregator.py` — `staking_pnl` now passes straight through to its
      own UAC field like every other dimension; updated the 2 staking tests
      (`test_staking_pnl_is_first_class_uac_dimension` — renamed from `..._folded_into_carry`, asserts
      `carry_pnl` stays untouched and `staking_pnl` lands on its own field;
      `test_staking_pnl_defaults_to_zero_when_unspecified` — asserts `staking_pnl == 0`); fixed the stale
      `_UAC_FOLD_TARGET` comment reference in `test_all_11_dimensions_sum`. Both repos' `quality-gates.sh
      --no-fix` green before commit. Evidence: `strategy-service@09d6dfaadd` (ancestor-verified on
      origin/live-defi-rollout).
- [ ] [AGENT] P1. Verify BLRS recon_excluded landed on origin; if absent re-run its recorded quickmerge, flip its
      todo in the main plan.
- [x] ✅ [AGENT] P1. RESOLVED — MTDS entitlement landed at market-tick-data-service@746ad763b (with rate-limiting+pagination in the same commit, 11150 green); §01 claim is now true on origin and was rewritten with real citations (unified-trading-pm@f5c4498582). WATCH closed: platform-api-reference.html §01 states the MTDS entitlement seam as landed, but that
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

## Host contention, 2026-08-22

Shared host reached load 275-344 on 10 cores with 26 concurrent `quality-gates.sh` processes, 8 quickmerges and 13
pytest runs, stalling every lane's gate. Investigated per the runaway-process rule: PID 36696 was orphaned
(reparented to init), 70 minutes old, running from a dead session's `/tmp/claude-*-cwd` isolated worktree, and was
still spawning fresh sub-gates (two started 8 minutes before discovery) whose results no live parent could ever
read. Terminated that tree only (36696, 36699, 73190, 73715, SIGTERM, all confirmed gone). Every other gate process
had a live parent and was left untouched per the never-bulk-kill-a-peer rule. Load did not materially drop, which
confirms the remaining pressure is legitimate concurrent fleet work, not orphans.

Lesson for future multi-lane pushes: an isolated-worktree gate whose parent agent dies keeps running and can keep
spawning, so a session that loses agents (network outage, crash) should sweep for `ppid=1` gate trees rather than
assume its work stopped with it.

## Coverage-quality push, scoped 2026-08-22 (operator ask: get unattributed, sports and unverified down)

- [ ] [BACKEND] P1. **Unattributed venues, re-measure then close the remainder.** Hypothesis to TEST first, not
      assume: the 24 manifest-unattributed tokens substantially overlap the 24 declared-but-unbucketed venues the
      SSOT fix just bucketed (23 DeFi venues bucketed, ALCHEMY-ONCHAIN re-homed to DATA_SOURCE_CAPABILITIES).
      After that lands, re-run the coverage dump and DIFF the still-unattributed set against the fix. Whatever
      remains is a manifest-side naming mismatch (pre-canonical bare-protocol tokens with no chain suffix), which
      needs a manifest attribution pass keyed on the canonical venue vocabulary, not another registry edit. Close
      to zero, then delete the Unattributed node from the client trees.
- [ ] [BACKEND] P1. **Sports coverage, honest root cause.** The sports tree is dominated by the eight Unity
      central-wallet child books (3ET, BROKER5, CROWN, SBO, SHARPBET, VX, BETDEX, IBC), which carry
      NO_ADAPTER_YET in venue_adapter_keys.py. This is OUR missing connector work, NOT venue-side onboarding, so
      the "coming soon (venue-side)" wording must not be used for them. Either build the Unity central-wallet
      adapter path (one integration unlocks all eight) or state them as covered by the Unity integration when it
      lands. Separately, extend the smoke-dump proof to the odds-API books that DO have adapters so their cells
      show proven data.
- [ ] [BACKEND] P1. **Unverified badges, extend the proven smoke-dump method.** The DeFi batch proved the harness
      works (30 venues proven via one-block dumps to -test- buckets, see defi_venue_smoke_batch1_2026_08_20.md).
      Extend the same harness to the remaining unverified CeFi, TradFi and prediction venues, and to sports per
      the item above. Blocked-on-credentials venues get the credential ask, never a silent unverified. Prereq to
      re-run cleanly: the IS_TEST_RUN bucket-routing fix (landed, market-tick-data-service@473c9c866c) and the
      -test- manifest-write gap tracked in the ws-resilience C3 issue.
- [ ] [DOC] P2. Once the three above land, refresh both client artefacts: coverage trees regenerated from the new
      measurement, Unattributed node deleted, sports stated accurately, and the header ready/not-ready tallies
      re-derived (they are still the 2026-08-19 snapshot and cannot be hand-edited).
