# Data-status drilldown + asset-group rename + manifest-429 — MASTER DISPATCH PROMPT

> Self-contained handover spanning three related rollouts. A fresh agent can execute all nine follow-ups end-to-end
> without re-investigating. Source rollouts:
>
> 1. **Data-status drilldown** (2026-04-24 → 2026-04-25) — UX gaps deferred from
>    `project_cross_category_audit_2026_04_25.md` + `project_data_status_institutional_drilldown_2026_04_25.md`. →
>    Follow-ups **A + B**.
> 2. **`asset_group` vocabulary rename** (`venue_axis_asset_group_vocabulary_2026_04_25.plan.md` Waves C + D,
>    `shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` Phase 0 + 3) — workspace-wide rename of the venue
>    axis. → Follow-ups **C + D + E**.
> 3. **Manifest-429 Phase 7 hardening** (`manifest_429_per_vm_sharding_2026_04_25.plan.md`) — four loose ends after
>    Phases 1-6 shipped (UTL `c95480de` + `d06a11d0`, deployment-service `1f8e29a`, MTDS `7825b83`+`8f6a5d5`). →
>    Follow-ups **F + G + H + I**.
>
> All nine are independent. Pick the order in [§ Order of execution](#order-of-execution) or fan out across multiple
> agents. The same touched code surfaces all three rollouts so executing them together amortises context cost.

## Context (read first)

**Already shipped (predecessor work):**

Drilldown UX foundation (2026-04-24 → 2026-04-25, ~10 commits):

- **unified-api-contracts** `cf79d54` — 11 new SchemaContracts + `ColumnSpec.required` +
  `ColumnSpec.provided_by_venues` + `validate_row_df` + enum-coverage test. `c7642f3` — 3 new PREDICTION SchemaContracts
  (`book_snapshot`, `market_metadata`, `fills`).
- **unified-trading-library** `f40481d7` — opt-in `validate_df` + `MANIFEST_WRITE_SCHEMA_MISMATCH` event. `d8d5f22c` —
  strict-mode flip to True default.
- **deployment-api** `9d93236` — `/api/data-status/shard-detail` + `/venue-detail` + 4 shard classes + DeFi-aware
  lookup. `daf15ec` — `instrument_type=AUTO` resolver. `93fc3cf` — instrument search backend. `c83821d` —
  `build_pool_breakdown` + `/api/data-status/pools/breakdown` route. `5afd182` — venue-detail e2e (alias resolution +
  nested partition + recent-days probe). `6a80956` — JSON-safe sanitizer + 404 on missing CSV.
- **deployment-ui** `f4a8e4e` — ShardDetailModal + clickable dates + VenueDetailPanel. `0caf2cc` — DeFi click passes
  `instrument_type=AUTO`. `2ebe1dc` — `searchInstruments` client. `ffba379` — Symbol Search Card UI. `4472cd5` —
  `getPoolBreakdown` client.
- **unified-trading-pm** `e3c0d970` — codex doc `data-status-drilldown.md`.

Manifest-429 Phase 1-6 (parent plan for F-I):

- **unified-trading-library** `c95480de` — per-VM writer + reader fallback. `d06a11d0` — manifest consolidator.
- **deployment-service** `1f8e29a` — `MANIFEST_PER_VM_SHARDS=true` flag in `setup-data-pipeline-vm.sh`.
- **market-tick-data-service** `7825b83`+`8f6a5d5` — adapter call-site updates.

**Vocabulary rule** (per `instruments-service/.claude/CLAUDE.md` and the
`venue_axis_asset_group_vocabulary_2026_04_25.plan.md` SSOT): the venue axis is **`asset_group`**, not `category`. New
code uses `asset_group` everywhere. Two intentional exceptions:

- Dict KEYS stay lowercase (`cefi` / `defi` / `tradfi` / `sports` / `prediction`).
- GCS path segments stay literal (`category=cefi/...` blob prefixes — wire-format SSOT).

The user-facing API params and Python kwargs use `asset_group`. Older code that still says `category` is on a separate
refactor wave; do not refactor it as part of these follow-ups.

**Reference memory files:**

- `reference_data_status_canonical_sources.md` — bucket families + canonical-ID source per asset_group + DeFi
  venue+chain combined partition + schema-adaptive parquet read pattern + `list_prefixes` bug workaround.
- `feedback_prek_restores_patch_on_failure.md` — pre-commit re-stage pattern.
- `project_cross_category_audit_2026_04_25.md` — what shipped 2026-04-25 + commit map.
- `project_data_status_institutional_drilldown_2026_04_25.md` — UAC schema backfill + ColumnSpec extension +
  ManifestWriter validation + shard-detail endpoint + ShardDetailModal + e2e fix for all 5 asset_groups.

**Reference plans:**

- `unified-trading-pm/plans/active/manifest_429_per_vm_sharding_2026_04_25.plan.md` — parent for F + G + H + I. Read the
  pre-audit manifest of writer/reader call sites before touching G.
- `unified-trading-pm/plans/active/venue_axis_asset_group_vocabulary_2026_04_25.plan.md` — parent for C + D. Lists the
  canonical UAC symbols (`VENUE_TO_ASSET_GROUP` etc.).
- `unified-trading-pm/plans/active/shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` — parent for E. ADR
  `unified-trading-pm/codex/11-project-management/decisions/adr-2026-04-25-category-and-asset-group-field-naming.md` is
  the authoritative naming-rule SSOT.

---

## Follow-up A — DeFi pool-breakdown UI modal

### Goal

Wire the existing `/api/data-status/pools/breakdown` endpoint (deployment-api `c83821d`) into the deployment-ui so users
can drill from a DEFI venue row down to per-pool coverage. The backend + tested client (`getPoolBreakdown` in
`src/api/client.ts`) already exist — this task is purely the UI surgery on `DataStatusTab.tsx`.

### Acceptance criteria

1. On any DEFI venue row in the data-status tree (e.g. `UNISWAP_V3-ETHEREUM`, `EIGENLAYER-ETHEREUM`,
   `BALANCER-POLYGON`), a compact "pools" link or icon appears next to the existing "schema" affordance.
2. Click → opens a modal (mirror the existing `setSchemaModal` pattern at `DataStatusTab.tsx` ~L4327) showing:
   - Title: `Pool breakdown · {VENUE}-{CHAIN} · {DAY}` (use the most recent day with data —
     `data_status_drilldown.py:_latest_available_day` pattern, but on the DeFi tick bucket, not instruments-store).
   - For each pool row: `pool_id` (truncated to ~40 chars with full ID in tooltip), per-`data_type` coverage badge
     (colour-coded green / amber / red / grey for `captured` / `empty_confirmed` / `missing` / `failed`), and a
     coverage_summary count tally.
   - Empty-state: "No pool data for this (venue, chain) on {DAY}" when response `status === "no_data"`.
3. Loading state: spinner while fetching (the cold first call hits multiple parquets so 5-15s is realistic; reuse the
   `Loader2` pattern from the existing schema modal).
4. Truncation: cap visible pools at 100 with a "+ N more" footer (DeFi shards can have hundreds of pools per day for
   UNISWAP_V3).
5. New `data-testid="defi-pools-modal"` + `data-testid="defi-pool-row-{pool_id}"` for Playwright.

### Files to touch

- `deployment-ui/src/components/DataStatusTab.tsx` — venue-row rendering loop. Find the DEFI branch
  (`asset_group === "DEFI"` or whatever the current selector is — vocabulary may still say `category`). Add a "pools"
  button next to the existing "schema" button (added 2026-04-24, `8054637`).
- New state: `setPoolBreakdownModal({venue, chain, day})` + `poolBreakdownData` result cache.
- Optional: extract the modal into `src/components/PoolBreakdownModal.tsx` if `DataStatusTab.tsx` is too big (it's
  already >5000 lines).

### Tests

- Vitest unit test for the modal component: render with mocked `getPoolBreakdown` response, assert pool rows + coverage
  badges + truncation footer.
- Playwright smoke (after Vite restart): click DEFI venue's "pools" button → modal opens → at least one pool row
  renders.

### Live verification

After UI changes, restart deployment-api + Vite, then drive Playwright:

1. Navigate `localhost:5183` → instruments-service → Data Status tab.
2. Click `Check Status`, wait for SPORTS+DEFI manifest to render.
3. Find DEFI category, expand a venue (e.g. `EIGENLAYER-ETHEREUM`).
4. Click the new "pools" button.
5. Assert modal renders with pool_id `EIGENLAYER-ETHEREUM:REWARDS:RESTAKING` and `coverage: {rewards: "captured"}`.

---

## Follow-up B — PREDICTION manifest enumeration

### Goal

Make the 3 new PREDICTION SchemaContracts (`book_snapshot`, `market_metadata`, `fills`) appear as expected rows in the
deployment-ui PREDICTION manifest panel. Today only `trades` is enumerated — the new contracts resolve via
`/api/data-status/schema` but don't surface as "expected denominator" rows in the manifest tree.

### Root cause

For SPORTS, the `SPORTS_DATA_TYPE_META` dict in `deployment-api/deployment_api/services/data_status_service.py` declares
the canonical denominator (which data_types should exist per league × venue × day). PREDICTION has no equivalent — it
just shows whatever the manifest parquet contains. The 3 new data_types have no rows in the manifest yet
(forward-looking schemas), so they don't appear at all.

### Acceptance criteria

1. Add `PREDICTION_DATA_TYPE_META` (or `PREDICTION_PRED_MARKET_DATA_TYPE_META` if the asset_group naming is too generic)
   to `deployment-api/deployment_api/services/data_status_service.py` with entries for:
   - `trades` (existing — 6-dim shard: data_source × venue × chain × market_category × underlying × market_type ×
     resolution_period)
   - `book_snapshot` (CLOB API; same shard; `condition_id`-keyed)
   - `market_metadata` (Gamma API; per-day-per-venue catalogue; `condition_id`-keyed)
   - `fills` (Data API; same shard as trades; `condition_id`-keyed)
2. Wire `PREDICTION_DATA_TYPE_META` keys into the manifest enumeration loop (mirror the SPORTS path at
   `data_status_service.py:3499`-ish with the `manifest_dt_vals | sports_ssot_vals` union — find the equivalent for
   prediction).
3. UI: PREDICTION row in the manifest panel shows 4 data_types (was 1). `book_snapshot` / `market_metadata` / `fills`
   show 0% captured (no parquets yet) but appear as expected rows so the SSOT gap is visible.
4. Full QG (`bash scripts/quality-gates.sh`) green on UAC + deployment-api.

### Files to touch

- `deployment-api/deployment_api/services/data_status_service.py` — add the new META dict + wire into the prediction
  manifest enumeration path.
- `deployment-api/tests/unit/test_data_status_service.py` — add a parametrised test verifying all 4 PREDICTION
  data_types appear in the manifest response under PREDICTION asset_group.
- Playwright assertion: PREDICTION panel shows 4 data_type rows after refresh.

### Open question to decide before coding

What's the right "expected" cardinality per data_type? For SPORTS, each sport data_type's denominator is
fixture-day-based or league-day-based. For PREDICTION:

- `trades` and `fills` are open-market (any active condition can have trades; cardinality varies wildly).
- `book_snapshot` is per-(condition_id, asset_id, snapshot_time); cardinality is hard to bound without a
  "expected_active_markets" count.
- `market_metadata` is one row per active market per day — finite, can enumerate via Polymarket Gamma API daily.

**Pragmatic call**: for `book_snapshot` / `market_metadata` / `fills` set `expected_count_per_day = "indeterminate"`
(matches SFI_PROGRESSIVE_STATS pattern in SPORTS_DATA_TYPE_META) so the UI just shows captured count without an
arbitrary denominator. Document the decision in the META dict's docstring.

### Tests

- Unit test: stub the manifest response, assert all 4 PREDICTION data_types appear in the rendered category breakdown.
- Live API: hit `/api/data-status/manifest?asset_group=PREDICTION` after the change, confirm `data_types` keys include
  all 4.

---

## Follow-up C — Wave C: features-\* services adopt `asset_group` symbols

### Goal

Roll the workspace-wide `category` → `asset_group` rename (parent plan
`venue_axis_asset_group_vocabulary_2026_04_25.plan.md`) into the seven feature services. UAC already exports
`VENUES_BY_ASSET_GROUP` / `DATA_TYPES_BY_ASSET_GROUP` / `VENUE_TO_ASSET_GROUP` (Wave A `c8d1f4` etc., shipped). Wave C
is the consumer step: each features service imports those symbols and renames local helpers + variable names
accordingly.

### Acceptance criteria

1. For every features service in this list:
   - `features-cross-instrument-service`
   - `features-delta-one-service`
   - `features-onchain-service`
   - `features-sports-service`
   - `features-volatility-service`
   - `features-multi-timeframe-service`
   - `features-commodity-service`
   - `features-calendar-service`

   Replace any local `_category` / `category_for_venue` / `CATEGORIES` helpers with imports from
   `unified_api_contracts.VENUE_TO_ASSET_GROUP` / `VENUES_BY_ASSET_GROUP`. Keep dict KEYS lowercase (`cefi` / `defi` /
   `tradfi` / `sports` / `prediction`) per the vocabulary rule.

2. Rename Python kwargs and CLI flags from `category` to `asset_group`.
3. Leave GCS path literals (`category=cefi/...`) untouched — those are wire-format SSOT and out of scope.
4. Each service's `bash scripts/quality-gates.sh` green.

### Files to expect

`rg "VENUE_TO_CATEGORY|category_for_venue|CATEGORIES\s*=" features-*` will surface the local helpers. Replace with the
UAC facade import.

### Tests

Existing service unit tests should pass as-is — the helpers change implementation but keep behaviour. If a test asserts
the literal string `"category"`, update it to `"asset_group"`.

### Watchouts

- Schema-provenance gate (QG-enforced) requires types come from UAC. When you import `VENUE_TO_ASSET_GROUP`, do it from
  the UAC facade (`from unified_api_contracts import VENUE_TO_ASSET_GROUP`), never from internal paths.
- If a service has a config reloader pattern that loads a `Set[Literal["CEFI", "DEFI", ...]]` typed alias, switch the
  alias source to `MarketAssetGroup` from UAC.

---

## Follow-up D — Wave D: execution-service / consumer JSON keys

### Goal

execution-service and any client consuming its CLI / gRPC payloads currently emit a JSON field literal `category`. The
vocabulary SSOT (`adr-2026-04-25-category-and-asset-group-field-naming.md`) gives two permitted resolutions per
consumer:

1. **Migrate** — flip the JSON key to `asset_group`, keep `category` as a pydantic `validation_alias` for one release,
   then drop.
2. **Document** — note the consumer is grandfathered on `category` for wire-format reasons (e.g. an external
   counterparty integration we don't control).

Each consumer picks one. Default to migrate unless there's a contractual reason not to.

### Acceptance criteria

1. Audit every JSON / CLI / gRPC surface in `execution-service` and adjacent consumers (search:
   `rg '"category"\s*[:=]' execution-service strategy-service position-balance-monitor-service risk-and-exposure-service`).
2. For each surface, choose **migrate** or **document**:
   - **Migrate**: rename emit-side to `asset_group`, add `category` as `validation_alias=AliasChoices("category")` for
     one release. Update consumer side to read `asset_group` first, fall back to `category`.
   - **Document**: add a one-line comment at the surface citing the reason
     (`# wire-format pinned: <counterparty> contract requires "category"`).
3. Update `/codex/13-codex-governance/SSOT-BOUNDARY.md` "renames in flight" table with the migrated surfaces.
4. Each touched repo's QG green.

### Test gate

For **migrate** surfaces: a unit test asserting the surface accepts BOTH `{"asset_group": "CEFI"}` and
`{"category": "CEFI"}` (deprecation window). For **document** surfaces: a regression test pinning the `"category"`
literal so future agents don't silently break the wire format.

### Watchouts

- Strategy-service `signal_emit` has a counterparty-facing wire format — almost certainly **document** not migrate.
  Check `signal_broadcast.WebhookPayload` for the lock.
- The single-mapper-at-the-API-boundary option from the ADR is still open; if you discover ≥ 5 consumers all needing
  migration, push the rename DOWN to UAC `BaseRequest` so every consumer flips together.

---

## Follow-up E — Shard dimension SSOT closeout

### Goal

Close out `shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` — two open Phase 0 / Phase 3 items remain. The
earlier phases shipped (UI

- deployment-api + deployment-service all flipped to `asset_group` for the shard dimension). The trailing items are
  external-reader confirmation
- SIT coverage.

### Acceptance criteria

1. **Phase 0 ENG audit**: confirm no production reader (external HTTP consumer of `/api/data-status/...`, or another
   internal service) still keys off the JSON literal `category` for the shard-filter dimension. Search:
   - `gh code-search "filters\\['category'\\]" --owner IggyIkenna`
   - `rg '"category"' system-integration-tests e2e-testing` Document findings (`category` is fully retired vs
     grandfathered) in the plan's Phase 0 todo.
2. **Phase 3 SIT**: update `system-integration-tests` deployment / shard dry-run tests to assert `filters` carries
   `"asset_group": "..."` not `"category": "..."`. Update fixtures in `tests/fixtures/`.
3. **Phase 3 staging smoke**: run a staging deploy-missing dry-run that exercises the new dimension key end-to-end.
   Assert the deployment-service log line says `dim=asset_group` not `dim=category`.
4. Flip the plan's `completion_gates.code` from `C5` to whatever the archive criterion is, and the touched repo gates
   from `C0` per the matrix.

### Files

- `system-integration-tests/tests/integration/test_shard_calculation*.py`
- `system-integration-tests/tests/fixtures/deployment_request_*.json`
- `unified-trading-pm/plans/active/shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` — tick the boxes once
  confirmed.

---

## Follow-up F — Refresh tarballs + setup script in GCS

### Goal

The new UTL per-VM-write code (commits `c95480de` + `d06a11d0`) and the `MANIFEST_PER_VM_SHARDS=true` flag in
`deployment-service/scripts/vm/setup-data-pipeline-vm.sh` are committed but not yet on GCS. Any next VM launch (backfill
/ forward-poll / smoke) pulls stale code from `gs://deployment-scripts-central-element-323112/`. This is pure ops — no
code changes — but it gates everything downstream of Phase 6.

### Acceptance criteria

1. Re-tarball every repo:

   ```bash
   cd /Users/ikennaigboaka/Code/unified-trading-system-repos/deployment-service
   bash scripts/vm/create-code-tarballs.sh --all
   ```

   On macOS use `/opt/homebrew/bin/bash` if bash 3.2 chokes on `${2^^}`.

2. Verify the new UTL tarball includes the consolidator module:

   ```bash
   gsutil cp gs://deployment-scripts-central-element-323112/code/unified-trading-library-code.tar.gz /tmp/utl.tar.gz
   tar -tzf /tmp/utl.tar.gz | grep manifest_consolidator
   ```

   Must show `unified_trading_library/manifest_consolidator.py`.

3. Push the updated boot script:

   ```bash
   gsutil cp deployment-service/scripts/vm/setup-data-pipeline-vm.sh \
     gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh
   ```

   Spot-check:

   ```bash
   gsutil cat gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh \
     | grep MANIFEST_PER_VM_SHARDS
   ```

   Must show `export MANIFEST_PER_VM_SHARDS="${MANIFEST_PER_VM_SHARDS:-true}"`.

4. Smoke-launch ONE small VM (cheapest possible — 5-day CeFi backfill or a single-day instruments-service VM). Confirm
   via `run.log`:
   - Tarball checksum matches the freshly uploaded one.
   - `MANIFEST_PER_VM_SHARDS=true` shows in the env.
   - First `ManifestWriter` call lands at `_index/per_vm/{vm-name}.parquet`, **NOT**
     `_index/availability_index.parquet`.
   - One consolidator cycle (within 60s) shows the row in the consolidated blob.

5. Reap the smoke VM (`gcloud compute instances delete <name> --zone <zone>`).

### Watchouts

- The `--all` flag is mandatory — bare `create-code-tarballs.sh` only re-tars CORE (UAC/UTL/MTDS/deployment-service) and
  silently runs stale code for the rest. SSOT: `/codex/05-infrastructure/vm-tarball-deployment.md`.
- If you launch a CeFi smoke VM, use a small year-range (single year or even 5 days). The asset_group flag is
  `--asset-group CEFI` per the new vocabulary.

---

## Follow-up G — UTL version floor bumped across 25 consumers

### Goal

UTL changes (`c95480de` per-VM writer + reader fallback, `d06a11d0` consolidator) are live on
`origin/live-defi-rollout`. Downstream services need `unified-trading-library>=` bumped in their `pyproject.toml` so
they pull the new code. Semver-rollout-bot normally fires automatically on merge to staging or main.

### Acceptance criteria

1. Check the UTL version in `unified-trading-library/pyproject.toml` — note the current shipped version (call it
   `<UTL_NEW>`).

2. Audit every consumer's version floor:

   ```bash
   for repo in instruments-service market-tick-data-service features-sports-service \
               features-onchain-service features-delta-one-service features-volatility-service \
               features-multi-timeframe-service features-cross-instrument-service \
               features-commodity-service features-calendar-service \
               ml-training-service ml-inference-service \
               strategy-service risk-and-exposure-service execution-service \
               pnl-attribution-service alerting-service market-data-processing-service \
               position-balance-monitor-service deployment-service deployment-api \
               unified-config-interface unified-cloud-interface; do
     echo "=== $repo ==="
     grep "unified-trading-library" \
       /Users/ikennaigboaka/Code/unified-trading-system-repos/$repo/pyproject.toml | head -2
   done
   ```

3. If `semver-rollout-bot` has NOT fired since `c95480de`/`d06a11d0` landed, **do NOT manually bump** (workspace rule:
   "NEVER bump versions manually"). Trigger the workflow:

   ```bash
   gh workflow run semver-agent.yml --repo IggyIkenna/unified-trading-library
   gh run list --repo IggyIkenna/unified-trading-library --workflow=semver-agent.yml --limit 5
   ```

4. Once UTL ships a new version, confirm the floor PR appears in each consumer (via `update-dependency-version.yml`). If
   any consumer is missing, dispatch manually:

   ```bash
   gh workflow run update-dependency-version.yml \
     --repo IggyIkenna/<consumer> \
     -f dep=unified-trading-library \
     -f version=<UTL_NEW>
   ```

5. Verify drift-free:

   ```bash
   bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh
   ```

### Watchouts

- This is workflow dispatch, not code — no commits in the consumer repos unless something fails the auto-PR path.
- If a consumer's pyproject has `unified-trading-library = ">=X.Y.Z"` with a floor that's already below the new version,
  the workflow opens a bump PR. If the floor is exact-pin (`=="X.Y.Z"`), that's a separate rule violation — flag in the
  report rather than fixing it ad-hoc.

---

## Follow-up H — Consolidator-vs-consolidator race (UTL sentinel lock)

### Goal

`manifest_consolidator_scheduler.tf` fires `*/1 * * * *` per bucket. If a cycle exceeds 60s (large bucket, GCS hiccup),
the next cron starts a second consolidator on the same bucket. Both call `_write_consolidated()` which uses
generation-match CAS — one wins, the other CAS-fails and retries up to 4 attempts. Wasted work, not broken, but adds
noise.

**Picked: Option B — sentinel-blob soft lock** (simplest + self-healing via TTL).

### Acceptance criteria

1. Edit `unified-trading-library/unified_trading_library/manifest_consolidator.py`:
   - Add `_acquire_lock(client, bucket) -> bool` that writes `_index/consolidator.lock` with `if_generation_match=0` and
     a JSON body `{"started_at": <iso>, "instance": "<pid>-<rand>"}`.
   - Add `_release_lock(client, bucket)` that deletes the lock blob.
   - At the top of `consolidate(bucket)`:
     - Read the lock blob if present; if `started_at` is < 90s old, log INFO and return
       `ConsolidationReport(success=True, no_op_lock=True, error_reason="locked")`.
     - Otherwise call `_acquire_lock`. If that returns False (race lost to a sibling cron), same no-op return.
   - At the end of the cycle (success or failure path), call `_release_lock`.
   - Add `ConsolidationReport.no_op_lock: bool = False`.

2. Stale-lock recovery: if a previous run crashed and left the lock, the 90s TTL ensures the next cycle proceeds.

3. Tests in `unified-trading-library/tests/unit/test_manifest_consolidator.py`:
   - `test_acquire_lock_skips_when_recent_lock_exists` — sentinel timestamp 30s ago → consolidate returns
     `no_op_lock=True`.
   - `test_acquire_lock_recovers_from_stale_lock` — sentinel 600s ago → consolidate proceeds normally.
   - `test_lock_released_on_success_and_failure` — lock blob deleted in both code paths.

4. UTL `bash scripts/quality-gates.sh` green; existing 78 manifest tests still pass.

### Verification

After commit, run two consolidator cycles back-to-back via:

```bash
gcloud run jobs execute prod-manifest-consolidator-instruments-cefi \
  --region asia-northeast1 --wait
```

twice in parallel. Confirm one logs `no_op_lock=True`.

### Watchouts

- The lock writes use `if_generation_match=0` — that's the GCS pattern for "create only if doesn't exist". Both
  simultaneous acquirers can't both succeed; whichever loses gets a `412 Precondition Failed` and treats it as a
  lock-already-held no-op.
- Don't widen scope: this is just the consolidator. The writer-side concurrency (multiple VMs writing different per-VM
  shards simultaneously) is unchanged — that's already safe by per-VM-shard design.

---

## Follow-up I — Reader staleness window for self-writer-then-read (UTL)

### Goal

When a writer-VM writes to its own per-VM shard then immediately calls `read_availability_index(bucket)`, the read
returns the FRESH consolidated blob (because it's < 120s old) and silently misses the just-written row. Real-world
consequence: adapter pre-flight skip-if-exists checks could decide to re-process a date the SAME VM just captured. Not a
correctness bug (write wins next consolidator cycle, eventual consistency holds) but surprising for operators.

**Fix**: when per-VM mode is on, the reader also merges in `_index/per_vm/{my_instance}.parquet` regardless of
consolidated freshness, so the writer always sees its own writes.

### Acceptance criteria

1. Edit `unified-trading-library/unified_trading_library/manifest_writer.py`:
   - In `read_availability_index(bucket)` per-VM branch (after the consolidated blob is loaded), also load
     `_index/per_vm/{my_instance}.parquet` where `my_instance = _resolve_instance_id()`.
   - If both exist, merge via `_merge_shard_frames` so the reader sees a consolidated-plus-self view.
   - Keep `_INDEX_CACHE` TTL at 60s (no change).

2. Edge cases:
   - `_index/per_vm/{my_instance}.parquet` doesn't exist → return consolidated unchanged (no extra I/O cost beyond the
     existence check).
   - Same instance row appears in BOTH consolidated AND own shard → dedup keeps the latest `attempted_at` (already
     handled by `_merge_shard_frames` after the Phase 2 fix).
   - Multi-process workers in one VM share `VM_NAME` → they share a shard, not a problem.

3. Tests in `unified-trading-library/tests/unit/test_manifest_writer_per_vm.py`:
   - `test_reader_includes_self_shard_when_consolidated_fresh` — set `VM_NAME=vm-X`, consolidated has row A (5s old),
     `per_vm/vm-X.parquet` has row B → reader returns BOTH A + B.
   - `test_reader_dedups_self_shard_against_consolidated` — same row in both, latest `attempted_at` wins.
   - `test_reader_falls_back_to_self_when_consolidated_missing` — consolidated absent, `per_vm/vm-X` exists → returns
     vm-X rows only.

4. **Update existing test**: `test_reader_uses_consolidated_when_fresh` previously asserts `list_blobs` is NOT called.
   That assertion is no longer correct — now the reader WILL list `per_vm/{my_instance}.parquet` (one file). Adjust to
   assert exactly one file is read (just the self-shard), not the full per-VM listing.

5. UTL `bash scripts/quality-gates.sh` green.

### Verification

The Follow-up F smoke VM is the live verification: after the VM writes its first shard, it should read its own writes
back within seconds — without waiting for the consolidator cycle.

---

## Order of execution

Nine follow-ups across three rollouts. They're disjoint — pick any ordering. Suggested order by **risk-adjusted
impact**:

### Pre-requisite (manifest-429 unblocks the next VM launch)

1. **Follow-up F** (~30 min ops) — refresh tarballs + setup script in GCS. Pure ops, no code. Without this, every
   subsequent VM launch silently runs stale code. **Do this first if any other follow-up needs to launch a VM.**

### Code-light, high-value

2. **Follow-up B** (~1-2 hours) — one Python file + one test. Closes PREDICTION SSOT visibility gap.
3. **Follow-up I** (~1-2 hours) — UTL reader merges self-shard. 4 tests, one existing test to update.
4. **Follow-up H** (~2-3 hours) — UTL consolidator sentinel lock. 3 new tests, no consumer impact.
5. **Follow-up G** (~30 min - 2 hours wall-clock, mostly waiting for workflow runs) — version-floor sweep across 25
   consumer repos. Workflow-dispatch only.

### Code-heavy, longer

6. **Follow-up E** (~2-3 hours) — audit + SIT smoke; closes the shard dimension SSOT plan.
7. **Follow-up A** (~2-4 hours) — UI surgery on `DataStatusTab.tsx` (5000+ line file but well-scoped).
8. **Follow-up C** (~3-5 hours) — cross-service rename across 8 features services. Parallelisable per service.
9. **Follow-up D** (~3-6 hours) — wire-format decisions per surface; needs ADR-aware judgement, do last.

### Disjoint groupings

- **Drilldown UX** (A + B): can ship without any of C-I.
- **Asset-group rename** (C + D + E): can ship without any of A/B/F-I.
- **Manifest-429 hardening** (F + G + H + I): F is purely ops; G, H, I are UTL-only with no consumer cascade. F unlocks
  any further VM-based verification across the board.

If you're a fresh agent and want one-pass execution, run the order above top-to-bottom; F first guarantees subsequent VM
smokes use the right code.

## Definition of done

### Per-follow-up

- All shipped follow-ups committed + pushed to `origin/live-defi-rollout`.
- All new tests passing; full QG green on touched repos (`bash scripts/quality-gates.sh`).
- Live Playwright verification of:
  - PREDICTION panel showing 4 data_types (Follow-up B).
  - DEFI pool breakdown modal opening on a venue row click and rendering real pool coverage data (Follow-up A).
- For C / D / E: completion gates flipped on the parent plans (`venue_axis_asset_group_vocabulary_2026_04_25` Waves C /
  D ticked; `shard_dimension_naming_asset_group_ssot_2026_04_25` Phase 0 + 3 ticked).
- For F: smoke VM run.log shows tarball checksum match + `MANIFEST_PER_VM_SHARDS=true` + first write to
  `_index/per_vm/...`.
- For G: `run-version-alignment.sh` reports drift-free.
- For H: two parallel consolidator job invocations — one logs `no_op_lock=True`.
- For I: smoke VM (from F) self-write-then-read sees the fresh row before the next consolidator cycle.

### Plan closeout

- Update `manifest_429_per_vm_sharding_2026_04_25.plan.md` — flip Phase 6 / 7 todos to `[x]`, remove `locked_by` /
  `locked_since` if all todos done, commit with `[unlock-plan]` in the message.
- Update `venue_axis_asset_group_vocabulary_2026_04_25.plan.md` — Waves C / D ticked.
- Update `shard_dimension_naming_asset_group_ssot_2026_04_25.plan.md` — Phase 0 + 3 ticked, gates flipped.

### Memory

- One memory entry per shipped follow-up linked from `MEMORY.md` summarising what shipped + commit hashes. Mirror the
  `project_cross_category_audit_2026_04_25.md` shape — under 200 chars per `MEMORY.md` index entry; detail in the topic
  file.

### Final report

Under 600 words at end of session summarising which acceptance gates passed and which (if any) need a follow-up session.
Per-follow-up status table with commit SHAs.

## Watchouts (lessons from the parent sessions)

### Drilldown-specific (A + B)

- **prek pre-commit hook** can stash + restore your changes via `~/.cache/prek/patches/` when auto-format runs. Re-stage
  and retry rather than `--no-verify`.
- **list_prefixes** has a delimiter-handling bug for non-FUSE GCS — use `list_objects(...)` with manual partition
  parsing for `day=` enumeration. The data-status drilldown work hit this; the workaround is in
  `deployment_api/services/shard_detail.py:_list_day_prefixes` which bypasses the UCI wrapper and uses
  `google.cloud.storage` directly for delimiter listings.
- **Date-walk vs full prefix scan**: full prefix listing on the SPORTS bucket times out at 60s+. Use the recent-days
  probe pattern from `_pick_latest_day` (forward 30 days + back 120 days) instead.
- **Concurrent agents** may have edits in your working tree (e.g. `data_status_service.py` had concurrent enumeration
  refactor when this audit shipped). Use the isolate-commit pattern: backup file → checkout HEAD → apply only your edit
  → commit → restore backup unstaged.

### Manifest-429-specific (F + G + H + I)

- **Tarball-stale-code is silent**: every VM launch reads from `gs://deployment-scripts-.../code/` blindly. Forgetting
  Follow-up F silently runs old code with no error. SSOT: `/codex/05-infrastructure/vm-tarball-deployment.md`.
- **Bare `create-code-tarballs.sh` only re-tars CORE** (UAC / UTL / MTDS / deployment-service). The `--all` flag is
  mandatory for any multi-repo feature. `--asset-group SPORTS|CEFI|TRADFI|DEFI|PREDICTION` scopes to one asset_group's
  pipeline.
- **macOS bash 3.2 chokes on `${2^^}`** in `create-code-tarballs.sh` — use `/opt/homebrew/bin/bash` (bash 4+).
- **Never bump versions manually** — semver-rollout-bot opens floor PRs. If it's stuck, dispatch the workflow rather
  than editing `pyproject.toml` by hand.
- **Concurrent consolidator cycles** can both succeed via generation-match CAS but waste work. Sentinel-lock with 90s
  TTL is the fix; option C (cron interval to `*/2`) is the bypass if the sentinel pattern feels overweight.
- **Self-writer-then-read consistency**: `_INDEX_CACHE` TTL is 60s and consolidator runs at `*/1`, so the staleness
  window is 60-120s. Reader merging the self-shard closes it without disturbing other readers.

### Vocabulary-specific (C + D + E)

- **`asset_group` not `category`** in new code; legacy uses are on separate waves. Two intentional exceptions: dict KEYS
  stay lowercase (`cefi` / `defi` / `tradfi` / `sports` / `prediction`), and GCS path segments stay literal
  (`category=cefi/...` blob prefixes — wire-format SSOT).
- **DeFi composite venues** use `<PROTOCOL>_V<N>-<CHAIN>` in UAC + UI (`AAVE_V3-ETHEREUM`) but `<PROTOCOL>V<N>-<CHAIN>`
  in GCS partition layout (`AAVE_V3-ETHEREUM`). The deployment-api shard_detail handles this via
  `_venue_aliases_for_bucket`. Any code that builds GCS paths from a UI-supplied composite venue must apply the same
  aliasing.
- **SPORTS partition key is `league=` not `venue=`** at the top level, with a nested
  `venue=<data_provider>/instruments.parquet` underneath. See `_partition_key_for_category` and the nested fallback in
  `_read_instruments_day_df` — replicate the pattern for any new sports reader.
- **UAC working-tree may have a broken import** (`from unified_api_contracts.internal.asset_group import MarketCategory`
  — module doesn't exist; concurrent agent's WIP). If your tests can't collect because of it, the canonical fix is
  `market_category` not `asset_group`; sed the one-liner to unblock and let the WIP owner finish their wave.
- **Schema-provenance gate**: every domain type must come from UAC. When importing the new asset-group symbols in
  features-\* services, use the facade (`from unified_api_contracts import VENUE_TO_ASSET_GROUP`), never deep paths.
