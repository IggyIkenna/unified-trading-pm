---
doc_type: plan
title: TradFi manifest/content recovery completion — Progress Log companion round 2 (2026-07-21/22 continuation section)
summary: >-
  Companion doc to `tradfi_manifest_content_recovery_completion_2026_07_24.md` — the verbatim "Progress Log —
  2026-07-21/22 continuation (writer fix, fleet drain, manifest-script bug, pre-compact checkpoint)" section (writer bug
  fix confirmation, VM fleet drain, manifest-script bug diagnosis, lessons-carried-forward, and the 2026-07-21/22
  deferred-work ordering), extracted for line-cap compliance (the live doc hit exactly 1000/1000 lines with no headroom
  for the context_scope backfill). Zero open todos lived in this section (verified before extraction); fully superseded
  by the parent's later "Progress Log — 2026-07-22" section, which is the doc's own live source of truth going forward.
  Mirrors the identical round-1 extraction this same parent doc already got 2026-07-24
  (`/plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md`).
status: complete
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [data-correctness, manifest-writer, tradfi, history, line-cap-remediation]
related: [/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Line-cap remediation per plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md's
  `[SCRIPT] P3` todo.
---

# TradFi manifest/content recovery completion — Progress Log companion round 2

> Extracted verbatim 2026-08-03 (line-cap remediation, live plan was at 1000/1000 lines) from
> `/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`'s "## Progress Log — 2026-07-21/22
> continuation" section, in full. The live plan keeps only its "## Progress Log — 2026-07-22 (all migration work moved
> to VMs — time/credit-constrained finish)" section onward inline going forward (which itself explicitly supersedes the
> section below); everything below was here before that.

## Progress Log — 2026-07-21/22 continuation (writer fix, fleet drain, manifest-script bug, pre-compact checkpoint)

**Read this section FIRST on resume — it supersedes the sequencing above with what's actually true now.**

### DONE + VERIFIED (durable, pushed)

- **Writer bug fixed**: `mtds@56d39325` — `equity`/`etf`/`index` manifest `record_captured` now uses the same canonical
  id + UPPERCASE type the file-path derivation already computed (`venue_fetch.py` + new `_tradfi_manifest_canon.py`). 12
  regression tests, quality-gates green. **CME `futures_chain`/`options_chain` confirmed NOT affected** —
  `instrument_id=null` is correct by design for bundle grain, `underlying=SP500` already correctly translated; the
  `future`/`FUTURE` split seen in an axis census is a small (2,023-row), static, non-growing legacy population,
  unrelated to the active CME backfill.
- **Fix-propagation gap found + closed**: code fix landing does NOT retroactively patch already-running VMs (tarball
  deploy model, fetched once at boot). Confirmed live (rows written after the fix landed were still legacy form).
  Refreshed the published tarball (`create-code-tarballs.sh`) and verified the new module is present
  (`_tradfi_manifest_canon` byte-grep on the downloaded tarball) — any VM launched from 2026-07-21T17:01Z onward gets
  the fix. VMs running before that point kept writing legacy rows until they finished naturally (not killed — would've
  lost in-flight capture progress).
- **FX `spot_pair` cash-id bug found, documented, NOT fixed (low priority)**: separate bug from the above — the
  2026-07-18 manifest fix stamped FX `SPOT_PAIR` rows with `instrument_id="ticks"` or blank instead of a real derived
  id. Only 3,126 total rows, 11/day currently — negligible volume, not urgent. Full detail:
  `plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`.
- **Docs-reconciliation findings applied**: 34 of the 35 tracked findings + the 4 stale-Massive-purge codex docs + the
  storage register patch, across 3 commits (`pm@935de9424`, `1dd1a22fd`, `6daaff49f`). The 3 deliberately DEFERRED
  (`tradfi_consolidated_closeout_2026_07_18.md` L97 + L460, `canonical-cutover-register.md` L237) still read their
  ORIGINAL 2026-07-18 text — do not apply their suggested fix verbatim, it overstates manifest/content completion; write
  a freshly-grounded correction instead once the migration work below is actually done.
- **Fleet fully drained** (GCP 34→0, AWS empty). The LAST VM (`tradfi-bf-cme-ohlcv-1m-pa-2021-20260721-105454`,
  palladium 2021) **hung** — confirmed via TWO independent signals (log-mtime frozen at 17:46:48Z, manifest writes
  stopped at 18:49:19Z) while `gcloud` kept reporting it RUNNING for ~5 more hours. Stopped it manually. It captured
  9,680 real rows before hanging — not wasted, but 2021 palladium coverage is incomplete.
  - `- [ ] [INFRA] P2. Relaunch CME palladium (PA) 2021 backfill to finish remaining days — AFTER the migration work below completes (relaunching now reintroduces an active writer mid-migration). Skip-if-fresh will resume from where it hung; use the now-fixed tarball (irrelevant for chains, but use it anyway).`
- **Manifest consolidator confirmed current**: last run 2026-07-21T23:36:42Z, clean no-op (0 shards changed), no lock
  present.
- **Pre-migration manifest snapshot taken**:
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/backups/availability_index.pre_content_migration_20260721T233802Z.parquet`
  (115.8 MiB, independent restore point ahead of any of the scripts below touching the manifest).
- **MVP scope gap found, NOT resolved — needs an operator decision**:
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py`'s tradfi `data_types` is
  still `frozenset({"ohlcv_1m"})` only — never extended to include `ohlcv_1s`, even though this session's whole backfill
  fleet captured both. Practical effect: a chunk of what was just backfilled likely isn't flagging `mvp=True` in the
  catalogue.
  - `[x] [DATA] P1. Operator decision — add "ohlcv_1s" to TRADFI_MVP_RULE.data_types in _mvp_scope_rules.py, or leave ohlcv_1m-only intentional? Operator answered via AskUserQuestion 2026-07-22: "Add ohlcv_1s to MVP scope." Shipped uac@68c4c371dfeab875ee8d78b1b6882d631614c570.`

### 🔴 IN FLIGHT, UNCOMMITTED ON DISK — CHECK THIS FIRST ON RESUME

Two background agents wrote real code to the **local `market-tick-data-service` checkout** that is **NOT YET COMMITTED
OR PUSHED** as of this checkpoint. This work will NOT appear in a fresh `git clone` / different slot — it only exists in
this exact tab's working tree. `cd market-tick-data-service && git status --porcelain` to check whether it's still there
(it survives context compaction fine — compaction only clears LLM conversation state, not the filesystem — but a fresh
session needs to know to look):

1. **Cash-bucket crash fix** (agent id `a37c3e3fc6f1ea5ee`, resumable via SendMessage by that id if still live) — fixing
   a REAL bug found in `scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py`: `_process_cash()`'s per-row loop has NO
   exception isolation around `canonicalize_raw_tradfi_id(...)`, so a single malformed spread symbol (reproduced:
   `VX/Q6:1:S - VX/X6:1:B` mis-typed as `INDEX`) crashes the ENTIRE dry-run/apply instead of being quarantined — **this
   is almost certainly why the 2026-07-18 run never actually finished on the full manifest population**, which is a big
   part of why so many equity/etf/index rows were still legacy despite that "fix" having supposedly run. As of this
   checkpoint, only the regression test exists on disk
   (`tests/unit/scripts/test_migrate_tradfi_manifest_usd_lin_2026_07_18.py`, untracked) — the actual fix to the source
   script has NOT been written yet (`git diff --stat scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py` was empty at
   last check). **On resume**: check if it finished (look for a `mtds@<sha>` ship + a green live dry-run stats report);
   if not, resume the agent or read `tradfi_id_canonicalizer.py::_canonicalize_cash` +
   `canonical_id_builder.py::build_instrument_id` yourself and finish the fix (wrap the per-row call in try/except,
   treat any exception as the existing quarantine/byte-identical path, mirror the sibling script's
   `migrate_tradfi_canonical_2026_07.py` per-object isolation discipline).
2. **Content-rewrite script build** (agent id `ad07a7345873f83d0`) — a NEW script,
   `market_tick_data_service/scripts/rewrite_tradfi_content_id_2026_07_21.py` (631 lines, untracked) +
   `tests/unit/scripts/test_rewrite_tradfi_content_id_2026_07_21.py` (275 lines, untracked), for the genuinely-new
   parquet-CONTENT `instrument_id` rewrite (the path migration that already ran never touched file content — see the
   root-cause section above this Progress Log entry). Built per a detailed brief reusing the 3 proven reference scripts'
   patterns (`migrate_tradfi_single_leg_product_root_lin_2026_07_09.py` for the per-object GCS
   backup→rewrite→verify→delete pattern, `migrate_tradfi_manifest_usd_lin_2026_07_18.py` for CAS manifest safety,
   `migrate_tradfi_canonical_2026_07.py` for disposition classification + UAC id derivation). Status at this checkpoint:
   NOT yet confirmed quality-gates-green, NOT yet dry-run-verified against live prod, NOT yet shipped. **HARD BOUNDARY
   that must carry forward**: this script must stay dry-run-only until a human/main-session reviews it and runs
   `--apply` deliberately — never let an agent or a fresh session run `--apply` on it unreviewed, given this exact
   repo's real prior incident (`tradfi_manifest_row_loss_regression_2026_07_12.md`, 1,017,024-row silent manifest loss
   from an unguarded read-modify-write).

**If both agents are gone/unresumable on resume**: the files are still sitting in the local working tree (verify with
`git status`) — read them, they are real, substantial attempts, not throwaway scratch. Finish reviewing + testing +
shipping them rather than starting over.

### Lessons from this stretch (carry forward)

- **A stopped background agent that says "waiting on my own quality-gates run" is not idle — resume it via `SendMessage`
  to its agent id and it continues from its own transcript.** Had to do this 4 times across 2 agents this session; each
  time it correctly picked back up rather than restarting. Don't assume a "completed" task notification with an
  inconclusive result means the work is done — read the result text.
- **`gcloud` reporting a VM as RUNNING is not proof of progress.** The last fleet VM (PA-2021) sat at `RUNNING` for ~5
  hours after its log AND its manifest writes both went silent. Two independent staleness signals (log-mtime + manifest
  row `written_at`) caught it; a naive "is it still RUNNING" check would have waited forever. This is the workspace's
  own async-wait-discipline rule proven out concretely, not just theory.
- **A shipped code fix does not mean a fixed _fleet_.** Tarball-deployed VMs fetch code once at boot; a git push doesn't
  reach already-running processes OR even new VM launches until the tarball itself is refreshed
  (`create-code-tarballs.sh`). Verify the ACTUAL tarball contents (byte-grep the downloaded artifact), don't trust the
  git SHA alone.
- **A migration script that "ran successfully" on 2026-07-18 (backup snapshots exist, no error surfaced to the operator)
  can still have silently died partway through** if it crashes on an uncaught exception rather than isolating per-row
  failures — there is no way to tell from a backup-snapshot's mere existence whether the run actually completed. This is
  why the cash-bucket crash bug sat undiscovered for 3+ days: nobody re-ran the script and watched it fail live.
  **Always re-verify a "done" migration claim by re-running its dry-run mode, don't trust a stale success report.**
- **Two independently-measured populations (`instrument_type` casing vs filename-colon presence) can look like the same
  signal but aren't.** The path-migration script's `MIGRATE_SINGLE_NOOP` heuristic (colon-in-filename ⇒ "already fine")
  and the true manifest-canonical population (UPPERCASE `instrument_type`) are correlated but not identical — don't
  conflate "the filename looks canonical" with "the row is canonical."
- **Pre-existing dangling scratchpad references found** (not from this session, not fixable now — the referenced files
  are already gone): `tradfi_consolidated_closeout_2026_07_18.md` lines ~437/456/488/800/852/928 reference
  `scope_{A,B,C,D}.md` / `measure_canonicalize.py` / `enumerate_dimensions.py` / `measure_metric.py` in "scratchpad" —
  none of these exist in the current scratchpad (confirmed missing). These are Phase-B-era pointers from earlier work
  than this visible session; the content they described is presumably still summarized in the plan prose itself, just
  not independently re-runnable anymore. Not urgent (that phase is long past), but a future full plan cleanup pass
  should strip or annotate these as gone.

### Deferred work after 2026-07-21/22 — pick up in this order

| Item                                                                                         | State / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                      | Blocked on                                                                                                      |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Cash-bucket crash fix** (manifest script)                                                  | Not done — real work, in flight                                                                                                                                                                                                                                                                                                                                                                                                                           | Agent `a37c3e3fc6f1ea5ee`, or pick up the uncommitted diff yourself                                             |
| **Content-rewrite script** (parquet content)                                                 | Not done — real work, in flight                                                                                                                                                                                                                                                                                                                                                                                                                           | Agent `ad07a7345873f83d0`, or pick up the uncommitted files yourself                                            |
| **Manifest re-run** (`migrate_tradfi_manifest_usd_lin_2026_07_18.py --apply --in-place-cas`) | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | The cash-bucket crash fix above — running it pre-fix will crash again on the first malformed spread symbol      |
| **Content-rewrite `--apply`** (sharded)                                                      | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | The script above being reviewed by a human (not just agent-shipped) — real prod parquet mutation                |
| **Rebundle** (`rebundle_tradfi_chains_2026_07.py --apply`, 112,839 rows)                     | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | Sequenced after the manifest+content migration, not before                                                      |
| **CME MBO monolith migration** (107 objects, migrate-first)                                  | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | Same — after the above; never blind-delete, content-read first                                                  |
| **Re-measure canonical %** (all 4 surfaces)                                                  | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | All migration steps above                                                                                       |
| **Deferred doc fixes** (L97/L460/cutover-register L237)                                      | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | Needs the TRUE post-migration numbers to write an accurate correction, not the migration to just be "attempted" |
| **PA-2021 relaunch** (palladium backfill)                                                    | Cannot be done yet (deliberately)                                                                                                                                                                                                                                                                                                                                                                                                                         | Wait until fleet-quiet is no longer needed for the migration work above                                         |
| **`ohlcv_1s` MVP scope decision**                                                            | Operator-owned                                                                                                                                                                                                                                                                                                                                                                                                                                            | Asked in-chat 2026-07-21, unanswered                                                                            |
| **Catalogue MVP promote** (`build_instrument_catalogue.py --asset-group tradfi`)             | **Actually UNBLOCKED now** — backfill completion (its stated gate) is met since the fleet fully drained. Not yet run only because this session ran out of turns before reaching it, not because of a real dependency. Safe to run independently of the manifest/content migration (different surface — catalogue is Surface A). **Recommended next item if you're picking this plan up fresh** — it's a clean, low-risk, high-value win with no blockers. | Nothing — just hasn't been run yet                                                                              |
| **Phase D gate** (`data-pipeline-check-is`/`-mtds`, tradfi, all shards)                      | Cannot be done yet                                                                                                                                                                                                                                                                                                                                                                                                                                        | Everything above                                                                                                |

**Recommended next action for a fresh session**: check `git status` in `market-tick-data-service` first (the two
in-flight agents' work). If it's still there uncommitted, finish reviewing/testing/shipping it — don't restart. If it's
already landed (check `git log` for `mtds@` shas matching the fix descriptions above), skip straight to running
`migrate_tradfi_manifest_usd_lin_2026_07_18.py --apply --in-place-cas` for real. Either way, the catalogue promote is
independent and can run in parallel right now with no blockers.

---
