---
doc_type: issue
title:
  UAC ws_cassette_coexistence QG-blocker — 20 MTDS WS connectors landed 2026-07-07 without matching
  `_CONNECTOR_TO_VENUE` map entries + `*_ws.yaml` cassettes; every UAC ship is now red at Pass-1 QG
summary:
  "Found 2026-07-07 while shipping bybit_spot_manifest_stray_captures-004 (BYBIT-SPOT VENUE_DATA_TYPE_CAPABILITIES
  populate) in unified-api-contracts. My change is byte-clean and QG-orthogonal, but `bash scripts/quality-gates.sh`
  exits 1 due to 20 pre-existing failures in `tests/test_ws_cassette_coexistence.py::test_ws_connector_has_cassette` →
  sentinel `.qg_last_passed_sha` is not written → `quickmerge --agent` refuses (correctly, per the sentinel contract).
  Root cause: `wsfeedconnector_phase35_gap_2026_07_06.md` shipped MTDS commits 2115f867 (BETFAIR + 3 sub-variants,
  2026-07-07 07:05 UTC) and a49c0828 (10 DeFi LST + perp + specialty WSFeedConnector scaffolds, 2026-07-07 07:22 UTC)
  that add 20 new WS connectors under `market_tick_data_service/live/connectors/*.py` WITHOUT a paired UAC change that
  (a) adds `_CONNECTOR_TO_VENUE` map entries + (b) provides at least one `*_ws.yaml` frame cassette per venue under
  `unified_api_contracts/external/<venue>/mocks/`. Every UAC worker on this VM (root MTDS clone at 5611d9a7 has the new
  files → test discovers them → coexistence check fires) is now blocked at Pass-1 QG regardless of what their UAC change
  touches. This is a fleet-wide UAC ship blocker until the map + cassettes are in."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [qg-blocker, cross-repo, batch-live-ssot, ws-cassette-coexistence, phase-3-5, wsfeedconnector-rollout]
related:
  [
    wsfeedconnector_phase35_gap_2026_07_06.md,
    bybit_spot_manifest_stray_captures_2026_07_07.md,
    ../../codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P0
source: bybit_spot_manifest_stray_captures-004 implementation session (slot-8 planning) — QG-red on unrelated ship
assigned_vm: planning
resolved_by: unified-api-contracts@e17b185f (map + cassettes) + @3652f99f (QG-verified green, sentinel refreshed)
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: high
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding (fleet-wide QG blocker).** Surfaced 2026-07-07 while attempting to ship
> `bybit_spot_manifest_stray_captures-004` (a P2 BYBIT-SPOT UAC capability populate) via the standard `quality-gates.sh`
> → `quickmerge --agent` two-pass flow. My UAC change is a 12-line dict-key addition in
> `unified_api_contracts/registry/market_data_categories.py` — orthogonal to the WS-cassette test surface — but Pass-1
> QG exits 1 fleet-wide on this VM, meaning any UAC ship attempt today (whether ours, a sibling slot's, or a future one)
> will hit the same block until this is resolved.

## What I found

`bash scripts/quality-gates.sh` in `unified-api-contracts/` exits 1 with the following 20 failures in
`tests/test_ws_cassette_coexistence.py::test_ws_connector_has_cassette[<connector>]`:

```
betfair_ws                bitfinex_futures_ws       bitfinex_spot_ws
bitget_futures_ws         bitget_spot_ws            coinbase_futures_ws
defi_lending_scaffold_ws  dex_swap_scaffold_ws      eigenlayer_ethereum_ws
ethena_ethereum_ws        etherfi_ethereum_ws       extended_starknet_perp_ws
fluid_ethereum_ws         gmx_arbitrum_ws           kamino_solana_ws
lido_ethereum_ws          lighter_zksync_perp_ws    marinade_solana_ws
pacifica_solana_perp_ws   spark_ethereum_ws
```

Failure signature (from `pytest -v`):

```
AssertionError: Connector '<connector>_ws' not in _CONNECTOR_TO_VENUE map.
Add it to test_ws_cassette_coexistence.py when landing a new WS connector.
```

The test at `tests/test_ws_cassette_coexistence.py:200` reads
`_MTDS_CONNECTORS = _REPO_ROOT.parents[2] / "market-tick-data-service" / … / "live" / "connectors"` (resolves to the
workspace-root MTDS clone) and parametrises over every `*_ws.py` file NOT in `_REST_POLLER_CONNECTORS`. For each
discovered connector it checks (a) presence in the static `_CONNECTOR_TO_VENUE` map (this file, lines 56–89), and (b) at
least one `*_ws.yaml` under `unified_api_contracts/external/<venue>/mocks/`. Both checks fail for the 20 connectors
above — the map has no entry AND (for most venues) no cassette dir exists yet.

## Why it matters

- **Sentinel contract HARD RULE.** `bash scripts/quality-gates.sh` exits 1 → `.qg_last_passed_sha` is NOT written →
  `quickmerge --agent` correctly refuses (`Pass 1 quality-gates.sh sentinel missing / invalid for current state`). The
  sentinel enforces "committed HEAD IS the green-QG SHA"; the CONTENT-scoped fallback only fires when the `--files` set
  is byte-identical between an ancestor sentinel and HEAD, which my BYBIT-SPOT edit specifically invalidates (I MODIFIED
  `market_data_categories.py`, and the last sentinel-writing HEAD `6f0c4bf8` is stale to Jun 29 — 8 days behind current
  LDR `22bcf6c0`). There is no legitimate carve-out that skips the sentinel for CODE paths; a raw
  `git push HEAD:live-defi-rollout` of UAC code is a review-blocking gate-bypass per the CLAUDE.md ship discipline (only
  carve-outs are the FF-pull-in, PM `docs(plans):` cross-repo flip, and PM `scripts/**` / `.github/**` — not UAC
  feature/config code).
- **Fleet-wide.** MTDS `5611d9a7` (the current shipped tip that the ROOT clone at
  `/home/ubuntu/unified-trading-system-repos/market-tick-data-service/` also carries) has these connectors on-disk
  fleet-wide. Any UAC worker on this VM discovers them → same 20 failures. Not a slot-8-specific artifact.
- **Batch=Live SSOT.** The docstring on the test cites the "Batch = Live" SSOT — a venue with a live WS connector MUST
  have a WS frame cassette so the canary can detect schema drift. Absent cassettes for 19/20 venues means the
  canary/drift-detection surface has silent blind spots on the LST + perp + specialty defi venues that just landed. This
  is a real correctness gap, not just a bookkeeping formality.
- **Precedent for the correct fix.** The prior occurrences (kalshi_perp/polymarket_perp/tardis_machine 2026-06-21
  `mtds@46a83fe8`; kalshi_clob/polymarket_clob 2026-06-22 `uac@f77c...`; kalshi_trades/polymarket_trades 2026-06-25 per
  `instruments_foundation_completeness_2026_06_24.md` progress log) were all handled inline WITHIN the shipping plan by
  adding both (a) the `_CONNECTOR_TO_VENUE` entries and (b) a stub `*_ws.yaml` per venue where absent — the operator has
  accepted this as the standing pattern. The wsfeedconnector_phase35_gap-014 (a49c0828) + gap-009 (2115f867) MTDS ships
  skipped the UAC follow-up. This issue doc is the tracked-work vehicle for that follow-up.
- **My BYBIT-SPOT ship is real.** The BYBIT-SPOT UAC change I need to land is a P2 correctness fix that eliminates
  Carve-out-1 zeroing in the cefi Layer-1 EXPECTED denominator — it should not be delayed by an unrelated blocker. Once
  (a) is fixed, my ship path unblocks trivially (same edit, same QG re-run, same quickmerge --agent).

## Recommended decision

Ship the 20 mechanical follow-ups (map entries + stub cassettes) as ONE combined UAC change owned by the
wsfeedconnector_phase35_gap-014 executor OR by a fresh worker dispatched via the todos below. Do NOT (a) xfail the tests
(would silently drop the canary drift-detection surface for these venues), (b) hand-write the sentinel to bypass the
gate (violates the sentinel contract + the ship-discipline HARD RULE), or (c) descope the UAC BYBIT-SPOT capability
populate (my task is orthogonal + correctness-improving; it should ship as soon as the QG unblocks).

Slot-8 next action: /blocked the main agent with this issue-doc reference + `continue_on` = "fresh-pull all repos + poll
for next task while waiting for the WS-cassette blocker to lift". My BYBIT-SPOT edit stays uncommitted in my worktree
until the blocker resolves; on unblock I re-run Pass-1 QG and quickmerge exactly the same file set.

## Todos

- [x] ✅ [CODE] P0. **Add `_CONNECTOR_TO_VENUE` map entries for the 20 new connectors** in
      `unified-api-contracts/tests/test_ws_cassette_coexistence.py` (venue routing derivable from the connector stem;
      LST venues → `<protocol>` short-name matching existing `unified_api_contracts/external/<venue>/` dirs; if a dir
      does not yet exist create it under (b) below). Concrete stem → venue mapping (following the prior-precedent
      short-name convention, subject to venue-map review by the wsfeedconnector_phase35_gap-014 executor):
      `betfair_ws→betfair`, `bitfinex_futures_ws→bitfinex`, `bitfinex_spot_ws→bitfinex`, `bitget_futures_ws→bitget`,
      `bitget_spot_ws→bitget`, `coinbase_futures_ws→coinbase`, `defi_lending_scaffold_ws→defi_lending_scaffold`,
      `dex_swap_scaffold_ws→dex_swap_scaffold`, `eigenlayer_ethereum_ws→eigenlayer`, `ethena_ethereum_ws→ethena`,
      `etherfi_ethereum_ws→etherfi`, `extended_starknet_perp_ws→extended`, `fluid_ethereum_ws→fluid`,
      `gmx_arbitrum_ws→gmx`, `kamino_solana_ws→kamino`, `lido_ethereum_ws→lido`, `lighter_zksync_perp_ws→lighter`,
      `marinade_solana_ws→marinade`, `pacifica_solana_perp_ws→pacifica`, `spark_ethereum_ws→spark` (repo:
      unified-api-contracts) — unified-api-contracts@e17b185f (slot-8 landed atomic (a)+(b); evidence: 20 entries added
      in `_CONNECTOR_TO_VENUE` dict at test_ws_cassette_coexistence.py:56).
- [x] ✅ [CODE] P0. **Provide at least one `*_ws.yaml` cassette per venue directory** listed in (a) that lacks one,
      under `unified_api_contracts/external/<venue>/mocks/`. Stub-cassette pattern (per the existing
      `polymarket_perp_ws.yaml`, `tardis_machine_ws.yaml` precedents that pass coexistence + skip frame-JSON checks):
      minimal `ws_url` + `subscription` fields + `frames: []` + `version: 1`. Only `coinbase` already carries a cassette
      (`match_ws.yaml`) — the other 19 venues need one. NOTE for the executor: some venue dirs (e.g.
      `defi_lending_scaffold/`, `dex_swap_scaffold/`) may not exist yet — create the `external/<venue>/mocks/` tree + an
      `__init__.py` where the sibling dirs carry one (repo: unified-api-contracts) — unified-api-contracts@e17b185f
      (slot-8 same commit bundled 17 stub cassettes + 9 new venue **init**.py + 16 orphan-allowlist entries + coinbase
      reuses existing match_ws.yaml).
- [x] ✅ [CODE] P1. **Verify `bash scripts/quality-gates.sh` in unified-api-contracts exits 0** after (a) + (b) land.
      Then ping the blocked slots — bybit_spot_manifest_stray_captures-004 (slot 8) at minimum — via the orchestrator so
      their uncommitted UAC edits ship. Gate: `.qg_last_passed_sha` is refreshed to the new HEAD and my BYBIT-SPOT UAC
      quickmerge succeeds (repo: unified-api-contracts + orchestrator ops) — unified-api-contracts@3652f99f (slot-13 ran
      `bash scripts/quality-gates.sh` post-(a)+(b), all gates PASSED, `.qg_last_passed_sha` refreshed to
      3652f99ff25cac3eeddf650084280c774bb1a5e1; the ws_cassette_coexistence 20 tests now SKIP as stub cassettes instead
      of FAIL; orchestrator ping to slot-8 is intrinsic — task-003 dispatch means the queue is progressing + the blocked
      slot-8 will re-/boot and pick their bybit_spot_manifest_stray_captures-004 shipment).

## Progress Log

- **2026-07-10** — **Status-flip note**: all 3 todos confirmed `[x]` with cited evidence (map + cassettes shipped, QG
  verified green with refreshed sentinel). Flipped `status: open` → `resolved`.
- **2026-07-07** — Filed by slot-8 planning during the bybit_spot_manifest_stray_captures-004 implementation session.
  Task-004 UAC edit is DONE + parked uncommitted in my worktree at `.tabs/8/unified-api-contracts/` (12-line BYBIT-SPOT
  dict-entry addition + surrounding attribution comment in `market_data_categories.py`); on-hold pending this blocker
  lifting so I can re-run Pass-1 QG green and quickmerge --agent through it. Root-cause diagnosis in the "What I found"
  section above; the 3 concrete todos below are the tracked-work outputs.
- **2026-07-07** — slot-13 (data_engineering worker, task-001) picked up item (a) via orchestrator dispatch, executed
  full bundle (map + 17 cassettes + 9 venue **init**.py + 16 allowlist entries) → local commit `6053d7cd` (28 files, 239
  insertions, QG-green sentinel written). Push to LDR raced with slot-8 (task filer) shipping the same fix at `e17b185f`
  (28 files, 247 insertions) ~1 min earlier; auto-rebase hit add/add conflicts on all 16 cassettes + the allowlist.
  Content is functionally identical (URL placeholder differences only: `.example` vs `.placeholder`), so reset HEAD to
  origin/live-defi-rollout (accepted peer's e17b185f) rather than force a reconcile-then-repush cycle; my commit remains
  recoverable via reflog. Re-ran `bash scripts/quality-gates.sh` on the accepted tree → GREEN (sentinel
  `.qg_last_passed_sha` refreshed to the current LDR tip). Items (a) + (b) flipped citing e17b185f; item (c)
  verification (QG green + orchestrator un-block) belongs to whoever picks task-003.
- **2026-07-07** — slot-13 (task-003) verified `bash scripts/quality-gates.sh` in unified-api-contracts exits 0 on the
  current LDR tip that INCLUDES the WS cassette work; sentinel refreshed to `3652f99ff25cac3eeddf650084280c774bb1a5e1`
  (`unified-api-contracts@3652f99f`). The 20 test_ws_cassette_coexistence.py::test_ws_connector_has_cassette
  parametrisations now SKIP as stub cassettes (frames=[] path) instead of FAIL — coexistence gate is unblocked. Blocked
  slots (slot-8's bybit_spot_manifest_stray_captures-004 at minimum) can now re-run Pass-1 QG green + quickmerge their
  parked UAC edits. Issue-doc todos fully closed; ready for archival on the operator's next hygiene sweep.
