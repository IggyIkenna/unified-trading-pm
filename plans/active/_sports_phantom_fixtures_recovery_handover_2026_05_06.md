# Handover Prompt — Execute Sports Phantom FIXTURES Recovery (2026-05-06)

Copy the block below into a fresh Claude Code session at the workspace root
(`/Users/ikennaigboaka/Code/unified-trading-system-repos`). It self-contains all context — the next agent doesn't need
to re-discover anything.

---

## START PROMPT

You are continuing work from a prior session. The plan is at:

```
unified-trading-pm/plans/active/sports_phantom_fixtures_recovery_2026_05_06.plan.md
```

Read it once before doing anything. It's locked to `live-defi-rollout` and has 7 todos in a phased DAG plus 3 parallel
cleanup tasks.

### What's already shipped (don't redo)

All on `origin/live-defi-rollout`:

| Repo                  | Commit    | What                                                                                                                                                                                             |
| --------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| instruments-service   | `f36651c` | Five `manifest.add(row_count=0)` → `record_empty(row_key)` sites in `orchestrator.py` (SPORTS zero-fixture + TradFi non-trading-day). Empty placeholder parquet writes dropped. 3 tests updated. |
| instruments-service   | `1703a09` | New script `scripts/fill_missing_player_stats.py` — targeted PLAYER_STATS gap-fill mirroring `/tmp/fill_missing_ohlcv.py`.                                                                       |
| unified-api-contracts | `9599e8f` | Dropped `SCOTTISH_LEAGUE_CUP_185` duplicate registry entry + RUF003 stray `×` in `tradfi_symbology.py:553`.                                                                                      |
| deployment-service    | `bd5e373` | `launch-fill-missing-player-stats-vm.sh` + `sports-gap-fill` dispatch in `setup-data-pipeline-vm.sh` + `fill-missing-player-stats-` watchdog prefix.                                             |
| deployment-service    | `c2ddda9` | Catch-all watchdog: every running VM watched (no more invisible-prefix footgun), daemons opt-out via `tier=daemon` / `purpose=vm-zombie-watchdog` labels.                                        |

### Live VMs at handover

```bash
gcloud compute instances list --zones=asia-northeast1-c --filter="status=RUNNING" --format="value(name)"
```

Should show (relevant ones — others may be running too):

- `fill-missing-player-stats-20260506-082808` — running, processing missing PLAYER_STATS shards. Rate-limit-bound by
  api_football. Auto-shuts on completion.
- `fs-backfill-20260506-083546` — running, full footystats sweep with new MATCHES adapter. Auto-shuts on completion.
- `vm-zombie-watchdog-20260506-094758` — daemon, running with new catch-all logic. Should NOT be killed (opted out via
  `purpose=vm-zombie-watchdog`).
- `manifest-consolidator-20260504-144754` — daemon, opted out via `tier=daemon`.

### The bug, summarised

While auditing why 38 sports leagues showed 0% PLAYER_STATS coverage, we discovered the FIXTURES adapter was emitting
`manifest.add(row_count=0)` for every Prediction-tier league on every date the orchestrator ran. This created phantom
`captured` rows with no parquet on disk, violating CLAUDE.md "4 pillars" rule #1 (`row_count > 0` OR `record_empty`,
NEVER `captured` with 0 rows).

**Concrete evidence**: AUSTRIAN_BUNDESLIGA had 3041 `captured` FIXTURES rows in the manifest, ALL with
`instrument_count=0` and **zero per-league fixtures parquet on disk**. Live api_football probe
(`/fixtures?league=218&season=2024` → 195 fixtures; `/fixtures/players?fixture=1218574` → 2 teams × 20 players) proved
data exists upstream — the writer was masking absence as captured.

The fix is shipped. **What remains is the manifest cleanup + re-run.**

### The two league categories

After running the recovery, expect this split:

- **Category A — recoverable** (~17 leagues including AUSTRIAN_BUNDESLIGA, GREEK_SUPER_LEAGUE, top-tier Prediction
  leagues): api_football has the data; the writer-fix + re-run will populate them.
- **Category B — tier limitation** (~21 leagues including POLAND_I_LIGA, J2_LEAGUE, EMPEROR_CUP, all national cups):
  api_football's Pro tier genuinely returns empty `/fixtures/players` for these. **Not a bug — they stay 0%
  PLAYER_STATS.** Confirmed via live probe of POLAND_I_LIGA fixture 1037780 → 0 teams. Worth excluding `api_football`
  from these leagues' `data_sources` in UAC eventually (P3 cleanup todo) so the orchestrator stops trying every run.

### Your job

Execute the plan's 7 todos in order. The 3 P0 + 1 P1 todos are sequential
(`refresh-tarballs → drop-phantom-fixtures-rows → relaunch-fixtures-backfill-category-a → relaunch-player-stats-gap-fill-after-fixtures → verify-deployment-ui-coverage-jump`).
The 3 parallel cleanup tasks (`monitor-watchdog-catch-all`, `extend-reconcile-script-if-needed`,
`probe-suspected-tier-limitations`) can run any time.

### Critical workspace conventions to honor

These are non-negotiable per `.claude/CLAUDE.md` files in each repo:

1. **VM launches are launch-and-monitor pairs**, never fire-and-forget. After every `gcloud compute instances create`,
   wait 90s and verify the events directory
   (`gs://central-element-323112-events/events/instruments-service/{today}/{vm-name}/hour=*/`) has a `STARTED` event.
   Recheck every 10-15min for new events. The user pushes back hard on missing this step.
2. **Sports per-(date, league) `record_empty` is mandatory** for honest coverage (the bug we just fixed). If you find
   any other site emitting `manifest.add(row_count=0)` patch it the same way.
3. **VM tarball refresh** is required after any code change to ship via VMs:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` (use `/opt/homebrew/bin/bash` on
   macOS — the script uses bash-4 features).
4. **Singleton-locked launchers** (af-backfill-, fill-missing-player-stats-) share api_football's per-key rate limit.
   The safety lock refuses concurrent launches. Use `--force` only when justified (e.g. you're killing the prior VM
   right after).
5. **No `--no-verify` on commits** unless the lint failures are pre-existing sibling-agent files. The user's stated
   preference is "commit dirty stuff so workspace wipe doesn't lose it" but only when the files genuinely aren't yours
   to lint-fix.
6. **Catch-all watchdog**: the next watchdog VM should run with the new `c2ddda9` code. If you launch a daemon, label it
   `--labels=...,tier=daemon,purpose=<service-name>`. Otherwise it'll get reaped after `--heartbeat-stale=15min` of
   silence.

### Manifest concurrency (workspace-wide rule)

Any script you write that consumes the canonical manifest as a "to-do list" MUST follow the
`read-once + per-shard freshness check + write-time CAS` pattern. Reference impl: `/tmp/fill_missing_ohlcv.py`.
Otherwise concurrent workers waste API quota re-doing each other's work.

### After completion

- Update the plan's todo statuses: `status: todo` → `status: done`. Switch every `- [ ]` checkbox in `content:` to
  `- [x]`.
- When all 7 todos are `done`, ASK THE USER for unlock approval before archiving (per workspace plan-locking
  convention). Don't auto-unlock.
- Update memory: append a one-line entry to
  `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/MEMORY.md`
  pointing at a new `project_*_2026_05_07.md` (or whenever) summarising the recovery outcome. Surprising things to
  capture:
  - Final FIXTURES `captured` counts for AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE (should be ~150/season — write the
    actual number).
  - Total api_football quota burn for the cascade (should be well under the 74k daily ceiling — the gap-fill smoke math
    estimated ~17k calls).
  - Any Category B leagues whose tier-limitation probe surprised you.

### How to ask for help

The user prefers terse exploratory back-and-forth: state your conclusion in 2-3 sentences with the main tradeoff,
propose a path, wait for "yes do that" or course-correction. Don't write essays.

When in doubt about destructive operations (especially the drop-phantom-fixtures-rows step which mutates the canonical
manifest), ASK before running live. Dry-run first, show the count of rows that would be reclassified, then proceed only
on user go-ahead.

## END PROMPT
