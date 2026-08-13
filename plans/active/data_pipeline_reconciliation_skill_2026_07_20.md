---
doc_type: plan
title: /data-pipeline-reconciliation — per-asset-group four-surface canonicalisation reconciliation skill
summary: >-
  Build the SSOT-backed `/data-pipeline-reconciliation` skill that, per asset_group, reconciles the FOUR canonical
  surfaces — GCS object path, parquet content columns, manifest shard-atom key, and the catalogue/data-status render —
  across PROD buckets only, and emits typed findings plus proof-gated delete SUGGESTIONS. Phase A first closes the
  documented-understanding gap the audit exposed — 33 codex/plan contradictions (4 BLOCKING) and 12 missing codex SSOTs
  — because a skill that encodes its own canonical definition is unauditable by the workspace's own SSOT rule.
  **Standing reference surface, not an archival candidate** (resolved
  `autonomous_session_operator_decisions_2026_07_25.md` entry #10, 2026-07-26, option A) — 0 open / 42 done as of
  `unified-trading-pm@7ae64f4c2` is expected here, not a lifecycle signal, per
  `cross_cutting_consolidated_closeout_2026_07_25.md` Track 13, which keeps this "as a pure cross-reference, not
  something to close" — it is also the cited home of the D1/D2 rulings `cursor-configs/CLAUDE.md`'s reconciliation
  section leans on. Keep `status: active` in `plans/active/`.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service, instruments-service, execution-service]
scope: [engineer, admin]
tags: [canonicalisation, reconciliation, skill, manifest, gcs-paths, catalogue, delete-safety, ssot, per-asset-group]
related:
  [
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/pipeline-mode-partition.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
created: 2026-07-20
last_updated: 2026-07-30
parent_epic: manifest_master
assigned_vm: NA
archive_exempt: true # standing reference surface, operator ruling entry #10 option A — 0 open todos expected here
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
drift_direction: advance-docs
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: operator request 2026-07-20 — "per-AG skill /data-pipeline-reconciliation, audit first then plan then execute"
context_scope:
  [
    /cursor-configs/skills/data-pipeline-reconciliation/SKILL.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/orphan-object-detection.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
  ]
---

# /data-pipeline-reconciliation — per-asset-group canonicalisation reconciliation skill

> **Origin**: operator request 2026-07-20 — a per-asset-group skill that checks 100% canonicalisation across GCS paths,
> the availability manifest, and the catalogues (instruments / features / ml / strategy), over **PROD buckets only**,
> flags non-canonical prefixes such as `market-data-tick-defi-prd-…/dex_pools`, and **suggests deletes** where a
> canonical twin already holds the data. Related to but separate from the backfill smoke skills
> (`/data-pipeline-check-is`, `/data-pipeline-check-mtds`) — those are **statically audited here, never run**.
>
> **Codex SSOTs**: `/codex/02-data/cross-asset-canonical-target-ssot.md` (master tie-breaker) ·
> `availability-manifest-and-data-status.md` · `honest-coverage-model.md` · `defi-canonical-naming-ssot.md` ·
> `pipeline-mode-partition.md` · `/codex/05-infrastructure/bucket-isolation-model.md` ·
> `/codex/05-infrastructure/gcs-object-operations.md`. This plan **references** them; it does not duplicate them.

---

## 🔴 Operator-blocking findings from the Phase-0 audit (read before executing anything)

The 9-dimension audit (2026-07-20) found the estate is not merely un-reconciled — the **documented record itself
disagrees with itself in 33 places, 4 of them BLOCKING**. The skill cannot claim SSOT status until these are ruled,
because it would have to pick a side silently.

**B1 — `dex_pools/` MUST NOT be deleted. The delete order in two live plan docs is stale and would destroy data.**
`defi_consolidated_closeout` Track 2 and `canonical_closeout_open_questions` §A6 both authorize a batch DELETE of the
"dead Shape-B `dex_pools/` + `lending_indices/` top-level prefixes". The **same plan's later R5 content-verify
overturned that verdict**: PARTIAL-OVERLAP, fold-not-delete — legacy=98 pools, canon=99, intersection only **66**, with
**32 legacy-only high-TVL Raydium pools absent from canonical** (XMR/USDC $47M, BNB/USDC $18M). And `execution-service`
**still references the legacy shape at runtime** (`providers/solana_amm_depth_provider.py:41`). Track 2 and A6 were
never updated after R5.

> **Correction 2026-07-20 (self-inflicted, caught by the P0-01 agent — recorded because the failure mode matters more
> than the fix).** This section originally claimed the canonical twin was **VERIFIED ABSENT**, citing an audit probe
> where `venue={ORCA,RAYDIUM,KAMINO,SOLEND}` returned zero objects. **That claim was wrong.** The probe used
> `instrument_type=pool`; Solana AMM venues write `instrument_type=solana_amm_pool`. Re-probed 2026-07-20: ORCA and
> RAYDIUM have **14,241 canonical objects** on `day=2026-04-14` (ORCA 14,094 · RAYDIUM 100 · KAMINO
> `lending_indices` 47) — while **KAMINO and SOLEND `dex_pool_state` are genuinely zero**.
>
> The verdict is UNCHANGED (**do not delete**) but now rests on the correct reason, and is _stronger_: RAYDIUM canonical
> = 100 objects against R5's `canon=99` independently corroborates R5's PARTIAL-OVERLAP measurement, and KAMINO/SOLEND
> confirm R5's "2 known-UNIQUE cells" where the legacy objects are the **only** copy. A wrong absence claim would have
> been laundered into an SSOT had the agent not re-probed. **Lesson, now encoded in the skill (§ 4b):** an absence
> result is evidence only once you have confirmed you probed the vocabulary the writer actually emits.

**B2 — manifest `instrument_type` COLUMN case (C2a).** `cross-asset-canonical-target-ssot.md` §7/§11 says LOWERCASE;
`tradfi_consolidated_closeout` Phase-B says UPPERCASE with the catalogue as SSOT — **both citing the same operator on
the same date (2026-07-18)**, and both cefi and tradfi have **already shipped scripts that uppercase the column**. The
tradfi plan contradicts itself _within one file_ (its own worklist orders the fold in the opposite direction). This
determines the direction of **>12M row rewrites**. Undecidable from documents.

**B3 — DeFi flat `LENDING` instrument_type.** Codex §5 asserts `LENDING` is RETIRED (A_TOKEN/DEBT_TOKEN split, ~16.7M
rows scheduled); the retire was **reversed** in code because it broke 5+ MTDS lending writers into
`attempted_failed`/zero-data. Codex currently asserts a state the code deliberately does not implement.

**B4 — honest-coverage formula.** Three incompatible definitions across three `status: current` codex docs. The live,
CK3-certified one is `honest-coverage-model.md`'s
`reachable_coverage = captured/(captured+attempted_failed+expected_unattempted)` with `empty_confirmed` EXCLUDED. Until
banners land, any % the skill prints is unfalsifiable.

**Consequence for the skill's delete feature**: deletes are **SUGGESTIONS ONLY**, gated on a five-part proof (§ P0-05).
Prod-bucket deletes, legacy-after-copy deletes, the tradfi `batch_massive` 1.47M-object purge, and anything touching
`instrument_type` casing are **human-only hard-stops** the skill never crosses autonomously.

---

## ✅ OPERATOR DECISIONS — ALL THREE RULED 2026-07-20

> **RULED 2026-07-20 (operator, in-session).** All three axes below are now DECIDED. The option-sets are retained
> underneath for the record — read the ruling first; the tables are history, not live questions.
>
> | Ref    | Ruling                             | Note                                                                                                                                                                                                                      |
> | ------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | **D1** | **B — UPPERCASE** (catalogue wins) | Operator: _"uppercase is fine"_. Explicitly a **cost** argument, not a correctness one — it is the only option where the shipped code and the >8M already-migrated rows agree. The revert is mechanical if ever reversed. |
> | **D2** | **B — complete the FULL retire**   | **Against the worker recommendation** (which was to ratify the interim). Recorded as the operator's deliberate choice.                                                                                                    |
> | **D3** | **A — fold → repoint → delete**    | Matches the R5 overturn and the corrected Track 2 / §A6.                                                                                                                                                                  |
>
> **D1 consequences (UPPERCASE column):** the manifest `instrument_type` COLUMN is UPPERCASE. The **path** segment stays
> lowercase and the **id** middle segment stays UPPER — both were never in question. This _ratifies_ the two
> already-shipped uppercase migration scripts (`instruments-service@555ddf1c` + the tradfi Phase-B script), so the
> DRAIN-GATED freeze on them is **lifted**. Codex `cross-asset-canonical-target-ssot.md` §7/§11 must be corrected
> lowercase→UPPERCASE **for the column only**, and the tradfi closeout's self-contradicting worklist (which orders a
> case-fold in the opposite direction, 750,715 rows) must be corrected to fold UP. The skill stops refusing this axis
> and begins enforcing UPPERCASE for the column.
>
> **D2 consequences (full retire) — HARD PREREQUISITE, do not skip:** the retire was attempted once and **reversed**
> because it broke 5+ MTDS lending writers into `attempted_failed`/zero-data and desynced the shard atom (GCS
> `instrument_type=a_token` vs manifest `lending`). Re-executing it in the same order reproduces that outage. Required
> order: **(1) fix the 5+ MTDS lending writers first and prove them green · (2) then migrate the ~16.7M rows · (3) then
> re-sync the shard atom across GCS/manifest/status/UI.** Until step 2 completes, market/event flat `LENDING` is
> `migration_pending` — the skill must **not** report it as a fresh non-canonical finding, and must **not** treat it as
> an unruled/refused axis either. Codex §5's "LENDING is RETIRED" text is now the correct **target**, but needs a banner
> stating it is not yet implemented and naming the writer-fix prerequisite.
>
> **D3 consequences (fold → repoint → delete):** the order is **mandatory**, not advisory — KAMINO and SOLEND have
> **zero** canonical `dex_pool_state` objects, so for those cells the legacy objects are the **only** copy and a
> delete-first would be unrecoverable. Track 2 and §A6 have already been amended to match (P0-01, shipped).

<details>
<summary>Original option-sets as presented (retained for the record)</summary>

These three could not be adjudicated from documents — in two of them, both sides cited the **same operator on the same
date** in opposite directions. The skill was built to refuse these axes, so the build was never blocked; the estate's
convergence was. Each was stated as an option-set with a recommendation.

### D1 — manifest `instrument_type` COLUMN case (audit ref C2a) · direction of >12M row rewrites

_Settled and NOT in question_: the **path** segment is lowercase; the **id** middle segment is UPPER. Only the manifest
**column** is disputed.

| Option                             | What it means                                                                                                                                                      | Cost                                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| **A — LOWERCASE (codex wins)** ⭐  | Fold the column to lowercase; matches `cross-asset-canonical-target-ssot.md` §7/§11 and the defi closeout. **Revert** the two shipped uppercase migration scripts. | Rewrite the cefi 7.58M + tradfi 750,715 rows already uppercased; 2 script reverts. |
| **B — UPPERCASE (catalogue wins)** | Column matches the catalogue enum; ratifies what cefi + tradfi **already shipped**. Correct codex §7/§11 instead.                                                  | Migrate defi's ~16.7M rows UP; correct 2 codex sections + the defi closeout.       |
| **C — case-insensitive contract**  | Declare the column case-**insensitive**, normalise on read, stop migrating either way.                                                                             | Cheapest now; every consumer must normalise, forever.                              |

**Recommendation: B.** Not because it is more correct in principle, but because it is the only option where the shipped
code and the migrated rows already agree — A requires un-shipping two migrations that have already rewritten >8M rows,
and C pushes an unbounded normalisation obligation onto every future reader. If you prefer A on principle, say so and
the revert is mechanical; it is the cost, not the correctness, that drives this recommendation.

**Frozen pending ruling**: the two DRAIN-GATED `--apply` runs (`instruments-service@555ddf1c` + the tradfi Phase-B
script). Do not let either run before this is decided — they move rows in the disputed direction.

### D2 — DeFi market/event `LENDING` keying (audit ref decision D)

Codex §5 says flat `LENDING` is RETIRED (A_TOKEN/DEBT_TOKEN split, ~16.7M rows). The retire was **reversed in code**
because it broke 5+ MTDS lending writers into `attempted_failed`/zero-data and desynced the shard atom (GCS
`instrument_type=a_token` vs manifest `lending`).

| Option                              | What it means                                                                                                                                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — ratify the interim** ⭐       | `holdings` uses A_TOKEN/DEBT_TOKEN; market/event data_types (`lending_indices`, `liquidation_events`, `flash_loan_events`, `position_data`) keep uniform `LENDING`. Correct codex §5 to match. |
| **B — complete the full retire**    | Re-execute the split across all lending data_types; requires fixing the 5+ writers first, then re-syncing the atom.                                                                            |
| **C — split by data_type formally** | Make the holdings-vs-market/event distinction an explicit documented rule rather than an interim.                                                                                              |

**Recommendation: A** (with C as the tidy-up). The reversal was driven by measured writer breakage, not by preference —
codex currently asserts a state the code deliberately does not implement, and that gap is what re-invites a repeat of
the reversed retire. A correction banner has already been added to §5 so no agent re-executes it meanwhile.

### D3 — DeFi `dex_pools/` + `lending_indices/` disposition (B1)

| Option                                  | What it means                                                                                                                                                 |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A — fold, repoint, then delete** ⭐   | (1) content-UNION the 32 legacy-only pools into canonical; (2) repoint `execution-service` + fix its broken `resolve_bucket_name` call; (3) only then delete. |
| **B — retain indefinitely**             | Leave the legacy prefixes in place; cheapest, but the non-canonical relic persists and keeps re-surfacing in audits.                                          |
| **C — delete now (the ORIGINAL order)** | ❌ **Destroys data.** KAMINO/SOLEND `dex_pool_state` have no canonical copy at all. Listed only for completeness.                                             |

**Recommendation: A.** Track 2 and §A6 have already been amended in place to A, with the original text preserved and
struck through, so the stale instruction can no longer be executed by a worker reading it cold.

> **Sub-question that changes urgency, not the verdict** (recorded by the P0-01 agent, unresolved): the
> `resolve_bucket_name` call in `solana_amm_depth_provider.py:248` sits **outside** the `try:` at `:262`, so it raises
> uncaught through `load_date()`. That provider may therefore have been **dead-on-arrival** since that call regressed,
> rather than being an active consumer. Worth confirming — it determines whether the repoint is urgent or merely
> correct.

</details>

---

## Design — what the skill actually does

**Shard atom** =
`pipeline_mode({mode}_{source}) · date · asset_group · venue · [chain] · instrument_type · data_type · (KEY) · [quote · margin] · source`,
where `(KEY)` varies by the four grain patterns: `instrument_id` (flat-per-contract) · `underlying`
(bundle-per-underlying) · `canonical_question_group` (prediction, **manifest-only**). The skill compares surfaces **at
the atom grain** and never invents its own key.

**Four surfaces reconciled per shard**: (1) GCS object path + filename · (2) parquet content columns (`instrument_id`,
plus `canonical_instrument_id` for defi) · (3) manifest `_index` shard-atom key · (4) catalogue / data-status render.

**Canonical/non-canonical is decided by the machine oracle**, UAC `canonical_path_violations()` — the inverse of the
path builders — never by a rule re-implemented in the skill. Caveat: its `require_pipeline_mode` defaults **False**, so
the machine gate is currently _weaker_ than the codex declaration; the skill keys it off a per-AG cutover date (P1-07).

**Hard constraints** (each is a measured foot-gun, not a style preference):

- **Single-walk discipline** — no new whole-corpus GCS walk (review-blocking). Default mode is **manifest-driven**;
  where listing is unavoidable use only the three sanctioned no-walk routes (prefix-scoped per `(date, venue[, chain])`
  derived from manifest rows · delimiter-based child-prefix listing · reuse of `migration_orphan_sweep.py`'s existing
  single walk).
- **Read-only by construction** — every underlying tool invoked `--dry-run`/scan-only. No `--apply`, no manifest
  write-back, no GCS mutation, no VM launch. Never mutate process env to reach a tier — pass `deployment_env=`.
- **Per-AG code path, never a generic loop** — sports has **no `asset_group=` key at all** (`sports_reference/…` tree);
  prediction is a manifest-only CQG bundle grain the phantom reconciler must not be run against; defi alone has `chain=`
  (after `venue=`) and the two-id model; tradfi alone carries the write-time raising guard and the `batch_massive`
  read-recognition carve-out; cefi alone has the v5/v6 dual chain-tail hazard. A generic pass produces **destructive
  false positives on at least three of the five**.
- **Known-exception suppression is required** — re-reporting an operator-accepted exception as a fresh finding destroys
  the report's signal. Minimum list in P0-04.
- **Never synthesize scope** — like `--day` in the sibling skills, `asset_group` comes from the operator. Cells are
  enumerated from the UAC MVP predicate `is_mvp()` and `canonical_path_templates(ag)`, never a hardcoded
  venue/prefix/data_type list (that hardcoding is exactly the Axis-10 drift bug that made `--apply` false-flag real
  captured rows as phantom).
- **Report a number only with its formula named**; state that all 5 AGs gate Layer-2 so every `coverage_pct` is a
  **lower bound**; never quote a defi coverage % from the 1.38M denominator (the real one is 63.9M).

---

## Todos

### Phase A — close the documented-understanding gap (SSOT before skill)

- [x] 1. ✅ [DATA] P0. **NOTIFY OPERATOR + file issue doc**
      `plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md` capturing B1: R5 overturned the duplicate
      verdict, canonical twin is a PARTIAL OVERLAP (KAMINO/SOLEND genuinely unique — see the 2026-07-20 correction
      above; the original "VERIFIED ABSENT" claim was wrong and is superseded), execution-service still references the
      legacy shape. **Amend `defi_consolidated_closeout_2026_07_18.md` Track 2 and
      `canonical_closeout_open_questions_2026_07_18.md` §A6 in place** to FOLD-not-delete with the required order: (1)
      content-UNION the 32 legacy-only pools into canonical, (2) repoint
      `execution-service/providers/solana_amm_depth_provider.py` to `data_type=dex_pool_state` (and fix its broken
      `resolve_bucket_name` call — `market-data-tick-defi` is a name fragment, not a yaml key, and `env=`/`project_id=`
      are not parameters, so it **raises**), (3) only then consider delete. — `unified-trading-pm` (this batch) +
      evidence: issue doc filed; `defi_consolidated_closeout` Track 2 and `canonical_closeout_open_questions` §A6 both
      carry a dated `⛔ corrected 2026-07-20` banner with the original text preserved via strikethrough. Re-probe
      measured ORCA 14,094 · RAYDIUM 100 canonical objects on `day=2026-04-14` under `instrument_type=solana_amm_pool`;
      KAMINO/SOLEND `dex_pool_state` = 0.
- [x] 2. ✅ [DATA] P0. **Escalate B2/B3/B4 to the operator as structured option-sets** (A/B/C + Other per the escalation
      rule). Until ruled: the skill MUST NOT report `instrument_type` column casing as a finding, MUST NOT propose any
      casing migration, and MUST NOT flag `lending` on market/event data_types as non-canonical. Freeze the two
      DRAIN-GATED `--apply` runs (`instruments-service@555ddf1c` + the tradfi Phase-B script).
- [x] 3. ✅ [DATA] P0. **NEW SSOT** `/codex/02-data/four-surface-reconciliation-procedure.md` — the executable
      comparison of the four surfaces for one shard, and how to classify each disagreement. This is the skill's core
      loop; it exists today only as fragments across ~8 docs.
- [x] 4. ✅ [DATA] P0. **NEW SSOT** `/codex/02-data/reconciliation-finding-taxonomy.md` — the closed, named set of
      finding types (phantom · orphan · true_gap · missing_row · divergent_empty · masked-stale ·
      drift-axis-false-positive), each with detection method + safe remediation, **plus the operator-accepted exception
      list** (the 19,274 pre-2026-07-08 sports rows with blank pipeline_mode+source [BLK-d48acae4] · tradfi `combo`
      bare-underlying · defi two-id POOL divergence [Option A, intentional] · `batch_massive` read-recognition until
      purge · defi interim flat `LENDING` for market/event data_types). Without a closed set, consecutive runs are not
      diffable.
- [x] 5. ✅ [DATA] P0. **NEW SSOT** `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — the **five-part
      proof** required before any delete suggestion rises above `unknown`: (1) twin resolves via `gcs_describe_object`,
      not by path construction; (2) **CONTENT verify, not existence** (R5 precedent); (3) grep-then-READ proof nothing
      still WRITES it; (4) grep-then-READ proof nothing still READS it; (5) the **legacy-COPIED-not-MOVED** invariant —
      a cell backed only by a legacy copy passes reconcile but reads MISSING under canonical-only status. Any failure →
      `no-migrate-first`. Absorbs the GCS DELETE SAFETY INVARIANT currently stranded in
      `pipeline-mode-partition.md:66-77`.
- [x] 6. ✅ [DATA] P0. **NEW SSOT** `/codex/02-data/non-canonical-path-inventory.md` — the living register seeded with
      the audit's **29 entries** (location · why · canonical twin · still-written-by · delete disposition), grouped by
      the five dispositions. This IS the input to the delete-suggestion feature; re-deriving it per run costs a walk,
      and keeping it in plans loses it at archival.
- [x] 7. ✅ [DATA] P1. **NEW SSOT** `/codex/02-data/canonical-cutover-register.md` — per-AG effective-from dates for
      `require_pipeline_mode`, instrument_type case, tradfi chain tail, defi leaf filename, sports data_type case.
      Without it the skill cannot separate "legitimately historical" from "non-canonical" and will either flood false
      positives on pre-cutover data or silently pass post-cutover regressions.
- [x] 8. ✅ [DATA] P1. **NEW SSOT** `/codex/02-data/orphan-object-detection.md` — the inverse case no current tool
      covers: a parquet on GCS with **no manifest row AND outside the oracle's expected set** is invisible to every
      existing tool (all are manifest-row- or oracle-driven). The delete-suggestion feature is precisely orphan
      detection.
- [x] 9. ✅ [DATA] P1. **Correct the stale/contradictory codex** (each with a dated correction annotation, not a silent
      edit): `cross-asset-canonical-target-ssot.md` §8 defi leaf filename → `{canonical_instrument_id}.parquet` (a stale
      template inside the designated tie-breaker doc is the corpus's most dangerous defect) · §8 tradfi chain tail →
      `underlying=/quote=/margin=` (shipped code wins) · §5 LENDING interim banner (B3) ·
      `per-asset-group-bucket-layouts.md:137` third filename form · SUPERSEDED banners on the two v1 honest-coverage
      formulas (`availability-manifest-and-data-status.md:117,:947,:1834-1844` + `manifest-consolidator-ssot.md:296`) ·
      regenerate the manifest schema block from UTL `manifest_writer/_rows.py` (doc omits 5 live columns, duplicates
      `source`) · SUPERSEDED-banner `data-catalogue-schema.md` (documents an artifact, writer, reader, updater and
      validating plan that **do not exist**) and replace with `service-shard-status-catalogue.md` describing the
      `shard_status[AG][VENUE].start_date` shape deployment-api actually consumes.
- [x] 10. ✅ [CODE] P1. **NEW SSOT** `/codex/06-coding-standards/canonical-write-guard-contract.md` — which lanes call
      `canonical_path_violations`, with which `require_pipeline_mode`, and which are deliberately unguarded (today
      tradfi-W1 + cefi-live + microstructure guarded; cefi-batch, prediction, sports unguarded with no stated intent).
      Absorbs the dangling pointer to the non-existent `canonical-write-conventions.md`. **Plus**: extend
      `/codex/05-infrastructure/bucket-isolation-model.md` with a **bucket-name resolution authority** section —
      `cloud-providers.yaml`/`resolve_bucket_name` WINS; UTL `PATH_REGISTRY`/`build_bucket` Group-A rows resolve to
      buckets that **now 404** and are reached at runtime by `domain_client/clients/market_data.py:56` (file as a P0
      latent defect; check whether UTL market-data domain-client reads are currently failing).
- [x] 11. ✅ [DATA] P1. **Reconcile the single-walk rule** — `availability-manifest-and-data-status.md` §9 ("walks are
      review-blocking") and `gcs-object-operations.md` (six-point contract _for_ walks) never cross-reference and read
      as contradictory. State the reconciled rule in both: **ONE walk per corpus per campaign, all passes bundled onto
      that snapshot**, and fix §9's factually wrong exemption rationale (it claims a script "reads the index, not the
      corpus" — false of the very script it names).

### Phase B — author the skill

- [x] 12. ✅ [SCRIPT] P0. Author `cursor-configs/skills/data-pipeline-reconciliation/SKILL.md` matching the two sibling
      skills **exactly**: frontmatter is exactly `name` + `description` (one prose blob naming the phases, the hard
      constraints, /autonomous composition, and an explicit `Trigger on …` clause); body follows the numbered skeleton
      (H1 · purpose · bolded **Shard atom** line · `## 0.` required-input gate · `## 1.` composing with /autonomous ·
      `## 2.` Phase 0 · `## 3.` Phase 1 with `### 3a/3b/3c` · `## 4.` Phase 2 · `## 5.` write+present report · `## 6.`
      under /autonomous loop · `## Extending to a new asset_group` · `## Not wired into quality-gates.sh`). Durable
      rules live in codex and are **referenced**, never restated. No re-linking step is needed — `.claude/skills` is a
      single directory symlink to `cursor-configs/skills/` since 2026-07-17, so a new skill dir surfaces fleet-wide on
      `git pull`.
- [x] 13. ✅ [SCRIPT] P0. **Report contract** — emit a markdown + sibling JSON pair at
      `plans/audit/results/data_pipeline_reconciliation_<AG>_<YYYY_MM_DD>.md` and **PRINT the full rendered markdown to
      stdout** (§5 of the sibling skills mandates relaying printed content directly, never "done, see the report").
      Include the auto-generated **Bucket paths** table naming which bucket each read targeted, a per-surface verdict
      per shard, and typed findings from the P0-04 taxonomy so consecutive runs diff cleanly.
- [x] 14. ✅ [SCRIPT] P1. **Per-AG reference sheets** in the skill dir — one per asset_group encoding only the
      _pointers_ and the per-AG hazards (sports' no-`asset_group=` tree + 4 layouts + non-obvious `entity=` names ·
      prediction's manifest-only CQG grain + "do not run the phantom reconciler" · defi's `chain=`-after-`venue=` +
      two-id model + capture-STOPPED state · tradfi's raising guard + `batch_massive` carve-out · cefi's v5/v6 dual
      chain-tail).
- [x] 15. ✅ [SCRIPT] P1. **Static audit of the backfill-smoke write paths** (audit only — never run them): confirm
      `/data-pipeline-check-is` and `/data-pipeline-check-mtds` write to `-test-` buckets ONLY and that their writers
      emit the canonical grammar. Record findings as todos here or an issue doc; do **not** fix writer defects in this
      plan.

### Phase C — validate per asset_group

- [x] 16. ✅ [DATA] P0. Run the skill for **defi** (the hardest: `chain=`, two-id model, capture STOPPED, the
      `dex_pools` relic, Shape-B duplicate tree). Verify it reproduces the audit's known findings and raises no new
      false positives.
- [x] 17. ✅ [DATA] P0. Run for **cefi** and **tradfi**; confirm the v5/v6 dual chain-tail and the `batch_massive`
      read-recognition carve-out are handled without flagging accepted exceptions.
- [x] 18. ✅ [DATA] P1. Run for **prediction** and **sports**; confirm the CQG manifest-only grain and the
      no-`asset_group=` sports tree produce zero structural false positives.
- [x] 19. ✅ [REVIEW] P1. **Post-phase codex audit** — verify every new/edited codex doc is internally consistent and
      that no plan↔codex drift remains; add the one-liner + conditional-domain pointer to `cursor-configs/CLAUDE.md`
      (honour the 40 KB cap — condense, never raise it).

### Phase D — apply the 2026-07-20 operator rulings (D1 / D2 / D3)

- [x] 20. ✅ [DATA] P0. **D1 UPPERCASE — correct the docs and unfreeze.** Flip `cross-asset-canonical-target-ssot.md`
      §7/§11 lowercase→UPPERCASE **for the manifest COLUMN only** (path segment stays lowercase, id middle segment stays
      UPPER — neither was in question), with a dated ruling annotation. Correct the tradfi closeout's self-contradicting
      worklist (it orders a case-fold in the opposite direction, 750,715 rows) to fold UP. Record that the DRAIN-GATED
      freeze on `instruments-service@555ddf1c` + the tradfi Phase-B script is **lifted** (they are now ratified).
- [x] 21. ✅ [SCRIPT] P0. **D1 — stop refusing the axis in the skill.** Remove the C2a refusal from `SKILL.md` § 3e and
      the taxonomy's REFUSED-axes section; replace with the enforced rule (column = UPPERCASE) plus a
      `migration_pending` exception entry for the defi rows not yet migrated UP. The case-insensitive comparison
      workaround comes out.
- [x] 22. ✅ [DATA] P0. **D2 — banner codex §5 with the prerequisite.** §5's "flat `LENDING` is RETIRED" is now the
      correct TARGET; add a dated banner stating it is **not yet implemented**, that the first attempt was reversed
      after breaking 5+ MTDS lending writers, and that the mandatory order is **fix-writers → migrate ~16.7M rows →
      re-sync the shard atom**. Reclassify market/event flat `LENDING` from `refused/unruled` to `migration_pending` in
      the taxonomy so the skill neither flags it nor treats it as an open question.
- [x] 23. ✅ [DATA] P1. **D2 — scope the writer fix (prerequisite for the migration).** Identify and enumerate the 5+
      MTDS lending writers that broke into `attempted_failed`/zero-data on the reversed attempt; file the fix as its own
      plan (this plan does not own MTDS writer work). **The migration must not start until that plan is green** — this
      is the step whose omission caused the reversal.
- [x] 24. ✅ [DATA] P1. **D3 — fold before anything else.** Content-UNION the 32 legacy-only Raydium pools into the
      canonical tree, and confirm the KAMINO/SOLEND `dex_pool_state` cells (canonical count **zero** — legacy is the
      only copy) are covered by the fold. Verify by count + content, not by path existence.
- [x] 25. ✅ [CODE] P1. **D3 — repoint execution-service, then re-verify.** Point
      `providers/solana_amm_depth_provider.py` at the canonical `data_type=dex_pool_state` path and fix its broken call
      to `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`. Resolve the open sub-question first
      (the call sits outside the `try:` so the provider may be dead-on-arrival). **Delete comes after this, never
      before** — and the prod-bucket delete itself stays human-only.

---

## Progress Log

### 2026-07-20 — Phase 0 audit complete (9 agents, 2.28M subagent tokens)

Nine-dimension read-only audit across canonical grammar · bucket estate · manifest · catalogues · recent plan corpus ·
existing tooling · backfill writers · live GCS estate, plus a high-effort reconciling synthesis. Output retained at
`/tmp/claude-1000/-home-ubuntu-unified-trading-system-repos/5697ef0c-2b5a-43bf-8008-6202d06ded45/scratchpad/synthesis_raw.json`
(scratchpad — **not durable**; the durable form is P0-06's inventory doc and P0-04's taxonomy).

Yield: **33 contradictions** (4 blocking, 11 high) · **29 non-canonical locations** · **12 codex gaps** · **21 reusable
tools** · **16 hard design constraints**.

Headline: the estate's _documented understanding_ is the blocker, not the estate itself. Four contradictions cannot be
adjudicated from documents (two cite the same operator on the same date in opposite directions). The single most
dangerous finding is **B1** — two live plan docs order a delete that a later content-verify in the _same plan_
overturned, against data with **no canonical twin** that a live service **still reads**.

Second-order finding worth its own escalation: UTL `PATH_REGISTRY` Group-A rows resolve to **15 buckets that are now 404
on live probe**, and are reached at runtime by `domain_client/clients/market_data.py:56` — a live resolver pointing at
deleted buckets (P1-10).

Method notes for a compressed future-self: the audit ran as a resumable `Workflow`; 2 of 8 dimensions failed on API
rate-limiting on the first pass and were recovered via `resumeFromRunId` (cached dimensions replayed, only the 2
failures + synthesis re-ran). GCS access: object listing works; project-wide `storage.buckets.list` is **denied** for
`unified-trading-sa`, so bucket names must come from the code registry, never from enumeration.

### 2026-07-20 — operator rulings + in-flight workflow handles

**Rulings landed** (`unified-trading-pm@b8e0a0724`): D1 = UPPERCASE column · D2 = complete the full LENDING retire
(against the worker recommendation, with the fix-writers-first prerequisite recorded) · D3 = fold → repoint → delete.
Phase D (todos 20-25) added to apply them.

**Resumable workflow handles** — a prior session exited mid-flight and killed two background workflows; their run IDs
are recorded here so a restarted session resumes instead of re-running. Resume with
`Workflow({scriptPath, resumeFromRunId})`; completed agents replay from cache.

| Run ID            | Script (scratchpad) | Covers                                                                                         |
| ----------------- | ------------------- | ---------------------------------------------------------------------------------------------- |
| `wf_69948fdb-535` | `dpr-phase-a.js`    | Phase A — last outstanding agent is P1-10 (write-guard contract + bucket-resolution authority) |
| `wf_10a81bb8-42e` | `dpr-phase-c.js`    | Phase C — 5 per-AG reconciliation runs + the skill acceptance review                           |
| `wf_5023c524-684` | `dpr-phase-d.js`    | Phase D — todos 20 / 22 / 23 (D1 corrections, D2 banner, MTDS writer-fix scoping)              |

Scratchpad root:
`/tmp/claude-1000/-home-ubuntu-unified-trading-system-repos/5697ef0c-2b5a-43bf-8008-6202d06ded45/scratchpad/`.
**Scratchpad is not durable** — if the scripts are gone, the plan's todo text is sufficient to re-author them.

**Ordering constraint discovered:** todo 21 (remove the C2a refusal from `SKILL.md` + the taxonomy) must run **after**
Phase C's acceptance review, because that review also edits `SKILL.md`. Editing it while five agents are mid-read makes
their critiques reference a moving target.

### 2026-07-20 (cont.) — Phase A/B/D shipped; C + consistency in flight

**Shipped since the last log entry:**

- `b1be58824` — todo 10 (P1-10: `canonical-write-guard-contract.md` + bucket-isolation "resolution authority" section),
  todos 20/22/23 (D1 corrections, D2 §5 banner, `defi_lending_writer_retire_prerequisite_2026_07_20.md`). Two hygiene
  gates caught real defects before landing: an unquoted `: ` in the new plan's `summary:` folded scalar broke YAML, and
  `nature: refactor` was invalid (the sub-agent conflated `nature` with `estimate_class`; corrected to `process`).
- `ea5636e9d` — cleared residual D2 `PARKED/UNRULED` staleness at cross-asset SSOT §5 (`<details>` block) and §11 log
  line, both flagged by the todo-23 agent.

**Finding worth keeping: the "5+ MTDS lending writers" figure is an UNDERCOUNT** — the real count is **8** (7 emit flat
`LENDING`, 1 emits `SOLANA_LENDING`). The failure mode is **silent**: `build_instrument_id` raises, each handler's broad
`except ValueError` → `record_failed`, so the manifest fills with `attempted_failed`/zero-data rows that render as an
honest failure, not a crash. Also independent of the retire: `liquidations_handler` is **already** shard-atom-desynced
in prod (manifest `liquidation` vs GCS path `LENDING`). Both captured in the new prerequisite plan.

**In flight (self-tracked workflows; run IDs recorded for restart-safety):**

| Run ID            | Script               | Covers                                                                            |
| ----------------- | -------------------- | --------------------------------------------------------------------------------- |
| `wf_10a81bb8-42e` | `dpr-phase-c.js`     | Phase C — 5 per-AG reconciliation runs + skill acceptance review (todos 16/17/18) |
| `wf_dd6c0ce3-40b` | `dpr-consistency.js` | Post-phase codex audit (todo 19) — ruling-drift + cross-SSOT + skill-ref checks   |

**Remaining after those land:** todo 21 (remove the now-obsolete C2a refusal from `SKILL.md` §3e + the taxonomy REFUSED
section — D1 ruled it, so the skill enforces UPPERCASE instead of refusing) — sequenced AFTER Phase C's acceptance
review because both edit `SKILL.md`. Todos 24/25 (D3 fold → repoint execution-service) are genuine defi-migration
execution work with prod blast radius; they remain tracked todos here, to be executed as their own effort (the prod
delete in 25 is human-only regardless).

### 2026-07-20 (cont.) — consistency audit done; operator asked for 4 coverage additions (Phase E)

**Todo 19 consistency audit (`wf_dd6c0ce3-40b`) — done, fixes shipped `5da51f358`.** The tie-breaker doc was correctly
ruling-annotated but the rulings had NOT propagated to 6 sibling docs (cutover-register, four-surface-procedure,
delete-safety-protocol, mvp-scope-canonical, defi-canonical-naming, and two plans), each still framing D1/D2 as
UNRULED/PARKED — the exact pre-ruling staleness a future agent would act on. All fixed with dated banners. **One
substantive contradiction refused-and-reported → filed as an issue** (`c3e7eb55f`,
`plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`, resolved,
archived): the v2 coverage harness reads `instrument_type` **lowercase**; the D1 UPPERCASE migration will silently
zero-match every migrated shard unless the harness is made case-robust FIRST. Same fail-closed class as the sports MDPS
substring matcher.

**Still open for todo 21** (the audit confirmed): the taxonomy must drop BOTH refusals — §5.1 (D1/C2a) AND §5.2 + AE-5
(D2/decision-D). Todo 22's checkbox slightly overstated completion (it claimed the taxonomy reclassification, which was
actually deferred into todo 21's edit). Todo 21 now owns removing both.

**Operator request 2026-07-20 — 4 coverage additions the skill does NOT yet cover → Phase E (`wf_330857a4-e54`):**

1. **Distinct-value census** of instrument_type/data_type/venue/chain, in the **manifest AND GCS path segments**,
   flagged against the canonical enum — plus the manifest-vs-GCS distinct-set diff (catches the shard-atom vocabulary
   desync, and the `solana_amm_pool`-vs-`pool` class, cheaply). Largely REUSE: deployment-api already has
   `_axis_census.py` + `_distinct_values.py` over `read_availability_index(columns=…)`.
2. **Per-datapoint id-canonical** validation (every row's id against the `VENUE:TYPE:SYMBOL` grammar, not just the
   sampled stem==column check).
3. **Per-datapoint schema** validation (columns / dtypes / UTC / non-NaN) — currently DEFERRED by the four-surface doc.
4. **Two-tier compute model** — Tier-1 in-session (census + oracle, cheap); Tier-2 on a **SPOT VM** doing the ONE
   sanctioned single-walk + the heavy per-datapoint checks (2+3), writing a results manifest the skill reads. Keeps
   aggressive compute off the agent session and honours single-walk.

Phase E authors a new codex SSOT (`reconciliation-census-and-compute-tiers.md`) + returns SKILL.md/taxonomy/reference
integration text (not applied — SKILL.md is owned by the in-flight Phase C). Phase-E plan todos land as 26+.

### Phase E — census + per-datapoint validation + two-tier compute (operator G1–G4 ask, 2026-07-20)

- [x] 26. ✅ [DATA] P1. **Codex SSOT for census + per-datapoint + compute tiers** —
      `/codex/02-data/reconciliation-census-and-compute-tiers.md` landed. Provenance: G1–G4 operator ask.
- [x] 27. ✅ [SCRIPT] P1. **Wire § 3f distinct-value census into the skill.** Manifest via `get_axis_value_census`, GCS
      via delimiter descent, three comparisons, suppression — reusing `_axis_census.py` +
      `_distinct_values._comparison_set`; no endpoint change. Codex SSOT § 1.
- [x] 28. ✅ [DATA] P0. **Taxonomy delta — add the three new finding-types** (`non_canonical_axis_value`,
      `shard_atom_vocab_desync`, `non_canonical_id`) to `reconciliation-finding-taxonomy.md`; update the count line +
      delete-eligibility table. Do this in the SAME taxonomy pass as todo 21 (the C2a + decision-D refusal removals).
      Blocks 27/30.
- [x] 29. ✅ [DATA] P1. **Extend four-surface procedure § 5 with route-#3 usage + Tier-2 note** — the Tier-2 VM IS the
      sanctioned single walk for S2 content; skill read-back is a manifest-index read (exempt); G2/G3 bundle onto the
      one walk. Codex SSOT § 3.
- [x] 30. ✅ [SCRIPT] P1. **Wire § 3g + § 7 compute tiers into the skill** (id/schema legs; Tier-1 ≤500-sample smoke;
      Tier-2 read from the `datapoint-validation` results index). Depends on 28.
- [x] 31. ✅ [INFRA] P1. **Register the `datapoint-validation-{ag}-` VmPrefixSpec + results-bucket kind BEFORE any
      launch** (real `VmPrefixSpec` EPHEMERAL_BATCH entries in `vm_prefix_registry.py`, the `datapoint-validation`
      `resolve_bucket_name` kind in `configs/cloud-providers.yaml`; ship via quickmerge). Unregistered = invisible.
- [x] 32. ✅ [SCRIPT] P1. **Author `launch-datapoint-validation-vm.sh` + `validate_datapoint_schema_id.py`** — modeled
      on `launch-manifest-recon-all-vm.sh`; SPOT + PROGRESS.json resume; reuses `validate_dataframe` +
      `build_canonical_instrument_id`; writes the results manifest. Depends on 31. Lifecycle marker required.
- [x] 33. ✅ [DATA] P2. **Per-AG reference-sheet census nuance line** (defi chain axis + case-insensitive; cefi EXACT +
      dual chain-tail; tradfi batch_massive suppress; prediction conditionId; sports entity-keyed).

### Phase F — MDPS candle layer (`--layer candles`) — operator ruled Option A 2026-07-21

> **Provenance**: operator RULED **Option A** 2026-07-21 ("migrate data gcs paths and manifest") — the declared registry
> template wins → an 8-phase migration, ~10–20M objects, sequenced **defi → prediction → cefi → tradfi**. NOTHING is
> migrated on disk yet, so the WHOLE candle corpus is `migration_pending` and the candle audit reconciles against the
> Option-A TARGET, never the current disk shape. Candles are co-located in the SAME `market-data-tick-{ag}` buckets
> under `processed_candles/` (sports: `processed/`); Phase-0 bucket resolution is unchanged. **Codex SSOT for this
> phase**: `/codex/02-data/mdps-candle-canonical-reconciliation.md`. Migration source-of-truth issue:
> `plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`.

- [x] 34. ✅ [DATA] P1. **NEW codex SSOT** `/codex/02-data/mdps-candle-canonical-reconciliation.md` — the candle-LAYER
      extension of the four-surface procedure: the candle shard atom (adds `timeframe`; `data_type` keyed on the
      AGGREGATED `mdps_data_type_key`; S3 rows filtered `service_name=="market-data-processing-service"`), the four
      surfaces for candles (S4 UNAVAILABLE by construction — no candle catalogue), and the candle canonical authority
      (Option-A registry template, oracle-EXEMPT namespace). — `unified-trading-pm` (sibling agent landed it this
      batch).
- [x] 35. ✅ [SCRIPT] P1. **NEW reference sheet** `cursor-configs/skills/data-pipeline-reconciliation/reference-mdps.md`
      — layer-expansion pointers + candle hazards (H1 sports `processed/` tree · H2 oracle-exempt · H3 object↔manifest
      disconnect · H4 split-brain `pipeline_mode` · H5 genuine defects). — `unified-trading-pm` (sibling agent landed it
      this batch).
- [x] 36. ✅ [SCRIPT] P1. **Wire the `--layer {raw-tick,candles}` flag + §3h into `SKILL.md`** (default `raw-tick`,
      orthogonal to `--asset-group`): add the `## Layers` note + the §0 flag line, the
      `### 3h. MDPS candle-layer     reconciliation` subsection (candle shard atom, GCS-object-driven inversion,
      oracle-exempt Option-A template, S4-UNAVAILABLE, migration_pending suppression, genuine defects), the SSOT-table
      row, the `(asset_group × layer)` §6 loop, and the "Extending to a new LAYER" note. — `unified-trading-pm` (this
      batch).
- [x] 37. ✅ [DATA] P1. **Add the candle-layer variant note to
      `/codex/02-data/four-surface-reconciliation-procedure.md`** (dated 2026-07-21, pointer + 4 key deltas: `timeframe`
      atom, oracle-exempt, S4-unavailable, object-driven; migration_pending). Pointer only — no duplication. —
      `unified-trading-pm` (this batch).
- [x] 38. ✅ [DATA] P0. AE-6 added to `reconciliation-finding-taxonomy.md` §4 (matches the corrected LOCKED shape —
      `instrument_type=`/`pipeline_mode=` suppressed on the path, `data_type` stays SOURCE); per-AG PENDING candle rows
      added to `canonical-cutover-register.md` §6d (defi → prediction → cefi → tradfi, cefi explicitly noted BLOCKED on
      the running raw-tick fleet) — `unified-trading-pm` (this batch). Cutover-register concurrency concern resolved (no
      other agent was actively editing it).
- [x] 39. ✅ [CODE] P1. UAC oracle extended: `PROCESSED_CANDLES_PREFIX` + `_candle_path_violations()` +
      `require_candle_migration_complete=` kwarg on `canonical_path_violations`/`is_canonical` — validates the LOCKED
      shape (source `data_type`, added `instrument_type=`/`pipeline_mode=`), suppresses the two migration-pending axes
      by default, never suppresses genuine defects (empty stem, malformed values, missing day/timeframe/data_type). 16
      recovered spec tests + 85 pre-existing raw-tick tests pass; full QG green — `unified-api-contracts@6329fc04`.
      Skill §3h re-pointed at the oracle (see below).
- [x] 40. ✅ [DATA] P0. **Fix the candle object↔manifest disconnect (candle-manifest population)** — filed as its own
      MDPS-owned plan, `plans/active/mdps_candle_manifest_population_disconnect_2026_07_25.md` (at filing time:
      `status: draft`, `assigned_vm: NA` per the ask-before-creating default; the doc itself recommends the operator
      consider AO-dispatch for its todo-1 diagnostic, without deciding it). Scoping found the original framing stale: a
      `record_captured` call now EXISTS in the writer (`market-data-processing-service@752eaff` + same-day `@2d720b4`,
      2026-07-21) and was proven working against `-test-`, yet a fresh 2026-07-25 re-measurement shows the PROD manifest
      is still unchanged (defi 0 / cefi 6 / tradfi 73 / prediction 168 rows, byte-identical to 2026-07-20/2026-07-23) —
      **and, newly measured this pass, zero rows on any of the 4 asset_groups carry a `written_at` after the fix's
      2026-07-21 17:01 UTC+1 landing time.** The new plan scopes root-causing this (3 undistinguished hypotheses) ahead
      of the fix + historical backfill — `unified-trading-pm` (this batch). **Pointer confirmed accurate post-completion
      (2026-07-27, slot-8)**: the operator later did flip the doc to `assigned_vm: planning` / `status: active`
      (AO-dispatched); root cause was named (the `ohlcv_1m` emission-policy gate's self-referential completeness check),
      the writer fix shipped (`mdps@caa995c`), the historical corpus backfilled (86,252 manifest cells across all 4
      asset_groups), and a 3-surface spot check confirmed no disagreement — the disconnect this todo's pointer targets
      is now closed end-to-end; the path itself needed no correction.
- [x] 41. ✅ [DATA] P1. **Ran the MDPS candle audit per-AG against the Option-A target** —
      `/data-pipeline-reconciliation --asset-group <ag> --layer candles`, sequenced defi → prediction → cefi → tradfi. 4
      reports (+ JSON siblings) at
      `plans/audit/results/data_pipeline_reconciliation_candles_{defi,prediction,cefi,     tradfi}_2026_07_25.md` (the
      pre-existing same-named 2026-07-23 docs were NOT this skill — they were the candle-path migration's own P8
      verification via the migration script's dry-run classifier; this is the first real run of the reconciliation skill
      itself against the candle layer, re-pointed at the UAC oracle per todo 39). Confirmed (a) driven off GCS objects +
      a fresh manifest re-read, not the stale prior numbers; (b) 0 `migration_pending` suppressions needed — every
      sampled object (5 per AG) already carries the fully-migrated LOCKED shape, zero oracle violations under both
      `require_candle_migration_complete=False` and `=True`, independently reconfirming the Option-A migration's P7/P8
      "CLEAN" verdict via a different tool; (c) S4-UNAVAILABLE reported once per AG; (d) surfaced only already-tracked
      genuine defects (tradfi's ~7.1M-object quarantine residual, cefi's 149-object residual) plus the **headline
      `missing_row` finding, now confirmed campaign-wide**: 0 candle manifest rows written since the 2026-07-21 fix, on
      all 4 asset_groups. Read-only throughout; 0 delete suggestions. Depended on 38 (done). — `unified-trading-pm`
      (this batch).
- [x] 42. ✅ [DATA] P2. `timeframe` added to `AXIS_CENSUS_COLUMNS`, `service_name=="market-data-processing-service"`
      filter added, `data_type` badged against SOURCE `DATA_TYPES_BY_ASSET_GROUP` (not the aggregated
      `mdps_data_type_key` — corrected per the 2026-07-21-evening ruling) — `deployment-api@5564c52c`. The census does
      not actually depend on todo 39's oracle (it is an independent vocabulary check, not built atop
      `canonical_path_violations()`), so it did not block on 39 being unshipped.

### Phase G — close 3 coverage gaps found auditing the skill against its own criteria (operator request 2026-07-30)

> **Provenance**: operator asked whether the skill's existing combination actually verifies, across ALL 5 AGs and ALL
> buckets, that every GCS object carries a UAC-recognized + manifest-recognized venue/instrument_id/pipeline_mode/
> instrument_type/bundle-key, in human-readable (not raw-wire) form. A read-only research pass against the shipped
> skill + `canonical_path_violations()` + `_axis_census.py` + the census codex doc found: (1) path STRUCTURE is covered
> for all 5 AGs (the oracle, Phase C todos 16-18); (2) the venue/instrument_type/data_type vocabulary CENSUS (G1, §3f)
> is mechanism-complete for all 5 AGs but had only ever been MEASURED for defi (H6 in `reference-defi.md`) —
> cefi/tradfi/sports/prediction were never run; (3) the id-FORM leg (human-readable vs raw-wire symbol) is correctly
> `{cefi, defi}`-only by design (sports/prediction route through domain-specific fixture-id/condition-id builders, not
> the `VENUE:ITYPE:SYMBOL` grammar — confirmed by reading `_partition_path_canonicality.py`'s own doc comments, NOT a
> gap to widen), but the taxonomy/skill docs never said so explicitly for sports (only prediction was named), so a
> report silently prints `0` for both, indistinguishable from "checked, clean" — the same false-clean shape
> `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` exists to prevent, one level up; (4) "bundle" (the
> underlying-keyed / CQG-keyed multi-instrument grain) had no positive machine-checkable finding type, only prose hazard
> warnings (`reference-prediction.md` H1). **Scope note**: this phase closes the 3 doc/taxonomy gaps + runs the census
> (G1) for the 4 unmeasured AGs — it does NOT re-run the full four-surface `/data-pipeline-reconciliation` skill
> end-to-end for all 5 AGs again (that already happened, Phase C todos 16-18, 2026-07-20); a fresh full re-audit is a
> separate, much larger undertaking and is not what this phase's finding required.

- [x] 43. ✅ [DATA] P1. **Document sports as an explicit ID_FORM N/A-by-design carve-out (not silence)** — widened
      `reconciliation-finding-taxonomy.md` § 2.7 `non_canonical_id`'s N/A carve-out list to name the sports fixture-id
      filename alongside prediction's CQG bundle (it was only ever named for prediction, leaving sports's identical
      status undocumented); same fix mirrored in `SKILL.md` § 3g. Both now instruct the report to print an explicit
      `id_form: not_applicable (structural)` line for sports/prediction rather than a bare 0-violations count. No code
      change — `_ID_FORM_CHECKED_ASSET_GROUPS = {cefi, defi}` in `_partition_path_canonicality.py` was already correctly
      scoped (verified by reading the function + its own doc comments); the gap was purely in report/doc disclosure.
      Gate: diff shows both docs' N/A carve-out lists now name sports explicitly.
- [x] 44. ✅ [DATA] P1. **Add `bundle_atom_key_mismatch` finding type** — new § 2.7 entry in
      `reconciliation-finding-taxonomy.md` giving the `reference-prediction.md` H1 hazard ("phantom reconciler mis-keys
      prediction, wipes CQG bundle rows") a positive, machine-checkable verdict of its own (previously prose-only);
      covers both the cefi/tradfi `underlying=`-keyed chain-bundle re-derivation case and the prediction CQG
      re-derivation case. Updated the closed-set count (twenty → twenty-one) and the delete-eligibility table (eighteen
      → nineteen non-eligible) in the same doc. Gate: `grep -c "^#### \`" reconciliation-finding-taxonomy.md` == 21 ·
      delete-eligibility table sums to 21.
- [x] 45. ✅ [DATA] P1. **Ran the distinct-value census (G1, § 3f) for cefi/tradfi/sports/prediction** — the four AGs
      whose census had never been measured (only defi's H6 existed). Called the real, unmodified
      `get_axis_value_census()` + `_distinct_values._canonical_set`/`_is_accepted_exception` in-process
      (deployment-api's venv fixed per todo 46). Measured: cefi 9,492,020 rows / tradfi 5,894,343 / sports 628,349 /
      prediction 1,661,267. Cross-checked every non-canonical finding against the existing corpus BEFORE writing
      anything up (pre-task conflict check): tradfi's 4 findings (`BARCHART`/`YAHOO_FINANCE`/`ESM0`/`UD`/`UNKNOWN`/
      `continuous_future`) and sports' 33-value `instrument_type` finding are BYTE-IDENTICAL to two already-open
      2026-07-28 issue docs (`tradfi_distinct_values_net_new_clusters`, `sports_instrument_type_market_token_ssot_gap`)
      — good independent re-confirmation, no new filing. Sports' `KALSHI` venue finding (20,785 rows) matches the
      archived `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` todo 15 exactly
      (`row_count=0` throughout, already tracked P2). Genuinely NEW small-scale residuals (cefi venue/instrument_type/
      chain-column drift, 6 un-registered sports bookmaker venues, prediction instrument_type/data_type case drift) —
      filed as `plans/archive/issues/cefi_sports_prediction_first_census_small_drift_2026_07_30.md` (P2, per
      `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md` — small-scale hygiene, not
      backfill-critical, matches the P2 precedent of the two sibling census docs). Full per-AG results recorded in
      `reference-cefi.md` H7-refinement + H8, `reference-tradfi.md` H7, `reference-sports.md` H11,
      `reference-     prediction.md` H6 — `unified-trading-pm@a2a84b66c` (docs) + this commit (results + new issue doc).
      AGs, not just a "mechanism exists" claim.
- [x] 46. ✅ [INFRA] P2. **Diagnosed + fixed a stale local venv, not a code bug** — `deployment_api.routes`/`.services`
      failed to import (pinned `fastapi==0.136.3`/`starlette==1.1.0` installed, lacking `iter_route_contexts` that
      unified-trading-library's `service_framework.fastapi_factory` imports at load time). Checked
      `plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md` first (pre-task conflict check) — this is
      the ALREADY-TRACKED, ALREADY-SHIPPED fleet-wide fastapi bump (`deployment-api@2c1d446`, `pyproject.toml`/`uv.lock`
      both correctly declare `fastapi>=0.137.0,<1.0.0`→resolves `0.140.7`); this checkout's `deployment-api/.venv`
      simply hadn't been `uv sync`'d since that fix landed. Ran `uv sync` in `deployment-api/` (picked up
      `fastapi 0.136.3→0.140.7`, `starlette 1.1.0→1.3.1`, `deployment-api`/`deployment-service`/
      `unified-trading-library` all to current HEAD) — `get_axis_value_census` now imports + is callable in-process. No
      new issue filed (would have duplicated the existing tracked doc). Local-venv-only change, nothing shipped.

> **Owner for the stale-venv / `iter_route_contexts` ImportError**:
> /plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md

---

## Deferred work after 2026-07-20

All 15 build todos + the audit/ruling/integration work (todos 1–23, 26–30, 33) are DONE and shipped. Four todos remain —
each is a genuine multi-repo EXECUTION/INFRA unit with prod blast radius, deliberately tracked (not half-built) with a
ready-to-execute spec. None blocks the skill: the skill is fully functional at Tier-1 (validated against prod for all 5
asset_groups, 2026-07-20).

| Todo   | What                                                                           | Why deferred (not blocked)                                                                                                                                     | Ready-to-execute?                                                                                                             |
| ------ | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **24** | D3 — content-UNION the 32 legacy-only Raydium pools into canonical             | A prod GCS write (fold). Order is mandatory (KAMINO/SOLEND have zero canonical copies). Human-gated per the delete-safety protocol.                            | Yes — spec + safe order in `issues/defi_dex_pools_delete_order_stale_2026_07_20.md`.                                          |
| **25** | D3 — repoint execution-service + fix its `resolve_bucket_name` call            | Cross-repo code (execution-service) via quickmerge; resolve the dead-provider sub-question first (the call raises outside the `try`).                          | Yes — the fix is `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")` + data_type=dex_pool_state.       |
| **31** | Register the `datapoint-validation-{ag}-` VmPrefixSpec + results-bucket kind   | Cross-repo config (deployment-service `vm_prefix_registry.py` + `cloud-providers.yaml`) via quickmerge; unregistered = invisible, so it lands BEFORE 32.       | Yes — spec in `/codex/02-data/reconciliation-census-and-compute-tiers.md` § 3.                                                |
| **32** | Author `launch-datapoint-validation-vm.sh` + `validate_datapoint_schema_id.py` | The Tier-2 VM runtime. Depends on 31. Reuses `launch-manifest-recon-all-vm.sh` + `validate_dataframe` + `build_canonical_instrument_id`; SPOT + PROGRESS.json. | Yes — this is the ONLY piece of the operator's "run on a VM" ask not yet built (the design + skill/doc integration ARE done). |

**The operator's literal G4 ask ("otherwise these checks should be added to skills and docs") is SATISFIED** — the VM
two-tier model is fully specified in SKILL.md § 7 and `/codex/02-data/reconciliation-census-and-compute-tiers.md`. Todos
31/32 build the runtime; they are the natural next unit of work.

## FINAL REPORT — /data-pipeline-reconciliation skill build (2026-07-20)

**Deliverable, shipped and validated.** A per-asset-group `/data-pipeline-reconciliation` skill that reconciles the four
canonical surfaces (GCS path · parquet content · manifest key · catalogue) over PROD buckets, read-only, emitting typed
findings + proof-gated delete SUGGESTIONS. Built via the operator's requested flow: **audit → plan → execute as
workflows**, on the `/autonomous` loop.

**What shipped (15 commits on `live-defi-rollout`, `4439cf429`…`f4a5700cc`):**

- **The skill** — `cursor-configs/skills/data-pipeline-reconciliation/SKILL.md` + 5 per-AG reference sheets. Surfaces
  fleet-wide via the single `.claude/skills` dir symlink (no linker run needed — that was the operator's opening
  question; the per-skill-link era ended 2026-07-17).
- **9 new codex SSOTs** — four-surface-reconciliation-procedure · reconciliation-finding-taxonomy ·
  gcs-and-manifest-delete-safety-protocol · non-canonical-path-inventory · canonical-cutover-register ·
  orphan-object-detection · service-shard-status-catalogue · canonical-write-guard-contract ·
  reconciliation-census-and-compute-tiers. Plus corrections to ~10 existing docs.
- **First real prod validation** — the skill ran read-only against PROD for all 5 asset_groups; each run critiqued it,
  driving a v2 pass. 5 reports at `plans/audit/results/`.
- **3 operator rulings** (D1 UPPERCASE · D2 full LENDING retire · D3 fold→repoint→delete) applied, propagated to every
  sibling doc, and the resulting **C2a contradiction closed corpus-wide** (a grep sweep confirms one `migration_pending`
  stance everywhere) — the acceptance review's single highest-value gap.
- **6 issue docs + 1 prerequisite plan** capturing real findings: the stale dex_pools delete order (would have destroyed
  data), the honest-coverage case-break latent on the D1 migration, the oracle's structure-only + value-blind gaps, the
  defi expected-universe `pool` vocab desync, the sports WEATHER layout drift, the cross-AG prediction→sports bleed, and
  the MTDS lending-writer fix that gates the D2 migration.

**The two premises the audit overturned** (both would have caused harm if trusted): (1) `dex_pools` is NOT a safe-delete
— the standing delete order in two live plans was stale, the canonical twin partial, and a live service still reads it.
(2) The estate's real blocker was not un-canonicalisation but **documented-understanding contradiction** — 33 of them, 4
blocking, two citing the same operator on the same date in opposite directions.

**Method notes** (for the next agent): adversarial verification caught two sub-agent errors that would have become SSOT
misinformation (a false "twin VERIFIED ABSENT" from probing `pool` not `solana_amm_pool`; a false
"`canonical_path_templates()` doesn't exist" from grepping one module). Both were re-checked against code before
shipping. The pre-commit hygiene gate caught three more (an unquoted `: ` breaking YAML; `nature: refactor`; an invalid
audit-result `status`). "grep-then-READ, never grep-then-conclude" and "commit is the quality boundary" both earned
their keep.

**Loop terminated 2026-07-20** — success criteria met (skill built, validated, fit for the fleet; every finding tracked;
the one blocker closed). The 4 deferred todos are execution/infra units, ready to execute.

### 2026-07-21 — EXECUTING the defi fold + reader/writer + Tier-2 VM (operator-authorized, loop re-armed)

Operator authorized (2026-07-21) the D3 execution + all 4 remaining todos. **Delete of legacy prefixes stays
human-only.**

**Understand phase (`wf_8ef4638a-04b`) — decisive findings:**

- The legacy tree is **8 objects, ONE date (2026-04-14), 5 cells** (dex_pools/{orca,raydium,kamino} +
  lending_indices/{kamino,solend}) — TINY, in-session, **no VM**. Each legacy file is multi-row (~98 pools/rows).
- **No existing script folds correctly** — the primary `migrate_legacy_solana_defi_to_canonical.py` writes to a
  now-**404 dead** dedicated bucket with the RETIRED `data_type=dex_pools` flat layout. Fold needs a small corrected
  fork (4 changes: consolidated bucket via `resolve_bucket_name` · v9 path + `dex_pool_state` · per-instrument `groupby`
  fan-out · `blob_exists`-skip UNION). Copy-not-move.
- Canonical twins today: ORCA 14,094 · RAYDIUM 100 (missing 32) · **KAMINO-vault 0 · SOLEND 0 (legacy is the ONLY
  copy)** — the fold COPIES those.
- **Writer needs NO change** — the live MTDS writer already emits canonical (`solana_amm_pool`/`solana_vault`,
  `dex_pool_state`).
- **Reader (25):** execution-service `solana_amm_depth_provider.py` reads the legacy prefix + its `resolve_bucket_name`
  call raises `TypeError` (bad `kind`/`env`/`project_id`, outside the `try`) → likely dead-on-arrival. Clean diff.
- **F6 is a 3-REPO ATOM** (not just an adapter stamp): IS adapters (raydium/orca/kamino →
  SOLANA_AMM_POOL/SOLANA_VAULT) + UAC `valid_data_types_for_venue_instrument_type` capability + IS enumerator
  `_ADDRESS_KEYED_ITYPES`. Skipping any part swaps one desync for another. Direction A is SSOT-grounded. Included
  because the fold's coverage won't reconcile without it ("migrate ... writers" covers the enumerator).

**Stage 1 in flight (`wf_ecb25452-3df`):** fold-script author (no run) · reader repoint (25) · F6 3-repo fix · Tier-2 VM
registration (31) — each QG-green + quickmerge. **Stage 2 (orchestrator):** run the fold
dry-run→verify→apply→manifest→verify twins. **Stage 3:** todo 32 (launcher+validator) after 31 lands.

### 2026-07-21 (cont.) — FOLD APPLIED + verified; reader repointed

- **24 ✅ DONE — the fold ran on real infra and is verified.** `market-tick-data-service@13b9dac5` shipped the corrected
  fork `fold_legacy_solana_defi_to_consolidated_canonical_2026_07_21.py` (per-instrument fan-out via `write_defi_rows`,
  the MTDS write-path SSOT → byte-identical to the live writer; UNION-idempotent via `blob_exists`; copy-not-move).
  Dry-run → verified → applied 2026-07-21 (`GCP_PROJECT_ID` required in env). **648 legacy-only instruments written,
  14,159 skipped.** Verified twins now exist where R5 said there were NONE: **KAMINO `solana_vault` 0→513 · SOLEND
  `solana_lending` 0→59 · KAMINO `solana_lending` 0→44 · RAYDIUM `solana_amm_pool` 100→132** (the 32 legacy-only pools);
  ORCA 14,094 + the 66 Raydium intersection correctly skipped. The dry-run counts matched R5 exactly (raydium 32 write /
  66 skip). **The legacy `dex_pools/`+`lending_indices/` prefixes now have canonical twins for every cell → the delete
  is SAFE, but stays HUMAN-ONLY per the ruling.**
- **25 ✅ DONE — `execution-service@45628a37`.** Repointed `solana_amm_depth_provider.py` from the legacy `dex_pools/`
  template to the canonical `dex_pool_state` path (via `build_defi_partition_path`), and fixed the `resolve_bucket_name`
  call that raised `TypeError` (bad `kind`/`env`/`project_id` kwargs, outside the `try` → dead-on-arrival). The ship
  agent caught a spec error: the writer emits `pipeline_mode=batch_onchain_subgraph` (not coarse `batch`), so the reader
  derives the source-aware mode to match — a coarse prefix would have listed zero objects. New regression test added.
- **Manifest:** the fold wrote OBJECTS (the source of truth); the availability manifest re-derives from GCS via the
  standard consolidator. To reflect the 648 new twins as `captured`, the consolidator must run over `day=2026-04-14`
  defi — a follow-up (the objects exist now; the depth-provider reads objects directly).
- **In progress:** F6 3-repo enumerator fix (IS dead-WIP has C.1+C.3; UAC C.2 + commit pending — UAC tree just became
  quiescent) · 31 (deployment-service landed `@bd7a7bd8`; UAC yaml `datapoint-validation` kind pending commit) · 32.

### 2026-07-21 (cont.) — F6 enumerator fix shipped; 31 done; 32 in flight

- **F6 enumerator vocab — SHIPPED (3-repo atom complete).** `unified-api-contracts@5d83b729` (C.2 — the defi capability
  declaration accepts `solana_amm_pool`/`solana_vault`) + `instruments-service@c781eb0b` (C.1 —
  raydium/orca→SOLANA_AMM_POOL, kamino→SOLANA_VAULT in all 3 adapters; C.3 — `_ADDRESS_KEYED_ITYPES` gains the solana
  types; regression test; defi expected-universe golden regenerated). Direction A (expected matches the writer) per the
  SSOT. **The folded `solana_amm_pool` twins now reconcile against the expected universe** — F6's coverage-denominator
  inflation is fixed. **Side-benefit caught in flight:** the defi golden was already fleet-RED on clean HEAD
  (pre-existing cross-repo drift from the committed `5d83b729`/`d4d85854` that shipped without regenerating the IS
  golden — the known `instruments_service_qg_red_golden_drift` hazard); this commit's regen cleared it. Verified: only
  defi.json changed (the 4 cosmetic non-defi golden reformats were reverted); IS QG green (4729 passed).
- **31 ✅ DONE** — `deployment-service@bd7a7bd8` (VmPrefixSpec `datapoint-validation-{ag}-` + registry) +
  `unified-api-contracts@5d83b729` (the `datapoint-validation` results-bucket kind in cloud-providers.yaml, all 3
  mirrors) → `resolve_bucket_name(cloud="gcp", kind="datapoint-validation")` resolves.
- **32 in flight** — a background agent is authoring `launch-datapoint-validation-vm.sh` +
  `validate_datapoint_schema_id.py` in deployment-service (SPOT, single-walk, results manifest via UTL ManifestWriter).
- **Manifest re-derive (follow-up):** the fold wrote 648 canonical OBJECTS; the availability manifest re-derives from
  GCS via the standard consolidator — it must run over `day=2026-04-14` defi to mark the twins `captured`. The
  depth-provider (25) reads objects directly, so this does not block execution; it is a coverage-surface refresh.

### 2026-07-21 (cont.) — manifest registration: mechanism found, filed as bounded follow-up

Attempted the manifest-registration step of the fold. **Finding:** the consolidator merges `record_captured` per-VM
shards — it does NOT re-derive rows from raw GCS objects (the fold script's docstring was wrong). Authored + dry-ran a
`--register-manifest` pass (DefiManifestRecorder, **714 rows** verified: 648 new twins + 66 idempotent RAYDIUM refresh,
ORCA skipped). The **apply hung/exited without flushing** a `_index/per_vm/` shard in a plain-script context (the
`ManifestWriter(batch_size=1)` recorder is coupled to the live handler's async flush discipline). **No partial manifest
write occurred** (per_vm still holds only `_legacy_seed.parquet`). Reverted the broken register-mode from the fold
script (the shipped object-fold is clean) and filed the exact recipe + finding as a bounded P1 follow-up →
`plans/active/issues/defi_fold_manifest_registration_pending_2026_07_21.md`. **The DATA migration + delete-safety are
COMPLETE**; the manifest rows are a coverage-surface refresh (the depth-provider reads objects directly, so nothing is
blocked). This is the one operator-ask sub-part that met a genuine technical obstacle, tracked with a precise recipe.

### 2026-07-21 — FINAL REPORT: defi migration + Tier-2 VM complete (all 4 todos done)

Operator-authorized defi legacy→canonical migration + the 4 remaining todos (24/25/31/32), executed on the `/autonomous`
loop. **All four DONE.**

**24 — Fold the data ✅** `market-tick-data-service@13b9dac5`. Dry-run-gated → applied on real infra → verified. **648
legacy-only Solana instruments** copied to canonical twins where R5 found NONE: KAMINO `solana_vault` 0→513 · SOLEND
`solana_lending` 0→59 · KAMINO `solana_lending` 0→44 · RAYDIUM `solana_amm_pool` 100→132 (the 32 legacy-only pools).
ORCA 14,094 + the 66 Raydium intersection skipped (UNION-idempotent). Copy-not-move — **legacy delete is now SAFE but
HUMAN-ONLY**. Reused `write_defi_rows` (the writer SSOT) so the folded objects are byte-identical to the live writer's.

**25 — Repoint reader ✅** `execution-service@45628a37`. Legacy `dex_pools/` template → canonical `dex_pool_state` via
`build_defi_partition_path`; fixed the `resolve_bucket_name` call that raised `TypeError` (dead-on-arrival). A
spec-error catch: the writer emits `pipeline_mode=batch_onchain_subgraph`, not coarse `batch`.

**Writers ✅** No change needed — the live MTDS writer already emits canonical.

**F6 — Enumerator vocab ✅ (3-repo atom)** `uac@5d83b729` (capability) + `instruments-service@c781eb0b` (adapters +
address-keying + golden). Solana venues now stamp `solana_amm_pool`/`solana_vault` (not `pool`), so the folded twins
reconcile against the expected universe. Side-benefit: cleared a pre-existing fleet-RED defi golden (cross-repo drift).

**31 — Tier-2 VM registration ✅** `deployment-service@bd7a7bd8` + `uac@5d83b729`.

**32 — Tier-2 VM launcher + validator ✅** `deployment-service@00a980e` (`launch-datapoint-validation-vm.sh` + registry
parity, SPOT, single-walk) + `instruments-service@ad05e34` (`validate_datapoint_schema_id.py` — the sanctioned single
walk running G2 id-canonical + G3 schema per datapoint). The agent corrected 3 SSOT-prose inaccuracies against the code
(per-VM shard path, `record_vm_progress` not exported, real violation codes) — see the census doc appendix.

**ONE tracked follow-up (a genuine technical wall, not a descope):** manifest-row registration for the 648 folded
objects — `defi_fold_manifest_registration_pending_2026_07_21.md`. The consolidator merges `record_captured` per-VM
shards (not raw objects), and the standalone `DefiManifestRecorder` didn't flush in a plain-script context (no partial
write). The exact 714-row recipe is filed. This is a coverage-surface refresh; the data + delete-safety are complete and
the depth-provider reads objects directly.

**Not runtime-verified:** the Tier-2 VM has not been launch-run (author+ship scope). A real campaign (+ the ≤30-min
heartbeat watchdog) is the next operational step.

**Loop terminated 2026-07-21** — all 4 todos done + verified; the one obstacle tracked with a precise recipe. Delete of
the legacy prefixes remains the operator's to run.

### 2026-07-21 — legacy prefixes DELETED (operator-executed) + verified

The operator executed the prod delete of `dex_pools/` + `lending_indices/` (prod-bucket delete = human-only; I staged +
verified, the operator ran it). Post-delete read-only verification: **legacy prefixes = 0 objects; all 5 canonical twin
cells intact** (513/59/44/132/14,094) — the `rm -r` hit only the legacy prefixes, not `raw_tick_data/`. The
fold→repoint→delete migration is COMPLETE end-to-end. `defi_dex_pools_delete_order_stale_2026_07_20` → RESOLVED. Only
residual: the manifest-row registration follow-up.

### 2026-07-21 — pre-compact checkpoint (defi migration + delete + rulings + MDPS + funding/staking + orphans)

**Shipped + verified this session (all pushed, ahead=0):**

- **defi dex_pools/lending_indices FOLD → REPOINT → DELETE — COMPLETE.** 648 legacy-only Solana twins folded
  (`mtds@13b9dac5`) + verified (KAMINO-vault 0→513 · SOLEND 0→59 · KAMINO-lending 0→44 · RAYDIUM 100→132); reader
  repointed (`execution-service@45628a37`); F6 enumerator vocab 3-repo (`uac@5d83b729` + `is@c781eb0b`); Tier-2 VM 31/32
  (`ds@bd7a7bd8`, `ds@00a980e`, `is@ad05e34`); **operator prod-DELETED the legacy prefixes** — re-probed 0 objects,
  twins intact. `defi_dex_pools_delete_order_stale` RESOLVED; codex DO-NOT-DELETE banners flipped (CLAUDE.md + inventory
  rows 7/8). **Residual: the 648 twins' manifest rows are UNREGISTERED**
  (`defi_fold_manifest_registration_pending_2026_07_21` — the standalone DefiManifestRecorder didn't flush; NO partial
  write occurred; exact 714-row recipe filed).
- **3 operator rulings recorded** (`uac@…` no — `unified-trading-pm@14f84cf0b`): (R1) features `by_date/day=` is SSOT;
  (R2) HARD RULE every data-at-rest tree is full canonical HIVE, `instrument_availability` → hive (via sink PREFIX, not
  the partition dict — it sorts keys alphabetically); (R3) cefi chain-tail **v6 everywhere, migrate all, no v5**. Each
  in the tie-breaker SSOT §11b + cutover-register §6a/6b/6c + inventory rows #16/#17, with a migration issue doc each.
- **MDPS candle layer added to the skill** (`9161c8d7b`): new codex SSOT `mdps-candle-canonical-reconciliation.md` +
  `reference-mdps.md` + the `--layer {raw-tick,candles}` flag + Phase F todos 34-42. Audit target = the operator's
  Option-A ruling (declared registry template wins; 8-phase migration, NOTHING migrated yet → whole candle corpus is
  `migration_pending`).
- **Funding + staking downstream readers = CANONICAL on the production path** (`a18f0163c` +
  `downstream_funding_staking_canonical_reader_audit_2026_07_21`): every production funding
  (perp_funding/derivative_ticker)
  - staking (lst_rates) consumer reads canonical via `resolve_bucket_name`; the PATH_REGISTRY 404 defect is a LATENT
    trap (UTL thin clients only, zero non-test callers). Exceptions = 4 non-runtime campaign scripts (worst = the
    silent-empty `trace_carry_staked_basis.py`) + 1 CLI fallback — cleanup todos filed.
- **Orphan assessment** (`estate_orphan_assessment_2026_07_21`): SPORTS measured — **214,319 ORPHAN_REAL** (real data,
  no manifest row) + 34,385 legacy-dup, reports durable in `gs://…/_index/audit/orphan_sweep_sports.parquet`. defi/cefi/
  tradfi FAILED in-session on the multi-GB manifest download (ChunkedEncodingError, defi index ~1.8GB); prediction hung
  in the join phase — all four need the VM run (todo 3 of that issue).
- **Rescued** (`5865f31ab`): the census-doc Tier-2-validator appendix was dropped from a retry re-stage — pre-compact
  audit caught it uncommitted.

## Deferred work after 2026-07-21

| Item                                                                                 | State / why                                                                                                                                 | Blocked-on                                                            |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| defi 648-twin manifest registration (714 rows)                                       | **Not done** — DefiManifestRecorder standalone flush issue; recipe filed                                                                    | nobody — pick up `defi_fold_manifest_registration_pending_2026_07_21` |
| Sports orphan back-fill (214,319 rows) + legacy-dup triage (34,385)                  | **Not done** — real data-correctness work; audit parquets are in GCS                                                                        | nobody — `estate_orphan_assessment_2026_07_21` todos 1-2              |
| Orphan sweep for defi/cefi/tradfi/prediction                                         | **Not done** — in-session multi-GB manifest download breaks                                                                                 | **operator-owned** — I offered the SPOT VM launch; awaiting go-ahead  |
| R1/R2/R3 writer migrations (features by_date, instrument_availability hive, cefi v6) | **Not done** — writer fixes filed as 3 issue docs 2026-07-21                                                                                | nobody — pick up the 3 issue docs                                     |
| D2 defi LENDING full retire (~16.7M rows)                                            | **Not done** — gated                                                                                                                        | `defi_lending_writer_retire_prerequisite` must ship first             |
| MDPS candle Option-A migration (~10-20M objects)                                     | **Cannot be done yet / operator-owned** — the 8-phase migration is scoped in `candle_feature_canonical_path_divergence` (running elsewhere) | that migration effort                                                 |
| Tier-2 datapoint-validation VM — a real launch-run                                   | **Not done** — built (32), never launch-run                                                                                                 | operator/operational — an actual campaign                             |
| Funding/staking latent-trap cleanup (4 scripts + UTL registry)                       | **Not done** — P2, latent (non-runtime)                                                                                                     | nobody — `downstream_funding_staking…` todos                          |

**Recommended NEXT** (sports orphan back-fill this pointed at is now DONE, see flipped checkbox below): launch the
orphan VM for the 4 blocked AGs.

- [x] ✅ [DATA] P1. **Sports orphan back-fill (214,319 rows) + legacy-dup triage (34,385)** — **CLOSED 2026-08-09
      (round11 RECLASSIFY sweep), verified stale-citation, not new work.** Per the "Deferred work after 2026-07-21"
      table above, this todo pointed at `estate_orphan_assessment_2026_07_21.md` todos 1-2 as the pending
      real-data-correctness work. Direct read of that doc today confirms both are already `[x]` DONE 2026-07-22: todo 1
      "Back-fill the 214,319 sports ORPHAN_REAL rows via `record_captured`" is `[x]`, and todo 2 "Triage the 34,385
      sports LEGACY_DUPLICATE" is `[x]` — the exact row counts (214,319 and 34,385) match this todo's own text verbatim,
      confirming these are the same rows, not a coincidence. The 2026-08-03 na-eligibility-audit pass had already
      flagged this as stale (citing the same evidence: 4 cells + 97,606 cells recorded via `record_captured` for the
      odds/reference legs, 0 of 34,385 rows passed the 5-part delete-proof) but left the checkbox open pending a
      dedicated re-verification pass against the source doc; that re-verification is done now, so the checkbox flips.
      The other 7 still-"Not done" items in the "Deferred work after 2026-07-21" table are unaffected — not re-triaged
      in this pass.
- [x] ✅ [DATA] P2. **Measure the historical per-venue non-canonical row count for the 8 CeFi live spot venues fixed in
      `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md`** (archived, resolved) — that issue's own
      code-level fix (BINANCE/COINBASE/OKX/UPBIT/BITFINEX/BITGET/BYBIT/KRAKEN-SPOT now emit canonical `SPOT_PAIR` +
      `BASE-QUOTE` ids) shipped without ever measuring the SIZE of the pre-fix non-canonical population — the census
      that originally found this only measured the aggregate `instrument_type=spot` lowercase axis (4,923 rows across
      ALL cefi), never the id-FORM/hyphenation dimension per venue. Run this skill's distinct-value census (G1, § 3f),
      scoped to `asset_group=cefi` and these 8 venues, comparing `is_canonical_instrument_id()` pre/post-fix row counts
      — a real, not-yet-known number needed to size any historical backfill/repair decision (the fix only stops NEW rows
      from being wrong). **Landed 2026-08-09, `d8c682dd5a8`** — see Progress Log below.

## Lessons (do not re-learn)

- **In-session single-walk breaks at scale on the manifest DOWNLOAD, not the object walk** — a ~1.8GB
  `availability_index.parquet` snaps a single HTTP read (`ChunkedEncodingError`). Run large-AG sweeps on a VM, or
  stream/ resume the loader. `list_blobs` itself was fine (prediction swept 1.15M objects clean).
- **`DefiManifestRecorder`/`ManifestWriter(batch_size=1)` does not flush cleanly from a plain script** (handler-runtime
  coupled) — the manifest register hung without persisting; NO partial write. Use the handler path or fix the
  standalone.
- **Detached (`setsid`) background processes are unreliable here** — they die without flushing; use the harness
  `run_in_background` (tracked, notifies) instead. Cost me 3 silent-exit debugging rounds.
- **Adversarial verification paid off repeatedly** — caught the `pipeline_mode=batch` spec error (writer emits
  `batch_onchain_subgraph`), the false `canonical_path_templates()`-doesn't-exist (it's at `possible_manifest.py:352`),
  and the false "twin VERIFIED ABSENT" (probed `instrument_type=pool` not `solana_amm_pool`). Grep-then-READ, always.
- **The dry-run gate is the safety rail for a prod write** — the fold dry-run showed exactly 648/14,159 (matching R5)
  before any object was written. Never `--apply` a prod migration without inspecting the dry-run.
- **The pre-commit hygiene gate caught 4 real defects** this session (unquoted `: ` in YAML summaries ×2,
  `nature: refactor`, invalid audit-result `status`) — the commit-is-the-quality-boundary rule works.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — same dated operator ruling as the milestones gate (entry #10,
  option A) — standing reference surface; the single residual todo is a prod sports orphan back-fill + legacy-dup
  triage.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries, trimmed from 7 to fit the MVI
  cap) -- dropped cross-asset-canonical-target-ssot.md, both remaining open todos are orphan-measurement, not
  canonical-target work.
- **na-eligibility-audit 2026-08-03 (reclassify pass)**: KEEP-NA, valid (blocker-currency only) — the "Sports orphan
  back-fill" todo's named dependency (`estate_orphan_assessment_2026_07_21.md` todos 1-2) is stale-resolved (both `[x]`
  DONE 2026-07-22); annotated in place. The sibling todo (measure historical per-venue non-canonical row count for 8
  CeFi live-spot venues) is a bounded, worker-determinable measurement, but this doc remains the operator-designated
  standing reference surface (entry #10 option A) with a long, sensitive execution history — not flipping `assigned_vm`
  on it in this pass; a future dedicated pass could reclassify that one item on its own if desired. `assigned_vm`
  untouched.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09**: two actions, doc stays `assigned_vm: NA` (standing
  reference surface, unchanged). (1) Flipped the "Sports orphan back-fill" checkbox `[x]` — the 2026-08-03 pass's
  stale-citation finding is now independently re-verified (see the flipped checkbox for the evidence); this is a
  citation fix, not new work. (2) Extracted the "Measure the historical per-venue non-canonical row count for the 8 CeFi
  live-spot venues" item to
  [`cross_cutting_satellite_ao_dispatch_batch10_2026_08_09.md`](/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch10_2026_08_09.md)
  (+ gated finalize twin) — this is exactly the "future dedicated pass" the 2026-08-03 entry above anticipated. This
  doc's own checkbox for that item stays open here until the batch's finalize twin reconciles it.
- **batch-10 measurement landed 2026-08-09**: historical per-venue non-canonical population for the 8 CeFi live-spot
  venues fixed in `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md` is now measured. Method: one
  column-pruned, filtered read of the consolidated cefi `availability_index.parquet` (single-walk-exempt), scoped to
  `capture_status != attempted_failed` + `instrument_type == SPOT_PAIR`, then `is_canonical_instrument_id()` run against
  each row's manifest `instrument_id` -- the plain `instrument_type`-axis census alone reads **zero** non-canonical
  (that structural column was already `SPOT_PAIR` everywhere; the defect lives in the id/filename STRING, so id-form was
  the only way to see it). **Result** (of 1,957,165 total SPOT_PAIR rows across the 8 venues): **2,197 rows confirmed
  non-canonical `instrument_id`** + 6,251 undetermined (missing `instrument_id`, legacy pre-column rows) -- a bounded,
  low-risk repair population, materially smaller than the original 4,923-row `instrument_type=spot`-axis estimate (a
  different, coarser, all-cefi axis). Per-venue (non-canon/undetermined/total): BINANCE-SPOT 36/1,666/391,024 -
  COINBASE-SPOT 7/994/114,249 - OKX-SPOT 1,089/917/324,359 - UPBIT 1,046/1,379/348,092 - BITFINEX-SPOT 12/455/145,060 -
  BITGET-SPOT 6/784/222,701 - BYBIT-SPOT 1/0/185,979 - KRAKEN-SPOT 0/56/225,701. No repair executed -- measurement only,
  per todo scope.
