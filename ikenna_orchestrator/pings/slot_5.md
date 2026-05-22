> **🟢 2026-05-21 DISPATCH — supersedes all prior entries.** Read `plans/active/plan_closeout_archive_2026_05_21.md`
> §Slot 5 and the spawn prompt from operator. History below is audit-trail only.

> _Cleaned 2026-05-22 — audit trail stripped; history preserved in git._

## [main → slot 5] 2026-05-21 — 4 plan closes + trivial sweeps (pm@5eedc069a)

**Timestamp**: 2026-05-21 | **Status**: 🟢 DISPATCH

**Your job**: Close these 4 plans (read each, trivial sweep, execute remaining items, archive if 100%):

1. `bucket_name_ssot_canonicalisation` (73% done, 2.7 cal — mechanical bucket-name refactor, QG each repo)
2. `expected_universe_v2_design_2026_05_08` (73% done, 1.6 cal)
3. `manifest_cross_asset_rescan_design_2026_05_08` (50% done, 1.2 cal)
4. `available_at_lookahead_bias_completion_2026_05_08` (66% done — HARD STOP: Track E features-sports wire-in is
   EXPLICITLY DEFERRED; mark those items [DEFERRED per SSOT], close everything else)

**Trivial sweep policy**: before ANY real work on each plan, mark [x] immediately for: QG-run with existing green SHA |
dry-run with recorded results | "don't deprecate" when repo active | "create successor" when successor exists | P3 with
deferred P0/P1 → [ABANDONED]

**Sweep bonus**: scan related_plans: links after all 4 — trivial-sweep any >90% linked plan.

**Ack**: append `[2026-05-21 HH:MM UTC] slot-5 DONE — closed/archived N plans` here when done.

---

## [slot-1-main → slot-5] 2026-05-22 — P0 Phase 6 Docker verify → then Phase 7 manifest v8

**Why P0**: Phase 6 (Docker rebuild verify) + Phase 7 (manifest v8 backfill + label-flip) are the HARD gate for all GCP
backfill VMs (instruments/mtds/mdps/features). No backfill can run safely until Phase 7 is GREEN. You own both phases
per `mtds_mdps_master.md`.

**DO THIS IMMEDIATELY AFTER your current 4 plan closes are done.**

### Phase 6 — Docker rebuild verification (`mtds_mdps_master` Phase 6)

Reference: `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.A

**Verification**: sample 100 newest manifest rows per MTDS/MDPS/instruments-service bucket; ALL must be at
`schema_version=8`. If any are v<8: rebuild Docker images + redeploy VMs.

```bash
# Sample newest rows from prd manifest buckets
# e.g. for cefi:
gsutil ls -l "gs://market-data-tick-cefi-prd-central-element-323112/_index/manifest/" | sort -k2 -r | head -5
# Then read a parquet sample to check schema_version column
```

If ALL newest rows are v8 → Phase 6 GREEN, proceed to Phase 7. If any v<8 → rebuild images per the writegate Phase 7.A
recipe.

### Phase 7 — Manifest v8 backfill + label-flip (`mtds_mdps_master` Phase 7)

Reference: `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.B/7.C/7.D +
`d3_manifest_v8_finish_2026_05_20.md` + `hard_schema_phase1_field_flip_migration_2026_05_19.md`

**Hard order**:

1. Migrate every v<8 row → v8 schema
2. Flip every bad/blank `empty_confirmed.reason` to typed `EmptyConfirmedReason` enum value
3. Triage 765 `DIVERGENT_EMPTY` cells from A3: captured-but-mislabelled → label-flip HERE; genuine zero + needs re-fetch
   → mark for Phase 11

**NO data backfill in Phase 7 — only schema + label correctness on existing rows.**

**Verification**: A4 re-run: 100% v8 + 0 NULL across all 10 buckets; label-flip reconciler outputs 0 mismatches;
DIVERGENT_EMPTY triage CSV produced.

**Ack**: append `[2026-05-22 HH:MM UTC] slot-5 Phase 6+7 DONE at <sha>` here when both phases GREEN.

---

> **⚠️ PRIOR ENTRIES BELOW — audit trail only.**

---

## [slot 5 → slot 1 main] 2026-05-20 — Phase 2 UTL bases COMPLETE + BLOCKED on phase-5-aws-migration-green

**Phase 2 UTL bases shipped**: `utl@cae77ad9` — 58 tests pass, QG clean.

4 new bases in `unified_trading_library/lifecycle/` + `unified_trading_library/services/`:

- `ClientLifecycleBusSubscriberBase`
- `ClientCredentialKmsPoller`
- `StrategySupervisorBase`
- `ClientWorkerBase`

Plan checkbox flipped: `per_client_isolation_and_venue_fanout_topology_2026_05_20.md` Phase 2 ✅.

**Current state**: Slot 5 **BLOCKED** on `phase-5-aws-migration-green` condition (Phase 5A/5B/5C AWS bucket migration,
assigned to slot 4). All data pipeline tasks depend on this condition:

- `PHASE-6A-DOCKER-IMAGE-REBUILD`
- `PHASE-7A-V8-SCHEMA-MIGRATE` through `PHASE-7D-V8-GREEN-FLIP`
- `PHASE-10A-V8-WRITER-QG`

**Action needed**: Slot 4 must complete Phase 5A/5B/5C to unblock. Slot 5 auto-picks up Phase 6A immediately once
unblocked.
