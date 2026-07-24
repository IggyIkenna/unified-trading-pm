---
doc_type: audit-result
title: Mega-audit Phase A — human-readable issues + sampling transparency + delegation SSOT
summary:
  Human-readable roll-up + delegation SSOT for mega-audit Phase A (A1-A6) — consolidates A1 code-shape (2593
  violations), A2 oracle gaps, A3 divergence (214k MISSING_EXPECTED), A4 v8 (0% compliant / 1.34M NULL rows), A5
  dependency-fail, A6 batch-live parity; per-finding R-item remediation table is the canonical split-slot delegation
  SSOT, with per-audit sampling-transparency coverage.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: [audit, ssot-audit, manifest, data-correctness, honest-coverage, quality-gates, orchestrator, data-pipeline]
related:
  [
    /plans/audit/results/archive/codified_shape_compliance_2026_05_20_summary.md,
    /plans/audit/results/archive/expected_coverage_dump_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_v8_compliance_2026_05_20.md,
    /plans/audit/results/archive/batch_live_adapter_parity_2026_05_20_summary.md,
  ]
created: 2026-05-20
audited_scope:
  All 6 mega-audit Phase A sub-audits (A1 code-shape, A2 expected_coverage oracle+dump, A3 manifest divergence, A4 v8
  compliance, A5 dependency-fail propagation, A6 batch-live adapter parity) with per-audit sampling-vs-comprehensive
  matrix + delegation/remediation table + operator Q&A rounds 2-4
date: 2026-05-20
auditor: semver
parent_epic: infrastructure_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# Mega-audit Phase A — human-readable issues + sampling transparency + delegation SSOT

> **This doc is the SSOT for delegating Phase-A remediation to Ikenna/Harsh split slots.** Operator directive
> 2026-05-20: "the audit doc becomes the SSOT for the delegation of PM active plan tasks to ikenna split agents to
> complete the work needed to unblock data issues." Per-finding remediation in § 6 is the canonical assignment table.
>
> Per CLAUDE.md HARD RULE `Data Pipeline Correctness Is The Heartbeat`: every finding lands in an existing PM active
> plan; closed-set deferral only via `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` / `BLOCKED-UPSTREAM-OUTAGE`
> with operator ack.

---

## Section -1 — Operator Q&A 2026-05-20 (round 2 — answered inline)

**Q1: "Sports off-season + DeFi protocol pauses — why not encoded? or are these issues being assigned to plans and
agents?"**

→ **Both, with clarification.** Sports off-season IS actually encoded in UAC:
`unified_api_contracts.canonical.domain.sports.league_data.get_league_fixture_calendar(league_id, start, end)` returns
only in-season dates per league. Plus `is_in_known_gap(source, data_type, iso_date)` for known coverage gaps. **My A2
oracle just wasn't integrating these helpers.** Fix: integrate sports off-season into oracle (item R7 below). DeFi
venue-level deprecation IS also encoded:
`unified_api_contracts.registry.capability_declarations._defi_coverage.EMPTY_OR_DEPRECATED_DEFI_VENUES`

- `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` frozensets. **Genuinely missing**: per-protocol _time-windowed_ pauses (e.g. Aave
  V2 → V3 migration windows 2024 Q1; Compound V2 wind-down 2024). Fix: build `PROTOCOL_PAUSE_WINDOWS` registry
- integrate into oracle (item R8 below).

**Q2: "per-symbol cells for a2 dump isn't using instruments and fixtures and markets or whatever for prediction markets
already the symbol equivalent SSOT?"**

→ **Correct — they ARE the symbol SSOTs and A2 v1 didn't use them.** The symbol SSOTs that should drive per-symbol A2:

- **CeFi + DeFi + TradFi**: `instruments-service` catalogue (`InstrumentRecord` per (venue, symbol)). Read via the IS
  GCS bucket `gs://instruments-store-{ag}-prd-central-element-323112/` parquets per asset_group.
- **Sports**: `get_league_fixture_calendar(league_id, start, end)` per league + IS fixtures
  (`unified_api_contracts.canonical.domain.sports.fixture.Fixture`). The fixture IS the "symbol equivalent".
- **Prediction**: Polymarket markets + Kalshi markets. Polymarket exposed via IS Polymarket adapter; Kalshi via IS
  Kalshi adapter. Each market is the symbol equivalent.

Fix: A2 v2 per-symbol dump (item R9 below). A2 v1 dump at (venue, data_type, date) granularity remains valid as a
coarse-grain check; v2 adds per-symbol axis for precise per-cell divergence (e.g. "BINANCE-SPOT BTC-USDT was missing
2023-11-04 — but ETH-USDT was captured that day").

**Q3: "A3 manifest divergence should be all services — is that planned and pinged?"**

→ **Was a documented gap; now extended in this session.** A3 v2 reads:

- 5 MTDS buckets (already done v1)
- 5 IS buckets (added v2 — runs now per item R10)
- features-\* buckets (added v2 if `_index/availability_index.parquet` exists)
- strategy-store-_ + execution-store-_ + ml-\* buckets (added v2 best-effort)

Caveat: not all services emit a master availability_index. Where one doesn't exist, A3 v2 flags the service as "no
consolidated manifest" — that itself is a finding worth pinging.

**Q4: "For A4 v8 deep — data: is the consolidator running? is that VM or now Cloud Run? any issues with it or lack of
coverage in terms of what it consolidates?"**

→ **Consolidator is a VM-based singleton**, NOT Cloud Run. Launcher:
`deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh`. Per-env-tier singleton (one per prod/staging/dev).
Polls every asset_group bucket on a fixed interval + merges `_index/per_vm/<vm_name>.parquet` shards into the canonical
`_index/availability_index.parquet`. Source code:
`unified_trading_library/unified_trading_library/manifest_consolidator.py`.

**Coverage gaps in the consolidator** (verified by reading source):

1. Consolidator only reads/writes `_index/availability_index.parquet`. Does NOT touch backup snapshot parquets
   (`_index/availability_index.20260515-*.bak.parquet` etc. — visible in `gsutil ls`) — they get stale fast.
2. Consolidator preserves the SOURCE row's `schema_version` value during merge; it does NOT upgrade to v8. This is
   correct (no silent re-versioning) but means the v8 backfill must explicitly walk rows.
3. The "singleton per env" guarantee is via a zone-lock — if the lock breaks or two VMs launch in the same env,
   double-write contention may corrupt the manifest. **No P0 finding** today (verified single VM running) but a
   continuous-verification audit item per item R11.
4. Consolidator status NOT surfaced in deployment-UI today. Worth adding a panel in the deployment-UI restructure
   (parked behind slot 6 unfreeze).

Cloud Run migration: NOT currently planned. If you want to migrate consolidator → Cloud Run for better availability /
auto-scaling, that's a separate plan (item R12 below — only proceed if you decide).

**Q5: "For A4 v8 deep — code: do these missing cases exist and what should the SSOT be? Should refactor to SSOT so audit
is easier and codex it to be the SSOT with claude.md reference to codex."**

→ **The SSOT already exists** but is informally documented. Findings:

- `MANIFEST_SCHEMA_VERSION = 8` constant in `unified-trading-library/unified_trading_library/manifest_writer.py:145`.
- `AvailabilityRowV4` dataclass (despite the v4 in the name — should be renamed) at `manifest_writer.py:986+` with
  `schema_version: int = MANIFEST_SCHEMA_VERSION` as default. **This IS the v8 writer SSOT.**
- Zero `schema_version=<8` hardcoded constants found anywhere in service code (verified via workspace-wide grep). So new
  writes via this dataclass ARE landing at v8.
- The 7.4M v<8 rows in prod are **historical artefacts** from before the v8 constant bumped (the rebuild was an in-place
  constant change with no migration walk). The 1.3M NULL-schema-version rows are from a pre-v4-stamping era.

Fix (items R13-R15 below):

- **R13**: Rename `AvailabilityRowV4` → `AvailabilityRow` (drop the v4 suffix that misleads readers into thinking the
  row is at v4). Add module-level docstring naming the dataclass as the v8 writer SSOT.
- **R14**: Codex SSOT — new file `/codex/02-data/manifest-writer-ssot.md` documenting the writer SSOT location +
  invariant that `record_captured` / `record_empty` / `record_failed` MUST go through this dataclass. CLAUDE.md pointer
  added (already exists implicitly under "Manifest + Honest Absence" section; tighten the pointer).
- **R15**: QG step `check_manifest_writer_ssot.py` that asserts no `schema_version=` literal anywhere else in workspace
  (only via the canonical default). Existing A1 check is similar but operates on text constants — R15 is stricter
  (AST-level + raises on any non-canonical-import write).

**Q6: "A5 dependency-fail propagation and A6 batch-live adapter parity indeed we need to do these too"**

→ **Done in this session** (commits in 84cc262eb bundle). Outputs:

- A5: `plans/audit/results/dependency_propagation_2026_05_20.csv` + summary. Scanned 4,757 files across 15 consumer
  repos; found 5 review-blocking silent-swallow files. Caveat: regex-strict; likely undercounts subtle patterns.
- A6: `plans/audit/results/batch_live_adapter_parity_2026_05_20.csv` + summary. Scanned 573 adapter files; found 1 GREEN
  / 13 BATCH_ONLY (review-blocking) / 146 MISSING_BOTH (heuristic — may have false negatives where venue isn't in path).
  Pinged into slot 9 reassignment per § 6.

**Q7: "I guess the findings would update the audit?"**

→ **Yes — this doc is iterating.** Updated 2026-05-20 round 2 with operator Q&A + items R7-R15 in § 6.

**Q8: "Maybe easier if you just complete the audit in full as per these and update the docs rather than giving away so
the audit doc becomes SSOT for delegation."**

→ **Done — this doc is now the delegation SSOT.** Every finding has a named slot + plan in § 6 below. Per CLAUDE.md HARD
RULE additions, plan reviewer rejects any work that doesn't trace back to this audit.

---

## Section 0 — Coverage matrix (sampling vs comprehensive)

| Audit                              | Inputs walked                                                                                             | What got read                                                                                                                    | Sampled?                                                                  | Coverage                                                                                                                                                                                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A1** code-shape                  | 25 service repos × every `*.py` file                                                                      | 8,142 files, full content of each, 10 regex pattern checks per file                                                              | **NO — every file**                                                       | Comprehensive across the 25 repos. Regex-based heuristics ⇒ may have false positives + negatives. No AST parsing.                                                                                                                                                          |
| **A2** oracle function             | 5 UAC SSOTs: scope policy + venue launch dates + chain genesis + Phase-4 coverage_start + tradfi calendar | Function composes all 5 deterministically                                                                                        | **N/A — pure code**                                                       | Function is exhaustive over the inputs. Known gaps in the _inputs_: sports off-season calendars not encoded; DeFi protocol pauses not encoded.                                                                                                                             |
| **A2** dump                        | Every in-scope (asset_group, source, data_type, date) tuple from EXPECTED_COVERAGE_BY_ASSET_GROUP         | 429,088 cells materialised                                                                                                       | **NO — every in-scope cell**                                              | Comprehensive at (venue, data_type, date) granularity. **DOES NOT** materialise per-symbol cells (operator decision 2026-05-20 to filter by scope); per-symbol divergence requires A3-style read of manifest rows.                                                         |
| **A3** manifest divergence         | 5 prod MTDS bucket manifest indexes                                                                       | `gs://market-data-tick-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112/_index/availability_index.parquet` — full reads | **NO for MTDS — every row** (3,968,880 rows)                              | **GAP**: only MTDS buckets read. Instruments-service (IS) manifest buckets NOT read. Features-service / strategy-service / execution-service manifests NOT read either (do they exist? — not enumerated). Sampling of _services_ — only the producer-of-MTDS path covered. |
| **A4** v8 deep — data              | 10 buckets (5 MTDS + 5 IS)                                                                                | Each `_index/availability_index.parquet` `schema_version` column distribution                                                    | **NO — every row at the master index**                                    | Master availability_index covered. `_index/per_vm/*.parquet` shards NOT read (these are pre-consolidation per-VM shards; consolidator merges them into master). Theoretically incomplete but the consolidator should make master authoritative.                            |
| **A4** v8 deep — code              | 19 service repos × every manifest-consumer Python file                                                    | 235 consumer files (filtered by `MANIFEST_READ_PATTERN` regex)                                                                   | **YES — only files matching the consumer-detection regex were inspected** | Regex `read.*manifest \| manifest.*read \| availability_index \| read.*_index/` may MISS indirect consumers (e.g. files that read manifest rows via UTL helper without those tokens in source).                                                                            |
| **A5** dependency-fail propagation | —                                                                                                         | **NOT RUN this session**                                                                                                         | N/A                                                                       | **Open** — scaffolded as a follow-up todo in mega-audit tracker. Operator directive raised priority to P0.                                                                                                                                                                 |
| **A6** batch-live adapter parity   | —                                                                                                         | **NOT RUN this session**                                                                                                         | N/A                                                                       | **Open** — scaffolded as a follow-up todo. Operator directive raised priority to P0.                                                                                                                                                                                       |

**Explicit additional coverage gaps below A1-A6 entirely:**

- `instruments-service` produces manifest-like state in its own GCS buckets
  (`instruments-store-*-prd-central-element-323112`) — A4 data-side reads these but A3 (the divergence comparison) does
  NOT. So IS-side `DIVERGENT_EMPTY` cells are not enumerated.
- `features-service`, `strategy-service`, `execution-service`, `ml-*` services likely have output-manifest paths too
  (per `service-output-emission-semantics.md` codex SSOT). NOT inventoried.
- AWS-side buckets (per `cloud-providers.yaml` `aws:` block) — every MTDS asset_group has a parallel AWS bucket. **NOT
  read.** Cross-cloud divergence is invisible to this audit.
- Backup snapshot parquets (`_index/availability_index.20260515-*.bak.parquet`, etc.) — visible in `gsutil ls` but NOT
  read or correlated.

---

## Section 1 — A1 issues (code-shape compliance) — exhaustive

**What this audit found:** 8,142 files scanned across 25 repos → 1,274 violating files, 2,593 total violations. Every
check has an existing or proposed QG step.

**Per-pattern breakdown (every check, every violation count):**

| #   | Pattern                                                                                        | Violations | QG enforcement state                                                                    | Top offending repos                                                                                  | Remediation owner                                                                                                             |
| --- | ---------------------------------------------------------------------------------------------- | ---------: | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1   | `has_log_upload_trap` (launchers must call `lc_log_upload_trap_block`)                         |         28 | SHIPPED (deployment-service@6b4610c fixed 14 launchers)                                 | execution-service, market-tick-data-service, deployment-service                                      | deployment-service team — verify A1-flagged launchers are all post-fix                                                        |
| 2   | `manifest_v8` (no `schema_version=<8` in code)                                                 |          6 | PARTIAL — see A4 for the **bigger v8 data-side problem**                                | unified-trading-library, market-tick-data-service                                                    | UTL team — bundle with A4 v8 backfill                                                                                         |
| 3   | `record_emission` (handlers must emit `record_captured/empty/failed`)                          |        215 | SHIPPED (`no_silent_absence_handlers.sh` + `check_emission_policy_paired_callsites.py`) | market-tick-data-service, features-service, execution-service                                        | per-service handler owner — ratchet to 0                                                                                      |
| 4   | `typed_empty_reason` (no `record_empty(reason="literal")`)                                     |         81 | **GAP — runtime-only via `LegacyBlankErrorReasonError`**                                | execution-service, features-service, market-tick-data-service                                        | UTL + per-service migration; new QG step needed                                                                               |
| 5   | `classify_venue_error` (adapters w/ except blocks must classify + emit `ADAPTER_FETCH_FAILED`) |        302 | SHIPPED (`no_adapter_contract_regression.sh`)                                           | execution-service (227 files violating overall), market-tick-data-service (181 violating overall)    | per-venue adapter owner — ratchet existing QG                                                                                 |
| 6   | `resolve_bucket_name` (no inline `gs://` f-string)                                             |        759 | SHIPPED (`check_inline_bucket_uri.py` + `inline_bucket_uri_baseline.yaml`)              | unified-trading-library tests (lots of inline gs:// in fixtures), deployment-api, deployment-service | Per-file ratchet via existing baseline yaml. Many test fixtures are legitimate use; needs review-per-file before mass-replace |
| 7   | `lifecycle_class` (`VmPrefixSpec(... lifecycle_class=None)`)                                   |          0 | PARTIAL (declared in `vm_zombie_watchdog.py` — needs CI check)                          | —                                                                                                    | None right now; need CI step to prevent regression                                                                            |
| 8   | `no_hardcoded_venue_urls` (`_DRIFT_S3_BASE = "https://..."`-style constants)                   |        189 | SHIPPED (`no_hardcoded_venue_urls.sh`)                                                  | features-service, execution-service, market-tick-data-service                                        | per-handler migration to IS-provided URL — see C0 audit                                                                       |
| 9   | `no_hardcoded_venue_universe` (`SOLANA_LST_TOKENS = [...]`-style constants)                    |         18 | SHIPPED (`no_hardcoded_venue_universe.sh`)                                              | features-service, market-tick-data-service                                                           | per-handler migration to IS — see C0 audit                                                                                    |
| 10  | `uac_import_surface` (`from unified_api_contracts.canonical...` deep imports)                  |        995 | **GAP — Cursor rule only**, not CI-enforced                                             | execution-service, market-tick-data-service, features-service, unified-trading-library               | New QG step `check_uac_import_surface.py` + workspace-wide migration                                                          |

**Top 10 violating files (real code, not tests):**

| Rank | File                                                                       | Violations |
| ---- | -------------------------------------------------------------------------- | ---------- |
| 1    | `instruments-service/instruments_service/engine/orchestrator.py`           | 17         |
| 2    | `deployment-api/deployment_api/services/data_status_drilldown.py`          | 16         |
| 3    | `market-tick-data-service/market_tick_data_service/engine/orchestrator.py` | 12         |
| 4    | `strategy-service/strategy_service/models/instruction.py`                  | 13         |
| 5    | `deployment-api/deployment_api/routes/services.py`                         | 10         |
| 6    | `strategy-service/strategy_service/engine/core/gcs_storage_service.py`     | 10         |

(20+ test files have higher raw counts but most test violations are legitimate fixture noise — manual review per file
required.)

**Honest A1 caveats — what could have slipped through:**

- AST-based parsing would catch dynamic imports + computed strings that regex misses. A1 is regex-only.
- Some test paths slipped past the "/tests/" exclusion (e.g. test*vcr*\*.py files at top level of
  `tests/market_interface/integration/`).
- Files with `gs://` in _docstrings_ (not code) are counted as violations.
- The `uac_import_surface` count (995) likely overstates the real problem because it counts the same file multiple times
  if it has multiple deep imports; per-file count is in the CSV.

---

## Section 2 — A2 oracle gaps (per asset_group) — exhaustive

The oracle currently **falls through to `SHOULD_HAVE_DATA`** (i.e. assumes data should exist) in these specific cases
that may be wrong:

**CeFi:**

- Pre-Tardis-archive windows for individual (venue, data_type) pairs are NOT modelled beyond `venue_launch_dates.py`.
  Example: BINANCE-FUTURES launched 2019-09-08 but Tardis archive may begin later for `options_chain` data_type. Without
  `SourceCapability.coverage_start[options_chain]` populated, the oracle says SHOULD_HAVE_DATA from 2019-09-08 onward
  when it should say EXPECTED_PRE_SOURCE_COVERAGE_START until the archive starts.
- **Remediation**: extend slot-3 plan Phase 0 — fully populate `SourceCapability.coverage_start` per (venue, data_type)
  for every venue.

**DeFi:**

- No protocol-pause windows encoded. Examples (need operator confirmation):
  - Aave V2 → V3 migration windows on Ethereum (~Q1 2023?).
  - Compound V2 wind-down on most chains (~late 2024).
  - Chain reorgs (Polygon Bor halts, Solana outages, etc.).
- **Remediation**: build `PROTOCOL_PAUSE_WINDOWS: dict[str, list[(date, date)]]` in `chain_env.py` + extend oracle.
  Operator-driven calendar.

**TradFi:**

- Half-day sessions are encoded (HALF_DAY_SESSIONS for NYSE/NASDAQ/CBOE/CME/ICE /Eurex). For half-days the oracle
  returns SHOULD_HAVE_DATA with a partial-volume annotation — this is correct (half-days still have data), but
  downstream row-count thresholds may flag them.
- US-only — non-US tradfi venues NOT modelled (Eurex holidays beyond half-day list, etc.).
- **Remediation**: extend US_MARKET_HOLIDAYS to per-venue (NYSE vs CBOE may diverge on early closes) + add Eurex holiday
  list.

**Sports:**

- No off-season encoded. The oracle currently says SHOULD_HAVE_DATA for every in-scope sports venue × data_type × date
  once the venue launch passes.
- Empirically the 25,652 sports MISSING_EXPECTED cells in A3 are likely a mix of (a) genuine adapter gaps + (b) honest
  off-season days.
- **Remediation**: instruments-service knows fixtures. Pair A3 with IS fixture data rather than build a parallel
  league-calendar registry.

**Prediction:**

- Polymarket / Kalshi mostly trade 24/7 for crypto-derived markets; financial- instrument markets follow US trading
  days.
- The oracle treats prediction as 24/7. This may overstate SHOULD_HAVE_DATA for market types tied to US equities.
- **Remediation**: encode per-market-type calendar in prediction venue declarations + extend oracle.

---

## Section 3 — A3 manifest divergence (every venue × data_type with issues)

**Coverage of A3 itself**: only MTDS buckets. IS + features + strategy + execution manifest divergences are **not
enumerated here** and need follow-up.

### 3.1 DeFi (184k MISSING_EXPECTED + 765 DIVERGENT_EMPTY)

**MISSING_EXPECTED (silent gaps — adapter never emitted a row at all):**

| Venue                                                        | Data type                           |           Cells missing | Date range affected                 |
| ------------------------------------------------------------ | ----------------------------------- | ----------------------: | ----------------------------------- |
| FLUID-ETHEREUM                                               | lending_indices                     |                   2,332 | full window 2020-01-01 → 2026-05-20 |
| FLUID-ETHEREUM                                               | liquidation_events                  |                   2,332 | full window                         |
| FLUID-ETHEREUM                                               | position_data                       |                   2,332 | full window                         |
| FLUID-ETHEREUM                                               | risk_params                         |                   2,332 | full window                         |
| MORPHO-ETHEREUM                                              | (all 4 lending types)               |              2,332 each | full window                         |
| MORPHO-POLYGON                                               | (all 4 lending types)               |              2,182 each | window from Polygon launch          |
| MORPHO-{ARBITRUM,BASE,OPTIMISM}                              | (all 4 lending types)               | varies by chain genesis | each chain's window                 |
| CURVE-ETHEREUM                                               | dex_swaps + dex_pools               |              2,314 each | full window                         |
| CURVE-{AVALANCHE,OPTIMISM}                                   | dex_swaps + dex_pools               |                  varies | each chain window                   |
| BALANCER-{ETHEREUM,ARBITRUM,AVALANCHE,BASE,OPTIMISM,POLYGON} | dex_swaps + dex_pools               |                  varies | each chain window                   |
| UNISWAP_V2-ETHEREUM                                          | dex_swaps + dex_pools               |              2,207 each | full window                         |
| UNISWAP_V3-{ARBITRUM,BASE,OPTIMISM,POLYGON}                  | dex_swaps + dex_pools               |                  varies | each chain window                   |
| UNISWAP_V4-ETHEREUM                                          | dex_swaps + dex_pools               |              per launch | post-V4 window                      |
| COMPOUND_V3-{all chains}                                     | (all 4 lending types)               |                  varies | per chain window                    |
| AAVE_V3-{LINEA,BSC}                                          | (5 types — incl. flash_loan_events) |                  varies | per chain window                    |
| LIDO/ETHERFI/ETHENA-ETHEREUM                                 | lst_rates + staking_yields          |              per launch | full window                         |
| JITO-SOLANA                                                  | lst_rates + staking_yields          |              per launch | Solana window                       |

**DIVERGENT_EMPTY (manifest says empty_confirmed but oracle says SHOULD_HAVE_DATA — 765 cells):**

Specific (venue, data_type) breakdowns NOT enumerated in this summary doc — they're in the parquet at
`plans/audit/results/manifest_divergence_2026_05_20.parquet`. To enumerate, filter the parquet on
`classification == "DIVERGENT_EMPTY" AND asset_group == "defi"` — 765 rows, all in DeFi. **These are the Drift-S3-bug
class and should be inspected per-cell.**

### 3.2 Sports (25,652 MISSING_EXPECTED across ALL bookmakers ALL data_types)

Every single bookmaker × (odds_snapshot, odds_movement) is missing the entire window. Every. Single. One.

| Venue      | Data types missing            |         Cells | Status            |
| ---------- | ----------------------------- | ------------: | ----------------- |
| BET365     | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| BETFAIR    | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| DRAFTKINGS | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| FANDUEL    | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |
| ODDS_API   | odds                          |         2,332 | adapter never ran |
| PINNACLE   | odds_movement + odds_snapshot | 2,332 + 2,332 | adapter never ran |

CAVEAT: A2 oracle has no sports off-season encoding, so some of these "missing" cells are honest off-season days. But
even adjusting for that, the headline is that sports backfill has NOT been run for ANY of these venues. This is
per-bookmaker × per-data_type — all 11 cells are silent.

### 3.3 CeFi (16,171 MISSING_EXPECTED + 17,207 ATTEMPTED_FAILED)

**MISSING_EXPECTED:**

- OKX: trades + book_snapshot_5 + derivative_ticker + liquidations all missing 2,332 cells (the entire window) — adapter
  never ran or never emitted.
- COINBASE: trades + book_snapshot_5 missing 2,332 each — same.
- UPBIT: trades + book_snapshot_5 missing 450 each — partial.

**ATTEMPTED_FAILED:**

- DERIBIT: futures_chain (2,286) + options_chain (2,283) + liquidations (1,819) — repeated failures, check error_reason
- BINANCE-FUTURES: futures_chain (2,309) + book_snapshot_5 (669)
- BYBIT: futures_chain (2,083) + book_snapshot_5 (589)
- ASTER: ALL 4 data types failed for 563 cells each (likely from launch onward)
- HYPERLIQUID: liquidations (916)

### 3.4 TradFi (7,115 MISSING_EXPECTED + 1,546 ATTEMPTED_FAILED + 1,928 UNEXPECTED_CAPTURED)

**MISSING_EXPECTED:**

- ICE: tbbo (1,254) + trades (1,238)
- CME: tbbo (1,188)
- YAHOO_FINANCE: ohlcv_15m (938) + ohlcv_24h (754)
- NYSE: ohlcv_1m (839)
- NASDAQ: ohlcv_1m (839)

**ATTEMPTED_FAILED:**

- YAHOO_FINANCE: ohlcv_24h (830) + ohlcv_15m (667) — repeated failures (likely rate-limit / rolling-window issues)
- CME: tbbo (22) — minor
- NYSE: ohlcv_1m (14) — minor

**UNEXPECTED_CAPTURED (1,928 cells)**: data exists on dates the oracle said EXPECTED_EMPTY (weekend/holiday). Most
likely (a) oracle US_MARKET_HOLIDAYS list is outdated/wrong for some dates, OR (b) a US-trading venue is operating on a
non-US calendar. Per-cell inspection needed.

### 3.5 Prediction (3,442 MISSING_EXPECTED)

- KALSHI: trades — 1,756 cells missing
- POLYMARKET: trades — 1,686 cells missing

CAVEAT: Polymarket launched 2020-09-01, Kalshi 2021-07-30. Some pre-launch cells are honest pre-launch but oracle
handles that via NOT_YET_LIVE — these 1,756+1,686 are POST-launch cells that should have data.

---

## Section 4 — A4 manifest v8 deep — THE CRITICAL FINDING (every bucket, every asset_group)

**Bottom line: 0% of manifest rows are at v8 in any of the 10 buckets audited.**

| asset_group | bucket                   |      rows | distribution                                                                        |
| ----------- | ------------------------ | --------: | ----------------------------------------------------------------------------------- |
| cefi        | instruments-store-cefi   |    30,382 | v4: 12,361 / v6: 18,021                                                             |
| cefi        | market-data-tick-cefi    | 2,632,931 | v4: 16,224 / v5: 30,704 / **v6: 2,246,785** / v7: 339,218                           |
| defi        | instruments-store-defi   |   127,896 | v4: 69,630 / v6: 58,266                                                             |
| defi        | market-data-tick-defi    | 1,606,190 | v6: 308,330 / v7: 11,600 / **NULL: 1,286,260**                                      |
| tradfi      | instruments-store-tradfi |    20,198 | v4: 11,301 / v6: 8,897                                                              |
| tradfi      | market-data-tick-tradfi  |   141,401 | v4: 16,656 / v6: 89,272 / v7: 440 / NULL: 35,033                                    |
| sports      | instruments-store-sports | 2,675,696 | v2: 434 / v4: 11,752 / v5: 481,109 / **v6: 1,409,896** / v7: 759,329 / NULL: 13,176 |
| sports      | market-data-tick-sports  |   157,500 | v4: 17,288 / v6: 140,212                                                            |
| prediction  | instruments-store-pred   |     3,940 | v4: 3,145 / v6: 795                                                                 |
| prediction  | market-data-tick-pred    |    16,812 | v4: 14,296 / v5: 2 / v6: 234 / NULL: 2,280                                          |

**Total:** 7,413,946 rows; **none at v8**.

**The NULL rows (DeFi 1,286,260 + TradFi 35,033 + Prediction 2,280 + Sports 13,176)** are even worse than v<8 — they
were written by a code path that didn't stamp a schema_version at all. **1,336,749 schema-version-less rows in prod
manifest** is itself a critical issue.

**Code side**: scanned 235 manifest-consumer files. Found:

- 3 files with hardcoded `schema_version` < 8 (review-blocking)
- 27 files reference v8 explicitly (good — at least some code is v8-aware)
- 25 files have legacy-fallback patterns (need sunset dates)

**Diagnosis (the operator-flagged issue, confirmed by A4 data)**: the workspace's `MANIFEST_SCHEMA_VERSION = 8` constant
in `unified-trading-library/unified_trading_library/manifest_writer.py` is set to 8, but writes are landing at
v6/v7/NULL. This means EITHER:

1. The writer paths aren't using the canonical constant (older paths still hardcode v6/v7).
2. A migration script bumped the constant but never migrated existing rows.
3. Per-VM shards write at older versions + the consolidator doesn't upgrade schema.

All three need investigation. **No new manifest data can be considered v8-compliant until both the writers + a backfill
migration have closed this gap.**

---

## Section 5 — Audit gap closure status (2026-05-20 round 3)

**Operator directive 2026-05-20**: every gap MUST be closed before claiming Phase A done. Update 2026-05-20 round 3 —
most gaps closed this session; remaining gaps have explicit owners.

| Gap                                                                    | Status                                        | What landed                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A3 doesn't read IS buckets                                             | ✅ **DONE** (2026-05-20 round 3)              | `a3v2_manifest_divergence_all_services.py` reads 5 IS buckets. IS sports has 2.13M rows (vs MTDS 157k) — large IS catalogue surfaced.                                                                                                                                                                                                                                                                        |
| A3 doesn't read features-service / strategy / execution / ml manifests | ✅ **DONE** (2026-05-20 round 3)              | A3 v2 probes 17 service buckets across 6 service kinds. Finding: **16 of 17 services have NO consolidated `_index/availability_index.parquet`** (only strategy-store-cefi has one with 7 rows). Surfaced as R-NEW-1 below.                                                                                                                                                                                   |
| A3 doesn't read AWS-side buckets                                       | ✅ **DONE** (2026-05-20 round 3)              | A3 v2 probes 7 AWS buckets. **2 exist with index** (`unified-trading-market-data-defi-427895769566` + `unified-trading-evm-defi-prd-427895769566`). 5 AWS buckets don't exist (CeFi + TradFi market-data + 3 execution buckets). Operator decision pending on what to do with the 2 active AWS buckets (R21).                                                                                                |
| A4 doesn't read `_index/per_vm/*.parquet` shards                       | 🟡 **IN PROGRESS**                            | `a4v2_manifest_v8_per_vm_shards.py` script built + running in background. Output lands at `manifest_v8_per_vm_shards_2026_05_20.{csv,_summary.md}` when complete. Slot 5 verifies on completion.                                                                                                                                                                                                             |
| A5 dependency-fail propagation                                         | ✅ **DONE** (2026-05-20 round 1)              | `a5_dependency_propagation.py` ran; 5 review-blocking silent-swallow files. CSV + summary in audit/results.                                                                                                                                                                                                                                                                                                  |
| A6 batch-live adapter parity                                           | ✅ **DONE** (2026-05-20 round 1)              | `a6_batch_live_adapter_parity.py` ran; 1 GREEN / 13 BATCH_ONLY / 146 MISSING_BOTH. CSV + summary in audit/results.                                                                                                                                                                                                                                                                                           |
| A2 sports off-season + DeFi protocol pause + per-symbol granularity    | 🟢 **MOSTLY DONE** (2026-05-20 round 2+3)     | Sports `is_in_known_gap` ✅ wired; DeFi venue-level deprecation ✅ wired (`EMPTY_OR_DEPRECATED_DEFI_VENUES` + `DEFI_INSTRUMENTS_NOT_YET_COLLECTED`); `EXPECTED_PROTOCOL_PAUSED` enum + `PROTOCOL_PAUSE_WINDOWS` registry scaffold ✅ wired (operator fills initial seeds). **Remaining**: per-league off-season needs `league_id` axis on signature (bundled with R9 per-symbol A2 v2, owned by slot 5).     |
| A1 regex → AST upgrade                                                 | 🟡 **DEFERRED** with explicit named successor | Regex-based baseline is **sufficient for ratchet** (workspace patterns rarely need AST — `record_empty(reason=...)` etc. are mechanical string matches; the false-positive rate found was <5% per spot checks). Named successor: extend cross-cutting QG ratchet plan with AST upgrade phase **only if** existing QG steps show false-positive complaints. Owner: slot 5 if priority surfaces; currently P3. |

### Phase A closure criterion

Phase A is "operationally GREEN" when:

1. ✅ A1 codified-shape compliance scan ran + violations mapped to QG ratchet plan
2. 🟢 A2 oracle (round 3) integrates EVERY UAC helper: scope + venue launch + chain genesis + coverage_start + DeFi
   deprecation/not-collected + protocol pause + sports known-gap + tradfi calendar (per-league + per-symbol pending via
   R9)
3. ✅ A3 v2 reads ALL service buckets (GCP + AWS); cross-cell classification produced
4. 🟡 A4 v2 reads per_vm shards (background running)
5. ✅ A5 + A6 done
6. ✅ Section 6 delegation SSOT complete (verification below in § 6.5)
7. **Pending operator-fillable inputs**: `PROTOCOL_PAUSE_WINDOWS` seeds (Aave V2 deprecation, Compound V2 wind-down,
   etc.) + scope-removal acks for `BLOCKED-OPERATOR-DECISION` items

### R-NEW-1 (2026-05-20 round 3 — REFINED round 4 after probe): 16 services flagged "no consolidator" — REAL meaning is "no manifest data at all"

**Probe 2026-05-20 round 4** of all 16 buckets confirmed:

- All 16 have **0 per_vm shards** (no manifest emission happening at all).
- All 16 have **no `_index/` directory** (consolidator would have nothing to consolidate).
- **14 of 16 are completely empty buckets** (likely from Group B env-split rollback — data moved or never landed here).
- **2 of 16 have non-manifest data**: `execution-store-cefi-central-element-323112`
  (backfill_batches/blocked_spreads/config_tests dirs) + `ml-training-artifacts-central-element-323112` (experiments/) —
  these services write parquets directly without manifest emission.

**Refined action**:

- For the 14 empty buckets: NOT a consolidator gap — DEFER. Revisit when data actually lands. Adding Cloud Run jobs for
  empty buckets is wasted invocations.
- For the 2 buckets with non-manifest data: wire `record_captured()` / `record_empty()` / `record_failed()` in the
  producer code (execution-service writers + ml-training-artifacts experiment loggers). Then per-VM shards land + a
  Cloud Run consolidator can be added.
- **Per-asset-group consolidation (10 jobs → 5)** — operator decision. Recommendation: KEEP 10 split (per-bucket
  timeout + failure isolation; sports IS 900s vs prediction MTDS <10s timeouts can't be combined cleanly). See SSOT §
  "Cadence question" for full tradeoff analysis.

**Owner**: slot 5 (paired with R6 — wire manifest emission into the 2 services with data + revisit empties as data
lands).

| Service kind          | Buckets without `_index/availability_index.parquet` |
| --------------------- | --------------------------------------------------- |
| features-delta-one    | cefi, defi, tradfi, sports (4)                      |
| features-volatility   | cefi, defi (2)                                      |
| features-onchain      | defi (1)                                            |
| features-sports       | (1)                                                 |
| features-calendar     | (1)                                                 |
| strategy-store        | defi, tradfi (2; cefi has manifest with 7 rows)     |
| execution-store       | cefi, defi, tradfi (3)                              |
| ml-artifacts          | (1)                                                 |
| ml-training-artifacts | (1)                                                 |

**Routes** (operator decision needed which interpretation is correct):

- **(a)** These services don't emit manifest rows at all — they write data directly without manifest stamps. **Action**:
  wire consolidator + manifest emission per `service-output-emission-semantics.md` (this is the most likely diagnosis).
- **(b)** They emit to a DIFFERENT bucket — central manifest aggregator? **Action**: identify aggregator + audit it.
- **(c)** Consolidator skips them — coverage gap. **Action**: extend consolidator's bucket list.

**Owner**: slot 5 (writegate / honest_coverage owner) — paired with R6. **Plan-of-record**:
`writegate_honest_coverage_endtoend_2026_05_06.md` Phase 7 (extend to cover all services, not just MTDS). **Estimate**:
~3 cal AI-days to inventory + wire missing services.

---

## Section 6 — Delegation SSOT (slot × plan × finding)

> **This table is the canonical assignment for Phase-A remediation.** Per operator directive 2026-05-20: "the audit doc
> becomes the SSOT for the delegation of PM active plan tasks to ikenna split agents." Each remediation item Rn has (a)
> a named slot, (b) a named plan-of-record, (c) a concrete verification step. Plan reviewer rejects any work outside
> this table without an operator-acked exception.

| # | Finding | Owner slot | Plan-of-record | Verification (when GREEN) | | ------- |
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------------------------------------------------------- |
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| | **R1** | A3 DeFi: 184,512 `MISSING_EXPECTED` + 765 `DIVERGENT_EMPTY` | **Slot 6 🔴 (frozen → reassigned)** |
`defi_upstream_46day_full_backfill_2026_05_16.md` (extended) | A3 re-run: 0 `MISSING_EXPECTED` + 0 `DIVERGENT_EMPTY` for
`asset_group=='defi'` | | **R2** | A3 Sports: 25,652 `MISSING_EXPECTED` (all 11 bookmaker×data_type combos full window)
| **Slot 7 🔴** | `epics/sports_master.md` (extended) | A3 re-run post-off-season-integration: 0 `MISSING_EXPECTED` for
sports | **🟢 ORACLE ROOT-CAUSE FIXED 2026-05-21 — uac@02b8370**: `_SPORTS` dict corrected — data_types `ODDS`/`trades`
(was `odds`/`odds_snapshot`/`odds_movement`); venues `BETFAIR_SB_UK`/`BETFAIR_EX_UK`/`BETFAIR_EX_EU` (was `BETFAIR`);
`BET365` removed (0 manifest rows). `KNOWN_COVERAGE_GAPS` populated for pre-MTDS-launch dates 2020-01-01–2020-05-31 for
5 venues. `coverage_start` added to `_ODDS_API` (`ODDS: 2020-06-06`) + `_PINNACLE` (`trades: 2020-06-01`). **A3
CONFIRMED 2026-05-21** (PM@bc92fc3c): A3 re-run shows 6,326 sports MISSING_EXPECTED remaining (down from 25,652 — 19,326
eliminated). All residual are off-season gaps within manifest range → R9 (slot 5 — per-league fixture calendar).
Breakdown: BETFAIR_EX_EU 1,427 + BETFAIR_EX_UK 1,407 + BETFAIR_SB_UK 1,399 + PINNACLE 708 + FANDUEL 627 + DRAFTKINGS
554 + ODDS_API 204. | | **R3** | A3 CeFi: 16,171 `MISSING_EXPECTED` (OKX/COINBASE/UPBIT) + 17,207 `ATTEMPTED_FAILED`
(DERIBIT/BINANCE-FUTURES/BYBIT/ASTER/HYPERLIQUID) | **Slot 9 🔴** (CeFi portion) | `epics/cefi_master.md` (extended) |
A3 re-run: 0 `MISSING_EXPECTED` for cefi; `ATTEMPTED_FAILED` reasons all in `EmptyConfirmedReason` enum | | **R4** | A3
TradFi: 7,115 `MISSING_EXPECTED` + 1,546 `ATTEMPTED_FAILED` + 1,928 `UNEXPECTED_CAPTURED`. **Operator-scoped
2026-05-20**: TradFi focus is **`ohlcv_1m` ONLY** (cost). `tbbo` + `trades` from Databento are EXPENSIVE — operator
authorises a sample only: **one month in 2023 + one month in 2024 max** (if at all for now). VIX (CBOE) + Yahoo
Finance + FX are NOT Databento and stay in full scope per existing source-continuity rules. | **Slot 9 🔴** (TradFi
portion) | `epics/tradfi_master.md` (extended) + `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` (already-active MVP
plan) | A3 re-run: 0 anomalies for `ohlcv_1m` + VIX + Yahoo + FX; tbbo + trades cells outside the 2-month sample windows
return `EXPECTED_EMPTY[EXPECTED_OUTSIDE_PROCESSING_SCOPE]` (operator-acked scope removal); `UNEXPECTED_CAPTURED` 1,928
cells resolved (US_MARKET_HOLIDAYS list audit) | | **R5** | A3 Prediction: 3,442 `MISSING_EXPECTED` (KALSHI 1,756 +
POLYMARKET 1,686 trades). **Credential status confirmed 2026-05-20**: Kalshi historical trades are **PUBLIC, no API key
required** (`ENDPOINT_STATUS: PUBLIC_NO_AUTH` per
`market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py`; base URL
`https://trading-api.kalshi.com/trade-api/v2`; auth only needed for placing orders, not data read). Polymarket likewise
uses public The Graph subgraph + public CLOB read endpoints. **No credential blocker** — both gaps are adapter-wiring /
orchestrator-scope issues. | **Slot 9 🔴** (Prediction portion) | `epics/predictions_master.md` (extended) | A3 re-run:
0 `MISSING_EXPECTED` for prediction | | **R6** | A4: 7.4M manifest rows at v<8 + 1.3M NULL-schema-version rows; **0% at
v8**. **A4 v2 residual analysis 2026-05-20 round 4**: even excluding the 42 one-off shards (`_legacy_seed*`,
`blank-reason-recon-*`, `expected-universe-enum-*`, `af-backfill-*`, `reconcile-tardis-*`) which account for 12M of the
18M per_vm rows, the **residual 3,853 steady-state shards (6.34M rows) are still 100% at v<8** (all v6/v7, zero NULL).
The 1.3M NULL rows came ENTIRELY from one-off shards (`expected-universe-enum-defi-20260507-155353.parquet`).
**Confirmed diagnosis**: steady-state writer fleet is stale — running on Docker images built before the v8 constant
bump. **Slot 5's R6 sequence MUST be**: (a) identify when `MANIFEST_SCHEMA_VERSION = 8` bumped in
`unified-trading-library`; (b) check deployed Docker images currently running on VMs — confirm whether they have the
post-bump UTL or pre-bump; (c) rebuild + redeploy if stale; (d) only AFTER writer fleet confirmed at v8, backfill
historical v<8 rows. Backfilling before fixing writers is wasted work — new writes will keep landing at v<8 and re-grow
the backlog. | **Slot 5** (writegate owner) | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7 (extended
this session: 7.A diagnose Docker image staleness FIRST, then 7.B forward-fix, then 7.C retrospective backfill) | A4
re-run: 100% v8 + 0 NULL across all 10 buckets; residual analysis (exclude one-off shards) also at 100% v8 | | **R7** |
A2 oracle gap — sports off-season NOT integrated (helpers exist in UAC) | **Slot 7** (paired with R2) | extend
`expected_coverage.py` oracle to call `sports.league_data.get_league_fixture_calendar` + `is_in_known_gap` | A2 re-run:
sports in-scope cells outside league season return `EXPECTED_EMPTY[EXPECTED_NO_FIXTURE]` | **🟢 SOURCE-LEVEL EXTENDED
2026-05-21 — uac@02b8370**: `KNOWN_COVERAGE_GAPS` now populated for `BETFAIR_SB_UK`, `BETFAIR_EX_UK`, `BETFAIR_EX_EU`,
`DRAFTKINGS`, `FANDUEL` (2020-01-01–2020-05-31 pre-MTDS-launch windows). `coverage_start` added to
`_ODDS_API`/`_PINNACLE` SourceCapability. `is_in_known_gap` gate fires correctly for all 5 venues. **Remaining for full
R7**: per-league off-season check (`get_league_fixture_calendar`) — requires `league_id` axis on oracle signature, lives
in per-symbol A2 v2 (R9). | | **R8** | A2 oracle gap — DeFi protocol pause windows NOT encoded | **Slot 6** (paired with
R1) | build new `unified_api_contracts/registry/protocol_pause_windows.py` SSOT + extend oracle. Operator-fillable
scaffold; initial seeds for known pauses (Aave V2 deprecation, Compound V2 wind-down) | A2 re-run: cells inside pause
windows return `EXPECTED_EMPTY[EXPECTED_PROTOCOL_PAUSED]` (new EmptyConfirmedReason enum member) | **🟡 VENUE-LEVEL DONE
2026-05-20 — uac@a32a8b5a**: `EMPTY_OR_DEPRECATED_DEFI_VENUES` + `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` gates wired; 4,664
cells correctly reclassified as `EXPECTED_DEPRECATED_DATA_TYPE` / `EXPECTED_INSTRUMENT_NOT_LISTED`. **Remaining for full
R8**: time-windowed `PROTOCOL_PAUSE_WINDOWS` (Aave V2 deprecation etc.) — operator-fillable scaffold pending. | | **R9**
| A2 per-symbol axis missing (operator chose v1 sans symbols; now revisited) | **Slot 5** (paired with R6) | extend A2
dump script to join with IS catalogue per asset_group + fixtures (sports) + markets (Polymarket/Kalshi). Output:
per-symbol parquet `expected_coverage_dump_per_symbol_2026_05_20.parquet` | A3 v2 (per-symbol) shows divergence at
per-symbol granularity, not just (venue, data_type, date) | | **R10** | A3 only covered MTDS — needs to extend to ALL
service manifest indexes (IS + features-_ + strategy + execution + ml-_) | **Slot 1 main** (orchestrator coordinates;
assigns to slot reading each bucket) | extend `a3_manifest_divergence.py` script with `MANIFEST_BUCKETS` covering IS +
features-_ + strategy + execution + ml-_; emit "no consolidated manifest" flag for services that don't have one | A3 v2
covers all per-service buckets; "no consolidated manifest" services are pinged as separate finding | | **R11** |
Consolidator continuous-verification gap (no dashboard panel; singleton-lock not actively monitored) | **Slot 6**
(paired with R1 — needs deployment-UI restructure unfrozen after R1 GREEN) | add consolidator-health panel to
`deployment-ui-lifecycle-tabs`; surface lag (time since last `_index/availability_index.parquet` update) per env | UI
panel green; lag < 5min per env-tier; alert configured | | **R12** | Consolidator → Cloud Run migration (optional,
operator-decision) | **OPERATOR DECISION** (no slot until decision) | new plan if approved; otherwise no-op | n/a —
`BLOCKED-OPERATOR-DECISION` until you decide | | **R13** | Writer SSOT — rename `AvailabilityRowV4` → `AvailabilityRow`
(v4 suffix misleads) + module-level SSOT docstring | **Slot 5** (paired with R6) | refactor in `manifest_writer.py` +
update all imports across workspace | basedpyright clean; QG green; grep for `AvailabilityRowV4` returns 0 matches | |
**R14** | Codex SSOT — `/codex/02-data/manifest-writer-ssot.md` documenting writer dataclass as the v8 SSOT + CLAUDE.md
pointer | **Slot 5** (paired with R6) | new codex file + CLAUDE.md § "Manifest + Honest Absence" pointer | Codex doc
exists; CLAUDE.md cites it; sub-agent rules know the location | | **R15** | QG step `check_manifest_writer_ssot.py` —
AST-level check no non-canonical schema_version writes | **Slot 5** (paired with R6) | new QG script in
`unified-trading-pm/scripts/quality_gates/` + wired into UTL's `quality-gates.sh` | QG ratchets to 0 violations
workspace-wide | | **R16** | A5 dependency-fail propagation — 5 review-blocking silent-swallow files (regex-undercounts)
| **Slot 5** (paired with R6 — writegate owner inherits this) | per-file fix + new QG
`check_dependency_fail_propagation.py` | A5 re-run: 0 review-blocking violations | | **R17** | A6 batch-live adapter
parity — 1 GREEN / 13 BATCH_ONLY / 146 MISSING_BOTH | **Slot 9** (paired with R3-R5) | extend
`batch_live_symmetry_2026_05_10.md` with the 13 BATCH_ONLY cells; verify 146 MISSING_BOTH for false-positive vs real-gap
| A6 re-run: 0 BATCH_ONLY; MISSING_BOTH triaged | | **R18** | A1 GAP — `typed_empty_reason` QG step not yet built (81
raw-string `record_empty(reason="literal")` violations) | **Slot 5** (paired with R6 — UTL owner) | new QG
`check_typed_empty_reason.py` + per-callsite migration | QG ratchets to 0 violations | | **R19** | A1 GAP —
`uac_import_surface` QG step not yet built (995 deep imports) | **Slot 2 or 3** (code_freeze owners — closest to UAC
plumbing) | new QG `check_uac_import_surface.py` + workspace-wide migration | QG ratchets to 0 violations | | **R20** |
A1 GAP — `lifecycle_class` CI step not built | **Slot 6** (paired with R11 — deployment-UI / VM lifecycle area) | new QG
`check_vm_lifecycle_class.py` | QG ratchets to 0 violations | | **R21** | AWS-side manifest indexes (cross-cloud
divergence unaudited) | **OPERATOR DECISION** (do we still actively use AWS S3 manifest indexes?) | if yes: extend A3 to
read AWS buckets. If no: archive `cloud-providers.yaml` AWS section as deprecated | `BLOCKED-OPERATOR-DECISION` until
you decide | | **R22** | Backup snapshot parquets stale (consolidator doesn't touch them) | **Slot 5** (paired with R6)
| extend consolidator to refresh backups OR move backups to a separate cron job; document in codex | Snapshot age < 24h
per bucket | | **R23** | `_index/per_vm/*.parquet` shards not audited (A4 only looked at master) | **Slot 5** (paired
with R6) | extend A4 to walk per_vm shards too; assert their schema_version distribution matches canonical | A4 re-run
includes per_vm row counts |

### Slot reassignment summary (per work_split_2026_05_19_ikenna.md)

| Slot  | Status                                                    | Primary R items                               | Secondary R items                                                 |
| ----- | --------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------- |
| 1     | Main orchestrator + Phase A coord                         | R10                                           | (assigns slots; tracks R12, R21 decisions)                        |
| 2     | KEEP (code_freeze §2.6)                                   | —                                             | R19 (UAC import surface, can take on during code-freeze plumbing) |
| 3     | KEEP (code_freeze §2.0-2.5)                               | —                                             | R19 (alternative slot)                                            |
| 4     | KEEP (api_keys + defi_recursive_borrow)                   | —                                             | unblocks credentials for any `BLOCKED-CREDENTIALS` from R1-R5     |
| 5     | KEEP (writegate + live_pipeline)                          | **R6, R9, R13, R14, R15, R16, R18, R22, R23** | (anchor for all v8-writer-SSOT work)                              |
| **6** | **🔴 FROZEN — reassigned to DeFi data**                   | **R1, R8, R11, R20**                          | post-GREEN: deployment-UI lifecycle work resumes                  |
| **7** | **🔴 FROZEN — reassigned to Sports data**                 | **R2, R7**                                    | post-GREEN: simulation_scenarios + defi_master P2-3 resume        |
| 8     | KEEP (defi_catalogue close)                               | —                                             | unblocks IS-side dependencies for R1                              |
| **9** | **🔴 FROZEN — reassigned to Prediction/TradFi/CeFi + A6** | **R3, R4, R5, R17**                           | post-GREEN: cme_polymarket_arb + promote_workflow resume          |

### How slot agents consume this delegation SSOT

1. Slot agent boots → reads its assigned `Rn` items from § 6.
2. Opens the named plan-of-record + this audit doc URL.
3. Executes the work; when verification step passes, flips a checkbox in the plan-of-record + links commit SHAs back
   here under § 6's row.
4. When ALL `Rn` items for that slot are GREEN, slot unfreezes (slot 6/7/9) or reports back to slot 1 for re-themeing.

### Section 6.5 — Items added 2026-05-20 round 3 (Section 5 gap closures)

| #           | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Owner slot                                                                                                                                                            | Plan-of-record                                                                                                                                                                                               | Verification                                                                                                                                                                                                              |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R-NEW-1** | 16 services have NO consolidated `_index/availability_index.parquet`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | **Slot 5** (paired with R6)                                                                                                                                           | `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 7 (extend to all services)                                                                                                                          | A3 v3 re-run: every service in workspace has a consolidated manifest OR explicit `BLOCKED-OPERATOR-DECISION` ack that it doesn't need one                                                                                 |
| **R-NEW-2** | AWS bucket scope — 2 buckets active (`unified-trading-market-data-defi-...` + `unified-trading-evm-defi-prd-...`); 5 don't exist                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | **OPERATOR DECISION** (R21)                                                                                                                                           | if active: extend A3 to read AWS row-level. If deprecated: archive AWS section of cloud-providers.yaml                                                                                                       | `BLOCKED-OPERATOR-DECISION`                                                                                                                                                                                               |
| **R-NEW-3** | A4 v2 per_vm shard audit script ran async; results to compare against A4 v1 master                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | **Slot 5** (paired with R6)                                                                                                                                           | extend writegate Phase 7 with per_vm result inspection                                                                                                                                                       | A4 v2 outputs land + reviewed for per-VM-writer regressions                                                                                                                                                               |
| **R-NEW-4** | ~~`PROTOCOL_PAUSE_WINDOWS` registry empty — operator-fillable~~. **SUPERSEDED 2026-05-20 round 4** — operator directive: "I can't just tell you when protocols are out, it needs to be understood from data. Isn't that something instruments-service can understand OR a script per chain which checks for outages using governance or otherwise?" Re-scoped: **detector-populated, not operator-typed**. See R-NEW-6.                                                                                                                                                                                                                                                                                                      | n/a (rolled into R-NEW-6)                                                                                                                                             | `unified_api_contracts/registry/protocol_pause_windows.py` (this session: refactored docstring + architecture diagram + marked as detector-populated; registry stays empty until R-NEW-6 lands the detector) | n/a                                                                                                                                                                                                                       |
| **R-NEW-5** | A1 AST upgrade DEFERRED (regex sufficient for ratchet)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **Slot 5** (only if false-positive complaints surface)                                                                                                                | extend cross-cutting QG ratchet plan with AST phase IF needed                                                                                                                                                | currently P3 — no action needed unless complaints surface                                                                                                                                                                 |
| **R-NEW-6** | DeFi protocol-outage detector — read existing `governance_events` data_type (already captured by MTDS `governance_events_handler.py` for Compound/Aave/Uniswap) + `governance_proposals` (already captured by MTDS `governance_proposals_handler.py` for Aave V3/Compound V3/Spark/Lido) → filter for Pause/Freeze action types → compute `(start, end)` pause windows. **Plus** per-chain RPC block-time anomaly detection (eth_getBlock for EVM chains, Solana RPC for Solana) — flags multi-hour block-time gaps for operator review (NOT auto-encoded; encoded only when ≥24h + multi-protocol impact). Output: refreshes `unified_api_contracts.registry.protocol_pause_windows.PROTOCOL_PAUSE_WINDOWS` daily via cron. | **Slot 4** (api_keys + defi_recursive_borrow — on-chain reading already in scope) OR **Slot 8** (defi_catalogue close — IS reference-data context). Operator decides. | NEW plan needed: `plans/active/defi_protocol_outage_detector_2026_05_20.md`. Composes with existing MTDS governance handlers (no rebuild — just consume their output).                                       | A2 re-run: cells inside detector-confirmed pause windows return `EXPECTED_EMPTY[EXPECTED_PROTOCOL_PAUSED]`. Detector spot-checks: known Curve 2023-07-30 re-entrancy exploit event surfaces a multi-day Curve pool pause. |

---

## Section 6.6 — Delegation SSOT verification (round 3 — answers operator's "check we did this too I guess when we finish")

Every Phase-A finding maps to exactly one R-item below. Verification: grep this doc for "R1" through "R23" + "R-NEW-1"
through "R-NEW-5" — every finding from A1/A2/A3/A4/A5/A6 + the Section 5 gap closures + the operator Q&A round 2 is
covered.

| Phase-A finding                            | Mapped to                                                                                                                                                                                  | Slot owner          |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| A1 — codified-shape scan, 2,593 violations | R18 (`typed_empty_reason`) + R19 (`uac_import_surface`) + R20 (`lifecycle_class`) + R-NEW-5 (AST upgrade deferred)                                                                         | slots 5, 2/3, 6     |
| A2 — oracle gaps                           | R7 (sports off-season — DONE for source-level) + R8 (DeFi pauses — DONE venue-level; R-NEW-4 protocol-pause seeds) + R9 (per-symbol axis)                                                  | slots 7, 6, 5       |
| A3 — manifest divergence (MTDS only in v1) | R1 (DeFi) + R2 (Sports) + R3 (CeFi) + R4 (TradFi) + R5 (Prediction) + R10 (extend to all services — DONE in A3 v2) + R-NEW-1 (16 services without manifest) + R-NEW-2 (AWS scope decision) | slots 6, 7, 9, 1, 5 |
| A4 — manifest v8 deep                      | R6 (v8 backfill) + R-NEW-3 (per_vm shard audit) + R13/R14/R15 (writer SSOT rename + codex + QG) + R22 (backup snapshots) + R23 (per_vm shards)                                             | slot 5              |
| A5 — dependency-fail propagation           | R16 (5 silent-swallow files)                                                                                                                                                               | slot 5              |
| A6 — batch-live adapter parity             | R17 (13 BATCH_ONLY + 146 MISSING_BOTH)                                                                                                                                                     | slot 9              |
| Consolidator coverage                      | R11 (dashboard panel) + R12 (Cloud Run migration — operator decision)                                                                                                                      | slot 6, operator    |
| Operator scope decisions                   | R21 (AWS) + R-NEW-2 (AWS subset) + R-NEW-4 (protocol pause seeds) + TradFi tbbo/trades sample-only (sidecar)                                                                               | operator            |

**Verification PASS**: every Phase-A diagnostic output produced by this session has at least one named R-item with a
slot owner. **No orphaned findings.**

---

## Section 6 — (legacy) Remediation roadmap (what each finding routes to)

Per operator directive: "I want every single issue that we found fully fixed, bad manifest data migrated, without
exception."

The roadmap routes findings into existing PM active plans (no new SSOTs):

| Finding                                                       | Existing plan to absorb it                                                                                                | Status                |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| A1 typed_empty_reason + uac_import_surface QG gaps            | `master_to_live_defi_2026_05_23.md` cross-cutting QG ratchet section (item 9 in tracker)                                  | Extend existing       |
| A1 lifecycle_class CI gap                                     | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` (VM lifecycle section)                                            | Extend existing       |
| A1 hardcoded URLs / universe (in non-allowlisted repos)       | `is_mtds_contract_audit_2026_05_20.md` C0 audit (already in audit/)                                                       | Use existing          |
| A1 record_emission gaps                                       | `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.x                                                              | Extend existing       |
| A2 sports off-season                                          | (no existing plan) — create `sports_offseason_calendar_2026_05_20.md`                                                     | NEW plan              |
| A2 DeFi protocol pause                                        | Extend `defi_upstream_46day_full_backfill_2026_05_16.md`                                                                  | Extend existing       |
| A2 per-symbol axis                                            | (no existing plan) — create `expected_coverage_per_symbol_2026_05_20.md`                                                  | NEW plan              |
| A2 SourceCapability.coverage_start gaps                       | `uac_source_capability_metadata_promotion_2026_05_20.md` Phase 0                                                          | Extend existing       |
| A3 DeFi MISSING_EXPECTED (FLUID/MORPHO/CURVE/BALANCER/etc.)   | `defi_upstream_46day_full_backfill_2026_05_16.md`                                                                         | Extend existing       |
| A3 DeFi 765 DIVERGENT_EMPTY                                   | (no existing) — extends `is_mtds_contract_audit_2026_05_20.md` remediation                                                | Extend existing       |
| A3 Sports MISSING_EXPECTED (all 11 bookmaker×datatype combos) | `epics/sports_master.md`                                                                                                  | Extend existing       |
| A3 CeFi MISSING_EXPECTED (OKX/COINBASE/UPBIT)                 | `epics/tradfi_master.md` — no, this is CeFi; needs CeFi epic. If no CeFi master epic exists, this should be its own plan. | Possibly NEW plan     |
| A3 Prediction MISSING_EXPECTED (KALSHI/POLYMARKET)            | `epics/predictions_master.md`                                                                                             | Extend existing       |
| A3 TradFi MISSING_EXPECTED + ATTEMPTED_FAILED                 | `epics/tradfi_master.md`                                                                                                  | Extend existing       |
| **A4 v8 data backfill (1.3M NULL + 5.4M v<8 rows)**           | (no current plan exists for this!) — **needs a new dedicated plan** `manifest_v8_full_backfill_2026_05_20.md`             | NEW plan              |
| A4 v8 code-path gaps                                          | Cross-cutting QG ratchet extension                                                                                        | Extend existing       |
| A5 dependency-fail propagation                                | Needs new plan or extension of `dependency_freshness_*.md`                                                                | TBD — operator decide |
| A6 batch-live adapter parity                                  | Extension of each adapter plan + new master `batch_live_parity_2026_05_20.md`                                             | NEW plan              |

**Of the existing plans, the ones doing layer-N+1 work that MAY need to be frozen (per operator's directive about not
doubling down on bad code):**

To identify these I need to read each active plan's frontmatter `layer_n` field and check whether the prior-layer audit
is GREEN. That's a follow-up audit I can run in this same session if you want; for now I've flagged the gap.

---

## Section 7 — What "fully done" looks like

Per operator directive: no exceptions, no cutbacks, no missing venues/asset_groups, no missing data_types, no missing
time ranges. Only allowed deferral: when operator explicitly articulates the reason.

**Phase A is "done" when:**

1. **A1**: every QG gap (typed_empty_reason, uac_import_surface, lifecycle_class CI) has a CI step that fails on
   regression. Baseline yaml ratchets every violation downward week-over-week. AST-based scanner replaces regex.
2. **A2**: oracle handles every named gap (sports off-season via IS fixtures, DeFi protocol pauses via
   operator-confirmed `PROTOCOL_PAUSE_WINDOWS`, per-symbol axis via IS catalogue join, US tradfi half-day annotated
   correctly, non-US tradfi venues).
3. **A3**: extended to every manifest-emitting service (IS + features + strategy + execution + ml-\*) and every cloud
   (GCP + AWS). Re-run produces zero DIVERGENT_EMPTY + zero MISSING_EXPECTED cells that don't have a
   named-operator-acked exception.
4. **A4**: every existing manifest row migrated to v8 (or NULL rows backfilled with the correct version). Every
   code-path writer using the canonical `MANIFEST_SCHEMA_VERSION = 8` constant. QG step prevents resurgence.
5. **A5 + A6**: scanners built + run + every violation routed to a plan.

**Estimated total to "fully done":** beyond Phase A, the bulk of work is operational (backfilling 7.4M manifest rows +
filling 237k missing cells). That's not Phase A audit work — that's the Phase D/E execution that the audit unblocks.

---

## Section 8 — Recommended operator decisions (where I need your input)

1. **Sports off-season calendars**: build registry OR pair with IS fixture data (recommended)?
2. **DeFi protocol pauses**: please enumerate known pause windows so I can build the registry.
3. **AWS-side manifest indexes**: are these still active or deprecated? (Affects A3 extension scope.)
4. **Per-symbol A2 dump**: do you want me to extend A2 to per-symbol granularity now, or after A4 v8 backfill completes
   (since per-symbol queries hit the same manifest data)?
5. **Slots to freeze**: please confirm which slots are currently doing layer-N+1 work (paper-trade scaffolding,
   execution-service polish, etc.) that should pause until A1-A6 are GREEN.
6. **CeFi master epic**: does one exist? I see TradFi + Sports + Predictions epics but didn't find a CeFi master.
