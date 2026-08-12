---
doc_type: plan
title: >-
  Retire legacy POOL / rate_indices / dex_pool_fees manifest rows post-rebuild, trigger a fresh honest-coverage rollup,
  and re-check the Distinct Values panel
summary: >-
  Extracted from `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos section — every judgment call
  this work depended on is now resolved (POOL/rate_indices/dex_pool_fees scope confirmed, the retirement pattern already
  proven twice on dex_pools/dex_swaps, the blocking rebuild VM's OOM root-caused and fixed) so the remaining steps are
  bounded, determinable, mechanical. `status: draft` until the rebuild VM (currently
  `canonical-migration-defi-rebuild-20260810-093118` or its latest successor) reaches genuine terminal SUCCESS — flip to
  `active` only then; a draft plan is not ingested, so this avoids an AO worker claiming a todo whose precondition isn't
  met yet.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, manifest, retirement, pool-casing, rate-indices, dex-pool-fees, honest-coverage, distinct-values]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
sequential: true
source: >-
  Interactive `/autonomous` session 2026-08-10, operator asked to flip the remaining well-scoped todos to an AO plan
  ("can we flip this to ao plan and tasks since the rest of the todos are clearly known").
---

# Retire legacy POOL / rate_indices / dex_pool_fees rows, refresh honest coverage, re-verify the panel

## Why `status: draft`

Every todo below reads live state before acting and is genuinely mechanical — but the retirement steps (todos 2-4) are
UNSAFE against a still-moving-target manifest: the `canonical-migration-defi-rebuild-*` VM chain has already OOM'd twice
on this exact prefix (see the related OOM issue doc), and a direct-CAS full-index-rewrite retirement racing an
actively-merging consolidator risks retiring an incomplete/stale snapshot. Flip `status: draft` → `active` only once
`canonical-migration-defi-rebuild-20260810-093118` (or whatever superseded it) has reached a genuine terminal
**SUCCESS**, not just any terminal state — todo 1 below re-verifies this itself as its own first action, since a worker
picking this plan up cold should never trust the flip-time state without a fresh check.

## Todos

- [x] ✅ [DATA] P1. **Verify the rebuild VM reached terminal SUCCESS + confirm POOL/rate_indices/dex_pool_fees counts
      are STABLE.** — unified-trading-pm (verification-only, no code). Latest successor VM
      `canonical-migration-defi-rebuild-20260810-204358` reached genuine terminal SUCCESS: `run.log` shows
      `Rebuild complete:` for the final chunk (`2026-08-25..2026-11-22` then `2026-11-23..2026-12-31`, both empty —
      corpus exhausted), `REBUILD_DEFI_MANIFEST_RUN_COMPLETED`, `[vm-exec] command exited rc=0`, deployment archived
      `status=completed exit_code=0`, then self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`). 3 live
      `read_availability_index()` queries (17:37:xx, 17:38:xx, 17:43:41 UTC 2026-08-11 — spanning the required ~5min)
      against the freshly-consolidated index blob (confirmed fresh via `get_blob_metadata()`,
      `last_modified=2026-08-11T17:33:39Z`) returned IDENTICAL counts every time: `instrument_type=POOL`
      (`dex_pool_swaps`) = 7,930,863; `data_type=rate_indices` `captured` = 26,128; `data_type=dex_pool_fees` `captured`
      = 21 (out of 39,349,334 total `captured` rows). Done-when met: VM terminal SUCCESS + all 3 counts stable. STOP
      clause not triggered.

      Note for todo 2's worker: the direct pandas `read_availability_index(columns=..., filters=[("capture_status",
                              "==", "captured")])` path OOM'd repeatedly (killed at 8G/16G/24G RSS caps, then again unwrapped) even against the
                              fresh consolidated blob — decoding 39M captured rows into a DataFrame is itself too heavy. Query via a streaming
                              DuckDB aggregate over a locally-streamed copy instead (`client.download_file()` + `duckdb.read_parquet()` +
                              `COUNT(*) FILTER (...)`), not a pandas `read_availability_index()` call — bounds memory to DuckDB's own
                              streaming footprint regardless of corpus size.

- [x] ✅ [DATA] P1. **Root-cause the 0→7,930,863 `instrument_type=POOL` recurrence before any retirement resumes**
      (blocks the retirement todo below — main-agent-added 2026-08-11 per
      `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`, BLK-e7fe6971 answered A). Confirm
      the rebuild VM's actual deployed code content (`cloudbuild`/tarball manifest `commit_sha`) to rule in/out a stale
      pre-N6a snapshot. (repo: market-tick-data-service) — unified-trading-pm (verification-only, no code). **Stale
      pre-N6a snapshot theory RULED OUT.** See Progress Log for evidence.
- [x] ✅ [DATA] P1. **Determine whether the manifest rebuild is full-replace or upsert-onto-existing-index** (same
      recurrence investigation). Read `rebuild_defi_manifest.py`'s top-level `main()`/index-write path — if upsert, any
      pre-existing uppercase rows that survived the 2026-08-05 fold would pass through untouched rather than being
      reintroduced by the rebuild. (repo: market-tick-data-service) — market-tick-data-service@`current HEAD`
      **VERDICT: UPSERT-onto-existing-index, NOT full-replace.** See Progress Log for the three lines of evidence.
- [ ] [DATA] P1. **Sample the 7,930,863 uppercase rows' underlying GCS objects directly**
      (`gcs_describe_object`/`list_blobs` under `instrument_type=POOL/`) to settle whether this is a
      manifest-column-only artifact (as the 2026-08-05 fold assumed) or genuinely reflects physical objects at an
      uppercase path — the latter needs the Part-5 "legacy COPIED not MOVED" migration treatment
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1 Part 5), not a manifest-only patch. Once (1)-(3)
      above are understood, re-evaluate whether the retirement todo below is safe to attempt (also still gated on
      slot-31's separate wrapped-id content-verify blocker). (repo: market-tick-data-service)
- [ ] [DATA] P1. **Pause the DeFi manifest consolidator cron, retire POOL (uppercase `instrument_type`) legacy
      `captured` rows in `dex_pool_swaps` via the proven reversible `capture_status: captured→attempted_failed`
      pattern.** Mirror `retire_dex_pools_legacy_captured_rows_2026_08_05.py` /
      `retire_dex_swaps_legacy_captured_rows_2026_08_09.py` (both `market-tick-data-service/scripts/one_offs/`). Pause
      `uts-prod-manifest-consolidator-market-data-defi-cron` (`asia-northeast1`) before writing, resume after.
      Done-when: a fresh `read_availability_index()` query shows 0 remaining `captured` rows with
      `instrument_type=POOL`. (repo: market-tick-data-service) — **NOT DONE, blocked on a genuine content-verify gap
      found live 2026-08-11 (slot 31) — see Progress Log for full evidence.** Wrote
      `retire_pool_uppercase_legacy_captured_rows_2026_08_11.py` (`market-tick-data-service@85677ff363`) mirroring the
      sibling scripts' reversible pattern, but the canonical `pool` (lowercase) population turned out to be itself mixed
      (a genuine subset still carries the full legacy wrapped id verbatim, not a clean bare-id rename) — a simple
      twin-match cannot safely tell "real bare-form canonical twin" from "same-string mislabeled duplicate" apart. 0
      rows retired, no manifest write executed (the script's own safety gate correctly excluded all 1,135,962 candidate
      keys rather than guess). Needs a content-verify pass (read actual swap data, not just id strings) before this todo
      can safely proceed.
- [ ] [DATA] P1. **Retire `rate_indices` legacy `captured` rows** (fold already GENUINELY 100% COMPLETE 2026-08-07 per
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 4 — this is the retirement half only, never
      done). Same reversible pattern + consolidator pause/resume as the prior todo (share the pause window if run
      back-to-back). Done-when: 0 remaining `captured` legacy `rate_indices` rows. (repo: market-tick-data-service)
- [ ] [DATA] P2. **Verify + retire `dex_pool_fees` legacy `captured` rows if any remain** (tiny scope — a prior read
      noted ~21 rows on the axis-census panel before that panel's `attempted_failed` filter fix; the corpus itself was 0
      real objects for its whole lifetime, phantom manifest rows only). Confirm the count live first — if 0, mark this
      todo done-with-nothing-to-retire and move on; if >0, same reversible pattern as above. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Resume the consolidator (if not already), trigger a fresh `measure_honest_coverage.py` rollup run**,
      and confirm it completes cleanly (the enumeration-key fix shipped `instruments-service@8b59e8ba2` this session
      must be live in whatever image/VM runs the rollup — verify before trusting output). Launcher:
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` or the existing scheduled job, whichever this
      workspace currently uses for on-demand triggers — check the launcher registry rather than guessing. Done-when: a
      new `coverage.json` is written with a timestamp after this todo's retirements. (repo: instruments-service)
- [ ] [DATA] P1. **Re-check the Distinct Values panel post-rollup.** Confirm: `dex_pools`/`dex_swaps`/`rate_indices`/
      `dex_pool_fees` no longer appear as non-canonical `data_type`s; `POOL` (uppercase) no longer appears as a
      non-canonical `instrument_type`; venues drop to the genuinely-unresolved set (ASTER/GMX/HYPERLIQUID/EXTENDED/
      LIGHTER + the 24 composite `VENUE-CHAIN` venues, which are CORRECTLY flagged-but-accepted per this epic's prior
      false-alarm investigation, not a bug); `instrument_types` clean modulo the small genuine `<blank>` gap (~58
      `captured` rows, not the ~5.3M raw count — that count is a KNOWN, separately-tracked panel over-report, see
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos). Record the live counts in this plan's
      Progress Log. (repo: unified-trading-pm)

## Progress Log

- **2026-08-11 (slot 31, data_engineering) — todo 2 attempted, NOT completed: canonical `pool` population is itself
  mixed, a simple casing-unwrap twin-match is unsafe.** First hit a real OOM (exit 137) using a bare
  `pandas.read_parquet(BytesIO(...), filters=...)` against this manifest (7.16GB raw, 158.3M total rows) — confirmed
  host recovered clean (`free -h`: 28GB available after), then redid every subsequent query via
  `run-bounded-analysis.sh` + DuckDB streaming as todo 1's own note already recommended (should have started there).
  Sampled `instrument_id` shapes for `instrument_type=POOL` (legacy, uppercase) vs `pool` (canonical, lowercase) within
  `data_type=dex_pool_swaps`: **legacy `POOL` is 100% wrapped-form** (`VENUE-CHAIN:POOL:id`, e.g.
  `AERODROME_V3-BASE:POOL:0xf8d5df4d3408acd52a3ff54e8dbce0b3b28aa744`) — ALL 7,930,863 captured rows contain a colon.
  **Canonical `pool` is MIXED**: of ~8.75M captured rows, `contains_colon`=5,361,579 (still carrying the full wrapped
  legacy-shaped id string VERBATIM, uppercase `POOL` token embedded and all — i.e. only the outer `instrument_type`
  column was casing-normalized at some point, the id itself was never re-derived) vs `no_colon`=3,391,479 (genuinely
  bare — hex address or bare symbol pair like `WEETH-WETH-1`). Wrote
  `retire_pool_uppercase_legacy_captured_rows_2026_08_11.py` (`market-tick-data-service@85677ff363`) mirroring the
  sibling scripts' Pass-1/Pass-2 reversible pattern (`captured→attempted_failed`, snapshot-before-write, round-trip
  verify), unwrapping canonical ids to the segment after the last `:` to compare against legacy's bare id — the same
  "wrong vocabulary" pattern `retire_dex_swaps_legacy_captured_rows_2026_08_09.py` already solved for a DIFFERENT
  population. A first isolated DuckDB probe (against a since-superseded manifest snapshot, the consolidator actively
  merges every few minutes) found 0 missing twins across 1,135,962 legacy keys; a full-corpus dry-run minutes later
  against a FRESH download found the opposite — ALL 1,135,962 keys excluded, 0 retirable — illustrating exactly the
  moving-target risk this plan's own `status: draft` rationale warned about, and confirming the population genuinely is
  mixed (not a stale-read artifact): the wrapped-form subset of "canonical" `pool` rows can never match my
  unwrap-last-segment key scheme since they're not actually in bare form. **Did not loosen the matching logic to force a
  match** — that would risk either quietly leaving true duplicates un-retired (harmless) or, worse, misclassifying a
  wrapped-form `pool` row that is NOT truly a duplicate of legacy `POOL` (different real data sharing a
  coincidentally-similar id string) as safe-to-retire, an irreversible-class judgment call on real financial data under
  time pressure — exactly the class of mistake `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`'s Part 2
  (content, not path/label) exists to prevent, even though this is a manifest-status flip rather than a GCS delete. **0
  rows retired, no manifest write executed** — the script's own Pass-1 safety gate is working exactly as designed.
  **What's needed next**: a genuine content-verify pass (read actual swap/price data for a sample of wrapped-form
  "canonical" `pool` rows vs their legacy `POOL` counterpart) to determine whether the wrapped-form `pool` subset is (a)
  a partial, incomplete casing migration that still needs its ids re-derived to bare form before this retirement can
  proceed, or (b) something else entirely. Filed as the blocking gap on the checkbox above rather than a separate issue
  doc — same doc, same todo, narrower scope than a new investigation needs.
- **2026-08-11 (slot 33)**: Todo 1 done. Rebuild VM `canonical-migration-defi-rebuild-20260810-204358` confirmed
  terminal SUCCESS (see checkbox evidence above). Stability-check counts (identical across 3 queries, 17:37:xx →
  17:43:41 UTC): `instrument_type=POOL` (`dex_pool_swaps`) = 7,930,863; `data_type=rate_indices` `captured` = 26,128;
  `data_type=dex_pool_fees` `captured` = 21. These are the baseline pre-retirement counts todo 2-4's workers should
  expect to drive to 0.
- **2026-08-11 (slot 4, data_engineering) — todo 2 still NOT DONE; filed a SECOND, independent blocking finding on top
  of slot-31's content-verify gap.** While researching how to safely resolve slot-31's wrapped-id matching problem,
  traced whether the 7,930,863 uppercase `POOL` rows todo 1 measured are consistent with what's known about this
  population's history — they are not. `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` P3 recorded a
  full-corpus-verified **0** `instrument_type=POOL` rows remaining as of 2026-08-05 (after
  `fold_pool_instrument_type_casing_2026_08_05.py --apply`). Ruled out the two obvious explanations for the 0→7.9M
  regrowth by direct code read (not inference): the only live `record_captured` call site for `dex_pool_swaps`
  pool-grain rows (`_dex_swaps_queries.py:174-182`) passes lowercase `instrument_type="pool"` with a bare id — not a
  regression; and `rebuild_defi_manifest.py::parse_hive_path` unconditionally lowercases `instrument_type`
  (`market-tick-data-service@3f5cc6e4`, shipped 2026-06-18, well before the just-completed rebuild VM chain) — so the
  rebuild's own path-parsing logic shouldn't be able to reproduce this either. **Mechanism for the recurrence is
  UNRESOLVED** — filed as `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` (also corrected
  the now-stale P3 "0 remaining, no further action needed" claim in the contamination issue doc, which is directly
  contradicted by this). Retiring the 7.9M rows again without understanding why they came back once already risks the
  same "fixed, then silently reverted" cycle repeating a third time. Did not attempt retirement this session — filed as
  a big finding (data-correctness, SSOT contradiction) per CLAUDE.md's findings-triage rule rather than absorbing an
  open-ended root-cause investigation as unplanned scope on a task scoped to "retire POOL rows." Recommend the
  operator/main review the new issue doc's 3-point verification list before todo 2-4 are attempted again.
- **2026-08-12 (slot 5, data_engineering) — todo 2 done: stale pre-N6a snapshot theory RULED OUT.** Read
  `vm-logs/<vm>/TARBALL_PINS.json` for both VMs in the `-093118`→`-204358` chain (GCS reads via UTL
  `download_from_storage`, per the storage-code HARD RULE): the OOM'd predecessor `-093118` had `MTDS_TARBALL_SHA`
  PINNED to `483eb895581cc645cf884ba780c871b65060202d` (well past N6a); the VM that actually reached terminal SUCCESS,
  `-204358`, had `MTDS_TARBALL_SHA` FLOATING (`"pins": {}`) — no per-deployment record captured the exact commit_sha it
  resolved to at launch (2026-08-10T19:43:58Z), a genuine observability gap in `create-code-tarballs.sh`'s
  floating-tarball path (not fixed here — infra-craft scope, flagged below). Since a floating tarball is built from
  whatever `market-tick-data-service` HEAD is checked out when `create-code-tarballs.sh` last ran, the relevant question
  is whether the N6a lowercasing fix (`market-tick-data-service@3f5cc6e4`, 2026-06-18) was EVER reverted between then
  and the VM's 2026-08-10 launch. `git log 3f5cc6e4..HEAD -- market_tick_data_service/scripts/rebuild_defi_manifest.py`
  lists every commit touching this file in that window (12 commits, none of them touching the `parse_hive_path`
  lowercasing lines); confirmed directly at HEAD (`market-tick-data-service@859405a1`, the tarball commit_sha as of
  2026-08-11T23:00:56Z — after the VM launch, used as the nearest-available content proof): both
  `instrument_type=p["itype"].lower()` call sites in `parse_hive_path` (lines 370, 395) are intact, unconditional,
  unchanged. **Conclusion: no floating-tarball snapshot in the 2026-06-18→2026-08-11 window could have shipped pre-N6a
  code — the stale-snapshot theory from the issue doc's "what I did NOT verify" #1 is RULED OUT.** This narrows the
  still-unresolved recurrence mechanism to the issue doc's remaining two open questions (full-replace vs. upsert;
  physical uppercase GCS objects vs. manifest-column-only) — those are this plan's next two todos, not re-litigated
  here. Updated `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` to mark this question
  resolved. **Follow-up flagged, not filed as new work** (small, non-blocking, outside this plan's `data_engineering`
  scope): `create-code-tarballs.sh`'s floating-pin path should persist the resolved `commit_sha` into
  `TARBALL_PINS.json` at launch time (mirroring the pinned-tarball case) so a future audit doesn't have to reconstruct
  it from git history — worth an infra-craft todo if this pattern comes up again.
