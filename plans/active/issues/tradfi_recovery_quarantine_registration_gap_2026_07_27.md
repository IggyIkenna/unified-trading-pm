---
doc_type: issue
title:
  "TradFi garbage-underlying recovery (2026-07-20): 428 content-recovered rows never registered under their real root +
  the run's own _quarantine/ physical mirror is now stale"
summary:
  While correcting the live tradfi availability_index for the 2026-07-20 garbage-underlying recovery run's 98,256
  processed rows (tradfi_satellite_ao_dispatch_batch2_2026_07_25.md item "Correct the live tradfi availability_index
  manifest for the ~97,828 combo/chain objects"), found that the run's own summed apply_outcomes.json Counters split
  cleanly into 97,828 genuinely-quarantined + 428 content-recovered-and-merged-elsewhere (97,828 + 428 == 98,256
  selected, 0 unaccounted). The 428 recovered rows' DATA now lives under a different (real) product root, but no NEW
  manifest row was ever registered for that root — the recovery script has no ManifestWriter call at all. Separately,
  verified the run's physical `_quarantine/` mirror for these 98,256 rows no longer exists on GCS today (only 9
  unrelated `day=2026-01-*` prefixes remain under `_quarantine/raw_tick_data/`, from a different quarantine event) — so
  a live GCS existence check can no longer disambiguate the two outcomes at the row level; only the retained TSV +
  apply_outcomes.json artifacts remain authoritative.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, manifest, recovery, registration-gap, data-correctness]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: tradfi_master
source:
  "tradfi_satellite_ao_dispatch_batch2-012 (Correct the live tradfi availability_index manifest for the ~97,828
  combo/chain objects), 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: ""
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# TradFi garbage-underlying recovery: 428 recovered rows unregistered + stale quarantine ground truth

## What I found

Working `tradfi_satellite_ao_dispatch_batch2-012` (correct the live tradfi `availability_index` manifest for the
`recover_tradfi_garbage_underlying_2026_07.py --apply` run `20260720-120911`), I downloaded and summed all 20 shards'
retained `recovery_mapping.tsv` + `*.apply_outcomes.json` artifacts (never a fresh GCS walk — per the plan's own
instruction). Two findings:

1. **428 rows were content-recovered, not quarantined, and were never registered under their real root.** The run's
   `A_QUARANTINE` category total across all 20 shards is 98,256; the summed `attempted_failed` outcome is exactly
   97,828; the summed `RECOVERED:*` outcome is exactly 428; 97,828 + 428 == 98,256 with zero unaccounted/error outcomes.
   `recover_tradfi_garbage_underlying_2026_07.py` has no `ManifestWriter` call anywhere in it (verified via full read),
   so neither branch ever touches the manifest. The 97,828 genuinely-quarantined rows are the ones this task's
   manifest-correction script (`correct_tradfi_recovery_quarantine_manifest_2026_07_27.py`) marks `attempted_failed` —
   but the 428 recovered rows' real, content-resolved data now sits in a canonical bundle under a DIFFERENT root with NO
   manifest row of its own. This mirrors the exact gap `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s
   register phase already fixes for a DIFFERENT raw-underlying corpus (per-contract Databento symbols stored raw in
   `underlying=`) — the same register-then-verify pattern would apply here, just against this recovery run's 428-row
   population instead.

2. **The run's physical `_quarantine/` mirror for these 98,256 rows is gone.** I initially designed the
   manifest-correction script to disambiguate the 97,828-vs-428 split via a targeted `gcs_describe_object` existence
   check against each row's quarantine target (`_quarantine/<original_rel>`) — mirroring
   `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s `confirm_targets_on_gcs` pattern. Live-verified
   2026-07-27: 0/98,256 targets exist. Listing `_quarantine/raw_tick_data/by_date/` (non-recursive, bounded — not a
   corpus walk) shows only 9 `day=2026-01-*` prefixes today, holding a DIFFERENT population entirely
   (`underlying=CME:OPTION:EW1-USD-260102-...@LIN` — a full instrument id stored as `underlying=`, not the
   numeric/opaque garbage codes this run processed). No bucket lifecycle rule explains this (only a 60-day Coldline
   storage-class transition; no auto-delete rule). Some unrelated, unidentified later operation evidently reused or
   pruned `_quarantine/raw_tick_data/` since 2026-07-20. Net effect: going forward, the retained TSV/JSON artifacts are
   the ONLY surviving ground truth for this run's outcome split — the live bucket can no longer corroborate it.

## Why it matters

Finding 1 is a small (0.44%), bounded, always-fixable-later data-visibility gap: 428 tradfi combo/chain cells have real
captured data sitting under a canonical bundle with no manifest row pointing at it, so a consumer querying by that real
root would see it as `todo`/missing rather than `captured`. Finding 2 means this specific disambiguation opportunity is
now closed — any future attempt to split this population by physical GCS state will get the same false "nothing
confirmed" result. Not urgent (finding 1 is additive-only, no destructive risk; finding 2 is a closed door, not an open
wound), but should be tracked rather than silently absorbed.

## Recommended decision

- [x] ✅ [SCRIPT] P2. Write a register-phase script (mirroring
      `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s register phase) that: for each of the 428
      `RECOVERED:*` rows implied by this run's per-shard `apply_outcomes.json` (the aggregate count is known; deriving
      the EXACT 428 keys requires either re-deriving the recovered root from the CURRENT canonical bundle's content — a
      targeted read per candidate combo/chain cell already resolved by the sibling migrate/rebundle tooling — or
      accepting that the exact 428 keys are unrecoverable and instead doing a targeted sweep: for every `A_QUARANTINE`
      TSV candidate whose OLD key is NOT registered `captured` anywhere, check whether a real-root canonical bundle
      exists for its (day, venue, instrument_type, data_type) tuple and, if so and no manifest row exists for that
      canonical key yet, register one additively (no CAS, mirrors `ManifestWriter.add()`/`per_vm_shards=True`)),
      confirms via targeted (never corpus-walking) `gcs_describe_object` checks, and additively registers the missing
      canonical rows. Repo: market-tick-data-service. **Done when**: every canonical bundle target reachable from this
      run's 98,256-row population that (a) physically exists on GCS today and (b) has no manifest row yet, is registered
      `captured`; count of newly-registered rows reported against the ~428 expected upper bound. —
      market-tick-data-service@c1e1de71: shipped `register_tradfi_recovery_quarantine_manifest_2026_07_30.py` (13 unit
      tests green, full quality-gates.sh clean). Implements the SWEEP alternative (the exact 428 keys are unrecoverable
      per the finding above — the run's own retained artifacts carry no per-row outcome, only the path-based A-category
      and the aggregate Counter): dedups the 98,256 A_QUARANTINE rows to their distinct
      (date,venue,instrument_type,data_type) cells, sweeps every recognised real product root per cell (excluding roots
      already keyed in the live manifest), confirms each candidate target via targeted `gcs_describe_object`, and writes
      a dry-run mapping TSV (`--apply` for the additive write). NOT yet executed against prod GCS — that dry-run +
      `--apply` pass is tracked as a new follow-up todo below (VM-scale I/O, out of scope for an interactive session per
      the heavy-I/O HARD RULE).
- [x] ✅ [SCRIPT] P2. Run `register_tradfi_recovery_quarantine_manifest_2026_07_30.py` (market-tick-data-service)
      against prod: first a dry-run (`--out register_mapping.tsv`, no `--apply`) and inspect the confirmed-candidate
      count against the ~428 upper bound + spot-check a sample of the mapping TSV's `target_uri` column for a real
      captured bundle; then, once the dry-run count looks sane, `--apply` (additive `ManifestWriter.add()`/
      `record_captured_from_counts()`, no CAS — safe to re-run) to register the confirmed rows, sharded
      (`--shard-of`/`--shard-index`) if the unsharded dry-run's candidate-key count makes a single-process
      `gcs_describe_object` sweep impractically slow. Repo: market-tick-data-service. **Done when**: the dry-run mapping
      TSV + confirmed count are reported, the `--apply` run completes, and a post-run spot-check confirms a sample of
      the newly-registered canonical keys read `captured` in the live manifest. — **Dry-run**: 248/585,331 candidates
      confirmed present on GCS (within the ~428 upper bound; 6,797 distinct cells x 144 recognised roots), 2
      independently spot-checked `target_uri`s confirmed real content on GCS. **Apply**: 248 canonical rows registered
      into `_index/per_vm/local-2108856-43a6.parquet` (additive, no CAS). **Data-correctness finding + remediation**
      (see `/plans/active/issues/tradfi_register_underlying_translation_bug_2026_07_30.md`): 98/248 (39.5%) of the
      written rows carried a manifest `underlying` that did NOT match the `underlying=` segment of the row's own
      physically-confirmed GCS path (chain instrument_types translate the root through `_exchange_to_product_root` when
      building the target path, but `apply_register` wrote the untranslated root). Caught BEFORE the
      manifest-consolidator cron merged the shard (main index `updateTime` 12:00:59 UTC, shard write 12:06:04 UTC,
      caught+patched by 12:10 UTC) — hand-patched the shard in place via a generation-CAS read-modify-write, verified 0
      remaining mismatches across all 186 affected cells. Root cause fixed at market-tick-data-service@35d1f328 (added
      `actual_underlying` to `RegisterCandidate`, used in both `apply_register` write branches; 4 new regression tests,
      19 total unit tests green). Also fixed an unrelated pre-existing QG-blocking failure (stale `SPORTS` shard-count
      pin, verified against `unified-api-contracts` commit history as a legitimate re-pin, not a regression) at
      market-tick-data-service@b4fd439e so both commits could ship. Full `quality-gates.sh` clean on both.
- [ ] [DATA] P3. Investigate what pruned/reused `_quarantine/raw_tick_data/` between 2026-07-20 and 2026-07-27 (only 9
      unrelated `day=2026-01-*` prefixes remain, from a different quarantine event — full instrument-id-as-underlying,
      not this run's numeric/opaque garbage codes). Not urgent (no destructive-risk signal found — no lifecycle
      auto-delete rule on the bucket), but the mechanism is currently unidentified and could recur for other in-flight
      quarantine passes. Repo: market-tick-data-service (or infra, if traced to a shared migration/cleanup script).
      **Done when**: root cause identified (which script/run touched `_quarantine/raw_tick_data/` and when) or
      documented as unable-to-determine with the evidence gathered.
