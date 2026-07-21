---
doc_type: issue
title:
  HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT — SSOT contradiction between a P0 registration finding and a same-week removal
  commit
summary:
  "RESOLVED 2026-07-12: operator decided Option B — huobi/bitstamp/htx should be entirely removed, no further
  investigation needed. 181b5311's removal stands as correct; the smoketest P0 finding is closed as stale. Swept for
  remaining references beyond 181b5311's original 4 files: removed a dangling pyproject.toml coverage-exclusion pointing
  at a bitstamp schema module that no longer exists, and 2 stale 'source: huobi'/'source: bitstamp' entries in
  ui-reference-data.json (both the root and openapi/ copies) that were still claiming supports_live/supports_batch
  despite the underlying registry no longer defining them — those two were genuinely still-live remnants, not just
  historical mentions. Left untouched (confirmed out-of-scope, not venue references): the 'HT' token symbol in
  test_cefi_universe_coverage.py's retired-top-100-coin survivorship-bias test (Huobi Token the ASSET, unrelated to
  Huobi the VENUE), docs/schema_health.svg (cosmetic-only diagram, no production consumption, would need a real
  pytest-integration run to regenerate correctly rather than a naive re-run that defaults every OTHER provider's status
  to unverified), and defillama/tardis mock fixtures (unrelated external ground-truth data — DeFiLlama's real protocol
  list and Tardis's real vendor exchange catalog, not our own venue registration). Original problem statement below for
  context: mtds_is_full_adapter_smoketest_findings_2026_07_07.md's P0 list called for registering
  HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT into the CeFi venue universe (claimed real captured data exists, just never
  fetched); one day before this session started, unified-api-contracts@181b5311 (2026-07-09) had deliberately removed
  huobi/bitstamp/htx from venue_mapping.py/provider_api_versions.yaml/venue_tokens.py/instrument_validation.py under the
  opposite reasoning ('never-captured'); neither doc had known of the other."
status: resolved
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [ssot-contradiction, cefi, huobi, bitstamp, htx, venue-registration]
related:
  [
    plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
    plans/active/issues/instruments_remaining_work_audit_2026_07_10.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
source: [P1-P3 headline sweep workflow, smoketest_59bug fix pass, 2026-07-10]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-12
locked_by:
locked_since:
resolved_by: "unified-api-contracts@62e0855c7a0d7823f6807549e97f41280e539a33 — see Resolution section below"
---

# HUOBI/BITSTAMP/HTX — two same-week decisions reached opposite conclusions

## The contradiction

- `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` (filed 2026-07-07, P0 list) found HUOBI-SPOT, HUOBI-FUTURES,
  and BITSTAMP-SPOT are **missing from the venue universe entirely** (`VENUES_BY_ASSET_GROUP["cefi"]` +
  `venue_adapter_keys.py` + `venue_mapping.py:169-205`) despite real captured data existing for them — i.e. "these
  venues should be registered, they're just never fetched in production."
- `unified-api-contracts@181b5311` (2026-07-09,
  `fix(cefi): remove never-captured huobi/bitstamp/htx venues from registry + instrument universe`) — filed **one day
  before this session started** — deliberately **removed** huobi/bitstamp/htx entries from `venue_mapping.py`,
  `provider_api_versions.yaml`, `venue_tokens.py`, and `instrument_validation.py`, on the reasoning that they were
  never-captured dead weight.
- `instruments_remaining_work_audit_2026_07_10.md`'s own cross-check of this same P0 item verdicted "Design: aligned
  with SSOT, Proceed" — also without knowledge of 181b5311.

Checked both docs directly: **neither mentions 181b5311**. This is not a re-litigation of an already-settled question —
it's a genuine case of two independent decisions landing in the same week, reaching opposite conclusions, neither aware
of the other.

## What re-reading 181b5311's diff shows

Every row it removed was an orphaned Tardis-slug mapping-table entry for a venue that was **never declared** in
`VENUES_BY_ASSET_GROUP["cefi"]` in the first place — so "never-captured" is literally true of that specific dead code
path. But that does not by itself prove the venues are unviable: a half-registered venue with a live Tardis archive
underneath it is a different fact pattern from a genuinely-dead venue with no real data behind it at all. The smoketest
finding's claim ("real captured data exists for these venues") has not been independently re-verified against live
Tardis/GCS data in this pass — that verification is the natural first step before either side is acted on further.

## 2026-07-10 (later) — partial verification, does not fully settle it

Read the LIVE cefi `availability_index.parquet` directly (14M+ row canonical): **zero rows exist for HUOBI-SPOT,
HUOBI-FUTURES, BITSTAMP-SPOT, HTX-SPOT, or any HUOBI/BITSTAMP/HTX-prefixed venue string** — a case-insensitive scan of
the entire `venue` column found no matches at all. This is consistent with "never fetched" and does directly contradict
a literal reading of "real captured data exists for them" (our own manifest has none). It does **not** settle whether
Tardis (the vendor) has a real, fetchable archive underneath — the codebase's own `venue_mapping.py` already carries a
Tardis-slug entry for `("HUOBI-FUTURES","PERPETUAL"): "huobi-dm"` (flagged elsewhere in the smoketest doc as pointing to
the wrong sub-market, not as nonexistent), which implies SOME real Tardis exchange archive exists for at least Huobi
futures — just possibly the wrong slug. Confirming whether Tardis actually has a fetchable, non-empty archive for these
3 venues needs a live Tardis API/catalog check, which this pass did not have credentials/time to make. **Leaning
evidence: closer to Option B (181b5311 was likely correct that nothing is captured), but the "genuinely available on
Tardis vs not" question is still open** — recommend whoever picks this up start with a live Tardis exchange-catalog
lookup for `huobi`/`huobi-dm`/`bitstamp` before deciding.

## Options

**A — Verify smoketest's "real captured data" claim directly, then decide.** Read the live manifest/Tardis archive for
HUOBI-SPOT/HUOBI-FUTURES/BITSTAMP-SPOT to confirm whether real, non-trivial captured rows actually exist. If yes,
181b5311 was premature and these venues should be registered per the original P0 finding (with the mapping-table rows
restored, correctly wired). If no meaningful data exists, 181b5311 was correct and the P0 finding should be closed as
stale. **[RECOMMENDED]** — this resolves the contradiction with evidence instead of picking a side blind.

**B — Defer to 181b5311 as the more recent decision and close the P0 finding as superseded.** Fast, but risks discarding
real, already-captured data if the smoketest's original claim was correct.

**C — Restore the removed venues per the P0 finding and re-open 181b5311's reasoning for review.** Fast the other
direction; risks re-adding genuinely dead code if 181b5311 was correct.

**Other:** operator may have additional context (e.g. a business reason huobi/bitstamp/htx were deliberately
deprioritized) not visible in either commit's message.

## Progress log

- 2026-07-10: Found during the P1-P3 headline sweep workflow's `smoketest_59bug` fix pass (re-triaging the smoketest
  doc's P0 list). Per the SSOT-contradiction HARD RULE, did not unilaterally re-reverse a same-week peer commit — filed
  this issue doc and escalating to the operator rather than forcing either direction. Still a real, open P0 gap either
  way it resolves.

## Resolution (2026-07-12)

Operator decision: **Option B** — huobi/bitstamp/htx should be entirely removed from everything. 181b5311's removal
stands; the smoketest P0 finding (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`) is stale and should be
treated as closed/superseded on this item.

Swept every repo (`unified-api-contracts`, `market-tick-data-service`, `instruments-service`, `unified-trading-library`,
`deployment-service`) for remaining huobi/bitstamp/htx references beyond 181b5311's original 4 files:

- **Removed**: a dangling `pyproject.toml` coverage-exclusion entry pointing at
  `unified_api_contracts/external/bitstamp/schemas.py`, a module that no longer exists on disk (already deleted, the
  pyproject.toml reference was just never cleaned up).
- **Removed**: 2 stale `capability_declarations` registry entries (`"source": "huobi"`, `"source": "bitstamp"`, both
  still claiming `"supports_live": true, "supports_batch": true"`) in the checked-in generated `ui-reference-data.json`
  and `openapi/ui-reference-data.json` — no Python source anywhere in `unified_api_contracts` still defines these as
  registry sources, confirming the generated file was simply stale relative to 181b5311's removal rather than reflecting
  a still-live registration. Applied as a targeted text-level edit (not a full regeneration) to avoid an unrelated
  ~2000-line reformatting diff from `json.dumps`'s default array-wrapping behavior differing from the original
  generator's compact-array style.
- Shipped as `unified-api-contracts@62e0855c7a0d7823f6807549e97f41280e539a33`.

**Confirmed out of scope, left untouched**:

- `tests/test_cefi_universe_coverage.py`'s `"HT"` entry — this is Huobi Token, a real historical top-100 cryptocurrency
  ASSET used in a survivorship-bias-freedom test (`_RETIRED_TOP100`), unrelated to Huobi the VENUE. Removing it would
  weaken the bias-freedom guarantee the test exists to provide.
- `docs/schema_health.svg` — cosmetic-only health-status diagram with zero production consumption. A naive YAML-only
  regeneration defaults every OTHER provider's status to "yellow/unverified" (loses real historical "verified" dates for
  unrelated providers) since it isn't backed by an actual pytest-integration run in this pass — left for the next real
  `scripts/update_schema_health_svg.py` run with real test data, which will drop huobi/bitstamp naturally as a side
  effect.
- `unified_api_contracts/external/defillama/mocks/*.yaml`, `unified_api_contracts/external/tardis/mocks/exchanges.yaml`
  — unrelated external ground-truth mock fixtures (DeFiLlama's real protocol/TVL list which happens to include an entity
  named "HTX", and Tardis's real vendor exchange catalog which genuinely does support huobi/bitstamp as exchanges) —
  these describe the real external world accurately and aren't part of our own venue registration.
- `scripts/canary/orphan-decisions.yaml`, `tests/cassette_orphan_allowlist.yaml` — historical decision/comment records
  already documenting these as orphaned/deleted; nothing further to action.
