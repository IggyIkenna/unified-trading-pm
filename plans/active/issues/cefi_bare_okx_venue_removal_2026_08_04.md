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
status: open
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
resolved_by:
---

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

- [ ] [OPERATOR] P2. **Restart `mtds-live-cefi-consolidated-20260802-142543`** (GCE, `asia-northeast1-c`,
      `LONG_LIVED_LIVE`, running since 2026-08-02 — confirmed still `RUNNING` as of this doc's creation). This VM booted
      before the tarball refresh and, per `vm-tarball-deployment.md`, a running process does not re-fetch its own code —
      it will keep attempting bare-OKX live captures (failing every time, same root cause as the 2,475 purged rows)
      until restarted onto the fresh tarball. Bounded impact (a live VM restart is brief downtime for CeFi live capture,
      not a backfill) — per CLAUDE.md "Maintenance-window restarts... skip operator scheduling pre-live-trading —
      group + do now, brief downtime OK", this does not need a scheduled window, but a live production capture VM
      restart deserves a deliberate action, not one folded into an unrelated session's checkpoint. Verify post-restart:
      confirm the VM's fresh boot log shows the new tarball's commit_sha, and that no NEW `venue=="OKX"` manifest rows
      accumulate over the following ~24h (re-check via the same `read_availability_index` + `venue=="OKX"` filter this
      doc's investigation used).
- [ ] [DIAG] P3. The `okx_futures_instid_marker_convention_mismatch_2026_07_30.md` issue (OKX-FUTURES's own
      `@LIN`/`@INV` id-marker convention) is unrelated to this doc's bare-OKX removal — cross-referenced only because
      it's the other currently-open OKX-family issue; no action needed here.

## Progress Log

- 2026-08-04 (interactive session): full investigation + fix + deploy + verify + manifest cleanup, as described above.
  Restart todo filed rather than executed — a live-capture VM restart warrants its own attention, not a same-session
  bundle with the manifest/code work.
