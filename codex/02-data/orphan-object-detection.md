---
doc_type: codex-ssot
title: Orphan object detection — the GCS object with no manifest row and no oracle expectation
summary: >-
  Defines an ORPHAN in terms of the four canonical surfaces (a real parquet on GCS with NO manifest atom and outside the
  UAC expected-coverage set), states precisely which existing tool does and does not see it, and gives the detection
  route that honours single-walk discipline. Corrects the widespread claim that NO tool covers the inverse case —
  `migration_orphan_sweep.py` class-E does, but it is the ONLY one, it requires the whole-corpus walk, and it has three
  VERIFIED structural blind spots that make specific real corpora invisible by construction. Exists because the
  delete-suggestion feature IS orphan detection: an undefined orphan oracle means unsafe deletes.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos: [instruments-service, unified-api-contracts, unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags: [orphan, gcs, manifest, reconciliation, delete-safety, single-walk, canonicalisation, data-correctness, class-e]
related:
  [
    four-surface-reconciliation-procedure.md,
    reconciliation-finding-taxonomy.md,
    gcs-and-manifest-delete-safety-protocol.md,
    non-canonical-path-inventory.md,
    canonical-cutover-register.md,
    availability-manifest-and-data-status.md,
    ../05-infrastructure/gcs-object-operations.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    orphan object definition,
    orphan detection coverage gaps in existing tooling,
    orphan detection under single-walk discipline,
  ]
referenced_by: [codex/02-data/canonical-cutover-register.md]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    instruments-service/scripts/migration_orphan_sweep.py,
    unified-api-contracts/unified_api_contracts/registry/possible_manifest.py,
    unified-trading-library/scripts/detect_manifest_divergence.py,
  ]
---

# Orphan object detection

> **Not to be confused with [`../04-architecture/orphan-audit.md`](../04-architecture/orphan-audit.md).** That doc is
> the **UI orphan-ROUTE** policy — Next.js / React-Router pages with no nav-surface reachability. It shares only the
> word "orphan". There is **no overlap in subject, tooling, or remediation**; this doc is about GCS objects. Neither doc
> extends the other.
>
> **This doc REFERENCES, it does not duplicate.** The four surfaces and the comparison loop →
> [`four-surface-reconciliation-procedure.md`](four-surface-reconciliation-procedure.md). The finding vocabulary and
> accepted exceptions → [`reconciliation-finding-taxonomy.md`](reconciliation-finding-taxonomy.md). The proof required
> before any delete → [`gcs-and-manifest-delete-safety-protocol.md`](gcs-and-manifest-delete-safety-protocol.md). This
> doc answers only: **what is an orphan, why is it invisible, and how do you find it without a new corpus walk.**

---

## §1 — What an orphan IS, in terms of the four surfaces

An **orphan** is an object that exists on surface 1 and on no other surface:

| Surface                    | Orphan state                                               |
| -------------------------- | ---------------------------------------------------------- |
| **1. GCS object path**     | **PRESENT** — a real parquet, `row_count > 0`              |
| **2. Parquet content**     | present (it is real data; that is what makes it dangerous) |
| **3. Manifest shard atom** | **ABSENT** — no `_index` row covers it                     |
| **4. Catalogue / oracle**  | **ABSENT** — outside the UAC expected-coverage set         |

Both absences are required. Drop either one and it is a different, already-named finding:

| Surface 1 (disk) | Surface 3 (manifest) | Surface 4 (oracle) | Finding                                             |
| ---------------- | -------------------- | ------------------ | --------------------------------------------------- |
| present          | absent               | absent             | **ORPHAN** — this doc                               |
| present          | absent               | present            | `MISSING_EXPECTED` — oracle-driven, already covered |
| present          | present              | —                  | manifested (canonical, or a legacy twin)            |
| absent           | present              | —                  | **phantom** — a row claiming data that is not there |
| absent           | absent               | present            | `true_gap` — honest absence                         |

The orphan is the **exact inverse of the phantom**, and this is why it is under-tooled: every reconciler in the estate
starts from a manifest row or an oracle expectation and asks "is the object there?" The orphan is the object that
**nothing ever asks about**, because no row and no expectation names it. It can only be found by starting from the disk.

**Why an orphan is a correctness defect, not just untidiness:**

- It is **real data that no reader can find** — readers resolve paths from the manifest, so an orphan is invisible to
  the pipeline while still being billed for.
- It **silently deflates coverage** — the cell reads as a gap while the data exists.
- It is a **delete hazard in both directions**: deleted as "junk", it was the only copy; kept as "probably a duplicate",
  it hides a real capture hole. See §4.

---

## §2 — Why it is (nearly) invisible today — VERIFIED tool by tool

> **Correction to a widely-repeated claim.** The Phase-0 audit synthesis states that the orphan case is covered by _no_
> current tool. **That is false as stated, and this doc does not launder it.** `migration_orphan_sweep.py` defines and
> emits exactly this class. The true finding is narrower and more useful: **it is the ONLY tool that does, it requires
> the whole-corpus walk, and it has three verified blind spots.**

### 2a. The one tool that DOES see orphans

`instruments-service/scripts/migration_orphan_sweep.py` classifies every object in an asset_group bucket into exactly
one of six classes; class **E** is the orphan:

- `ObjectClass.ORPHAN_REAL = "E_orphan_real"` (`migration_orphan_sweep.py:101`)
- returned at `:363` with reason `"real data (rows>0) with NO manifest row — backfill record_captured"`
- acceptance bar is `orphan_class_E == 0` per AG (`:35`), and the report exits non-zero unless class-E is 0 **and** the
  prefix taxonomy has no `unknown` label (`:638-639`)

Its orphan test is manifest-coverage-aware in the correct, grain-tolerant way: `is_covered()` treats blank manifest
fields as **wildcards in both directions** (`:393-409`), because the manifest is keyed at a coarser grain than the
per-instrument object path. An exact 5-tuple match would false-flag nearly every object; the 2026-06-10 smoke caught
this as prediction class-A = 0 (`:347-351`).

### 2b. Blind spot 1 — top-level prefix labels short-circuit the orphan logic _(the dangerous one)_

`classify_object` resolves a prefix label **first**, and returns immediately as `NON_DATA` / `MANIFEST_INFRA` before any
manifest lookup happens (`:312-316`). Anything in the label table is therefore **excluded from the A/B/D/E logic
entirely** — the source comment says so explicitly: _"EXCLUDED from the raw-orphan A/B/D/E logic (NEVER deleted by this
sweep)"_ (`:106-107`).

`_NON_DATA_TOP_LEVEL_LABELS` (`:137-145`) includes:

```python
"dex_pools/": "legacy-data",
"lending_indices/": "legacy-data",
```

**So the two DeFi legacy top-level trees at the centre of the B1 delete incident are, by construction, incapable of
being reported as orphans by the only orphan-detecting tool in the estate.** They are labelled "understood", which is a
statement about the _taxonomy_ (0 `unknown` prefixes is the CF-17 bar) — not a statement that their contents are
manifested. They are not.

This is the single most important fact in this doc: **a prefix being labelled means the sweep stops asking whether its
contents are orphaned.** Any new non-canonical top-level tree added to that table inherits the same blindness.

### 2c. Blind spot 2 — the classified corpus is only raw tick data

`_DATA_PREFIXES = ("raw_tick_data/", "day=")` (`:113`). Everything else is other-corpus and labelled out:
`processed_candles/`, `processed_data/`, `features/` (`:158-163`). The exclusion is deliberate and correct in itself —
the 2026-06-10 smoke mis-read 7,946 processed-candle objects as class-E before the label existed (`:109-112`).

The source comment asserts these corpora _"have their own re-runnable sweep"_ (`:112`).

> **UNVERIFIED.** This agent grepped for a processed-candle / features orphan sweep and found only migration and rebuild
> scripts (`_rebuild_processed_corpus.py`, `migrate_legacy_tick_buckets_to_canonical.py`, `audit_legacy_paths.py`), **no
> orphan sweep for those corpora**. A 0-hit grep is not proof of absence and these are runtime-resolved codebases, so
> this is recorded as an open question (§6), not as a finding.

### 2d. Blind spot 3 — `JUNK` absorbs unattributable real data

An object whose hive key cannot be parsed, or falls outside the valid could-exist space, returns `JUNK` at `:324-325`
and `:345-346` — **before `row_count` is ever consulted**. Only the step-5 `JUNK` return (`:361-362`, refined by the
lazy footer read at `:570-573`) is row-count-gated.

Consequence: **a real, rows-greater-than-0 parquet with a missing or unparseable `data_type=` hive segment is
indistinguishable from a zero-row shell in the output.** Both land in class D.

The out-of-space gate is narrower than it first appears, and this is a point in the tool's favour — `is_valid_shard_key`
deliberately **admits** rather than rejects the unknown: an unmapped `instrument_type` returns `True`
(`possible_manifest.py:423-425`), a non-canonical `data_type` passes through (`:402-406`), and venue is intentionally
not gated at all (`:409-412`). So class D is reached mainly via a blank `data_type` or an unknown asset_group
(`:415-418`) — but that is exactly the shape a legacy pre-hive tree has.

The mitigations elsewhere in the walk are sound and should be preserved by anything that reuses it: `row_count=None` is
treated as non-zero, i.e. the object **stays** class-E (`:306-309`), and the footer read is bounded to <256KB candidates
because only a small object can be a 0-row shell (`:566-570`). Both err toward surfacing, which is correct.

### 2e. Every other tool is manifest-row-driven or oracle-driven

Verified, and none of them can see an orphan:

| Tool                                     | Starts from                      | Sees an orphan?          |
| ---------------------------------------- | -------------------------------- | ------------------------ |
| `reconcile_phantom_manifest_rows_all.py` | manifest rows                    | No — inverse question    |
| `detect_manifest_divergence.py`          | UAC `expected_coverage()` oracle | No                       |
| `reconcile_market_tick_manifest.py`      | manifest ⇄ scoped object listing | Partially, in-scope only |
| `validate_shards_4pillar.py`             | sampled known shards             | No                       |
| `manifest_hygiene_daily.py`              | composes the above (index-only)  | No                       |

The decisive one is `detect_manifest_divergence.py`: its `MISSING_EXPECTED` (`:219`) is computed by joining the UAC
`expected_coverage()` oracle (`:51-53`, `:117`) against the index. **`MISSING_EXPECTED` is an oracle statement, never a
disk listing** — so an object outside the oracle's expected set cannot produce one. That is precisely the orphan.

---

## §3 — Detecting an orphan without a new whole-corpus walk

**The structural fact that governs everything here:** orphan detection is the one reconciliation question that
**cannot** be answered in manifest-driven mode. Manifest-driven means the manifest supplies the work list — and an
orphan has no manifest row. You cannot enumerate orphans from the index, by construction, at any cost.

This collides head-on with single-walk discipline: any new whole-corpus GCS walk is **review-blocking**
(`availability-manifest-and-data-status.md:1635-1642`). Manifest-index reads are exempt (`:1655-1656`) — but they are
exactly what does not work here.

The three sanctioned no-walk routes are enumerated in
[`four-surface-reconciliation-procedure.md`](four-surface-reconciliation-procedure.md) §5 and are not restated. Their
application to **this** question is asymmetric, and that asymmetry is the operative rule:

| Route                                        | Use for orphans                                                                                                                     |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1 — prefix-scoped listing from manifest rows | **CONFIRM only.** Cannot enumerate — the prefixes come from the rows an orphan lacks.                                               |
| 2 — delimiter-based child-prefix listing     | **DISCOVER candidate trees only.** Enumerates prefixes, not objects — cheap, and it is how an unexpected top-level tree is spotted. |
| 3 — reuse of the existing single walk        | **The ONLY enumeration route.** Bundle onto `migration_orphan_sweep.py`'s one snapshot.                                             |

**The rule:** orphan _enumeration_ rides route 3 or does not happen. A reconciliation pass that needs orphan coverage
does **not** open its own walk — it bundles its question onto the existing sweep, per §9's standing instruction to fold
new passes into the ongoing single walk. Routes 1 and 2 are for confirming or scoping a _suspected_ orphan, and are
legitimate on their own.

**Corollary — the honest reporting obligation.** Because enumeration is gated on a walk that most runs will not perform,
a reconciliation report MUST NOT state "0 orphans" off a manifest-driven pass. The truthful verdict is
**`orphans: NOT ASSESSED (no walk in this run)`**. Reporting an unmeasured 0 here is the same class of error as quoting
a coverage percentage without naming its formula.

---

## §4 — Relationship to the delete-suggestion feature

**The delete-suggestion feature IS orphan detection, run in the opposite direction.** "This object can be deleted" is
the claim "this object is a redundant twin of a manifested canonical object" — and its negation is "this object is the
only copy", i.e. an orphan. There is no third state. **An undefined orphan oracle therefore does not merely weaken
delete suggestions; it makes them unsafe**, because the check that would have said "stop" is the one that was never
defined.

This is not hypothetical. The **R5 near-miss** (recorded in
`plans/active/defi_consolidated_closeout_2026_07_18.md:467-479`):

- Two live plan docs authorised a batch DELETE of the `dex_pools/` + `lending_indices/` top-level trees as "dead
  prefixes".
- A later **content**-verify in the same plan overturned it: legacy = 98 pools, canonical = 99, **intersection only 66**
  — PARTIAL OVERLAP, not duplication — with **32 legacy-only high-TVL Raydium pools absent from canonical** (XMR/USDC
  $47M, BNB/USDC $18M, USD1/USDC $9.9M, ZEC/USDC $7.5M).
- A live GCS probe on 2026-07-20 sharpened it further: for **KAMINO `dex_pool_state` and SOLEND the canonical twin count
  is 0** — for those cells the legacy objects are **the only copy in existence**.
- `execution-service/execution_service/providers/solana_amm_depth_provider.py:41` **still reads the legacy shape at
  runtime**.
- Disposition is now **FOLD-not-delete**, and _"a snapshot-first delete is NOT adequate protection."_

Now close the loop with §2b: **those two trees are exactly the ones the orphan sweep cannot classify**, because
`dex_pools/` and `lending_indices/` are label-excluded at `migration_orphan_sweep.py:140-141`. The delete order was
authored against a corpus the orphan oracle was structurally blind to. The near-miss was caught by a **content** verify,
not by the tooling.

Three durable rules follow:

1. **Existence of a twin is not evidence. Content equality is.** Path construction and object counts both said
   "duplicate"; only reading the content said "no". This is part-2 of the five-part proof
   ([`gcs-and-manifest-delete-safety-protocol.md`](gcs-and-manifest-delete-safety-protocol.md)) and is not restated
   here.
2. **A label-excluded prefix must be treated as `unknown` disposition, never as delete-eligible** — the sweep's silence
   about it is an artifact of the label table, not a finding of redundancy.
3. **Orphan status must be resolved BEFORE any delete suggestion rises above `unknown`.** Where orphan status is
   `NOT ASSESSED` (§3), the disposition ceiling is `unknown`, full stop.

---

## §5 — Open questions — stated, not decided

- **Do `processed_candles/` / `processed_data/` / `features/` have an orphan sweep?** The source comment asserts one
  exists (`migration_orphan_sweep.py:112`); this agent could not find it (§2c). Until someone reads the candidate
  consumer and confirms, those corpora have **no known orphan coverage** and any delete suggestion touching them is
  capped at `unknown`.
- **Should the label table gain an "excluded but unmanifested" third state?** Today a prefix is either classified or
  label-excluded, and exclusion is silent. A third label — understood, but contents not manifest-checked — would have
  made the `dex_pools/` blindness visible at CF-17 acceptance time instead of at delete time. Not proposed as a change
  here; recorded as the design question the near-miss raises.
- **Is class D splittable?** Separating "zero-row shell" from "real data, unattributable path" (§2d) would surface a
  category that is currently invisible. This has a real cost — it needs a footer read for objects the walk currently
  skips — so it is a trade-off to rule on, not an obvious fix.

---

## §6 — Maintaining this doc

- **Adding a prefix to `_NON_DATA_TOP_LEVEL_LABELS` is a coverage-reducing change.** Record it here in the same turn,
  with whether its contents are known-manifested. A label added without that check silently creates a new blind spot.
- **Never report an unmeasured `0 orphans`.** `NOT ASSESSED` is the correct verdict for a manifest-driven run (§3).
- **A new whole-corpus walk is not the answer to a gap in this doc.** Bundle onto the existing sweep (§3, route 3).
