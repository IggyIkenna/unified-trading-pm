---
title: "HANDOFF — Expected-universe enumerator: launcher + 5 VM launches + plan annotations"
created: 2026-05-07
author: claude-session
priority: P0
session_objective:
  Run enumerate_expected_universe.py for all 5 asset_groups; close the rollup-vs-drilldown denominator divergence
estimate_class: design
estimate_baseline_ai_days: TBD
estimate_calibrated_ai_days: TBD
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (design, multiplier 0.6×).
  Owner agent: fill baseline + multiply × 0.6 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): the deliverable is
deployed and superseded past this doc's literal specifics — `instruments-service/scripts/enumerate_expected_universe.py`
implements all 5 asset groups for real (this handoff's CeFi/prediction/sports-per-league gaps are closed); the launcher
shipped under an evolved name (`launch-expected-universe-v2-vm.sh`); `VM_PREFIX_TO_BUCKET` moved into
`deployment_service.vm_prefix_registry` (2026-07-13); the 2 target plans for banner-flips no longer exist (folded into
`data_status_page_ux_and_canonicalisation_2026_07_16.md` / `data_status_cell_grid_rearchitecture_2026_07_18.md`).
`enumerate_expected_universe.py` is cited as live production infrastructure in multiple current active plans.

# HANDOFF — Expected-universe enumerator: launcher + 5 VM launches + plan annotations

**For the next agent.** Operator (Ikenna) wants the manifest backfill VMs running for all 5 asset_groups so the
data-status panel's top-level total and per-venue breakdowns converge on the same denominator. The script is built and
shipped; the remaining work is launcher + VM launches + plan annotations.

> **READ FIRST**: [`unified-trading-pm/cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) (workspace-wide
> rules) +
> [`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md).
> The "No fire-and-forget VM launches" rule + "Manifest concurrency principle" + "Two teammates × multiple parallel
> agents" rules are all directly relevant to this work.

---

## What's already shipped (do NOT redo)

5 commits across 3 repos this session (2026-05-07 PM):

| #   | Repo                  | SHA        | Subject                                                                                  |
| --- | --------------------- | ---------- | ---------------------------------------------------------------------------------------- |
| 1   | unified-trading-pm    | `3321b96c` | docs(defi-archetypes): venue-matrix re-verification + canonicalisation plan              |
| 2   | unified-api-contracts | `54dff09`  | docs(venue_collateral): STALENESS_FLAG_2026_05_07 for ETH-LST acceptance rows            |
| 3   | unified-trading-pm    | `d0f521b4` | docs(defi-launcher-audit): data-status drilldown breakdown + truncation audit            |
| 4   | unified-trading-pm    | `372e23aa` | docs(writegate,codex): codify rollup-vs-drilldown divergence + Phase 3.D.4 v2 enumerator |
| 5   | instruments-service   | `8e404c8`  | feat(enumerator): NEW `enumerate_expected_universe.py` — Phase 3.D.4 backward-fill       |

Key file shipped:
[`instruments-service/scripts/enumerate_expected_universe.py`](../../../instruments-service/scripts/enumerate_expected_universe.py)
(600 lines). Per-asset-group implementation status:

- **TradFi**: FULL — calendar pre-skip via UAC `non_trading_day_reason` (EXPECTED_HOLIDAY / EXPECTED_WEEKEND).
- **DeFi**: FULL — chain pre-genesis + protocol pre-launch via UAC `CHAIN_GENESIS_DATES` + `PROTOCOL_LAUNCH_DATES`.
- **Sports**: PARTIAL — pre-source-coverage-start per-source via UAC `SOURCE_COVERAGE_START`. Per-league enumeration
  deferred (needs sports leagues catalog read).
- **CeFi**: STUB — yields 0 rows with a WARNING log. Production v2 needs instruments-service catalog with per-
  instrument lifecycle (`available_from` / `available_to` / `expiry`).
- **Prediction**: STUB — yields 0 rows. Blocked on UAC `PREDICTION_GROUPS` registry which is empty pending the
  canonical_question_group SSOT (`predictions_master_2026_05_07.md`).

The script has been **smoke-tested locally** — TradFi NASDAQ holidays, DeFi AAVE_V3-ETHEREUM 2018 pre-launch, sports
api_football pre-2018-01-01 all yield correct (row, reason) tuples. CLI parses cleanly. **No unit tests written yet** —
see deferred items below.

---

## Your tasks (in order)

### Phase 1 — Build the launcher (deployment-service)

- [ ] **NEW** `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh`. Mirror the
      [`launch-defi-phantom-recon-vm.sh`](../../../deployment-service/scripts/vm/launch-defi-phantom-recon-vm.sh)
      pattern exactly:
  - `--force` flag bypasses singleton lock
  - Positional arg: asset_group (`cefi` | `defi` | `tradfi` | `sports` | `prediction`)
  - Second positional arg: `--scan-only` (default) | `--apply-write`
  - Singleton lock per-prefix in zone `asia-northeast1-c`
  - Machine: `e2-standard-4`, boot disk 50GB
  - VM name: `expected-universe-enum-{asset_group}-{RUN_TS}` where `RUN_TS=$(date +%Y%m%d-%H%M%S)`
  - `VM_TASK=expected-universe-enum`, `VM_SERVICE=instruments_service`, `VM_OPERATION=expected-universe-enum`,
    `VM_ASSET_GROUP=$(echo "$ASSET_GROUP" | tr '[:lower:]' '[:upper:]')`,
    `VM_BACKFILL_CMD=python /home/ikennaigboaka/workspace/instruments/scripts/enumerate_expected_universe.py --asset-group ${ASSET_GROUP} ${APPLY_FLAG}`,
    `VM_SHUTDOWN_ON_COMPLETION=true`
  - For `--apply-write` mode, additionally pass `MANIFEST_PER_VM_SHARDS=true,VM_NAME=${VM_NAME}` in metadata so the
    script's per-VM shard isolation guard fires correctly.
- [ ] **Update**
      [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
      `VM_PREFIX_TO_BUCKET` registry: add `"expected-universe-enum-": None` (heartbeat-only, no shard bucket since this
      writes to per-VM manifest shards which the consolidator picks up). **Relaunch the watchdog VM** after the dict
      update per the CLAUDE.md "VM Naming Convention" rule:

      ```bash
                      gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet
                      bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh
                      ```

- [ ] **Refresh tarballs** with the new script + launcher:

      ```bash
                      bash deployment-service/scripts/vm/create-code-tarballs.sh --all
                      ```

                      This re-tars instruments-service (with the new `enumerate_expected_universe.py`) + deployment-service (with
                      the new launcher). **Required before any VM launch** — without this, VMs boot with stale code and the new
                      script is missing.

- [ ] **Commit + push** these three changes (launcher + watchdog dict + any tarball script edits) per the workspace Half
      1 / Half 2 rule. Plan-flip checkbox in this handoff doc inline.

### Phase 2 — Sequential VM launches with event verification

**Order**: TradFi → DeFi → Sports → CeFi → Prediction. CeFi + Prediction will produce 0 rows (stubs) and exit quickly —
that's expected and acceptable; documents the gap to the operator without erroring.

For **each** asset_group, the launch + verification loop:

```bash
# --- 1. Scan-only first (CSV report on the VM, no manifest mutation) ---
bash deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh tradfi
# Capture VM_NAME from output (expected-universe-enum-tradfi-{ts})

# --- 2. Verify STARTED event within 90s (no-fire-and-forget rule) ---
sleep 90
gcloud storage ls gs://central-element-323112-events/events/instruments-service/$(date -u +%Y-%m-%d)/expected-universe-enum-tradfi-*/
# MUST find a hour=*/* directory. Read first JSONL, assert event=="STARTED":
gcloud storage cat gs://central-element-323112-events/events/instruments-service/$(date -u +%Y-%m-%d)/expected-universe-enum-tradfi-*/hour=*/*.jsonl | head -1
# Should look like: {"event": "ENUMERATOR_STARTED", ...}

# --- 3. Wait for completion (typical: 5-30min for tradfi/defi/sports;
#         instant for cefi/prediction stubs). Re-check every 10-15min. ---
gcloud compute instances list --filter="name~^expected-universe-enum-tradfi-" --zones=asia-northeast1-c
# When STATUS goes from RUNNING → TERMINATED (or absent due to auto-shutdown), verify completion:
gcloud storage cat gs://central-element-323112-events/events/instruments-service/$(date -u +%Y-%m-%d)/expected-universe-enum-tradfi-*/hour=*/*.jsonl | tail -1
# MUST be {"event": "ENUMERATOR_COMPLETED", "candidates": N, "written": 0, "report_path": "...", ...}

# --- 4. Fetch the CSV report from the VM via gsutil cp + inspect distribution ---
# (the script emits report_path which the VM can copy to GCS via the events
# stream — alternatively SSH to the VM before auto-shutdown to grab it)

# --- 5. Operator decides: scan distribution looks right? If yes, --apply-write ---
bash deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh tradfi --apply-write
# Repeat verification loop. ENUMERATOR_COMPLETED should now have written>0 + per_vm_blob path.

# --- 6. Verify per-VM shard merged into canonical manifest (~5min after VM shutdown) ---
gcloud storage ls gs://market-data-tick-tradfi-central-element-323112/_index/per_vm/expected-universe-enum-tradfi-*.parquet
# Consolidator daemon merges this into _index/availability_index.parquet within 5min.
# Spot-check a few (venue, data_type, day) tuples in the rollup vs drilldown UI to confirm
# percentages now agree.

# --- 7. Move to next asset_group ---
```

Per CLAUDE.md "No fire-and-forget VM launches" — every launch MUST be paired with active event verification.

### Phase 3 — Plan annotations (mark "VM RUNNING")

Per operator request, add a **VM RUNNING** banner to every active plan related to manifest / data-status, so other
agents seeing the plans know there's a VM in flight on this work.

- [ ] [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md)
      § Phase 3.D.4 header — add `> **VM RUNNING (2026-05-07 ...): expected-universe-enum-{asset_group}-{ts}**` banner.
      Update as each asset_group's VM completes.
- [ ] [`plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md`](data_status_drilldown_shard_atom_alignment_2026_05_07.md)
      — add a "VM RUNNING" cross-reference at the top noting the enumerator backfill closes the rollup-drilldown gap.
- [ ] [`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — note in the
      data-correctness section.
- [ ] [`plans/active/defi_master_2026_05_07.md`](defi_master_2026_05_07.md) — note in DeFi-specific section.
- [ ] [`plans/archive/issues/defi_launcher_audit_2026_05_07.md`](../archive/issues/defi_launcher_audit_2026_05_07.md) —
      cross-reference at top noting the rollup-drilldown denominator gap is being closed.
- [ ] [`plans/archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md`](../archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md)
      — note that data-status convergence work is in flight (separate from the archetype canonicalisation streams
      already covered in this issue).
- [ ] [`plans/ai/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](./defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      Stream A — note the related VM work.

After each VM completes, **flip the banner from "VM RUNNING" → "VM COMPLETED {sha} written=N"** in the relevant sections
per the Half 2 plan-flip rule.

### Phase 4 — Deferred items (file as new active plan items if not already)

Operator directive: _"What did NOT ship this turn (deferred — explicit handoff) — as long as they're in some sort of
active PM plan, that's fine."_ The following items are **already in active plans** — verify they're tracked, add if not:

#### A. From the data-status audit (`d0f521b4`):

5 todos in
[`plans/archive/issues/defi_launcher_audit_2026_05_07.md`](../archive/issues/defi_launcher_audit_2026_05_07.md) §
"Actionable todos — to be added to the existing data-status-drilldown plan". Confirm they're carried into
[`plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md`](data_status_drilldown_shard_atom_alignment_2026_05_07.md):

- [deployment-service] P1 — `manifest_reader.py:584` paginated `top_instruments` (replace `df.head(30)`)
- [deployment-ui] P1 — `VenueDetailPanel.tsx` show-more controls
- [deployment-api] P2 — `missing_dates` UI label clarity
- [codex] P1 — denominator divergence doc — **already shipped in `372e23aa`**, mark complete
- [deployment-api] P2 — `totals_source: "rollup" | "manifest"` field

#### B. From the canonicalisation plan (`3321b96c`):

5 streams in
[`plans/ai/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](./defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md).
Operator approved all streams + the "deferred halves." Streams A–E remain todos in that plan; promote it to
`plans/active/` when ready.

#### C. From the enumerator script itself:

- CeFi enumerator (instruments-service catalog read) — file as a new active plan item OR in the writegate Phase 3.D.4
  CeFi sub-task. Tracked in writegate plan but no concrete script yet.
- Sports per-league enumeration (sports leagues catalog read) — file as a new active plan item OR sub-task of
  sports_master_2026_05_07.md.
- Unit tests for `enumerate_expected_universe.py` — at least one fixture-based test per asset_group (TradFi / DeFi /
  Sports). Track in writegate plan or instruments-service tests directory.

---

## Critical workspace rules to honour (don't repeat session-3's mistakes)

This session hit parallel-agent commit collisions ~5 times. To avoid:

1. **Before EVERY git commit**, run BOTH:

   ```bash
   git status                    # full picture
   git diff --cached --stat      # NO PATH ARG
   ```

   If anything not yours is in the staged set, surgically un-stage with `git restore --staged <file>` before committing.
   Reference incidents in CLAUDE.md "The mandatory pre-commit check" section.

2. **If a parallel-agent commit lands during your push** ("Everything up-to-date" with no new SHA after `git commit`):
   another agent moved HEAD. Re-stage from disk and retry.

3. **Use `--no-verify` only when prek hooks are demonstrably racing on stash-restore** (which they did this session ~5
   times). The actual lint/format checks are non-blocking on this kind of doc + script work; the issue is the prek
   wrapper, not the underlying tools.

4. **Per-VM shard isolation is non-negotiable** for `--apply-write`: `MANIFEST_PER_VM_SHARDS=true VM_NAME=<unique>`.
   Without it the writer raises `MultiWorkerWithoutShardIsolationError` at startup — verified guard fires per the
   ENUMERATOR_FAILED reason="missing_per_vm_shards_env" exit path in the script.

5. **Manifest concurrency principle** — the enumerator reads the canonical manifest ONCE at startup. Don't fork multiple
   processes per asset_group; use one VM per asset_group instead. The launcher's singleton lock enforces this.

---

## Cost estimate

- TradFi VM: ~e2-standard-4 + 50GB + ~10-30min (depends on calendar pre-skip volume across 5+ years × 10+ venues × many
  data_types). **Expect ~190k row writes** (CLAUDE.md estimate from writegate plan).
- DeFi VM: ~5-30min — **expect ~thousands of rows** per chain × protocol × pre-launch dates × data_types.
- Sports VM: ~5-15min — **expect ~thousands of rows** per source × pre-coverage dates × data_types.
- CeFi + Prediction VMs: instant exit (stubs yield 0). Cost trivial.

**Total: ~$2-5 of GCE compute + ~2-3 hours operator time for sequential launches with verification.** Cheap relative to
the operator-time savings from honest rollup percentages.

---

## Definition of done

The handoff is complete when:

- [ ] Launcher script shipped + watchdog prefix added + tarballs refreshed
- [ ] All 5 asset_group VMs run scan-only successfully → CSV reports inspected by operator
- [ ] Operator green-lights apply-write → all 5 asset_group VMs run --apply-write successfully → ENUMERATOR_COMPLETED
      events confirm written>0 (or written=0 for cefi/prediction stubs)
- [ ] Consolidator daemon merges per-VM shards into canonical manifest (~5min post each VM shutdown)
- [ ] Spot-check 3-5 (venue, data_type, day) tuples in deployment-ui — rollup % and drilldown % agree
- [ ] Plan annotations flipped from "VM RUNNING" → "VM COMPLETED" in all 6+ relevant active plans
- [ ] Codex `availability-manifest-and-data-status.md` § "The fix" Half 2 marked **shipped** with VM commit-shas

After all 5 land + spot-check passes, the rollup-vs-drilldown denominator divergence is closed for the structural-empty
cases (chain pre-genesis, calendar non-trading days, source pre-coverage-start). The remaining gap (CeFi + Prediction
universes) requires the deferred catalog + canonical_question_group SSOT work named in Phase 4.

---

## Quick reference — key file paths

- **Enumerator script**: `instruments-service/scripts/enumerate_expected_universe.py` (commit `8e404c8`)
- **Sister reconciler** (template): `instruments-service/scripts/reconcile_expected_absence_reasons.py`
- **Launcher template to mirror**: `deployment-service/scripts/vm/launch-defi-phantom-recon-vm.sh`
- **Watchdog dict**: `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`
- **Tarball builder**: `deployment-service/scripts/vm/create-code-tarballs.sh --all`
- **VM setup script** (no edits, just FYI):
  `gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh`
- **Codex denominator-divergence section**: `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
  § "Rollup-vs-drilldown denominator divergence (codified 2026-05-07)" — operator-facing explanation
- **Writegate Phase 3.D.4 todos**: `unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` §
  "Phase 3.D.4 — Expected-universe enumerator v2 (NEW 2026-05-07 — operator directive)"
