---
doc_type: issue
title:
  "sports_live_availability_and_source_latency_2026_07_24.md's open P2 todo asks to wire api_football `/odds` in-play as
  a second live MTDS sports-odds source -- this directly conflicts with the operator's 2026-06-24 ruling + a resolved
  1.26M-row wrong-source data-correctness incident that established api_football has ZERO legitimate business writing
  sports odds/TRADES into MTDS at all"
summary:
  "Picked up infra_capture_and_devops_leftovers-001 (backlog task derived from
  infra_capture_and_devops_leftovers_2026_07_06.md's P2 pointer checkbox, which itself redirects to
  sports_live_availability_and_source_latency_2026_07_24.md's own [DATA] P2 todo as the live tracker). That todo's text
  ('picked a paid sports-odds API quota tier -- proceed with the resume' + 'api_football /odds in-play as the free
  second source') was written 2026-07-24/28/29 without cross-referencing two ALREADY-RESOLVED issue docs from
  2026-07-22/23 in the SAME repo: mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md and its
  root-cause chain. That doc's own evidence: api_football has NO MTDS odds adapter, NO SOURCE_PRIORITY key for sports
  TRADES/odds, and a dedicated wipe script (wipe_api_football_sports_odds_2026_06_24.py) whose docstring states 'every
  source=api_football row in the MTDS sports manifest is odds-like wrong-source data.' The operator ruled 2026-06-24 to
  WIPE EVERYTHING source=api_football from the MTDS sports raw-tick manifest+GCS (1,398,423 rows + 231,532 objects
  deleted); a SOURCE_PRIORITY gap (missing ('sports','TRADES') entry) caused a SECOND accidental 1,266,874-row
  re-accumulation discovered 2026-07-22, root-caused + fixed (uac@44623d25 added ('sports','TRADES'):['odds_api'] -- NOT
  api_football) and re-wiped 2026-07-23 (market-tick-data-service@e9d9dec0). The resolved doc explicitly states:
  'confirmed: api_football has zero legitimate business writing into market-data-tick-sports-prd at all -- its
  sanctioned writes are fixtures/reference data in the instruments-store-sports bucket.' Building a NEW, deliberate
  api_football live-odds MTDS connector (as the P2 todo asks) would be the FIRST legitimate such write path ever -- not
  a re-enable of prior functionality -- but risks recreating the exact wrong-source/mislabeling failure class that
  burned real engineering time twice if not built with extreme care (its own SOURCE_PRIORITY/PipelineMode entry, never
  falling through to a shared fallback). Separately (non-conflicting, independently verified this session): NO live
  sports-odds VM (mtds-live-sports-odds-api-trades or any mtds-live-sports-* instance) is currently running in the GCE
  fleet at all (live gcloud compute instances list --project central-element-323112, 2026-08-02) -- contradicting the
  plan's own coverage-matrix claim of 'LIVE -- coded + RUNNING' for the WS odds_api_ws.py connector. This second finding
  is NOT blocked -- the operator's 2026-07-28 ruling already authorizes resuming it -- and is being worked as
  continue_on while this doc's api_football question is escalated."
status: open
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, unified-api-contracts, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    api-football,
    wrong-source,
    sports,
    mtds,
    odds,
    live-connector,
    data-correctness,
    ssot-contradiction,
    operator-decision,
  ]
related:
  [
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/2026_07/sports_live_availability_and_source_latency_2026_07_24_finalize_2026_07_30.md,
    /plans/archive/2026_08/infra_capture_and_devops_leftovers_2026_07_06.md,
    plans/archive/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md,
    plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md,
  ]
created: 2026-08-02
author: unknown
parent_epic: sports_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: unknown
assigned_vm: planning
execution_scope: orchestrator-agent
source: [infra_capture_and_devops_leftovers-001 backlog task, slot 3, 2026-08-02]
resolved_by:
locked_by:
depends_on: []
last_updated: 2026-08-02
context_scope:
  [
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_core.py,
    instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football.py,
  ]
---

## Why this is a big finding, not routine triage

Per CLAUDE.md's findings-triage rule: "big finding (data-correctness / cross-repo / SSOT contradiction) → NOTIFY
OPERATOR + issue doc." This is exactly that class. Silently building the api_football live-odds connector because a
2026-07-24-authored plan says to, without accounting for the 2026-06-24 operator ruling + the 2026-07-22/23
resolved-incident chain that DIRECTLY concerns the same (asset_group=sports, vendor=api_football, target=MTDS
odds/TRADES) surface, risks a THIRD occurrence of the exact wrong-source pollution class that already cost real
engineering time twice (2026-06-24 wipe, 2026-07-23 re-wipe). Conversely, silently refusing/skipping the todo because of
a keyword match without confirming applicability would leave a legitimate, operator-intended second-source todo stuck.
Escalating for an explicit ruling is correct per the HARD RULE.

## What I found (evidence)

1. **Task derivation chain**: `infra_capture_and_devops_leftovers-001` (this session's assigned backlog task) →
   `infra_capture_and_devops_leftovers_2026_07_06.md`'s `[DATA] P2` checkbox (still `[ ]` by design — its own text says
   the sibling plan is the live tracker, not itself) → `sports_live_availability_and_source_latency_2026_07_24.md`'s
   `[DATA] P2` todo (still `[ ]`), whose "Done when" reads: _"the api_football `/odds` in-play second source is wired as
   a fallback/supplement, and the live sports-odds ingestion is confirmed resumed (a fresh poll cycle succeeding against
   the live key in production, not just a direct-API-call verification)."_
2. **The conflicting ruling**:
   `plans/archive/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md` (status: resolved)
   documents: api_football's ONLY sanctioned writes are reference data in `instruments-store-sports-prd`
   (fixtures/teams/standings/etc. via the existing `ApiFootballAdapter` in instruments-service). It has **no MTDS odds
   adapter and no `SOURCE_PRIORITY` entry** for any sports odds/TRADES data_type.
   `market_tick_data_service/scripts/wipe_api_football_sports_odds_2026_06_24.py`'s own docstring: _"api_football is NOT
   a sanctioned bookmaker-odds source for MTDS ... every source=api_football row in the MTDS sports manifest is
   odds-like wrong-source data."_ Also confirmed live this session:
   `instruments_service/reference_data/adapters/sports/adapters/api_football.py::get_odds()` is a literal stub — _"API
   Football does not provide odds data. This adapter is for reference data only. Returns an empty list."_
3. **Incident timeline**: 2026-06-24 operator-ruled wipe of ALL `source=api_football` rows from the MTDS sports raw-tick
   manifest+GCS (1,398,423 rows + 231,532 objects). A missing `("sports","TRADES")` `SOURCE_PRIORITY` entry then caused
   the sentinel fan-out to silently fall through to `_ASSET_GROUP_FALLBACKS["sports"] = PipelineMode.BATCH_API_FOOTBALL`
   for every sports TRADES row, re-accumulating 1,266,874 mislabeled rows over ~3 weeks (found 2026-07-22).
   Root-caused + fixed `unified-api-contracts@44623d25` (added `("sports","TRADES"):["odds_api"]` — **not**
   api_football) and re-wiped CAS-safe via `market-tick-data-service@e9d9dec0` (2026-07-23,
   `scripts/sports/wipe_api_football_sports_manifest_2026_07_23.py`).
4. **The sibling plan's todo was authored 2026-07-24** (2 days after the wrong-source finding, 1 day after the re-wipe)
   and **does not reference either issue doc** — reads as independently derived from the earlier coverage-matrix
   research (the "cheap second source, already-subscribed key" framing), not as a deliberate override of the wipe
   ruling.
5. **Separate, non-conflicting finding**: live `gcloud compute instances list --project central-element-323112`
   (2026-08-02, this session) shows **zero** `mtds-live-sports-*` instances running anywhere in the fleet — the plan's
   own coverage-matrix table claims `odds_horizon_bucket`/`LIVE_ODDS` is "LIVE — coded + RUNNING ... running VM
   `mtds-live-sports-odds-api-trades`," which is stale as of today. No `mtds-live-sports-*` VM_PREFIX launcher dedicated
   wiring was found either — the generic
   `deployment-service/scripts/vm/launch-mtds-live.sh --asset-group sports --shard-spec sports:ODDS_API:trades`
   invocation is the documented pattern (mirrors the ASTER example in
   `infra_capture_and_devops_leftovers_2026_07_06.md`), and `mtds-live-sports-` is a registered `VmPrefixSpec`
   (`deployment_service/vm_prefix_registry.py`, `LONG_LIVED_LIVE`). This part of the "Done when" bar is NOT gated on the
   api_football question and is being worked separately (see Progress Log).

## Recommended decision

Two options for the api_football half specifically:

- **A. Proceed, carefully** — build `api_football_odds_ws.py` (MTDS live connector for api-football's `/odds/live`
  in-play endpoint) as a genuinely NEW, deliberate write path, with its OWN `SOURCE_PRIORITY` entry (e.g.
  `("sports","ODDS_IN_PLAY"):["api_football"]`) and
  `PipelineMode.LIVE_API_FOOTBALL`/`SOURCE_MODE_CAPABILITY["api_football"]` flip to include `Mode.LIVE` — so it can
  never fall through to the old ambiguous-fallback failure mode. This treats the 2026-06-24 ruling as "wipe the
  accidental mislabeled data," not "api_football is permanently forbidden from ever legitimately writing sports odds."
  Requires an explicit operator sign-off given the history.
- **B. Decline** — treat the sibling plan's todo as based on incomplete information (written without the wipe/incident
  context) and correct it: strike the api_football half, keep only the primary `odds_api` live-resume half (which this
  session is already executing, unblocked). File a plan-hygiene note in the sibling plan explaining why.

**My recommendation: B**, unless the operator has a specific reason to want api_football odds coverage despite the
history — the "free/no extra cost" framing that motivated the original todo is a weak justification against a
documented, twice-burned data-correctness risk, and the primary `odds_api` source already covers the
LIVE_ODDS/odds_horizon_bucket gate this todo exists to close.

## Resolution (2026-08-10, prose-findings formalization sweep)

**Both open questions from this doc are already resolved — no todo needed, both were already actioned via the
`/blocked` escalation mechanism this doc itself started.**

1. **Recommended decision → RULED, option B (decline).** `BLK-b969f5f0` was answered "decision B" — confirmed via the
   sibling tracker doc's own record: `plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md`
   states (line 169) "**api_football `/odds` in-play second-source half STRUCK 2026-08-02 (`BLK-b969f5f0`, main,
   decision B) — SUPERSEDED, not pursued**" and (line 415) "recommendation B (strike the api_football half as based on
   incomplete information)." The sibling plan's P2 todo was corrected accordingly — a genuine second live-odds source
   is now explicitly scoped as "its OWN new operator-gated design decision if ever wanted," not folded back into that
   todo. Matches this doc's own recommendation exactly.
2. **The separate, non-conflicting finding (live sports-odds VM not running) → RESOLVED 2026-08-03.** Same sibling
   tracker doc, its coverage-matrix row for LIVE_ODDS/odds_horizon_bucket: "**LIVE — RUNNING**
   (`mtds-live-sports-odds-api-trades-20260803-172841`, verified 2026-08-03: 35+ min of clean `run.log`, zero
   errors/401s...)" — "RESOLVED 2026-08-03: the 2026-08-02 quota-exhaustion finding is closed... the live VM is
   confirmed healthy, not just started."

No content in this doc needs a fresh todo; `status`/`assigned_vm` left untouched per this sweep's scope (a
close-out/archival pass, not this formalization pass, is the right place to flip `status: open` → `resolved`).

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-08-10 (prose-findings formalization sweep)**: converted 0 prose findings into todos (0 new todos needed) — both
  of this doc's open questions (the A/B recommendation, and the separate live-VM finding) were already resolved via the
  `/blocked` mechanism this doc itself started; cited the evidence directly in a new "Resolution (2026-08-10)" section
  above rather than adding checkboxes for already-settled questions.
- **2026-08-02** — Filed by slot 3 (data_engineering) while working `infra_capture_and_devops_leftovers-001`. Reverted
  an in-progress UAC edit (`PipelineMode.LIVE_API_FOOTBALL` + `SOURCE_MODE_CAPABILITY["api_football"]` Mode.LIVE flip)
  before committing, once this conflict surfaced — no code shipped, tree clean. Escalating via `/blocked`; continuing on
  the non-conflicting primary `odds_api` live-VM resume in parallel (see
  `/plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md` Progress Log for that thread).
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
