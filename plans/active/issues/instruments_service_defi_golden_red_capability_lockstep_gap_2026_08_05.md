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
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, expected-universe, golden-drift, protocol-capabilities, lst-rates, qg-red, cross-repo, lockstep]
related:
  [
    /plans/active/issues/defi_protocol_capabilities_lst_rates_audit_2026_08_05.md,
    /plans/active/issues/defi_six_lst_vault_venues_missing_protocol_capabilities_2026_07_31.md,
    /plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md,
    /plans/archive/issues/instruments_service_qg_red_golden_drift_2026_07_10.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-08-05"
author: slot-14 (data_engineering craft)
last_updated: "2026-08-05"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: engineer
priority: P1
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-022 (slot-14)]
resolved_by:
locked_by:
locked_since:
depends_on: []
---

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
  (`/tmp/slot14_smoke_watch.sh` → SMOKE-COMPLETE / SMOKE-FAIL / SMOKE-VM-EXITED; matches the script's real completion
  line `"Done. N/M cells written (K failed). Manifest closed..."`).
- **Full `--apply` launch**: pending smoke confirmation of the dispatch path.

### 2026-08-05 (slot-14) — BLOCKED-OPERATOR-DECISION (escalated → BLK-2b07d861)

**Escalated via `/api/slots/14/blocked` (2026-08-05 ~12:45Z → `BLK-2b07d861`, "Escalated to dashboard. Main/review agent
will answer.")**. Decision required from the operator / defi-track owner before slot-14 can ship:

- **option (a) [RECOMMENDED]** — the defi track that owns the UAC `PROTOCOL_CAPABILITIES` churn regenerates the defi
  expected-universe golden in LOCKSTEP once the capability state stabilizes (07-30 deribit precedent
  `/plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`); slot-14 ships immediately
  after the tree goes green.
- **option (b)** — operator approves an immediate golden regen now (`scripts/regenerate_expected_universe_golden.py`; it
  refuses while UAC/UTL have uncommitted changes, so both trees must be clean; bakes current UAC LDR HEAD).
- **option (c)** — operator directs an alternative path.
- **`can_continue`**: NO for shipping; YES for prep (backfill script + VM launcher are validated and ready).

## Deferred work after 2026-08-05 (blocked on BLK-2b07d861)

| Item                                                                                                                   | State / why deferred                                                                                                  | Blocked-on                              |
| ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Ship `instruments-service/scripts/backfill_teams_full_history_2026_08_05.py` via quickmerge `--agent`                  | **DONE** — `instruments-service@8a6597db` (golden cleared 13:07:59Z)                                                  | —                                       |
| Launch SPOT backfill VM (`--apply`, `launch-sports-teams-full-history-backfill-vm.sh`, `instr-backfill-sports` prefix) | Launcher written + dry-run-validated; VM launch **in progress** (`--force` past the cross-slot singleton-lock holder) | launcher committed + tarballs refreshed |
| Post-backfill coverage census (expected_unattempted→0, bounded)                                                        | Not run                                                                                                               | VM `--apply` run completes              |
| Flip plan checkbox (plan line 561, Track S2) + `docs(plans):` commit SAME turn                                         | Not flipped (correctly — not done)                                                                                    | backfill + census complete              |
| POST /done `sports_consolidated_native_ao_extract-022`                                                                 | Not posted                                                                                                            | all above                               |

**Resume path (next session — this issue doc is the SSOT)**: watch for the defi golden to clear at UAC LDR HEAD
(`instruments-service` `test_expected_matches_golden[defi]` passes), then in order: quickmerge-ship the script, launch
the SPOT VM `--apply`, run the bounded post-backfill census, flip the plan checkbox same-turn, POST /done. The backfill
script survives on disk (untracked — cannot commit on a red tree) at
`instruments-service/scripts/backfill_teams_full_history_2026_08_05.py`.

**Session lessons (do not re-learn)**: (1) CI dep resolution is CONTENT-FIRST —
`python-quality-gates-v2.yml::clone_repo` clones each dep at its LDR HEAD, so local editable path-dep == CI clone ==
byte-identical → a local QG red is fleet-wide, NOT a local-ahead-of-CI artifact; (2) the availability-index manifest
read MUST be column-projected pyarrow (5 cols) — an unfiltered 9.25M-row read OOMs the 6G bounded-analysis cap (RSS
7.35GB, 2026-08-05, first dry-run attempt); (3) PM issue-doc frontmatter: a `title:` containing `: ` must be a folded
`> -` scalar or plan-hygiene fails with "mapping values are not allowed here" (82 corpus usages).
