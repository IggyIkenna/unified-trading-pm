---
doc_type: plan
title: sports-phantom-fixtures-recovery-2026-05-06
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, deployment-ui, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-06"
overview:
  Recover Category A leagues (AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE / ~36 others) from phantom-captured FIXTURES
  rows, then re-run dependent enrichments (PLAYER_STATS / FIXTURE_*) under the writer fix shipped in instruments-service
  `f36651c`.
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: instruments-service, code: C5, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C5, deployment: none, business: none }
  - { repo: deployment-service, code: C5, deployment: none, business: none }
depends_on: []
todos:
  - {
      id: refresh-tarballs,
      content:
        "- [x] [HUMAN+AGENT] P0. Refresh SPORTS tarballs to ship the orchestrator writer fix + UAC dedupe to future
        VMs.\n      Command: `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group
        SPORTS`\n      (use `/opt/homebrew/bin/bash` on macOS — the script uses bash-4 features).\n      Verify with
        `gcloud storage ls -l \"gs://deployment-scripts-central-element-323112/code/instruments-service-code.tar.gz\"`
        showing fresh mtime.\n      If the upload md5-mismatches and nukes a sibling tarball (mtds, etc.), re-run the
        script — same-day re-run reproduces fine.\n      **Done 2026-05-06**: instruments-service tarball mtime
        `08:26:57Z` → `11:03:51Z`; all 23 service tarballs refreshed.\n",
      status: done,
      note: Quick — 1-2 min.,
    }
  - { id: drop-phantom-fixtures-rows, content: "- [x] [HUMAN+AGENT] P0. Convert phantom `captured` FIXTURES rows
        (instrument_count=0, no parquet on disk) to honest manifest state so the orchestrator's `_should_skip_shard` no
        longer treats them as done.\n      **Done 2026-05-06** — implemented as a targeted one-shot script
        `instruments-service/scripts/flip_phantom_fixtures_zero_rows.py` (commit `962982e`) instead of using the generic
        reconcile_phantom_manifest_rows_all.py. The phantom signature here is unambiguous (`capture_status='captured'
        AND data_type='FIXTURES' AND instrument_count==0` violates 4-pillar rule #1 by definition — legacy
        `manifest.add(row_count=0)` API never wrote parquets), so per-row GCS path probing is unnecessary; takes the run
        from ~2h to ~30s.\n      **Production --apply outcome**: 100,431 rows flipped to
        `capture_status='empty_confirmed'` with `error_reason='phantom_zero_row_count_fixed_by_f36651c'`, original
        `attempted_at` preserved. Backup:
        `gs://instruments-store-sports-central-element-323112/_index/availability_index.20260506-111222.bak.parquet`.\
        \ Post-flip verification: 0 phantom rows remaining; 29,273 real captured FIXTURES rows untouched; 119 leagues
        affected (broader than the plan's ~38 estimate — every top European league had ~3041 phantoms from off-season /
        international-break dates).\n      Distinct from the original plan note: shipped as `empty_confirmed` (not
        `attempted_failed`) because manifest.add() was a manifest-only API — no parquet was ever written, so these are
        equivalent to \"we tried, source returned zero data, recorded honestly\". Saves ~100k unnecessary api_football
        re-attempts.\n", status: done, blocked_by: refresh-tarballs, note: "Implementation diverged from the original
        plan note (which suggested extending reconcile_phantom_manifest_rows_all.py with a 6th axis). The targeted
        one-shot pattern (flip_cefi_bug_x2_leaked_text.py / rename_vault_venue_canonical.py /
        flip_phantom_fixtures_zero_rows.py) is simpler, faster, and more idempotent for well-understood single-axis
        bugs. Reconcile-script extension is left for general-purpose phantom audits (cross-axis drift); this specific
        bug class is self-contained.

        " }
  - { id: corrective-reflip-to-attempted-failed, content: "- [x] [HUMAN+AGENT] P0. Re-flip the prior 100,431 FIXTURES
        `empty_confirmed` rows to `attempted_failed` (the orchestrator skips both `captured` and `empty_confirmed`, so
        the writer fix never re-attempts under the prior flip). PLUS extend to api_football per-fixture entities that
        share the same bug class (manifest.add(row_count=0) when FIXTURES enumeration was phantom-empty): INJURIES,
        FIXTURE_STATS, FIXTURE_EVENTS, FIXTURE_LINEUPS, PLAYER_STATS — filtered to (date, league) pairs that match the
        FIXTURES phantom set.\n      **Done 2026-05-06 12:23 UTC** —
        `instruments-service/scripts/flip_phantom_to_attempted_failed.py` (commit `2821111`); production --apply flipped
        176,021 rows total. Backup: `_index/availability_index.20260506-112347.bak.parquet`.\n      **Insufficient on
        its own**: discovered `check_shard_freshness` (UTL `manifest_writer.py:2356`) only checks row presence +
        schema_version + written_at — does NOT consider `capture_status`.\
        \ attempted_failed rows are still treated as \"fresh\" by the orchestrator pre-flight. See
        `feedback_check_shard_freshness_ignores_capture_status.md`. Required two follow-ups below (per-VM shard mirror +
        targeted DELETE).\n", status: done, blocked_by: drop-phantom-fixtures-rows }
  - {
      id: per-vm-shard-mirror-for-reader-visibility,
      content:
        "- [x] [HUMAN+AGENT] P0. Mirror corrective rows to a per-VM shard so the reader's per-VM merge sees them
        regardless of canonical mtime staleness (the 120s threshold means direct-canonical writes are invisible to
        readers >2 min later). **Done 2026-05-06 12:41 UTC** —
        `instruments-service/scripts/write_phantom_reflip_per_vm_shard.py` (commit `2d18d0d`) wrote 176,021 rows to
        `_index/per_vm/flip-phantom-corrective-20260506-114110.parquet`.\n      **Still insufficient**: even with
        corrective rows visible to the reader, attempted_failed rows pass `check_shard_freshness` because that function
        ignores capture_status. Two FIXTURES VMs (af-backfill-20260506-122705 / -124157) skip-cycled all 100k phantom
        dates and were killed.\n",
      status: done,
      blocked_by: corrective-reflip-to-attempted-failed,
    }
  - { id: targeted-delete-phantom-rows-from-shards, content: "- [x] [HUMAN+AGENT] P0. Delete phantom rows ENTIRELY from
        canonical + every per-VM shard so the orchestrator sees them as MISSING (the only state that bypasses
        `check_shard_freshness`). **Done 2026-05-06 13:07 UTC** —
        `instruments-service/scripts/delete_phantom_rows_from_shards.py` (commit `73be000`) production --apply deleted
        183,796 canonical rows + 623,307 per-VM rows across 10 shards (with duplicates between shards). Phantom
        signature: `(capture_status='attempted_failed' AND error_reason marker) OR (capture_status='captured' AND
        instrument_count==0)` restricted to FIXTURES + 5 api_football per-fixture entities. Backup-then-write per shard.
        Idempotent.\n      **Why DELETE not --force**: `--force` re-fetches EVERY date in the range (~6 years × 119
        leagues × 6 entities = millions of api_football calls). Targeted delete forces only the 176k truly-phantom rows
        to be re-fetched. The `check_shard_freshness` design only respects \"missing\"\
        \ as a re-attempt signal.\n", status: done, blocked_by: per-vm-shard-mirror-for-reader-visibility }
  - { id: relaunch-fixtures-backfill-category-a, content: "- [x] [HUMAN+AGENT] P0. Relaunch FIXTURES backfill for the
        176,021 (now-deleted) phantom (date, league) rows. The orchestrator will see them as MISSING and fetch under the
        new writer fix, which `record_empty`s zero-fixture days correctly.\n      Command: `bash
        deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity FIXTURES 2020-06-06
        2026-05-04`\n      **Multiple VM iterations** (each killed/replaced as bugs surfaced):\n        * v1
        `af-backfill-20260506-122705` 12:27 — skip-cycled because corrective flip was empty_confirmed. Killed
        12:40.\n        * v2 `af-backfill-20260506-124157` 12:42 — skip-cycled because attempted_failed still passes
        `check_shard_freshness`. Killed 12:55.\n        * v3 `af-backfill-20260506-125413` 12:54 — launched with
        `--force` but bypassed too broadly. Killed 13:00.\n        * v4 `af-backfill-20260506-130727` 13:07 — OOM at
        exit_code=137 on e2-standard-2 (per-VM shard merge × 51 shards ×\
        \ pandas concat blew past 8GB). Auto-shut.\n        * **v5 `af-backfill-20260506-131302` 13:13 LIVE on
        e2-standard-4** — launcher patched (deployment-service `b7c5d8e`) to default e2-standard-4 with MACHINE_TYPE
        override. Phantom rows previously deleted from canonical + 10 per-VM shards (instruments-service `73be000`);
        orchestrator should now see them as missing and fetch.\n", status: launched, blocked_by: targeted-delete-phantom-rows-from-shards, note: 'Watch
        for new captures via the manifest: AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE FIXTURES `captured` count should
        rise from 0-real to ~150 fixtures/season. Run `python3 -c "import pandas as pd, io; from google.cloud import
        storage; df =
        pd.read_parquet(io.BytesIO(storage.Client().bucket(''instruments-store-sports-central-element-323112'').blob(''_index/availability_index.parquet'').download_as_bytes()));
        print(df[(df[''data_type'']==''FIXTURES'') &
        (df[''league_id''].isin([''AUSTRIAN_BUNDESLIGA'',''GREEK_SUPER_LEAGUE''])) &
        (df[''capture_status'']==''captured'') & (df[''instrument_count'']>0)].groupby(''league_id'').size())"` to
        verify post-run.

        ' }
  - { id: relaunch-per-fixture-downstream-after-fixtures, content: "- [ ] [HUMAN+AGENT] P0. After FIXTURES re-backfill
        (`af-backfill-20260506-131302`) auto-shuts, sequentially relaunch the api_football per-fixture downstream
        entities for the 75,590 deleted-phantom rows. Use the chain runner (deployment-service `5be53a7`) which
        auto-cycles through all 5 entities:\n      ```\n      tmux new-session -d -s phantom-chain bash
        deployment-service/scripts/vm/run-sports-phantom-downstream-chain.sh \\\\\n        --start-date 2020-06-06
        --end-date 2026-05-04\n      ```\n      Or invoke launchers manually (singleton lock on `af-backfill-` prefix
        means these are sequential, one VM at a time):\n      1. `bash
        deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity PLAYER_STATS 2020-06-06 2026-05-04` —
        15,646 attempted_failed rows\n      2. `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh
        --entity FIXTURE_STATS 2020-06-06 2026-05-04` — 17,919 rows\n      3. `bash
        deployment-service/scripts/vm/launch-api-football-backfill-vm.sh\
        \ --entity FIXTURE_EVENTS 2020-06-06 2026-05-04` — 17,590 rows\n      4. `bash
        deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity FIXTURE_LINEUPS 2020-06-06 2026-05-04`
        — 16,633 rows\n      5. `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity INJURIES
        2020-06-06 2026-05-04` — 7,802 rows\n      (Optional alternative for PLAYER_STATS:
        `launch-fill-missing-player-stats-vm.sh` is the targeted gap-fill that reads manifest + only fetches missing —
        same outcome, slightly faster startup.) Each VM auto-shuts on completion; estimate ~30-60 min wall-clock per
        entity at api_football Pro tier rate ceiling. Total ~3-5h sequential.\n", status: todo, blocked_by: relaunch-fixtures-backfill-category-a, note: "The
        orchestrator's per-fixture adapters depend on FIXTURES being correctly populated first — that's why the sequence
        is FIXTURES → downstream. Cat-B leagues (POLAND_I_LIGA / J2_LEAGUE / EMPEROR_CUP / cups) will continue to write
        `empty_confirmed` because api_football Pro tier doesn't cover them — that's correct behaviour, not a bug to
        retry.

        " }
  - {
      id: audit-and-flip-stale-empties,
      content:
        "- [ ] [AGENT] P1. After the per-fixture downstream sweep completes, audit the residual ~223k `empty_confirmed`
        rows on per-fixture entities for any drift: rows that were stamped empty when FIXTURES was phantom-empty but
        where the now-correctly-populated FIXTURES has `instrument_count > 0`. Those are wrongly-empty downstream
        rows.\n      Logic: for each per-fixture data type (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS /
        FIXTURE_LINEUPS / INJURIES), filter rows with `capture_status='empty_confirmed'`. For each, look up the
        corresponding FIXTURES row; if FIXTURES is now `captured AND instrument_count > 0`, flip the downstream row to
        `attempted_failed`. Re-launch the per-fixture backfills if any drift is found.\n      Expected scale: ~14% of
        223k = ~31k rows (matches the 13% match-day ratio observed in EPL etc.). Worth one final pass to close the
        loop.\n",
      status: todo,
      blocked_by: relaunch-per-fixture-downstream-after-fixtures,
      note: "Implementation pattern mirrors `flip_phantom_to_attempted_failed.py` — read manifest, build cross-reference
        index, flip drift rows, backup-then-write.

        ",
    }
  - { id: verify-deployment-ui-coverage-jump, content: "- [ ] [HUMAN] P1. After all entity runs above complete (FIXTURES
        + 5 per-fixture downstreams + audit-and-flip-stale-empties pass), clear the `/turbo` cache (`curl -X POST
        http://localhost:8004/api/data-status/turbo/clear` OR click \"Clear Cache\" in the deployment-UI) and verify
        SPORTS coverage in the UI.\n      Expected jumps:\n        - Category A leagues (AUSTRIAN_BUNDESLIGA /
        GREEK_SUPER_LEAGUE / ~17 others): 0% → ~30-40% (top tiers, normal coverage rate).\n        - Category B leagues
        (cups + lower divisions): stay at low coverage but with HONEST `empty_confirmed` rows instead of phantom
        captured ones.\n        - Overall PLAYER_STATS: 78% → ~85%+ (driven by Category A recovery).\n        - Overall
        FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES: similar climb (broader downstream sweep covered all
        api_football per-fixture entities, not just PLAYER_STATS).\n        - Overall FIXTURES: marginal change
        (denominator stays same,\
        \ captured count drops to honest figures, empty_confirmed grows).\n      Take a screenshot for the session
        log.\n", status: todo, blocked_by: audit-and-flip-stale-empties, note: "" }
  - {
      id: monitor-watchdog-catch-all,
      content:
        "- [ ] [HUMAN+AGENT] P2. Tail the catch-all watchdog logs (`vm-zombie-watchdog-20260506-094758` or its
        successor) for 24h to confirm:\n        1. NO false-positive kills of legitimate slow VMs (gap-fill,
        mdps-tradfi, etc.).\n        2. Daemons (`manifest-consolidator-*`, `vm-zombie-watchdog-*`) are correctly opted
        out via `tier=daemon` / `purpose=vm-zombie-watchdog`.\n        3. Unknown-prefix VMs (if any) show up in the new
        \"heartbeat-only watch\" log line.\n      If any false-positive kill: tighten `--heartbeat-stale` (default 15
        min) or extend the `DAEMON_TIER_LABELS` set.\n",
      status: todo,
      note: Independent of the FIXTURES recovery — runs in parallel.,
    }
  - {
      id: extend-reconcile-script-if-needed,
      content:
        "- [ ] [AGENT] P2. If `reconcile_phantom_manifest_rows_all.py` doesn't already handle the
        \"captured-with-row_count=0-and-no-parquet\" axis, extend it to do so. This is drift axis #6 (per the CLAUDE.md
        memory's \"5 axes\" — adds a sixth).\n      New axis: scan all `capture_status=captured` rows where
        `instrument_count == 0`. For each, probe the canonical parquet path. If parquet missing OR present-but-empty:
        convert to `empty_confirmed` (preserve original `attempted_at`). NOT a delete — the row's `attempted_at` is
        still real history we want to keep.\n      Update CLAUDE.md memory file
        `feedback_phantom_audit_five_drift_axes.md` to \"six drift axes\".\n",
      status: todo,
      note:
        Only needed if drop-phantom-fixtures-rows reveals the existing script can't handle this case. Probe with
        --dry-run first.,
    }
  - {
      id: probe-suspected-tier-limitations,
      content:
        "- [ ] [AGENT] P3. For the 18 Category B leagues that probably ARE api_football tier limitations (cups + lower
        divisions), run a single live probe per league to confirm and document. Update each league's `LeagueDefinition`
        in UAC `league_data_other.py` with `data_sources=` excluding `api_football` if confirmed empty, so the
        orchestrator stops pre-emptively trying.\n      Reference incident shape: POLAND_I_LIGA fixture 1037780 captured
        on disk, `/fixtures/players?fixture=1037780` → 0 teams. Same expected for J2_LEAGUE / EMPEROR_CUP / SCOTTISH_CUP
        / etc.\n      Output: PR to UAC with the data_sources updates + a short
        `/codex/02-data/sports-data-source-coverage-matrix.md` table extension. Avoids the orchestrator burning
        api_football quota on permanent-empty leagues every run.\n",
      status: todo,
      note: Cleanup. Lifts the noise floor for cup-heavy weekends.,
    }
isProject: false
---

# Sports Phantom FIXTURES Recovery — 2026-05-06

> **2026-05-06 supersession note.** Remaining open todos in this plan are either (a) **already superseded by
> `sports_fixtures_truthset_recovery_2026_05_06.md`** (which declares `supersedes_phases:` covering
> `relaunch-fixtures-backfill-category-a` + `audit-and-flip-stale-empties`), or (b) **blocked by the upcoming UTL
> `check_shard_freshness` fix** (extend to treat `ATTEMPTED_FAILED` as stale; once shipped, the DELETE-shard pattern
> here becomes optional and flip-to-`attempted_failed` works as originally designed). The downstream-entity sweep
> (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES) has dependency on the truthset's
> api_football direct-call truth-set, not this plan's manifest-trust approach. **Action:** read truthset plan first; if
> any todo here isn't superseded by truthset and isn't unblocked by the UTL fix, mark it explicit. Otherwise treat this
> plan as historical context, archive when truthset closes its Phase 2.

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
