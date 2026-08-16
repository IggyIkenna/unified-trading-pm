---
doc_type: issue
title: >-
  CRITICAL DP_CATALOG_NOT_RUNNING (DP-CATALOG-001) — sports instrument catalogue stale, traced to an uncaught
  JunkSymbolError (mojibake player/team name) crashing the entire FTP rollup; fixed with per-row shard isolation
summary: >-
  data_pipeline_failure escalation agt-941c20 responded to a CRITICAL page: gs://instruments-store-sports-prd-central-
  element-323112/prod/catalog.parquet age 1776min (29.6h) > 24h budget. Root cause traced via live Cloud Run Job logs
  (not a guess): the 2026-08-06 01:00 UTC lifecycle-catalogue-regen-sports execution ran the full FTP (fixture/team/
  player) window rebuild over 99,488 by_date parquets, then crashed with an UNCAUGHT
  unified_api_contracts.canonical.domain.sports.canonical_ids.JunkSymbolError: "control character in name: 'JeleÅ\x84'"
  raised out of build_player_id → _slug → _reject_junk_symbols. "JeleÅ\x84" is a classic UTF-8-bytes- decoded-as-Latin-1
  mojibake of the Polish surname "Jeleń" — a genuine upstream capture/encoding defect somewhere in the sports
  player-name pipeline, NOT this catalogue script's bug, but the catalogue script had zero shard-level isolation around
  the per-row id-build call: ONE corrupted name anywhere in the 99k-blob window crashed the ENTIRE rollup (exit 1), so
  the job never reached the monotonic-guard/promote-write step at all — a structurally different failure mode from the
  two PRE-EXISTING sports catalogue incidents this codebase already fixed (2026-07-15 FTP frozen- tail shrink-block;
  2026-08-02 defi's separate R3-migration-gated pause). Fixed by wrapping the per-row build_team_id/build_player_id
  calls in build_sports_fixture_team_player_catalogue with try/except ValueError (JunkSymbolError subclasses ValueError)
  — skip + count the corrupted row, log once, continue rolling up the other ~99,487 files — the same
  shard-level-failure-isolation discipline this codebase already applies to other per-blob loops in this same file (see
  _iter_sports_ftp_snapshots' own "skip vanished/malformed blob" warnings).
status: archived
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    catalog,
    catalogue,
    dp-catalog-001,
    dp-alerts,
    sports,
    junk-symbol,
    mojibake,
    encoding,
    shard-isolation,
    data-pipeline,
    critical-page,
  ]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md,
    /plans/archive/issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md,
  ]
created: 2026-08-06
last_updated: "2026-08-16"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  "data_pipeline_failure one-shot escalation agt-941c20, slot-4, 2026-08-06, responding to a CRITICAL DP-CATALOG-001
  page"
resolved_by: ["instruments-service@497c4f5e"]
locked_by:
locked_since:
context_scope:
  [
    instruments-service/scripts/build_instrument_catalogue.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/canonical_ids.py,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md,
  ]
---

> **📦 ARCHIVED 2026-08-16 — RESOLVED.** Every todo done (P1 crash-isolation fix, P2 promotion-verification, P3
> upstream-encoding-defect trace+fix), unlocked, no dependents blocking. Final fix: instruments-service@5f2f3ca619
> (pinned `encoding="utf-8"` on every `resp.json(content_type=None)` call site in the sports adapters — see the P3 todo
> below for full root-cause evidence). Successor: none — self-contained fix, no follow-on doc needed (a narrow
> non-sports fleet-audit follow-up was filed separately as `aiohttp_json_charset_guessing_audit_2026_08_16.md`).

> **✅ UNBLOCKED 2026-08-08 — the promotion blocker cleared; the verification todo is now runnable.** This doc's
> remaining verification todo was gated on
> `/plans/archive/2026_08/issues/instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md`. That
> blocker is RESOLVED: `instruments-service` `main` HEAD is `db7f7d3b44` _"chore(promote): LDR → main (Option-B
> direct)"_ (2026-08-07T23:02:53Z), and the fix is confirmed present **by content** on main —
> `origin/main:scripts/build_instrument_catalogue.py` contains `junk_name_skips`. (SHA reachability against the
> pre-rewrite `497c4f5e` is not a valid check: the repo underwent a history rewrite on 2026-08-05.) **Now runnable**:
> confirm the sports catalogue advances past the frozen 2026-08-05T01:09:18Z snapshot, which is what actually clears
> DP-CATALOG-001.

# DP-CATALOG-001: sports catalogue stale — traced to an uncaught JunkSymbolError crashing the whole FTP rollup

## Evidence trail (all verified live, this session — `gcloud`/`gsutil` as `unified-trading-sa`)

1. **Alert**: `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` age 1776min (29.6h) > 24h
   budget at dispatch time. `gsutil stat` confirmed the frozen snapshot: `Update time: Wed, 05 Aug 2026 01:09:18 GMT`.
2. **The cron IS firing** —
   `gcloud run jobs executions list --job=lifecycle-catalogue-regen-sports --region=asia-northeast1`: fired daily at
   01:00 UTC every day 2026-07-28 through 2026-08-05 (all `succeededCount=1`), then the 2026-08-06 execution
   (`lifecycle-catalogue-regen-sports-rhcp4`) ran 23 minutes and exited 1 (`NonZeroExitCode`, `retriedCount: 1` — one
   internal retry, same crash both times).
3. **Failure mode: uncaught `JunkSymbolError`, not the previously-fixed shrink-block/OOM classes.**
   `gcloud logging read` on the failed execution shows the full traceback:
   `build_instrument_catalogue.py:5054 run_rollup → _merge_sports_ftp_with_frozen_tail → line 4317 → build_sports_fixture_team_player_catalogue → line 3328 → build_player_id → canonical_ids.py:164 → _slug → line 76 → _reject_junk_symbols → JunkSymbolError: control character in name: 'JeleÅ\x84'`,
   then `Container called exit(1)`. Both the primary attempt (01:12:03Z) and the retry (01:23:13Z) hit the
   byte-identical error on the byte-identical name — not a flake.
4. **The name is a genuine mojibake, not a real junk value.** `'JeleÅ\x84'` is the classic signature of UTF-8 bytes
   (`Jeleń` → `4A 65 6C 65 C5 84`) decoded as Latin-1/cp1252 somewhere upstream: `0xC5` → `Å`, `0x84` → an unassigned C1
   control character (hence "control character in name"). `_reject_junk_symbols`'s own docstring correctly distinguishes
   this from a legitimate accented name ("México", "São Paulo" are NOT rejected) — the guard is doing its job; the bug
   is that ONE row hitting this guard took down the whole rollup instead of just that row.
5. **No shard-level isolation around the per-row id-build call.** `build_sports_fixture_team_player_catalogue` (the
   function this exact traceback names) iterates ~99,488 by_date parquet-derived rows across 3 grains
   (fixtures/teams/players) and called `build_team_id`/`build_player_id` directly inside the loop with no `try/except` —
   a single corrupted name anywhere in the whole trailing 400-day window is fatal to the entire job, contradicting this
   codebase's own shard-level-failure-isolation convention (the same function's sibling walk,
   `_iter_sports_ftp_snapshots`, already logs-and-skips a malformed/vanished blob rather than raising).

## Fix shipped (instruments-service@497c4f5e, quickmerge, quality gates green 84s)

Wrapped the two `_slug`-reachable id-build call sites in `build_sports_fixture_team_player_catalogue` in
`try/except ValueError` (`JunkSymbolError` is a `ValueError` subclass, so this also covers a corrupted home/away team
name reached via `build_team_id`, not just the player-name path the live traceback hit): a caught row increments a
`junk_name_skips` counter and `continue`s; after the loop, a single `logger.warning` reports the skip count (visible in
Cloud Logging, non-fatal, doesn't spam per-row). Added a regression test
(`test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run`) reproducing the exact live incident string
(`'JeleÅ\x84'`) plus a junk home-team-name fixture in the same blob, proving both are skipped while the clean
fixture/player rows in the SAME blob still roll up. Full `instruments-service` `quality-gates.sh --no-fix` green (94s
local, 84s on quickmerge's own Pass-1 re-run).

**Not a mask**: `_reject_junk_symbols` still rejects the corrupted name exactly as designed (the row does NOT enter the
catalogue with a mangled slug) — this fix only stops one bad row from vetoing the other 99,487.

## Not fixed here — the upstream encoding defect (follow-up)

The catalogue-rollup crash is fixed, but the ROOT CAUSE of the mojibake itself — some sports player-name capture path
somewhere upstream (MTDS `sports_reference` adapters, most likely api_football lineups given the traceback's
`fixture_lineups` entity) is producing UTF-8-as-Latin-1 double-encoded names — is NOT diagnosed or fixed in this
escalation. Grepped MTDS for `player_name`/`fixture_lineups` writers and found no direct hit in this repo (the raw
`player_name` field the catalogue script reads is written by whatever MTDS sports adapter/orchestrator populates
`sports_reference/by_date/.../entity=fixture_lineups/`); tracing the EXACT write site would need either a targeted grep
sweep of the MTDS sports orchestrator/adapters for a wrong-charset decode (`.decode("latin-1")` /
`.encode("latin-1").decode("utf-8")` anti-pattern) or pulling the actual corrupted by_date blob(s) containing this row —
out of scope for a bounded one-shot escalation responding to a live page. The new `junk_name_skips` warning log line
(STEP above) now makes future occurrences of this class visible in Cloud Logging without crashing anything, which is the
observability hook whoever picks up the follow-up needs.

## Todos

- [x] [DATA] P1. Fix the uncaught-exception crash so a single corrupted display name cannot fail the whole sports
      catalogue rollup — instruments-service@497c4f5e (try/except ValueError, regression test, QG green, quickmerged).
- [x] ✅ DONE 2026-08-08 (round5-sports session) — re-verified live: `gsutil stat` on
      `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` now shows Update time
      **2026-08-08T08:16:12Z** (creation time identical, i.e. a clean fresh write, not a stale re-stat), well past the
      frozen 2026-08-05T01:09:18Z snapshot — DP-CATALOG-001 clears. Cross-checked against instruments-service
      `origin/main` HEAD `d89b9cb193` (fetched live 2026-08-08), which contains `junk_name_skips` in
      `scripts/build_instrument_catalogue.py` (confirmed by content, not by a since-rewritten SHA-ancestry check) — the
      fix is live on `main` and the deployed image has run it successfully. ~~[OPS] P2. Verify a
      `lifecycle-catalogue-regen-sports` run promotes cleanly and `prod/catalog.parquet` mtime advances past the frozen
      2026-08-05T01:09:18Z snapshot, confirming DP-CATALOG-001 clears. NOT possible yet this session** — the deployed
      Cloud Run Job image (`…/instruments-service:latest`, digest confirmed unchanged, built 2026-08-05T11:24:03 from a
      DIFFERENT commit `04ce8cd`) has not picked up `497c4f5e`: a manual `gcloud run jobs execute --wait` re-run at
      07:42 UTC hit the byte-identical pre-fix traceback (same line numbers, no `try/except` in the stack), proving the
      running container is still the OLD image. The fix reaches the image only once it lands on `main` — LDR→main
      promotion PR **instruments-service#1084** (`promote/instruments-service/497c4f5e824d`) is open and progressing
      normally (`sit-gate/fleet-green` PASS, `quality-gates-v2` PASS, `semver-agent/label-check` PASS; the
      `validate / GCP Cloud Build` image-build-gate check was still QUEUED as of 08:06 UTC) — once that check passes the
      PR auto-merges (`*/15` fleet cadence), Cloud Build rebuilds `:latest`, and the next
      `lifecycle-catalogue-regen-sports` execution (scheduled `0 1 * * *` UTC, or a fresh manual trigger) will run the
      fixed code. **STALE CITATION (found 2026-08-07): PR #1084 is now CLOSED, mergedAt=null** — superseded by a chain
      of later same-title "chore(promote): LDR -> main (Option-B direct)" PRs (#1085-#1092, all closed unmerged); the
      current live promote PR is **#1093** (opened 2026-08-06T22:10:44Z, head 8985daedf532, OPEN/mergeable as of
      2026-08-07). Don't chase #1084 — check the CURRENT open LDR→main promote PR via
      `gh pr list --repo <org>/instruments-service --search "promote"` (the number will likely have moved again by
      execution time), then re-trigger the job once it merges. (repo: instruments-service, verification only — blocked
      on the standard promotion pipeline, not a new problem)~~
- [x] ✅ DONE 2026-08-16 (slot-23) — root cause was in **instruments-service**, not MTDS (this todo's own "most likely
      MTDS" guess was wrong — noting the correction since it would have misled the next grep). Traced to
      `instruments_service/reference_data/adapters/sports/adapters/base.py`'s shared `_get_with_retry()` (used by every
      api_football `fixture_lineups`/`fixtures_schedule`/`teams` fetch) and `api_football.py`'s own `/status` call: both
      called aiohttp's `resp.json(content_type=None)` with no `encoding=` override. Without one, aiohttp's
      `ClientResponse.json()` falls back to statistical charset detection whenever Content-Type doesn't literally say
      `application/json` — exactly what api-football.com's responses don't reliably send — and the detector
      occasionally misidentifies a UTF-8 multi-byte sequence (Polish "Jeleń" → bytes `C5 84`) as Latin-1/cp1252,
      producing the exact `"JeleÅ\x84"` mojibake from the live incident. Fixed by pinning `encoding="utf-8"` (RFC 8259:
      JSON is always UTF-8) at all 5 `resp.json(content_type=None)` call sites in the sports adapters directory (the 2
      api_football sites, plus the identical anti-pattern found in the adjacent `transfermarkt.py` adapter, 3 sites) —
      instruments-service@5f2f3ca619, regression test `test_utf8_name_survives_missing_charset_content_type` reproduces
      the exact incident byte pattern, full `quality-gates.sh` green (335s). Not independently re-verified against a fresh
      live blob sample — the fix needs to reach `main` and the running container needs a fresh image before any NEW
      capture reflects it (same promotion-lag caveat this doc's own P1/P2 history already hit); re-running that full
      cycle is out of scope for this P3 follow-up. The corrupted historical rows are isolated to a re-fetchable window
      (api_football serves the same day/league data on request, not a one-time-only capture), so the routine sports
      catalogue regen cadence will naturally correct them once the fix deploys — satisfying this todo's "OR isolated to
      a re-captureable window with a stated plan" bar. Mirrors `sports_satellite_ao_dispatch_batch10_2026_08_06.md`
      todo 1 (same fix, same evidence — flipped there too, same session). Broader non-sports fleet exposure to the same
      `resp.json(content_type=None)`-without-`encoding=` anti-pattern is out of this doc's scope — filed as
      `aiohttp_json_charset_guessing_audit_2026_08_16.md`. Every todo in this doc is now resolved; archived this same
      session.

## Progress Log

- **slot-4 (data_pipeline_failure escalation agt-941c20) 2026-08-06**: Filed while responding to a CRITICAL
  `DP_CATALOG_NOT_RUNNING` page for sports. Root-caused via live `gcloud run jobs executions list` +
  `gcloud logging read` (full traceback, not a guess) to an uncaught `JunkSymbolError` from a mojibake player name
  crashing the entire ~99k-blob FTP rollup — a new, distinct failure mode from the two previously-fixed sports catalogue
  incidents (2026-07-15 shrink-block, unrelated to this repo's defi R3-migration incident). Fixed with per-row shard
  isolation (try/except + skip + count + log) in `build_sports_fixture_team_player_catalogue`, added a regression test
  reproducing the exact live incident string, ran full `quality-gates.sh --no-fix` green, shipped via quickmerge
  (`instruments-service@497c4f5e`, verified ancestor of `origin/live-defi-rollout`). Manually triggered a fresh
  `lifecycle-catalogue-regen-sports` execution to confirm the fix live — it FAILED again with the byte-identical pre-fix
  traceback, which on inspection proves the deployed `:latest` Cloud Run image is still the OLD build
  (`gcloud artifacts docker images list` shows `:latest` last updated 2026-08-05T11:24:03 from commit `04ce8cd`, not
  today's `497c4f5e`) — the fix is correct and shipped to `live-defi-rollout` but has not reached the running container
  yet. Confirmed this is the normal pipeline, not a stall: LDR→main promotion PR `instruments-service#1084` is open and
  green on every gate checked so far (`sit-gate/fleet-green`, `quality-gates-v2`, `semver-agent/label-check`), with only
  the `GCP Cloud Build` image-build-gate check still queued — once it merges (auto-merge fleet cadence) and Cloud Build
  rebuilds `:latest`, the next job execution will pick up the fix. Left the P2 verification todo open with this exact
  status rather than falsely closing it. Did NOT chase down the upstream encoding-defect root cause (filed as a P3
  follow-up todo) — out of scope for a bounded one-shot page response; the crash-isolation fix is itself a full
  root-cause fix for the ALERT (DP-CATALOG-001), not a mask, since the corrupted name is still correctly rejected from
  the catalogue, just no longer fatal to the whole job. Pinging `dp-fleet-monitor` (authoring slot) with this outcome
  and completing this one-shot escalation.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — added
  `/codex/04-architecture/shard-level-failure-isolation.md` (already cited in `related:`; the fix IS an application of
  this exact codex discipline to a new per-row call site, so it belongs in the reading list, not just the sidebar link);
  dropped `defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md` (only cited contrastively — "a structurally
  different failure mode from" — not a resource this doc's own follow-up work needs) to stay minimal; the other 3
  pre-existing entries re-verified to resolve on disk and kept.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 2 open items: 1 dependency-blocked, 1 lower-confidence
  AO-eligible candidate not yet promoted.
- **na-eligibility-audit 2026-08-07**: RECLASSIFY (sports tranche) — both remaining open items are bounded,
  deterministic-outcome verification/diagnose-and-fix work simply defaulted to `assigned_vm: NA` by the one-shot
  escalation responder, not a deliberate human-gate. Live re-verification (2026-08-07) confirmed the P2 verify-item is
  still genuinely open (commit `497c4f5e` still not on `main`) but its PR #1084 citation is now stale/closed — corrected
  above (current live promote PR is #1093). Added `market-tick-data-service` to `repos:` since the P3 item names it as
  the likely target. Conflict-check cleared: grepped every active `assigned_vm: planning` doc in
  `parent_epic: instruments_master` (6 docs) for
  DP-CATALOG-001/lifecycle-catalogue-regen-sports/mojibake/JunkSymbolError — 0 hits;
  `sports_consolidated_closeout_2026_07_19.md` has zero overlap (grepped directly). Flipped
  `assigned_vm: NA -> planning`, `execution_scope: local-only -> orchestrator-agent`. Issue doc under
  `plans/active/issues/` — exempt from the finalize-plan-coverage rule, no companion finalize doc needed.
- **resolve-round5-sports 2026-08-08**: RESOLVED — closed the `[OPS] P2` verification todo with fresh live evidence
  (catalogue mtime advanced to 2026-08-08T08:16:12Z, past the frozen snapshot; instruments-service `main` HEAD
  `d89b9cb193` confirmed to carry the fix by content). This also independently resolves round-5 sports item 12 (the
  instruments-service LDR→main provenance-range judgment call blocking this fix from reaching main) — the fix reached
  `main` via the normal promotion pipeline without needing the operator bulk-bless/gate-patch judgment call described in
  `instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md`'s remaining open todo; that doc's own
  broader ~19-foreign-commit provenance-range question (a `ci` tranche concern, not sports-specific) remains genuinely
  open and is left untouched here.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **slot-23 (data_engineering) 2026-08-16**: Closed the final open P3 todo — traced + fixed the upstream mojibake
  encoding defect (instruments-service@5f2f3ca619, see todo above for full evidence). Every todo in this doc is now
  `[x]`, unlocked, no dependents blocking — archiving to `plans/archive/2026_08/issues/` in a follow-up commit per the
  6-step archival ritual. Also flipped the duplicate-tracking todo 1 in
  `sports_satellite_ao_dispatch_batch10_2026_08_06.md` (same fix) and fixed its `related:` path to point at the new
  archive location. Filed `aiohttp_json_charset_guessing_audit_2026_08_16.md` for the out-of-scope fleet-wide follow-up
  (auditing non-sports aiohttp adapters for the same anti-pattern).
