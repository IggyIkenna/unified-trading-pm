---
doc_type: issue
title:
  "features-service quality-gates.sh RED — STEP 5.104 asset-group parity gate's check_asset_group_parity.py
  _KIND_TO_FAMILY mapping is stale post-bucket-fold, blocking every ship from the repo"
summary:
  "Dispatched onto api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency-007 (fix
  features-service's _filter_completed_before H2H status filter — unrelated). Full quality-gates.sh run is RED at STEP
  5.104 (ASSET-GROUP PARITY GATE), verified byte-identical on a clean tree with my diff stashed per RULES.md § 4b. 5
  families (features-delta-one, features-mtf, features-onchain, features-volatility, features-xinstrument) are reported
  as declared on NO cloud in unified-api-contracts/config/cloud-providers.yaml while their CLIs still accept
  asset_group_choices. This is a known side-effect of the Wave-3 bucket fold
  (plans/active/bucket_fold_features_2026_07_17.md, plans/active/bucket_fold_closeout_2026_07_17.md) that folded these 5
  per-family cloud-providers.yaml keys into a single 'features' key — the closeout doc's Alias-Sunset-Part-A entry
  explicitly lists check_asset_group_parity's _KIND_TO_FAMILY mapping-dict as a site 'correctly LEFT (legitimate,
  non-breaking)' at the time (2026-07-19), but the gate is now actively RED, blocking quality-gates.sh (and therefore
  quickmerge --agent's sentinel) for EVERY task in features-service, not just this one."
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [features-service, unified-api-contracts, unified-trading-library, deployment-service, deployment-api]
scope: [engineer, admin]
tags: [features-service, quality-gates, asset-group-parity, bucket-fold, repo-blocker, qg-red]
related:
  [
    plans/active/bucket_fold_features_2026_07_17.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    plans/active/issues/features_service_qg_red_bucket_symbol_ssot_drift_2026_07_18.md,
    plans/active/issues/api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md,
  ]
created: "2026-07-19"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency-007]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# features-service quality-gates.sh RED at STEP 5.104 (asset-group parity gate) — stale post-fold kind mapping

## What I found

Dispatched onto `api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency-007` (fix
`features-service/features_service/sports/exporters/derived_features_helpers.py::_filter_completed_before` — entirely
unrelated to buckets/asset-groups). After landing that fix + tests, ran the full `bash scripts/quality-gates.sh` in
`features-service`: green through STEP 5.92 (17702 passed, 0 failed, 209 skipped), then **STEP 5.104 ASSET-GROUP PARITY
GATE fails** with 5 violations:

```
FAIL: 5 asset-group parity violation(s) between unified_api_contracts/config/cloud-providers.yaml and features-service:
  • 'features-delta-one' is declared on NO cloud (gcp/aws), but features_service/delta_one/cli/ still accepts
    asset_group_choices — every resolve_bucket(kind='features-delta-one', …) raises BucketNamingError.
  • 'features-mtf' — same pattern (features_service/multi_timeframe/cli/)
  • 'features-onchain' — same pattern (features_service/onchain/cli/)
  • 'features-volatility' — same pattern (features_service/volatility/cli/)
  • 'features-xinstrument' — same pattern (features_service/cross_instrument/cli/)
```

**Verified pre-existing per RULES.md § 4b**: `git stash push -u`, re-ran
`.venv/bin/python scripts/quality_gates/check_asset_group_parity.py` directly on the clean tree at LDR HEAD —
byte-identical 5 violations — then `git stash pop` to restore my diff. This is not caused by my change (I touched only
`features_service/sports/exporters/derived_features_helpers.py` and its test file).

**Root cause (traced, not fixed — outside my task's craft/scope)**: `plans/active/bucket_fold_closeout_2026_07_17.md`'s
"ALIAS SUNSET Phase 2 Part A" entry (2026-07-19) already documents that the Wave-3 bucket fold
(`plans/active/bucket_fold_features_2026_07_17.md`) collapsed the 5 per-family `cloud-providers.yaml` keys
(`features-delta-one`/`features-mtf`/`features-onchain`/`features-volatility`/`features-xinstrument`) into a single
folded `features` key, and every live `resolve_bucket_name(kind=...)` caller was repointed to the folded kind. That same
entry explicitly calls out `check_asset_group_parity`'s `_KIND_TO_FAMILY` kind→family mapping-dict as a site that was
**"correctly LEFT (legitimate, non-breaking)"** at the time. That assumption is now invalidated: the gate script itself
(`scripts/quality_gates/check_asset_group_parity.py`) still expects the 5 OLD per-family keys to exist in
`cloud-providers.yaml`, and since the fold removed them, every run now fails. The gate's own error message names both
options: **(a)** restore the 5 per-family cloud-providers.yaml declarations, or **(b)** the families are genuinely
retired (folded into `features`) — drop them from `_KIND_TO_FAMILY` in the gate script and update the CLIs'
`asset_group_choices` accordingly if they're also stale.

**I did not make this judgment call** — it requires reading the Fold design doc
(`plans/active/bucket_estate_fold_design_2026_07_13.md`) + the actual current CLI/cloud-providers.yaml state to
determine whether (a) or (b) is correct, which is out of scope for this dispatch (data_engineering craft, a
features-service sports-fixture status-filter fix, not bucket-fold/infra work).

## Why it matters

- **Blocks every ship from features-service** — `quickmerge --agent` refuses whenever `scripts/quality-gates.sh` cannot
  write a fresh `.qg_last_passed_sha` sentinel, and it can't while STEP 5.104 is red. My own fix (green in isolation:
  full suite 17702 passed / 0 failed, new tests for the NS-status fix included) cannot ship via the mandated quickmerge
  flow until this repo goes green.
- This is the SAME class of "fold-closeout follow-up assumed non-breaking, turned out to actually break something"
  pattern already seen once in `features_service_qg_red_bucket_symbol_ssot_drift_2026_07_18.md` (Cluster A) — a second
  independent instance suggests the Wave-3 bucket-fold closeout's "correctly LEFT" sites should get a fresh sweep rather
  than being assumed still-safe.

## Determination (todo 1, 2026-07-19, slot-5)

**Verdict: (b) — the 5 families are genuinely retired as separate `cloud-providers.yaml` keys; the fold is real,
deliberate, and code has already fully cut over. `cloud-providers.yaml` is not missing anything — the gate script's
`_KIND_TO_FAMILY` dict is stale.**

Evidence:

1. `unified_api_contracts/config/cloud-providers.yaml:58-65` (gcp) / `:197-203` (aws) carry an explicit fold-A comment:
   _"features FOLD A (fold_a_cutover_spec, 2026-07-18): folded per-asset_group key; the 5 retired per-kind buckets
   collapse into features-{ag}-${DEPLOYMENT_ENV_SHORT}-{pid}, per-kind → key prefix."_ The single folded `features:` key
   declares `CEFI`/`TRADFI`/`DEFI`/`PREDICTION`/`SPORTS` on both clouds — none of the 5 old per-family keys
   (`features-delta-one`/`-volatility`/`-onchain`/`-xinstrument`/`-mtf`) exist any more, by design.
2. Every one of the 5 families' writer/reader call sites is already repointed to `resolve_bucket(kind="features", ...)`
   — grepped `kind="features-{delta-one,volatility,onchain,xinstrument,mtf}"` across
   `features_service/{delta_one,volatility,onchain,cross_instrument,multi_timeframe}/`: zero live code call sites remain
   (`delta_one/app/core/feature_writer.py:79`, `volatility/core/feature_writer.py:109`, `onchain/config.py:116` and
   `:124`, `cross_instrument/app/cross_venue_arb_runner.py:140`, plus each family's `config.py` — all call
   `kind="features"`). The only 2 hits for the old strings are stale docstring comments, not executable code
   (`cross_instrument/app/calculators/paired_dispatch.py:218`, `volatility/core/dependency_checker.py:80`).
3. Every family's CLI `asset_group_choices` is a **subset** of the folded key's declared set — no orphan/missing risk
   from the union either:
   - `delta_one`: CEFI/TRADFI/DEFI/PREDICTION (`delta_one/cli/parser.py:44`, `CATEGORIES`)
   - `volatility`: CEFI/TRADFI (`volatility/cli/parser.py:24-27`, `ASSET_GROUP_CHOICES`)
   - `cross_instrument`: CEFI/DEFI/TRADFI/PREDICTION (`cross_instrument/cli/main.py:180`)
   - `multi_timeframe`: CEFI/TRADFI/DEFI (`multi_timeframe/cli/main.py:246`)
   - `onchain`: DEFI only, pinned via the `_ONCHAIN_ASSET_GROUP` constant (`onchain/config.py:22`) — not a CLI choice;
     already routed through the gate's `_CONSTANT_AUTHORITY` path, not the AST CLI-scan path.
   - Union = `{CEFI, TRADFI, DEFI, PREDICTION}` ⊆ folded key's `{CEFI, TRADFI, DEFI, PREDICTION, SPORTS}`.

**Fix shape for todo 2** (do NOT restore the 5 old per-family yaml keys — that re-provisions the exact orphan-bucket
problem the 2026-07-17 sweep and this fold were built to eliminate): drop the 5 stale entries from
`check_asset_group_parity.py`'s `_KIND_TO_FAMILY`. Because that dict's schema is 1:1 (`kind → single family`) and 5
families now share ONE folded kind (`"features"`), a straight drop with no replacement silently loses gate coverage for
these families' future asset_group/CLI drift — the gate needs a small structural change so the folded `"features"` kind
is checked against the **union** of all 5 families' invocable asset groups (CEFI/TRADFI/DEFI/PREDICTION), not a single
family (a naive `"features": "<one-family>"` entry would wrongly treat another family's legitimate asset_group as an
"EXTRA" violation). **Do NOT touch the 5 families' `asset_group_choices`** — they are all correct as-is; the issue's
original phrasing ("so the CLIs no longer accept an asset_group with nowhere to write") is not accurate — every one of
these asset groups already resolves through the folded `features` bucket, there is nowhere left to remove.

**Flagged, out of scope for todo 2, feeds the existing P3 re-sweep todo below**: `scripts/e2e/run_pipeline_e2e.py`'s
`FAMILY_SPECS` dict (`output_kind=` at lines ~72/80/89/97) still hardcodes the same 4 retired kind strings
(`features-delta-one`/`-volatility`/`features-cross-instrument`/`features-multi-timeframe`) for its `_test_bucket()`
resolution. This is exactly the "features e2e harness" site the closeout doc already called out as one of the OTHER
"correctly LEFT" sites — it is now stale by the same pattern this issue documents, a second data point for the P3
re-sweep. Not expanded here; left for that todo.

## Note on todo 2 (slot-6, 2026-07-19)

Landed on this issue independently (via the todo-3 dispatch) while slot-5 was already applying the same todo-2 fix.
Discovered + fixed the identical orphan-SPORTS-key finding slot-5 documents in "Fix applied (todo 2, slot-5)" below —
reconciled via `git pull --rebase --autostash` (one real conflict, resolved keeping slot-5's already-shipped
`unified-api-contracts@1ff91e5b`/`features-service@bc7bc4ff` content; my duplicate local edit to the same 2 files was
discarded as redundant). One finding from that investigation slot-5's writeup does not cover: removing the SPORTS yaml
key risked breaking any consumer that enumerated it. Checked —
`unified-trading-library/unified_trading_library/migrations/upgrade_manifest_to_v8.py`'s `_PER_AG_KINDS` list enumerated
`("features", (..., "sports", ...))`. This script is NOT dead code (contra its "dead one-off migration" characterization
in the closeout doc — it IS invoked, via `deployment-service/scripts/vm/phase11-backfill-coordinator.sh` and
`unified-trading-library/scripts/migrate_manifest_v8.py`). Confirmed fail-soft: `_collect_buckets()` wraps each
`resolve_bucket_name` call in `try/except BucketNamingError` + `logger.warning(...)`, so removing the SPORTS yaml key
would NOT have crashed it, just logged a benign warning and silently skipped a resolve that was already redundant with
the separate `_FLAT_KINDS_SPORTS` enumeration (same physical bucket, sports coverage stays intact). Fixed anyway for
hygiene: dropped `"sports"` from that tuple + added a comment explaining why. Shipped as part of "Fix applied (todo 3,
slot-6)" below (`unified-trading-library`).

## Determination (todo 3 re-check, 2026-07-19, slot-6)

Re-checked all 4 named "correctly LEFT (legitimate, non-breaking)" sites from the closeout doc's Alias-Sunset-Part-A
entry, now that the fold + a follow-on alias sunset (2026-07-19, `bucket_naming.py` `_KIND_ALIASES`) have both landed:

1. **Features e2e harness — BROKEN, FIXED.** `features-service/scripts/e2e/run_pipeline_e2e.py`'s `FAMILY_SPECS` dict
   set `output_kind="features-delta-one"` / `"features-volatility"` for the `delta_one`/`volatility` families — both
   SHORT retired kind aliases that the SAME-DAY alias sunset removed from `_KIND_ALIASES`. Proved the break directly:
   `resolve_bucket_name(cloud="gcp", kind="features-delta-one", asset_group="cefi")` raises
   `BucketNamingError: Unknown kind 'features-delta-one'` (not caught anywhere in `run_e2e()` — a real crash for any
   `--family delta_one` or `--family volatility` e2e run). `cross_instrument`/`multi_timeframe` were unaffected — they
   already used the LONG, PERMANENT consumer-facing alias names (`features-cross-instrument`/`features-multi-timeframe`,
   which the sunset explicitly keeps). **Fixed**: `output_kind="features"` for both broken entries (matches the
   already-correct `_delta_one_test_bucket()` helper a few lines below, which had already been fixed independently and
   carries an "alias retired 2026-07-19" comment — the main `FAMILY_SPECS` dict was simply never updated to match).
   Verified all 4 families now resolve to the same folded test bucket. Also found + fixed the SAME pattern in a sibling
   file: `features-service/scripts/multi_timeframe/smoke_matrix.py`'s `SMOKE_INPUT_KIND = "features-delta-one"` — this
   one is WORSE because `features_service/common/__init__.py::resolve_latest_captured_date()` wraps the resolve in a
   broad `except Exception: return None`, so the break was SILENT (no crash, no warning — just always falling back to
   the hardcoded `FALLBACK_DATE` instead of ever finding the real latest-captured smoke date). Fixed to `"features"`.
2. **`check_asset_group_parity` kind→family mapping-dict — the ORIGINAL finding this issue doc is about; FIXED** by
   slot-5 (`features-service@bc7bc4ff`, "Fix applied (todo 2, slot-5)" below).
3. **`upgrade_manifest_to_v8.py` — genuinely NOT dead** (contra the closeout doc), but its SPORTS-enumeration break was
   fail-soft; fixed as a hygiene cleanup (see "Note on todo 2 (slot-6)" above). No further action.
4. **`cloud_constants` legacy "positions" map — confirmed STILL dead.** No live caller of `get_bucket_name("positions")`
   anywhere in the workspace (grepped all repos). Correctly LEFT, no action.
5. **Inference-config comments — confirmed STILL just comments.** `ml-service`'s many `"features-delta-one-service"`
   references are SERVICE-NAME labels for dependency-graph tracking (`UPSTREAM_DEPS`, `feature_sources`, etc.) — a
   different namespace entirely from the bare `"features-delta-one"` bucket-KIND string that broke elsewhere. Zero
   `resolve_bucket_name(kind=...)` calls with a retired kind string found in `ml-service`. Correctly LEFT, no action.

**NEW finding, deferred (NOT fixed in this task — see the new todo below)**: while chasing the "data-status-drilldown
service→kind maps" reference from an EARLIER (superseded) closeout-doc log entry, found
`deployment-api/deployment_api/services/data_status_drilldown/_core.py`'s `SERVICE_TO_KIND` dict still maps
`"features-delta-one-service"` → `"features-delta-one"`, `"features-volatility-service"` → `"features-volatility"`,
`"features-onchain-service"` → `"features-onchain"` (all 3 SHORT retired kind strings). Confirmed this IS live and
UNGUARDED: `build_bucket_name()` (same file) and `deployment_api/services/data_status/manifest.py:742` both call
`resolve_bucket_name(cloud="gcp", kind=kind, ...)` with this dict's value directly, no try/except — a genuine unhandled
`BucketNamingError` for any delta_one/volatility/onchain data-status-drilldown lookup (this backs the data-status UI's
per-service bucket resolution). This CONTRADICTS the closeout doc's later claim that "the deployment-api features leg
was done in 4c@ff1c691" — either that repoint targeted a different site, or this dict was missed. **Not fixed here**:
deployment-api is a large service I have zero prior context in (import graph, `PREDICTION_KIND_MAP` coupling, full test
suite) — a blind edit risks a worse regression than the one it fixes. Filed as todo 4 below instead.

## Recommended decision / next steps

- [x] [INFRA] P1. Determine the correct current state for the 5 folded families
      (features-delta-one/mtf/onchain/volatility/xinstrument): read
      `plans/active/bucket_estate_fold_design_2026_07_13.md` + current `cloud-providers.yaml` `features:` folded key +
      each CLI's `asset_group_choices` to decide whether these 5 families are genuinely retired (folded into `features`)
      or whether cloud-providers.yaml lost declarations it should still carry. (repo: unified-api-contracts /
      features-service) — ✅ determination: (b), see "Determination (todo 1)" above (this doc, slot-5, 2026-07-19).
- [x] [INFRA] P1. Apply the determined fix: drop the 5 retired families from `check_asset_group_parity.py`'s
      `_KIND_TO_FAMILY` dict and replace with union-of-families coverage for the folded `"features"` kind (CEFI/TRADFI/
      DEFI/PREDICTION) — see "Fix shape for todo 2" above. Do NOT touch the 5 families' `asset_group_choices` (they are
      correct as-is) and do NOT restore the 5 old per-family `cloud-providers.yaml` keys. Re-run
      `bash scripts/quality-gates.sh` end to end to confirm STEP 5.104 (and the rest of the gate) goes green and a fresh
      sentinel is written. (repo: features-service, unified-api-contracts) — ✅ features-service@bc7bc4ff,
      unified-api-contracts@1ff91e5b — both shipped via quickmerge, both quality-gates.sh green end to end (STEP 5.104
      confirmed passing in both runs), see "Fix applied" + "Evidence" below.
- [x] [PROCESS] P3. Once fixed, re-check `plans/active/bucket_fold_closeout_2026_07_17.md`'s other "correctly LEFT
      (legitimate, non-breaking)" sites listed in the same Alias-Sunset-Part-A entry (the features e2e harness,
      `upgrade_manifest_to_v8.py`, `cloud_constants` legacy "positions" map, inference-config comments) for the same
      assumed-safe-but-now-broken pattern, given this is the second such instance found post-fold. — ✅ DONE 2026-07-19
      slot-6: found + fixed 2 genuinely broken sites (e2e harness `FAMILY_SPECS` — this ALSO resolves the duplicate P3
      todo below; `multi_timeframe/smoke_matrix.py` `SMOKE_INPUT_KIND`); confirmed 2 sites still correctly LEFT
      (`cloud_constants` positions map, inference-config comments); found 1 NEW live-broken site in a 4th repo
      (deployment-api), deferred to todo 4. See "Fix applied (todo 3, slot-6)" below.
- [x] [PROCESS] P3. `scripts/e2e/run_pipeline_e2e.py`'s `FAMILY_SPECS` dict (lines ~72/80/89/97) hardcodes 4 retired
      per-family kind strings
      (`features-delta-one`/`-volatility`/`features-cross-instrument`/`features-multi-timeframe`) for `_test_bucket()`
      resolution — stale by the exact same post-fold pattern this issue documents (found during todo-1 investigation,
      2026-07-19). Repoint to the folded `kind="features"` or fold into the P3 re-sweep above. (repo: features-service)
      — ✅ DONE 2026-07-19 slot-6 as part of the todo-3 re-check above: `delta_one`/`volatility` repointed to
      `output_kind="features"` (the 2 LONG consumer-facing names `features-cross-instrument`/`features-multi-timeframe`
      were already valid permanent aliases, unaffected).
- [x] [INFRA] P0. **NEW — deployment-api `SERVICE_TO_KIND` still maps 3 services to retired SHORT kind strings**
      (`features-delta-one-service`→`"features-delta-one"`, `features-volatility-service`→`"features-volatility"`,
      `features-onchain-service`→`"features-onchain"` in `deployment_api/services/data_status_drilldown/_core.py`). Both
      `build_bucket_name()` (same file) and `deployment_api/services/data_status/manifest.py:742` call
      `resolve_bucket_name(kind=kind, ...)` with these values UNGUARDED (no try/except) — genuine unhandled
      `BucketNamingError` for delta_one/volatility/onchain data-status-drilldown lookups (a live UI-facing API path).
      Fix shape: remap the 3 dict values to `"features"` (matching the fold); check `PREDICTION_KIND_MAP` and any other
      structure keyed by the OLD kind strings for a matching repoint (grep `PREDICTION_KIND_MAP\[.features-delta-one.\]`
      etc. — may need consolidating since 3 services now converge on ONE folded kind). Run deployment-api's full
      `quality-gates.sh` + the `data_status_drilldown` test suite (`tests/unit/test_data_status_drilldown.py`,
      `tests/unit/test_drilldown_cache.py`, `tests/unit/test_data_status_service.py`) before shipping — this file has
      real production coupling not yet fully traced. (repo: deployment-api) — ✅ deployment-api@6279e9c, shipped via
      quickmerge. Remapped all 3 dict values to `"features"`. Verified no other repoint needed: `defi.py`/`manifest.py`
      both import this same `SERVICE_TO_KIND` dict so they inherit the fix automatically; grepped for
      `PREDICTION_KIND_MAP[.features-delta-one.]` etc. — zero hits, no consolidation needed (the folded `"features"`
      kind already carries a `PREDICTION` yaml entry, so the existing fallback path in `manifest.py`/`defi.py` resolves
      it directly). `SINGLE_ASSET_GROUP_SERVICES["features-onchain-service"]="defi"` left untouched (still correct —
      onchain only ever writes DEFI). Full `bash scripts/quality-gates.sh` green end-to-end (109s, 4702 passed / 0
      failed / 16 skipped, fresh sentinel `00560807b8adbd5c6cf1a3cee612ea8c30f5c273` →
      `6279e9c05308f81deec31bc4220b0c0b699a069c`); the 3 named test suites
      (`test_data_status_drilldown.py`/`test_drilldown_cache.py`/`test_data_status_service.py`) pass within that run.

## Fix applied (todo 2, 2026-07-19, slot-5)

Applied determination (b): rewrote `check_asset_group_parity.py` so `_KIND_TO_FAMILY: dict[str, str]` (1:1 kind→family)
became `_KIND_TO_FAMILIES: dict[str, tuple[str, ...]]` (1:many), with a single entry
`"features": ("volatility", "delta_one", "onchain", "cross_instrument", "multi_timeframe")`. `check()` now unions every
mapped family's invocable asset groups per kind before diffing against the yaml-declared set, and violation messages
name the specific family(ies) that need/reject a given asset_group rather than assuming one family per kind. The 5 CLIs'
`asset_group_choices` were left untouched, as determined.

**Second finding, fixed in the same commit (in-file, per findings-triage "in your file → fix in same commit")**: running
the rewritten gate surfaced a NEW violation the original 5-violation report didn't show —
`{gcp,aws}.storage.features.SPORTS` is declared in `cloud-providers.yaml` but none of the 5 folded families' CLIs accept
`SPORTS`. Traced: the fold (2026-07-18) reintroduced the exact orphan the 2026-07-17 asset-group-parity sweep had
already deleted from the old `features-delta-one` per-family dict (yaml carries the removal comment one section above
the fold). Confirmed safe to drop — `features-sports-${env}-${pid}` (the SPORTS template string) is identical to the
separate dedicated `features-sports` flat key the `sports` family actually writes through
(`features_service/sports/.../resolve_bucket(kind="features-sports", asset_group="sports")` — never `kind="features"`),
so removing the per-AG alias loses no reachable bucket. Dropped `SPORTS:` from the folded `features:` dict on both
clouds in `cloud-providers.yaml`, with an inline comment explaining the removal and pointing back to this issue doc.

Verified: `.venv/bin/python scripts/quality_gates/check_asset_group_parity.py` (default UAC-packaged yaml, editable
local-path dependency so the sibling-repo edit is live) →
`OK: every per-asset-group feature kind matches its family's CLI asset_group_choices`. Full
`bash scripts/quality-gates.sh` re-run end to end for final confirmation + fresh sentinel (see Evidence).

**Shipped**: `features-service@bc7bc4ff` (quickmerge, full QG green 326s incl. STEP 5.104) and
`unified-api-contracts@1ff91e5b` (quickmerge, full QG green 276s). Both landed on `live-defi-rollout`.

**Near-miss during shipping (operational note, not a plan action item)**: committed the UAC fix locally before shipping
it, then ran `features-service`'s `quickmerge.sh`, which cascades ancestor path-dependencies (`unified-api-contracts`,
`unified-trading-library`) onto the current dep-branch as STAGE 0 — that cascade force-aligned `unified-api-contracts`
to `origin/live-defi-rollout` (a hard reset), silently discarding the not-yet-pushed local commit (working tree was
clean so no pre-commit-hook or dirty-tree guard caught it). Recovered cleanly via `git reflog`
(`git reset --hard <sha>`) since origin still only had the pre-fix state — no data was lost upstream, only a few minutes
of re-running QG. Lesson for future cross-repo fixes touching an ancestor + a dependent repo in the same task: **ship
(quickmerge) the ancestor repo BEFORE running quickmerge on the dependent repo**, not after — the dependent's cascade
step assumes ancestors are already at the intended pushed state.

## Fix applied (todo 3, 2026-07-19, slot-6)

**e2e harness** (`features-service/scripts/e2e/run_pipeline_e2e.py`): `FAMILY_SPECS["delta_one"].output_kind` and
`FAMILY_SPECS["volatility"].output_kind` repointed from the retired short aliases (`"features-delta-one"`,
`"features-volatility"`) to the folded `"features"` kind. `cross_instrument`/`multi_timeframe` untouched (already used
the still-valid long consumer-facing aliases). Verified all 4 families now resolve to the same folded `-test-` bucket
via `_test_bucket()`.

**Smoke matrix** (`features-service/scripts/multi_timeframe/smoke_matrix.py`): `SMOKE_INPUT_KIND` repointed from
`"features-delta-one"` to `"features"` — this one degraded silently (`resolve_latest_captured_date()` swallows
`BucketNamingError` and returns `None`), so the smoke matrix was always falling back to the hardcoded `FALLBACK_DATE`.

**v8 migration hygiene** (`unified-trading-library/unified_trading_library/migrations/upgrade_manifest_to_v8.py`):
dropped the now-invalid `"sports"` entry from `_PER_AG_KINDS`'s `"features"` tuple (see "Note on todo 2" above) — fixes
a benign warning-log-only skip, sports coverage was never actually lost (`_FLAT_KINDS_SPORTS` already covers it).

**Mirror-copy sync** (the SPORTS removal slot-5 shipped in the UAC SSOT needed mirroring — 2 of the 5 copies were still
stale after slot-5's fix): `deployment-service/configs/cloud-providers.yaml`,
`unified-trading-pm/configs/cloud-providers.yaml`,
`unified-trading-pm/scripts/quality-gates-base/ci-test-cloud-providers.yaml`,
`unified-trading-library/tests/fixtures/cloud-providers.yaml` — all 4 dropped the same orphan `SPORTS:` line under the
folded `features:` key (both clouds), matching `unified-api-contracts@1ff91e5b`.

**Deferred**: the deployment-api `SERVICE_TO_KIND` break (todo 4) — see "Determination (todo 3 re-check)" above for why
it was not fixed in this task.

## Evidence

- Full run: `bash scripts/quality-gates.sh` in `.tabs/3/features-service` — green through STEP 5.92 (17702 passed, 0
  failed, 209 skipped, ~206s), FAILS at STEP 5.104 with 5 asset-group parity violations.
- Pre-existing verification: `git stash push -u -m "wip-check-preexisting-red"` (removed my sports-only diff) →
  `.venv/bin/python scripts/quality_gates/check_asset_group_parity.py` on clean LDR HEAD → byte-identical 5 violations →
  `git stash pop` (restored my diff).
- My own scope (features-service sports `_filter_completed_before` NS-status fix): full `tests/` suite green in
  isolation (17702 passed / 0 failed / 209 skipped, including 3 new tests: `test_ns_status_with_goals_is_included`,
  `test_ns_status_without_goals_still_excluded`, `test_cancelled_status_with_goals_still_excluded`).

## Slot-3 action

Declared repo-blocker `qg_red` for `features-service` via `/api/repo-blockers` and continuing to `/blocked` or idle per
the RULES.md § 4b protocol — my task's own code is finished and correct but cannot ship until this gate is green.
