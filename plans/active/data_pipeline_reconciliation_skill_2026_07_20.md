---
doc_type: plan
title: /data-pipeline-reconciliation — per-asset-group four-surface canonicalisation reconciliation skill
summary:
  Build the SSOT-backed `/data-pipeline-reconciliation` skill that, per asset_group, reconciles the FOUR canonical
  surfaces — GCS object path, parquet content columns, manifest shard-atom key, and the catalogue/data-status render —
  across PROD buckets only, and emits typed findings plus proof-gated delete SUGGESTIONS. Phase A first closes the
  documented-understanding gap the audit exposed — 33 codex/plan contradictions (4 BLOCKING) and 12 missing codex SSOTs
  — because a skill that encodes its own canonical definition is unauditable by the workspace's own SSOT rule.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service, instruments-service, execution-service]
scope: [engineer, admin]
tags: [canonicalisation, reconciliation, skill, manifest, gcs-paths, catalogue, delete-safety, ssot, per-asset-group]
related:
  [
    ../../codex/02-data/cross-asset-canonical-target-ssot.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/02-data/honest-coverage-model.md,
    ../../codex/02-data/defi-canonical-naming-ssot.md,
    ../../codex/02-data/pipeline-mode-partition.md,
    defi_consolidated_closeout_2026_07_18.md,
    cefi_consolidated_closeout_2026_07_18.md,
    tradfi_consolidated_closeout_2026_07_18.md,
    sports_consolidated_closeout_2026_07_19.md,
    issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: manifest_master
assigned_vm: NA
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
---

# /data-pipeline-reconciliation — per-asset-group canonicalisation reconciliation skill

> **Origin**: operator request 2026-07-20 — a per-asset-group skill that checks 100% canonicalisation across GCS paths,
> the availability manifest, and the catalogues (instruments / features / ml / strategy), over **PROD buckets only**,
> flags non-canonical prefixes such as `market-data-tick-defi-prd-…/dex_pools`, and **suggests deletes** where a
> canonical twin already holds the data. Related to but separate from the backfill smoke skills
> (`/data-pipeline-check-is`, `/data-pipeline-check-mtds`) — those are **statically audited here, never run**.
>
> **Codex SSOTs**: `codex/02-data/cross-asset-canonical-target-ssot.md` (master tie-breaker) ·
> `availability-manifest-and-data-status.md` · `honest-coverage-model.md` · `defi-canonical-naming-ssot.md` ·
> `pipeline-mode-partition.md` · `codex/05-infrastructure/bucket-isolation-model.md` ·
> `codex/05-infrastructure/gcs-object-operations.md`. This plan **references** them; it does not duplicate them.

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
- [x] 3. ✅ [DATA] P0. **NEW SSOT** `codex/02-data/four-surface-reconciliation-procedure.md` — the executable comparison
      of the four surfaces for one shard, and how to classify each disagreement. This is the skill's core loop; it
      exists today only as fragments across ~8 docs.
- [x] 4. ✅ [DATA] P0. **NEW SSOT** `codex/02-data/reconciliation-finding-taxonomy.md` — the closed, named set of
      finding types (phantom · orphan · true_gap · missing_row · divergent_empty · masked-stale ·
      drift-axis-false-positive), each with detection method + safe remediation, **plus the operator-accepted exception
      list** (the 19,274 pre-2026-07-08 sports rows with blank pipeline_mode+source [BLK-d48acae4] · tradfi `combo`
      bare-underlying · defi two-id POOL divergence [Option A, intentional] · `batch_massive` read-recognition until
      purge · defi interim flat `LENDING` for market/event data_types). Without a closed set, consecutive runs are not
      diffable.
- [x] 5. ✅ [DATA] P0. **NEW SSOT** `codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — the **five-part proof**
      required before any delete suggestion rises above `unknown`: (1) twin resolves via `gcs_describe_object`, not by
      path construction; (2) **CONTENT verify, not existence** (R5 precedent); (3) grep-then-READ proof nothing still
      WRITES it; (4) grep-then-READ proof nothing still READS it; (5) the **legacy-COPIED-not-MOVED** invariant — a cell
      backed only by a legacy copy passes reconcile but reads MISSING under canonical-only status. Any failure →
      `no-migrate-first`. Absorbs the GCS DELETE SAFETY INVARIANT currently stranded in
      `pipeline-mode-partition.md:66-77`.
- [x] 6. ✅ [DATA] P0. **NEW SSOT** `codex/02-data/non-canonical-path-inventory.md` — the living register seeded with
      the audit's **29 entries** (location · why · canonical twin · still-written-by · delete disposition), grouped by
      the five dispositions. This IS the input to the delete-suggestion feature; re-deriving it per run costs a walk,
      and keeping it in plans loses it at archival.
- [x] 7. ✅ [DATA] P1. **NEW SSOT** `codex/02-data/canonical-cutover-register.md` — per-AG effective-from dates for
      `require_pipeline_mode`, instrument_type case, tradfi chain tail, defi leaf filename, sports data_type case.
      Without it the skill cannot separate "legitimately historical" from "non-canonical" and will either flood false
      positives on pre-cutover data or silently pass post-cutover regressions.
- [x] 8. ✅ [DATA] P1. **NEW SSOT** `codex/02-data/orphan-object-detection.md` — the inverse case no current tool
      covers: a parquet on GCS with **no manifest row AND outside the oracle's expected set** is invisible to every
      existing tool (all are manifest-row- or oracle-driven). The delete-suggestion feature is precisely orphan
      detection.
- [ ] 9. [DATA] P1. **Correct the stale/contradictory codex** (each with a dated correction annotation, not a silent
      edit): `cross-asset-canonical-target-ssot.md` §8 defi leaf filename → `{canonical_instrument_id}.parquet` (a stale
      template inside the designated tie-breaker doc is the corpus's most dangerous defect) · §8 tradfi chain tail →
      `underlying=/quote=/margin=` (shipped code wins) · §5 LENDING interim banner (B3) ·
      `per-asset-group-bucket-layouts.md:137` third filename form · SUPERSEDED banners on the two v1 honest-coverage
      formulas (`availability-manifest-and-data-status.md:117,:947,:1834-1844` + `manifest-consolidator-ssot.md:296`) ·
      regenerate the manifest schema block from UTL `manifest_writer/_rows.py` (doc omits 5 live columns, duplicates
      `source`) · SUPERSEDED-banner `data-catalogue-schema.md` (documents an artifact, writer, reader, updater and
      validating plan that **do not exist**) and replace with `service-shard-status-catalogue.md` describing the
      `shard_status[AG][VENUE].start_date` shape deployment-api actually consumes.
- [ ] 10. [CODE] P1. **NEW SSOT** `codex/06-coding-standards/canonical-write-guard-contract.md` — which lanes call
      `canonical_path_violations`, with which `require_pipeline_mode`, and which are deliberately unguarded (today
      tradfi-W1 + cefi-live + microstructure guarded; cefi-batch, prediction, sports unguarded with no stated intent).
      Absorbs the dangling pointer to the non-existent `canonical-write-conventions.md`. **Plus**: extend
      `codex/05-infrastructure/bucket-isolation-model.md` with a **bucket-name resolution authority** section —
      `cloud-providers.yaml`/`resolve_bucket_name` WINS; UTL `PATH_REGISTRY`/`build_bucket` Group-A rows resolve to
      buckets that **now 404** and are reached at runtime by `domain_client/clients/market_data.py:56` (file as a P0
      latent defect; check whether UTL market-data domain-client reads are currently failing).
- [ ] 11. [DATA] P1. **Reconcile the single-walk rule** — `availability-manifest-and-data-status.md` §9 ("walks are
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

- [ ] 16. [DATA] P0. Run the skill for **defi** (the hardest: `chain=`, two-id model, capture STOPPED, the `dex_pools`
      relic, Shape-B duplicate tree). Verify it reproduces the audit's known findings and raises no new false positives.
- [ ] 17. [DATA] P0. Run for **cefi** and **tradfi**; confirm the v5/v6 dual chain-tail and the `batch_massive`
      read-recognition carve-out are handled without flagging accepted exceptions.
- [ ] 18. [DATA] P1. Run for **prediction** and **sports**; confirm the CQG manifest-only grain and the
      no-`asset_group=` sports tree produce zero structural false positives.
- [ ] 19. [REVIEW] P1. **Post-phase codex audit** — verify every new/edited codex doc is internally consistent and that
      no plan↔codex drift remains; add the one-liner + conditional-domain pointer to `cursor-configs/CLAUDE.md` (honour
      the 40 KB cap — condense, never raise it).

### Phase D — apply the 2026-07-20 operator rulings (D1 / D2 / D3)

- [ ] 20. [DATA] P0. **D1 UPPERCASE — correct the docs and unfreeze.** Flip `cross-asset-canonical-target-ssot.md`
      §7/§11 lowercase→UPPERCASE **for the manifest COLUMN only** (path segment stays lowercase, id middle segment stays
      UPPER — neither was in question), with a dated ruling annotation. Correct the tradfi closeout's self-contradicting
      worklist (it orders a case-fold in the opposite direction, 750,715 rows) to fold UP. Record that the DRAIN-GATED
      freeze on `instruments-service@555ddf1c` + the tradfi Phase-B script is **lifted** (they are now ratified).
- [ ] 21. [SCRIPT] P0. **D1 — stop refusing the axis in the skill.** Remove the C2a refusal from `SKILL.md` § 3e and the
      taxonomy's REFUSED-axes section; replace with the enforced rule (column = UPPERCASE) plus a `migration_pending`
      exception entry for the defi rows not yet migrated UP. The case-insensitive comparison workaround comes out.
- [ ] 22. [DATA] P0. **D2 — banner codex §5 with the prerequisite.** §5's "flat `LENDING` is RETIRED" is now the correct
      TARGET; add a dated banner stating it is **not yet implemented**, that the first attempt was reversed after
      breaking 5+ MTDS lending writers, and that the mandatory order is **fix-writers → migrate ~16.7M rows → re-sync
      the shard atom**. Reclassify market/event flat `LENDING` from `refused/unruled` to `migration_pending` in the
      taxonomy so the skill neither flags it nor treats it as an open question.
- [ ] 23. [DATA] P1. **D2 — scope the writer fix (prerequisite for the migration).** Identify and enumerate the 5+ MTDS
      lending writers that broke into `attempted_failed`/zero-data on the reversed attempt; file the fix as its own plan
      (this plan does not own MTDS writer work). **The migration must not start until that plan is green** — this is the
      step whose omission caused the reversal.
- [ ] 24. [DATA] P1. **D3 — fold before anything else.** Content-UNION the 32 legacy-only Raydium pools into the
      canonical tree, and confirm the KAMINO/SOLEND `dex_pool_state` cells (canonical count **zero** — legacy is the
      only copy) are covered by the fold. Verify by count + content, not by path existence.
- [ ] 25. [CODE] P1. **D3 — repoint execution-service, then re-verify.** Point `providers/solana_amm_depth_provider.py`
      at the canonical `data_type=dex_pool_state` path and fix its broken call to
      `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`. Resolve the open sub-question first
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
