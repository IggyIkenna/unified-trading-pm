---
doc_type: issue
title:
  "None of this session's adapter/instrument-definition findings have been verified for 3-layer reconciliation — GCS
  parquet, manifest, and deployment-ui/API may each tell a different story"
summary:
  "The 2026-07-07 full adapter smoke test (17 clusters, [[mtds_is_full_adapter_smoketest_findings_2026_07_07]]) and the
  lending a-token/debt-token investigation ([[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]) verified
  correctness at exactly one layer: can instruments-service/MTDS's adapters actually fetch/ enumerate real data from the
  venue/protocol's own API or on-chain source. Operator flagged (2026-07-08, using AAVE_V3 as the concrete example): we
  have not verified whether these same findings are consistently visible at the other two layers a real user/operator
  actually looks at — (1) the raw GCS parquet files themselves (column names, instrument_id values physically written to
  disk), (2) the manifest (`availability_index.parquet` / `expected_universe_ranges.parquet` — what
  `codex/02-data/honest-coverage-model.md`'s Layer-1/Layer-2 model actually audits), and (3)
  deployment-ui/deployment-api (the actual UI surface this whole multi-week effort exists to fix). A bug could be fixed
  at the adapter level and still show wrong in the UI if the manifest or deployment-api has its own independent bug
  (stale cache, hardcoded instrument_type allowlist that does not know about A_TOKEN/DEBT_TOKEN yet, wrong query, etc) —
  or a bug could look fixed in a spot-check of raw GCS data while the manifest never gets updated to reflect it. This
  doc documents the gap; per the operator, actually closing it is staged work, not a single pass."
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data, meta]
repos: [instruments-service, market-tick-data-service, deployment-api, deployment-ui, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    gcs,
    manifest,
    deployment-ui,
    deployment-api,
    honest-coverage,
    data-pipeline-correctness,
    verification-gap,
  ]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
    defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P1
source:
  'Operator, 2026-07-08: "for all the issues for example aave_v3 are we reconciling at gcs data level (the parquets
  themselves) the manifest level and the deployment ui/api level? because we should" + "we should document that at
  least, fixing will be in stages ofc."'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **Verification-gap finding, not a confirmed bug — the whole point is we don't yet know.** Every finding in the two
> cross-referenced docs was verified at the adapter/live-fetch layer only. This doc's job is to name the gap precisely
> and stage the work to close it, not to claim any specific 3-layer mismatch exists yet (though given the volume and
> severity of what the adapter-layer audit found, it would be surprising if none did).

## The three layers, precisely

1. **GCS parquet level** — the actual bytes on disk: column names, the literal `instrument_id`/`instrument_type` string
   values written into each row, partition path shape. This is what
   `instruments-store-{ag}-prd-.../prod/catalog.parquet` and `market-data-tick-{ag}-prd-.../raw_tick_data/...`
   physically contain. This IS what the smoke test and lending investigation read directly (via `get_storage_client()` +
   `download_bytes` + `pandas.read_parquet`) — this layer is well-covered by this session's work.
2. **Manifest level** — `availability_index.parquet` / `expected_universe_ranges.parquet`, the Honest-Coverage-v2
   tracking layer (`codex/02-data/honest-coverage-model.md`) that derives `capture_status` (captured / empty_confirmed /
   expected_unattempted / attempted_failed) per `(venue, instrument_type, data_type, day)`. This layer is built FROM the
   GCS writes but is a separate artifact that can drift from what's actually on disk (already confirmed possible this
   session — the HYPERLIQUID phantom-audit false-negative found earlier flags exactly this kind of manifest/reality
   mismatch, just in the opposite direction: manifest said phantom, GCS had the real file). **Not checked this session**
   for any of the 59 adapter-layer findings.
3. **deployment-ui / deployment-api level** — the actual coverage.json v2 response
   (`codex/06-coding-standards/data-status-endpoint-contract.md`) and what deployment-ui renders from it. This is what
   an operator actually looks at day to day, and it's the layer this whole multi-week instrument-completion effort
   exists to make trustworthy. **Not checked this session at all** — no deployment-api endpoint was hit, no
   deployment-ui page was loaded, for any of the 59 findings.

## Why this matters (concrete, using the operator's own example)

Take AAVE_V3's `instrument_type` mislabel (real catalogue already splits A_TOKEN/DEBT_TOKEN correctly at the KEY level,
but the stored `instrument_type` FIELD says `LENDING` for both). Three independent questions, none yet answered:

- Does deployment-api's coverage computation key off the stored `instrument_type` FIELD, or off the instrument_id KEY's
  embedded type segment? If the field, deployment-api is currently showing AAVE_V3 as 100% `LENDING`-typed with zero
  A_TOKEN/DEBT_TOKEN breakdown, even though the real position-level split already exists in the data — a real
  under-representation the operator can't see today.
- Once the field gets fixed (per the queued P1 todo in [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]),
  does the manifest's own `expected_universe_ranges.parquet` get regenerated with the new type split, or does it need an
  explicit re-enumeration run? If the latter, the fix could ship in instruments-service and STILL not show up in
  deployment-ui until a separate manifest-rebuild step runs.
- Does deployment-ui have any hardcoded `instrument_type` allowlist/enum (a TypeScript union type, a filter dropdown's
  option list, a color-coding switch statement) that would need its OWN update to even display an `A_TOKEN`/`DEBT_TOKEN`
  row correctly, versus silently dropping or mis-rendering it?

Multiply this by all 59 findings in the smoke-test doc (margin-type mislabels on OKX/BYBIT/KRAKEN-FUTURES, the DERIBIT
live-vs-batch misclassification, HUOBI/BITSTAMP missing-from-venue-universe, ETHENA's fabricated prices, GMX's synthetic
funding, etc) — each one has this same 3-layer question open.

## What this is NOT

- Not a claim that deployment-api/deployment-ui are definitely broken — they may already correctly key off instrument_id
  rather than the (buggy) `instrument_type` field, in which case several of these findings might already be invisible to
  the operator in exactly the right way (correctly hidden) or exactly the wrong way (correctly hidden bugs that should
  be surfaced as gaps). Genuinely unknown until checked.
- Not asking to re-verify all 59 findings' adapter-layer correctness — that work is done and stands.
- Not a request to fix anything yet — per the operator, this is staged: document now, reconcile in stages later,
  starting with whichever findings turn out to matter most once the first few real traces are done.

## Todos

- [ ] [VERIFY] P1. **Trace AAVE_V3 end-to-end as the pilot case** (operator's own example) — for a single real reserve
      (e.g. `AAVE_V3-ARBITRUM:A_TOKEN:AAAVE`), confirm what deployment-api's `/data-status` (or equivalent coverage.json
      v2) endpoint actually returns for this instrument today, and whether deployment-ui renders it distinctly from its
      `DEBT_TOKEN` counterpart or collapses both under a generic `LENDING` bucket. This single trace answers whether the
      `instrument_type` field mislabel is cosmetic (key already correct, UI doesn't care) or a real UI-visible gap.
- [ ] [VERIFY] P1. **Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger**
      when an instruments-service adapter's stamped `instrument_type` changes (relevant the moment any of the
      AAVE_V3/SPARK/COMPOUND_V3/MORPHO/FLUID/etc fixes actually ship) — if manual, that's a real "fix shipped but
      nothing looks different for N days" trap worth flagging in each fix's own rollout plan.
- [ ] [VERIFY] P2. **Spot-check 2-3 more findings from the smoke-test doc across all 3 layers** — good candidates: the
      DERIBIT live-vs-batch FUTURE misclassification (does deployment-ui show a FUTURE count that matches the real GCS
      row count, or does the live-WS mislabel bleed into the manifest?), and HUOBI-SPOT's missing-from-venue-universe
      gap (does deployment-ui even have a HUOBI-SPOT row to look wrong, or does the venue not appear in the UI's venue
      list at all — a different, more visible kind of gap).
- [ ] [VERIFY] P2. **Check deployment-ui for hardcoded `instrument_type` allowlists/unions** (TypeScript types, filter
      dropdowns, color-coding switches) that would need their own update once A_TOKEN/ DEBT_TOKEN (and other
      target-state types from the canonicalization decision) start appearing in real data — a silently-broken or
      silently-dropped row is worse than a visibly-wrong one.
- [ ] [DECISION] P2. **Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
      findings** — full trace per finding (expensive, thorough) vs a lighter spot-check pattern informed by what the
      AAVE_V3 pilot reveals about where 3-layer drift actually tends to occur.

## Progress Log

- **2026-07-08** — Filed after the operator asked, while reviewing the drilldown mockup's AAVE_V3 entry, whether this
  session's adapter-level findings have been reconciled against the manifest and deployment-ui/API layers too.
  Confirmed: no, they have not — this session's verification (the full adapter smoke test + the lending investigation)
  only ever checked the GCS/adapter layer. Operator explicitly wants this documented now with staged fixing to follow,
  not a single pass today. No investigation done yet beyond naming the gap and proposing AAVE_V3 as the pilot trace.
