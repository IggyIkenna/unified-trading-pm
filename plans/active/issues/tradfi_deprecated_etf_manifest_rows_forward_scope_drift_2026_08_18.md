---
doc_type: issue
title: TradFi manifest carries 5,932 re-accumulated deprecated-ETF rows — forward-going capture-scope drift, unowned
summary: >-
  `market-data-tick-tradfi-prd-...`'s manifest currently carries 5,932 rows matching the exact deprecated-ETF
  ticker/venue pattern (`ETHE`/`GBTC`/`BITO`/`FBTC`/`ARKB`/`FETH` at `NYSE`/`NYSE_ARCA`/`BATS`/`CBOE_BZX`), dated
  through 2026-08-11 -- well after `purge_deprecated_etf_manifest_rows_2026_05_16.py`'s 2026-05-16 one-off purge
  (121 rows, confirmed correctly executed, CAS-verified). This means some capture path is still fetching/writing
  these MVP-excluded tickers going forward, independent of the purge script itself (which worked correctly at the
  time and is not the bug). Side finding surfaced 2026-08-18 during the fleet-wide UTL GCS-client Category-1
  data-integrity audit -- flagged there as out of that audit's scope, not investigated or fixed. Corpus-wide grep
  (2026-08-18, this doc's own filing session) confirms no other plan or issue doc tracks this specific
  re-accumulation -- genuinely unowned until now.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [tradfi, etf, scope-drift, data-correctness, unowned, manifest]
related:
  [
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    /plans/epics/tradfi_master.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-18
last_updated: "2026-08-20"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: data
effort: low
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    deployment-service/scripts/migrations/instruments-service/purge_deprecated_etf_manifest_rows_2026_05_16.py,
    /plans/active/tradfi_satellite_ao_dispatch_batch18_2026_08_19.md,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-18 as a side finding during the UTL GCS-client Category-1 data-integrity audit (row 9 of the
    per-script classification table in
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md) -- explicitly flagged
    there as 'out of this audit's scope' and not investigated further. This doc's own filing session (Priority 3 of
    a tracked backlog pass) grepped plans/active/ + plans/active/issues/ for '5,932'/'5932'/'deprecated-etf' and
    confirmed no dedicated tracking doc exists -- only this one inline mention in the source audit doc and a
    filename citation (of the unrelated purge script) in
    migration_script_canonicalization_into_deployment_service_2026_08_18.md's Phase-1 file list.",
  ]
locked_by:
locked_since:
---

# TradFi manifest carries 5,932 re-accumulated deprecated-ETF rows — forward-going scope drift, unowned

## What's known (from the source audit, not re-verified independently by this filing session)

`instruments-service/scripts/purge_deprecated_etf_manifest_rows_2026_05_16.py` ran successfully on 2026-05-16
(`instruments-service@f203ef3`, per `plans/epics/tradfi_master.md`): deleted 121 rows via CAS
(`if_generation_match=1778936472461402`), no backup step by design (direct CAS overwrite), and the fix was working
code — this is not the GCS `upload_from_string`/silent-write-failure bug the source audit doc was investigating.

A live GCS read done during that audit (2026-08-18) confirmed the *original* 121-row purge target is gone, but found
**5,932** rows matching the identical deprecated-ETF ticker/venue pattern have since re-accumulated in
`market-data-tick-tradfi-prd-...`'s manifest, with dates extending to **2026-08-11** — nearly three months after the
one-off purge. The exact match criteria: tickers `ETHE`/`GBTC`/`BITO`/`FBTC`/`ARKB`/`FETH` at venues
`NYSE`/`NYSE_ARCA`/`BATS`/`CBOE_BZX`.

## What this means

Some capture path — not identified by the source audit, which was scoped to a different bug — is still
fetching/writing these MVP-excluded tickers going forward. The 2026-05-16 purge was a one-off cleanup of a
point-in-time state, not a scope enforcement mechanism; nothing currently stops the same tickers from being
recaptured on every subsequent run.

## Explicitly not yet done (this filing session's scope was ownership-check only)

- Root cause not investigated: which capture path (a venue adapter's own instrument-universe resolution? an MVP
  scope filter that doesn't cover these specific tickers? a stale reference-data cache?) is sourcing these tickers.
- No re-purge attempted — a second one-off purge without fixing the forward-going source would just re-accumulate
  again, per the same mechanism that produced this 5,932-row count in the first place.
- No confirmation of current row count as of this doc's filing date (2026-08-18) — the 5,932 figure is from the
  source audit's live read on the same day; a future session picking this up should re-measure rather than trust
  this number if meaningfully more time has passed.

## Todos

- [ ] [DATA] P3. **Root-cause which capture path is still fetching/writing the deprecated-ETF tickers
      (`ETHE`/`GBTC`/`BITO`/`FBTC`/`ARKB`/`FETH` at `NYSE`/`NYSE_ARCA`/`BATS`/`CBOE_BZX`) going forward** — check
      whether a venue adapter's own instrument-universe resolution, an MVP scope filter that doesn't cover these
      specific tickers, or a stale reference-data cache is the source. Open-ended investigation, not a bounded
      single action.
- [x] ✅ [DATA] P3. **Re-measure the current re-accumulated row count** against the 2026-08-18 baseline (5,932 rows)
      before acting further — the figure is from a same-day live read during an unrelated audit and should not be
      trusted without a fresh confirmation if meaningfully more time has passed. — **EXTRACTED 2026-08-19
      (na-eligibility-audit, tradfi tranche, dispatch agt-5d34f9) →
      `tradfi_satellite_ao_dispatch_batch18_2026_08_19.md` todo 1** (conflict-cleared: corpus-wide grep confirms
      no other active/draft doc tracks this re-accumulation). Fully-specified deterministic query (exact tickers,
      exact venues, exact target manifest named above), bounded worker-determinable outcome (a number) — clears
      the dispatch-scope-eligibility bar on its own, unlike todos 1/3 below which stay genuinely open-ended/gated.
- [ ] [DATA] P3. **Once root-caused: fix the forward-going source AND re-purge** the re-accumulated rows — a second
      one-off purge without fixing the source would just re-accumulate again, per the same mechanism that produced
      this count in the first place. Gated on the root-cause todo above.

## Progress Log

- **2026-08-18**: filed while checking Priority-3 ownership of this side finding (tracked backlog pass). Confirmed
  via corpus-wide grep this re-accumulation was flagged but never tracked as its own item anywhere —
  `assigned_vm: NA` pending root-cause investigation into the still-active capture path.
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — converted prose to
  tracked todos (HARD RULE: every follow-up is a `- [ ]` todo, never prose).** The doc's own "Explicitly not yet
  done" section named 3 real follow-up items that existed only as prose — added as tracked checkboxes above,
  content unchanged. All 3 are genuine open-ended investigation/execution work (root cause unknown, needs
  exploration), not a single worker-determinable outcome. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **RECLASSIFY, per-todo split.** 3 open
  todos re-read end-to-end. Todo 2 (re-measure the row count) is a fully-specified, deterministic read-only query —
  bounded/worker-determinable, conflict-checked clean — extracted to
  `tradfi_satellite_ao_dispatch_batch18_2026_08_19.md` todo 1. Todos 1 (root-cause which capture path, open-ended,
  multiple unresolved hypotheses) and 3 (fix + re-purge, gated on todo 1's unknown outcome) stay genuinely
  investigation/judgment work. Doc stays `assigned_vm: NA` — 2 of 3 todos remain genuinely NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
