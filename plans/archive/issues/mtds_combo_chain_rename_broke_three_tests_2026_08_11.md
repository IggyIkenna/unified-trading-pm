---
doc_type: issue
title: >-
  market-tick-data-service's combo→combo_chain rename (c31cfe7a) missed the reader's own copy of the partitioned-types
  set, misrouting every combo_chain read + leaving 3 tests asserting stale bare-``combo`` behavior — plus a same-batch
  file-size-cap split blocked on a net-new blanket pyright-suppression-header regression on the LDR→main promote PR
summary: >-
  c31cfe7a (2026-08-11, "rename combo wrapper to combo_chain across writer + manifest") updated the writer + manifest to
  the new ``combo_chain`` instrument_type but left ``reader.py``'s own ``_UNDERLYING_PARTITIONED_TYPES`` frozenset still
  keyed on the old bare ``combo`` — so every ``combo_chain`` read (tradfi + cefi) silently misrouted through the
  single-file-per-instrument path meant for non-chain types instead of the underlying-partitioned chain path. 3 tests
  (``test_cefi_combo_stays_bare_underlying_ticks_parquet``, ``test_tradfi_combo_stays_bare_underlying_ticks_parquet``,
  ``test_cme_combo_shard_itype_stays_lowercase_id_stays_empty``) still asserted the OLD pre-rename behavior and failed
  red against the new naming. Fixed + shipped by a parallel session (market-tick-data-service@b13e3a2b, same commit that
  also split the two files crossing the 900-line file-size cap per the sibling ci-reconcile issue doc's P1 follow-up).
  This session's own pass found that commit's promote PR (#952, LDR→main) still red on a DIFFERENT gate: the split-out
  ``migrate_tradfi_canonical_classify_2026_07.py`` and the already-landed
  ``migrate_tradfi_underlying_display_names_2026_08.py`` both carried a blanket file-level ``# pyright: reportX=false,
  ...`` suppression header that is net-new relative to `main` (STEP 5.94's diff-scoped attribution ratchet) — fixed by
  converting both files to narrow per-line ``# pyright: ignore[exactRule]`` suppressions plus two genuine type-safety
  improvements (a typed ``_Args`` dataclass boundary for the argparse Namespace, a named function replacing an
  unannotated lambda passed to ``ThreadPoolExecutor.map``), verified 0 basedpyright errors on both files with the
  blanket headers fully removed. The originally-flagged empty-string-fallback ratchet overage (baseline 66, commit
  486f82ba added 5 sites → 71) was independently already resolved by the time of this fix: the same b13e3a2b split
  commit's net effect left the corpus at 64 sites (7 below its own post-486f82ba peak), so no baseline bump or code
  change was needed there.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags:
  [
    tradfi,
    combo-chain,
    reader-routing,
    test-regression,
    file-size-cap,
    basedpyright,
    blanket-pyright-suppression,
    quality-gates,
    promote-pr,
  ]
related:
  [
    /plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md,
    /plans/archive/issues/mtds_blanket_pyright_suppressions_ssot_contradiction_2026_07_30.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
context_scope:
  [
    /plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
    market-tick-data-service/market_tick_data_service/reader.py,
  ]
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-11
parent_epic: tradfi_master
priority: P1
source: >-
  Operator-authorized follow-up to ci_reconcile_overnight_batch_2026_08_11.md item 10 (file-size-cap split blocking PR
  #950/#951) — dispatched as a combined fix-both-blockers-and-ship task; found on arrival that the reader-routing fix +
  test updates + file split were already shipped by a parallel session (market-tick-data-service@b13e3a2b, authored
  [slot-4·laptop]) between task assignment and execution (high-velocity shared repo). This session's contribution:
  diagnosed + fixed the resulting promote PR's (#952) net-new blanket-pyright-suppression-header regression, confirmed
  the empty-string-fallback ratchet was already clean, and shipped both fixes.
assigned_vm: planning
resolved_by:
  "market-tick-data-service@b13e3a2b (reader routing + 3 tests + file split); market-tick-data-service@ccb84c57c9 (this
  session — blanket-suppression-header narrow-ignore conversion, shipped via quickmerge)"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# combo→combo_chain rename broke the reader + blocked the file-size-cap split's promote PR

## What happened

`c31cfe7a` ("feat(tradfi): rename combo wrapper to combo_chain across writer + manifest", 2026-08-11) renamed the
bundle-grain wrapper instrument_type from bare `combo` to `combo_chain` in the writer + manifest, but
**`market_tick_data_service/reader.py`'s own `_UNDERLYING_PARTITIONED_TYPES` frozenset was not updated** — it still read
`frozenset({"options_chain", "futures_chain"})`, missing the new `combo_chain` value. Since this frozenset decides which
instrument types route through the underlying-partitioned chain-read path vs. the single-file-per-instrument path, every
`combo_chain` object (tradfi AND cefi — the frozenset is asset-group-agnostic) silently misrouted through the wrong read
path after the rename landed.

Three pre-existing tests still asserted the OLD bare-`combo` behavior and failed red against the renamed `combo_chain`:

- `tests/unit/test_partitioned_writer_cefi_chain_tail_v6.py::test_cefi_combo_stays_bare_underlying_ticks_parquet`
- `tests/unit/test_partitioned_writer_tradfi_filename_canonical.py::test_tradfi_combo_stays_bare_underlying_ticks_parquet`
- `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py::TestTradfiRecordVenueShardCountsCanonicalization::test_cme_combo_shard_itype_stays_lowercase_id_stays_empty`

Separately, this exact rename's `e5581a63` parent commit pushed two files over the 900-line file-size hard cap
(`partitioned_writer.py` 906L, `migrate_tradfi_canonical_2026_07.py` 905L), blocking `live-defi-rollout` and promote PR
#950/#951 — tracked as `ci_reconcile_overnight_batch_2026_08_11.md` item 10's P1 follow-up.

## Resolution

**Reader fix + test updates + file split — already shipped before this session's fix landed**, by a parallel session on
the same repo (`market-tick-data-service@b13e3a2b988ad82b55ffd9c4cddda2568859d5bc`,
`fix(tradfi): combo_chain reader routing + split 2 files past the 900-line SRP cap`, `[slot-4·laptop]`,
2026-08-11T08:18:40+01:00):

- `reader.py`: added `combo_chain` to `_UNDERLYING_PARTITIONED_TYPES`.
- All 3 tests updated to assert the NEW intentional `combo_chain` behavior (v6 quote/margin chain tail, populated id)
  instead of the old bare-`combo` exclusion — verified correct against `c31cfe7a`'s own stated intent, not a blind
  revert (diff reviewed in this session; each test's new assertion matches the writer's actual v6-chain-tail behavior
  for `combo_chain`).
- `partitioned_writer.py` split 906L→846L (extracted 4 pure chain-partition-dims/timestamp helpers into
  `engine/orchestrator/chain_partition_dims.py`, re-exported, zero call-site changes).
- `migrate_tradfi_canonical_2026_07.py` split 905L→562L (extracted the disposition-classification
  - canonical-target-derivation half into `scripts/migrate_tradfi_canonical_classify_2026_07.py`, 45 names re-exported,
    zero call-site changes across 5 downstream production scripts).
- 300+ tests passing across both split files and every downstream consumer (per that commit's own message; independently
  re-verified in this session — `tests/unit/scripts/test_migrate_tradfi_canonical_2026_07.py`, 33/33 passing).

**This session's own contribution** (found b13e3a2b's promote PR #952 still red on arrival, diagnosed + fixed at the
root):

1. **PR #952 (LDR→main) `quality-gates-v2` was failing on `lint-codex` / STEP 5.94** (blanket file-level
   pyright-suppression header — diff-scoped attribution ratchet vs. `main`'s tip,
   `market-tick-data-service/scripts/quality-gates.sh` lines 607-639). Both
   `migrate_tradfi_canonical_classify_2026_07.py` (new in b13e3a2b's split) and
   `migrate_tradfi_underlying_display_names_2026_08.py` (new in `486f82ba`, still unreleased to `main`) carried the
   fleet's common 7-check blanket header (`# pyright: reportAny=false, reportUnknownMemberType=false, ...`) — net-new
   relative to `main`'s diff base, tripping the ratchet even though the pattern itself is pre-existing/common elsewhere
   in the repo (`mtds_blanket_pyright_suppressions_ssot_contradiction_2026_07_30.md`). Per that issue doc's own
   established precedent ("verify the header is gratuitous before keeping it — a header-stripped copy passing
   basedpyright clean means delete it"), ran `basedpyright` with both headers stripped: NOT gratuitous (61 real errors
   across both files, mostly `reportAny`/`reportUnknown*` cascading from `argparse.Namespace`'s inherent untyped-ness).
   Fixed at the root rather than re-adding the blanket header:
   - `migrate_tradfi_underlying_display_names_2026_08.py`: introduced a typed `_Args` frozen dataclass + `_parse_args()`
     boundary function — the single deliberate point where `argparse.Namespace`'s Any-ness is unavoidable (narrowly
     ignored there, 7 lines, each with a `# pyright: ignore[reportAny]  # argparse.Namespace is untyped` reason) —
     eliminating ~40 cascading `reportAny`/`reportUnknownArgumentType` errors that used to be scattered across every
     `args.X` call site in `main()`/`run_manifest_and_reconcile()`/`run_apply()`. Replaced an unannotated
     `lambda f: _apply_one(f, bucket=bucket)` passed to `ThreadPoolExecutor.map` with a named, fully-typed
     `_apply_bound(full: str) -> tuple[str, str]` closure — a real fix, not a suppression, removing 3 more errors
     outright. Remaining genuine library-stub gaps (gcsfs `cat_file`, pyarrow `read_table`/`to_pylist()` — both
     `reportUnknownMemberType`/`reportAny`) and 4 deliberate cross-module private-symbol reuses
     (`_canonical_chain_path`, `_classify_disposition`, `_kv`, `_rel` imported from the base migrator, by design, for
     byte-identical lockstep with the writer) got narrow single-line `# pyright: ignore[exactRule]` markers instead of
     the blanket header. Verified
     `basedpyright market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py` →
     `0 errors, 0 warnings, 0 notes`.
   - `migrate_tradfi_canonical_classify_2026_07.py`: annotated the dynamic `getattr(InstrumentType, enum_name)` result
     with an explicit `InstrumentType` return type (narrow `reportAny` ignore on that one unavoidable dynamic-lookup
     line, reason cited) and added narrow `# pyright: ignore[reportPrivateUsage]` on the two deliberate reuse imports
     (`_HYPHEN_ITYPE_MAP`, `_parse_hyphen` from the base v9 migrator). Verified
     `basedpyright market_tick_data_service/scripts/migrate_tradfi_canonical_classify_2026_07.py` →
     `0 errors, 0 warnings, 0 notes`.
   - Ran `ruff check --fix` to let the import-formatter re-wrap the now-longer single-line imports into their canonical
     multi-line form (the narrow-ignore comments correctly stayed pinned to each individual imported name's own line,
     not the `from ... import (` line — verified this is load-bearing: pyright only honors an inline ignore on the exact
     reported line).
2. **The empty-string-fallback ratchet (STEP 5.101,
   `unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml`) was independently already clean by
   the time of this fix** — re-measured live via `check_no_empty_string_fallback.py --scope market-tick-data-service`:
   current count **64**, baseline **66** (WARN "ratchet the baseline down", not a failure). `486f82ba` genuinely did add
   5 new `.get(key, "")` sites to `migrate_tradfi_underlying_display_names_2026_08.py` as originally reported, but the
   SAME `b13e3a2b` split commit's net changes across the two split files left the corpus 7 sites lower than its
   post-`486f82ba` peak — no baseline bump or code change was needed by the time this session ran the check. No action
   taken (verified, not assumed).
3. Full local `bash scripts/quality-gates.sh --no-fix` re-run green after the fixes (ruff, 300+ basedpyright-clean
   files, full pytest suite, file-size cap, both STEP 5.94/5.101 ratchets).
4. **Shipped**: `market-tick-data-service@ccb84c57c9` via
   `quickmerge.sh --agent --files 'market_tick_data_service/scripts/migrate_tradfi_canonical_classify_2026_07.py market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py'`.
   Landed on `live-defi-rollout`; post-push ancestry verified; `quality-gates-v2` on that branch for `ccb84c57c9` =
   SUCCESS (confirmed via `gh run list`).

## Two more moving-target regressions hit + resolved during the ship attempt

Both encountered mid-ship, both self-resolved by the SAME parallel session (`[slot-4·laptop]`) that had already fixed
the reader routing — not fixed by this session, just diagnosed + waited out per the "don't chase an ever-moving target
indefinitely" guidance:

1. **`quickmerge.sh`'s STAGE 0.4 fast-forward pull picked up two more of that session's commits mid-attempt**
   (`fbc9cc6f` "correct migration-script combo target-path remap + implement instrument_id-blank design for chain-bundle
   rows", `143fceff` "retire the now-backwards combo-blank-id restamp script"). `fbc9cc6f` deleted
   `_tradfi_manifest_shard.py::_resolve_chain_bundle_manifest_id` as part of a deliberate design change (chain-bundle
   rows now get a blank `instrument_id` unconditionally, matching `combo_chain`'s pre-existing behavior) but left
   `tests/unit/scripts/test_restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py` + its target script
   importing the now-deleted symbol — 26 test-collection `ERROR`s on the first quickmerge attempt. Diagnosed (not fixed)
   in this session: the whole restamp script's premise (blank `instrument_id` = a bug to fix) was now the INVERSE of the
   new deliberate design, so a narrow import-fix would have been wrong — the correct move was deletion, per "delete
   deprecated code, no shims." Before this session acted on that diagnosis, the same parallel session shipped exactly
   that fix (`143fceff`, "delete per the 'delete deprecated code, no shims' rule") — pulling it via `git fetch` resolved
   the 26 errors with zero action needed here.
2. **A workspace-wide cross-repo check (`STEP 5.94`'s neighbor in the log, actually
   `check_adapter_contract_regression.py` / the `[5.70/6] IS-MTDS CONTRACT INTEGRITY` section) flagged
   `deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py`** at 0 contract calls vs. baseline 1
   — genuinely live on `deployment-service`'s own `live-defi-rollout` (confirmed via a clean `git diff`, not a
   local-only artifact), but entirely unrelated to MTDS: a different repo, actively tracked in
   `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`'s own `meta_watchers` P2 todo, and introduced by a
   legitimate `deployment-service` refactor commit (`0c38c00d`) this session has no domain standing to fix blind. This
   check has no `--scope` parameter (scans the full workspace regardless of which repo's `quality-gates.sh` invoked it)
   and would NOT be reproduced by MTDS's own isolated CI clone (`deployment-service` is not an MTDS dependency, so CI
   never checks it out as a sibling) — confirmed by PR #952's actual CI failure reason being `ruff` (lint-codex), never
   this check. `quickmerge.sh` itself correctly classified the resulting re-gate failure as
   duration-budget/host-contention (its own printed diagnostic: "Re-gate hit ONLY the duration budget — every content
   check passed... re-run with IGNORE_TIMEOUT=true if the content already gated green") — re-ran with
   `IGNORE_TIMEOUT=true` once MTDS's own core gate was independently confirmed green (sentinel written,
   `ALL QUALITY GATES PASSED` banner), which shipped cleanly. No deployment-service changes made from this session —
   outside scope, actively owned elsewhere.

Two removed stray broken self-referential symlinks (`unified-api-contracts/unified-api-contracts`,
`market-tick-data-service/market-tick-data-service`, both `-> ../../<name>`, both broken/unusable) were blocking
quickmerge's pre-flight dependency-cleanliness audit — deleted (not committed; not real content, environment artifacts
from the `.tabs/N` slot structure) rather than following the audit's literal "git add -A + commit" suggestion, which
would have been wrong per the `git add -A` ban.

## Verification

- `.venv/bin/basedpyright market_tick_data_service/scripts/migrate_tradfi_canonical_classify_2026_07.py market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py`
  → `0 errors, 0 warnings, 0 notes`.
- `.venv/bin/ruff check` on both files → `All checks passed!`.
- `.venv/bin/python -m pytest tests/unit/scripts/test_migrate_tradfi_canonical_2026_07.py -q` → `33 passed`.
- `python3 check_no_empty_string_fallback.py --scope market-tick-data-service` → `64 < baseline 66` (pass).
- Full `bash scripts/quality-gates.sh --no-fix` → green (MTDS's own core gate; the one residual workspace-wide
  cross-repo finding is documented above, not MTDS's to fix).
- `market-tick-data-service@ccb84c57c9` landed on `live-defi-rollout`; `gh run list --branch live-defi-rollout` shows
  `quality-gates-v2` = `success` for that sha.
- Promote-PR chain: #950/#951/#952 all superseded (closed) as LDR advanced past each; #953 (for the intermediate
  `143fceff`) was still open as of this doc's writing, predating `ccb84c57c9`. The `ldr-to-main-promote-fleet.yml` fleet
  job runs on a `*/15` cadence and was NOT manually dispatched per CLAUDE.md's explicit ban on ad-hoc triggering (shared
  single-concurrency slot, starves the queue) — the next scheduled run will open/update the promote PR for `ccb84c57c9`.
  See the sibling `ci_reconcile_overnight_batch_2026_08_11.md` item 10 follow-up for the eventual PR-green + auto-merge
  confirmation.

## Follow-ups

- [x] ✅ [OPERATOR] P2. Confirm `market-tick-data-service@ccb84c57c9` promotes LDR→`main` cleanly — CONFIRMED (content-
      verified 2026-08-15, see Progress Log). Doc `status` flipped to `resolved` + archived per
      plan-completion-and-archival-discipline.

## Progress Log

- **2026-08-15 (tradfi_satellite_ao_dispatch_batch13 item)**: Confirmed `ccb84c57c9`'s promotion — NOT a literal SHA
  ancestor of `origin/main` (`git merge-base --is-ancestor` false, and no matching `git patch-id` on any `main` commit
  in the 2026-08-11..13 window either), because `main-backmerge-to-ldr`'s "Option-B direct" promote bulk-pushes/squashes
  many LDR commits per promote event rather than preserving individual commit hashes — expected, not a defect. Verified
  the actual SUBSTANCE instead: `migrate_tradfi_canonical_classify_2026_07.py` on `main` is byte-identical to
  `ccb84c57c9`'s version. `migrate_tradfi_underlying_display_names_2026_08.py` differs from `ccb84c57c9`'s raw diff, but
  only because a later, unrelated, legitimate commit (`c1559849`, 2026-08-14, "unblock STEP 5.101 baseline via noqa
  annotations on unrelated pre-existing tradfi migration script") re-touched the same lines for the DIFFERENT
  empty-string-fallback ratchet check — confirmed `origin/live-defi-rollout`'s current tip matches `origin/main` exactly
  on this file (no LDR/main divergence, no lost work). Confirmed neither file carries a reintroduced blanket
  `# pyright: reportX=false, ...` header on `main` (`grep '^# pyright:'` → 0 hits both files) — `ccb84c57c9`'s actual
  STEP-5.94 fix (narrow per-line ignores, no blanket header) is intact and live on `main`. Fleet-wide
  `scripts/cicd/promotion_lag_monitor.py` (run via `.venv`) independently reports "all branches in sync" — the promote
  pipeline itself is healthy, not stuck. Conclusion: `ccb84c57c9` promoted LDR→main cleanly in substance; the SHA itself
  is absent from `main`'s ancestry only due to the promote mechanism's own squash/bulk-push shape, not a lost or dropped
  commit. Flipping this doc to `resolved` + archiving per the follow-up's own instruction.

- **context-scout 2026-08-14**: populated context_scope (3 entries).

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- **2026-08-11 (this session)**: Filed retrospectively — the reader-routing + test fixes + file split (b13e3a2b) were
  already shipped by a parallel session before this task's diagnosis phase completed (high-velocity shared repo,
  multiple concurrent AO/interactive workers). This session's actual contribution was diagnosing + fixing the resulting
  promote PR's net-new blanket-pyright-suppression-header regression (STEP 5.94) and confirming the
  empty-string-fallback ratchet was a non-issue by the time of measurement. Shipped
  `market-tick-data-service@ccb84c57c9` after riding out two more moving-target regressions from the same parallel
  session (see section above) and a workspace-wide cross-repo check flagging an unrelated `deployment-service` file (out
  of scope, not fixed). `quality-gates-v2` green for the shipped sha on `live-defi-rollout`. Promote-to-main not yet
  confirmed (fleet job on its own `*/15` cadence, not manually triggered per CLAUDE.md). Archiving deferred until that's
  confirmed (see sibling doc's item 10 follow-up).
- **2026-08-11 (this session, self-correction)**: A concurrent hygiene pass (`unified-trading-pm@e1a93a4e83`, a
  different parallel session) independently found this doc duplicated against an earlier, less-complete archived draft
  and correctly resolved it by keeping THIS active twin + discarding the archived one — landing between this session's
  own ship commit and its doc-push. Acting on stale local state, this session then mistakenly deleted this (the
  surviving, correct) copy in a follow-up doc-push, believing it was cleaning up a stale duplicate of the
  already-discarded archive version. Caught via `git log`/`git show` on the immediately-following push's diff and
  restored verbatim from the shipped `cb026aa28a` blob. `ci_reconcile_overnight_batch_2026_08_11.md`'s pointer (which
  had been flipped to the now-deleted archive path in the same mistaken push) is being flipped back to this active path.
  Net effect: no information lost, corrected within the same session.
