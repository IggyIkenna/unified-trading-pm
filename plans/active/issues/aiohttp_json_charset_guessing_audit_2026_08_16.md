---
doc_type: issue
title: >-
  Audit non-sports aiohttp adapters for the resp.json(content_type=None)-without-encoding charset-guessing anti-pattern
summary: >-
  DP-CATALOG-001 follow-up (2026-08-16, slot-23): root-caused the 2026-08-06 sports catalogue mojibake crash
  ("JeleÅ\x84" for "Jeleń") to aiohttp's ClientResponse.json() falling back to statistical charset detection whenever a
  response's Content-Type doesn't literally say "application/json" — exactly what api-football.com's responses don't
  reliably send. Fixed the 5 call sites in instruments-service's sports adapters (base.py, api_football.py,
  transfermarkt.py) by pinning encoding="utf-8" (RFC 8259: JSON is always UTF-8). That fix is scoped to sports; the same
  `resp.json(content_type=None)` anti-pattern was not swept across the rest of the fleet (cefi/defi/tradfi/prediction
  adapters in instruments-service, or any aiohttp-based adapter in market-tick-data-service) — any of those hitting a
  vendor that also omits an explicit application/json charset carries the identical latent mojibake risk. Filed as a
  bounded, deterministic follow-up rather than folding into the (now-archived) sports-scoped source doc.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [aiohttp, json, encoding, charset, mojibake, dp-catalog-001, follow-up]
related:
  [
    /plans/archive/2026_08/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: "sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md follow-up, slot-23, 2026-08-16"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    instruments_service/reference_data/adapters/sports/adapters/base.py,
    instruments_service/reference_data/adapters/sports/adapters/api_football.py,
    /plans/archive/2026_08/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
  ]
---

# aiohttp resp.json(content_type=None) charset-guessing audit

## What I found

Fixing DP-CATALOG-001's mojibake root cause (instruments-service@5f2f3ca619) confirmed the exact mechanism: aiohttp's
`ClientResponse.json()` only defaults to UTF-8 when the response's Content-Type mimetype is literally
`application/json`/`application/rdap+json`; for anything else (a vendor that omits charset, or sends a non-JSON
Content-Type on a JSON body) it falls back to statistical charset detection over the raw bytes, which can misidentify a
UTF-8 multi-byte sequence as Latin-1/cp1252. `content_type=None` (used to skip aiohttp's strict Content-Type assertion)
does NOT fix this — it only suppresses the assertion, not the encoding guess.

The fix (pin `encoding="utf-8"`, since JSON is always UTF-8 per RFC 8259) was applied only to the 5 call sites found in
`instruments-service/instruments_service/reference_data/adapters/sports/adapters/{base,api_football,transfermarkt}.py`.
No sweep was done of:
- Other instruments-service adapter families (cefi/, defi/, tradfi/, prediction/) for the same
  `resp.json(content_type=None)` shape.
- market-tick-data-service's aiohttp-based adapters/connectors.

## Why it matters

Any adapter hitting a vendor whose responses don't reliably declare `application/json` carries the same latent
mojibake risk — silent, since a mis-decoded string parses as valid JSON and only surfaces later (e.g. via a downstream
validator like `_reject_junk_symbols`, or not at all if nothing validates the field).

## Recommended decision

Grep both repos for `\.json\(content_type=None\)` (or `\.json\(\s*content_type=None` allowing line breaks), check each
hit for a missing `encoding=` kwarg, and pin `encoding="utf-8"` on any that lack it — mirroring the sports fix exactly.
Consider whether a QG check is warranted (the existing "No raw response.json()" check at
`scripts/quality-gates-base/base-service.sh` enforces a different, unrelated convention — parse-through-Pydantic — and
does not cover this encoding gap) once the sweep shows how many repos/call-sites are actually affected.

## Todos

- [ ] [DATA] P3. Grep instruments-service (cefi/defi/tradfi/prediction adapter families) and market-tick-data-service
      for `resp.json(content_type=None)` (or equivalent `aiohttp` response-json calls) missing an explicit
      `encoding="utf-8"`; pin it on every hit found, mirroring instruments-service@5f2f3ca619. Done when: every
      `content_type=None` JSON-decode call site across both repos either already pins `encoding="utf-8"` or has been
      fixed to do so, and `quality-gates.sh` is green in each touched repo. (repos: instruments-service,
      market-tick-data-service)

## Progress Log

- **slot-23 (data_engineering) 2026-08-16**: Filed while closing out
  `sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md`'s P3 todo — the sports-scoped fix is shipped
  (instruments-service@5f2f3ca619), this doc tracks the deliberately out-of-scope fleet-wide sweep for the same
  anti-pattern.

- **slot-29 (data_engineering) 2026-08-16**: Worked the todo's market-tick-data-service half. Grepped the repo for
  `\.json\(content_type=None` and found 5 call sites missing `encoding=`:
  `market_interface/adapters/sports/sportradar_adapter.py`, `market_interface/adapters/tradfi/{ecb_adapter,
  ofr_adapter}.py`, `cli/handlers/solana_defi_amm.py` (3 sites), `cli/handlers/_solana_defi_fetch.py` (1 site). Pinned
  `encoding="utf-8"` on all 5, mirroring the sports fix exactly. `quality-gates.sh` PASSED (613s; full pytest suite
  10912 passed / 0 failed / 28 skipped / 1 xpassed). Committed locally as `market-tick-data-service@7ffa995c`; shipping
  via `quickmerge.sh` was still in flight at session end (re-gating after a peer's HEAD move on
  `live-defi-rollout`, queued behind the host-wide QG governor) — **not yet confirmed pushed to origin**, so the todo
  checkbox below is deliberately left unflipped. Also checked instruments-service's side of this todo: all 5 of its
  `resp.json(content_type=None)` sites (the original sports fix) already pin `encoding="utf-8"`, and a full-repo grep
  found no other call sites in cefi/defi/tradfi/prediction adapter families — **instruments-service's side is already
  fully done**, so once `7ffa995c` lands on origin this todo is fully closeable across both repos, not partial. Next
  session: confirm `market-tick-data-service@7ffa995c` (or its post-rebase SHA) is on `origin/live-defi-rollout`
  (`git fetch && git rev-list --count origin/live-defi-rollout..HEAD` = 0), then flip the todo to `- [x] ✅` with that
  SHA as evidence — no further code changes needed.

- **slot-29 (data_engineering) 2026-08-16, pre-compact checkpoint**: `market-tick-data-service@7ffa995c` still
  unpushed — `ahead=1 behind=1` vs `origin/live-defi-rollout` (my commit not yet on origin; a peer commit landed on
  origin after my last rebase). The shipping `quickmerge.sh` run (background task) is genuinely still in progress, not
  stalled: it hit a second sentinel invalidation ("HEAD moved — a peer likely pushed"), auto-re-gated, and is now
  queued 720s+ in the host-wide QG governor (`sub-cap 1 / host-wide cap 6`) — confirmed via `ps aux` that 6+ concurrent
  `quality-gates.sh` processes are running across other slots (17/18/19/33) right now, i.e. real host contention, not a
  hung process. Left it running rather than killing/retrying — killing a queued-but-live governor client only makes
  contention worse for everyone. Verified the other 4 repos this session cascaded into (`unified-trading-pm`,
  `deployment-service`, `unified-api-contracts`, `unified-trading-library`) are all `ahead=0` (fully pushed, nothing at
  risk); `deployment-service@1d78d15c` (vm-launcher e2-highmem-16 fix) in particular was already confirmed durable, not
  something this checkpoint needed to act on. Scratchpad's 6 `qg_mtds*.log` files are disposable QG debug output from
  earlier attempts (the largest, `qg_mtds6.log`, stopped updating at 03:18:56Z with no live PID behind it — an
  abandoned standalone debug run, superseded by the quickmerge job's own internal QG pass); none are referenced by any
  committed doc. **Lesson for next session**: a `[qg-governor] queued Ns` line climbing past 10 minutes under confirmed
  multi-slot contention is still not a failure signal — only a terminal exit code (or the task notification) is;
  resist the urge to kill and restart, since a restart re-enters the same queue from zero. Next session (or this one on
  wake): check the task notification/final output for `✅ Pushed <sha>` vs `QUICKMERGE_BLOCKED`; if pushed, verify
  `rev-list --count origin/live-defi-rollout..HEAD` = 0 for market-tick-data-service, then flip the todo below with the
  landed SHA.
