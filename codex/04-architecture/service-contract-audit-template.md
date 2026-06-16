---
scope: [engineer]
status: stable
last_reviewed: 2026-05-20
source: B1 lift from is_mtds_contract_audit_2026_05_20.md (mega audit 2026-05-20)
---

# Service-Contract Audit — Reusable Template

> Use this template for every upstream→downstream pair in the C-series audits (C1–C11). Instantiate it in
> `plans/audit/<upstream>_<downstream>_contract_audit_<date>.md`. Each section corresponds to one of the 7 reusable
> architectural patterns.
>
> The template drives the **4-dimensional audit matrix** that surfaces the actual state of the contract for the pair
> being examined. Run the grep recipes BEFORE writing any remediation; paste the output as evidence in each Dim section.
>
> Post-audit the **QG-ratchet phase** converts findings into enforced checks so the contract never drifts again. The
> **continuous-verification column** wires each check into an always-on monitor.

---

## 0. Header block (fill per audit)

```yaml
pair: <upstream> → <downstream>
auditor: <slot / github handle>
audit_date: <YYYY-MM-DD>
audit_file: plans/audit/<slug>_contract_audit_<date>.md
feeds_ordering_step: <list of ordering steps from mega_audit_and_plan_beefup_progression_2026_05_20.md §Phase D>
status: in-flight | complete
```

---

## Pattern 1 — SSOT-owned reference flowing down

### What this pattern governs

The upstream service owns the **canonical universe** for every (asset*group, venue, instrument_type) it manages: adapter
metadata (URLs, coverage windows, record-type names), catalogue entries (InstrumentRecord / PoolRecord / etc.), and
enumeration results (which instruments existed on which day). The downstream service MUST source all of this via an
explicit read-call (e.g. `load*\*\_metadata_for_date()` — the dex_pools_handler.py canonical pattern) rather than
re-fetching the upstream API or hardcoding any symbol, URL, or universe.

### Anti-patterns (block-listed)

- Module-level URL constants (`_DRIFT_S3_BASE = "https://..."`) in downstream handlers
- Hardcoded symbol lists (`SOLANA_LST_TOKENS = [...]`)
- Re-calling the upstream API from the downstream handler to enumerate markets when the upstream service already wrote
  them to GCS/instruments-store
- Returning from a handler function without having consulted the upstream catalogue

### Dim 1 — Upstream adapter coverage (per asset_group)

| asset_group | Working adapters | Stubs / gaps | Downstream-uses-but-no-upstream-call (the violation) |
| ----------- | ---------------- | ------------ | ---------------------------------------------------- |
| CEFI        |                  |              |                                                      |
| DeFi        |                  |              |                                                      |
| TradFi      |                  |              |                                                      |
| Sports      |                  |              |                                                      |
| Prediction  |                  |              |                                                      |

**Pre-audit grep recipe:**

```bash
# Identify hardcoded URL constants in downstream handlers:
rg '_[A-Z_]+_URL\s*=\s*"https?://' <downstream-repo>/
rg '_[A-Z_]+_BASE\s*=\s*"https?://' <downstream-repo>/
rg '_[A-Z_]+_ROUTE\s*=\s*"https?://' <downstream-repo>/

# Identify hardcoded universe lists in downstream handlers:
rg '[A-Z_]+_TOKENS\s*=\s*\[' <downstream-repo>/
rg '[A-Z_]+_MARKETS\s*=\s*\[' <downstream-repo>/
rg '[A-Z_]+_VENUES\s*=\s*\[' <downstream-repo>/

# Verify the ✅ pattern — upstream catalogue read calls:
rg 'load_.*_metadata_for_date\|load_.*_catalog' <downstream-repo>/ --type py

# Check IS adapter outputs that the downstream should read:
rg 'source_archive_url_template\|source_record_types\|coverage_start' \
  <upstream-repo>/ --type py
```

### Dim 2 — Downstream handler IS-consumption status

| Handler          | Status                                                    | Citation  |
| ---------------- | --------------------------------------------------------- | --------- |
| `<handler_a>.py` | ✅ Reads upstream via `load_<domain>_metadata_for_date()` | lines X-Y |
| `<handler_b>.py` | ❌ Hardcodes URL constant                                 | lines X-Y |
| `<handler_c>.py` | ⚠ Partial — fallback hardcodes                           | lines X-Y |

### Remediation pattern (per ❌/⚠ handler)

1. Add `source_archive_url_template`, `source_record_types`, `source_coverage_start/end` to the upstream
   `InstrumentRecord` / `PoolRecord` (or equivalent) for this venue. Land in UAC if it's a canonical type; land in the
   upstream adapter otherwise.
2. In the downstream handler: replace the module-level constant with a call to
   `load_<domain>_metadata_for_date(venue, date)`. Source the URL from `record.source_archive_url_template`. Source the
   universe from `record.ids`.
3. Add a static fallback dict (e.g. `_<VENUE>_STATIC_<DOMAIN>`) keyed by instrument ID for the rare "IS not yet
   backfilled for this date" case — use only as a `log_warn` fallback, never as the primary path.

---

## Pattern 2 — Manifest emission discipline

### What this pattern governs

Every (data*type × shard_key × date) iteration in a handler MUST emit exactly one of: `record_captured(...)`,
`record_empty(reason=<EmptyConfirmedReason>)`, or `record_failed(...)`. Silent returns (no record*\* call) are the
Drift-bug class — they leave the manifest index in DIVERGENT_EMPTY state without any signal for the operator.

### Dim 3 — Manifest emission per handler

| Handler          | Status                                                            | Evidence  |
| ---------------- | ----------------------------------------------------------------- | --------- |
| `<handler_a>.py` | ✅ Emits record_captured + record_empty + record_failed per shard | lines X-Y |
| `<handler_b>.py` | ❌ Silent absence — returns without record\_\* call               | lines X-Y |
| `<handler_c>.py` | ⚠ Emits record_captured but no record_empty path                 | lines X-Y |

**Pre-audit grep recipe:**

```bash
# Handlers without any record_* call (candidates for silent absence):
for h in <downstream-repo>/.../*_handler.py; do
  if ! grep -q 'record_captured\|record_empty\|record_failed\|record_expected_unattempted' "$h"; then
    echo "SILENT-ABSENCE CANDIDATE: $h"
  fi
done

# Handlers with record_captured but no record_empty (incomplete):
for h in <downstream-repo>/.../*_handler.py; do
  has_captured=$(grep -c 'record_captured' "$h" || echo 0)
  has_empty=$(grep -c 'record_empty' "$h" || echo 0)
  [ "$has_captured" -gt 0 ] && [ "$has_empty" -eq 0 ] && echo "MISSING record_empty: $h"
done

# Verify the ✅ dex_pools canonical pattern (for reference):
rg 'record_captured\|record_empty\|record_failed' \
  <downstream-repo>/.../dex_pools_handler.py -n
```

### Remediation pattern

Every path through `handle_date()` / `collect_*()` / `backfill_*()` must end with one `record_*` call. Wrap the try
block:

```python
try:
    rows = fetch_data(...)
    if not rows:
        recorder.record_empty(data_type=..., reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)
    else:
        recorder.record_captured(data_type=..., row_count=len(rows), ...)
except VenueError as e:
    classified = classify_venue_error(e, venue=...)
    recorder.record_failed(data_type=..., error=classified)
    log_event("ADAPTER_FETCH_FAILED", details={"venue": ..., "error": str(e)})
```

---

## Pattern 3 — Schema-version compliance

### What this pattern governs

Every manifest index parquet MUST carry `schema_version=8` (v8). Legacy v4 rows produce DIVERGENT_EMPTY false-negatives:
the `expected_coverage()` function computes against v8 semantics; v4 rows lack `capture_status` + `error_reason`
columns.

### Dim 4 — Manifest schema version per bucket

| Bucket                                      | Schema version                   | Action        |
| ------------------------------------------- | -------------------------------- | ------------- |
| `gs://<bucket>-prd-central-element-323112/` | v8                               | OK            |
| `gs://<legacy-bucket>/`                     | v4 (hardcoded in `handler.py:N`) | MIGRATE to v8 |

**Pre-audit grep recipe:**

```bash
# Find hardcoded schema_version < 8 in code:
rg 'schema_version\s*=\s*[1-7]' <downstream-repo>/ --type py

# Check actual schema versions in prod buckets:
python3 - <<'EOF'
import pyarrow.parquet as pq
import gcsfs
fs = gcsfs.GCSFileSystem(project="central-element-323112")
for bucket in ["market-data-tick-defi-prd-central-element-323112",
               "instruments-store-defi-prd-central-element-323112"]:
    path = f"{bucket}/_index/availability_index.parquet"
    try:
        tbl = pq.read_table(f"gs://{path}", filesystem=fs, columns=["schema_version"])
        print(f"{bucket}: {tbl['schema_version'].unique().to_pylist()}")
    except Exception as e:
        print(f"{bucket}: {e}")
EOF
```

### Remediation pattern

1. Patch the hardcoded `schema_version=<old>` to `schema_version=8` in the writer.
2. Add v8 columns to the migration script:
   - `capture_status` (default `"captured"` for existing rows)
   - `error_reason` (default `""`)
   - `attempted_at` (default `""`)
   - `pipeline_mode` (default `""`)
3. Snapshot the index before migrating:
   `gsutil cp gs://.../availability_index.parquet gs://.../_index/snapshots/pre_v8_<date>.parquet`

---

## Pattern 4 — Honest-absence reason taxonomy

### What this pattern governs

Every `record_empty(...)` call MUST supply a `reason=` from the closed set `EmptyConfirmedReason` in UAC
`canonical.crosscutting.honest_coverage`. Blank `reason=""` raises `LegacyBlankErrorReasonError` at runtime. Unknown
strings fail validation. The 17 typed reasons are the only valid values:

| Reason                               | When to use                                                                         |
| ------------------------------------ | ----------------------------------------------------------------------------------- |
| `SOURCE_RETURNED_ZERO`               | API returned 0 rows for this (venue, day) — expected                                |
| `EXPECTED_PRE_SOURCE_COVERAGE_START` | Date is before the source began writing                                             |
| `EXPECTED_PAST_SOURCE_COVERAGE_END`  | Date is after the source stopped writing (e.g. Drift tradeRecords ended 2025-01-08) |
| `EXPECTED_WEEKEND_OR_HOLIDAY`        | Tradfi market / sports league off                                                   |
| `EXPECTED_OFF_SEASON`                | Sports league off-season                                                            |
| `EXPECTED_PRE_LISTING`               | Instrument not yet listed on this date                                              |
| `EXPECTED_POST_DELISTING`            | Instrument delisted before this date                                                |
| `EXPECTED_LOW_LIQUIDITY_PERIOD`      | Thin-market protocol during bootstrap                                               |
| `EXPECTED_PROTOCOL_PAUSE`            | Known on-chain governance pause                                                     |
| `EXPECTED_MAINTENANCE_WINDOW`        | Scheduled downtime                                                                  |
| `EXPECTED_API_RATE_LIMIT`            | Rate-limit hit; data expected to be absent                                          |
| `EXPECTED_REGULATORY_RESTRICTION`    | Geo-blocked or compliance-gated                                                     |
| `EXPECTED_MARKET_STRUCTURE_GAP`      | Structural absence (no options on this expiry, etc.)                                |
| `EXPECTED_DATA_NOT_YET_AVAILABLE`    | Source publishes with delay                                                         |
| `EXPECTED_INSTRUMENT_TYPE_MISMATCH`  | Handler scope excludes this instrument type                                         |
| `EXPECTED_ASSET_GROUP_MISMATCH`      | Handler scope excludes this asset_group                                             |
| `EXPECTED_VENUE_MISMATCH`            | Handler scope excludes this venue                                                   |

**Pre-audit grep recipe:**

```bash
# Find blank reason strings (will raise LegacyBlankErrorReasonError at runtime):
rg 'record_empty\s*\(.*reason\s*=\s*""' <downstream-repo>/ --type py

# Find string literals instead of enum (will fail UAC validation):
rg 'record_empty\s*\(.*reason\s*=\s*"[A-Z_]+"' <downstream-repo>/ --type py

# Verify clean enum usage (the ✅ pattern):
rg 'record_empty\s*\(.*EmptyConfirmedReason\.' <downstream-repo>/ --type py
```

---

## Pattern 5 — `expected_coverage()` preflight + `DIVERGENT_EMPTY` post-hoc check

### What this pattern governs

Before fetching, every handler should call `expected_coverage(venue, data_type, date)` to classify the shard as
`SHOULD_HAVE_DATA | EXPECTED_EMPTY:<reason> | NOT_YET_LIVE`. If `EXPECTED_EMPTY`, emit `record_empty(reason=<reason>)`
immediately — do not fetch. After the run, a post-hoc reconciler identifies `DIVERGENT_EMPTY` cells: `actual=0 rows` but
`expected_coverage = SHOULD_HAVE_DATA`. These are the Drift-bug class; every `DIVERGENT_EMPTY` cell requires a
root-cause investigation.

**Pre-audit grep recipe:**

```bash
# Handlers that lack expected_coverage() call:
for h in <downstream-repo>/.../*_handler.py; do
  grep -q 'expected_coverage' "$h" || echo "NO preflight: $h"
done

# Post-hoc divergence scan (materialise DIVERGENT_EMPTY cells):
python3 - <<'EOF'
import pyarrow.parquet as pq
import gcsfs
from unified_api_contracts.canonical.crosscutting.honest_coverage import expected_coverage
fs = gcsfs.GCSFileSystem(project="central-element-323112")
tbl = pq.read_table(
    "gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet",
    filesystem=fs
)
df = tbl.to_pandas()
# Identify cells where manifest says empty/zero but expected_coverage says SHOULD_HAVE_DATA
empty_rows = df[df['capture_status'].isin(['empty_confirmed', 'expected_unattempted'])]
for _, row in empty_rows.iterrows():
    ec = expected_coverage(row['venue'], row['data_type'], row['date'])
    if ec == 'SHOULD_HAVE_DATA':
        print(f"DIVERGENT_EMPTY: {row['venue']} / {row['data_type']} / {row['date']}")
EOF
```

---

## Pattern 6 — Error classification at the boundary

### What this pattern governs

Every adapter `except` block that catches a network, API, or parsing error MUST:

1. Call `classify_venue_error(exc, venue=<venue_name>)` from UAC `canonical.crosscutting.errors.classify_venue_error` to
   get a typed error class (FAIL / RETRY / SKIP prefix).
2. Emit `log_event("ADAPTER_FETCH_FAILED", details={"venue": ..., "error": ...})`.
3. Call `recorder.record_failed(...)` with the classified error.

Bare `except: pass` or `except Exception: logger.warning(...)` without `classify_venue_error` is a blocker.

**Pre-audit grep recipe:**

```bash
# Adapters with except blocks but no classify_venue_error:
python3 - <<'EOF'
import ast, pathlib
for f in pathlib.Path("<downstream-repo>").rglob("*.py"):
    src = f.read_text()
    if 'except' not in src: continue
    if 'classify_venue_error' in src: continue
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.ExceptHandler,)):
            print(f"{f}:{node.lineno} — except block without classify_venue_error")
            break
EOF

# Verify ADAPTER_FETCH_FAILED emission exists:
rg 'ADAPTER_FETCH_FAILED' <downstream-repo>/ --type py | wc -l

# Check classify_venue_error import is from the right module:
rg 'from.*classify_venue_error\|import.*classify_venue_error' <downstream-repo>/ --type py
```

---

## Pattern 7 — Bucket-SSOT

### What this pattern governs

Every GCS bucket reference MUST go through
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`. Inline `gs://` f-strings (e.g.
`f"gs://market-data-tick-{asset_group}-prd-{project_id}"`) are banned. The canonical source is
`deployment-service/configs/cloud-providers.yaml`. QG STEP 5.69 enforces this via the `check_inline_bucket_uri.py`
script with a per-file ratchet baseline.

**Pre-audit grep recipe:**

```bash
# Find inline gs:// URIs:
rg '"gs://' <downstream-repo>/ --type py | grep -v 'test_\|tests/\|#'

# Find f-string bucket construction:
rg 'f"gs://{.*}' <downstream-repo>/ --type py | grep -v 'test_\|tests/'

# Verify resolve_bucket_name is imported:
rg 'resolve_bucket_name' <downstream-repo>/ --type py
```

---

## 4-dimensional audit matrix (template)

Fill all 4 dims per audit instantiation. Link to Dim sections above.

| Dim   | What it measures                               | Status        |
| ----- | ---------------------------------------------- | ------------- |
| Dim 1 | Upstream adapter coverage per asset_group      | See Pattern 1 |
| Dim 2 | Downstream handler upstream-consumption status | See Pattern 1 |
| Dim 3 | Manifest emission discipline per handler       | See Pattern 2 |
| Dim 4 | Manifest schema version per bucket             | See Pattern 3 |

---

## Pre-audit checklist (run before writing any remediation)

1. `git fetch origin live-defi-rollout` — get latest state of all repos.
2. Run all 7 grep recipes above against the upstream + downstream repos.
3. Read the 3 related codex SSOTs:
   - `codex/02-data/availability-manifest-and-data-status.md`
   - `codex/02-data/honest-absence-downstream-handling.md`
   - `codex/02-data/service-output-emission-semantics.md`
4. Check `plans/audit/results/codified_shape_compliance_2026_05_20.csv` for the downstream repo's rows — this lists all
   10 A1 pattern violations with counts.
5. Record the commit SHA of each repo at audit time. Changes after the SHA are out-of-scope for this instantiation.

---

## QG-ratchet phase shape

Every audit instantiation MUST include a "QG-ratchet" phase. The shape:

### Phase Q — QG enforcement (the gates that should have caught this)

The 7 patterns above map to QG steps. Wire each violated pattern as a QG step in the **downstream** service's
`quality-gates.sh`:

| Pattern                          | QG script                                                                                     | Status                |
| -------------------------------- | --------------------------------------------------------------------------------------------- | --------------------- |
| P1 — SSOT-owned reference        | `unified-trading-pm/scripts/qg/no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` | SHIPPED (STEP 5.70)   |
| P2 — Manifest emission           | `unified-trading-pm/scripts/qg/no_silent_absence_handlers.sh`                                 | SHIPPED (STEP 5.70)   |
| P3 — Schema-version              | `rg 'schema_version\s*=\s*[1-7]'` inline in QG                                                | **GAP — add as STEP** |
| P4 — Honest-absence reasons      | `rg 'record_empty.*reason\s*=\s*""'` inline in QG                                             | **GAP — add as STEP** |
| P5 — expected_coverage preflight | (runtime-only today; scaffold as STEP TBD)                                                    | **GAP**               |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                                               | SHIPPED               |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                                                      | SHIPPED               |

For each GAP above: add the enforcement step to `quality-gates.sh` in the same commit as the remediation code.

---

## Continuous-verification column (required per plan)

| Pattern                          | Continuous-verification path                                 | Cadence               | Last verified |
| -------------------------------- | ------------------------------------------------------------ | --------------------- | ------------- |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` runs in QG on every push to LDR | every push            |               |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh` runs in QG                   | every push            |               |
| P3 — Schema-version              | Inline QG rg step (once added)                               | every push            |               |
| P4 — Honest-absence reasons      | `LegacyBlankErrorReasonError` raised at runtime              | every batch run       |               |
| P5 — expected_coverage preflight | Post-hoc `DIVERGENT_EMPTY` scanner (A3-style)                | daily scheduled audit |               |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)              | every push            |               |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                     | every push            |               |

---

## Phased execution DAG (template — adapt per pair)

```
Phase 1 — UAC schema extension (upstream adds new fields to shared types)
   │
   ├── Phase 2 — Upstream adapter writes new fields (IS / MTDS / features)
   │
   ├── Phase 3 — Downstream handler migration (consume upstream, emit manifest)
   │
   ├── Phase 4 — Schema-version migration (v4 → v8 if needed)
   │
   ├── Phase 5 — Re-backfill where audit found data corruption
   │
   ├── Phase 6 — Real-fleet verification (expected_coverage vs manifest)
   │
   └── Phase Q — QG enforcement (gates for Patterns 1–7)

Phase D — Codex doc update follows Phase Q
```

**Foundation-completion-gate rule (HARD RULE)**: no Phase N+1 work starts before Phase N is GREEN-audited and
manifest-divergence = 0 for affected asset_groups.

---

## Temporary states + canonical follow-up plans

- **Per-audit instantiation**: each `plans/audit/<slug>_contract_audit_<date>.md` must declare a `## Temporary states`
  section listing any dual-path or shim introduced during remediation and naming the Phase where it retires.
- **Static fallback dicts** (Pattern 1 remediation): retire when IS catalogue is fully backfilled for the affected
  venue + date range. Track in deprecation-ledger.
- **Script-only enforcement** (Pattern 5 pre-QG): retire when CI step ships.

---

## Scope exclusions (document per instantiation)

Not every upstream→downstream pair has violations in all 7 patterns. Document which patterns were **verified clean** vs
which have violations. A verified-clean pattern still requires the continuous-verification path.

Example:

> **P3 (schema-version)**: All buckets confirmed v8 as of audit date `<SHA>`. Continuous-verification: inline QG rg step
> (STEP TBD — not yet wired). No remediation needed in this instantiation.
