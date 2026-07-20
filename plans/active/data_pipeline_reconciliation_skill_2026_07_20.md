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
**32 legacy-only high-TVL Raydium pools absent from canonical** (XMR/USDC $47M, BNB/USDC $18M). The live probe run
during this audit corroborates: `venue={ORCA,RAYDIUM,KAMINO,SOLEND}` return **zero** objects under `raw_tick_data/` on
both the relic's own day and a recent day — **no canonical twin exists**. And `execution-service` **still reads the
legacy shape at runtime** (`providers/solana_amm_depth_provider.py:41`). Track 2 and A6 were never updated after R5.

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

- [ ] [DATA] P0-01. **NOTIFY OPERATOR + file issue doc**
      `plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md` capturing B1: R5 overturned the duplicate
      verdict, canonical twin VERIFIED ABSENT, execution-service still reads the legacy shape. **Amend
      `defi_consolidated_closeout_2026_07_18.md` Track 2 and `canonical_closeout_open_questions_2026_07_18.md` §A6 in
      place** to FOLD-not-delete with the required order: (1) content-UNION the 32 legacy-only pools into canonical, (2)
      repoint `execution-service/providers/solana_amm_depth_provider.py` to `data_type=dex_pool_state` (and fix its
      broken `resolve_bucket_name` call — `market-data-tick-defi` is a name fragment, not a yaml key, and
      `env=`/`project_id=` are not parameters, so it **raises**), (3) only then consider delete.
- [ ] [DATA] P0-02. **Escalate B2/B3/B4 to the operator as structured option-sets** (A/B/C + Other per the escalation
      rule). Until ruled: the skill MUST NOT report `instrument_type` column casing as a finding, MUST NOT propose any
      casing migration, and MUST NOT flag `lending` on market/event data_types as non-canonical. Freeze the two
      DRAIN-GATED `--apply` runs (`instruments-service@555ddf1c` + the tradfi Phase-B script).
- [ ] [DATA] P0-03. **NEW SSOT** `codex/02-data/four-surface-reconciliation-procedure.md` — the executable comparison of
      the four surfaces for one shard, and how to classify each disagreement. This is the skill's core loop; it exists
      today only as fragments across ~8 docs.
- [ ] [DATA] P0-04. **NEW SSOT** `codex/02-data/reconciliation-finding-taxonomy.md` — the closed, named set of finding
      types (phantom · orphan · true_gap · missing_row · divergent_empty · masked-stale · drift-axis-false-positive),
      each with detection method + safe remediation, **plus the operator-accepted exception list** (the 19,274
      pre-2026-07-08 sports rows with blank pipeline_mode+source [BLK-d48acae4] · tradfi `combo` bare-underlying · defi
      two-id POOL divergence [Option A, intentional] · `batch_massive` read-recognition until purge · defi interim flat
      `LENDING` for market/event data_types). Without a closed set, consecutive runs are not diffable.
- [ ] [DATA] P0-05. **NEW SSOT** `codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — the **five-part proof**
      required before any delete suggestion rises above `unknown`: (1) twin resolves via `gcs_describe_object`, not by
      path construction; (2) **CONTENT verify, not existence** (R5 precedent); (3) grep-then-READ proof nothing still
      WRITES it; (4) grep-then-READ proof nothing still READS it; (5) the **legacy-COPIED-not-MOVED** invariant — a cell
      backed only by a legacy copy passes reconcile but reads MISSING under canonical-only status. Any failure →
      `no-migrate-first`. Absorbs the GCS DELETE SAFETY INVARIANT currently stranded in
      `pipeline-mode-partition.md:66-77`.
- [ ] [DATA] P0-06. **NEW SSOT** `codex/02-data/non-canonical-path-inventory.md` — the living register seeded with the
      audit's **29 entries** (location · why · canonical twin · still-written-by · delete disposition), grouped by the
      five dispositions. This IS the input to the delete-suggestion feature; re-deriving it per run costs a walk, and
      keeping it in plans loses it at archival.
- [ ] [DATA] P1-07. **NEW SSOT** `codex/02-data/canonical-cutover-register.md` — per-AG effective-from dates for
      `require_pipeline_mode`, instrument_type case, tradfi chain tail, defi leaf filename, sports data_type case.
      Without it the skill cannot separate "legitimately historical" from "non-canonical" and will either flood false
      positives on pre-cutover data or silently pass post-cutover regressions.
- [ ] [DATA] P1-08. **NEW SSOT** `codex/02-data/orphan-object-detection.md` — the inverse case no current tool covers: a
      parquet on GCS with **no manifest row AND outside the oracle's expected set** is invisible to every existing tool
      (all are manifest-row- or oracle-driven). The delete-suggestion feature is precisely orphan detection.
- [ ] [DATA] P1-09. **Correct the stale/contradictory codex** (each with a dated correction annotation, not a silent
      edit): `cross-asset-canonical-target-ssot.md` §8 defi leaf filename → `{canonical_instrument_id}.parquet` (a stale
      template inside the designated tie-breaker doc is the corpus's most dangerous defect) · §8 tradfi chain tail →
      `underlying=/quote=/margin=` (shipped code wins) · §5 LENDING interim banner (B3) ·
      `per-asset-group-bucket-layouts.md:137` third filename form · SUPERSEDED banners on the two v1 honest-coverage
      formulas (`availability-manifest-and-data-status.md:117,:947,:1834-1844` + `manifest-consolidator-ssot.md:296`) ·
      regenerate the manifest schema block from UTL `manifest_writer/_rows.py` (doc omits 5 live columns, duplicates
      `source`) · SUPERSEDED-banner `data-catalogue-schema.md` (documents an artifact, writer, reader, updater and
      validating plan that **do not exist**) and replace with `service-shard-status-catalogue.md` describing the
      `shard_status[AG][VENUE].start_date` shape deployment-api actually consumes.
- [ ] [CODE] P1-10. **NEW SSOT** `codex/06-coding-standards/canonical-write-guard-contract.md` — which lanes call
      `canonical_path_violations`, with which `require_pipeline_mode`, and which are deliberately unguarded (today
      tradfi-W1 + cefi-live + microstructure guarded; cefi-batch, prediction, sports unguarded with no stated intent).
      Absorbs the dangling pointer to the non-existent `canonical-write-conventions.md`. **Plus**: extend
      `codex/05-infrastructure/bucket-isolation-model.md` with a **bucket-name resolution authority** section —
      `cloud-providers.yaml`/`resolve_bucket_name` WINS; UTL `PATH_REGISTRY`/`build_bucket` Group-A rows resolve to
      buckets that **now 404** and are reached at runtime by `domain_client/clients/market_data.py:56` (file as a P0
      latent defect; check whether UTL market-data domain-client reads are currently failing).
- [ ] [DATA] P1-11. **Reconcile the single-walk rule** — `availability-manifest-and-data-status.md` §9 ("walks are
      review-blocking") and `gcs-object-operations.md` (six-point contract _for_ walks) never cross-reference and read
      as contradictory. State the reconciled rule in both: **ONE walk per corpus per campaign, all passes bundled onto
      that snapshot**, and fix §9's factually wrong exemption rationale (it claims a script "reads the index, not the
      corpus" — false of the very script it names).

### Phase B — author the skill

- [ ] [SCRIPT] P0-12. Author `cursor-configs/skills/data-pipeline-reconciliation/SKILL.md` matching the two sibling
      skills **exactly**: frontmatter is exactly `name` + `description` (one prose blob naming the phases, the hard
      constraints, /autonomous composition, and an explicit `Trigger on …` clause); body follows the numbered skeleton
      (H1 · purpose · bolded **Shard atom** line · `## 0.` required-input gate · `## 1.` composing with /autonomous ·
      `## 2.` Phase 0 · `## 3.` Phase 1 with `### 3a/3b/3c` · `## 4.` Phase 2 · `## 5.` write+present report · `## 6.`
      under /autonomous loop · `## Extending to a new asset_group` · `## Not wired into quality-gates.sh`). Durable
      rules live in codex and are **referenced**, never restated. No re-linking step is needed — `.claude/skills` is a
      single directory symlink to `cursor-configs/skills/` since 2026-07-17, so a new skill dir surfaces fleet-wide on
      `git pull`.
- [ ] [SCRIPT] P0-13. **Report contract** — emit a markdown + sibling JSON pair at
      `plans/audit/results/data_pipeline_reconciliation_<AG>_<YYYY_MM_DD>.md` and **PRINT the full rendered markdown to
      stdout** (§5 of the sibling skills mandates relaying printed content directly, never "done, see the report").
      Include the auto-generated **Bucket paths** table naming which bucket each read targeted, a per-surface verdict
      per shard, and typed findings from the P0-04 taxonomy so consecutive runs diff cleanly.
- [ ] [SCRIPT] P1-14. **Per-AG reference sheets** in the skill dir — one per asset_group encoding only the _pointers_
      and the per-AG hazards (sports' no-`asset_group=` tree + 4 layouts + non-obvious `entity=` names · prediction's
      manifest-only CQG grain + "do not run the phantom reconciler" · defi's `chain=`-after-`venue=` + two-id model +
      capture-STOPPED state · tradfi's raising guard + `batch_massive` carve-out · cefi's v5/v6 dual chain-tail).
- [ ] [SCRIPT] P1-15. **Static audit of the backfill-smoke write paths** (audit only — never run them): confirm
      `/data-pipeline-check-is` and `/data-pipeline-check-mtds` write to `-test-` buckets ONLY and that their writers
      emit the canonical grammar. Record findings as todos here or an issue doc; do **not** fix writer defects in this
      plan.

### Phase C — validate per asset_group

- [ ] [DATA] P0-16. Run the skill for **defi** (the hardest: `chain=`, two-id model, capture STOPPED, the `dex_pools`
      relic, Shape-B duplicate tree). Verify it reproduces the audit's known findings and raises no new false positives.
- [ ] [DATA] P0-17. Run for **cefi** and **tradfi**; confirm the v5/v6 dual chain-tail and the `batch_massive`
      read-recognition carve-out are handled without flagging accepted exceptions.
- [ ] [DATA] P1-18. Run for **prediction** and **sports**; confirm the CQG manifest-only grain and the no-`asset_group=`
      sports tree produce zero structural false positives.
- [ ] [REVIEW] P1-19. **Post-phase codex audit** — verify every new/edited codex doc is internally consistent and that
      no plan↔codex drift remains; add the one-liner + conditional-domain pointer to `cursor-configs/CLAUDE.md` (honour
      the 40 KB cap — condense, never raise it).

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
