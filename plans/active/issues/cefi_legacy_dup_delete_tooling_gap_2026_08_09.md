---
doc_type: issue
title:
  cefi legacy-GCS-dup delete (batch2 P1) needs new VM-launcher wiring + fresh candidate-list — est_hours:1.0 badly
  undersells the real scope
summary: >-
  Investigated `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`'s P1 INFRA item ("Delete the legacy GCS
  duplicate objects in `market-data-tick-cefi-prd-central-element-323112`", ~1.08M objects/~9.98TB). The plan assumed a
  ready SAFE-TO-DELETE candidate list just needed a fresh spot-check before running. In reality: the referenced
  `legacy_dup_delete_list_cefi.parquet` is not confirmed to exist in GCS right now (its cefi-specific freshness was
  explicitly excluded from the 2026-07-13 re-audit scope); the only producer of that schema
  (`e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`) does path-membership-only twin checks, not the crc32c
  content-verify the delete-safety protocol's Part 2 requires; and no existing delete tool ran at the workers=32 scale
  the plan's own done_definition specifies. Shipped a properly-hardened, threaded, dual-schema, §3a-gated
  verified-delete tool (`instruments-service/scripts/cleanup_legacy_twins.py`) as the safe part of this work, but the
  ACTUAL execution requires new VM-launcher category wiring
  (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` is a 2351-line security-sensitive bash script with a
  hardcoded per-category dispatch — no generic passthrough exists) plus a genuinely multi-hour VM-scale run, which this
  session did not complete.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [gcs-delete, delete-safety, vm-launcher, cefi, tooling-gap, batch2]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-09
author: slot-16-infra
source: [cross_cutting_satellite_ao_dispatch_batch2-c67c2aa57f37]
assigned_vm: planning
parent_epic: instruments_master
priority: P1
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

The batch2 plan item (`cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` line 225-234) is P1, `est_hours: 1.0`,
and its own text already flags scale for "extra operator awareness" — it asks the worker to "re-confirm the twin-verify
output immediately before running, not trust a stale prior pass." Investigating what that actually requires surfaced a
much bigger gap than a spot-check:

1. **The candidate list's live existence is unconfirmed.** The source plan
   (`instruments_mtds_consistency_remediation_residuals_2026_07_24.md:840-847`) references
   `legacy_dup_delete_list_cefi.parquet` (1,077,672 objs / ~9.98TB) as "ready for operator inspection," but the
   2026-07-13 re-audit that re-verified the other 4 AGs explicitly EXCLUDED cefi from scope
   (`--ag defi,tradfi,sports,pred`) — cefi's own list was never re-confirmed, and it does not exist anywhere on local
   disk in any `.tabs/*` slot clone. It may or may not still exist at
   `gs://market-data-tick-cefi-prd-central-element-323112/_index/audit/legacy_dup_delete_list_cefi.parquet` — this
   session did not verify (would need a live `gcs_describe_object` call, itself deferred pending the scope decision
   below).
2. **The only producer of that exact schema does not satisfy the delete-safety protocol's Part 2.**
   `e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py` classifies SAFE-TO-DELETE by canonical-path MEMBERSHIP
   in a per-day name-set ("no per-object STAT needed, far faster" — its own docstring) — this proves twin EXISTENCE
   (Part 1, weakly) but never CONTENT equivalence (Part 2: crc32c match). Per
   `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1's own R5 precedent, existence-only is exactly the
   failure mode that would have destroyed 32 high-TVL legacy-only defi pools had it not been caught — "the paths looked
   duplicated; the content was not."
3. **No existing delete tool ran at the plan's own specified scale.**
   `instruments-service/scripts/cleanup_legacy_twins.py` (the one tool that DOES crc32c-verify, CF-21) had a plain
   sequential `for` loop with no `--workers` — contradicts the plan's stated done_definition ("gcs_delete_object runs
   (in-region VM, workers=32)"). It also only consumed `migration_orphan_sweep.py`'s output schema, not the schema
   `audit_legacy_gcs_dup_delete_list.py` actually produced.
4. **`launch-canonical-migration-vm.sh` has no generic dispatch.** It is a 2351-line bash script where every migration
   category is a hardcoded `elif [[ "$cat" == "..." ]]` branch with its own command-builder function, under strict
   shell-injection validation (comma-free `--metadata` embedding, `WORKERS`/bucket-name regex gates). Adding a new
   category (e.g. `cefi-legacy-dup-cleanup`, which would reuse the already-registered `canonical-migration-cefi-`
   `VM_PREFIX_TO_BUCKET` prefix — no new registry entry needed) is real, security-sensitive engineering, not a config
   change.

# What I shipped this session

`instruments-service/scripts/cleanup_legacy_twins.py` — enhanced to:

- Accept EITHER candidate-list schema (auto-detected): `migration_orphan_sweep.py`'s `obj_class`/venue/chain/...
  columns, or a prior audit's `legacy_path`/`canonical_twin_path`/`classification` columns (carries the known canonical
  path through, but ALWAYS re-verifies crc32c fresh — never trusts the source list's own membership check).
- `ThreadPoolExecutor`-based verify (fresh `gcs_describe_object` for both legacy + canonical twin, workers configurable,
  default 32) and delete (`gcs_conditional_delete` keyed to the generation captured at verify time — closes the
  verify-then-delete race).
- A FRESH, same-run `gcs_bucket_soft_delete_retention_seconds()` check before any `--apply`, aborting if < 604800s
  (delete-safety protocol §3a) instead of trusting a cached/prior claim.
- A post-delete verification pass: every URI believed deleted is re-`gcs_describe_object`'d to confirm it now resolves
  to `None`; a nonzero "still present" count is a hard failure (exit 3).

This is genuinely useful, low-risk (still `--dry-run` by default, existing unit tests unchanged/passing) work, but it is
NOT sufficient on its own — nothing has walked the actual cefi bucket or deleted anything yet.

# Why it matters

This is a 9.98TB, ~1.08M-object PROD delete — the largest single delete in the whole batch2 plan (its own text says so).
Rushing either (a) a new category into a 2351-line security-sensitive VM launcher, or (b) a multi-hour-to-day GCS-scale
walk+verify+delete run, inside a single continuous session without room for careful review, is a worse outcome than
scoping it properly. The plan's `est_hours: 1.0` reflects the (incorrect) assumption that the candidate list was ready
and only needed a spot-check.

# Recommended decision

- [x] ✅ [INFRA] P1. Confirm whether
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/audit/legacy_dup_delete_list_cefi.parquet` currently
      exists (single `gcs_describe_object` call). If absent, run
      `migration_orphan_sweep.py --asset-group cefi --workers 32 --report-out gs://.../orphan_sweep_cefi_fresh_<date>.parquet`
      on an in-region VM (this IS the sanctioned single-walk tool for this exact purpose, CF-17) to regenerate a
      trustworthy class-B candidate list — this alone is a multi-hour run given cefi's corpus size. Repo:
      instruments-service. — **EXISTS** (confirmed via a live `gcs_describe_object` call, slot-14, 2026-08-09):
      `size=33860018` bytes, `last_modified=2026-07-02T20:39:21.182000+00:00`, `crc32c=g+UWHw==`,
      `generation=1781804372051559`. Object is present so the "if absent" regenerate branch does not trigger — no
      `migration_orphan_sweep.py` VM run needed for THIS todo. Caveat for the next todo (VM-launcher wiring + dry-run):
      this list's `last_modified` (2026-07-02) predates the 2026-07-13 re-audit that excluded cefi from scope, so its
      content freshness is still UNVERIFIED beyond bare existence — the dry-run's own verify pass (fresh
      `gcs_describe_object` + crc32c re-check per object, per `cleanup_legacy_twins.py`) is what actually re-validates
      it, not this existence check alone.
- [ ] [INFRA] P1. Add a new `cefi-legacy-dup-cleanup` category to `launch-canonical-migration-vm.sh` (reuses the
      already-registered `canonical-migration-cefi-` VM_PREFIX_TO_BUCKET prefix, no new registry entry): dry ->
      `cleanup_legacy_twins.py --asset-group cefi --report-uri <candidate-list> --workers 32` (no `--apply`); full ->
      same + `--apply --i-understand`. Follow the existing category-builder pattern (comma-free command string,
      `WORKERS` already validated as a bare positive integer by the launcher's existing gate). Repo: deployment-service.
- [ ] [INFRA] P1. Launch the dry-run category first, verify deletable/blocked counts + a few blocked reasons are sane
      against the expected ~1.08M/~9.98TB, THEN launch full (`--apply`). No fire-and-forget — verify STARTED <60s,
      periodic progress (verify + delete counts logged every 50k), and a terminal state; monitor via a progress-metric
      poll (checkpoint/log line count), not activity. Repo: deployment-service, instruments-service.
- [ ] [REVIEW] P1. After the full run's post-delete verification reports 0 "still present," flip the original checkbox
      in `/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` citing the VM run's evidence (deleted
      count, post-delete-verify result). Repo: unified-trading-pm.

# Progress Log

- 2026-08-09 (slot-16): investigated, shipped `cleanup_legacy_twins.py` hardening, filed this issue doc; the original
  batch2 checkbox stays unchecked pending the todos above.
- 2026-08-09 (slot-11): dispatched only the 4th todo (flip the batch2 checkbox). Confirmed the other 3 todos are still
  `queued` in the backlog (ids `cefi_legacy_dup_delete_tooling_gap-{d2c76ca9ef30,e03a4801e66b,8e4ddd1a79a5}`) — no
  commits landed against `launch-canonical-migration-vm.sh` or a new `cleanup_legacy_twins.py` run since the prior
  session's hardening; no VM run evidence exists. This todo has no `prereqs.completed_tasks` gate on the other 3, so the
  dispatcher handed it to slot-11 anyway even though its done_definition (cite a completed full-run's post-delete
  verification) is unsatisfiable right now. Filed BLK-33bbcb2a recommending a dependency gate be added rather than
  fabricating a flip. Checkbox intentionally left unflipped.
- 2026-08-09 (slot-14, task `cefi_legacy_dup_delete_tooling_gap-d2c76ca9ef30`): ran the single `gcs_describe_object`
  call on `legacy_dup_delete_list_cefi.parquet` — it EXISTS (33,860,018 bytes, `last_modified=2026-07-02T20:39:21Z`,
  `crc32c=g+UWHw==`, generation `1781804372051559`). Flipped todo 1. No `migration_orphan_sweep.py` VM run was triggered
  since the "if absent" branch didn't fire. Flagged for the next todo: the list's mtime predates the 2026-07-13 re-audit
  that excluded cefi, so freshness beyond bare existence is still unverified — that's the dry-run verify pass's job, not
  this todo's.
