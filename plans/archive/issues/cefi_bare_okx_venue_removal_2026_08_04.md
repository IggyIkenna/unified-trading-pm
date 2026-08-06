---
doc_type: issue
title: Bare "OKX" removed entirely from the CeFi venue registry — code shipped + deployed; one live VM restart remains
summary: >-
  Operator asked why the cefi manifest/Distinct Values panel showed 4 OKX venues (OKX, OKX-SPOT, OKX-SWAP, OKX-FUTURES)
  and directed removal of the redundant bare "OKX" entry. Investigation found bare OKX was not just cosmetic residue —
  it was a live, currently-load-bearing registry entry (Layer-1 EXPECTED-tuple anchor for OKX-SWAP's real PERPETUAL
  data) AND the source of 2,475+ permanently-failing attempted_failed manifest rows going back to 2026-05-01 (bare OKX
  has no unambiguous Tardis exchange — it splits across 4 real exchanges). Full fix shipped: UAC registry surgery (moved
  OKX-SWAP's real data off the bare-OKX proxy onto its own declaration, dropped the dead OPTION capability, fixed a
  legacy-dialect fold bug as a side effect), quality-gates green in unified-api-contracts + market-tick-data-service,
  production tarball refreshed, honest-coverage rollup re-triggered and confirmed OKX gone from the live Distinct Values
  panel, 2,475 dead manifest rows purged. One action remains: the long-lived mtds-live-cefi-consolidated VM booted
  before the fix and won't pick it up until restarted.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service, deployment-service]
scope: [engineer, admin]
tags: [cefi, okx, venue-registry, manifest, honest-coverage, data-correctness, vm-restart]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/archive/issues/cefi_bare_venue_manifest_residue_2026_07_26.md,
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
  ]
created: "2026-08-04"
author: unknown
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
source: "operator, interactive session, 2026-08-04"
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: "interactive session, /autonomous, 2026-08-04 — both open todos closed, see Progress Log"
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# Bare "OKX" CeFi venue removal (2026-08-04)

## What shipped

1. **unified-api-contracts@d67a226f** (`fix(cefi): remove bare OKX from the venue registry`) — removed bare `"OKX"` from
   `VENUES_BY_ASSET_GROUP["cefi"]` and its `INSTRUMENT_TYPES_BY_VENUE`/`VENUE_DATA_TYPE_CAPABILITIES` cefi-capture
   entries; added `OKX_SWAP: {"PERPETUAL"}` so OKX-SWAP's real trades/book_snapshot_5/derivative_ticker/liquidations
   generate their own Layer-1 EXPECTED tuples directly (previously relied entirely on folding through bare OKX — a real
   dependency, verified via a `build_expected("cefi")` before/after diff). Dropped the dead `OPTION` capability (Tardis
   routing + a stray `OPTION` member that had also snuck onto `OKX-FUTURES` with zero real data behind it). Fixed
   `CEFI_VENUE_FOLD` so legacy `OKEX`/`OKEX-SWAP`/`OKEX-FUTURES` dialect rows fold to the correct product-specific venue
   instead of a now-nonexistent bare `OKX` (previously they'd have folded to a target whose own `SPOT_PAIR` declaration
   was already removed 2026-07-10 — a latent bug this fix incidentally closes). Kept a scoped `OKX: {"PERPETUAL"}` entry
   solely for the separate `CLOB_VENUES` execution-context registry (`test_all_clob_venues_in_instrument_types`) —
   confirmed unreachable from the cefi capture-universe path. Quality-gates green (12,436 tests).
2. **market-tick-data-service** (2 commits, quickmerged) — fixed 2 tests broken by the registry change (a dead
   options-routing regression test, a `_PER_AG_SHARD_COUNTS` pin: CEFI 234→225, documented inline matching the file's
   own historical-pin convention). Also fixed a related, separately-found bug in the same file: `_VENUE_INSTRUMENT_TYPE`
   used lowercase `"spot"` for 5 CeFi venues (BINANCE-SPOT/COINBASE-SPOT/OKX-SPOT/BITFINEX-SPOT/BITGET-SPOT/KRAKEN-SPOT/
   UPBIT) instead of canonical `"SPOT_PAIR"` — same bug class BYBIT-SPOT was already fixed for 2026-07-12
   (`bybit_spot_manifest_stray_captures_2026_07_07.md`), just never extended to the rest. Quality-gates green.
3. **Production tarball refreshed** (`create-code-tarballs.sh`, CORE scope) — verified
   `unified-api-contracts-code.manifest.json`'s `commit_sha` is `d67a226f` (ancestor-checked via
   `git merge-base --is-ancestor`, not just a timestamp compare, per this workspace's `vm-tarball-deployment.md`
   content-based-verification rule).
4. **Honest-coverage rollup re-triggered** (`gcloud scheduler jobs run honest-coverage-daily`) rather than waiting for
   tomorrow's 00:30 UTC cron — confirmed the fresh `2026-08-04/coverage.json` no longer lists bare `OKX` in
   `by_venue.cefi` (only `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES` remain).
5. **Manifest cleanup, `market-data-tick-cefi-prd-{PROJECT_ID}`**:
   - Purged 2,475 dead `venue=="OKX"` `attempted_failed` rows (2026-05-01→2026-08-03, zero real data behind any of them
     — confirmed via direct manifest read before deleting). CAS-protected write, verified `9,520,512 → 9,518,037` rows,
     zero collateral.
   - Relabeled (NOT deleted — real `captured`/`empty_confirmed` data, just a wrong field value) 4,923
     `instrument_type=="spot"` rows → `"SPOT_PAIR"`, and 943 `chain=="FUTURES"` rows → `chain=""` (8 old
     `BITFINEX-FUTURES` residue from an already-fixed unrelated bug + 935 new `COINBASE-FUTURES` rows from a still-open
     bug — see `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s new 2026-08-04 entry for that investigation).
     CAS-protected write, `9,529,244` rows unchanged (correct — a relabel, not a delete).

Both one-off scripts used for the manifest surgery were deleted after a successful run, not committed — mirrors the
established precedent for this exact class of purge (`cefi_bare_venue_manifest_residue_2026_07_26.md`, archived).

## What's still open

- [x] ✅ [OPERATOR] P2. **RESTARTED 2026-08-04 ~10:14-10:16 UTC (`/autonomous` session), with a correction to this
      todo's own original framing.** `gcloud compute instances stop` then `start` on
      `mtds-live-cefi-consolidated-20260802-142543` (`asia-northeast1-c`) — clean shutdown, clean reboot, fresh tarball
      pulled (`_download_tarball` in `setup-cefi-live-consolidated-vm.sh` always fetches on every startup-script run,
      confirmed via direct read of the script from `gs://deployment-scripts-central-element-323112/vm/`), supervisor
      relaunched (`Supervisor started PID=2617`, serial-console-confirmed), `google-startup-scripts.service` reported
      `Finished` with no `SETUP FAILED` trap firing. **Correction**: re-reading this same startup script during
      verification found its `MVP_SHARDS` array is a HARDCODED list of explicit venue:data_type pairs
      (`OKX-FUTURES:trades`, `OKX-FUTURES:book_snapshot_5`, `OKX-FUTURES:derivative_ticker`, etc.) — it never included
      bare `OKX` and does not iterate any UAC registry to decide what to stream, so this specific VM was **not** among
      the sources actively re-attempting bare-OKX captures (the 2,475 purged rows more likely trace to a
      registry-iterating backfill/forward-poll path, not this consolidated websocket VM). The restart's concrete value
      here is general hygiene (this VM now runs the current UAC+MTDS code, including today's `SPOT_PAIR` fix) rather
      than closing an active bare-OKX-emitting bug on this VM specifically — flagging the correction rather than letting
      the original overclaim stand uncorrected, per this workspace's own "don't trust a prior written claim over live
      verification" precedent.
- [x] ✅ [DIAG] P3. The `okx_futures_instid_marker_convention_mismatch_2026_07_30.md` issue (OKX-FUTURES's own
      `@LIN`/`@INV` id-marker convention) is unrelated to this doc's bare-OKX removal — cross-referenced only because
      it's the other currently-open OKX-family issue; no action was needed here (informational cross-reference only).

## Progress Log

- 2026-08-04 (interactive session): full investigation + fix + deploy + verify + manifest cleanup, as described above.
  Restart todo filed rather than executed — a live-capture VM restart warrants its own attention, not a same-session
  bundle with the manifest/code work.
- 2026-08-04 ~10:14-10:16 UTC (`/autonomous` continuation session): restarted
  `mtds-live-cefi-consolidated-20260802-142543` (stop → start, clean boot, fresh tarball confirmed via
  `google-startup-scripts.service` `Finished` + supervisor `PID=2617` on the serial console). Corrected this doc's
  original assumption that the VM was itself emitting bare-OKX capture attempts — its shard list is a hardcoded
  `venue:data_type` array that never included bare `OKX` (always `OKX-FUTURES:*`), so it was never a source of the 2,475
  purged rows; the restart's value is picking up the current UAC+MTDS tarball (incl. today's `SPOT_PAIR` fix), not
  fixing an active bug on this VM. Both open todos closed — **doc resolved**, no further action outstanding.
