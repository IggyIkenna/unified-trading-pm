---
name: sports-phantom-fixtures-recovery-2026-05-06
overview:
  Recover Category A leagues (AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE / ~36 others) from phantom-captured FIXTURES
  rows, then re-run dependent enrichments (PLAYER_STATS / FIXTURE_*) under the writer fix shipped in instruments-service
  `f36651c`.
type: code
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-06

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: instruments-service
    code: C5 # writer fix shipped + tests passing (f36651c)
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C5 # SCOTTISH_LEAGUE_CUP_185 dedupe + RUF003 fix shipped (9599e8f)
    deployment: none
    business: none
  - repo: deployment-service
    code: C5 # gap-fill launcher + watchdog catch-all shipped (c2ddda9 + bd5e373)
    deployment: none
    business: none

depends_on: []

todos:
  - id: refresh-tarballs
    content: |
      - [x] [HUMAN+AGENT] P0. Refresh SPORTS tarballs to ship the orchestrator writer fix + UAC dedupe to future VMs.
            Command: `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`
            (use `/opt/homebrew/bin/bash` on macOS — the script uses bash-4 features).
            Verify with `gcloud storage ls -l "gs://deployment-scripts-central-element-323112/code/instruments-service-code.tar.gz"` showing fresh mtime.
            If the upload md5-mismatches and nukes a sibling tarball (mtds, etc.), re-run the script — same-day re-run reproduces fine.
            **Done 2026-05-06**: instruments-service tarball mtime `08:26:57Z` → `11:03:51Z`; all 23 service tarballs refreshed.
    status: done
    note: "Quick — 1-2 min."

  - id: drop-phantom-fixtures-rows
    content: |
      - [x] [HUMAN+AGENT] P0. Convert phantom `captured` FIXTURES rows (instrument_count=0, no parquet on disk) to honest manifest state so the orchestrator's `_should_skip_shard` no longer treats them as done.
            **Done 2026-05-06** — implemented as a targeted one-shot script `instruments-service/scripts/flip_phantom_fixtures_zero_rows.py` (commit `962982e`) instead of using the generic reconcile_phantom_manifest_rows_all.py. The phantom signature here is unambiguous (`capture_status='captured' AND data_type='FIXTURES' AND instrument_count==0` violates 4-pillar rule #1 by definition — legacy `manifest.add(row_count=0)` API never wrote parquets), so per-row GCS path probing is unnecessary; takes the run from ~2h to ~30s.
            **Production --apply outcome**: 100,431 rows flipped to `capture_status='empty_confirmed'` with `error_reason='phantom_zero_row_count_fixed_by_f36651c'`, original `attempted_at` preserved. Backup: `gs://instruments-store-sports-central-element-323112/_index/availability_index.20260506-111222.bak.parquet`. Post-flip verification: 0 phantom rows remaining; 29,273 real captured FIXTURES rows untouched; 119 leagues affected (broader than the plan's ~38 estimate — every top European league had ~3041 phantoms from off-season / international-break dates).
            Distinct from the original plan note: shipped as `empty_confirmed` (not `attempted_failed`) because manifest.add() was a manifest-only API — no parquet was ever written, so these are equivalent to "we tried, source returned zero data, recorded honestly". Saves ~100k unnecessary api_football re-attempts.
    status: done
    blocked_by: refresh-tarballs
    note: |
      Implementation diverged from the original plan note (which suggested extending reconcile_phantom_manifest_rows_all.py with a 6th axis). The targeted one-shot pattern (flip_cefi_bug_x2_leaked_text.py / rename_vault_venue_canonical.py / flip_phantom_fixtures_zero_rows.py) is simpler, faster, and more idempotent for well-understood single-axis bugs. Reconcile-script extension is left for general-purpose phantom audits (cross-axis drift); this specific bug class is self-contained.

  - id: relaunch-fixtures-backfill-category-a
    content: |
      - [ ] [HUMAN+AGENT] P0. Relaunch FIXTURES backfill for Category A leagues. After the phantom drop, every (date, league) pair in the affected leagues will be either `attempted_failed` (the dropped phantoms) or `missing` (never attempted). The orchestrator will re-attempt them under the new tarball's writer fix, which `record_empty`s zero-fixture days correctly.
            Command: `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity FIXTURES 2020-06-06 2026-05-04`
            VM_END_DATE clipped to api_football PLAYER_STATS coverage start (matching the gap-fill scope already established).
            Singleton lock: kill the current `fill-missing-player-stats-*` VM first or use `--force` if it's still running. Will share api_football quota until gap-fill VM auto-shuts.
    status: todo
    blocked_by: drop-phantom-fixtures-rows
    note: |
      Watch for new captures via the manifest: AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE FIXTURES `captured` count should rise from 0-real to ~150 fixtures/season. Run `python3 -c "import pandas as pd, io; from google.cloud import storage; df = pd.read_parquet(io.BytesIO(storage.Client().bucket('instruments-store-sports-central-element-323112').blob('_index/availability_index.parquet').download_as_bytes())); print(df[(df['data_type']=='FIXTURES') & (df['league_id'].isin(['AUSTRIAN_BUNDESLIGA','GREEK_SUPER_LEAGUE'])) & (df['capture_status']=='captured') & (df['instrument_count']>0)].groupby('league_id').size())"` to verify post-run.

  - id: relaunch-player-stats-gap-fill-after-fixtures
    content: |
      - [ ] [HUMAN+AGENT] P0. After FIXTURES re-backfill completes, relaunch the targeted PLAYER_STATS gap-fill so the now-discoverable Austrian / Greek / etc. fixtures get player-stats captured.
            Command: `bash deployment-service/scripts/vm/launch-fill-missing-player-stats-vm.sh --concurrency 4`
            (Reads canonical manifest, recomputes the missing-shard set — should now include the 38 leagues' real fixtures because the FIXTURES manifest finally has truthful `instrument_count > 0` rows for them.)
            Singleton lock will protect against running while af-backfill VM is still alive.
    status: todo
    blocked_by: relaunch-fixtures-backfill-category-a
    note: |
      Estimated run-time: similar to the original gap-fill run (~30-60 min wall-clock at api_football's per-key rate ceiling). Cat-B leagues (POLAND_I_LIGA / J2_LEAGUE / EMPEROR_CUP / cups) will continue to write `empty_confirmed` because api_football Pro tier doesn't cover them — that's correct behaviour, not a bug to retry.

  - id: verify-deployment-ui-coverage-jump
    content: |
      - [ ] [HUMAN] P1. After all three runs above complete, clear the `/turbo` cache (`curl -X POST http://localhost:8004/api/data-status/turbo/clear` OR click "Clear Cache" in the deployment-UI) and verify SPORTS coverage in the UI.
            Expected jumps:
              - Category A leagues (AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE / ~17 others): 0% → ~30-40% (top tiers, normal coverage rate).
              - Category B leagues (cups + lower divisions): stay at low coverage but with HONEST `empty_confirmed` rows instead of phantom captured ones.
              - Overall PLAYER_STATS: 78% → ~85%+ (driven by Category A recovery).
              - Overall FIXTURES: marginal change (denominator stays same, captured count drops to honest figures, empty_confirmed grows).
            Take a screenshot for the session log.
    status: todo
    blocked_by: relaunch-player-stats-gap-fill-after-fixtures
    note: ""

  - id: monitor-watchdog-catch-all
    content: |
      - [ ] [HUMAN+AGENT] P2. Tail the catch-all watchdog logs (`vm-zombie-watchdog-20260506-094758` or its successor) for 24h to confirm:
              1. NO false-positive kills of legitimate slow VMs (gap-fill, mdps-tradfi, etc.).
              2. Daemons (`manifest-consolidator-*`, `vm-zombie-watchdog-*`) are correctly opted out via `tier=daemon` / `purpose=vm-zombie-watchdog`.
              3. Unknown-prefix VMs (if any) show up in the new "heartbeat-only watch" log line.
            If any false-positive kill: tighten `--heartbeat-stale` (default 15 min) or extend the `DAEMON_TIER_LABELS` set.
    status: todo
    note: "Independent of the FIXTURES recovery — runs in parallel."

  - id: extend-reconcile-script-if-needed
    content: |
      - [ ] [AGENT] P2. If `reconcile_phantom_manifest_rows_all.py` doesn't already handle the "captured-with-row_count=0-and-no-parquet" axis, extend it to do so. This is drift axis #6 (per the CLAUDE.md memory's "5 axes" — adds a sixth).
            New axis: scan all `capture_status=captured` rows where `instrument_count == 0`. For each, probe the canonical parquet path. If parquet missing OR present-but-empty: convert to `empty_confirmed` (preserve original `attempted_at`). NOT a delete — the row's `attempted_at` is still real history we want to keep.
            Update CLAUDE.md memory file `feedback_phantom_audit_five_drift_axes.md` to "six drift axes".
    status: todo
    note:
      "Only needed if drop-phantom-fixtures-rows reveals the existing script can't handle this case. Probe with
      --dry-run first."

  - id: probe-suspected-tier-limitations
    content: |
      - [ ] [AGENT] P3. For the 18 Category B leagues that probably ARE api_football tier limitations (cups + lower divisions), run a single live probe per league to confirm and document. Update each league's `LeagueDefinition` in UAC `league_data_other.py` with `data_sources=` excluding `api_football` if confirmed empty, so the orchestrator stops pre-emptively trying.
            Reference incident shape: POLAND_I_LIGA fixture 1037780 captured on disk, `/fixtures/players?fixture=1037780` → 0 teams. Same expected for J2_LEAGUE / EMPEROR_CUP / SCOTTISH_CUP / etc.
            Output: PR to UAC with the data_sources updates + a short `codex/02-data/sports-data-source-coverage-matrix.md` table extension. Avoids the orchestrator burning api_football quota on permanent-empty leagues every run.
    status: todo
    note: "Cleanup. Lifts the noise floor for cup-heavy weekends."

isProject: false
---

# Sports Phantom FIXTURES Recovery — 2026-05-06

## Context

While auditing why 38 sports leagues showed 0% PLAYER_STATS coverage in the deployment-UI, we discovered a deeper bug:
the FIXTURES adapter's zero-fixture path was emitting `manifest.add(row_count=0, ...)` for every Prediction-tier league
on every date, creating phantom `captured` rows that **violate CLAUDE.md "4 pillars" rule #1** (`row_count > 0` OR
`record_empty`, NEVER `captured` with `row_count=0`).

**Diagnosed evidence (2026-05-06):**

- AUSTRIAN_BUNDESLIGA: 4572 manifest FIXTURES rows, of which 3041 marked `captured`, **0 with `instrument_count > 0`**.
  Live api_football probe: `/fixtures?league=218&season=2024` returns 195 results; `/fixtures/players?fixture=1218574`
  returns 2 teams × 20 players. Data exists upstream.
- GREEK_SUPER_LEAGUE: same shape. SCOTTISH_LEAGUE_CUP_185: same shape.
- POLAND_I_LIGA / J2_LEAGUE / EMPEROR_CUP: have 825 / 552 / 77 real captured fixtures respectively, but 0 PLAYER_STATS
  captures. Direct probe of POLAND_I_LIGA fixture 1037780 → `/fixtures/players` returns `0 teams` → **api_football tier
  limitation, not our bug**. These leagues stay 0%.

## Pre-audit manifest

Already shipped (this session):

| Repo                  | Commit    | Change                                                                                                                                                                                         |
| --------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service   | `f36651c` | 5 sites in orchestrator.py: `manifest.add(row_count=0)` → `record_empty(row_key)` for SPORTS zero-fixture + TradFi non-trading-day. Empty placeholder parquet writes dropped. 3 tests updated. |
| unified-api-contracts | `9599e8f` | Dropped `SCOTTISH_LEAGUE_CUP_185` duplicate registry entry + fixed RUF003 stray `×` in `tradfi_symbology.py:553`.                                                                              |
| deployment-service    | `c2ddda9` | Catch-all watchdog (every running VM watched, daemons opt-out via `tier=daemon` / `purpose=vm-zombie-watchdog`).                                                                               |
| deployment-service    | `bd5e373` | `launch-fill-missing-player-stats-vm.sh` + `sports-gap-fill` dispatch in `setup-data-pipeline-vm.sh` + `fill-missing-player-stats-` watchdog prefix.                                           |
| instruments-service   | `1703a09` | `scripts/fill_missing_player_stats.py` — targeted gap-fill mirroring `/tmp/fill_missing_ohlcv.py` pattern.                                                                                     |

Live VMs at handover:

- `fill-missing-player-stats-20260506-082808` — running, processing chronologically through the missing PLAYER_STATS
  set, rate-limit-bound (api_football). Will auto-shutdown on completion.
- `fs-backfill-20260506-083546` — running, full footystats sweep with the new MATCHES adapter.
- `vm-zombie-watchdog-20260506-094758` — running with new catch-all logic + `tier=daemon` opt-out label.

## Execution DAG

```
refresh-tarballs (P0, ~1 min)
    │
    ▼
drop-phantom-fixtures-rows (P0, ~30-60 min on a same-region VM)
    │
    ▼
relaunch-fixtures-backfill-category-a (P0, ~1-2h wall-clock at api_football rate ceiling)
    │
    ▼
relaunch-player-stats-gap-fill-after-fixtures (P0, ~30-60 min)
    │
    ▼
verify-deployment-ui-coverage-jump (P1, ~5 min)


PARALLEL throughout (independent):
  monitor-watchdog-catch-all (P2)
  extend-reconcile-script-if-needed (P2 — only if needed)
  probe-suspected-tier-limitations (P3 — cleanup)
```

## Success criteria

- **C5** instruments-service: orchestrator writer fix landed (already met, `f36651c`).
- **C5** unified-api-contracts: registry dedupe landed (already met, `9599e8f`).
- **Manifest correctness**: zero `captured` rows where `data_type ∈ sports_data_types AND instrument_count == 0` after
  the drop-phantom step.
- **Coverage recovery**: AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE FIXTURES `captured + instrument_count > 0` count rises
  from 0 to ~150 per season after the FIXTURES re-backfill.
- **PLAYER_STATS jump**: deployment-UI shows PLAYER_STATS overall climb from 78% → ~85%+.
- **No regression**: Category B leagues (cups + lower divisions) stay at low coverage with `empty_confirmed` rows (NOT
  phantom captured), since api_football tier genuinely doesn't have player_stats for them.

## Risk + rollback

- **Risk**: dropping phantom rows then re-running FIXTURES could overwhelm the api_football daily quota (74k req/day at
  handover). Mitigation: the targeted gap-fill pattern (manifest-aware) already restricts work to the missing set, so
  re-running on a phantom-cleared manifest fires API calls only for the previously-phantomed dates — much smaller than a
  full 6-year sweep. Estimated ~17k api calls per CDR-style sizing math from the gap-fill smoke test.
- **Rollback**: every step is idempotent. If the drop-phantom step misclassifies anything, the next legitimate run
  rewrites it. The original phantom rows are reproducible from `attempted_at` if needed.
- **Concurrent VMs**: gap-fill VM and re-backfill VM share api_football's per-key rate. Acceptable because they target
  different entities (the running gap-fill is PLAYER_STATS-only; the new VM would be FIXTURES-only). They throttle each
  other by ~50% but eventually both finish.

## Anti-patterns to avoid

- **DO NOT** delete phantom rows outright — convert them to `empty_confirmed` or `attempted_failed` so the historical
  `attempted_at` audit trail is preserved.
- **DO NOT** write empty placeholder parquets ever again. The orchestrator fix dropped these explicitly.
- **DO NOT** re-add `SCOTTISH_LEAGUE_CUP_185` to UAC if the next af-backfill emits unmapped api_football_id=185 fixtures
  — `_canonical_league_id()` should fall through and the row gets dropped, which is honest. The duplicate was the bug.
- **DO NOT** retry Category B leagues hoping api_football changes its mind. Confirm tier limitation once via probe and
  exclude `api_football` from `data_sources` in UAC.
