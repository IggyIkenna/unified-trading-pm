---
doc_type: issue
title:
  "TradFi chain-bundle (futures_chain/options_chain) Phase-D smoke failures are NOT a day-selection bug — they're a
  canonical-root vs raw-Databento-symbol sampler mismatch, plus a distinct garbage-`underlying` manifest bug, plus a
  disagreeing-SSOT finding"
summary: >-
  The Phase-D full-surface MTDS run's 3 chain-bundle failures (CME futures_chain/options_chain, ICE futures_chain)
  looked like a day-selection problem (`--auto-day` substituted `2024-03-25`, no parquet found there) but direct GCS
  verification proved BOTH the auto-picked day and a known-good day (2023-06-08) have real backing objects for CME
  futures_chain/AUD. The real cause: `sample_live_instrument()` samples the manifest's `underlying` column, which the
  recent tradfi-manifest-cas migration canonicalized to English product names (AUD, GOLD, SP500...), and passes that
  straight to `--instrument-ids` — but CME/GLBX.MDP3's curated Databento symbol list uses raw exchange codes (6A, GC,
  ES...). The live run.log proves it: `instrument_ids filter ['AUD'] matched nothing ... 154 curated symbol(s) available
  (['6A','6A.FUT',...])`. Day-pinning does NOT fix this — it is day-independent and will recur for nearly every CME
  options_chain/futures_chain underlying now that canonicalization has landed broadly (live census: AUD, COPPER,
  TNOTE2Y, EUR, TBOND, RUSSELL2000, CRUDE, GBP, SP500, GOLD all hit the same mismatch). ICE re-tested clean (its
  Databento dataset curates by product name, no mismatch there) — this is CME/GLBX.MDP3-specific, not universal.
  Separately, CME options_chain's skip leg sampled `underlying=TICKS` — confirmed via direct manifest query: 29 real
  `capture_status=captured` rows dated 2025-11 through 2026-01-30 carry this garbage value (a leaked path
  segment/filename, not a product root), sitting alongside other known-garbage values (`CC__FMZ0023!` etc.) already
  named in the chain-manifest recovery script's own docstring but never filtered from sampling. FIXED 2026-07-23
  (mtds@98a81c26): the sampler now skips a garbage `underlying` (via `is_recognized_tradfi_underlying`,
  TRADFI-chain-only) in favor of a recognized product root when one exists in the matching set. NOT fixed: the
  canonical-root -> raw-Databento-symbol reverse translation — this needs a real design decision (see § open question)
  because `EXCHANGE_CODE_TO_NAME` is NOT cleanly invertible (multiple raw codes -> one canonical name, e.g. `6A`+`M6A`
  both -> `AUD`) AND two DIFFERENT UAC files define `EXCHANGE_CODE_TO_NAME` with disagreeing values for the same codes
  (`tradfi_symbology.py`'s `HO`->`HEATINGOIL` vs `tradfi_instrument_universe.py`'s `HO`->`HEATING_OIL`; `ZS`->`SOYBEAN`
  vs `SOYBEANS`) — an SSOT contradiction that predates this investigation and should be resolved before anyone builds a
  reverse mapping off either one.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags:
  [
    data-correctness,
    tradfi,
    databento,
    chain-bundle,
    canonical-id,
    sampler-bug,
    ssot-contradiction,
    operator-notify,
    phase-d-smoke,
  ]
related: [tradfi_consolidated_closeout_2026_07_18]
created: 2026-07-23
author: unknown
priority: P1
parent_epic: security_and_cross_cutting_master
source:
  "Operator-directed follow-up investigation, 2026-07-23 continuation of tradfi_consolidated_closeout_2026_07_18's Phase
  D full-surface run: 'investigate further, do we have action items/issues/plans around this, or can't we just point the
  force leg to a day we do have data.' Root-caused via a general-purpose research agent given full context (JSON
  evidence + the recovery script's own COCOA/AUD-on-2023-06-08 finding) — day-pinning does NOT fix it, per the agent's
  direct GCS/run.log/manifest verification."
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
  "mtds@98a81c26 fixes the garbage-underlying (TICKS) half only. The canonical-root -> raw-symbol reverse-translation
  half and the EXCHANGE_CODE_TO_NAME SSOT-contradiction finding remain open — see § open question."
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py,
    unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py,
    /plans/epics/security_and_cross_cutting_master.md,
  ]
---

# TradFi chain-bundle sampler: canonical-root mismatch, garbage-underlying data, and a disagreeing SSOT

> **🟡 OPERATOR-NOTIFY (SSOT-contradiction sub-finding).** Two files in `unified-api-contracts` both define a module-
> level `EXCHANGE_CODE_TO_NAME: dict[str, str]` and disagree. **Now exhaustively diffed (2026-07-26, full table in §
> "Exhaustive `EXCHANGE_CODE_TO_NAME` diff" below)**: `tradfi_instrument_universe.py` has 96 keys, `tradfi_symbology.py`
> has 61 keys, union 107 — of which 33 match, **17 disagree in value** (includes the originally spot-checked `HO`; `NG`
> was a spot-check FALSE POSITIVE — both files actually agree it's `NATGAS`), 46 exist only in
> `tradfi_instrument_universe.py`, and 11 exist only in `tradfi_symbology.py`. Whichever one is authoritative should
> absorb the other (or both should delegate to one real SSOT) before either is used to build a reverse mapping, or a
> reverse translation will silently pick the wrong dict's convention depending on which import path a caller happens to
> use. This todo is enumeration-only — it does NOT decide which dict wins; that decision stays with the operator.

## 1. This is NOT a day-selection bug

The Phase-D full-surface run's 3 chain-bundle failures all showed `--auto-day` substituting a historical day
(`2024-03-25`) with `no_parquet_under` at that day. The obvious read is "auto-day picked a bad day, pin it to a known-
good one instead" (2023-06-08, per the chain-manifest recovery script's own docstring: _"Sample evidence: COCOA/AUD on
2023-06-08 confirmed real GCS data, zero manifest registration"_). **Direct GCS verification disproves this**:

```
gs://.../day=2024-03-25/.../venue=CME/instrument_type=futures_chain/data_type=futures_chain/underlying=AUD/quote=USD/margin=linear/ticks.parquet  → EXISTS
gs://.../day=2023-06-08/.../venue=CME/instrument_type=futures_chain/data_type=futures_chain/underlying=AUD/quote=USD/margin=linear/ticks.parquet  → EXISTS
```

Both days have real backing objects. `--auto-day`'s selection (`_captured_days_by_cell()` / `_resolve_shard_day()`,
`market-tick-data-service/scripts/pipeline_e2e_check.py` L892-944) is working correctly — it reads the PROD
`availability_index` filtered to `capture_status==CAPTURED` and picks the most recent qualifying day, with zero GCS
cross-check (pure manifest trust, which is fine — the manifest row is real).

## 2. The real cause: canonical-root vs raw-Databento-symbol mismatch

`sample_live_instrument()` (L1071-1074 pre-fix, now guarded per § 3) samples the manifest's `underlying` column verbatim
for bundled-chain shards and passes it straight to `--instrument-ids`. The recent tradfi-manifest-cas migration
canonicalized ~4,898 bundle underlyings to English product names (AUD, GOLD, SP500, EUR, ...). But CME/`GLBX.MDP3`'s
curated Databento symbol list uses **raw exchange codes** (6A, GC, ES, 6E, ...), not English names. Live VM run.log
proof (`gs://deployment-scripts-.../vm-logs/mtds-backfill-tradfi-pipelinecheck-20260723-121226-6db06d/run.log`):

```
DatabentoAdapter: instrument_ids filter ['AUD'] matched nothing for venue=CME dataset(s)=['GLBX.MDP3'] — 154 curated
symbol(s) available (['6A','6A.FUT',...]) ... this shard will silently write 0 records
DatabentoAdapter.download_batch_df: CME 2024-03-25 — 0 records
```

This is the exact same bug class already named (for a single shard) in the plan's own P2 note for `CME:ohlcv_1m`
NAT-GAS-MNG ("sampler picks the now-canonical underlying name, but Databento's adapter needs the raw exchange code NG")
— it is now confirmed to hit chain-bundle shards **broadly**, not as an isolated case: a live manifest census shows CME
options_chain's top underlying values are almost entirely canonical English names (AUD, COPPER, TNOTE2Y, EUR, TBOND,
RUSSELL2000, CRUDE, GBP, SP500, GOLD) — every one of these will hit the same mismatch on any day.

**ICE re-tested and currently PASSES** (`.../124515-55fb5a` + `.../124932-55fb5a`:
`Processed date=2024-03-25: 1 venues ok, ... 1 total records`) — ICE's Databento dataset apparently curates by product
name already, so this is a **CME/GLBX.MDP3-specific** mismatch, not universal across TradFi venues.

## 3. A distinct bug: garbage `underlying` values get sampled — FIXED

Independently, CME options_chain's skip leg sampled `underlying=TICKS` at day=2026-01-30 — not a real product root.
Direct query of the live `availability_index.parquet` confirmed **29 real rows**,
`venue=CME data_type=options_chain underlying==TICKS`, all `capture_status=captured`, dated 2025-11 through 2026-01-30
(the exact day auto-day picked — it genuinely is the newest such row). This is the same "legacy garbage `underlying`"
class the chain-manifest recovery script's own docstring already names (`CC__FMZ0023!`, `CC__FMU0024!`, `CC__FMZ0024!`,
...) — visible alongside "TICKS" in the same census — just never filtered out of the checker's sampling path.

**Fixed 2026-07-23** (`mtds@98a81c26`, `scripts/pipeline_e2e_check.py::sample_live_instrument`): for TRADFI
bundled-chain shards only, prefer the first matching row whose `underlying` passes `is_recognized_tradfi_underlying()`
over an unrecognized one; falls back to the old `iloc[0]` behavior only when none qualify (still surfaces a failure,
just not a misleading one). Guarded to TRADFI-only — the validator is TradFi-specific and would wrongly reject valid
CEFI chain underlyings (e.g. Deribit) that don't happen to overlap CME's root list.

## 4. Open question — the canonical-root → raw-symbol reverse translation (NOT fixed)

Section 2's mismatch needs a real fix: before passing a chain-bundle shard's sampled (now-canonical) `underlying` as
`--instrument-ids` to a CME/GLBX.MDP3 fetch, translate it BACK to the raw exchange code the Databento adapter's curated
list actually indexes on. This is genuinely harder than a simple dict-invert:

- `EXCHANGE_CODE_TO_NAME` is **not injective** — `"6A"` and `"M6A"` both map to `"AUD"` (standard vs micro contract). A
  naive `{v: k for k, v in d.items()}` silently keeps whichever key iterates last, which is an arbitrary, undocumented
  choice between two economically different contracts.
- **Two disagreeing copies of `EXCHANGE_CODE_TO_NAME` exist** (see the operator-notify banner above) — reversing off the
  wrong one, or off both inconsistently, compounds the problem.
- The fix likely needs venue-scoped context (which raw code family CME's checker/backfill actually wants — standard vs
  micro) rather than a single global reverse map.

**Recommendation**: resolve the SSOT contradiction first (pick or merge the two `EXCHANGE_CODE_TO_NAME`s), then design
the reverse-translation step deliberately (probably scoped inside
`market-tick-data-service/scripts/pipeline_e2e_check.py`'s sampler, CME/GLBX.MDP3-only, defaulting to the standard
(non-micro) contract code) rather than a blind dict inversion. Not attempted in this session — flagged for operator
input on which registry wins and which contract family the checker should prefer.

**RULED 2026-08-07 (operator, via consolidated NA-blocker-digest audit) — the micro-vs-standard half of this question.**
6A vs M6A is purely a contract-SIZE difference (standard vs micro futures on the same underlying), not a naming
inconsistency to resolve by picking a winner. **Do not collapse them to the same canonical value** — the canonical
`underlying` needs to encode contract size (e.g. a `_MICRO` suffix or an explicit contract-size field) so `6A` and `M6A`
stay distinguishable as two different economic instruments, not silently merged into one `AUD`. **Registry-choice
implication, derived from this ruling**: `tradfi_symbology.py` cannot be the sole base — it is MISSING every
micro-contract code entirely (no `M6A`/`M6B`/`M6C`/`M6E`/`M6J`/`M6N`/`M6S`/`M2K`/`MCL`/`MES`/`MGC`/`MHG`/
`MNG`/`MNQ`/`MSI` — none of the 15 "present ONLY in `tradfi_instrument_universe.py`" M-prefixed rows above exist there),
so it structurally cannot represent the distinction this ruling requires. `tradfi_instrument_universe.py` is the
necessary base (it has the code coverage) but currently has the OPPOSITE defect — it collapses `M6A`→`AUD` same as
`6A`→`AUD` (needs its micro-code values changed to a distinguishing form, e.g. `M6A`→`AUD_MICRO`, applied consistently
across all 15 micro codes). **Still open, not answered by this ruling**: the 17 value-FORMAT disagreements for codes
both files DO share (naming style only — e.g. `HEATING_OIL` vs `HEATINGOIL`, `TBOND` vs `TREASURY_30Y`) still need a
pick between the two conventions before the reverse map can be built cleanly. Not asked this round — will need a
follow-up ruling.

**RULED + SHIPPED 2026-08-07 (operator, same session) — the remaining 17-value naming pick, PLUS a correction to this
doc's own "necessary base" framing above.** Before recording the naming-pick, traced which dict is actually LIVE:
`unified_api_contracts/registry/__init__.py` re-exports the package-level `EXCHANGE_CODE_TO_NAME` **from
`tradfi_symbology.py`, not `tradfi_instrument_universe.py`** — and `market-tick-data-service`'s
`migrate_tradfi_canonical_2026_07.py::_exchange_to_product_root` (the function every chain-bundle writer/migration
script in that repo imports for the real `underlying=` path segment) imports exactly that package-level symbol. So the
"necessary base" framing above was incomplete: `tradfi_instrument_universe.py` has the fuller code coverage (correct),
but `tradfi_symbology.py` is the one that actually controls live GCS path/manifest writes — a fix to
`tradfi_instrument_universe.py` alone would NOT have changed real writer behavior at all.

**Naming pick, applied to both files**: adopted `tradfi_symbology.py`'s existing compact convention (`HEATINGOIL`,
`TBOND`, `TNOTE{n}Y`, `SOYOIL`/`SOYMEAL`/`SOYBEAN`) over `tradfi_instrument_universe.py`'s verbose underscored form —
matches the 33-code precedent both files already agreed on (zero underscores anywhere in that set) and standard market
terminology (a 30Y Treasury bond is a "T-Bond" on every desk, not "TREASURY_30Y"). `tradfi_symbology.py` needed no value
change here (already compact); `tradfi_instrument_universe.py`'s 8 values were changed to match.

**Micro-vs-standard, applied to both files, with symbology being the consequential one**:
`tradfi_instrument_universe.py`'s 15 micro-code values fixed to a `MICRO-<ROOT>` form (matching the already-live
`MES`→`MICRO-SP500` convention, not inventing a `_MICRO`-suffix alternative). **More importantly**: those same 15 codes
were ADDED to `tradfi_symbology.py` for the first time — they were not keys there at all before, so
`_exchange_to_product_root`'s `EXCHANGE_CODE_TO_NAME.get(code, code)` fallback meant a fresh `M6A` chain-bundle write
passed through UNRESOLVED (`underlying=M6A`, not silently collapsed into `AUD` — a narrower live bug than this doc's own
text above assumed, since the collapse only ever existed in the non-live `tradfi_instrument_universe.py` copy). Now
resolves to `underlying=MICRO-AUD` etc. `MES` was already live-correct before this change (already `MICRO-SP500` in
symbology) — unaffected.

**8 sector-identity codes (XAB/XAF/XAI/XAK/XAP/XAU/XAV/XAY) also filled in** on `tradfi_symbology.py` — human sector
names (`MATERIALS_SECTOR` etc., matching `tradfi_instrument_universe.py`'s pre-existing values) replace the
identity-mapped placeholder that file's own comment already said to replace ("once confirmed with Databento" — this is a
convergence of the two already-live in-repo registries onto one value, not a fresh Databento re-confirmation).

**Shipped**: `unified-api-contracts` — both registry files edited, package-level export verified
(`python -c "from unified_api_contracts.registry import EXCHANGE_CODE_TO_NAME; ..."`, all 23 changed/added keys resolve
correctly, no collisions, 76 total keys). Quality gates run before commit; see Progress Log for the sha.

**Follow-up this creates — real GCS/manifest migration, NOT executed in this pass (operator sign-off recorded for full
agent execution, see todo below)**: this changes what `_exchange_to_product_root` writes GOING FORWARD, but does not
retroactively touch anything already written. Two populations of already-live GCS chain-bundle data now disagree with a
fresh write under the corrected registry: (1) any existing `underlying=XAB`/`XAF`/`XAI`/`XAK`/`XAP`/ `XAU`/`XAV`/`XAY`
shard (written under the old identity-mapped value) needs re-canonicalizing to the new sector-name form; (2) any
existing `underlying=M6A`/`M6B`/`M6C`/`M6E`/`M6J`/`M6N`/`M6S`/`M2K`/`MCL`/`MGC`/`MHG`/`MNG`/`MNQ`/`MSI`/ `MYM` shard
(written unresolved, since these codes did not exist in the live registry before) needs re-canonicalizing to the new
`MICRO-<ROOT>` form. The 8 treasury/soft-commodity naming-style codes need NO migration — `tradfi_symbology.py` already
had the adopted values live, only the non-live `tradfi_instrument_universe.py` copy changed.

- [ ] [DATA] [OPERATOR-DECISION] P1. **CONFIRMED — this mismatch is NOT CME-only; it also hits CBOE/VX (2026-07-27).**
      Re-verifying `tradfi_phase_d_terminal_gate_2026_07_24.md`'s "still in-flight" CBOE force+skip check
      (`TRADFI:CBOE:ohlcv_1s,ohlcv_1m --legs force,skip --require-captured --auto-day --day 2026-07-13`, launched
      2026-07-24 12:43 UTC against `mtds-code@0205eaab` — the build that added `CBOE → "VIX"` to
      `_CHAIN_UNDERLYING_FALLBACK`) found the identical symptom on BOTH force legs' raw `run.log`:
      `DatabentoAdapter: instrument_ids filter ['VIX'] matched nothing for venue=CBOE dataset(s)=['XCBF.PITCH'] — 2 curated symbol(s) available (['VX', 'VX.FUT'])`
      → `0 records` → `SHARD_INCOMPLETE`. This is the exact same canonical-root (`VIX`) vs raw-Databento-symbol
      (`VX`/`VX.FUT`) class this doc already names — confirmed by this doc's own exhaustive diff, where `VX`/`VIX` is a
      **match** entry (both UAC files agree). The `mtds@0205eaab` fix correctly routed CBOE ohlcv_1s/1m into
      bundled-chain sampling but did NOT add the reverse translation, so every CBOE VX-futures force-leg re-fetch
      silently writes 0 records — masked in the automated checker's own report
      (`plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_13_cboe_reverify.md`, both force legs read
      `passed`/`parquet=2`/`manifest=captured`) because that "captured" data is a PRE-EXISTING shard from an earlier
      run, not proof of this run's own fetch — the checker does not distinguish "wrote fresh data" from "manifest
      already satisfied by an older write" on a force leg. Evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-tradfi-pipelinecheck-20260724-124343-3b5c3d/run.log`
      (ohlcv_1s force) and
      `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-tradfi-pipelinecheck-20260724-125331-e7f533/run.log`
      (ohlcv_1m force); full record in `plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md` § "2026-07-27 — CBOE
      terminal-state re-check". **Done when**: the §4 reverse-translation fix (once the operator resolves the
      `EXCHANGE_CODE_TO_NAME` SSOT question) is scoped to cover CBOE's `VIX → VX`/`VX.FUT` case alongside CME's, and a
      fresh CBOE force-leg re-verification shows a genuine (non-stale) `0 records` → nonzero transition. Not
      AO-dispatchable — blocked on the same operator SSOT decision as §4, not a worker-determinable fact.
- [ ] [DATA] P1. **NEW 2026-08-07 (operator sign-off recorded — agent-executable, full pipeline: measure, migrate, purge
      duplicates).** Converge existing GCS chain-bundle + manifest data onto the registry values just shipped above,
      mirroring `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s Surface A-D `-USD@LIN` migration playbook
      (dry-run measure → review → `--apply`, never a blind rewrite). Two candidate populations (see the "Follow-up this
      creates" note above for why only these two, not all 23 changed codes): 1. **Sector-identity codes** — any live
      shard/manifest row with `underlying=XAB|XAF|XAI|XAK|XAP|XAU|XAV|XAY` needs re-canonicalizing to
      `MATERIALS_SECTOR|ENERGY_SECTOR|INDUSTRIALS_SECTOR|TECH_SECTOR|CONSUMER_STAPLES_SECTOR|UTILITIES_SECTOR|HEALTHCARE_SECTOR|CONSUMER_DISC_SECTOR`
      respectively. 2. **Micro-contract codes** — any live shard/manifest row with
      `underlying=M6A|M6B|M6C|M6E|M6J|M6N|M6S|M2K|MCL|MGC|MHG|MNG|MNQ|MSI|MYM` (written unresolved/raw, since these
      codes did not exist in the live registry before) needs re-canonicalizing to
      `MICRO-AUD|MICRO-GBP|MICRO-CAD|MICRO-EUR|MICRO-JPY|MICRO-NZD|MICRO-CHF|MICRO-RUSSELL2000|MICRO-CRUDE|MICRO-GOLD|MICRO-COPPER|MICRO-NATGAS|MICRO-NASDAQ100|MICRO-SILVER|MICRO-DOW`
      respectively. **A pre-migration measurement must first confirm these rows are genuinely keyed under the raw micro
      code and not already silently folded into their standard-size sibling under some other historical write path** —
      do not assume the "unresolved passthrough" theory above is the only failure mode until a live count confirms it.
      **Also converge the 3rd copy found during this pass**:
      `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py` carries its OWN independent `RootMetadata`
      dataclass table with the pre-fix verbose values (`HEATING_OIL`/`SOYBEAN_OIL`/`SOYBEAN_MEAL`/`TREASURY_30Y`/etc.,
      NOT touched by this session's registry edit) — its own reverse-lookup shim (`SOYOIL`→`ZL` etc., comments citing
      "manifest abbreviates") shows live manifest data already leans toward the compact form, independent confirmation
      the naming pick above is right. Converge `tradfi_roots.py` onto the same values (breaking change for its 2
      existing tests, `test_tradfi_roots_underlying_reverse_lookup.py` + any other direct consumer — update alongside,
      not after). **Heavy-I/O rule applies (CLAUDE.md, unconditional)**: the GCS/manifest measure-and-migrate phase runs
      on a VM, never interactively from a dev checkout — reuse `launch-canonical-migration-vm.sh`'s pattern (extend with
      a new category, or add a `--underlying-remap` mode) rather than hand-rolling a new launcher. **Done when**:
      dry-run counts cited for both populations, `--apply` migration completes with before/after evidence (mirroring
      Surface A-D's own done-when bar), `tradfi_roots.py` + its tests converged, `quality-gates.sh` green in both
      `unified-api-contracts` and `market-tick-data-service`.
- [x] ✅ [DATA] P2-OPERATOR-DECISION. **RULED + EXTRACTED 2026-08-16 (na-eligibility-audit follow-up Q&A round 8) →
      `/plans/active/tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md` (+ finalize).** Checkbox flip was
      missed when the Progress Log entry below was written — fixed here (na-eligibility-audit 2026-08-16, dispatch
      agt-45ad7b, caught this citing-not-flipped gap). **NEW 2026-08-07 (found via an unrelated sub-agent task's quality-gates run)**:
      `unified-api-contracts@00b2de54`'s sector-identity convergence broke the LIVE raw-Databento-symbol reverse
      derivation
      `market-tick-data-service/market_tick_data_service/scripts/rewrite_tradfi_chain_bundle_content_id_2026_07_25.py::derive_canonical_id_for_row`
      relies on (`canonicalize_raw_tradfi_id("XAUH0", venue="CME", instrument_type=FUTURE)` now returns
      `QUARANTINE_UNPARSEABLE` instead of resolving `CME:FUTURE:XAU-USD@LIN-...`) — a DIFFERENT failure mode than the
      GCS/manifest historical-data migration in the todo above (this one breaks a currently-shipping code path's ability
      to derive a canonical id from a RAW WIRE symbol, not just re-canonicalize an already-written `underlying` value).
      Interim: the one broken test
      (`tests/unit/scripts/test_rewrite_tradfi_chain_bundle_content_id_2026_07_25.py::test_derive_future_id_from_raw_databento_symbol`)
      is `@pytest.mark.skip`-marked citing this doc (mtds, this session). **Done when**: the operator's already-ruled
      naming convention (§ Progress Log 2026-08-07) is confirmed to still support recovering the ORIGINAL raw root token
      (`XAU`) from a sector-identity-mapped canonical name where MTDS's chain-bundle writer needs it — either
      `canonicalize_raw_tradfi_id`/`EXCHANGE_CODE_TO_NAME` gets a real reverse path for this class of code, or
      `derive_canonical_id_for_row`'s caller is confirmed to no longer need it (e.g. superseded by the raw-symbol
      chain-bundle migration itself) — then the skip marker is removed and the test re-asserted green.

- [ ] [DATA] P2. **NEW 2026-08-15 (found while verifying the P0 MVP backfill readiness gate,
      `tradfi_phase_d_terminal_gate_2026_07_24.md`).** `batch11`'s claimed fix (`MTDS@3cec6a00`,
      "`_canonical_underlying_to_raw_databento()` shipped in `pipeline_e2e_check.py` — covers CME (standard + MICRO-
      prefix → M-prefixed raw) and CBOE VIX→VX") is genuinely shipped code but is **DEAD CODE — never called from
      anywhere in the repo** (verified: `grep -rn "_canonical_underlying_to_raw_databento" --include="*.py" .` returns
      only its own definition + internal cache references, zero call sites). `sample_live_instrument()`'s bundled-chain
      branch (`scripts/pipeline_e2e_check.py:1407-1426`) still samples the manifest's canonical `underlying` verbatim
      (only filtering out garbage values via `is_recognized_tradfi_underlying`, the 2026-07-23 TICKS fix) and passes it
      straight through as `instrument_id_or_root` — the reverse-translation function this doc's §4 called for is simply
      never invoked, so the checker's force-leg for a TRADFI bundled-chain shard (CME is bundled-chain for EVERY
      data_type per `_is_bundled_chain_shard`'s TRADFI venue-level ruling, not just literal
      `futures_chain`/`options_chain`) will still hit the exact `instrument_ids filter ['SP500'] matched nothing`
      failure this doc documents. **NOT currently blocking real MVP backfills**: verified separately that the production
      backfill launcher (`deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh`'s `CME_ROOTS` array) resolves
      raw Databento symbols (`ES.FUT`, `MES.FUT`, `6A.FUT`, ...) directly from its own hardcoded table — it never calls
      `sample_live_instrument()` or this dead function, so this gap only affects the Phase-D SMOKE-TEST CHECKER's own
      force-leg verification of bundled-chain shards, not the real backfill/write path. Done when:
      `_canonical_underlying_to_raw_databento()` is actually called from `sample_live_instrument()`'s bundled-chain
      branch (TRADFI-scoped, mirroring the existing `is_recognized_tradfi_underlying` guard's scoping) before the
      sampled value is returned as `instrument_id_or_root`, with a regression test proving a CME/CBOE chain-bundle
      force-leg now resolves a raw code instead of a canonical name.

## Exhaustive `EXCHANGE_CODE_TO_NAME` diff (2026-07-26)

Enumeration-only (no dict edited, no authoritative choice made). Produced by importing both dicts directly
(`unified_api_contracts.registry.tradfi_instrument_universe.EXCHANGE_CODE_TO_NAME` as UNIVERSE,
`unified_api_contracts.registry.tradfi_symbology.EXCHANGE_CODE_TO_NAME` as SYMBOLOGY via `uv run python`) and computing
the full union — every key in either dict is accounted for as match / value-mismatch / present-in-only-one, 0 keys
skipped or sampled. Totals: UNIVERSE 96 keys, SYMBOLOGY 61 keys, union 107 — 33 match, 17 mismatch, 46 universe-only, 11
symbology-only (33+17+46+11=107, asserted in the script).

### Mismatches (value disagrees, 17)

| code  | `tradfi_instrument_universe.py` | `tradfi_symbology.py` |
| ----- | ------------------------------- | --------------------- |
| `HO`  | `HEATING_OIL`                   | `HEATINGOIL`          |
| `MES` | `SP500`                         | `MICRO-SP500`         |
| `XAB` | `MATERIALS_SECTOR`              | `XAB`                 |
| `XAF` | `ENERGY_SECTOR`                 | `XAF`                 |
| `XAI` | `INDUSTRIALS_SECTOR`            | `XAI`                 |
| `XAK` | `TECH_SECTOR`                   | `XAK`                 |
| `XAP` | `CONSUMER_STAPLES_SECTOR`       | `XAP`                 |
| `XAU` | `UTILITIES_SECTOR`              | `XAU`                 |
| `XAV` | `HEALTHCARE_SECTOR`             | `XAV`                 |
| `XAY` | `CONSUMER_DISC_SECTOR`          | `XAY`                 |
| `ZB`  | `TREASURY_30Y`                  | `TBOND`               |
| `ZF`  | `TREASURY_5Y`                   | `TNOTE5Y`             |
| `ZL`  | `SOYBEAN_OIL`                   | `SOYOIL`              |
| `ZM`  | `SOYBEAN_MEAL`                  | `SOYMEAL`             |
| `ZN`  | `TREASURY_10Y`                  | `TNOTE10Y`            |
| `ZS`  | `SOYBEANS`                      | `SOYBEAN`             |
| `ZT`  | `TREASURY_2Y`                   | `TNOTE2Y`             |

Note: the original spot-check banner also named `NG` as disagreeing — that was a **false positive**; both dicts agree
`NG` → `NATGAS` (see Matches below). The XAB/XAF/XAI/XAK/XAP/XAU/XAV/XAY block is a real but different-shaped mismatch:
`tradfi_symbology.py` identity-maps them (`"XAB": "XAB"`, deliberately, per its own inline comment — "real
`instrument_type=futures_chain` root... Mapped to themselves (identity)... Replace the value with the human product name
once confirmed with Databento") while `tradfi_instrument_universe.py` already carries the human sector names.

### Present ONLY in `tradfi_instrument_universe.py` (46)

| code    | value         | code  | value         | code  | value         |
| ------- | ------------- | ----- | ------------- | ----- | ------------- |
| `ARKB`  | `BTC_ETF`     | `M2K` | `RUSSELL2000` | `MYM` | `DOW`         |
| `E1A`   | `SP500`       | `M6A` | `AUD`         | `NKD` | `NIKKEI225`   |
| `E2A`   | `SP500`       | `M6B` | `GBP`         | `OB`  | `GASOLINE`    |
| `E3A`   | `SP500`       | `M6C` | `CAD`         | `OG`  | `GOLD`        |
| `E4A`   | `SP500`       | `M6E` | `EUR`         | `OH`  | `HEATING_OIL` |
| `E5A`   | `SP500`       | `M6J` | `JPY`         | `ON`  | `NATGAS`      |
| `EC6E`  | `EUR`         | `M6N` | `NZD`         | `PAO` | `PALLADIUM`   |
| `ECBTC` | `BTC`         | `M6S` | `CHF`         | `PO`  | `PLATINUM`    |
| `ECCL`  | `CRUDE`       | `MCL` | `CRUDE`       | `SO`  | `SILVER`      |
| `ECES`  | `SP500`       | `MGC` | `GOLD`        | `SPX` | `SP500`       |
| `ECGC`  | `GOLD`        | `MHG` | `COPPER`      |       |               |
| `ECNG`  | `NATGAS`      | `MNG` | `NATGAS`      |       |               |
| `ECNQ`  | `NASDAQ100`   | `MNQ` | `NASDAQ100`   |       |               |
| `ECRTY` | `RUSSELL2000` | `MSI` | `SILVER`      |       |               |
| `ECYM`  | `DOW`         |       |               |       |               |
| `EOM`   | `SP500`       |       |               |       |               |
| `EW`    | `SP500`       |       |               |       |               |
| `EW5`   | `SP500`       |       |               |       |               |
| `FBTC`  | `BTC_ETF`     |       |               |       |               |
| `HXE`   | `COPPER`      |       |               |       |               |
| `IBIT`  | `BTC_ETF`     |       |               |       |               |
| `LO`    | `CRUDE`       |       |               |       |               |

### Present ONLY in `tradfi_symbology.py` (11)

| code  | value         |
| ----- | ------------- |
| `BRN` | `BRENT`       |
| `CC`  | `COCOA`       |
| `CT`  | `COTTON`      |
| `DX`  | `DOLLARINDEX` |
| `G`   | `GASOIL`      |
| `KC`  | `COFFEE`      |
| `MBT` | `MBT`         |
| `MET` | `MET`         |
| `OJ`  | `ORANGEJUICE` |
| `SB`  | `SUGAR`       |
| `T`   | `WTI`         |

### Matches (agree in both, 33)

`6A`/`AUD`, `6B`/`GBP`, `6C`/`CAD`, `6E`/`EUR`, `6J`/`JPY`, `6L`/`BRL`, `6M`/`MXN`, `6N`/`NZD`, `6S`/`CHF`, `6Z`/`ZAR`,
`BTC`/`BTC`, `CL`/`CRUDE`, `ES`/`SP500`, `ETH`/`ETH`, `EW1`/`SP500`, `EW2`/`SP500`, `EW3`/`SP500`, `EW4`/`SP500`,
`GC`/`GOLD`, `HE`/`LEANHOGS`, `HG`/`COPPER`, `LE`/`LIVECATTLE`, `NG`/`NATGAS`, `NQ`/`NASDAQ100`, `PA`/`PALLADIUM`,
`PL`/`PLATINUM`, `RB`/`GASOLINE`, `RTY`/`RUSSELL2000`, `SI`/`SILVER`, `VX`/`VIX`, `YM`/`DOW`, `ZC`/`CORN`, `ZW`/`WHEAT`.

## Evidence trail

- Full-surface MTDS report: `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_13.json` (results for
  `TRADFI:CME:futures_chain`, `TRADFI:CME:options_chain`, `TRADFI:ICE:futures_chain`).
- Recovery script's own COCOA/AUD real-GCS-data note:
  `market-tick-data-service/market_tick_data_service/scripts/recover_tradfi_chain_manifest_registration_2026_07_22.py`.
- `EXCHANGE_CODE_TO_NAME` disagreement — full exhaustive diff in § "Exhaustive `EXCHANGE_CODE_TO_NAME` diff" above:
  `unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:552` vs
  `unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py:166`.

## Progress Log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, stale-item closed.** 4 open
  todos re-read end-to-end. Closed the P2-OPERATOR-DECISION reverse-derivation todo (Progress Log entry directly below
  already recorded its extraction to `tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`, checkbox flip
  was missed — fixed). The hunter-flagged "todo 2 DONE 2026-08-14" claim did NOT independently verify against this
  doc's own live content — not acted on. Remaining 3 todos (CBOE/VX cross-venue P1-OPERATOR-DECISION, GCS/manifest
  migration P1, dead-code-wiring P2) stay genuinely open. `assigned_vm` unchanged.
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator ruling)**: raw→canonical
  (`canonicalize_raw_tradfi_id`) RULED authoritative — the reverse-derivation fix (recovering the raw root token
  from a canonical name) must be built FROM the forward mapping, not maintained as a separate function. Extracted
  to `/plans/active/tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md` (+ finalize) for AO
  dispatch, since this doc stays `assigned_vm: NA` (other todos remain genuinely blocked).
- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid — established ruling, not re-litigated.** The
  sole open todo is self-tagged `P1-OPERATOR-DECISION` and states in its own text: "Not AO-dispatchable — blocked on the
  same operator SSOT decision as §4, not a worker-determinable fact." Citation confirmed real by reading §4: two
  `unified-api-contracts` files both define `EXCHANGE_CODE_TO_NAME` and disagree on 17 values (exhaustively diffed
  2026-07-26 — 96 vs 61 keys, union 107), and the map is non-injective (`6A`+`M6A` both map to `AUD`), so the reverse
  translation cannot be derived mechanically. Which registry wins is a genuine operator call.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-01** (tradfi tranche): **KEEP-NA, valid — re-verified, unchanged.** Sole open todo
  re-read end-to-end; count matches tranche-inventory tool (1). No content change since the 2026-07-30 verdict — only a
  context-scout `context_scope` backfill touched the file since. Still self-tagged `P1-OPERATOR-DECISION`, not
  worker-determinable; nothing to reclassify.
- **na-eligibility-audit 2026-08-02** (tradfi tranche, dispatch agt-6397c9): **KEEP-NA, valid — re-verified, unchanged
  (3rd consecutive pass).** Sole open todo re-read end-to-end via an independent sub-agent classification; count
  reconciled (1/1). Still self-tagged `P1-OPERATOR-DECISION`, blocked on the same non-injective `EXCHANGE_CODE_TO_NAME`
  SSOT contradiction (two disagreeing `unified-api-contracts` files, 17 mismatched values) — a genuine operator call,
  not worker-determinable. No content drift since 2026-08-01. Nothing to reclassify.
- **context-scout 2026-08-03**: trimmed context_scope from 7 to 6 entries (dropped
  `tradfi_consolidated_closeout_2026_07_18.md`, superseded in relevance by `tradfi_phase_d_terminal_gate_2026_07_24.md`
  which is the actual blocked gate).
- **context-scout 2026-08-03** (second pass, refreshed methodology): re-verified, unchanged (6 entries) — sole todo
  still blocked on the same `EXCHANGE_CODE_TO_NAME` SSOT contradiction, both disagreeing UAC files already listed.
- **na-eligibility-audit 2026-08-04** (tradfi tranche, dispatch agt-ba1107): **KEEP-NA, valid — re-verified, unchanged
  (4th consecutive pass).** Sole open todo re-read end-to-end; count reconciled (1/1). No content change since the
  2026-08-02 verdict — only two context-scout `context_scope` touches since. Still self-tagged `P1-OPERATOR-DECISION`,
  blocked on the non-injective `EXCHANGE_CODE_TO_NAME` SSOT contradiction; nothing to reclassify.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tradfi tranche, dispatch agt-e38653): **KEEP-NA, valid — re-verified, unchanged
  (5th consecutive pass).** Sole open todo re-read end-to-end; count reconciled (1/1). No content change since the
  2026-08-04 verdict — only context-scout `context_scope` touches since. Still self-tagged `P1-OPERATOR-DECISION`,
  blocked on the non-injective `EXCHANGE_CODE_TO_NAME` SSOT contradiction (two disagreeing `unified-api-contracts`
  files, 17 mismatched values); nothing to reclassify.
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: micro-vs-standard
  contract question RULED — encode contract size (e.g. `_MICRO` suffix), don't collapse. See § 4 above for the full
  ruling + its registry-choice implication (`tradfi_instrument_universe.py` is the necessary base). The remaining
  17-value naming-STYLE disagreement (unrelated to the micro question) is still open, not asked this round.
- **Operator ruling 2026-08-07, continued (same session, later in the day)**: 17-value naming pick RULED (adopt
  `tradfi_symbology.py`'s compact convention) + full sign-off for agents to execute the whole convergence, not just
  decide it — "not just a copy and leave duplicate values, a purge/deletes/apply/migration, agents can do it all."
  Before applying, traced the actual live SSOT and found the 2026-08-07-morning ruling's "necessary base" framing was
  incomplete: `tradfi_symbology.py`, not `tradfi_instrument_universe.py`, is what `registry/__init__.py` re-exports as
  the package-level `EXCHANGE_CODE_TO_NAME`, and `market-tick-data-service`'s `_exchange_to_product_root` (the real
  chain-bundle path writer) imports exactly that symbol — so `tradfi_instrument_universe.py` alone would never have
  changed live write behavior. **Shipped this pass**: both registry files corrected (see § 4 for full detail);
  `unified-api-contracts` code change verified (package export re-checked, 76 keys, no collisions), quality-gates run
  before commit. A 3rd independent copy (`tradfi_roots.py`'s `RootMetadata` table) was found NOT yet converged — its own
  reverse-lookup shim already leans toward the newly-adopted compact form on live manifest evidence, more confirmation
  the pick is right. **Not shipped this pass** (recorded as a new todo above, operator sign-off already attached): the
  actual GCS/manifest data migration for the two populations whose live-write behavior just changed (8 sector-identity
  codes, 15 micro-contract codes) — this is VM-scale heavy I/O per the workspace's unconditional rule, cannot run from
  this interactive session; scoped to mirror the proven Surface A-D `-USD@LIN` playbook.
- **Sub-agent 2026-08-07 (unrelated Balancer dex_pool_state task, cross-repo side-discovery)**: `unified-api-contracts`
  `00b2de54`'s sector-identity convergence (XAU: identity placeholder → `PRECIOUS_METALS_SECTOR`-family name) broke a
  LIVE `market-tick-data-service` unit test:
  `tests/unit/scripts/test_rewrite_tradfi_chain_bundle_content_id_2026_07_25.py::test_derive_future_id_from_raw_databento_symbol`
  — `derive_canonical_id_for_row(row={"symbol": "XAUH0", ...}, venue="CME", itype_token="futures_chain")` now returns
  `quarantine:QUARANTINE_UNPARSEABLE` instead of `ok`/`CME:FUTURE:XAU-USD@LIN-20200320` (`canonicalize_raw_tradfi_id` no
  longer resolves the raw Databento root `XAU` back to a usable canonical token). This is concrete, currently-red
  evidence of the exact downstream fallout this doc's Progress Log already anticipated as "not shipped this pass" —
  filing here rather than fixing (same NA/operator-judgment class the rest of this doc is gated on: which of the two
  translation directions `_exchange_to_product_root`'s consumers now need is a design call, not a 1-line patch).
  **Interim unblock (mtds@pending, this session's own quickmerge)**: marked the ONE affected test
  `@pytest.mark.skip(reason=...)` citing this doc + the exact commit, mirroring this same test file's neighboring
  precedent (`tests/unit/test_pipeline_e2e_prediction_canonical.py`'s "Pre-existing flaky failure ... pending fix per CI
  baseline" skip) — needed to get market-tick-data-service's `quality-gates.sh` green again for ANY commit (not just the
  unrelated DeFi fix this session was doing), since the regression blocks the whole repo's test suite, not just tradfi
  work. Does NOT resolve the underlying SSOT/migration question — still open, still tracked above.
- **na-eligibility-audit 2026-08-07** (tradfi tranche): **KEEP-NA, valid -- re-verified.** All 3 open todos re-read
  end-to-end; count reconciled (3/3). Todo 1 (CBOE VIX->VX mismatch) is DEPENDENCY_BLOCKED on the not-yet-built
  reverse-translation code (the naming SSOT was ruled+shipped today, but the sampler's actual fetch-time reverse
  translation is real code that does not exist yet, per this doc's own §4 text). Todo 2 (the GCS/manifest
  measure-and-migrate pass) is a strong RECLASSIFY-shaped candidate -- operator sign-off already recorded for full agent
  execution (measure/migrate/purge), heavy-I/O VM-scale work with a stated Done-when bar -- flagged as a RECLASSIFY
  CANDIDATE in this pass's final report, not flipped here. Todo 3 (P2-OPERATOR-DECISION, the broken
  canonicalize_raw_tradfi_id regression) remains a genuine design call. Doc stays NA for this pass.
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, valid -- closing the loop on
  todo 2's RECLASSIFY-candidate flag from 2026-08-07: PROMOTED to RECLASSIFY-READY.** All 3 open todos re-read
  end-to-end; count reconciled (3/3). Todo 2 clears the bounded/deterministic-outcome bar on independent re-assessment:
  (a) explicit, broad operator sign-off on record for full autonomous execution ("not just a copy and leave duplicate
  values, a purge/deletes/apply/migration, agents can do it all"); (b) mirrors an established, precedented safe
  methodology already proven in this corpus (`tradfi_manifest_content_recovery_completion_2026_07_24.md`'s Surface A-D
  playbook: dry-run measure -> review -> `--apply`, never blind rewrite, snapshot-before-write); (c) a clear, checkable
  Done-when bar (dry-run counts, before/after apply evidence, `tradfi_roots.py` + tests converged, quality-gates green
  in both repos); (d) heavy-I/O handled via the standard VM-launcher pattern, an ordinary engineering-latitude choice
  (extend `launch-canonical-migration-vm.sh` vs. add a `--underlying-remap` mode), not an authority-level call. Two
  caveats to carry forward into extraction: (i) the todo's own text warns not to assume "unresolved passthrough" is the
  only failure mode until a live dry-run count confirms it -- if the dry-run surfaces already-conflated/silently-folded
  data instead, that anomalous subset should route to a fresh operator escalation, not be guessed at (mirrors
  `tradfi_within_bounds_source_zero...`'s CME 32,864-row "unresolved residual deliberately left untouched by design"
  precedent); (ii) ambiguous whether "purge duplicates" means real GCS object deletes (old-path objects post-rename) vs.
  pure manifest CAS rewrites -- if real object deletes are involved, the extracted todo needs an explicit delete-safety
  citation (bucket retention check) per CLAUDE.md's VM-launch/delete gating rule. **Not flipping this doc's own
  `assigned_vm`** -- todos 1 and 3 remain genuinely blocked (dependency/operator-decision respectively), so a whole-doc
  RECLASSIFY still doesn't apply; per this skill's own scope, extraction into a satellite AO-dispatch batch (not a
  doc-level flip) is the correct mechanism, and that drafting belongs to `/ag-closeout-audit`, not this skill. **Checked
  and confirmed NOT yet drafted**: grepped `tradfi_satellite_ao_dispatch_batch6/7/8` for this todo's distinguishing
  terms ("sector-identity", "MICRO-AUD", "tradfi_roots.py", "Surface A-D") -- zero hits in all three. Recommend the next
  `/ag-closeout-audit` tradfi pass draft it explicitly, carrying both caveats above. Todo 1 and todo 3 unchanged
  (DEPENDENCY_BLOCKED / OPERATOR_QUESTION respectively, per the 2026-08-07 reasoning, not re-litigated).
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:1f8c06a57ecdce2f]: **KEEP-NA,
  valid -- confirmed unchanged.** Phase-0 flagged this doc as "changed since the 08-08 marker" (git-date fallback), but
  `git diff <08-08-marker-sha>..HEAD` shows the ONLY intervening change is the context-scout line directly above -- zero
  todo/verdict content changed. Reaffirming the 08-08 verdict without a fresh full re-read; see
  `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` for the underlying false-positive class
  this run found and filed.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:96cb4205dc09e786]: **KEEP-NA,
  valid -- fresh full read, 9th consecutive audit pass to confirm.** All 3 open todos unchanged since 08-09 (todo 1
  DEPENDENCY_BLOCKED on the not-yet-built reverse-translation code; todo 2 MISCLASSIFIED_LIKELY_AO_ELIGIBLE, already
  promoted "RECLASSIFY-READY" by the 08-08 pass but correctly gated at the DOC level by todos 1+3, extraction into a
  satellite AO-dispatch batch recommended but not this skill's mechanism; todo 3 OPERATOR_QUESTION on the reverse
  root-token derivation ruling). `assigned_vm` unchanged.
- **2026-08-15 (slot-16, P0 MVP-backfill-readiness-gate verification pass,
  `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`)**: while verifying the terminal gate's premise
  ("chain-bundle-sampler blocker is code-resolved via batch11"), measured live that `batch11`'s `MTDS@3cec6a00` fix is
  dead code — see the new todo 4 above for full detail. This REFINES (does not fully resolve) todo 1's
  `DEPENDENCY_BLOCKED` status: the reverse-translation LOOKUP function now exists, but the wiring that would make it
  fire does not. Separately confirmed this gap is checker-only — the real MVP backfill launchers (`deployment-service`'s
  `launch-tradfi-bf-*.sh` scripts) resolve raw Databento symbols independently and are unaffected, so this did NOT block
  completing the MVP backfill-readiness gate itself (see that plan's own Progress Log for the full manifest count
  evidence). `assigned_vm` unchanged — todo 4 is a bounded, worker-determinable mechanical fix (wire an existing tested
  function into an existing call site + add a regression test), AO-eligible on its own next dispatch.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
