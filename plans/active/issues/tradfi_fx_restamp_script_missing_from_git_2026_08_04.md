---
doc_type: issue
title:
  TradFi FX restamp script (`restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py`) is missing from git entirely —
  the production CAS-apply it performed is real and verified, but its source code was never committed
summary: >-
  Incidental finding from a `/context-scout` Phase 1 research pass over
  `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md`. That doc's parent
  (`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`, Progress Log entry "2026-08-03 (slot 8,
  data_engineering)") describes building `market-tick-data-service/scripts/restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py`
  (+ a 31-test regression suite), taking a pre-apply GCS snapshot, CAS-applying a content-verified instrument_id
  restamp against the live production manifest index (25 of 3,795 affected rows; generation `1785798001134900` →
  `1785798271092627`), verifying rows-in==rows-out (6,600,311), and resuming the paused consolidator cron. The doc
  explicitly states "Script kept in place, NOT deleted... will be re-run once the two follow-up todos land."
  **The script does not exist anywhere**: not at `market-tick-data-service` HEAD, not in `git log --all
  --diff-filter=A` (full history, any branch), not in any other slot's worktree under `.tabs/*/market-tick-data-service/`,
  not in the root clone. Independently verified the claimed production mutation is nonetheless real: the pre-apply
  backup object `gs://market-data-tick-tradfi-prd-central-element-323112/_index/backups/availability_index.pre_fx_spot_pair_instrument_id_restamp_apply_20260803T230354Z.parquet`
  exists in GCS with `creation_time: 2026-08-03T23:03:54+0000` — exactly matching the timestamp embedded in its own
  filename. This is very likely genuine work whose SOURCE CODE was simply never committed/pushed (a Commit+Push+Flip
  HARD RULE violation / lost-work incident), not a fabricated Progress Log entry — but that can't be proven 100% from
  documentation alone, only inferred from the snapshot's independent corroboration. Either way,
  `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` todo P3 ("re-run `restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py
  --apply`") is currently **not executable as written** — the script must be recovered or rebuilt first.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    tradfi,
    fx,
    manifest,
    commit-push-flip,
    lost-work,
    audit-trail,
    process-gap,
    context-scout,
  ]
related:
  [
    /plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/active/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: 2026-08-04
last_updated: 2026-08-04
parent_epic: tradfi_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: context_scout_auditor (agt-c156dc, 2026-08-04, incidental finding during Phase 1 doc research)
---

# TradFi FX restamp script missing from git — production mutation real, source code lost

## Why this matters

A plan doc's Progress Log is only trustworthy as an audit trail if the artifacts it describes actually exist. Here the
underlying claim (a real production GCS manifest mutation, CAS-applied with a pre-apply snapshot and post-apply
verification) checks out against independent evidence — but the script that performed it is gone from version control,
so:

1. The open follow-up todo that depends on it (`tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` P3) cannot
   be executed as written.
2. If this happened once, silently, it may not be isolated — any other Progress Log entry making a similar
   "built + ran against production" claim deserves the same scrutiny.
3. Per `/codex/12-agent-workflow/commit-push-flip-rule.md`, shipping code without committing it is the #1 tracked
   false-progress failure mode in this workspace — this is a concrete instance of exactly that class, on a script that
   touched production data.

## Evidence

- **Claim** (`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`, Progress Log, "2026-08-03 (slot 8,
  data_engineering)"): built `market-tick-data-service/scripts/restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py`
  (+ 31-test regression suite); pre-apply snapshot to
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/backups/availability_index.pre_fx_spot_pair_instrument_id_restamp_apply_20260803T230354Z.parquet`;
  CAS-applied via the shared `_scheduler_pause_resume_2026_07_30.py` maintenance-window primitive; old generation
  `1785798001134900` → new generation `1785798271092627`; verified rows-in==rows-out (6,600,311); resumed the
  `uts-prod-manifest-consolidator-market-data-tradfi-cron`.
- **Verified MISSING** (2026-08-04): `git log --all --oneline --diff-filter=A -- '*restamp_tradfi_fx_spot_pair*'` in
  `market-tick-data-service` returns nothing (checked with the clone fully current: 0 ahead / 0 behind
  `origin/live-defi-rollout`). `find . -iname "*restamp_tradfi_fx_spot_pair*"` finds nothing. Checked every other
  slot's `.tabs/*/market-tick-data-service/scripts/` and the root clone — not present anywhere. The only two places
  this filename appears in the entire workspace are the two related plan docs' own prose.
- **Verified REAL** (2026-08-04): `gcloud storage objects describe` on the claimed backup object succeeds —
  `generation: '1785798234687049'`, `creation_time: 2026-08-03T23:03:54+0000`, `size: 118833291` — the creation
  timestamp exactly matches the `20260803T230354Z` embedded in the filename itself, which is strong independent
  corroboration the described operation genuinely ran (a fabricated claim would be very unlikely to also fabricate a
  real, correctly-timestamped GCS object). The live index's current generation (`1785805792126573`, checked
  2026-08-04) is neither the claimed old nor new generation, which is expected — normal cron consolidation has moved
  it many times since 2026-08-03.
- **Not independently checked** (out of this finding's scope): whether the 25-row restamp itself is still intact in
  the current manifest (i.e., re-verifying the claimed generation-to-generation diff's actual row content) — the
  point of this issue is the missing source, not re-auditing the data outcome, which the original doc already
  verified at the time (rows-in==rows-out).

## Open todos

- [ ] [OPERATOR] P2. Decide recovery path: (a) check whether slot 8's 2026-08-03 session/task artifacts are retained
      anywhere recoverable (agent-orchestrator dispatch history, tmux scrollback, any other durable session record) —
      if the original script can be recovered verbatim, prefer that; or (b) rebuild it fresh from the fully-detailed
      6-step spec already written in `tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s Progress Log
      (soft-delete retention check → snapshot → content-verified per-shard read-and-extract restamp → CAS-apply via
      `_scheduler_pause_resume_2026_07_30.py` → verify rows-in==rows-out → resume cron) — the spec is detailed enough
      to reconstruct from. Either path unblocks `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` todo P3.
- [ ] [SCRIPT] P2. Once recovered or rebuilt: commit + push to `market-tick-data-service` immediately, same turn
      (Commit+Push+Flip, per `/codex/12-agent-workflow/commit-push-flip-rule.md`) — do not leave it locally
      uncommitted again. Re-run `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` todo P3 once its own two
      blocking prerequisites (phantom-row root-cause, duplicate-row dedup) land.
- [ ] [SCRIPT] P3. Bounded audit: grep the rest of the corpus (`plans/active/` + `plans/active/issues/`) for other
      Progress Log entries claiming a script was "Built" and used against production without a `repo@sha` citation
      near the claim (this entry had none, unlike every other claim in its own doc-chain) — scoped check, not a full
      corpus-wide forensic sweep; report count found (including 0) rather than silently expanding scope.

## Progress Log

- **2026-08-04**: Filed by `context_scout_auditor` (dispatch `agt-c156dc`) as an incidental finding during
  `/context-scout` Phase 1 research on `tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` (batch C sub-agent
  surfaced the dead pointer; main agent independently verified both the absence from git and the GCS backup object's
  authenticity before filing). No fix attempted — outside this role's scope (context-scout only ever writes
  `context_scope` + a dated marker to existing docs; this is a new, separate finding needing its own record per the
  workspace's big-finding/findings-triage HARD RULE).
