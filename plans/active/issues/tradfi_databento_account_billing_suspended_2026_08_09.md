---
doc_type: issue
title: TradFi Databento account suspended by vendor for non-payment — all Databento fetches fail account-wide
summary: >-
  Operator report 2026-08-09: Databento has suspended our account because the bill was not paid — a recurring
  condition (resolved 2026-08-10, re-suspended 2026-08-12, confirmed still live as of 2026-08-15, see Progress Log).
  **CORRECTED 2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a)**: this doc's original framing below ("FULL
  account-level outage... EVERY Databento request... will fail") is broader than the doc's own fresher 2026-08-15
  live-verified finding — the actual blast radius is dataset-scoped, not account-wide: in the same run, CME's
  GLBX.MDP3 dataset returned 402 while ICE/NASDAQ/NYSE/FX all wrote successfully. Treat the narrower, dated finding in
  the Progress Log as current; the paragraph below is the ORIGINAL 2026-08-09 report, kept for history, not the
  current-state summary. With CME/GLBX.MDP3 specifically blocked, every open TradFi MTDS/backfill todo that depends on
  a live CME/GLBX.MDP3 Databento fetch is non-dispatchable until this resolves; other venues are unaffected. Original
  2026-08-09 report (kept for history): "This is a FULL account-level outage — broader than the existing 3-dataset
  billing-safety allowlist (`/codex/02-data/tradfi-databento-sourcing-ssot.md`)... With the account itself suspended,
  EVERY Databento request (batch backfill AND the live `databento_tradfi_ws` connector) will fail regardless of
  allowlist compliance, until the operator pays the bill and the vendor restores the account." Features/ML work on
  already-captured data is UNAFFECTED and should proceed.
status: blocked
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, databento, billing, backfill, mtds, operator-decision, outage]
related:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
  ]
created: 2026-08-09
author: claude-code (interactive session, operator-reported 2026-08-09)
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    'Operator chat instruction, 2026-08-09: "tradfi is currently billing blocked because databento have stopped our
    account because we didn''t pay .. every issue and plan involving a databento backfill needs to be put on hold for
    now because it won''t work anyway. anything which is not mtds or is backfill related can proceed including features
    and ml because we do have data for those."',
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    instruments-service/instruments_service/reference_data/adapters/tradfi/databento/adapter.py,
    market-tick-data-service/market_tick_data_service/live/connectors/databento_tradfi_ws.py,
  ]
drift_direction: advance-code
depends_on: []
---

# TradFi Databento account suspended by vendor for non-payment

## What's actually different from the existing billing-safety SSOT

`/codex/02-data/tradfi-databento-sourcing-ssot.md` documents a **fail-closed allowlist** that stops us from being billed
for out-of-subscription `(dataset, schema, start)` cells on an otherwise-live, paid-up subscription. That mechanism is
unrelated to this issue: this is the vendor suspending the **account itself** for non-payment. Every Databento call —
allowlisted or not — will now fail (auth/entitlement rejection at the account level), including:

- The MTDS batch OHLCV/tick backfill launchers (`--source databento`).
- The instruments-service reference-data `definition` schema fetch
  (`instruments_service/reference_data/adapters/tradfi/databento/adapter.py`).
- The live `databento_tradfi_ws` connector (same account, same credential) — **not explicitly called out by the operator
  but almost certainly affected too**; worth a live-side verification pass once someone is checking on this, it is not
  itself the thing being paused here.

## What is paused

Any OPEN (`- [ ]`) todo in a TradFi-tagged active plan/issue that requires a **new fetch from Databento** — MTDS
backfill launches, instruments-service databento-sourced instrument-definition backfills, VM launches whose payload
calls the Databento adapter. These are gated `BLOCKED-OPERATOR-DECISION` (task_template.md's non-dispatchable
ingestion-gate family) pointing at this doc, so the AO backlog stops offering them to workers. Re-check
`unified-api-contracts/registry/databento_subscription_allowlist.py`'s live behavior once the operator confirms the
account is restored, then lift the gates doc-by-doc.

## What is NOT paused (operator explicit)

- **Features / ML** — feature computation and model training/inference read already-captured data; they do not call
  Databento. Proceed normally.
- Any non-TradFi asset_group work (cefi/defi/sports/prediction) — Databento is TradFi-only, unaffected.
- TradFi audit/reconciliation/read-only todos that don't fetch new data (e.g. manifest/catalog audits, canonical-path
  reconciliation, docs work) — these read what's already captured, not blocked.
- TradFi ML/strategy/backtest work that consumes already-captured TradFi data.

## Resolution path

Operator pays the outstanding Databento bill and the vendor restores account access. Until then this is a
`BLOCKED-OPERATOR-DECISION` (finding U(i) class — a business/spend judgment with no data-derivable answer). Once
restored: live-verify with a cheap real call (e.g. `definition` schema fetch for a known instrument) before resuming any
bulk backfill, then flip each gated todo's marker back to dispatchable in the same edit that confirms it works (per the
"retag the moment the block resolves" hard rule).

## Todos

- [ ] [BLOCKED-UPSTREAM-OUTAGE] P0. **Databento CME billing — operator paying.** **RULED 2026-08-21 (operator decision
      D5, `.ao_checkpoints/issues_corpus_completion_2026_08_21/triage_decisions.json`)**: operator pays the
      outstanding Databento CME (GLBX.MDP3) invoice directly — retagged from `[OPERATOR]` (an open decision) to
      `BLOCKED-UPSTREAM-OUTAGE` (the decision is made; only the vendor-side payment/restoration is outstanding). No
      further worker action on this todo until the operator confirms payment — then re-verify per the method below
      before lifting any dependent gate. **RECURRED 2026-08-12 — pay the outstanding Databento invoice again; the
      account went unpaid a second time after the 2026-08-10 restoration below.** Evidence: `mtds-live-tradfi-cme-trades-20260809-163443`'s
      `run.log` records `gateway error code=api_key_deactivated err='User or API key deactivated'` at
      2026-08-12T00:03:56.894Z, immediately followed by a reconnect attempt that also failed CRAM auth:
      `CRAM authentication error: Unable to submit the request because there is an unpaid invoice.` The process itself
      never crashed (heartbeats/RESOURCE_SAMPLE lines continued every ~30s through at least 2026-08-14), so this is
      invisible to any liveness/heartbeat check — a zombie producer: process alive, feed permanently dead, zero
      reconnect attempts in the ~50h between the failure and discovery. Manifest confirms the boundary exactly: CME
      trades captured cleanly 2026-08-09..08-11, then 100% `empty_confirmed`/`SOURCE_RETURNED_ZERO` from 2026-08-12
      onward. Same resolution path as the first occurrence — pay the invoice, then re-verify with
      `DatabentoBaseClient.warmup()` / `metadata.list_datasets()` per the 2026-08-10 method below, but this time ALSO
      explicitly re-verify the LIVE WS session specifically (the 2026-08-10 verification only checked the batch/
      historical client — never independently confirmed for live, per that entry's own caveat — and it was in fact the
      live side that silently died the second time).
- [ ] [CODE] P2. **Flag for the market-tick-data-service connector owner (out of scope for this doc's tradfi/VM-launcher
      owner): the Databento live WS connector should retry/backoff on a dead session instead of giving up after one
      failed reconnect, and/or a VM-level watchdog should distinguish "process alive" from "feed alive" so this class of
      failure pages instead of running silently for 2+ days.** File:
      `market_tick_data_service/live/connectors/ databento_tradfi_ws.py` (not touched by this session — out of ownership
      scope; diagnosed 2026-08-14 during `cross_ag_live_capture_parity_2026_08_14.md` Finding C).
- [x] ✅ [OPERATOR] P0. **Pay the outstanding Databento bill so the vendor restores account access.** **CONFIRMED
      RESOLVED 2026-08-10** — operator reported believing the block had cleared ("check live i think we found that
      databento wasnt blocked anymore"); independently live-verified rather than trusted at face value. Ran the
      codebase's own account-level connectivity check (`DatabentoBaseClient.warmup()`,
      `market-tick-data-service/market_tick_data_service/market_interface/clients/databento_base_client.py`) — resolved
      the API key via the existing Secret Manager path (`get_secret_client`, secret `databento-api-key`, no key
      printed/hardcoded), then called `client.metadata.list_datasets()` (the same **unscoped, account-level**
      lightweight call the client's own `_AUTH_ERROR_PATTERNS` warmup logic uses to detect a locked/suspended account).
      Result: **succeeded — 29 datasets returned, no 401/403/locked/suspended error.** This is broader evidence than the
      2026-08-09 narrow carve-out below (which covered only the MVP-of-MVP in-scope item list) — an unscoped
      `list_datasets()` success indicates the ACCOUNT itself is active, not just specific in-scope datasets.
      Corroborates the same conclusion the 2026-08-09 scope-ruling doc reached (`metadata.list_datasets` + a real
      `ES.FUT ohlcv-1m` pull, both succeeded that day too). Gated every open TradFi Databento-fetch todo across the
      corpus (see "Plans/issues gated by this doc" below for the sweep — re-swept same session, see Progress Log). Repo
      checked: market-tick-data-service (this repo, `unified-trading-pm`, was the only one editable;
      instruments-service's parallel `databento/adapter.py` reference-data path and the live `databento_tradfi_ws`
      connector were NOT independently re-verified this pass — both share the same account/credential as the MTDS
      historical client just proven live, so account-level restoration should cover them too, but flagging as not
      directly re-tested).
- [ ] [DOCS] P2. **Archive this doc via the 6-step ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) once the corpus-wide referrer-path sweep
      is done.** Deliberately NOT done in the same edit as the resolution above — a `git grep` found 9 referrer files
      citing this doc's path (`data_completion_tradfi_2026_07_15.md`,
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
      `/plans/archive/2026_08/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`,
      `issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`,
      `issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`,
      `issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`,
      `tradfi_phase_d_terminal_gate_2026_07_24.md`, `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md`,
      `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`) — several with dated Progress Log history entries (e.g. the
      mdps doc's DP-FETCH-009 alert diagnosis chain) that need a careful per-doc read before repointing their path
      citations to `/plans/archive/2026_08/issues/...`, not a blind sed. Done when: all 9 referrers' path citations
      updated (or confirmed already historical/no-op), then the standard `git mv` + banner + codex- align steps. Kept
      this doc `status: resolved` but un-archived in the interim per this workspace's own `archive_exempt`-bridge
      precedent (`RULED 2026-08-09` in the archival-discipline SSOT) — the doc also still functions as the standing
      awareness/runbook record for this incident class until the sweep lands.
- [x] ✅ [OPERATOR] P1. **RESOLVED 2026-08-21 (operator ruling D5, recorded in
      `/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md` item 7) — option (A): paused
      the fleet wave mechanism at its actual source + shipped a live billing-probe gate as defense-in-depth.** See
      the dated Progress Log entry below in THIS doc for full evidence (mechanism found, pause verified, VMs
      stopped, code shipped). **The CURRENT
      `tradfi-bf-cme-ohlcv-1m-` fleet-wide relaunch wave (~29 instances) is confirmed
      hitting the same billing block.** NEW 2026-08-17 (slot 16, data_pipeline_failure escalation agt-4e1517) —
      launched ~09:01-09:06Z today across
      `btc`/`es`/`eth`/`g01-6a-6l`/`g02-6m-cl`/`g03-ct-hg`/`mbt`/`met`/`nq` groups, years 2020-2026) is confirmed
      hitting this SAME billing block from each shard's very first CME date.** Spot-checked
      `tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-090227` directly via GCS SDK read:
      `DatabentoAdapter: GLBX.MDP3 failed [402]: 402 account_delinquent_invoice` on its first three attempted dates
      (2020-01-02/-03/-07), zero `PROGRESS.json` checkpoint written. Every VM in this wave shares `VENUE=CME`, so
      every one is equally exposed — not an isolated straggler like the entries above, the WHOLE fresh wave is
      burning SPOT compute with zero chance of success right now. Each will very likely self-terminate via its own
      in-VM stall watchdog (~3900s/65min no-progress threshold, the same mechanism the 2026-08-17 entries above
      confirmed) around ~10:06-10:11Z today, producing a fresh DP-VM-001 alert storm across up to ~29 VMs. Decide:
      (A) pause the `tradfi-bf-cme-ohlcv-1m-` launcher family's scheduler/wave mechanism until this billing block
      resolves (avoids the coming alert storm + SPOT burn, at the cost of not auto-resuming the instant billing
      clears), or (B) accept it as a known, safely self-resolving condition (no data corruption — every failure
      writes an honest partial manifest — just wasted SPOT compute + alert noise) and let the existing
      RB-INFRA-RELAUNCH `≤2/(vm-prefix,day)` bound keep absorbing it. Not independently verified: the identity/
      trigger of whatever launched this wave (looks scheduled/automated, not this session's doing) or whether it
      already has its own stop condition — flagging for the operator rather than guessing.

- [ ] [OPERATOR] P1. **NEW 2026-08-21 — the actual `tradfi-bf-cme-ohlcv-1m-` fleet-wide relaunch mechanism found this
      session (a crontab entry directly on the AO orchestrator VM's `ubuntu` user running `scripts/wave_launcher.py`
      every 3h, `WAVE_MAX_CONCURRENT=20`) predates this session, is completely undocumented (no install script /
      Terraform resource / referring doc anywhere in the corpus names it — grepped), and its origin is unknown.**
      Paused (commented out, not deleted — see Progress Log) rather than removed, so it stays reversible and
      inspectable. Decide: (a) formalize it into Terraform (replacing or alongside the existing but 2-months-dormant
      `uts-prod-tradfi-wave-launcher-cron` Cloud Scheduler + Cloud Run Job pair, which this crontab appears to have
      silently superseded without ever being registered anywhere), or (b) delete it permanently once the Terraform
      Cloud Scheduler job is confirmed to still work end-to-end (untested since 2026-06-25) and re-enable that
      instead. Either way, re-enabling ANYTHING should wait until Databento CME billing is confirmed OK (this doc's
      other P0 todo) — the shipped `cme_billing_probe_ok()` gate (deployment-service@3367cfea) now protects either
      path.
- [x] ✅ [CODE] P2. **Databento live WS auth/billing failure is recorded as `empty_confirmed[SOURCE_RETURNED_ZERO]` (false honest-absence) instead of `record_failed` — surface the gateway auth failure into the runner's empty-window classification.** Verified live 2026-08-20 (slot 31, agt-db01a4): `mtds-live-tradfi-cme-trades-20260809-163443` recorded 40 `empty_confirmed[SOURCE_RETURNED_ZERO]` rows across 08-12..08-20 for a stream whose Databento key was deactivated 2026-08-12T00:03:56Z (unpaid invoice), because `market_tick_data_service/live/websocket_runner.py::_record_empty_window` routes to `record_failed` only on `_in_connectivity_gap()` (watchdog GAP) — a state `market_tick_data_service/live/connectors/databento_tradfi_ws.py` never sets for an auth failure, so every window is stamped honest-absence. Mirror the batch path (`databento_adapter.py` classifies `402/DATABENTO_PAYMENT_REQUIRED` as a venue error): surface credential-failure state from the connector so the runner writes `attempted_failed[CLASSIFIED_VENUE_ERROR]` per `/codex/02-data/honest-absence-downstream-handling.md` §401-rule. Distinct from the retry/backoff + feed-alive-watchdog todo above. Evidence: market-tick-data-service@6836a68eb5484e7d424405d557921cda30de47a4; quality-gates=PASS (11,071 passed, 82.07% coverage).

## Plans/issues gated by this doc (sweep log)

**RESOLVED 2026-08-10 — all 4 docs re-swept, all 7 todos unblocked.** See the Progress Log entry below for what changed
in each. This section is kept as the historical sweep record (method + original gate rationale); it is no longer a live
blocking list.

**Method**: swept every active plan/issue whose `asset_group` frontmatter includes `tradfi` (61 docs), narrowed to the
15 carrying an open (`- [ ]`) todo matching backfill/databento/mtds/ohlcv/launch/download/capture/fetch, then read each
match's surrounding context to judge whether it's a genuine new-Databento-fetch dependency vs. a manifest repair,
audit/read-only task, features/ML computation, or a non-Databento source (e.g. ForexFactory econ calendar, Yahoo VIX,
Massive-historical). 7 todos across 4 docs were genuine and gated `BLOCKED-OPERATOR-DECISION` (original 2026-08-09
sweep, historical):

- `/plans/active/data_completion_tradfi_2026_07_15.md` — the `build_instrument_catalogue.py` scheduler todo (gated on
  Databento IS reference-capture restore) and the IS instrument-capture `--source databento` replacement-path todo.
- `/plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — "Launch the ES_OPT backfill" and its dependent
  post-launch manifest-verify todo.
- `/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md` — the "MVP backfill readiness gate" (tradfi MVP backfills,
  SPOT VMs, single Databento IP) and its dependent post-backfill reconciliation-run checkpoint.
- `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` — the combined ES_OPT launch +
  manifest-verify todo (same task as the instruments_tradfi_g1_g5 pair above, tracked here too since batch6 is the live
  AO-dispatch surface; its own Progress Log recorded a watcher session actively polling the singleton lock and launching
  as of 2026-08-07T~04:46Z — if that watcher is still running, it will now fail every attempt until billing is
  restored). **RETAGGED 2026-08-09 (was stale — flagged by two separate sessions as needing this fix, now applied): this
  specific gate is LIFTED.** `/plans/archive/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (same day,
  same author) recorded a live Databento API verification (`metadata.list_datasets` + a real `ES.FUT ohlcv-1m` pull,
  both succeeded) that lifted this gate specifically for its in-scope list — which includes S&P 500 futures+options.
  Live evidence since: 2 real `tradfi-bf-es-opt-*` launches on 2026-08-09 both fetched genuine Databento data (confirmed
  via manifest — 1,407/1,728 distinct trading dates already carry real OHLCV bars, see
  `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`). The account-level suspension this
  doc as a whole describes may still be real for OUT-of-scope Databento calls; this retag narrowly resolves only the
  batch6/ES_OPT entry per the scope-ruling doc's own explicit carve-out — not a claim that the broader billing issue is
  resolved.

**Explicitly left ungated** (read, judged not a live-fetch dependency):
`tradfi_backfill_throughput_followups_2026_07_24.md` (OOM-remediation umbrella pointer — its one real open leg is a
log-audit, not a fetch), `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` (ForexFactory, not
Databento), `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` (re-measure ratio on already-captured
data), `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` (features-VM relaunch, reads existing data),
`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md` (manifest-row repair script), `estate_orphan_assessment_2026_07_21.md`
(manifest reclassification script, cross-cutting not tradfi-specific), `data_completion_tradfi_2026_07_15.md`'s
ohlcv_15m/24h conversion todo (MDPS aggregation of already-captured 1s/1m data),
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (manifest reclassification, CEFI/TradFi),
`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s two open todos (an audit-pointer and a manifest-only
re-stamp/backfill of already-captured rows), `mdps_features_deadcode_consolidation_2026_07_20.md` (prediction/sports/
generic launcher bugs, none tradfi-specific), and `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` /
`..._batch8_2026_08_08.md` / the `_finalize` plans (all open todos there are manifest reconciliation, investigation, or
archival — no live Databento dependency).

## Progress Log

- **2026-08-17 (slot 4, data_pipeline_failure escalation agt-990205)**: Fresh independent reconfirmation — DP-VM-001
  on `tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-090227` (+ same-day siblings `...btc-2021-...-090428` and
  `...btc-2022-...-090626`) all show the `DatabentoAdapter: GLBX.MDP3 failed [402]: 402 account_delinquent_invoice`
  signature in `run.log` (125-240 occurrences per VM), stalling forward progress until the in-VM watchdog killed
  them (`exit_code=137`). Still `status: blocked` — no relaunch attempted per RB-INFRA-RELAUNCH. Full writeup in
  `dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`.
- **2026-08-10 (prose-findings formalization sweep)**: converted 1 prose finding into 1 formal todo (0 already
  resolved). The doc's own "Resolution path" prose ("Operator pays the outstanding Databento bill...") had never been
  formalized as a `- [ ]` checkbox despite `status: blocked`/`priority: P0` and being escalated in prose elsewhere
  (`tradfi_satellite_ao_dispatch_batch11_2026_08_10.md`'s Deferred section) — added an `[OPERATOR] P0` todo under a new
  `## Todos` section.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up)**: KEEP-NA, valid — the sole open todo is paying an
  outstanding vendor bill, an explicit `[OPERATOR]`-tagged business/spend decision with no data-derivable answer
  (`status: blocked`, `BLOCKED-OPERATOR-DECISION` per the doc's own text). Doc stays NA.
- **2026-08-10 (live-verification session, operator prompted "check live i think we found that databento wasnt blocked
  anymore") — CONFIRMED RESOLVED, account access restored.** Did not trust the operator's recollection at face value —
  independently live-verified via the existing `market-tick-data-service` `DatabentoBaseClient.warmup()` connectivity
  check (no new fetch code written): API key resolved from Secret Manager (`databento-api-key`, via `get_secret_client`
  — never printed), then `client.metadata.list_datasets()` (an unscoped, account-level call) succeeded — 29 datasets
  returned, no auth/locked/suspended error. This is stronger evidence than the 2026-08-09 scope-ruling doc's narrower
  in-scope-only verification, since `list_datasets()` is not scoped to any particular dataset/subscription. Also checked
  for any other corpus record of resolution: `git log --all --since=2026-08-09 -- '*databento*'` showed nothing new
  beyond the already-known 2026-08-09 narrow retag; no other doc had recorded a broader resolution before this session.
  Flipped the `[OPERATOR] P0` "Pay the bill" todo to `[x]` with this evidence. Re-swept the "7-todo/4-doc gate list":
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` and `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` were
  already retagged UNBLOCKED on 2026-08-09 (no change needed). Lifted the remaining databento-specific citations in
  `data_completion_tradfi_2026_07_15.md` (the catalogue-scheduler todo + the `--source databento` replacement-path todo,
  plus 2 consistency-citation notes on dependent items) and `tradfi_phase_d_terminal_gate_2026_07_24.md` (the MVP
  backfill readiness gate + its dependent reconciliation checkpoint — databento portion lifted, but the readiness gate's
  SEPARATE chain-bundle-sampler blocker is unrelated and stays open, not touched). Added a `[DOCS] P2` todo to archive
  this doc via the 6-step ritual once a 9-file corpus-wide referrer-path sweep is done (deliberately not attempted in
  this same pass — several referrers carry dated Progress Log history needing a careful per-doc read before repointing,
  not a blind path swap). Doc frontmatter `status` flipped `blocked` → `open` (NOT `resolved` —
  `resolved`/`false-positive`/`superseded` are `check_terminal_status_archived.py`'s TERMINAL set and would force
  archival in this same commit; `open` accurately reflects "underlying block cleared, doc still carries a real open
  todo" without tripping that gate). Stays in `plans/active/issues/` per the new todo above.

- **2026-08-14 (cross_ag_live_capture_parity_2026_08_14.md Finding C, tradfi CME live-shard diagnosis) — RECURRED, the
  2026-08-10 resolution above did NOT hold for the live side.** Diagnosing why
  `mtds-live-tradfi-cme-trades-20260809- 163443` (RUNNING since 2026-08-09) produced only 28 captured rows before going
  silent found the account was suspended again: `run.log` shows `gateway error code=api_key_deactivated` +
  `CRAM authentication error: ... unpaid invoice` at 2026-08-12T00:03:57Z, one failed reconnect attempt, then nothing —
  the process kept heartbeating for the following ~50h with a permanently dead feed, invisible to any process-liveness
  check. This directly confirms the 2026-08-10 entry's own stated caveat ("the live `databento_tradfi_ws` connector...
  not independently re-verified this pass") — the live side was the one that actually broke. Frontmatter `status`
  flipped back `open` → `blocked` (a real operator-gated blocker exists again) and the "pay the bill" todo un-resolved
  as a NEW `[ ]` P0 (kept the original `[x]` entry as history rather than rewriting it — this is a recurrence, not a
  correction of the first fix). Separately flagged (not fixed — out of this session's VM-launcher/shard-config ownership
  scope) that the connector has no reconnect/backoff on a dead live session, which is why this ran silent for 2 days;
  that's a `market-tick-data-service` connector-owner fix, tracked as its own `[CODE] P2` todo above. Did NOT
  restart/relaunch the VM — restarting a producer whose feed is dead on the vendor side would not fix anything and was
  correctly identified as pointless per the diagnose-before-restart principle; the VM stays as-is pending the invoice
  being paid, at which point relaunching is the AO-eligible follow-up
  (`bash deployment-service/scripts/vm/launch-mtds- live.sh --asset-group tradfi --shard-spec tradfi:CME:trades --instrument-ids <ids>`
  per that launcher's usage, or simply confirming the existing VM's connector auto-recovers once the account is live
  again — untested either way).

- **2026-08-15 (data_pipeline_failure escalation agt-f752fb, DP-VM-001 on
  `tradfi-bf-cme-ohlcv-1m-btc-2023-20260815-000731`, BATCH-side confirmation) — still `blocked`, batch backfill hits the
  SAME unpaid-invoice wall.** Dispatched to relaunch a VM the exit-code fleet monitor found terminated `exit_code=137`;
  live-read the archived `run.log`/`EXIT_STATUS` via `_gcs.read_terminal_exit_code`/`run_log_shows_stall_text` BEFORE
  relaunching and confirmed the kill was genuinely stall-induced (in-guest no-progress watchdog, `stalled_for=3931s`
  threshold=3900s, `mem_pct` only 52.5% — not OOM), so per DP-VM-001's own routing ("OOM: auto-recover · non-OOM: page")
  and `RelaunchBackfillVm`'s OOM-only remedy (resize-up — wrong fix for a hang), this was not an automated-OOM-actuator
  case; no prior relaunch/paged marker existed and `PROGRESS.json` showed a genuine monotonic checkpoint
  (`last_completed_date=2023-01-28`), so manually relaunched via
  `launch-tradfi-bf-cme-ohlcv-1m.sh --only-root BTC --year 2023 --env prod` (checkpoint-resume, no resize). **It resumed
  correctly past the prior checkpoint (started at 2023-02-08) — but every request then failed immediately**:
  `WARNING DatabentoAdapter: GLBX.MDP3/ohlcv_1m failed [402]: 402 account_delinquent_invoice ... unpaid invoice`
  (2026-08-15T04:39:56Z) — this doc's `[ ]` P0 "pay the invoice again" recurrence is STILL live today, 3 days after the
  2026-08-12 detection. Strongly suggests the ORIGINAL VM's stall was this same root cause (402s fast-failing in a loop
  that never satisfies the no-progress watchdog). Did NOT leave the relaunched VM running once the 402 confirmed the
  block — deleted it
  (`gcloud compute instances delete tradfi-bf-cme-ohlcv-1m-btc-2023-20260815-043021 --zone=asia-northeast1-c`) to avoid
  burning further SPOT compute on a call that cannot succeed; confirmed no other `tradfi-bf-*` VMs were live at the
  time. Did NOT add the launcher to `DEFAULT_WORKER_STALL_SAFE_LAUNCHERS` despite the clean resume evidence — vetting it
  under a billing-outage run would conflate "safely idempotent" with "nothing downstream succeeded either way";
  re-attempt once the invoice todo is next confirmed paid. No code changed; this doc's existing `[ ]` P0 invoice todo
  already covers the fix. Filed no new issue doc (this one already tracks the live recurrence). Paged the operator via
  `/blocked` per the escalation contract — same pre-existing `[OPERATOR]`-gated action, not a new decision.

- **2026-08-15 (slot-14, backend_engineer, `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "run the by_date
  re-feed chain" todo) — STILL `blocked`, IS reference-data adapter (not just MTDS OHLCV) also hits the same wall, AND
  the failure is narrower than this doc's "full account-level outage" framing.** Launched
  `instr-backfill-tradfi-20260815` (`launch-instruments-backfill-vm.sh --asset-group TRADFI`, the exact re-feed path
  this doc's "What's actually different" section names —
  `instruments_service/reference_data/adapters/tradfi/databento/adapter.py`). Within the first ~3 minutes (2020-01-01
  through 2020-01-03 shards) CME hit `Databento SDK error dataset GLBX.MDP3 symbols=78: 402 account_delinquent_invoice`
  on every single date, retry-exhausted both attempts every time (10s then 30s backoff) — same signature as the
  04:39:56Z BATCH-side confirmation above, now independently reconfirmed ~5h later the same day on the IS reference-data
  path. **Narrower finding, worth flagging against this doc's current "FULL account-level outage... EVERY Databento
  request... will fail" characterization**: in the same shards, the OTHER 4 venues (ICE/NASDAQ/NYSE/FX) wrote
  successfully — each date logged `4/5 venues written (80% complete), 1 missing — ['CME']`, not a 0/5 account-wide
  failure. Only CME's `GLBX.MDP3` dataset returned 402; no other venue's fetch in this run hit a
  402/delinquent/suspended error. Not re-verified whether NASDAQ/NYSE actually route through Databento for this call
  (router.py's own docstring says they do) or a different source — flagging the discrepancy rather than guessing; if
  true this is dataset/subscription-scoped (GLBX.MDP3 specifically unpaid), not account-wide, which would change the
  resolution's blast radius but not its `[OPERATOR]`-gated nature. **Did NOT let the VM keep running** — deleted it
  (`gcloud compute instances delete instr-backfill-tradfi-20260815 --zone=asia-northeast1-c`) once the 02-day pattern
  confirmed CME would fail identically across the full 2020-2026 requested range (~2400 days × ~40s of guaranteed-futile
  CME retry overhead each, on top of SPOT compute cost for zero CME progress) — mirrors the 04:39:56Z entry's same
  delete-on-confirmed-402 precedent. The re-feed todo's own done-when ("write-rate recovers toward the historical
  16-18K/day range") cannot be satisfied while CME/GLBX.MDP3 — TradFi's largest single instrument-type population
  (options/futures) per this same plan family's own G1 enumerate counts — stays blocked; marking that todo
  `NOT ACTIONABLE` in its batch plan rather than partially running it. No code changed; this doc's existing `[ ]` P0
  invoice todo already covers the fix. Did not re-page the operator — already paged same day (04:39:56Z entry above),
  this is corroboration not a new event.

- **2026-08-17 (slot 4, data_pipeline_failure escalation agt-5af8eb, DP-VM-001 on
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209`) — STILL `blocked`, reconfirmed ~19h after the 2026-08-15
  entries above, same signature.** A fleet monitor flagged this VM's `exit_code=137` as a generic stall; this
  worker pulled `run.log` (unlike the two same-day DP-VM-001 sibling docs for the same shard, which did not) and
  found `DatabentoAdapter: GLBX.MDP3/ohlcv_1s failed [402]: 402 account_delinquent_invoice` on `2020-06-10` at
  `2026-08-16T23:11:13Z`, after the shard had progressed cleanly through `2020-06-09` — the same CME/`GLBX.MDP3`
  dataset-scoped signature as the 2026-08-15 entries, not a different failure mode. The billing block stopped
  forward progress; the in-VM stall watchdog fired 3903s later and the VM self-terminated. Did not relaunch (would
  blindly repeat the same failure). Full root-cause writeup + correction of the sibling docs' wrong "poison
  instrument" hypothesis:
  `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`.
  Did not re-page the operator — this doc's existing P0 `[OPERATOR]` invoice todo already covers the ask; this is
  corroboration, not a new event. No code changed.
- **2026-08-17 (slot 13, data_pipeline_failure escalation agt-d350cd, DP-LIVE-004 on
  `mtds-live-tradfi-cme-trades-20260809-163443`) -- STILL `blocked`, same root cause, LIVE-side reconfirmation.**
  `dp-fleet-monitor`'s `live_stream_watcher.check_live_capture_productivity` paged: the VM is `RUNNING` and actively
  attempting (`last attempt 0.0h ago`) but CME trades last `captured` 5.3d ago (staleness budget 3d). This is the
  exact live producer named in the 2026-08-14 entry above, and the same failure class as the 2026-08-15/08-16
  BATCH-side 402s already logged in this doc -- the VM's connector went silent after the last confirmed
  `api_key_deactivated`/`unpaid invoice` CRAM auth failure and has zero reconnect attempts since (the pre-existing
  `[CODE] P2` todo above already tracks the connector's missing retry/backoff on a dead session as the reason this is
  invisible to process-liveness checks). Did not attempt a code fix -- this is the SAME `BLOCKED-OPERATOR-DECISION`
  the doc's open `[OPERATOR]` P0 "pay the invoice again" todo already covers, not a new or code-fixable failure mode;
  masking it (relaunching the VM, or patching the connector to suppress the alert) would not restore capture while
  the invoice stays unpaid. Did not re-page the operator via a fresh escalation -- this doc's existing P0 todo already
  covers the ask, and 3 other sessions corroborated the same root cause in the last 48h; posted a bounded `/blocked`
  pointing at this doc instead of duplicating the page. No code changed.
- **2026-08-17 (slot 12, data_pipeline_failure escalation agt-dfccf4, DP-VM-001 on
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-060542`) — STILL `blocked`, reconfirmed via a SECOND shard/day pair.**
  A fleet monitor flagged this VM's `exit_code=137` (stall-induced, not OOM) with the `tradfi-bf-cme-ohlcv-1m-`
  family already at its 2/2 RB-INFRA-RELAUNCH dispatch bound for today. Per the runbook, checked for an existing
  open issue doc — found
  `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`
  (same `btc-2020` shard, prior day's VM `...-20260816-180410`, still open with an unresolved "launcher-family-wide
  code defect vs poison instrument" hypothesis in its "Why this is a PAGE case" section). Pulled `run.log` for
  BOTH this VM and the prior day's `...-20260816-180410` (via GCS SDK reads, never subprocess) — both show the
  identical `DatabentoAdapter: GLBX.MDP3/ohlcv_1m|1s failed [402]: 402 account_delinquent_invoice` signature
  starting from the shard's very first CME trading date (2020-01-02), continuing through every subsequent date
  attempted, until the in-VM stall watchdog fired (3903-3951s no-progress) and self-terminated. This corrects the
  sibling doc's cross-shard-code-defect hypothesis: `btc-2020` is the SAME tracked billing block as
  `g01-6a-6l-2020` (see the 2026-08-17 entry above), not an independent poison-instrument or shared-code-defect
  issue — 3 of the 4 same-week `tradfi-bf-cme-ohlcv-1m-` DP-VM-001 incidents are now confirmed billing-caused (only
  `es-2020` remains undiagnosed, tracked in `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md`). Did not relaunch
  (would blindly repeat the same failure). Updated the sibling doc's Todo 1 + "Why this is a PAGE case" section and
  narrowed `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md`'s Todo (btc-2020 → resolved, es-2020 only remains)
  in the same session. Did not re-page the operator — this doc's existing P0 `[OPERATOR]` invoice todo already
  covers the ask; this is a second independent corroboration, not a new event. No code changed.
- **context-scout 2026-08-17**: populated/refreshed context_scope (1 entries).
- **2026-08-18 (interactive session, answering dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md's
  carried-over [OPERATOR] investigate-the-2-live-capture-stalls todo) — STILL `blocked`, reconfirmed via a fresh direct
  manifest read of the SAME live VM this doc already tracks, not a re-citation of old evidence.** Downloaded
  `_index/per_vm/mtds-live-tradfi-cme-trades-20260809-163443.parquet` directly (UTL `download_bytes`, not gcloud/gsutil)
  and read all 44 rows: `captured` (real row_count 8-201) on 2026-08-09..08-11, then **100% `empty_confirmed` /
  `SOURCE_RETURNED_ZERO` on every single date from 2026-08-12 through TODAY 2026-08-18** (including rows written
  `2026-08-18T10:23:01Z`/`10:24:01Z`/`10:25:01Z`/`10:26:01Z` — literally minutes before this entry, i.e. the VM is
  still actively attempting and still getting zero, right now). This is byte-for-byte the same boundary the
  2026-08-14/08-15/08-17 entries above already established (captured cleanly through 08-11, dead from 08-12 onward) —
  ~6 days further into the same unresolved recurrence, no new mechanism, no code fix possible (the existing `[OPERATOR]`
  P0 "pay the invoice again" todo above already covers the correct action; not re-added as a duplicate). Did not attempt
  a fresh `DatabentoBaseClient.warmup()` call this session — the manifest evidence above is itself a today-dated live
  measurement of the actual symptom (not the account-level auth probe), which is the more direct signal for "is CME
  live capture working," so a redundant warmup call was judged unnecessary. Did not relaunch/restart the VM — the feed
  is dead on the vendor side per every prior diagnosis in this doc; a restart would not fix anything.
- **2026-08-17 (slot 16, data_pipeline_failure escalation agt-4e1517)**: Received a DUPLICATE dispatch of the
  identical DP-VM-001 finding agt-dfccf4 (slot 12) already fully diagnosed above — same VM
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-060542`, same `tradfi-bf-cme-ohlcv-1m-` family at its 2/2 relaunch
  bound. Confirmed via `git log` that agt-dfccf4's doc updates (this doc + the `btc_2020` sibling) had already
  landed (commit `07fdae278a`) before I started editing — pulled first rather than risk clobbering. Did not
  re-diagnose or re-edit the already-covered single-VM root cause (would be pure duplication). Independently found
  NEW information instead: checked the live `tradfi-bf-cme-ohlcv-1m-` fleet and found a fresh ~29-instance
  fleet-wide wave (launched ~09:01-09:06Z today, spanning 9 instrument groups × up to 7 years each) already
  running — including a `btc-2020` replacement, `...-090227`. Pulled ITS run.log directly (GCS SDK read) and
  confirmed it is ALSO hitting the identical `402 account_delinquent_invoice` GLBX.MDP3 signature from its very
  first attempted date, with zero `PROGRESS.json` checkpoint — the entire fresh wave is currently burning SPOT
  compute against the still-active billing block with zero chance of success, not just the isolated stragglers the
  existing entries above cover. Added a new `[OPERATOR]` P1 todo (above) flagging the predictable ~65min-out mass
  stall-watchdog kill across this wave (a coming DP-VM-001 alert storm) and asking the operator to decide
  pause-vs-accept. Did not delete any of the ~29 live VMs myself — unlike the 2026-08-15 precedent above (where the
  agent had personally launched+monitored the one VM it deleted), these were launched by some other
  scheduled/automated mechanism this session did not identify, so unilaterally deleting a fleet I don't own and
  only spot-checked one instance of was judged out of this one-shot escalation's scope; deferring to the operator
  decision above instead. Did not relaunch. Posted a bounded `/blocked` focused on this new wave-scale finding
  (the root cause itself is already covered by agt-dfccf4's page). No code changed.
- **2026-08-19 (slot 31, data_pipeline_failure escalation agt-2e69b4, DP-LIVE-004 on
  `mtds-live-tradfi-cme-trades-20260809-163443`) — STILL `blocked`, same root cause, further-aged reconfirmation.**
  `dp-fleet-monitor`'s `live_stream_watcher.check_live_capture_productivity` paged again: VM `RUNNING`, actively
  attempting (`last attempt 0.0h ago`), CME trades last `captured` **7.5d ago** (staleness budget 3d) — up from the
  5.3d/6d figures the 2026-08-17/08-18 entries above recorded, confirming the gap is still monotonically widening
  with zero recovery, not a new or different failure. Ran `DatabentoBaseClient.warmup()` fresh this session
  (`market-tick-data-service`, Secret Manager key resolved, never printed): **succeeded — 29 datasets, no
  auth/locked/suspended error**, differing from this doc's per-VM-manifest evidence. Per the 2026-08-15 entry's own
  established finding (CME/GLBX.MDP3 is a **dataset-scoped** 402, not an account-wide suspension — other Databento
  venues/datasets write fine), an unscoped account-level `warmup()`/`list_datasets()` success does **not** contradict
  or resolve the CME-specific block; it is consistent with every prior entry since 2026-08-15 and is not new evidence
  either way for whether GLBX.MDP3 itself is unblocked. Deliberately did **not** attempt a live GLBX.MDP3 fetch or a
  fresh manifest/GCS read to further verify — five independent sessions over the last 5 days (08-14/08-15×2/08-17×3/
  08-18) already established this exact signature (`402 account_delinquent_invoice` / `api_key_deactivated`/`unpaid
  invoice` CRAM auth failure) via direct `run.log`/manifest evidence with no change since; a sixth identical
  live-fetch probe would add no new information and risks incurring real Databento cost for a call whose outcome is
  already known with high confidence. Did not attempt a code fix or relaunch — this is the same
  `BLOCKED-OPERATOR-DECISION` the doc's open `[OPERATOR]` P0 "pay the invoice again" todo already covers; masking it
  (relaunching the VM, silencing the alert) would not restore capture while the invoice stays unpaid. Posted a
  bounded `/blocked` pointing at this doc's existing P0 todo rather than duplicating the page. `$AUTHORING_SLOT` was
  `dp-fleet-monitor` (non-numeric) — per the role contract's own carve-out, skipped the authoring-slot ping (the
  dispatch-time Slack alert already covers that FYI). No code changed.
- **2026-08-20 (slot 31, data_pipeline_failure escalation agt-db01a4, DP-LIVE-004 on
  `mtds-live-tradfi-cme-trades-20260809-163443`) — STILL `blocked`, same root cause, 8.0d-aged reconfirmation with fresh
  ground truth.** `live_stream_watcher.check_live_capture_productivity` paged again: VM `RUNNING`, actively attempting
  (`last attempt 0.0h ago`), CME trades last `captured` **8.0d ago** (staleness budget 3d) — gap widened to 8 days, zero
  recovery. Re-verified independently this session via UTL SDK reads (never subprocess gcloud/gsutil): (1) per-VM shard
  `market-data-tick-tradfi-prd-central-element-323112/_index/per_vm/<vm>.parquet` — 52 rows, 12 `captured` (08-09..08-11)
  + 40 `empty_confirmed[SOURCE_RETURNED_ZERO]` (08-12..08-20, `attempted_at` re-stamped every ~60s); (2) `run.log` — same
  `ERROR gateway error code=api_key_deactivated` → reconnect → `CRAM authentication error: ... unpaid invoice` at
  2026-08-12T00:03:56Z, process idle (0.2% CPU / ~739MiB) ever since, feeding zero ticks. Same `BLOCKED-OPERATOR-DECISION`
  — the open `[OPERATOR]` P0 "pay the invoice again" todo above covers the fix. NEW this session (honest-absence gap,
  previously untracked): `websocket_runner.py::_record_empty_window` records a dead-auth stream as
  `empty_confirmed[SOURCE_RETURNED_ZERO]` (false honest-absence) because the connector never surfaces the gateway auth
  failure into the watchdog GAP state the runner gates on; the batch path classifies `402/DATABENTO_PAYMENT_REQUIRED` as
  a venue error — tracked as a new `[CODE] P2` todo above. Posted a bounded `/blocked` pointing at this doc's existing
  P0 (no duplicate page). `$AUTHORING_SLOT`=`dp-fleet-monitor` (non-numeric) — skipped the authoring-slot ping per the
  role contract carve-out. No code changed; doc-only.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-20 (slot 1, data_pipeline_failure escalation agt-f6fbb5)**: Shipped `market-tick-data-service@6836a68eb5484e7d424405d557921cda30de47a4`. Databento auth/payment failures now surface from the live connector and route empty windows to `record_failed` with the classified reason instead of `empty_confirmed[SOURCE_RETURNED_ZERO]`; the billing P0 remains operator-gated.
- **2026-08-20 (data_pipeline_alerts_reconciler, slot 27, dispatch agt-41775d), 6-hourly sweep**: `slack-read-channel.py
  data-pipeline-alerts 24` (2,531 msgs/24h) confirms the P1 todo above (line 162, "the fleet-wide relaunch wave keeps
  hitting the same billing block") is not a one-time 2026-08-17 event — it recurs daily. `DP_VM_EXIT_NONZERO` (122
  msgs/24h) resolves to 114 DISTINCT `tradfi-bf-cme-ohlcv-1m-*` VMs (one exit each, not one VM repeating), all
  `exit_code=137` stall-induced, launched in a single ~12:05-12:17Z wave on 2026-08-19 — consistent with the
  2/shard/day relaunch budget applied across ~55-60 distinct CME-OHLCV shards, all doomed by the same GLBX.MDP3 402
  block. `gcloud compute instances list` confirms a FRESH wave of 17 more launched today (2026-08-20 ~12:03-12:09Z,
  all `RUNNING`) — the pattern is ongoing, not historical. This is pure reconfirmation of the already-open P1 todo
  above (pause-vs-accept the relaunch actuator for this launcher prefix while billing stays blocked), not a new
  finding — no new issue doc filed. Separately, `DP_CRON_DID_NOT_FIRE` (2,122 msgs/24h) is dominated by
  `mtds-live-sports-odds-api-odds-20260816-145019` (1,797 msgs, ~33 venues, never-captured odds) and this VM's own
  `DP_CRON_DID_NOT_FIRE` fire-cadence for individual identities is now averaging ~25-26min (occasional dips to
  ~13-14min) against the 1800s(30min) cooldown — down from the ~15min-flat storm the 2026-08-18/19 dedup-fix chain
  was chasing, and the `uts-prod-alerting-paging-cron` duplicate-consumer fix (paused 06:55Z today per the sibling
  doc) is confirmed still `PAUSED` with no regression; `dp-alerting-subscriber` is on a fresh revision
  (`-00138-lzr`, 100% traffic). Full per-alert classification recorded in
  `/plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` and
  `/plans/active/issues/dp_cron_did_not_fire_still_storming_after_gcs_persistence_fix_2026_08_20.md` rather than
  duplicated here — this entry only adds the CME-OHLCV-relaunch-wave reconfirmation, which belongs on this doc.
- **2026-08-21 (operator ruling D5, autonomous dispatch) — fleet wave mechanism PAUSED at its actual source; 2
  zero-progress VMs stopped; live billing-probe gate shipped.** Operator ruled (D5,
  `.ao_checkpoints/issues_corpus_completion_2026_08_21/triage_decisions.json`): pay the invoice directly AND pause
  the fleet mechanism now (zero-cost, autonomous), make relaunch conditional on a live billing probe. **Root-cause
  finding (misled every prior session that checked, including several entries in this very doc): the daily
  17-114 VM/day relaunch wave was NOT driven by the Terraform-managed `uts-prod-tradfi-wave-launcher-cron` Cloud
  Scheduler job** — that job is confirmed `state: PAUSED` since 2026-06-24, unchanged, zero executions of its Cloud
  Run Job (`uts-prod-tradfi-wave-launcher`) since 2026-06-25 (`gcloud scheduler jobs describe` /
  `gcloud run jobs executions list`, both re-verified live this session) — **it was a separate, undocumented crontab
  entry directly on the AO orchestrator VM's (`i-0c9b283b31d6b5ca7`) `ubuntu` user**, running
  `scripts/wave_launcher.py` every 3h at `WAVE_MAX_CONCURRENT=20` (the hard ceiling), confirmed via the script's own
  `vm-census/wave-launcher-last-run.json` sentinel showing a fresh tick at `2026-08-21T21:00:06Z` — 3 minutes before a
  ~20-VM burst appeared in `gcloud logging read` (`protoPayload.methodName="v1.compute.instances.insert"`, all
  `principalEmail=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, 21:03-21:26Z). Every prior
  session (2026-08-09/11/15×3/17) that checked only the Cloud Scheduler job and concluded "PAUSED, not the source"
  was correct about that job but never found this shadow host cron. **Actions taken, in order:**
  1. **Paused at the source** — via AWS SSM `AWS-RunShellScript` on `i-0c9b283b31d6b5ca7`: backed up the `ubuntu`
     crontab (`/home/ubuntu/crontab_backup_pre_wave_launcher_pause_2026_08_21.txt`), then commented out the
     `wave_launcher.py` line with a dated marker citing this doc + the re-enable condition (billing confirmed OK
     AND the shipped billing-probe gate live), confirmed via `crontab -l -u ubuntu` post-edit.
  2. **Verified the pause held** — 0 `tradfi-bf-cme-ohlcv-1m*` instances present in `gcloud compute instances list`
     both immediately after the pause and again at a fresh check 20 minutes later (`2026-08-21T22:54:57Z` →
     `2026-08-21T23:14:57Z`, background-timed, zero rows both times) — zero new CME VMs launched in the observation
     window.
  3. **Stopped the 2 CME VMs that were running at pause time, burning SPOT compute for zero progress** —
     `tradfi-bf-cme-ohlcv-1m-es-2022-20260821-215556` (ES.FUT/OPT, launched 21:55) and
     `tradfi-bf-cme-ohlcv-1m-nq-2020-20260821-221610` (NQ.FUT/OPT, launched 22:16). Read `run.log` for both directly
     via UTL `get_storage_client()` (never subprocess) before deleting: both showed the identical
     `DatabentoAdapter: GLBX.MDP3/ohlcv_1s failed [402]: 402 account_delinquent_invoice` on every attempted date with
     `SHARD_INCOMPLETE`/0-records writes, confirming genuine zero progress against the billing wall (not a
     transient/recoverable state) before `gcloud compute instances delete`.
  4. **Shipped a live Databento billing-probe gate into `wave_launcher.py` as defense-in-depth** for whenever this
     (or the Terraform Cloud Scheduler) mechanism is re-enabled: `cme_billing_probe_ok()` calls
     `databento.Historical(...).metadata.get_cost()` — a cost ESTIMATE that never transfers data / never bills —
     scoped to `GLBX.MDP3`, which still exercises the same account+dataset entitlement check a real fetch would hit.
     `run_tick()` now drops CME dispatches from the wave (logs + emits `DP_TRADFI_CME_BILLING_BLOCKED`) whenever the
     probe fails, fail-CLOSED on any exception (an ambiguous probe error must never be read as "billing is fine").
     Evidence: `deployment-service@3367cfea` (`scripts/wave_launcher.py`,
     `tests/unit/test_wave_launcher_cme_billing_probe.py`); quality-gates=PASS (3660 passed, 0 failed, sentinel
     `e15198e4b2d6bbdab6758805cc5dba0e8a5fa778`→`3367cfea`); verified ancestor-or-equal of
     `origin/live-defi-rollout` (0 ahead/0 behind post-push). Also fixed one PRE-EXISTING, unrelated red-gate test in
     the same shipped commit (`tests/unit/test_refetch_feed.py::test_dry_run_plan_includes_cli` — stale literal
     `refetch-feed:binance` vs. the already-shipped, intentional `rotate-websocket:binance` verb-aware routing from
     `/plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md`; confirmed via `git log`/`git
     diff` that no local WIP or plan collision existed — a stale-assertion fix, not a design change) per the
     autonomous-dispatch rule that red quality gates in this slot are mine to fix now, not defer.
  **Not done this session (explicitly out of scope for D5, left for the operator/a future session):** re-enabling
  either mechanism (correctly stays paused until the operator confirms the invoice is paid AND live-verifies CME
  specifically, per this doc's own dataset-scoped-not-account-wide finding from 2026-08-15); registering the
  discovered host-cron mechanism into Terraform/a tracked launcher registry (it predates this session and its origin
  is unknown — flagging as a follow-up, not fixing the meta-problem of "undocumented host crons exist" here).
