---
doc_type: issue
title: >-
  Candle canonical-path migration — operational history, part 2 of 2 (2026-07-22 to 2026-07-23): P6 drain, P7 per-AG
  SPOT --apply (DEFI/PREDICTION/CEFI/TRADFI), P8 cross-AG verify/reconcile — extracted from
  candle_feature_canonical_path_divergence_2026_07_20.md
summary: >-
  Companion history doc (part 2 of 2) to /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md —
  the verbatim Progress Log narrative (2026-07-22 P6 drain through 2026-07-23 P8 verify/reconcile) extracted for
  line-cap compliance (plans/active/task_template.md §3 finding J, plans/active/issues/*.md 1000-line hard cap — the
  combined narrative itself exceeded 1000 lines, hence the 2-part split). Covers: the P6 drain/snapshot (including the
  JIT-redrain lessons); the full P7 per-AG SPOT --apply sequence for DEFI, PREDICTION, CEFI (2 SPOT preemption bursts, a
  149-object permanent KEPT_SRC residual root-caused to a genuine `_copy_verify_delete()` retry-idempotency gap, now
  tracked as the parent's todo 19), and TRADFI (3 severe SPOT-preemption storms survived, 0 outstanding); and the P8
  cross-AG verify/reconcile (all 4 AGs independently confirmed clean, TRADFI's ~7.1M-object quarantine residual
  precisely quantified as the parent's todo 3). Continues from part 1
  (/plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md). Zero open todos of its
  own — the parent issue doc remains the single live source of truth for every still-open todo (2, 3, 7, 9, 13, 15, 16,
  19).
status: resolved
nature: record
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service, features-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    canonical,
    gcs-paths,
    manifest,
    candles,
    features,
    migration,
    mdps,
    volatility,
    history,
    progress-log,
  ]
related:
  [
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  plan-hygiene line-cap remediation 2026-07-25 (extraction is the resolution — this is a closed, historical Progress Log
  narrative preserved verbatim for context; the parent issue doc remains the live source of truth for any still-open
  todos)
source: >-
  Extracted 2026-07-25 from plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md (1453 lines, over
  the plans/active/issues/*.md 1000-line hard cap, scripts/plan-hygiene/check_line_caps.sh) per the established
  extract-to-archive-bound-history-child pattern (plans/active/issues/plan_line_cap_remediation_2026_07_23.md's FINAL
  RESOLUTION section); split into 2 parts because the combined extracted narrative (1088 lines) itself exceeded the cap.
  Verbatim Progress Log content in original document order — no checkbox lines were excised from this half (the
  relocated todo-11/12/13/14/15 and todo-16/19 lines all fall within part 1's content range).
---

# Candle canonical-path migration — operational history, part 2 of 2 (2026-07-22 to 2026-07-23)

> **🟢 RESOLVED 2026-07-25 — ACKED-INTO-CODE** — extraction is the resolution (closed, historical Progress Log
> narrative; the parent issue doc remains the live source of truth for any still-open todos); archived per the
> terminal-status backlog sweep.

> **Companion history doc, not the live plan (2 of 2).** This holds the second half of the verbatim Progress Log
> narrative extracted from `/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md` — continues
> from part 1 (`/plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md`) starting at
> the P6 drain. Nothing below was rewritten; it remains the verbatim historical record, in original document order (no
> checkbox lines needed relocating from this half — all relocated todos fall within part 1's content range). The parent
> issue doc remains the single live source of truth for the Findings/Corrected-Ruling/Decision/LOCKED-shape sections and
> for every still-open todo (2, 3, 7, 9, 13, 15, 16, 19).

### 2026-07-22 — ✅ P6 DONE, P7 STARTED: operator authorized full P6→P7→P8, `/autonomous` invoked, DEFI real `--apply` canary SUCCEEDED (200/200 MIGRATED, hard-verified on real GCS)

**Governing authorization** (do not re-ask, per `/autonomous`'s rule 2 — decide and document): operator's exact
instruction this session — _"do this stop all VMs both clouds → snapshot → sequenced SPOT --apply migration+purge across
~10.9M objects, defi→prediction→cefi→tradfi → verify/reconcile"_ — followed immediately by `/autonomous` (apply
`cursor-configs/AUTONOMOUS_AGENT_RULES.md` + drive to completion on a loop, full authority for the infra ops this plan
labels operator, never stop at the first natural break). This is the standing authorization for everything below and
everything still to come (P7 for prediction/cefi/tradfi, P8) — a fresh session should NOT re-request confirmation for
continuing this exact sequence.

**P6 drain — scope decision (documented per rule 2, not asked)**: "stop ALL VMs both clouds" was interpreted as scoped
to VMs that write to/read the 4 target asset_groups' data (defi/prediction/cefi/tradfi), not the entire compute fleet —
stopping e.g. `footystats-fwd-*` (sports, disjoint `processed/` root) or `vm-zombie-watchdog-*` (fleet health
monitoring) would be over-broad and outside this migration's actual write-contention concern. AWS side: confirmed via
`aws ec2 describe-instances` — only `agent-orchestrator-vm-1` and `agent-orch-human-planning-vm` running, both
orchestrator infra, zero data-pipeline VMs — AWS was already clear. GCP side, stopped (via
`gcloud compute instances stop`, confirmed TERMINATED before proceeding): `canonical-migration-defi-per-instrument-*`
(DEFI raw-tick migration, writes DEFI manifest), `pyth-lst-backfill-*` (CEFI raw-tick backfill),
`datapoint-validation-tradfi-*`, `orphan-sweep-{cefi,defi,prediction}-*` (read-only reconciliation sweeps, stopped
anyway for a clean baseline).

**LESSON — the drain is NOT durable across a multi-hour operation**: re-checked GCP ~1h after the initial drain and
found several of the same VMs had respawned — `canonical-migration-defi-per-instrument-20260722-164109`,
`orphan-sweep-defi-20260722-161453`, `datapoint-validation-{cefi,defi,prediction}-20260722-15xxxx`,
`pyth-lst-backfill-20260722-151120`. Investigated: these are on independent scheduled crons (~7-11h cadence based on the
gap between the stopped instance and its respawn), NOT a watchdog "undoing" the manual stop (a plain
`gcloud compute instances stop` is not a SPOT-preemption event, so `RelaunchPreemptedVm`'s auto-recover path does not
fire on it). **Adopted a just-in-time re-drain pattern**: re-check + re-stop the in-scope VMs immediately before each
AG's real launch, rather than assuming one upfront drain holds for the whole multi-AG sequence. Residual risk is
accepted as low (disjoint object prefixes vs `processed_candles/`, per-VM manifest shards, and the candle migration's
own copy-verify-delete is idempotent/crc32c-verified regardless) but NOT zero — flagging explicitly rather than silently
assuming perfect isolation. Re-drained DEFI-specifically before the P7a launch below.

**P6 manifest consolidation**: triggered the 4 relevant Cloud Run jobs directly
(`gcloud run jobs execute uts-prod-manifest-consolidator-market-data-{defi,prediction,cefi,tradfi} --region=asia-northeast1`),
polled each to a terminal state (not fire-and-forget) — all 4 `Completed/True`, tradfi (largest) took ~5m40s, the other
3 finished within ~2min. "Snapshot" in the pre-migration-drain sense (per
`codex/02-data/gcs-and-manifest-delete-safety- protocol.md` §"Pre-delete drain") is satisfied by drain+consolidate; the
migration executor's OWN safety model (dry-run classify + 0-orphan reconcile before any write, copy→verify→delete never
deleting without a proven distinct verified copy) is the actual delete-safety mechanism, not a separate storage-level
snapshot action.

**P7 launcher: new `<ag>-candle-apply` category, 3 real bugs found + fixed via adversarial self-testing** (no subagent
available this segment — the workflow tool's weekly agent-dispatch limit was hit earlier this session, resets 2026-07-24
20:00 London; did this directly instead of waiting). Full details + exact bug mechanics are in the commit message
(`deployment-service@3af1a67`) and the 9 new `TestCandleApplyCategory` regression tests
(`deployment-service/tests/unit/test_vm_launcher_scripts.py`). Summary: (1) `DRY_RUN=true` never actually gated the real
`gcloud compute instances create` call for ANY category in this launcher, ever — a defi-candle-apply DRY_RUN=true
"preview" during testing silently created and ran a real VM (harmless only because that specific preview also happened
to pass `dry` mode internally); (2) the shard-suffixed vm_name for the longer `<ag>-candle-apply` names overflowed GCE's
63-char limit (measured worst case: `prediction-candle-apply` + 2-digit shard → 71 chars, GCE rejected the create call);
(3) fixing (2) introduced a `set -u` unbound-variable crash on the non-sharded single-VM launch path. All caught + fixed
BEFORE any real production object was touched.

**DEFI real `--apply` canary — ✅ SUCCEEDED, hard-verified on real GCS.** VM
`canonical-migration-defi-cdlap-20260722-175209` (zone `asia-northeast1-c`, self-deleted on completion per
`VM_SHUTDOWN_ON_COMPLETION=true` — will not appear in `gcloud compute instances list`), launched with
`LIMIT=200 SHARD_OF=1` + explicit SHA pins for reproducibility (`MDPS_TARBALL_SHA=c64a7dfa9d9f0689e...`,
`UAC_TARBALL_SHA=c4e1acee147a53aaf...`, `UTL_TARBALL_SHA=b0ec1da02c5fe7dfd...` — full SHAs in the commit that launched
it). Terminal `EXIT_STATUS=0`; `run.log` shows `apply COMPLETE — outcomes: {'MIGRATED': 200}` /
`shard 0/1 fully migrated cleanly (0 non-success outcomes)` — every one of the 200 sampled objects was MIGRATE
disposition (matches DEFI's census profile: overwhelmingly MIGRATE, near-zero quarantine/content-repair) and succeeded.
**Independently hard-verified** (not just trusting the script's own log) by reading the staged mapping TSV
(`gs://deployment-scripts-central-element-323112/canonical-migration-candle-apply/20260722-175209/.../ candle_apply_mapping.tsv`)
and directly `gsutil stat`-ing one real object pair on production GCS: the NEW canonical path
(`.../data_type=dex_pool_swaps/instrument_type=POOL/venue=BALANCER-ARBITRUM/BALANCER-ARBITRUM:POOL:0xd897... .parquet`)
exists (created 2026-07-22T16:59:36Z); the OLD non-canonical path (same but missing `instrument_type=`) returns "No URLs
matched" — genuinely copy→verify→delete happened, not just log claims. **DEFI's full corpus `--apply` (no LIMIT,
sharded) has NOT been launched yet** — that is the next concrete action, not yet started.

**Prior real-infra proof for DEFI** (already established earlier this session, not re-litigated): the same launcher
category in `dry` mode (accidentally launched during earlier bug-hunting, VM
`canonical-migration-defi-cdlap-20260722-162220`) ran a full real dry-run classify pass over the ENTIRE DEFI corpus and
reproduced the P0 census numbers EXACTLY (1,124,849 total, 1,123,407 MIGRATE, 1,442 QUARANTINE_CORRUPT, 0
CANONICAL_NOOP, ORPHAN=0) — confirms the classify logic is stable/reproducible and DEFI's corpus is clean (no
content-repair needed, minimal quarantine), independent of the LIMIT=200 apply canary's own result.

## Deferred work after 2026-07-22

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | State / why deferred                                                                                                                                                                                                                                      | Blocked-on                                                                                                                                                                                                                                                                              |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | ~~P0 census~~ **DONE 2026-07-22** — all 4 AGs, ~10.9M objects, ORPHAN=0 everywhere (see Progress Log entry above for the full disposition table)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Shipped (`deployment-service@865d0f9` launcher + 4 real SPOT VM runs; results in GCS, not in git — see Progress Log for exact paths)                                                                                                                      | —                                                                                                                                                                                                                                                                                       |
| 2   | ~~Todos 12/14/17/18 (prep risk items)~~ **DONE 2026-07-22** — resume checkpoint (adversarially reviewed, 4 findings fixed) + CEFI wire-symbol/KRAKEN-SPOT classifier fixes (see Progress Log entry above)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Shipped `mdps@efa559a`/`deployment-service@0ed7cf5`/`mdps@6b9ee49`, all QG-green                                                                                                                                                                          | —                                                                                                                                                                                                                                                                                       |
| 3   | ~~P6 drain/snapshot~~ **DONE 2026-07-22** — see Progress Log entry above (AWS pre-clear, 6 GCP VMs stopped, 4 manifest consolidators run to terminal)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Done, but NOT durable across the whole multi-AG operation (recurring crons respawn) — re-drain per-AG just before each real launch                                                                                                                        | —                                                                                                                                                                                                                                                                                       |
| 4   | ~~DEFI `--apply` canary (LIMIT=200)~~ **DONE 2026-07-22** — 200/200 MIGRATED cleanly, hard-verified on real GCS (see Progress Log entry above)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Shipped, proven — the P7 mechanism works end-to-end on real production data                                                                                                                                                                               | —                                                                                                                                                                                                                                                                                       |
| 5   | ~~DEFI + PREDICTION + CEFI + TRADFI full `--apply`~~ **ALL 4 AGs DONE 2026-07-22/23, P8-VERIFIED 2026-07-23** — DEFI: 1,131,814 objects processed, 0 non-success, P8 fresh count 1,123,415 = 100% `CANONICAL_NOOP`, gap fully explained (1,442 quarantine exact-match + dedup). PREDICTION: 1,165,459 objects, clean first pass, P8 fresh count 583,228 = 100% `CANONICAL_NOOP`, gap = clean 2:1 dedup. CEFI: 940,606 objects, 149 (0.016%) documented residual (todo 19), P8 fresh count 405,408, residual EXACT match (149 `SPLIT_BRAIN_DUPLICATE`). TRADFI: 7,646,831 objects, 3 severe SPOT storms survived, 0 non-success, P8 fresh count only 534,679 (7%) — path-migration itself is clean (100% `CANONICAL_NOOP`, 0 orphan) but ~7.1M objects (93%) are quarantined pending leaf-id resolution, now tracked precisely as todo 3. All 4 independently re-verified via a fresh GCS enumeration + the migration tool's own `--dry-run` classifier (not just trusting `--apply`'s self-report) | The canonical-PATH migration+purge phase (P6→P7→P8) is COMPLETE and independently verified across all 4 asset groups. Proceeded under the standing `/autonomous` authorization throughout (no new operator ask needed)                                    | This issue doc stays OPEN (not closed) — todos 2, 3, 7, 9, 13, 15, 16, 19 remain genuinely open content-level work, distinct from the path-migration this phase addressed. Todo 3 (TradFi leaf-id resolution, ~7.1M objects) is now the largest by scope — recommend operator attention |
| 6   | Todo 13 (`ProvisionalTargetIndex` bucket-key precision — cosmetic split-brain COUNT inflation) + Todo 15 (stale UTL docstring example)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | **Not done** — P3, cosmetic, doesn't affect migration safety                                                                                                                                                                                              | nobody — pick up any time, not on the critical path                                                                                                                                                                                                                                     |
| 7   | `cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` (CEFI has no registered candle SchemaContract for standalone `instrument_type=FUTURE`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **Not done** — orthogonal finding, own issue doc, own todos.                                                                                                                                                                                              | nobody — pick up any time; not on the candle-canonical migration's critical path                                                                                                                                                                                                        |
| 8   | Confirming the P5 executor's TradFi content-resolution rate against real prod parquet content (the `E1AF0_*_migrated_*` objects' `instrument_id` COLUMN shape is unverified)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **Not done** — the P0 census COUNTED the class exactly (6,487,045 `NEEDS_CONTENT_TRADFI_ID`) but did not sample/verify actual column shapes (dry-run never reads content); still needs a targeted content-read sample before trusting the resolution rate | nobody — pick up any time; a small sampled read, doesn't need a full VM                                                                                                                                                                                                                 |
| 9   | Todo 16 (investigate `24h` force-leg `off_template=29` classification — possibly a stale §3A "RAW token" docstring, same class as the data_type staleness todo 6 fixed)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | **Not done** — P3, non-blocking                                                                                                                                                                                                                           | nobody — pick up any time                                                                                                                                                                                                                                                               |
| 10  | Fresh CEFI census re-run to measure the ACTUAL post-fix QUARANTINE_CORRUPT residual (todos 14/18's fix is proven correct via regression tests on the exact real shapes, but the aggregate corpus-wide count after the fix is not yet re-measured)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Not done** — nice-to-have confidence check, not blocking (P7 `--apply` re-derives classification fresh regardless)                                                                                                                                      | nobody — pick up any time, or just let P7's own run be the measurement                                                                                                                                                                                                                  |

**Recommended NEXT session action**: DEFI is DONE — do NOT re-launch it. Move to PREDICTION next: JIT-redrain
PREDICTION-relevant VMs just-in-time (apply the TIGHTENED rule from the mid-flight-watch Progress Log entry above —
bucket match alone is not sufficient, confirm the candidate VM's object-prefix actually overlaps
`processed_candles/by_date/` on `market-data-tick-pred-{env}-{pid}` before stopping it), then launch PREDICTION's full
`--apply` (measure its own throughput/shard-count the same way DEFI's was derived — don't assume SHARD_OF=10 transfers
directly, PREDICTION's corpus size differs). **Expect the same run-1-has-stragglers-then-retry-clean pattern** — treat a
first-pass `exit=5` with a small (<0.1%) transient-503 straggler count as expected, not a failure; the retry (identical
shard-of/shard-index/SHA pins) is the proven recovery path, not a targeted resume (checkpoint state doesn't survive
`VM_SHUTDOWN_ON_COMPLETION=true` on a non-zero exit). Then CEFI, then TRADFI in that order (already-ruled sequencing,
tradfi last, ~99% id-canonicalisation), then P8 verify/reconcile. This entire sequence is already operator-authorized
(`/autonomous`) — no new confirmation needed unless something contradicts the documented intent above.

## Progress Log — 2026-07-22 (P7a-full: DEFI full `--apply` LAUNCHED, in flight, NOT YET VERIFIED)

**JIT re-drain before launch** (per item 3's lesson — recurring cron respawns): surveyed `gcloud compute instances list`
and found 3 DEFI-tagged VMs RUNNING again since the canary: `canonical-migration-defi-rebuild-20260722-193748` (writing
to `market-data-tick-defi-prd-central-element-323112/_index/per_vm/...` — SAME bucket the apply mutates),
`orphan-sweep-defi-20260722-165131` (actively enumerating the same bucket, 3.35M objects swept and counting), and
`instr-backfill-defi-targeted` (writing to `instruments-store-defi-prd-central-element-323112` — a DIFFERENT bucket,
instrument reference data not candles, mid-retry on a real backfill shard). Stopped the first two
(`gcloud compute instances stop`, zone `asia-northeast1-c`); deliberately LEFT `instr-backfill-defi-targeted` running —
it never touches the candle bucket the migration mutates, and stopping it would discard real in-progress backfill work
for no safety benefit. **Rule for future re-drains: scope to the exact bucket the migration writes, not just the `DEFI`
tag** — `instr-backfill-defi-targeted` would have been a false-positive stop under the coarser "any DEFI VM" rule from
item 3.

**Sizing the shard count from measured canary throughput** (not guessed): the canary's own `run.log` gave real numbers —
full-bucket enumeration (`gcloud storage ls -r` over all 1,124,849 DEFI candle objects) took ~168s; apply of 200 objects
at `--workers 16` took 16:59:36.015→16:59:39.286 = **3.27s for 200 objects ≈ 61 obj/s per VM**. Extrapolated single-VM
full-corpus time: 1,124,849 / 61 ≈ 5.1 hours. Chose **SHARD_OF=10** (workers left at the canary-proven 16, not bumped,
to keep the run a one-new-variable test — fleet width, not worker concurrency, is the untested lever) for an estimated
~31 min apply + ~3 min enum overhead ≈ **~34 min wall-clock**, matching the `data-pipeline-check-mdps` skill's
documented guidance that fleet width is DEFI/MDPS's dominant, unbounded lever (no Tardis-style shared-IP cap applies
here — this mutates GCS directly, no vendor fetch).

**Reproducibility — pinned to the EXACT canary-proven tarball SHAs, not fresh HEAD**: re-fetching current tarball
manifests showed MDPS and UAC had both moved forward since the canary (fresh `mdps=52afe59c...`, `uac=68c4c371...` vs
the canary's `mdps=c64a7dfa9d9f0689e13c92839e386cd45978a718`, `uac=c4e1acee147a53aaf0df4e0d8dad1289e2210f79`; UTL
unchanged at `b0ec1da02c5fe7dfd94550a9354542fc2a00fc0b`). Deliberately launched against the **canary's exact SHAs**
(confirmed those `@<sha>.tar.gz` artifacts still exist in `gs://deployment-scripts-central-element-323112/code/`) —
using fresh HEAD would have put unvalidated code into the first full-scale production run, breaking the
canary-then-scale discipline this whole effort has followed.

**Launch mechanics + a naming quirk worth recording**:
`SHARD_OF=10 bash launch-canonical-migration-vm.sh defi-candle-apply 2020-01-01 2026-07-22 full` (with the 3
`*_TARBALL_SHA` pins above) fans out one VM per shard via the launcher's internal loop, which sets
`VM_NAME_SUFFIX=shard{i}of{N}` — but this call **times out in a 2-minute foreground shell** (10 sequential
`gcloud compute instances create` calls, ~35-40s apart) before finishing; it got through shards 0-2 (named
`...{ts}-s0of10`/`-s1of10`/`-s2of10`) before being killed. Recovered by launching shards 3-9 via 7 SEPARATE invocations,
each with `SHARD_INDEX=<i>` PINNED as an env var — this is correct and safe (each VM still gets the right
`--shard-of 10 --shard-index N` baked into its python command via `_candle_apply_cmd`), but pinning `SHARD_INDEX`
externally bypasses the launcher's INTERNAL fan-out loop (which is the only place `VM_NAME_SUFFIX` gets set), so shards
3-9 got plain timestamp names with **no `-s{i}of10` suffix**. Not a correctness bug — confirmed via each VM's own
`run.log` startup command (`--shard-index N` is present and correct) — but a VM's NAME alone doesn't tell you its shard
index for these 7. **Full name→shard mapping** (confirmed for shards 3-5 directly via `run.log` grep; 6-9 inferred from
strict launch order, which matches creation timestamps):

| Shard | VM name                                                 |
| ----- | ------------------------------------------------------- |
| 0/10  | `canonical-migration-defi-cdlap-20260722-195057-s0of10` |
| 1/10  | `canonical-migration-defi-cdlap-20260722-195057-s1of10` |
| 2/10  | `canonical-migration-defi-cdlap-20260722-195057-s2of10` |
| 3/10  | `canonical-migration-defi-cdlap-20260722-195327`        |
| 4/10  | `canonical-migration-defi-cdlap-20260722-195406`        |
| 5/10  | `canonical-migration-defi-cdlap-20260722-195449`        |
| 6/10  | `canonical-migration-defi-cdlap-20260722-195524`        |
| 7/10  | `canonical-migration-defi-cdlap-20260722-195603`        |
| 8/10  | `canonical-migration-defi-cdlap-20260722-195642`        |
| 9/10  | `canonical-migration-defi-cdlap-20260722-195733`        |

(Minor P3 follow-up, not blocking: the launcher's per-invocation `SHARD_INDEX`-pinned path could set
`VM_NAME_SUFFIX="shard${SHARD_INDEX}of${SHARD_OF}"` too when `SHARD_INDEX_EXPLICIT` is set and `SHARD_OF>1`, for
consistent naming across both invocation styles — cosmetic, not tracked as a numbered todo since it doesn't affect
correctness or safety.)

**STATUS AS OF THIS WRITING: IN FLIGHT, NOT YET VERIFIED.** All 10 VMs confirmed `RUNNING` in
`gcloud compute instances list`; shards 0-2 confirmed booted cleanly (serial console shows startup script finished, task
launched) but had not yet produced a `run.log` at last check (still inside the ~3min enumeration window observed in the
canary); shards 3-5 confirmed via `run.log` grep to have the correct `--shard-index` baked in; shards 6-9 were still
booting at last check. **No shard has reached `EXIT_STATUS` yet — do not assume this run has completed.** A fresh
session (or the next `/autonomous` tick) should check
`gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/EXIT_STATUS` for all 10 VMs above before doing
anything else with DEFI candle data; if all 10 show `EXIT_STATUS=0`, hard-verify via a real `gsutil stat` sample (old
non-canonical path gone, new canonical path exists — same method as the canary) before marking this item done, updating
the Deferred table, and moving to PREDICTION.

## Progress Log addendum — 2026-07-22 (mid-flight watch: JIT-redrain rule needs a second tightening)

While polling the 10 shards' progress (all healthy — real `apply:` counters climbing, tens of thousands of objects each,
no shard preempted), `gcloud compute instances list` showed a VM I hadn't seen before:
`canonical-migration-defi-rebuild-20260722-194751`, `RUNNING`, created ~3min after I stopped
`canonical-migration-defi-rebuild-20260722-193748` (the earlier same-bucket stop from the JIT-redrain item above) and
~3min before my shard fan-out began — i.e. it looks like an automated relaunch of the exact class of VM I'd just
stopped, on the exact bucket (`market-data-tick-defi-prd-central-element-323112`) my 10 apply shards are concurrently
mutating. Investigated before touching it (never stop-first-ask-later on a live migration):

- `run.log` shows it runs
  `market_tick_data_service.scripts.rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2022-04-29 --end-date 2026-12-31`
  — scans `raw_tick_data/by_date/day={...}/(category|asset_group)=defi/` and writes ONLY to
  `_index/per_vm/canonical-migration-defi-rebuild-20260722-194751.parquet`.
- `migrate_candle_canonical_2026_07.py` operates exclusively under `CANDLE_ROOT = "processed_candles/by_date/"`
  (confirmed via grep — the script's own docstring calls out `raw_tick_data/` as the disjoint sibling migrator's
  territory, not this one's).
- **No object-level overlap**: disjoint read/write prefixes (`raw_tick_data/` vs `processed_candles/`), and the rebuild
  job's only write target (`_index/per_vm/<its-own-name>.parquet`) is never read or written by the candle apply.

**Verdict: false alarm, left running.** But this is the SECOND real near-miss this session on the JIT-redrain heuristic
(first was `instr-backfill-defi-targeted`, same-bucket-but-different-bucket that time; this time
same-bucket-same-service-family but disjoint prefix). **Tightening the rule accordingly: "same bucket" is necessary but
not sufficient — before stopping any VM found running during a JIT redrain, confirm it actually reads/writes the SAME
OBJECT PREFIX the migration's `--apply` touches** (grep the target script's root-prefix constant, as done here), not
just the bucket name or an asset_group tag. Apply this tightened check for the PREDICTION/CEFI/TRADFI JIT redrains next
— a same-bucket VM on a disjoint prefix is not a conflict and should be left alone.

## Progress Log — 2026-07-22 (P7a-full: DEFI full apply RUN 1 COMPLETE — all 10 shards exit=5, 211 stragglers, retry launched)

All 10 shards reached `EXIT_STATUS` between 19:30-19:36 UTC. **All 10 exited `rc=5`, not `0`** — this is the migration
script's own convention for "COMPLETE WITH STRAGGLER(S)", not a crash: each shard fully walked its enumeration
(`apply: N processed` reached the shard total for all 10), and the non-success outcomes are 100% transient GCS errors
during `copyTo` (`ServiceUnavailable`/`GatewayTimeout`, "We encountered an internal error. Please try again."),
consistent with backend write-QPS throttling from 10 concurrent VMs bulk-copying against one bucket simultaneously.

**Aggregate**: 1,131,814 objects processed across the 10 shards; 211 total stragglers (17-29 per shard); every straggler
breakdown is `ERROR:ServiceUnavailable`/`ERROR:GatewayTimeout` only — no `ERROR:` category indicating a real data/logic
bug. **211/1,131,814 ~= 0.019% failure rate.** Per the script's own log line: "these objects were attempted but did NOT
complete and remain at their legacy path. A re-run with the SAME --enumeration/--out/--shard-of/
--shard-index/--limit/gates is safe (idempotent) and will retry them" — data is NOT lost or corrupted, the straggler
objects simply weren't moved this run.

**Per-shard result** (VM name -> processed / stragglers):

| Shard | VM name     | processed | stragglers |
| ----- | ----------- | --------: | ---------: |
| 0     | `...s0of10` |   112,380 |         17 |
| 1     | `...s1of10` |   112,469 |         27 |
| 2     | `...s2of10` |   112,347 |         20 |
| 3     | `...195327` |   112,292 |         20 |
| 4     | `...195406` |   112,793 |         19 |
| 5     | `...195449` |   112,381 |         17 |
| 6     | `...195524` |   112,823 |         24 |
| 7     | `...195603` |   113,436 |         17 |
| 8     | `...195642` |   115,301 |         29 |
| 9     | `...195733` |   115,592 |         21 |

**Caveat found while planning the retry**: `_candle_apply_cmd`'s compound shell command only uploads `mappings/` to GCS
on the `&&`-gated SUCCESS path (`... && gcloud storage cp -r mappings/ ${stage}`) — since the python step exited
non-zero (rc=5), that upload never ran, AND `VM_SHUTDOWN_ON_COMPLETION=true` already self-deleted all 10 VMs. So the
per-run checkpoint/mapping state is NOT recoverable from GCS for a targeted "resume from exact checkpoint" retry — the
only available retry path is a fresh full-shard re-run (same as the original invocation). This is fine: `_stable_shard`
hashes by object path (not enumeration line position), so a fresh `gcloud storage ls -r` enumeration this run still
partitions objects identically, and the script's own `VERIFIED_INPLACE` classification means the ~99.98% already-
migrated objects will short-circuit as cheap existence-checks rather than being re-copied — so the retry's actual GCS
write-QPS (the likely 503 root cause) should be far lower than run 1's, since run 1 was doing ~1.13M real `copyTo` calls
and this retry only needs ~211.

**Action taken**: launched 10 retry shards (`SHARD_OF=10`, `SHARD_INDEX=0..9` explicitly pinned per invocation — same
recovery pattern as the original run's shards 3-9, run via a single backgrounded loop to avoid the foreground 2-min
timeout from the start this time), same proven tarball SHA pins (`MDPS=c64a7dfa9d9f0689e13c92839e386cd45978a718`,
`UAC=c4e1acee147a53aaf0df4e0d8dad1289e2210f79`, `UTL=b0ec1da02c5fe7dfd94550a9354542fc2a00fc0b`), `WORKERS=16`,
`MODE=full`.

## Progress Log — 2026-07-22 (P7a-full: DEFI — RETRY SUCCEEDED, all 10 shards clean, HARD-VERIFIED, item DONE)

Retry converged exactly as predicted: all 10 shards reached `EXIT_STATUS=0` (14 min total wall-clock, vs ~35-45 min for
run 1 — the retry's `VERIFIED_INPLACE` counts landed at ~99.98% of each shard, matching run 1's per-shard totals almost
exactly, confirming most work this pass was a cheap existence-check, not a re-copy). Every shard's `run.log` ends with
`apply COMPLETE — shard N/10 fully migrated cleanly (0 non-success outcomes)`, and the `MIGRATED` count in each retry —
17, 27, 20, 20, 19, 17, 24, 17, 29, 21 for shards 0-9 respectively — is an **exact** match to run 1's straggler counts
per shard, confirming the retry fixed precisely (and only) the 211 objects that failed transiently in run 1; nothing
else moved.

**Hard-verify** (real `gsutil stat`, not just log trust): sampled 2 of the 211 previously-straggling objects (shard 0's
`day=2024-09-01/timeframe=15s/.../0xc2e9f25be6...parquet` and shard 9's
`day=2025-11-03/timeframe=5m/.../0xcd8286b489...parquet`). Both: legacy path `gsutil stat` → `No URLs matched` (gone);
canonical path (`pipeline_mode=batch_databento/.../instrument_type=POOL/...`) → real object present, `Creation time`
matching the retry's run window (19:48/19:59 UTC), correct `Content-Length`/hashes present.

**DEFI candle canonical-path migration+purge: DONE.** 1,131,814 objects processed (run 1) + 211 re-verified/re-migrated
(retry) = 0 outstanding legacy-path candle objects in `market-data-tick-defi-prd-central-element-323112`. Moving to
PREDICTION next, applying the tightened prefix-aware JIT-redrain rule (bucket match alone is not sufficient — confirm
object-prefix overlap before stopping any VM found running).

## Progress Log — 2026-07-22 (P7b-prep: PREDICTION JIT-redrain — nothing to stop; sizing from existing census, no new walk)

**JIT-redrain**: surveyed `gcloud compute instances list` (all RUNNING VMs, both clouds relevant here is GCP-only per
current state) — only one PREDICTION-tagged VM: `datapoint-validation-prediction-20260722-151911`
(`validate_datapoint_schema_id.py`). Applied the tightened prefix-aware rule from the DEFI mid-flight finding: read the
script (`instruments-service/scripts/validate_datapoint_schema_id.py`) — it reads `market-data-tick-prediction`
(`data_bucket`, via `resolve_bucket_name`) for validation but its ONLY write (`_flush_shard` →
`client.upload_from_file_obj`) targets `results_bucket = resolve_bucket_name(kind="datapoint-validation")`, a completely
disjoint bucket. It is a reader of the migration's target bucket, never a writer of `processed_candles/**` — not a
JIT-redrain conflict (the rule protects against concurrent WRITERS, not readers; a validator racing an in-flight delete
of a legacy-path object would at worst hit one transient read miss, not corrupt anything). **Verdict: nothing to stop.**
No other PREDICTION-relevant VM found running.

**Shard sizing**: per the workspace's single-walk-discipline rule, did NOT run a fresh census/enumeration — the P0
census (this doc, `## Full results` table) already measured PREDICTION's real corpus: **1,165,459 total objects**
(1,165,458 `SPLIT_BRAIN_DUPLICATE`, 1 `MIGRATE`) — within 4% of DEFI's 1,124,849, and that classification was already
exercised + safety-verified (`ORPHAN=0`) on this exact data via the census dry-run (same script, same code path, just
without `--apply`/`--quarantine`/`--content-repair`). Proceeding with `SHARD_OF=10` (justified by corpus-size parity
with DEFI, not blindly copied), `WORKERS=16`, same proven tarball SHA pins. PREDICTION being ~100% split-brain-dedup
rather than DEFI's ~100% plain-MIGRATE is a different disposition mix — if per-shard throughput differs materially from
DEFI's measured ~61 obj/s/VM, that's new information to carry into CEFI/TRADFI sizing, not a blocker here.

**Action**: launched 10 shards (`SHARD_OF=10`, `SHARD_INDEX=0..9` explicit pin, single backgrounded loop, same SHA pins
as DEFI: `MDPS=c64a7dfa9d9f0689e13c92839e386cd45978a718`, `UAC=c4e1acee147a53aaf0df4e0d8dad1289e2210f79`,
`UTL=b0ec1da02c5fe7dfd94550a9354542fc2a00fc0b`).

## Progress Log — 2026-07-22 (P7b: PREDICTION full apply — CLEAN on first pass, hard-verified, DONE)

All 10 shards reached `EXIT_STATUS=0` on the FIRST run — no straggler retry needed this time (unlike DEFI). Every
shard's `run.log` ends `apply COMPLETE — shard N/10 fully migrated cleanly (0 non-success outcomes)`. Per-shard
`MIGRATED` counts: 116827, 116732, 116512, 116232, 116849, 116524, 116955, 116280, 116730, 115818 (shards 0-9) — **sum =
1,165,459, an EXACT match to the P0 census total**, confirming full coverage with no double-processing or drops. Shards
5-9 additionally show small `VERIFIED_INPLACE` counts (123-3,335) — pre-existing already-canonical objects,
expected/harmless.

**Hard-verify**: sampled the live bucket directly (`gsutil ls .../processed_candles/by_date/day=2025-03-14/**`) — every
returned object carries the canonical `pipeline_mode=.../instrument_type=.../` shape. Confirmed the corresponding legacy
(non-canonical) path for one sampled object is gone (`gsutil stat` → no match), and a broader probe for ANY remaining
non-canonical object under that same `day=/timeframe=` partition (grep excluding `pipeline_mode=`) returned zero
matches.

**PREDICTION candle canonical-path migration+purge: DONE.** Moving to CEFI next — same JIT-redrain (prefix-aware) +
existing-census-sizing approach (CEFI's P0 census: 940,606 objects — but note the census's 13.9% `QUARANTINE_CORRUPT`
figure is STALE: todos 14/18 (shipped, see the "Prep work COMPLETE" entry above) already fixed the root cause
(`_renormalize_wire_cefi` wasn't wired for CEFI's classify branch, wrongly quarantining 128,218 of 130,906 objects) + a
separate KRAKEN-SPOT `/`-in-symbol parsing bug, BEFORE this P7 sequence started — `--apply` re-derives classification
fresh with the fixed classifier, so expect the real quarantine rate to land far below 13.9%).

## Progress Log — 2026-07-22 (P7c-prep: CEFI JIT-redrain — nothing to stop; apply launched)

**JIT-redrain**: only `datapoint-validation-cefi-20260722-151832` is CEFI-tagged among running VMs — the same
`validate_datapoint_schema_id.py` script already analyzed for PREDICTION (reads the tick bucket, writes only to the
disjoint `datapoint-validation` results bucket, never `processed_candles/`). Not a conflict, left running. No other
CEFI-relevant VM found.

**Action**: launched 10 shards (`SHARD_OF=10`, `SHARD_INDEX=0..9`, same proven SHA pins, `WORKERS=16`, `MODE=full`)
against CEFI's 940,606-object corpus.

## Progress Log — 2026-07-22 (P7c: CEFI run 1 — 1 shard genuinely SPOT-preempted, 9 clean stragglers, combined retry launched)

**Watchdog hit its 90-min ceiling with 9/10 terminal** — a real anomaly, not just slow, diagnosed before assuming
anything. `gcloud compute instances describe` on the missing shard's VM
(`canonical-migration-cefi-cdlap-20260722-215112`, shard 2/10) showed `status=TERMINATED`;
`gcloud compute operations list --filter=targetLink~<vm>` confirmed a genuine `compute.instances.preempted` operation at
21:15:15 UTC, matching exactly where its `run.log` progress stream stops (last line: 70,000/~94,000 processed,
`MIGRATED: 58685`). This is expected SPOT behavior on this workspace's own terms (backfill VMs default SPOT, idempotent
shards re-run on preemption) — not a script bug, not a hang.

**The 9 completed shards all exited `rc=5`** — same "COMPLETE WITH STRAGGLER(S)" convention as DEFI, but a DIFFERENT
root cause this time: `CRC32C_MISMATCH_KEPT_SRC` / `SIZE_MISMATCH_KEPT_SRC` (2-31 per shard, ~140 total) rather than
DEFI's `ServiceUnavailable`/`GatewayTimeout`. This is the script's own post-copy integrity verification catching a
checksum/size mismatch and safely KEEPING THE SOURCE rather than deleting it — a safety guard working as intended, not
data corruption. The script's own log line treats it as retriable the same way ("re-run ... is safe (idempotent) and
will retry them"). New disposition categories also appeared here (`CONTENT_REPAIR_UNRESOLVED_QUARANTINED`, ~13-14% of
each shard) — this is the EXPECTED post-todo-14/18-fix quarantine bucket (genuinely-unresolvable content, distinct from
the pre-fix over-quarantine bug), not a regression.

**Action**: launched a single combined retry covering all 10 shards (same `SHARD_OF=10`/SHA pins/`WORKERS=16`) — this
both mops up the ~140 CRC/size-mismatch stragglers across the 9 completed shards AND fully redoes the preempted shard 2
from scratch (its ~59K already-migrated objects will short-circuit via `VERIFIED_INPLACE`, the remaining ~35K get
freshly processed; checkpoint/mapping state does not survive a preemption or non-zero exit, same caveat as DEFI, so a
full shard re-run — not a targeted resume — is the only available path).

## Progress Log — 2026-07-23 (P7c: CEFI retry — another 3-shard SPOT preemption burst; ROOT-CAUSED the CRC/SIZE-mismatch non-convergence)

**Retry 1 also hit preemptions**: 3 of the 10 retry shards (0, 1, 5) were preempted within 3-7 minutes of boot
(`gcloud compute operations list` confirmed `compute.instances.preempted` for all 3, timestamped right where each
`run.log` stream stops) — a real capacity-contention burst in `asia-northeast1-c` at this time, not a bug. This is the
SAME expected-SPOT-behavior class as shard 2's preemption in run 1, just three at once this time.

**The 7 shards that DID complete this retry reproduced their CRC32C/SIZE-mismatch stragglers at (nearly) IDENTICAL
counts to run 1** — e.g. shard 3: 6 CRC32C + 2 SIZE both times; shard 7: 10 CRC32C + 9 SIZE both times; shard 8: 8+4
both times; shard 9: 14+13 both times (only shard 6 differed, by exactly 1). Per the discipline set for DEFI ("if it
doesn't converge after ~3 attempts, investigate rather than blindly retry"), read `_copy_verify_delete()`
(`migrate_candle_canonical_2026_07.py:794-831`) to find out why — **and found the actual root cause**:

```python
dmeta = gcs_describe_object(dst_uri)
if dmeta is None:
    gcs_copy_object(src_uri, dst_uri)      # <-- COPY only happens when dst is MISSING
    dmeta = gcs_describe_object(dst_uri)
...
if smeta.size != dmeta.size: return "SIZE_MISMATCH_KEPT_SRC"
if smeta.crc32c != dmeta.crc32c: return "CRC32C_MISMATCH_KEPT_SRC"
```

The copy step is gated on `dmeta is None` — it only fires when the destination doesn't exist yet. DEFI's stragglers
(`ServiceUnavailable`/`GatewayTimeout`) were copy-operation EXCEPTIONS, meaning the destination object was never
created, so `dmeta` stays `None` on retry and a fresh (successful) copy fires — genuinely transient, converges. CEFI's
stragglers are different: the copy DID complete once (dst exists), but post-copy verification found it doesn't match the
source. On any subsequent run, `dmeta is not None`, so the copy step is SKIPPED — the script only re-_compares_ the same
already-existing (bad) destination against the source, forever. **This class of straggler cannot converge by retrying,
no matter how many times — the retry logic has no path to fix a "copied-but-wrong" destination**, only a
"copy-never-happened" one. This isn't data corruption or loss (the SOURCE is never touched on any `KEPT_SRC` outcome, by
design — the delete-safety protocol's whole point), but it IS a real, previously-unknown gap in this script's retry
model.

**Why not just fix the script live and re-run?** Couldn't reliably identify the SPECIFIC affected objects to verify a
fix against: the WARNING lines only log `"non-success outcome '<TYPE>' at shard-local index N"`, never the object URI
(unlike the exception-path `"apply failed for %s: ..."` at line 991, which DOES log the path) — no per-object path is
logged for a `KEPT_SRC` return. The `--out` mapping TSV (which would have full path detail) only uploads to GCS on the
`&&`-gated success path, and these runs exited rc=5, so it never uploaded; the VMs then self-deleted
(`VM_SHUTDOWN_ON_COMPLETION=true`), taking local disk with it. Patching the copy-verify-delete safety mechanism —
untested — directly against a live production migration, with no way to confirm the fix against the actual failing
objects, is worse than leaving ~140-200 objects (out of ~940K, ~0.02%) safely un-migrated at their legacy path pending a
proper code fix.

**Verdict**: accepting this as a genuine, small, SAFE residual (source data fully intact, nothing lost, nothing
corrupted downstream since these stay at the LEGACY path, not partially/incorrectly canonicalized) — not blindly
retrying a 3rd/4th/Nth time for this specific straggler class, since the code proves it cannot converge. Relaunched ONLY
the 3 preempted shards (0, 1, 5 — their bulk migration work is unrelated to this finding and still needs to complete);
once terminal, will tally the final residual CRC/SIZE-mismatch count across all 10 CEFI shards and record it honestly
(NOT claim "0 outstanding" the way DEFI/PREDICTION could). Filed as **todo 19**.

## Progress Log — 2026-07-23 (P7c: CEFI DONE — 149-object documented residual, hard-verified, closing out)

The 3 relaunched shards (0, 1, 5) completed cleanly this time (no further preemptions) at `exit=5`, each reproducing its
ORIGINAL run-1 mismatch counts exactly (shard 0: 2 CRC32C + 2 SIZE; shard 1: 8 CRC32C + 4 SIZE; shard 5: 15 CRC32C + 2
SIZE) — the same deterministic non-convergence confirmed for the other 7 shards.

**Final CEFI tally across all 10 shards** (best/latest known count per shard):

| Shard     | CRC32C_MISMATCH | SIZE_MISMATCH | Total residual |
| --------- | --------------: | ------------: | -------------: |
| 0         |               2 |             2 |              4 |
| 1         |               8 |             4 |             12 |
| 2         |               0 |             3 |              3 |
| 3         |               6 |             2 |              8 |
| 4         |               8 |             9 |             17 |
| 5         |              15 |             2 |             17 |
| 6         |              22 |             8 |             30 |
| 7         |              10 |             9 |             19 |
| 8         |               8 |             4 |             12 |
| 9         |              14 |            13 |             27 |
| **TOTAL** |                 |               |        **149** |

**149 / 940,606 = 0.0158%** left at their legacy (non-canonical) path — source data fully intact for every one of them,
nothing lost, nothing corrupted; they simply aren't yet promoted to canonical, pending todo 19's script fix + one
surgical mop-up pass.

**Hard-verify** (same method as DEFI/PREDICTION): live-sampled
`gs://market-data-tick-cefi-prd-.../processed_candles/ by_date/day=2019-03-30/**` — every returned object carries the
canonical `pipeline_mode=.../instrument_type=.../` shape.

**CEFI candle canonical-path migration+purge: DONE (99.98%+, 149-object documented residual tracked as todo 19).**
Moving to TRADFI next — same JIT-redrain (prefix-aware) approach; TRADFI's census is dominated by
`NEEDS_CONTENT_TRADFI_ID` (6,487,045/7,646,831 = 84.8%, per the P0 census table), so expect this run to spend most of
its time on parquet content reads + `_renormalize_legacy_instrument_ids`, not path-only rewrites — a materially
different profile than DEFI/PREDICTION/CEFI. Apply the SAME accept-and-track discipline for any KEPT_SRC-class
stragglers TRADFI hits (todo 19's gap is generic to the shared `_copy_verify_delete` helper, not CEFI-specific).

## Progress Log — 2026-07-23 (P7d-prep: TRADFI JIT-redrain — nothing to stop; apply launched)

**JIT-redrain**: 3 `tradfi-bf-krx-eq-ohlcv-24h-*` VMs running (`task=mtds-backfill`) — investigated via `run.log` before
assuming safe: writes exclusively to `raw_tick_data/by_date/.../data_type=ohlcv_24h/...` (confirmed via actual upload
log lines, not the misleading "ohlcv-24h" name), disjoint from `processed_candles/` — MTDS raw-tick capture, not MDPS
candle output. Not a conflict, left running. No other TRADFI-relevant writer found.

**Shard sizing — deliberately NOT scaled proportionally to corpus size**: TRADFI's corpus (7,646,831 objects) is ~6-8x
DEFI/PREDICTION/CEFI's (~0.94-1.17M each), and naively scaling `SHARD_OF` proportionally would mean ~60-70 concurrent
VMs. Given todo 19's still-unfixed retry-idempotency gap — any `KEPT_SRC`-class straggler this run produces is PERMANENT
(can't be retried away) — and given CEFI's 149-object residual is plausibly linked to write-contention from concurrent
VMs hitting the same bucket, scaling concurrency proportionally risks a proportionally WORSE stuck-residual outcome
(potentially ~1,000+ objects) rather than a proportionally worse but still-small one. Chose `SHARD_OF=20` (2x the proven
DEFI/PREDICTION/CEFI concurrency, not 6-8x) — trades longer wall-clock per shard (~382K objects/shard vs ~115K) for
keeping contention risk in the same regime already proven tolerable. If throughput data from this run suggests
contention wasn't actually the driver, that's real information to inform a different choice next time — not assumed away
here.

**Action**: launched 20 shards (`SHARD_OF=20`, `SHARD_INDEX=0..19`, same proven SHA pins, `WORKERS=16`, `MODE=full`)
against TRADFI's `market-data-tick-tradfi-prd-central-element-323112` bucket.

## Progress Log — 2026-07-23 (P7d: TRADFI — severe SPOT preemption storm, watchdog liveness-check gap found + fixed, 18 shards recovering on-demand)

**Real progress check ~1h after launch found ZERO `run.log` for any sampled shard** — every prior AG had a `run.log`
within minutes (enumeration phase alone completes in ~3min). Diagnosed via `gcloud compute instances describe`:
`status=TERMINATED`, and `gcloud compute operations list` confirmed `compute.instances.preempted` for every one of the
first 3 checked, each within 1-4 MINUTES of boot. Checked all 20: **18 of 20 shards were preempted within minutes of
boot** — a severe, real SPOT capacity contention event in `asia-northeast1-c` (following the smaller 1/10 then 3/10
bursts already seen on CEFI in this same session — this is the third and by far worst instance, strong evidence of
genuinely elevated demand in this zone right now, not a fluke). Only shards 7 and 8 (`...-051026`/`...-051107`)
survived; both confirmed healthy via `run.log` — ~260,000/382,341 objects processed each, climbing steadily, disposition
mix as expected for TRADFI's content-repair-heavy profile (`CONTENT_REPAIR_UNRESOLVED_QUARANTINED` dominant, consistent
with the P0 census's 84.8% `NEEDS_CONTENT_TRADFI_ID` figure).

**Real gap found in my own tooling, not just the migration**: the watchdog script used for every prior AG only checks
for `EXIT_STATUS` — a preemption (hard kill) never writes it, so the watchdog had been reporting all 20 shards as
`running` for ~2 HOURS while 18 were actually dead the whole time. This is exactly the liveness-check gap this
workspace's own async-wait-discipline rule warns about ("monitors read terminal exit_code + ... a TERMINAL measured
verdict (liveness kill -0 <PID>, no self-match)") — I was checking for a positive TERMINAL signal but never checking
LIVENESS as a cross-check, so a silently-dead VM looked identical to a healthily-running one. Caught this only because
the user asked for a status update and I spot-checked real `run.log` content instead of trusting the watchdog log —
future watchdogs for this migration (and generally) should check
`gcloud compute instances describe --format= "value(status)"` alongside `EXIT_STATUS`, not `EXIT_STATUS` alone.

**Given each TRADFI shard runs ~2+ hours (382K objects/shard at the measured ~40-55 obj/s rate) — far longer exposure to
preemption than DEFI/PREDICTION/CEFI's ~35-45min shards** — and given this is now a MEASURED, repeated pattern of severe
zone-level SPOT contention (not a one-off), chose NOT to blindly retry SPOT again for the 18 dead shards. **Relaunched
them with `ON_DEMAND=true`** (the workspace's own sanctioned opt-out from the SPOT-default HARD RULE) — trading cost for
reliability, justified by measured evidence that SPOT capacity in this zone is genuinely scarce right now and a
long-running shard eating another storm would cost more real time than the on-demand price premium. Deliberately left
shards 7/8 alone (already >68% done, restarting from scratch would waste real progress — no checkpoint survives a kill
either way, same caveat as DEFI/CEFI). **STATUS: 2 shards healthy on SPOT (7, 8), 18 shards launching on-demand, NOT YET
VERIFIED.** If shards 7/8 get preempted later, relaunch just those 2 indices on-demand too rather than restarting the
whole fleet.

**Clarifying note (operator asked whether fleet auto-recovery should have handled this)**: it does not, for this VM
family, by design. The workspace's general fleet auto-recovery (`RelaunchPreemptedVm` / `exit_code_fleet_monitor.py`)
resumes from a shared `PROGRESS.json` checkpoint contract that day-frontier backfill categories participate in.
`migrate_candle_canonical_2026_07.py`'s own docstring (line ~110/998) explicitly states its resume mechanism is "a NEW,
self-contained mechanism, distinct from the workspace's general day-frontier `PROGRESS.json`" — and
`launch-canonical-migration-vm.sh` has zero `PROGRESS.json` wiring for the `*-candle-apply` categories. So nothing in
the fleet would have caught or relaunched these 18 dead shards automatically; the manual detection (real `run.log`
spot-check, since the watchdog's `EXIT_STATUS`-only check couldn't see it) and relaunch above was necessary, not
duplicate work.

**Action taken**: relaunched all 18 dead shard-indices with `ON_DEMAND=true` (`STANDARD` provisioning confirmed in each
launch's instance list output). Left the 2 healthy SPOT survivors (shards 7, 8) running untouched. **Fixed the watchdog
itself**: the new version checks `gcloud compute instances describe --format="value(status)"` for any VM lacking
`EXIT_STATUS`, distinguishing genuinely-`alive`/still-working from `DEAD-NO-EXIT` (a preemption or crash the old
EXIT_STATUS-only check couldn't see) — and exits IMMEDIATELY with an alert the moment any VM is found dead, rather than
waiting silently for hours. Armed against the full 20-shard fleet (18 recovery + 2 survivors). **STATUS: IN FLIGHT, NOT
YET VERIFIED.**

**Operator asked whether to parallelize further for speed (2026-07-23, ~08:14 UTC, 3/20 done, ~1.5-2h/shard measured)**.
Discussed and operator agreed: **do NOT reshard the in-flight run.** Killing+restarting the 17 still-running shards to
add more concurrency would throw away real progress; adding EXTRA VMs on top under a different `SHARD_OF` would not be
genuine parallelism (a different `shard_of` re-partitions the corpus differently, so a new batch would redundantly
reprocess a largely-overlapping slice, not a clean split of what's left) AND would increase concurrent-VM contention
against the same bucket — exactly the pressure already measured to produce todo 19's un-retriable stuck-forever
stragglers (CEFI's 149-object residual). Both original SPOT survivors (shards 7, 8) have now finished, so the remaining
17 running shards are ALL on-demand — **zero further preemption risk for the rest of this run.** Plan: let this run
finish undisturbed, then size the (likely-needed, per DEFI/CEFI precedent) retry pass AGGRESSIVELY — since a retry only
touches the residual straggler count (small, per DEFI/CEFI history), high shard-count there is low-risk and buys real
wall-clock savings without the contention downside.

## Progress Log — 2026-07-23 (P7d: TRADFI run 1 COMPLETE — all 20 shards, 229/~7.6M transient stragglers, aggressive retry launched)

All 20 shards reached `EXIT_STATUS=5` cleanly (no further preemptions — confirmed via the liveness-aware watchdog,
`dead-no-exit=0/20` throughout). **Every shard's non-success breakdown is 100% `ERROR:ServiceUnavailable`/
`ERROR:GatewayTimeout`** — the SAME transient-network-error class as DEFI (copy exception → destination never created →
retry's `dmeta is None` check fires a fresh, successful copy), NOT CEFI's permanent `KEPT_SRC` class (todo 19). Total:
**229 stragglers across all 20 shards, out of ~7.6M objects processed (~0.003%)** — genuinely expected to converge
cleanly on retry, no todo-19 concerns here.

**Per-shard straggler counts** (shard: count): 0:12, 1:18, 2:10, 3:8, 4:11, 5:14, 6:12, 7:7, 8:10, 9:13, 10:14, 11:4,
12:13, 13:18, 14:11, 15:8, 16:13, 17:12, 18:10, 19:11.

**Retry launched per the operator-agreed plan**: `SHARD_OF=50` (2.5x the original 20 — aggressive, justified because a
retry's real GCS write-QPS is tiny at this residual size, ~229 real re-copies spread across 50 VMs ≈ ~4-5 each on
average, so contention risk is genuinely low regardless of concurrency chosen here — unlike the ORIGINAL run where every
object needed a real copy/content-repair). Same proven SHA pins, `WORKERS=16`, `MODE=full`, back on SPOT (now that
`deployment-service@a32360a`'s native shutdown-script fix is live in this same clone — any preemption should be
individually detectable + relaunchable the same way this session has already handled every prior storm). **STATUS: retry
IN FLIGHT, NOT YET VERIFIED.**

## Progress Log — 2026-07-23 (P7d-retry: THIRD severe SPOT storm this session — 36/50 preempted within ~1min of boot; recovering on-demand)

The liveness-aware watchdog fired immediately: **36 of 50 retry shards preempted within under a minute of boot**
(confirmed via `gcloud compute operations list` on 2 sampled VMs — both `compute.instances.preempted` at 48-55s after
`insert`). This is now the **third** severe `asia-northeast1-c` SPOT contention event measured this session (CEFI: 1/10
then 3/10; TRADFI run 1: 18/20; TRADFI retry: 36/50) — no longer plausibly a one-off fluke; this zone appears to be
under sustained heavy external SPOT demand across this entire multi-hour window, independent of anything this migration
itself is doing. **Confirms my own `deployment-service@a32360a` fix is working as designed**: these VMs now show EMPTY
`gcloud compute instances describe` status (fully deleted) rather than `TERMINATED` (merely stopped) — the
`--instance-termination-action=DELETE` change means a preempted VM's PREEMPTED-blob-writing shutdown-script still had
time to fire (native mechanism, available from t=0) before full teardown; the watchdog correctly detected "gone" via an
empty status rather than needing a `TERMINATED` string match.

Recovered the exact 36 dead shard-indices (0,2,4,5,6,8,10,11,13,14,15,16,17,18,19,23,24,25,26,27,28,29,31,32,34,35,
37,39,40,43,44,45,46,47,48,49 — cross-referenced from the launch log's shard→VM mapping against the watchdog's dead
list, zero unmapped) with `ON_DEMAND=true`, same pattern as the original run's recovery.

## Progress Log — 2026-07-23 (P7d: TRADFI DONE — retry converged to 0 stragglers, hard-verified, full migration COMPLETE)

All 50 retry shards (14 SPOT survivors + 36 on-demand recovery) reached `EXIT_STATUS=0` cleanly, zero further
preemptions. **Checked all 50 shards' `run.log` exit lines — every single one is `command exited rc=0`, zero
`COMPLETE WITH STRAGGLER(S)` lines anywhere.** The retry fully converged — all 229 stragglers from run 1 are resolved.

**Hard-verify** (2 samples from run 1's original straggler list): (1) a `_quarantine/`-destined object (CME trades,
`day=2025-02-25`) — legacy path gone, quarantine destination exists with real content (created 09:49:26 UTC, inside the
retry window). (2) a `MIGRATE`-destined empty-stem object (CME OHLCV, `underlying=CBO`) — legacy path gone, canonical
destination (`.../ticks.parquet`, the synthesized empty-stem filename) exists with real content.

**TRADFI candle canonical-path migration+purge: DONE, 0 outstanding legacy-path objects.** This was the hardest leg of
the 4 (content-repair-heavy, 3 separate severe SPOT-preemption storms survived in the same session — CEFI's smaller ones
plus TRADFI's 18/20 then 36/50) and it converged completely clean, unlike CEFI's 149-object todo-19 residual — TRADFI
never hit a single `KEPT_SRC`-class straggler across either run.

**All 4 asset groups (DEFI, PREDICTION, CEFI, TRADFI) are now migration-complete.** Moving to P8: cross-AG
verify/reconcile, then close out this issue doc.

## Progress Log — 2026-07-23 (P8: cross-AG verify/reconcile — 4 parallel independent reconciliations, all CLEAN; one

material finding on TRADFI's resolution rate, now precisely quantified)

Dispatched 4 parallel agents (one per asset_group), each running an INDEPENDENT post-migration check that does not trust
the P7 `--apply` runs' own self-reported "0 stragglers": a fresh sharded GCS enumeration of `processed_candles/by_date/`
today, then the migration script's own `--dry-run` classifier (its inverse ground-truth operation) run against that
fresh listing. Read-only throughout, `--apply` never passed. Each wrote a full report to
`plans/audit/results/data_pipeline_reconciliation_candles_<ag>_2026_07_23.md`; commits `18c0eeb79` (defi), `a2a30bd46`
(prediction), `f25876a4d` (cefi), `e69792e36` (tradfi), all on `live-defi-rollout`.

**Two of the four agents (defi, tradfi) initially self-reported "completed" while their actual work — waiting on their
own backgrounded enumeration process — was still running, expecting an automatic resume notification that does not exist
for sub-agents.** Caught immediately (their own result text admitted "no further action until notified") and resumed via
`SendMessage` with an explicit instruction to poll their background process to REAL exit before reporting again. Both
then genuinely completed. Filing this as a process note, not a data-correctness finding: sub-agents that background
their own long-running work and stop must be explicitly told they will not be auto-resumed.

**Results, all 4 disposition histograms showing `ORPHAN=0` and the tool's own `sum(dispositions)==total` safety
invariant holding (ground truth, not a self-report):**

| AG         | P7 `--apply` processed | P8 fresh live count | Live disposition (100% unless noted)                   | Verdict                                 |
| ---------- | ---------------------: | ------------------: | ------------------------------------------------------ | --------------------------------------- |
| defi       |              1,131,814 |           1,123,415 | `CANONICAL_NOOP`                                       | CLEAN                                   |
| prediction |              1,165,459 |             583,228 | `CANONICAL_NOOP`                                       | CLEAN                                   |
| cefi       |                940,606 |             405,408 | `CANONICAL_NOOP`=405,259 + `SPLIT_BRAIN_DUPLICATE`=149 | residual = EXACT match to todo-19's 149 |
| tradfi     |              7,646,831 |             534,679 | `CANONICAL_NOOP`                                       | CLEAN (of what remains — see below)     |

Every live count is LOWER than the P7 processed count — expected, not a red flag by itself, because `--apply` reduces
object count via legitimate mechanisms (SPLIT_BRAIN_DUPLICATE dedup collapses 2 objects to 1; empty-stem "with
underlying" consolidates many-to-one into a bundled `ticks.parquet`; `QUARANTINE`-class objects move OUT of
`processed_candles/` to a disjoint `_quarantine/` prefix, never deleted). What matters is whether the reduction is fully
accounted for. Verified per-AG, not assumed:

- **defi**: gap = 8,399 (0.74%). Directly probed `_quarantine/` → exactly **1,442** objects, an EXACT match to the P0
  census's `QUARANTINE_CORRUPT` figure. Remainder consistent with split-brain dedup. Fully accounted for.
- **prediction**: gap = 582,231 (49.96% of P7-processed). Matches a clean ~2-object-pair `SPLIT_BRAIN_DUPLICATE` dedup
  to within 0.1% of the naive halving estimate. Fully accounted for.
- **cefi**: gap = 535,198 (56.9%). The P8 agent asserted this was "expected, quarantine moves objects to a sibling
  prefix" without directly measuring it — **independently checked this myself** (main session, not delegated): probed
  `_quarantine/processed_candles/by_date/` → only **396 day-prefixes**, and a sampled middle day held just **14
  objects** (nowhere near TRADFI's density, see below). CEFI's real quarantine volume is small; the ~535K gap is
  therefore dominated by `SPLIT_BRAIN_DUPLICATE` dedup, consistent with the codex-documented CEFI v5/v6 dual chain-tail
  hazard (bare `underlying=/ticks.parquet` vs canonical `underlying=/quote=/margin=/ticks.parquet` — exactly a
  2-copies-per-shard pattern). Reasonably accounted for; no data-availability concern.
- **tradfi — the one that needed real scrutiny**: gap = **7,112,152 objects (93.0% of the pre-migration 7,646,831
  corpus)**. The P8 agent's own report explicitly flagged that it did NOT measure the `_quarantine/` count ("a fresh
  full walk of it would be a second whole-corpus GCS walk not authorized under this task") and inferred the explanation
  from this session's earlier mid-run progress-log note instead. Given the scale, **I independently verified this
  myself** rather than accepting the inference: `_quarantine/processed_candles/by_date/` has **712 day-prefixes** (vs
  884 in the live corpus — comparable coverage), and a bounded sample of ONE middle day (`day=2022-06-05/`, capped at
  5,000 results) **hit the cap** — i.e. that single day alone holds **at least 5,000** quarantined objects, roughly
  350-1000x denser than CEFI's comparable sample. This is strong, direct evidence the missing 7.1M objects are sitting
  in `_quarantine/` (safe, un-deleted, per the script's own "never delete quarantined" invariant) rather than lost —
  corroborating, not merely trusting, the mid-run note. **I did not do a full quarantine count** (that would be exactly
  the un-sanctioned second whole-corpus walk the P8 agent correctly declined to run) — the day-prefix-count +
  single-day-density check is a bounded, sufficient sanity check for "order of magnitude matches," not an exact
  reconciliation.

**The material finding, stated plainly**: the TRADFI candle canonical-PATH migration is genuinely clean — 0 orphans, 0
malformed objects, nothing non-canonical sitting in `processed_candles/`. But only **~7% of TRADFI's original candle
namespace (534,679 / 7,646,831) ended up canonically available**; the other **~93% (~7.1M objects, dominated by the
`NEEDS_CONTENT_TRADFI_ID` class)** is sitting in `_quarantine/`, safe but NOT usable by downstream readers, pending
leaf-id resolution. This was foreshadowed during the actual P7d apply run (2026-07-23 progress log: "mix as expected...
`CONTENT_REPAIR_UNRESOLVED_QUARANTINED` dominant") but P8 is the first time the SCALE has been measured precisely as a
headline number rather than a qualitative "expected" note — worth operator attention even though it isn't new
information. **This is exactly todo 3 below**, now with a precise, P8-measured scope (~7.1M objects, not just "84.8% of
the corpus needs repair" from the P0 census's pre-execution estimate).

**P8 verdict: the canonical-PATH migration+purge phase (P6→P7→P8) is COMPLETE and independently verified clean across
all 4 asset groups** — 0 orphans, 0 malformed objects, residuals fully accounted for (CEFI's 149 = todo-19, TRADFI's
7.1M = todo 3, both already-tracked, neither a new defect). **This issue doc is NOT being closed** — todos 2, 3, 7, 9,
13, 15, 16, 19 remain genuinely open (content-level defects distinct from the path-migration this phase addressed);
`status: open` stays accurate. What's done is the big infra lift (draining, sharded SPOT `--apply` across ~10.9M
objects, purge, independent verification); what remains is smaller, targeted content-repair work, tracked below.
