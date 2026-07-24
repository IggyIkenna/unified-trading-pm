---
doc_type: plan
title: MTDS lending instrument_type — historical manifest re-stamp
summary: >-
  MTDS `liquidations_handler.py`'s lending `instrument_type` writer bug is already fixed going forward (`mtds@fec20de2`
  — manifest stamp + disk write both derive from the same `resolve_lending_instrument_type()` call), but existing
  historical manifest rows are still stamped `instrument_type="liquidation"` (the value the distinct-values census
  currently reads as non-canonical). Forked out of the distinct-values non-canonical audit (2026-07-24 operator rescope)
  to build + apply the paired historical re-stamp, mirroring the already-shipped cefi venue-as-chain and sports
  odds_horizon_bucket re-stamp pattern (pre-apply GCS snapshot, CAS-guarded --apply, operator-authorized paused-writer
  window).
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest, data-correctness, restamp, canonicalisation, lending]
related:
  [
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  forked from /plans/active/distinct_values_noncanonical_audit_2026_07_20.md per explicit operator rescope decision
  2026-07-24 (fork ONLY the MTDS lending-instrument-type historical-restamp workstream out; RESTAKING stays in the
  parent as shipped historical record)
last_updated: 2026-06-27
---

# MTDS lending instrument_type — historical manifest re-stamp

## Background (moved verbatim from the parent audit plan)

MTDS `liquidations_handler.py`'s lending `instrument_type` writer code is fixed (`market-tick-data-service@fec20de2`,
"single-resolution-point instrument_type for market/event lending writers", verified ancestor of
`origin/live-defi-rollout`) — both the manifest stamp (`liquidations_handler.py:441`, `.value.lower()`) and the disk
write (`:551`) now derive from the SAME `resolve_lending_instrument_type(protocol)` call, so there is no more
manifest-vs-disk desync GOING FORWARD.

**Still open**: the paired re-stamp of EXISTING historical rows (still stamped `instrument_type="liquidation"`, the
count the distinct-values census currently reads) has NOT been executed — no script exists for it yet (checked: no
`restamp*lending*` script in market-tick-data-service as of 2026-07-22/24). This is a genuine manifest-mutation
follow-up, same class/risk as the MTDS venue-as-chain re-stamp (`restamp_cefi_onchain_perp_venue_chain_2026_07_21.py`,
applied+verified 2026-07-22) and the sports `odds_horizon_bucket` re-stamp
(`restamp_sports_odds_horizon_bucket_2026_07_22.py`, shipped, apply pending a paused-writer window) — both are the
precedent pattern for the todos below: pre-apply GCS snapshot of the manifest availability index, CAS-guarded `--apply`
write, dry-run-by-default script, operator-authorized paused-consolidator-cron window to apply without CAS contention,
post-write verification (row-count in == row-count out, 0 duplicate row_keys, only the target rows changed), then resume
the cron.

This is NOT something executed inside the parent audit session (destructive-beyond-local = human-only /
operator-authorized-cron-pause, per that plan's own established precedent) — hence this dedicated fork.

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` (manifest row-key / CAS-write model)
- `/codex/02-data/defi-canonical-naming-ssot.md` (lending instrument_type canonical spelling)
- `/plans/active/distinct_values_noncanonical_audit_2026_07_20.md` (parent audit — headline finding, classification
  framework, and the two already-shipped sibling re-stamps this plan mirrors)

## Todos

- [ ] [DATA] P1. Measure the exact scope: live-count MTDS manifest rows where `instrument_type="liquidation"` was
      written by the pre-fix `liquidations_handler.py` code path (before `mtds@fec20de2`), across all affected
      shards/venues/date ranges. Confirm these are genuinely lending rows (not real liquidation-event rows that should
      stay `liquidation`) by cross-checking `resolve_lending_instrument_type(protocol)` against the historical
      `protocol` column per row. Cite the exact row count and shard breakdown.
- [ ] [DATA] P1. Build `market-tick-data-service/scripts/restamp_lending_instrument_type_2026_07_24.py`, mirroring the
      `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` / `restamp_sports_odds_horizon_bucket_2026_07_22.py` safety
      pattern exactly: dry-run by default, `--apply` performs the live CAS-guarded write, pre-apply GCS snapshot of the
      manifest availability index taken first, post-write verification (rows-in == rows-out, 0 duplicate row_keys, only
      the confirmed-lending rows flip `liquidation`→`lending`, every other column/row byte-identical). Add unit tests
      covering the classification + dry-run + apply paths.
- [ ] [DATA] P1. Ship the script + tests via `quickmerge.sh --agent --files` (quality-gates.sh green first, per repo
      convention); verify the commit lands as an ancestor of `origin/live-defi-rollout`.
- [ ] [OPERATOR] P1. Obtain operator authorization for a paused-writer apply window (mirrors the venue-as-chain
      2026-07-22 pause/impersonation/resume recipe): identify + pause the relevant MTDS manifest-consolidator cron, run
      `restamp_lending_instrument_type_2026_07_24.py --apply`, confirm the post-write verification output, then resume
      the cron and confirm `state=ENABLED`. This is the human-only / operator-gated step — do not execute the pause or
      the `--apply` write without explicit operator authorization, per this plan's inherited destructive-beyond-local
      precedent.
- [ ] [DATA] P2. Post-apply: confirm the distinct-values panel (`GET /distinct-values/defi`) no longer badges
      `liquidation` as a non-canonical/unexpected `instrument_type` value stamped by this writer path (re-pull the live
      nightly honest-coverage rollup and diff against the pre-apply baseline); cross-link the result back into
      `/plans/active/distinct_values_noncanonical_audit_2026_07_20.md`'s Progress Log, and close out this plan.

## Progress Log

### 2026-07-24 — forked out of the parent audit

Forked out of `/plans/active/distinct_values_noncanonical_audit_2026_07_20.md` per an explicit operator rescope decision
(that plan was ~1627 lines and needed a size-cap split). Only this MTDS lending-instrument-type historical-restamp
workstream was forked — it is the one genuinely open, unscoped-into-concrete-todos item left on the parent. The parent's
own already-completed RESTAKING `InstrumentType` workstream is NOT forked (fully shipped and git-verified done
2026-07-22 — historical record only, not open work) and stays in place there. No code has been written or executed for
this workstream yet; the 5 todos above are the first concrete breakdown of the narrative description that lived on the
parent plan's line ~437 ("Writer half fixed... DEFERRED: historical manifest rows...") and line ~151-167 ("Still open —
one writer fix is only HALF done...").
