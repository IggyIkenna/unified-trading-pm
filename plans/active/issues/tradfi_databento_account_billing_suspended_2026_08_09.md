---
doc_type: issue
title: TradFi Databento account suspended by vendor for non-payment — all Databento fetches fail account-wide
summary: >-
  Operator report 2026-08-09: Databento has suspended our account because the bill was not paid. This is a FULL
  account-level outage — broader than the existing 3-dataset billing-safety allowlist
  (`/codex/02-data/tradfi-databento-sourcing-ssot.md`), which guards against silent metered charges on an otherwise-live
  subscription. With the account itself suspended, EVERY Databento request (batch backfill AND the live
  `databento_tradfi_ws` connector) will fail regardless of allowlist compliance, until the operator pays the bill and
  the vendor restores the account. Every open TradFi MTDS/backfill todo that depends on a live Databento fetch is
  non-dispatchable until this resolves. Features/ML work on already-captured data is UNAFFECTED and should proceed.
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
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
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
context_scope: [/codex/02-data/tradfi-databento-sourcing-ssot.md]
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

- [ ] [OPERATOR] P0. **RECURRED 2026-08-12 — pay the outstanding Databento invoice again; the account went unpaid a
      second time after the 2026-08-10 restoration below.** Evidence: `mtds-live-tradfi-cme-trades-20260809-163443`'s
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
      `market_tick_data_service/live/connectors/     databento_tradfi_ws.py` (not touched by this session — out of
      ownership scope; diagnosed 2026-08-14 during `cross_ag_live_capture_parity_2026_08_14.md` Finding C).
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
      `issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`,
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
  specific gate is LIFTED.** `/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (same day,
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
