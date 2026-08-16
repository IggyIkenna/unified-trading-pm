---
doc_type: issue
title: >-
  instruments-service defi expected-universe GOLDEN red at UAC LDR HEAD — PROTOCOL_CAPABILITIES churn has no lockstep
  golden regen owner (2026-08-05: golden=320 vs actual=376, 58 to add, 2 to remove)
summary: >-
  instruments-service QG fails `test_expected_matches_golden[defi]` FLEET-WIDE (local AND CI). CI's dep resolution is
  CONTENT-FIRST: `python-quality-gates-v2.yml` clones each dep at its `live-defi-rollout` HEAD ("the SSOT content local
  QG resolves against"), falling back to the version-aware tag only if the LDR clone fails — so local editable path-dep
  and CI clone are byte-identical, and the golden test is red for EVERYONE resolving UAC at LDR HEAD. Root cause: UAC's
  `PROTOCOL_CAPABILITIES` is mid-audit churn (12 commits 2026-08-05 11:07Z→12:29Z, adding lst_rates/oracle_prices/
  staking_yields declarations + removing LIDO/ETHERFI "rewards"), while the defi expected-universe golden was last
  regenerated 2026-07-21 (`instruments-service@1cb3624d`). Fresh bounded diff 2026-08-05 ~12:45Z: golden=320 actual=376
  extra=58 missing=2, and the gap is still growing (13 extra at ~12:10Z). Nobody owns the lockstep golden regen:
  slot-7's same-day audit `defi_protocol_capabilities_lst_rates_audit_2026_08_05.md` covers the capability declarations
  but not the golden fixture. Regenerating now is WRONG (the golden docstring forbids blind regen — 07-10 incident — and
  UAC is still churning, so a regen would be stale again within hours). This blocks ALL instruments-service shipping
  (quickmerge re-gates on a red tree), including slot-14's sports TEAMS full-history backfill (task
  `sports_consolidated_native_ao_extract-022`).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, expected-universe, golden-drift, protocol-capabilities, lst-rates, qg-red, cross-repo, lockstep]
related:
  [
    /plans/archive/issues/defi_protocol_capabilities_lst_rates_audit_2026_08_05.md,
    /plans/archive/issues/defi_six_lst_vault_venues_missing_protocol_capabilities_2026_07_31.md,
    /plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md,
    /plans/archive/issues/instruments_service_qg_red_golden_drift_2026_07_10.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-08-05"
author: slot-14 (data_engineering craft)
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: engineer
priority: P1
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-022 (slot-14)]
resolved_by: slot-17, 2026-08-16
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/archive/issues/defi_protocol_capabilities_lst_rates_audit_2026_08_05.md,
    /plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md,
    /plans/archive/issues/instruments_service_qg_red_golden_drift_2026_07_10.md,
    instruments-service/scripts/regenerate_expected_universe_golden.py,
    instruments-service/scripts/backfill_teams_full_history_2026_08_05.py,
  ]
---

> **🗄️ ARCHIVED 2026-08-16 (slot 17).** Every checkbox closed, 0 open. Core issue (defi golden red blocking fleet-wide
> instruments-service shipping) resolved same-day via the lockstep regen (`instruments-service@0975de10`, golden
> cleared 13:07:59Z); the blocked sports TEAMS backfill (`sports_consolidated_native_ao_extract-022`) shipped
> (`d6fa4db9e`) and its own `/done` POST — the doc's last remaining prose-tracked follow-up — was independently
> confirmed already landed (`done_at=2026-08-05T15:17:01Z`, verified live via `GET /api/backlog`). The
> CI-content-first-dep-resolution lesson this doc surfaced is already codified at `/codex/08-workflows/ci-cd-flow.md`.
> The SAME golden-red failure class recurred 2026-08-14 — see `/plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md`
> (open) for the current live incident of this pattern.

## Problem

instruments-service `quality-gates.sh` is red on `test_expected_matches_golden[defi]`, and this is a FLEET-WIDE red —
**not** a local-ahead-of-CI artifact. CI's dep clone is content-first (`python-quality-gates-v2.yml::clone_repo`,
operator decision 2026-06-11): it clones each dep at its `live-defi-rollout` HEAD (the content local editable siblings
resolve against), only falling back to the version-aware tag/branch chain if the LDR clone fails. Local editable
path-dep and CI clone are therefore byte-identical → identical `build_expected("defi")` → identical golden failure.

## Evidence (2026-08-05)

- **Golden last regenerated**: `instruments-service@1cb3624d`, 2026-07-21 18:13Z
  (`fix(cefi): regenerate stale expected-universe golden`).
- **UAC `PROTOCOL_CAPABILITIES` churn since then** (UAC live-defi-rollout HEAD now `6e791b05`, 2026-08-05 12:29Z): 12
  commits today (11:07Z→12:29Z), incl. `394fdbf0` BEEFY lst_rates, `e1639234` IDLE lst_rates, `96070f2b` PENDLE
  lst_rates, `e4e4e5a9` YEARN_V3 lst_rates, `8feaea84` BINANCE/COINBASE/ROCKETPOOL/SANCTUM/SOLBLAZE entries, `b2874193`
  "add 10 undeclared DeFi data_types", `bc397b93` "remove aspirational rewards from LIDO/ETHERFI" — plus 07-22→08-02
  commits (RENZO/KELPDAO/ankr/stader/… lst_rates).
- **Fresh bounded diff vs golden** (`run-bounded-analysis.sh`, 2026-08-05 ~12:45Z):
  `golden=320 actual=376 extra=58 missing=2`.
  - extra classes: `lst_rates` for BEEFY/BINANCE/COINBASE/IDLE/PENDLE/ROCKETPOOL/SANCTUM/SOLBLAZE/YEARN_V3/etc.;
    `oracle_prices` for MORPHO/SPARK/RADIANT/KAMINO; `staking_yields` for ROCKETPOOL.
  - missing: `LIDO-ETHEREUM (yield_bearing, rewards)` + `ETHERFI-ETHEREUM (yield_bearing, rewards)` — matches UAC
    `bc397b93` rewards-removal at 12:21Z.
- **The mismatch is STILL GROWING** (13 extra at ~12:10Z → 58 extra at ~12:45Z) → UAC is mid-flight, not settled.

## Why this is not fixable by a unilateral golden regen

- The defi golden's own docstring + the 07-10 incident
  (`plans/archive/issues/instruments_service_qg_red_golden_drift_2026_07_10.md`) forbid regenerating the fixture while
  UAC/UTL capability content is in flux — a regen silently bakes whatever UAC state is live into the checked-in golden.
- UAC is STILL CHURNING right now; a regen would be stale again within hours (13→58 extra in ~35 min).
- The capability declarations are the subject of slot-7's open audit
  `defi_protocol_capabilities_lst_rates_audit_2026_08_05.md` — until that audit's verdict is locked (are the additions
  correct? is the LIDO/ETHERFI rewards-removal right?), the golden must not be re-baked.
- The `rewards` removal is itself an audit-driven change mid-review.

## Why it blocks the fleet

Any instruments-service QG — local or CI — resolves UAC at LDR HEAD → `build_expected("defi")` reads the new
capabilities → 376 vs 320 golden → RED. quickmerge re-gates on a red tree → **no instruments-service code ships**. This
blocked slot-14's sports TEAMS full-history backfill (task `sports_consolidated_native_ao_extract-022`) at the ship
step: the backfill script is written + dry-run-validated (67,782 `expected_unattempted` cells across 322 api_football
leagues, census-exact, 0 pre-2022-floor cells) but cannot be committed via quickmerge while the tree is red.

## Resolution (AO-scope — regenerate the golden in LOCKSTEP with the capability work)

The defi track that owns the UAC `PROTOCOL_CAPABILITIES` churn (slot-7's audit
`defi_protocol_capabilities_lst_rates_audit_2026_08_05.md` + the six-LST-venues issue) must, once the capability state
stabilizes (no further LDR commits expected / audit verdict locked):

1. run `instruments-service/scripts/regenerate_expected_universe_golden.py` — it REFUSES while UAC/UTL have uncommitted
   changes, so keep both trees clean,
2. commit the golden regen together with the capability commits (lockstep — the 07-30 deribit precedent
   `instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md` resolved its UAC↔golden drift exactly this way:
   fix the UAC side + regen the golden in the same effort),
3. confirm `instruments-service` `quality-gates.sh` green (5200+ tests).

**done-when**: `test_expected_matches_golden[defi]` passes at UAC LDR HEAD; `instruments-service` QG green.

## Progress Log

### 2026-08-05 (slot-14) — sports TEAMS backfill blocked at ship step by this golden drift

- **Prerequisite live-probe CONFIRMED** for task `sports_consolidated_native_ao_extract-022`: the consolidator
  NULL/empty-string dedup-key fix shipped (`unified-trading-library@11009da7`, verified ancestor-or-equal of
  origin/live-defi-rollout). The task's STOP condition was NOT triggered.
- **Backfill script written + validated** (`instruments-service/scripts/backfill_teams_full_history_2026_08_05.py`, 301
  lines, untracked): `--dry-run` reproduces the coverage census exactly — 322/384 expected api_football leagues have
  67,782 `expected_unattempted` cells (2021-09-18..2026-07-23, 0 pre-floor cells). Write-path verified: TEAMS rows are
  uniformly `venue=""` → `record_captured` without an explicit venue produces matching rows (no dedup-twin risk).
- **OOM event (shared-host; operator directive)**: the FIRST dry-run attempt was OOM-killed by `run-bounded-analysis.sh`
  at RSS 7.35GB > 6G cap — `_read_canonical_manifest()` read the full 9.25M-row consolidated index unfiltered. FIXED by
  column-projected pyarrow read (5 cols only); re-run exit 0. Recorded here per the operator's shared-host directive;
  the plan file is at its 1000-line hard cap so this session record lives in this issue doc.
- **QG status**: `quality-gates.sh --no-fix` → 5200 passed / 1 failed (`test_expected_matches_golden[defi]`) / 6 skipped
  / coverage 88.78%. The sole failure is this pre-existing cross-repo drift, NOT caused by the backfill script (no test
  references it).
- **Blocked at ship step**: quickmerge `--agent` (no QG sentinel in instruments-service) would force a full Pass-2 QG →
  red → exit 1.

### 2026-08-05 (slot-14) — resume: golden cleared; script shipped; VM launch in flight

- **BLK-2b07d861 RESOLVED (externally)**: defi golden cleared at 13:07:59Z (`extra=0 missing=0`) via the lockstep regen
  (`instruments-service@0975de10` `test(instruments-service): regenerate expected-universe golden fixtures`). QG green:
  5201 passed / 6 skipped.
- **Backfill script SHIPPED**: `instruments-service/scripts/backfill_teams_full_history_2026_08_05.py` via quickmerge
  `--agent` → `instruments-service@8a6597db`, origin-verified.
- **Launcher written** (`deployment-service/scripts/vm/launch-sports-teams-full-history-backfill-vm.sh`, untracked):
  SPOT-by-default, singleton lock on `af-backfill-`/`fill-missing-player-stats-`/`instr-backfill-sports-teams-`,
  `VM_TASK=sports-gap-fill` dispatch, `MANIFEST_PER_VM_SHARDS`, preemption-signal + launch-params, tarball-freshness
  gate.
- **CROSS-SLOT FINDING — existing VM `instr-backfill-sports-teams-20260805-055622` is another slot's stalled run**:
  launched 05:56Z via `launch-sports-is-gap-fill.sh` (sports_af_full_entity_completion campaign,
  `VM_TASK=instruments-backfill` CLI orchestrator, `VM_SPORTS_ENTITY=TEAMS`), SPOT, RUNNING, but **stalled since
  12:02Z** (log mtime updates = 403 GcsEventSink retry loop only) and **structurally incapable of Track S2**: reads
  teams from cache ("0 API calls"), queues 0 enrichment calls, presence-guard refuses to stamp ("NOT stamping
  empty_confirmed over present data"), writes **0 TEAMS cells** (only `entity=fixtures` per-VM shard rows). Per
  multi-agent safety it is NOT mine to delete. It is also **not competing for the api_football key** (0 calls queued) —
  so launching my backfill with `--force` past my own singleton lock is safe: my run makes only 322 paced `/teams` calls
  total (1.2s delay), a negligible slice. The `--force` bypasses only my conservative self-lock; it does not touch the
  other VM.

### 2026-08-05 (slot-14) — smoke-test VM launched; full `--apply` pending smoke confirmation

- **Smoke-test VM launched 13:30:11Z**: `instr-backfill-sports-teams-20260805-133011` (SPOT, e2-standard-4,
  asia-northeast1-c, RUNNING) via `launch-sports-teams-full-history-backfill-vm.sh --force --limit-leagues 1` —
  validates the novel `VM_TASK=sports-gap-fill` dispatch path (`setup-data-pipeline-vm.sh:1381` rewrites `python` →
  `$VENV/bin/python`), the Secret Manager api_football key, and the GCS+manifest write path on ONE league before
  committing the full 322-league / 67,782-cell run. `--force` past the singleton lock is safe: the existing cross-slot
  VM (`instr-backfill-sports-teams-20260805-055622`) makes 0 api_football calls. Watcher armed
  (`/tmp/slot14_smoke_watch.sh` — a session-scoped /tmp harness, consumed; → SMOKE-COMPLETE / SMOKE-FAIL /
  SMOKE-VM-EXITED; matches the script's real completion line
  `"Done. N/M cells written (K failed). Manifest closed..."`).
- **Full `--apply` launch**: pending smoke confirmation of the dispatch path.

### 2026-08-05 (slot-14) — smoke PASSED; full `--apply` VM launched

- **Smoke test PASSED (13:33:30Z)**: `instr-backfill-sports-teams-20260805-133011` logged
  `Done. 232/232 cells written (0 failed). Manifest closed (per-VM shard drained).` then **self-deleted**
  (`VM_SHUTDOWN_ON_COMPLETION` path verified — the instance is gone from the fleet list). This proves the novel
  `VM_TASK=sports-gap-fill` dispatch, the `python`→`$VENV/bin/python` rewrite, the Secret Manager api_football key, and
  the GCS+manifest write path all work end-to-end on real prod infra.
- **Full backfill VM launched 13:36:52Z**: `instr-backfill-sports-teams-20260805-133652` (SPOT, e2-standard-4, RUNNING)
  via `launch-sports-teams-full-history-backfill-vm.sh --force` →
  `python scripts/backfill_teams_full_history_2026_08_05.py --apply --concurrency 32` (322 leagues / 67,782 cells). All
  4 tarballs verified fresh at launch (instruments-service@8a6597db, UAC@6e791b05, UTL@0b957b4a,
  deployment-service@e1e475d). `--force` past the singleton lock: safe (cross-slot stalled VM makes 0 api_football
  calls). Watcher armed (`/tmp/slot14_full_backfill_watch.sh` — session-scoped /tmp harness; → FULL-COMPLETE /
  FULL-ABORT / FULL-VM-EXITED / FULL-TIMEOUT; re-arm per the Resume-path note below). Estimated 40-80 min to completion.
- **T+10min verify (mandatory)**: confirm the full VM is still RUNNING and the run.log is progressing.

### 2026-08-05 (slot-14) — BLOCKED-OPERATOR-DECISION (escalated → BLK-2b07d861) — **RESOLVED 13:43Z**

**Escalated via `/api/slots/14/blocked` (2026-08-05 ~12:45Z → `BLK-2b07d861`, "Escalated to dashboard. Main/review agent
will answer.")**. Decision required from the operator / defi-track owner before slot-14 can ship.

**RESOLUTION**: the defi track executed option (a) — the golden was regenerated in LOCKSTEP with the capability work
(`instruments-service@0975de10`, golden cleared 13:07:59Z, `extra=0 missing=0`); slot-14's /heartbeat flipped from
`blocked` → `working`, confirming the ticket closed. No remaining operator decision pending; slot-14 resumed and
shipped.

- **option (a) [RECOMMENDED]** — the defi track that owns the UAC `PROTOCOL_CAPABILITIES` churn regenerates the defi
  expected-universe golden in LOCKSTEP once the capability state stabilizes (07-30 deribit precedent
  `/plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`); slot-14 ships immediately
  after the tree goes green.
- **option (b)** — operator approves an immediate golden regen now (`scripts/regenerate_expected_universe_golden.py`; it
  refuses while UAC/UTL have uncommitted changes, so both trees must be clean; bakes current UAC LDR HEAD).
- **option (c)** — operator directs an alternative path.
- **`can_continue`**: NO for shipping; YES for prep (backfill script + VM launcher are validated and ready).

### 2026-08-05 (slot-14) — census DONE; residual fully explained; Track S2 flip ready

- **Consolidated index fresh 14:10:06Z** (watcher bwzyzdf27): `consolidator_run_at=2026-08-05T14:10:06`,
  `consolidator_content_write_at=2026-08-05T14:00:42` ≥ backfill shard (13:54:18Z). Execution `w8szq` (lock 14:00:42)
  included the 44,296 backfill cells — the per-minute cron self-healed exactly as the churn note below predicted.
- **Fresh bounded TEAMS census** (`teams_coverage_census_2026_08_05.py` under `run-bounded-analysis.sh --mem-cap 6G`, on
  the post-consolidation index): TEAMS rows=678,275;
  `captured=582,088 empty_confirmed=74,252 expected_unattempted=21,918 attempted_failed=17`; **0 surviving dedup twins**
  (dedup-key fix verified in the consolidated output); NULL league_id=3,134 / ''=0 (pre-existing representation);
  captured span 2018-01-01→2026-08-12.
- **Residual 21,918 is FULLY EXPLAINED — source-empty, NOT a defect**: the backfill's own launch gap-analysis was 322
  leagues / **66,487** cells; 44,296 written; **104 leagues' `/teams` calls returned 0 teams** (VM run.log:
  `0 teams returned — no roster to backfill with`; 0 fetch failures) → excluded from writes. Post-consolidation residual
  league set (98) ⊂ 0-team set (104): **0 residual cells exist for any roster-having league**. 6 of the 104 (~273 cells:
  COPA_LIGA_PROFESIONAL / COPA_MX / EMPEROR_CUP / FA_CUP / GREEK_SUPER_LEAGUE_2 / SUPERCOPPA_ITALIANA) were cleared by
  concurrent writers. A roster-stamp backfill cannot fabricate teams for these 98 leagues (off-season cups / defunct /
  no registered teams) — structurally unbackfillable. Follow-up tracked below.
- **Probe OOM lesson**: the first residual probe OOM'd at RSS 6.82GB (>6G cap) materialising the full 9.25M-row index to
  pandas; the arrow-native rewrite (filter-in-pyarrow → only ~22k rows reach pandas) runs well under the cap. Never
  materialise the full index to pandas in-session.

**Follow-up (tracked — findings-triage, not prose):**

- [x] ✅ [DATA] P3. **TEAMS 98-league residual (21,918 cells) — resolved: leave `expected_unattempted`** — option (a)
      per the decision tree below. The cells are correctly classified: api_football returns 0 teams for these 98 leagues
      (off-season cups / defunct / no registered teams — structurally unbackfillable without fabricating data). Option
      (b) `empty_confirmed` is technically blocked (presence-guard refuses over historical cells). Option (c) per-season
      API variant is deferred — investigate if the sports track needs it. Rationale + close-out in the Progress Log
      below. SSOT: this issue doc.

### 2026-08-05 (slot-14) — RESOLVED: Track S2 SHIP cleared via the sanctioned docs(plans) carve-out (was: BLOCKED-OPERATOR on fleet-wide PM QG red — 3 pre-existing foreign checks)

- **The flip + evidence commit is ready on-disk but CANNOT ship.** PM quickmerge's post-gate re-gate fails AND PM
  `quality-gates.sh` is itself RED on 3 checks — all 3 are PRE-EXISTING and FOREIGN: committed on
  `origin/live-defi-rollout`, introduced by today's commits from other agents (I pulled 8 such commits 14:20Z;
  `git rev-list --count origin/live-defi-rollout..HEAD` = 0). Verified NONE touch this issue doc or
  `sports_consolidated_native_ao_extract_2026_07_25.md` — grep of the full failure lists shows 0 hits for my 2 files,
  and my `UTL@11009da7` citation resolves.
- **The 3 failing checks** (all wired into PM `quality-gates.sh` → PM QG globally red → blocks EVERY PM ship, not just
  this task):
  1. **finalize-plan-coverage** (1 > baseline 0):
     `plans/archive/2026_08/resolve_mtds_ts_event_timestamp_naming_collision_2026_08_05.md` — a NEW AO plan (committed
     today `3b0d18bd9`) shipped without a gated finalize plan. Owner: MTDS track (author its finalize phase). NOT a
     re-baseline case — that would permanently mask a real mid-flight process violation.
  2. **plan-commit-sha-evidence** (28 > baseline 26, +2 from today's new plans): 28 unresolved citations across ~12+
     other plans. Owner: per-plan owners / gate-maintainer. NOT re-baselined unilaterally (would mask potentially-real
     citation issues).
  3. **agent-rules-size-cap** (HARD cap, 48 B over): `cursor-configs/CLAUDE.md` = 41,008 B > 40,960 B, from today's
     `docs(agent-rules)`/`docs(codex)` edits. Owner: workspace maintainers (condense per the file's own rule). I did NOT
     edit the shared config — another session is actively editing it.
- **Workarounds still forbidden**: re-baselining the ratchets or condensing the shared `cursor-configs/CLAUDE.md` would
  mask/alter FOREIGN violations — not mine to do, and the owners are actively working (MTDS plan + CLAUDE.md both
  touched today). **Direct-pushing a PURE `docs(plans):` flip is DIFFERENT — it is the SANCTIONED carve-out for exactly
  this case, not a dodge**: the pre-push hook (`scripts/hooks/pre-push`) states "any commit touching NO source
  (docs/plans/codex/scripts/.github, _.md/_.yaml/… via CARVE_PREFIX/CARVE_EXT) … A docs or plan push is therefore
  unaffected in every repo"; `check_strict_quickmerge.py`'s closed carve-out set includes `plans/**`/`*.md`;
  unified-trading-pm is EXEMPT from the strict-quickmerge guard (operator ruling 2026-07-17); and CLAUDE.md's
  QG-batching rule routes "pure doc/plan-flip → prek only". The flip changes 0 source files, adds 0 new violations, and
  leaves all 3 foreign reds fully visible to their owners.
- **Status**: `can_continue` NO for shipping until the tree clears. The flip is safe on-disk (plan line 561 `- [x] ✅`,
  line 567 evidence, line-neutral @ 1000). A bounded watchdog (Monitor, 60 min) polls the 3 checks and fires when the
  tree is green → then: quickmerge issue doc + flip together, verify `origin/live-defi-rollout..HEAD` = 0, POST /done
  `sports_consolidated_native_ao_extract-022`.
- **Task WORK is DONE + verified independent of the ship block**: prerequisite shipped (`UTL@11009da7`), backfill
  44,296/44,296 cells (0 failed, SPOT VM self-deleted), fresh bounded census cited in the entry above.

### 2026-08-05 (slot-14) — SHIPPED (corrected re-land): Track S2 flip + evidence on origin/live-defi-rollout (d6fa4db9e)

- **The ship block was cleared via the documented carve-out** (re-analysis in the section above), **but the FIRST ship
  attempt produced a CORRUPTED local commit — never pushed.** The commit-time `prettier-autostage` hook inflated the
  plan to 1003 lines (> the 1000 hard cap): the `plan-hygiene` pre-commit gate runs BEFORE prettier and validated the
  pre-prettier ~999-line staged file, then prettier re-staged a 1003-line file, so the corruption slipped past the gate.
  Repair: `git reset --soft` to origin (safe — the corrupted commit was local-only, ahead=1, never on a shared branch),
  re-applied ONLY the intended edits, pre-ran `prettier@3.9.5` + the scoped `check_line_caps.sh` so commit-time hooks
  saw a canonical ≤1000-line file, re-committed, pushed.
- **Shipped (final)**: `plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` — Track S2 todo flipped to
  `- [x] ✅` (line 559) with the evidence line (line 565:
  `UTL@11009da7; 44,296/44,296 cells (0 failed); residual in this issue doc`), plus a stale-header correction
  (parent-plan over-cap claim, now 995L) — committed `d6fa4db9e` `docs(plans):`, direct push to
  `origin/live-defi-rollout` (carve-out), `git rev-list --count origin/live-defi-rollout..HEAD` = 0 verified after push
  (ahead=0, behind=0).
- **The 3 foreign PM QG reds re-verified still red after the re-pull** (finalize-plan-coverage /
  plan-commit-sha-evidence / agent-rules-size-cap) — quickmerge stays unusable, so the carve-out was the correct path.
  This flip adds 0 new violations and hides none.
- **Watchdog stopped** (Monitor bjp1tzgee via TaskStop — it polled the 3 reds for a green tree to quickmerge; the
  carve-out made that wait moot). POST /done `sports_consolidated_native_ao_extract-022` is the final step.

### 2026-08-05 (slot-14) — P3 follow-up RESOLVED: 21,918 residual stays `expected_unattempted`

- **Decision: option (a) — leave `expected_unattempted`.** The 21,918 cells across 98 leagues are correctly classified.
  Evidence chain: (1) api_football `/teams` returns 0 teams for all 98 leagues (VM run.log:
  `0 teams returned — no roster to backfill with`, 0 fetch failures); (2) residual set ⊂ 0-team set — no residual cell
  exists for any roster-having league; (3) these are off-season cups / defunct leagues / leagues with no registered
  teams — structurally unbackfillable without fabricating data, which is exactly what `expected_unattempted` models.
- **Option (b) `empty_confirmed` is technically blocked**: the daily orchestrator's presence-guard refuses
  `empty_confirmed` over present data for historical cells — this is by design (honest-absence must be source-verified
  at write time, not retroactively reclassified).
- **Option (c) per-season API variant**: deferred — no evidence `api_football` supports `season=` on the `/teams`
  endpoint. If the sports reference-data track wants to pursue this, file a separate issue.
- **No code changes required.** Checkbox flipped; this task is complete.

## Deferred work after 2026-08-05 (blocked on BLK-2b07d861)

| Item                                                                                                                   | State / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                          | Blocked-on |
| ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Ship `instruments-service/scripts/backfill_teams_full_history_2026_08_05.py` via quickmerge `--agent`                  | **DONE** — `instruments-service@8a6597db` (golden cleared 13:07:59Z)                                                                                                                                                                                                                                                                                                                                                                          | —          |
| Launch SPOT backfill VM (`--apply`, `launch-sports-teams-full-history-backfill-vm.sh`, `instr-backfill-sports` prefix) | **DONE** — full VM `instr-backfill-sports-teams-20260805-133652` (SPOT, launched 13:36:52Z) logged `Done. 44296/44296 cells written (0 failed). Manifest closed (per-VM shard drained).` at 13:54:19Z, rc=0, `DEPLOYMENT_COMPLETED exit_code=0`, then **self-deleted** (STOPPING→gone). Per-VM shard `_index/per_vm/instr-backfill-sports-teams-20260805-133652.parquet` (1.57 MB) written 13:54:18Z. Smoke VM (133011) pre-verified 232/232. | —          |
| Post-backfill coverage census (expected_unattempted→0, bounded)                                                        | **DONE** — 678,275 TEAMS rows: captured=582,088, empty_confirmed=74,252, expected_unattempted=21,918, attempted_failed=17; 0 dedup twins; residual 21,918 FULLY explained (98 source-empty leagues — api_football 0-team, residual⊂0-team set, 0 fetch failures); empty_confirmed re-classification tracked as follow-up todo above                                                                                                           | —          |
| Flip plan checkbox (Track S2) + `docs(plans):` commit SAME turn                                                        | **DONE** — flip (`- [x] ✅`, line 559) + evidence (line 565: UTL@11009da7; 44,296/44,296 cells) + stale-header correction, committed `d6fa4db9e` `docs(plans):`, direct-pushed via the SANCTIONED carve-out (PM exempt from strict-quickmerge + no-source commit = documented carve-out); `git rev-list --count origin/live-defi-rollout..HEAD` = 0 verified after push.                                                                      | —          |
| POST /done `sports_consolidated_native_ao_extract-022`                                                                 | **DONE** — verified 2026-08-16 (slot 17) via `GET /api/backlog`: `status="done"`, `done_sha="d6fa4db9e8edfdad15cd76e4956036cbc298d20e"`, `done_at="2026-08-05T15:17:01.011551Z"`, `dispatched_to=14`. The table's "PENDING" note was stale — the /done POST had already landed same-day, just never reflected here.                                                                                                                          | —          |

**Resume path (next session — this issue doc is the SSOT)**: the defi golden cleared 13:07:59Z, the backfill script
shipped (`instruments-service@8a6597db`), the full backfill VM **COMPLETED**
(`Done. 44296/44296 cells written (0 failed). Manifest closed (per-VM shard drained).` at 13:54:19Z, rc=0, VM
self-deleted), the post-consolidation bounded census is DONE (section above), and the Track S2 flip + evidence are
SHIPPED (`d6fa4db9e`, carve-out push, ahead=0 verified). **Nothing pending for this task except the /done POST** (see
the deferred table) — plus the P3 follow-up todo above (`empty_confirmed` re-classification) is owned by the sports
reference-data track, NOT this task.

**Consolidator churn observed 14:00-14:04Z (do not re-diagnose)**: the backfill shard landed 13:54:18Z while execution
`m522p` (a 6-9 min backlog merge, lock held 13:50:48→14:00:42) was mid-merge with a 13:40:40 content cutoff — so its
13:50:34 index EXCLUDES the backfill. Every per-minute tick since (`dv8qr` 14:01, `mkhcc` 14:02, `j5llr` 14:03) skipped
with `error=locked` (sibling fresh-lock). The lock churn is NORMAL (lock TTL for instruments-sports = 2400s). Execution
`w8szq` acquired the lock 14:00:42Z and listed shards AT 14:00:42 — AFTER the backfill shard landed — so its merge WILL
include the 44,296 cells; it writes the fresh index on completion (expected ~14:06-14:09Z, per the 6-9 min pattern;
possibly longer if it inherits the backlog). No action needed — the per-minute cron self-heals once w8szq releases.

**Re-arm the index-freshness watcher (if the /tmp harness is gone)**: terminal =
`gsutil stat gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` showing
`consolidator_content_write_at:` ≥ `2026-08-05T13:54:19Z` (the backfill completion). Poll every ~30s up to ~30 min; ALSO
verify `consolidator_run_at:` is newer than `13:50:34Z` (the pre-backfill index). When fresh, run the census command
above. (This replaces the OLD VM-completion watcher — the VM is done and self-deleted; do NOT re-launch it.) The census
script survives at `instruments-service/scripts/teams_coverage_census_2026_08_05.py`.

**Session lessons (do not re-learn)**: (1) CI dep resolution is CONTENT-FIRST —
`python-quality-gates-v2.yml::clone_repo` clones each dep at its LDR HEAD, so local editable path-dep == CI clone ==
byte-identical → a local QG red is fleet-wide, NOT a local-ahead-of-CI artifact; (2) the availability-index manifest
read MUST be column-projected pyarrow (5 cols) — an unfiltered 9.25M-row read OOMs the 6G bounded-analysis cap (RSS
7.35GB, 2026-08-05, first dry-run attempt); (3) PM issue-doc frontmatter: a `title:` containing `: ` must be a folded
`> -` scalar or plan-hygiene fails with "mapping values are not allowed here" (82 corpus usages).

- **context-scout 2026-08-06**: populated context_scope (5 entries). No dedicated `## Progress Log` section exists in
  this doc (dated `###` sections instead); appended here as the last line per the fallback convention.

## Follow-ups

- [x] ✅ [OPS] P3. **RESOLVED 2026-08-16 (slot 17) — already done, doc was stale.** `GET /api/backlog` confirms
      `sports_consolidated_native_ao_extract-022` was `status="done"` (`done_sha=d6fa4db9e8edfdad15cd76e4956036cbc298d20e`,
      `done_at=2026-08-05T15:17:01.011551Z`) — the /done POST this todo was tracking had already landed same-day as the
      ship; only the Deferred-work table's "PENDING" note had gone stale. No further action needed; this was a
      doc-correction, not an outstanding POST.

> **2026-08-06 archive-candidate audit**: Core issue (defi golden red) is genuinely resolved (golden cleared 13:07:59Z
> via lockstep regen instruments-service@0975de10; backfill shipped and completed 44296/44296; census done; flip shipped
> d6fa4db9e). But the doc's own Deferred-work table carries an explicitly PENDING prose item (POST /done
> sports_consolidated_native_ao_extract-022) that was never converted to a tracked todo — a deferred follow-up in prose
> blocks archival.
>
> **2026-08-16 (slot 17) — that PENDING claim is now confirmed stale, not real; see the Follow-ups checkbox above.**
> Every todo in this doc is now closed and unlocked — archival-eligible per CLAUDE.md's "plan with every todo done +
> unlocked MUST be archived immediately" rule.
