---
doc_type: plan
title: Codex-vs-repo-docs SSOT audit + consolidation (all active repos)
summary:
  Audit and consolidate all active repo docs/ folders against codex/ SSOT, removing duplication and migrating unique
  content into codex.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [audit, documentation, ssot, codex, consolidation, deduplication]
related: []
created: 2026-06-01
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
last_updated: 2026-07-28
locked_by: live-defi-rollout
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    unified-trading-pm/codex/06-coding-standards/documentation-standards.md,
    unified-trading-pm/codex/00-SSOT-INDEX.md,
    unified-trading-pm/plans/archive/issues/repo_docs_codex_ssot_consolidation_2026_06_01.md,
  ]
assigned_role: review
drift_direction: correct-codex
model_tier: sonnet-doable
thinking: high
context_scope:
  [
    /codex/06-coding-standards/documentation-standards.md,
    /codex/00-SSOT-INDEX.md,
    /codex/06-coding-standards/model-tier-selection.md,
    /plans/archive/issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md,
    scripts/quality_gates/check_repo_docs_ssot.py,
  ]
---

# Codex-vs-repo-docs SSOT audit + consolidation

> **🟢 GATE-1 RULED 2026-07-28 (operator gate-clearance pass) — hold LIFTED, flipped back `NA → planning`.** The
> 2026-06-01 FIX-STALE-only hold is **LIFTED** for this plan: Option A of
> `/plans/archive/issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md` is the ruling — the
> deliberate 2026-07-27 `NA→planning` reclassification was the authorization signal, confirming it just removes the
> standing contradiction rather than creating a new risk. Phases 3/4 (REDIRECT/DELETE/slim APPLY, ~20 repos) may now
> proceed. **`model_tier` CORRECTED 2026-08-10 (plan_reconciler infra shard, agt-716973)**: `opus-required` →
> `sonnet-doable`, `execution_model: opus-1m` removed — this plan's sole surviving opus rationale ("cross-repo +
> governance judgment") was retired as an opus trigger 2026-08-04 (`model-tier-selection.md:256-259`); see "Execution
> model" below. **Mandate for whoever executes Phases 3/4**: full completion across every repo in the per-repo rollout
> list below — no partial/half-applied REDIRECT or DELETE passes, no repo skipped because it "looked fine last time."
> Once applied, update every per-repo registry note below that still says "Apply stays Phase-3/4 under the operator's
> FIX-STALE-only hold" — that phrase is now historical (describes the audit-time state, 2026-06-01 through 2026-07-27),
> not a current gate; leaving it unedited after Phase 3/4 land would itself become a stale contradiction of the kind
> this exact gate was created to catch.
>
> _Prior park (superseded by the ruling above, kept for history)_: 🅿️ PARKED `assigned_vm: NA` — 2026-07-28 (main
> agt-4d8de7). Flipped `planning → NA` to stop re-dispatch churn (slot-12 BLK-613a61ff, slot-16 before it) while GATE-1
> was pending (escalated: server block `BLK-d1b29089` + main SPLIT-DECISION). See the issue doc for the full history.

> **Goal**: `unified-trading-pm/codex/` is the single source of truth for all canonical / cross-cutting documentation.
> Every repo `docs/` folder is audited against it; duplicated content is removed and replaced with a link to the codex
> SSOT; genuinely repo-specific essentials stay (kept light); any unique info found only in a repo doc is migrated INTO
> codex first (never lost). End state: **zero documentation duplication between codex and repo docs.** Contract:
> `/codex/06-coding-standards/documentation-standards.md` **§ S5.11** (codified 2026-06-01).

## Execution model — **sonnet-doable** (corrected 2026-08-10)

**Run this plan on Sonnet 5, `thinking: high`.** Both qualitative opus rationales below are now RETIRED (corrected by
`plan_reconciler`, infra shard, agt-716973, 2026-08-10):

- ~~**Large working set**~~ — RETIRED 2026-07-26 (`/plan-reconcile`): Sonnet 5's 1M context window retires context SIZE
  as an opus-escalation reason (`model-tier-selection.md:36-38`).
- ~~**Cross-repo + governance judgment**: migrate/redirect/delete calls across 20 repos are Opus-grade, not Sonnet.~~
  RETIRED 2026-08-10 — `model-tier-selection.md:256-259`: "cross-repo architecture judgment... retired 2026-08-04... now
  classifies `sonnet-doable`." No qualitative trigger survives.
- **Sub-agents**: set `model` explicitly on every `Agent` call — `sonnet` (no longer opus).
- **Self-check**: confirm running model == Sonnet 5. Opus is no longer required or expected on this plan.

## Principles (operator, 2026-06-01)

1. **Codex is the SSOT.** Repo docs are updated to match codex — not the other way around.
2. **mtime safety check.** Before treating a repo doc as stale-and-duplicative, compare its git mtime / last-edit vs the
   corresponding codex doc. It is _very unlikely_ a repo doc holds newer canonical info while codex is empty — but
   verify to be safe. If a repo doc is genuinely newer AND carries info absent from codex → **migrate that delta into
   codex FIRST** (commit to codex), then slim the repo doc. Never delete unique info.
3. **Keep repo docs light.** Repo `docs/` carry only the minimum essential, repo-specific information. If canonical info
   is missing from codex, **add it to codex** (don't leave it duplicated in the repo doc).
4. **Redirect, don't duplicate.** A repo doc whose content is canonical becomes a thin redirect to the appropriate codex
   doc(s) (S5.11 redirect template — still substantive enough to clear the S5.4 stub gate). No content appears in both
   places.
5. **All active repos.** Every repo in the workspace with a `docs/` folder (or per-family doc dirs) is in scope.

## Method (per repo)

For each repo, run the loop:

1. **Inventory** — `find <repo> -name '*.md' -not -path '*/node_modules/*' -not -path '*/.venv*/*'` (includes per-family
   dirs like `features_service/*/docs/`). Record git mtime (`git log -1 --format=%cI -- <file>`) per doc.
2. **Classify** each doc against codex (consult `00-SSOT-INDEX.md` + the relevant `codex/<area>/` docs):
   - `KEEP-ESSENTIAL` — genuinely repo-specific, low/no codex overlap → keep, slim if bloated.
   - `REDIRECT` — content is canonical/duplicated → migrate any unique delta to codex, then convert to the S5.11
     redirect template.
   - `DELETE` — pure duplicate / dead one-off dump, zero unique value → migrate nothing, remove (git history =
     rollback).
   - `FIX-STALE` — correct shape but wrong literals (bucket names, hyphen partitions, retired names) → fix in place.
   - `MIGRATE-TO-CODEX` — repo doc is newer (mtime) and holds canonical info **missing** from codex → write/extend the
     codex doc first, then REDIRECT/DELETE the repo copy.
3. **mtime gate** (principle 2): for every REDIRECT/DELETE, confirm the repo doc is not the unique source of newer info.
   If unsure, diff against codex and migrate the delta before removing.
4. **Apply**: codex edits first (migrations) → then repo-doc redirects/deletes/fixes.
5. **Verify**: S5.7 doc-audit script passes (no missing/stub required docs); `rg` finds no codex table/contract
   duplicated in repo docs; all redirect links resolve to existing codex docs; repo builds.

## Contract (already codified — S5.11)

`pm/codex/` = SSOT for canonical/cross-cutting content. Repo `docs/` = repo-specific essentials + codex links; never
duplicate. Required docs (S5.1/2/3) whose content is entirely canonical collapse to the redirect template; non-required
pure-dups are deleted (after migrating unique deltas). Full per-doc-type split + redirect template:
`/codex/06-coding-standards/documentation-standards.md` § S5.11.

## Scope — all active repos with docs (20)

Service/library/infra (codex-overlap heavy → audit first): `deployment-service`, `unified-api-contracts`,
`market-data-processing-service`, `execution-service`, `instruments-service`, `market-tick-data-service`,
`strategy-service`, `unified-trading-library`, `e2e-testing`, `agent-orchestrator`, `deployment-api`,
`client-reporting-api`, `alerting-service`, `trading-agent-service`, `ibkr-gateway-infra`,
`batch-live-reconciliation-service`, `system-integration-tests`, `features-service` (per-family doc dirs). UI (mostly
UI-specific — audit only the data/path/contract docs, leave genuine UI docs): `unified-trading-system-ui`,
`deployment-ui` (`user-management-ui` ARCHIVED 2026-04-20 — corrected 2026-07-15, plan-reconcile: repo archival, drop
from scope).

> `unified-trading-pm` itself is NOT a target — it _is_ the codex/plans SSOT. Its `plans/*` are historical records (do
> not rewrite). Repo `issues/*` + `*_LOG-REVIEW.md` + vendored `context/codex|pm/*` mirrors are records/mirrors, not
> living docs — out of scope (mirrors re-sync from canonical codex).

## Phases

- **Phase 0 — already shipped (2026-06-01)**: S5.11 contract codified; read-only audit registry for 8 core repos +
  FIX-STALE pass-1 (~340 literal fixes across 9 repos on `live-defi-rollout`). Evidence + 8-repo registry + per-repo
  rollout list folded into **Appendix A** below (migrated 2026-06-01 from the now-archived
  `issues/repo_docs_codex_ssot_consolidation_2026_06_01.md`).
- [x] ✅ [DOCS] P0. **Phase 1 — audit-complete the remaining 12 repos** (read-only): agent-orchestrator, deployment-api,
      client-reporting-api, alerting-service, trading-agent-service, ibkr-gateway-infra,
      batch-live-reconciliation-service, system-integration-tests, deployment-ui (`user-management-ui` ARCHIVED
      2026-04-20, dropped — corrected 2026-07-15, plan-reconcile), unified-trading-system-ui (data/path docs only), +
      finish features-service audit. Produce the full per-doc registry (extend the pass-1 registry). **DONE 2026-07-27**
      — per-doc registry for all remaining repos in **Appendix B** below (read-only audit via 7 parallel opus
      sub-agents). Net: near-zero codex duplication (most repo docs are legitimately service-local); dominant
      remediation is a corpus-wide archived-mirror `unified-trading-codex/` → PM `/codex/` reference fix + FIX-STALE
      literals; 2 MIGRATE-TO-CODEX deltas (client-reporting-api commercial facts) + 2 operator-gated big findings
      captured as todos below.
- [x] ✅ [DOCS] P0. **Phase 2 — migrate unique deltas into codex.** For every MIGRATE-TO-CODEX doc (mtime-newer +
      codex-missing), write/extend the codex SSOT doc first. Commit codex changes. This must precede any
      REDIRECT/DELETE. **DONE 2026-07-27** — every DETERMINABLE migrate candidate is resolved (see "Phase 2 progress"
      below): the 3 AUDIT-03/gcs_hive candidates were verified no-op (codex already correct), and the deployment-service
      "marginal MIGRATE" SHARDING_AND_DATA_ALIGNMENT shard-atom taxonomy (sports `league_id`, prediction
      `canonical_question_group`, ML/strategy/execution `job_id`) was VERIFIED already present verbatim in
      `/codex/02-data/availability-manifest-and-data-status.md` (lines 53-67, 302-318) — no codex write needed. The ONE
      genuine remaining delta (client-reporting-api commercial facts) is OPERATOR-GATED and already tracked on its own
      separate `[OPERATOR-DECISION]` todo below — per CLAUDE.md "only operator-gated
      BLOCKED-CREDENTIALS/-OPERATOR-DECISION/-UPSTREAM-OUTAGE defer" + the dispatch-scope-eligibility ruling
      (2026-07-23: a non-determinable operator gate must not keep an otherwise-complete, worker-determinable phase open
      indefinitely / re-dispatching). Phase 3 (redirect + slim) can proceed on schedule.
- [x] [DOCS] P1. **Phase 3 — redirect + slim.** ✅ CANCELLED 2026-07-29 (main) — REDUNDANT: the per-repo satellite tasks
      (Appendix A/B; backlog `-004..-013`) own the combined Phase-3/4 apply per repo. Backlog task `-001` was already
      cancelled on this basis; this reconciles the plan so regen stops re-deriving it. Original scope kept for
      provenance: Convert REDIRECT docs to the S5.11 template; slim KEEP-ESSENTIAL docs to repo-local + codex links.
      Per-repo commit + push (PR where LDR is branch-protected — e.g. features-service). **✅ GATE CLEARED 2026-07-28
      (operator ruling, Option A of
      `/plans/archive/issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md`): the
      FIX-STALE-only hold is LIFTED — this REDIRECT/DELETE APPLY is cleared to execute.** Still opus-gated
      (redirect/slim editorial judgment must run on an opus sub-agent per this plan's "Execution model" section, not a
      default-tier worker delegating the call out) — that requirement is unchanged, only the hold itself lifted.
      Full-completion mandate: apply REDIRECT/slim across every repo in the per-repo rollout list (Appendix A/B) in this
      pass, not a partial subset; the mechanical FIX-STALE archived-mirror sweep (line ~519) was already DONE under the
      old hold and does not need repeating. SSOT for the ruling:
      `/plans/archive/issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md`.
- [x] [DOCS] P1. **Phase 4 — delete pure-dups.** ✅ CANCELLED 2026-07-29 (main, BLK-3b8233e0) — REDUNDANT with the
      per-repo satellite tasks (own combined Phase-3/4 apply); mirrors the `-001` cancellation. Also carried a LIVE
      same-file collision (all-repos delete of unified-trading-library `docs/specs/README.md` vs `-006` editing that
      repo on slot 9) and is opus-required (was dispatched to a Sonnet slot). Backlog task `-002` deleted. Original
      scope kept for provenance: Remove DELETE-class docs (migration already done in Phase 2). Update any `INDEX.md` /
      README doc-index links. **✅ Same gate-clearance as Phase 3 — DELETE-class apply is cleared to execute (2026-07-28
      operator ruling, Option A of
      `/plans/archive/issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md` — the same
      clearance as Phase 3 above).** Full-completion mandate applies here too: every DELETE-class doc identified in
      Appendix A/B, not a partial sweep.
- [x] ✅ [DOCS] P2. **Phase 5 — verify + enforce.** Run S5.7 audit per repo; add a QG/CI check that flags repo docs
      duplicating a codex table/contract (or hardcoding a resolver-owned literal); confirm all redirect links resolve.
      **DONE 2026-07-29 (slot-10) — unified-trading-pm@4558bcff8.** (1) **ENFORCE**: shipped
      `scripts/quality_gates/check_repo_docs_ssot.py` (+ unit test + `repo_docs_ssot_baseline.yaml`, 32 pre-existing
      seeded), wired into `scripts/quality-gates.sh` post-gates as a baselined shrinking ratchet (blocks on NEW drift
      only; needs `WORKSPACE_ROOT`, CI-noop when siblings absent — same shape as the codex-freshness gate). It walks
      every sibling repo's living docs (`docs/**/*.md` + root `README.md`; `unified-trading-pm` excluded — it IS the
      codex SSOT; `docs/archive/**` + vendored `.cursor/`/`.venv`/`node_modules` excluded) and flags the two
      deterministic drift classes the audit found dominant: `mirror-ref` (a repo doc pointing at the ARCHIVED
      `unified-trading-codex/` mirror instead of live PM `/codex/`, Appendix B's #1 remediation) and `hardcoded-literal`
      (a resolver-owned literal S5.6 bans — the real GCP project id, use `{project_id}`). The fuzzier "semantic
      codex-table duplication" detection is a follow-up (P3 todo below) — the S5.11/S5.6 literal+mirror-ref clause is
      what's deterministically enforceable without false positives. (2) **VERIFY — redirect links**: all S5.11 redirect
      docs' `../../unified-trading-pm/codex/…` links resolve (scanned every `Canonical SSOT`-bearing repo doc; zero
      broken). (3) **VERIFY — S5.7 required-docs audit**: ran per repo; 9/17 miss ≥1 required doc, but the gaps are
      mostly legitimately-absent (non-data-writing repos have no GCS/schema) — captured as a scoping finding in
      `/plans/active/issues/s5_7_required_docs_gaps_2026_07_29.md` (out of this dedup plan's scope; operator/main
      tiering decision).
- [x] ✅ [DOCS] P3. **Phase 5 follow-up — semantic codex-table-duplication detector.** `check_repo_docs_ssot.py`
      (Phase 5) enforces the deterministic clauses (archived-mirror refs + hardcoded resolver-owned literals) but does
      NOT yet detect a repo doc that reproduces a codex TABLE/contract verbatim (S5.11's core "no duplication" rule) — a
      verbatim-block detector is false-positive-prone (codex tables get legitimately quoted/referenced) and needs a
      calibrated heuristic. Design + add it as a third rule to `check_repo_docs_ssot.py`, baselined. (repo:
      unified-trading-pm) **DONE 2026-07-31 — unified-trading-pm@dc1c65c80.** Added the `table-duplication` rule:
      extracts markdown pipe-tables from BOTH the live codex corpus and each repo doc, canonicalizes cell content
      (whitespace/pipe-alignment-blind via a `\x1f` join, case-preserving, separator row dropped), and flags an EXACT
      whole-table match against a codex table that clears a significance floor (`_MIN_TABLE_ROWS=3` /
      `_MIN_TABLE_CHARS     =100`). The floor is the false-positive control the todo called out: calibrated against the
      live corpus (2358 codex tables) it drops the 88 trivial 2-row idiom-shaped tables that get legitimately echoed,
      while still indexing >2200 real tables. Exact-match (not fuzzy) keeps the FP rate at the same bar as the other two
      rules — a fuzzy pass is noted as future work in the docstring. Ratchets against the same
      `repo_docs_ssot_baseline.yaml`; live-corpus scan finds ZERO new table-duplication violations (baseline content
      unchanged — the codex/repo-doc corpus is already S5.11-clean on tables). +6 unit tests
      (flag/no-flag/floor/backward-compat/archived-codex-exclusion), full suite 13 green; QG-green sentinel==HEAD,
      quickmerge --agent, verified on origin.

## Phase 2 progress (2026-07-27)

Phase-1 audit (Appendix B) found the codex-migration surface is **tiny**: only `client-reporting-api` carries genuine
MIGRATE-TO-CODEX deltas (2 docs), and the 3 legacy AUDIT-03/gcs_hive codex-update candidates in Appendix A were all
either already-satisfied or stale. This session (Phase-2 worker) executed the **determinable** slice:

- **3 AUDIT-03/gcs_hive codex-migration candidates → resolved no-op** (flipped above with evidence): F-45 (codex never
  claims `correlation_id` is a path key — already `instance_id`-correct), gcs_hive (codex examples already canonical
  `key=value`), F-06 (recommendation stale — entity-governance SSOT already exists in
  `org-fund-client-entity-model.md` + `capital-structure-and-regulatory.md`; the remaining Elysium refs are the client
  POD, not the removed provider). **Zero codex writes were needed** — codex already holds the canonical content for all
  three.
- **2 genuine MIGRATE-TO-CODEX deltas (client-reporting-api commercial facts) → RULED 2026-07-28, cleared to migrate.**
  Confirmed codex-missing (`codex/14-customer-journeys/commercial-model/` has no client-roster/fee-tier/three-HWM SSOT)
  and source docs present (`CLIENT_OPERATIONS_GUIDE.md`, `PNL_AND_INVOICING_GUIDE.md`). These carry **real client IDs +
  per-client fee %s + org hierarchy** — the operator has now confirmed directly ("Yes, the client roster/fee numbers ARE
  still current. Confirmed, no re-check needed."), so the currency-gate that held this migration is resolved. Tracked on
  its OWN separate todo (line ~479 below) — it is not re-blocking the Phase-2 umbrella checkbox (closed 2026-07-27, see
  below); the migration target is `/codex/14-customer-journeys/commercial-model/` (new roster+fees SSOT) per that todo,
  now AO-dispatchable.
- **1 marginal-MIGRATE candidate → VERIFIED already-satisfied, no codex write needed (closes Phase 2, 2026-07-27).** The
  deployment-service refreshed registry (below) flagged `SHARDING_AND_DATA_ALIGNMENT.md`'s shard-atom taxonomy (sports
  `(league_id, day)`, prediction `(canonical_question_group, day)`, ML/strategy/execution `job_id` v7 column) as "worth
  folding into" `availability-manifest-and-data-status.md`. Direct grep confirms it is ALREADY there verbatim — the
  deployment-service doc's "Multi-axis correction (2026-05-06)" callout (lines 5-12) and the codex doc's identical
  callout (lines 53-67) match; `job_id`/`league_id`/`canonical_question_group` shard-atom semantics are documented at
  codex lines 65-67, 53-54, 58-60, 302-318 respectively. The deployment-service doc's own text already declares codex as
  the "Canonical SSOT for shard atoms + manifest semantics" (line 18) — the "marginal MIGRATE" framing in the prior
  audit pass was stale; this was already a REDIRECT-class doc, not a migrate source. With this, **every determinable
  Phase-2 migrate candidate across all 20 repos is resolved** — the umbrella checkbox above is flipped, leaving only the
  one already-separately-tracked operator-gated item open.

## Success criteria

- Every in-scope repo: `rg` finds no codex table/contract/path-template duplicated in its `docs/`; every required doc is
  either KEEP-ESSENTIAL (repo-specific) or an S5.11 redirect; no DELETE-class dumps remain.
- Zero unique info lost: every MIGRATE-TO-CODEX delta is in codex before its repo copy was removed (mtime-gated).
- S5.7 doc-audit passes for all service/library repos (no missing/stub required docs).
- All redirect links resolve to existing codex docs.

## Out of scope / guardrails

- No git surgery on shared/foreign branches (no cherry-pick/rebase-of-others/force-push/revert). If a repo's LDR is
  branch-protected or another agent is active, land via a clean PR or defer + flag — never untangle by hand.
- `unified-trading-pm/plans/*`, repo `issues/*`, `*_LOG-REVIEW.md`, vendored `context/*` mirrors: not rewritten.

---

## Appendix A — pass-1 evidence + 8-repo audit registry (migrated 2026-06-01 from archived issue)

> Folded here so PM stays SSOT after `issues/repo_docs_codex_ssot_consolidation_2026_06_01.md` was archived. The Phase
> 1–5 todos above are the live work breakdown; the per-repo rollout list below is the per-repo target inventory that
> feeds them. **Caveat**: audit agents proposed codex SSOT targets by grep — **verify each target exists before
> redirecting** (some proposed paths e.g. `/codex/05-infrastructure/gcs-lifecycle-policies.md`,
> `/codex/04-architecture/concurrency.md`, `/codex/02-data/bucket-naming-and-config.md` may need creating/remapping).

### Per-repo rollout (20 repos with docs/, ~520 docs) — ordered by codex-duplication likelihood

- [x] ✅ **market-tick-data-service** (31) — `GCS_PATHS.md` env-tiered + hive-canonical + codex pointer (mtds@9acbee1);
      remaining: DEPLOYMENT_GUIDE_FEMI/SHAHRIYAR delete-redirect (P1 below).
- [ ] [DOCS] P1. **market-tick-data-service finish**: `DEPLOYMENT_GUIDE_FEMI.md` (person-named onboarding dup) +
      `SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md` (infra-spec dup) → migrate unique delta, replace with redirect to
      `codex/05-infrastructure` + `codex/08-workflows`, delete the dumps. Slim `DEPENDENCIES.md` / `ARCHITECTURE.md`.
- [x] ✅ [DOCS] P0. **deployment-service** (79) — deploy-flow/infra/bucket/VM-tarball docs vs `codex/05-infrastructure`,
      `codex/08-workflows`. Highest duplication surface. **AUDIT DONE 2026-07-27** — refreshed per-doc registry (89
      repo-owned docs: 47 core + 42 infra/profiles/runbooks; excl. `docs/archive/*` 13 + vendored `.terraform` provider
      CHANGELOGs 10) in **Appendix B** below; SUPERSEDES the stale `deployment-service (~52)` entry in Appendix A. Net:
      12 DELETE (dead Feb/Mar-2026 impl-plan dumps + the `audit/` trio, not codex-dups) · 14 REDIRECT (all 12 codex
      targets VERIFIED-EXIST — none need creating) · systemic FIX-STALE = archived-mirror `unified-trading-codex/`
      links + a stale `POST_PLAN_BANNER_2026_05_06` replicated across ~30 files. **REDIRECT half ✅ SHIPPED**
      (`deployment-service@07ba33fc2`, verified ancestor of `origin/live-defi-rollout` 2026-08-06). **DELETE half ✅
      SHIPPED 2026-08-10** (`deployment-service@42ec7572`, verified ancestor of `origin/live-defi-rollout`) — the
      `audit/` trio was already gone; all 9 remaining core-doc DELETE items confirmed still live on disk before this
      commit (the earlier 2026-08-10 re-verify's "same 4 files" note undercounted — `IMPLEMENTATION_MAX_WORKERS`,
      `MAX_WORKERS_UNIFIED_IMPLEMENTATION_PLAN`, `UI_TYPESCRIPT_TYPES`, `GCS_LIFECYCLE_COST_OPTIMIZATION`,
      `docs/SPECS.md`, `docs/specs/README.md`, `CONFIGURATION`, `service-bundling-review` were also still present) and
      are now deleted, plus the now-empty `docs/specs/` dir removed and the dangling `IMPLEMENTATION_MAX_WORKERS` /
      `ML_IMPLEMENTATION` / `SPECS.md` links in `cli.md`/`BIGQUERY_INTEGRATION_GUIDE.md`/`INDEX.md` fixed. Phase-3/4
      hold itself LIFTED 2026-07-28 (GATE-1 banner above) — corrected 2026-08-06 (/plan-reconcile ao).
- [x] ✅ [DOCS] P0. **unified-api-contracts** (36) — **CLOSED 2026-08-10 (slot-24)**. All DEFERRED items resolved: (1) 4
      DELETE-class `docs/` twins already gone (verified absent; archive copies preserved). (2) SCHEMA_GOVERNANCE
      placement-table already accurate — all paths verified against live dirs (`canonical/domain/`,
      `canonical/crosscutting/`, `normalize_utils/`, `normalize_utils/errors/`, `canonical/crosscutting/errors/`,
      `registry/` all exist). (3) 3 mirror refs: `SCHEMA_CHANGELOG` L13 already points to PM codex
      `schema-versioning.md` (exists); `BATCH_LIVE_SYMMETRY` is now a REDIRECT (shipped
      `unified-api-contracts@f952e17f`); `UAC_FULL_GAP…` L278 `unified-trading-codex` → PM
      `/codex/04-architecture/batch-live-architecture.md` — **unified-api-contracts@e17837f01**. Phase-3/4 hold LIFTED
      2026-07-28 (GATE-1).
- [x] ✅ [DOCS] P0. **market-data-processing-service** (22→25) — path/manifest/candle docs vs `codex/02-data`. **AUDIT
      REFRESHED 2026-07-27** (registry in **Appendix B**): Appendix-A largely HOLDS but drifted — `GCS_PATHS.md` is NO
      LONGER un-tiered (edited 2026-07-21, now `{env}`-carrying; residual staleness is only inline `gs://`/`gsutil` vs
      `resolve_bucket_name`), and the count was undercounted 22→25
      (+`CONFIGURATION`/`ERROR_HANDLING`/`SCHEMA_VALIDATION` carry retired `{category}` vocab; +`specs/README` DELETE;
      +root `README` archived-mirror FIX-STALE). 5 DELETE · 7 FIX-STALE · 3 REDIRECT (all codex targets VERIFIED-EXIST)
      · no MIGRATE. **REDIRECT half SHIPPED** (`market-data-processing-service@0e9656c`, verified ancestor of
      `origin/live-defi-rollout` 2026-08-06) — DELETE/FIX-STALE halves not independently re-verified this pass;
      Phase-3/4 hold itself LIFTED 2026-07-28 (GATE-1) — corrected 2026-08-06 (/plan-reconcile ao).
- [x] ✅ [DOCS] P0. **execution-service** (20) — execution-arch/venue docs vs `codex/04-architecture`,
      `codex/02-venues`. **AUDIT VERIFIED + FIX-STALE APPLIED 2026-07-27** (Appendix-A `execution-service (20)` registry
      HOLDS, ground-truthed vs live code): pass-1 FIX-STALE already landed @`4b0ea42f` (ARCHITECTURE bucket literals
      env-tiered `execution-store-{ag}-{env}-{project_id}` ✓; README py3.13-canonical ✓). Applied the
      operator-hold-PERMITTED residual FIX-STALE only: 2 archived-mirror `unified-trading-codex/` refs → verified-live
      `../../unified-trading-pm/codex/` (`06-coding-standards/integration-testing-layers.md` in `docs/TESTING.md`;
      `08-workflows/t1-batch-dag.md` in `docs/GCS_PATHS.md` — both VERIFIED-EXIST) + 1 dangling deploy-spec ref (dead
      `docs/SHARDING_GUIDE.md`+`docs/SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md` → live `docs/DEPLOYMENT_GUIDE.md`, in
      `docs/`+`specs/BACKTEST_DEPLOYMENT.md`) — **execution-service@`0c6a93e1`** (QG-green sentinel c4fbb495).
      Sonnet-scoped mechanical sweep (plan §"Execution model" permits sonnet ONLY for FIX-STALE literal sweeps).
      **REDIRECT half ✅ SHIPPED** (`GCS_PATHS`/`ROUTING_MATRIX`/`CONFIGURATION`/`ERROR_HANDLING`/`DEPLOYMENT_GUIDE`,
      `execution-service@2a59ca09`, verified ancestor of `origin/live-defi-rollout` 2026-08-06). **DELETE half ✅
      SHIPPED 2026-08-10** (`execution-service@da81755e`, verified ancestor of `origin/live-defi-rollout`): deleted
      `docs/UNIFIED_BATCH_LIVE_ARCHITECTURE.md`, `docs/CLEAN_ALGORITHM_INTERFACE_DESIGN.md`,
      `docs/DEFI_INTEGRATION_TODO.md`, `specs/CLEAN_ALGORITHM_INTERFACE_DESIGN.md`, `specs/DEFI_INTEGRATION_TODO.md`
      (docs/+specs/ duplicates confirmed byte-identical; no live repo-wide refs to any of the 3 filenames). no MIGRATE
      (codex/04-architecture already holds the execution-arch SSOTs; codex/02-venues exists w/
      venue-registry-reference). Item now fully closed. Phase-3/4 hold itself LIFTED 2026-07-28 (GATE-1) — corrected
      2026-08-06 (/plan-reconcile ao).
- [x] ✅ [DOCS] P0. **instruments-service** (19→13) — IS→MTDS contract/path docs vs `codex/04-architecture`,
      `codex/02-data`. **AUDIT REFRESHED 2026-07-27** (read-only via opus sub-agent; registry in **Appendix B** below,
      SUPERSEDES the stale Appendix-A `(19)` entry). Repo drifted hard from Appendix-A: `specs/` dir GONE (consolidated
      into `ADAPTER_ARCHITECTURE` + 5 asset docs), `POLYMARKET_PREDICTION`→`PREDICTION_INSTRUMENTS`,
      `instrument-catalogue` gone. Net: duplication vs codex LOW (asset catalogs + adapter arch legitimately
      service-local); 2 DELETE · 6 FIX-STALE (README dead-repo/CLI/mirror drift is the big one) · no REDIRECT strictly
      required (nothing to ship on that axis) · no MIGRATE · no codex target needs creating. **Phase-3/4 hold itself
      LIFTED 2026-07-28 (GATE-1) — corrected 2026-08-06 (/plan-reconcile ao): "stays Phase-3/4" no longer describes a
      live operator block; whether the DELETE (2 items) + FIX-STALE (6 items) apply has actually shipped for this repo
      was not independently re-verified this pass.** BIG FINDING (determinable FIX-STALE, not operator-gated) captured
      in the registry: README front-door contradicts its two newer authoritative docs on the dependency graph.
- [ ] [DOCS] P1. **strategy-service** (15) — archetype/promote docs vs `codex/09-strategy`, `codex/04-architecture`.
- [x] ✅ [DOCS] P1. **unified-trading-library** (15) — events/cloud/bucket docs. **DONE 2026-07-29 (slot-9, opus
      sub-agent for editorial apply) — unified-trading-library@2737844b.** Ground-truth refresh REQUIRED and applied —
      the pass-1 Appendix-A registry OVER-classified (matches the e2e-testing/instruments-service refresh pattern): the
      4 "REDIRECT" docs `ERROR_HANDLING`/`PATTERNS`/`ID_NAMING_CONVENTIONS`/`CONFIGURATION` were ALREADY proper S5.11
      redirects (no-op). Net remediation: **9 FIX-STALE** — the dominant finding is a repo-rename drift
      (`unified-cloud-services`→`unified-trading-library`; package `unified_cloud_services`→`unified_trading_library`,
      verified against live pyproject/exports; `UnifiedCloudServicesConfig` kept as intentional legacy alias) across
      root `README`,
      `docs/{README,ARCHITECTURE,DEPENDENCIES,data-sink-validation,CLOUD_API_PATTERNS,TESTING,CLOUD_BUILD_TRIGGER_SETUP}`;
      plus removed 2026-05-06 `POST_PLAN` banners (10 docs), repointed/dropped archived-mirror `unified-trading-codex/`
      refs (README/ARCHITECTURE/TESTING), bare `pip`→`uv pip`; `CloudTarget` import corrected to verified path
      `unified_trading_library.domain_client`; dead Aster/Hyperliquid perps section removed (0 live defs); `DEV_SETUP`
      converted to S5.11 redirect. **2 DELETE**: `docs/specs/{README,PLANS_ALIGNMENT}.md` (dead plan-alignment dumps
      citing 5 archived plans — `PLANS_ALIGNMENT` was Appendix-A KEEP but reclassified DELETE to match the Appendix-B
      deployment-api/alerting-service treatment; `docs/specs/` dir removed). QG-green sentinel==HEAD (140s); quickmerge
      --agent. Reviewer caught + fixed 2 stray sub-agent artifact tags pre-ship.
- [x] ✅ [DOCS] P1. **e2e-testing** (21) — defi/sports/prediction runbooks vs `codex/08-workflows`, `codex/15-runbooks`.
      **DONE 2026-07-29 (slot-12, opus) — e2e-testing@7af2dd3** (+ PAPER_LIVE_CONVERGENCE redirect already landed
      @e00ee80, slot-10). **Ground-truth refresh REQUIRED and applied** — the pass-1 Appendix-A registry OVER-classified
      (see "e2e-testing refreshed registry (2026-07-29)" below): net remediation = 1 REDIRECT (PAPER_LIVE_CONVERGENCE,
      done) + light FIX-STALE/cross-links on 4 docs (E2E_PIPELINE_GUIDE `{category}`→`{asset_group}`;
      VM_BACKFILL_GUIDE + architecture gain codex cross-links, KEEP not REDIRECT; sports/ROADMAP expired-trial-dates
      annotated historical); **UI_DEMO_WALKTHROUGH reclassified DELETE→KEEP** (pass-1 "removed-provider creds" rationale
      was wrong: `demo`/`demo` creds + Elysium = the client POD, not the removed data provider). Dominant finding
      matches Appendix-B: e2e-testing docs are legitimately service-local, near-zero codex duplication. QG-green
      sentinel==HEAD; quickmerge --agent.
- [x] ✅ [DOCS] P3. **e2e-testing sports/ROADMAP epic-migration follow-up (from the 2026-07-29 refresh)**:
      `docs/sports/ROADMAP.md` is forward-looking sports planning content (expired trial windows now annotated
      historical) that belongs in a sports epic, not an e2e-testing repo doc. Migrate the roadmap content into the
      sports epic, then slim/redirect the repo copy. (repo: e2e-testing, unified-trading-pm) — **DONE 2026-08-02
      (slot-8)**: migrated the durable roadmap (vision / data-source layers / execution venues / phased plan / decision
      tree, expired trial content marked historical) into a condensed _"Sports arb-execution & live-trading roadmap"_
      section in `plans/epics/sports_master.md` (1509→1567 lines, under the 2000 cap); slimmed the repo copy to a
      redirect stub keeping only its repo-local sports script/doc file index. — e2e-testing@77e199d (ROADMAP stub) +
      unified-trading-pm (epic section + this flip).
- [x] ✅ [DOCS] P1. **agent-orchestrator** (10) — vs `codex/12-agent-workflow`, `codex/04-architecture`. — **RE-CLOSED
      2026-07-29 (slot-11, fresh audit against current single-VM/Path-B code) — agent-orchestrator@`3abe56c`**
      (FIX-STALE apply, shipped via `quickmerge --agent` by slot-12; this session ground-truth-verified the applied
      fixes are correct + complete, then flipped). The REOPENED fresh audit found the Appendix-B classification HOLDS:
      only 2 FIX-STALE docs, no DELETE/REDIRECT/MIGRATE. **`dashboard/API_REFERENCE.md`** — all retired `tab/<op>/N`
      branch literals repointed to `live-defi-rollout` (SlotView `branch` comment L53; the `/bootstrap` endpoint desc
      now describes Path-B `git clone --reference`-on-LDR clones, no tab branch; stdout/stderr examples + the
      branch-name convention note). **`docs/AUTH_INVENTORY.md`** — bare `agents/{worker,main}.md` →
      `unified-trading-pm/agents/…` (L161) + a re-verify banner on the 2026-05-19 prod-cutover/URL status (predates the
      2026-06-27 single-VM pivot; points to `/codex/04-architecture/runtime-deployment-topology.md`). Final sweep of
      both docs: **zero** un-annotated tab-branch literals, **zero** port-8026 refs, **zero** bare `agents/` paths,
      **zero** archived-mirror `unified-trading-codex/` refs, **zero** multi-vm refs. KEEP the rest (README rewritten
      2026-07-24 single-VM-aligned;
      ENV_VARS/REPO_PROVENANCE/SLOTS_AGENTS_AND_FLEET/WORKER_SPAWN_PREREQUISITES/BACKLOG_RELATIONS/DESIGN_* = repo-local
      impl SSOT cited BY `/codex/04-architecture/agent-orchestrator-overview.md`, fix-in-place not redirect). —
      **REOPENED 2026-07-24** (was marked SHIPPED `unified-trading-pm@c6b2d9eb1` 2026-06-22, but that verification
      predates the single-VM architecture pivot 2026-06-27 — a `[x]` from before a pivot reads as current coverage when
      it isn't). Concrete drift found on re-check: the "multi-vm-topology" doc + "multi-vm auth diagram" the 2026-06-22
      pass reconciled no longer exist under those names —
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` and
      `/codex/04-architecture/runtime-deployment-topology.md` are the current SSOTs (multi-VM dispatch deprecated
      2026-06-27; single central orchestrator VM + role-based dispatch replaced it). The "backlog-model / base-branch
      docs already-accurate" claim also needs re-checking against Path-B (per-slot `git clone --reference` on
      `live-defi-rollout`, no `tab/<op>/N` branch — the tab-branch model this audit pass may have verified against is
      itself RETIRED). Needs a fresh audit pass against current code before it can re-close. — **SHIPPED (superseded)
      `unified-trading-pm@c6b2d9eb1` 2026-06-22**: reconciled 5 codex docs against the live code as of that date
      (PlanRegenLoop cadence 6h→30min; AutoSpawn ceilings 50/80→95/95 + env-name fixes; backend port 8026→8765 across
      overview/worker-liveness/multi-vm-topology; ES256 internal-token + HS256-retired in the multi-vm auth diagram).
- [x] ✅ [DOCS] P2. **deployment-api** (8) / **client-reporting-api** (8) / **alerting-service** (8). — **DONE
      2026-07-31** (Phase-3/4 apply, gate cleared). Ground-truthed each repo vs the Appendix-B registry before applying;
      all cited codex targets VERIFIED-EXIST. **deployment-api@74785bf**: README un-archived (dropped the WRONG
      `unified-trading-deployment-v3 — ARCHIVED` banner — it IS the live deploy/launch+subscriptions backend for both
      UIs); TESTING → `scripts/quality-gates.sh` entrypoint (never-run-pytest); DEPLOYMENT_GUIDE `gcr.io/` → Artifact
      Registry; DELETE `docs/specs/{PLANS_ALIGNMENT,README}.md` (dead dumps, all 5 cited plans archived). (Adopted this
      slot's prior interrupted-session WIP that matched the registry exactly.) **client-reporting-api@93374e9**:
      GCS_PATHS rewritten — the `does not read/write GCS` claim was STALE (service is a live GCS reader/writer via
      `core/{hwm_reader,attribution_reader,ledger_views,invoice_state,recon_view}.py`, `resolve_bucket_name` kinds
      `client-statements`/`client-reports`; layout deferred to the CLIENT_OPERATIONS_GUIDE runbook + codex bucket/object
      SSOTs); TESTING → QG entrypoint; DEPLOYMENT_GUIDE `gcr.io/` → Artifact Registry (the MIGRATE-TO-CODEX
      commercial-facts deltas were already shipped 2026-07-29, see the Phase-1 todo above).
      **alerting-service@5d96dd2**: TESTING → QG entrypoint; DELETE `docs/specs/{PLANS_ALIGNMENT,README}.md` (dead
      dumps, all 5 cited plans archived). KEEP-class docs untouched. Each shipped Pass-1 QG-green →
      `quickmerge --agent`, verified on origin; all changed `.md` prettier-clean.
- [x] ✅ [DOCS] P2. **trading-agent-service** (7) / **ibkr-gateway-infra** (4) / **batch-live-reconciliation-service**
      (1) / **system-integration-tests** (1). — **DONE 2026-07-31 (slot-6, opus).** Ground-truthed each repo vs current
      code/docs before applying (registries drift). **trading-agent-service@a84fccc**: `docs/CONFIGURATION.md` 3 stale
      defaults fixed vs `config.py` (`data_refresh_seconds` 60→300, `fill_verify_seconds` 30→60 [registry missed this
      one — caught by full-table ground-truth], `min_signal_strength` 0.20→0.25; the doc was the outlier vs
      `SCHEMA_VALIDATION.md`+tests); `README.md` Key Dependencies replaced 3 NONEXISTENT packages
      (`unified-trade-execution-interface`/`unified-ml-interface`/`unified-domain-client` — not in pyproject/imports; a
      reader would import phantoms) with the 4 real path deps (`unified-api-contracts`/`unified-config-interface`/
      `unified-trading-library`/`unified-cloud-interface`, matching
      `DEPENDENCIES.md`+`ARCHITECTURE.md`+`pyproject.toml`) + linked `DEPENDENCIES.md`; archived-mirror refs already 0
      (b481cf9). **batch-live-reconciliation-service@529bee8**: `docs/GCS_PATHS.md` References gained the canonical
      recon SSOT (`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) — the determinism spine this
      service reconciles (KEEP content; archived-mirror already live-form). **system-integration-tests@dd34439**: README
      already fully remediated (verified 0 stale: manifest v9 not v5, `per-asset-group-bucket-layouts.md` not the
      missing per-category, live `operational-modes-matrix.md` path); `docs/portable-backtest-criteria.md` References
      gained the recon SSOT cross-link for its §3 Batch-Live Symmetry. **ibkr-gateway-infra**: NO worker-determinable
      FIX-STALE remains — archived-mirror ARCHITECTURE ref already fixed (2496fcb); the two remaining contradictions
      (`QUALITY_GATE_BYPASS_AUDIT.md` "Repo is archived" vs live README/coverage-floor; 2FA manual-vs-IBGA+TOTP) are
      exactly the `[OPERATOR-DECISION]` items already tracked below (Phase-1 findings, the ibkr internal-contradictions
      todo) — a strategy/owner call, not a worker guess; NOT re-filed. Each changed repo shipped Pass-1 QG-green →
      `quickmerge --agent`, verified on origin; changed `.md` prettier-clean.
- [x] ✅ [DOCS] P2. **deployment-ui** (3) (`user-management-ui` dropped — ARCHIVED 2026-04-20, corrected 2026-07-15,
      plan-reconcile). — deployment-ui@b7ccd3b (2026-07-31): DELETE `src/README.md` (stock Vite+React boilerplate);
      FIX-STALE `README.md` (env var `VITE_API_URL`→`VITE_DEPLOYMENT_API_URL` + `VITE_OAUTH_CLIENT_ID`→
      `VITE_GOOGLE_CLIENT_ID` to match actual code; stale 7-tab table → real 16-screen/7-group nav per
      `src/components/NavMenu.tsx`) + `docs/ARCHITECTURE.md` (stale "8-tab"/route table, component structure, endpoint
      list all reconciled to current source). Repo-internal drift only, no codex target. QG-green (55s), verified on
      origin.
- [x] ✅ [DOCS] P3. **unified-trading-system-ui** (152) — audit only data/path/contract docs; leave genuine UI docs. —
      unified-trading-system-ui@c0d28753: FIX-STALE repoint dart-v2-audit-context.md §10.1 broken
      `per-category-bucket-layouts.md` → `per-asset-group-bucket-layouts.md` + stale vocabulary `categories` →
      `asset groups`

### FIX-STALE pass-1 — landed 2026-06-01 (operator chose FIX-STALE-only; DELETEs/REDIRECTs held), ~340 fixes on LDR

deployment-service@`9627260`; instruments-service@`8bea654`+`9ecc4b2`; execution-service@`4b0ea42f`;
market-data-processing-service@`89161dc`; strategy-service@`80d298fe`; e2e-testing@`0de5471`;
unified-trading-library@`168e649`+`c88278b`; market-tick-data-service@`d97ca3c`.

- [x] ✅ [DOCS] P2. **No NEW URDI refs in instruments-service (was: "Audit + rename in instruments-service" — corrected
      2026-07-12, finding 369, §A2 "50 reclassified" blanket ruling)**: `urdi_reference_provider.py` is grep-confirmed
      LOAD-BEARING — imported by `instruments_service/engine/orchestrator/__init__.py` +
      `reference_data/utils/defi_utils.py` + 6 production adapters (cefi/hyperliquid.py, cefi/deribit_combo_adapter.py,
      cefi/tardis/adapter.py, prediction/kalshi.py, defi/aave_v3.py, tradfi/databento/adapter.py) — NOT a phantom name
      to rename away. `instruments_mtds_subset_consistency_remediation_2026_06_17.md` (line 1855-1857) independently
      reached the same correction 16 days later ("`rg URDI` → 0 hits is wrong; `urdi_reference_provider.py` is the LIVE
      fetch spine"). Guard going forward: no NEW URDI refs (grep-based CI guard), not a blanket rename of the existing
      load-bearing module. Original text preserved: "Follow-up: URDI still in instruments-service CODE — docs URDI refs
      fixed, but code still uses URDI symbols (`URDI` is a phantom name per CLAUDE.md). Audit + rename in
      instruments-service." (Note: `cursor-configs/CLAUDE.md`'s system-map "URDI phantom" note is also stale per this
      finding but is out of scope for this edit — not named in this chunk.) — **DONE 2026-07-31 (slot-6, opus).** The
      URDI-is-load-bearing ruling is applied everywhere: the forward guard ("no NEW URDI refs in docs") is already the
      workspace `cursor-configs/CLAUDE.md` system-map rule ("URDI is a live internal module — 'phantom' label retired
      2026-07-12"), and `instruments-service/docs/ADAPTER_ARCHITECTURE.md` already frames URDI correctly as the internal
      load-bearing `reference_data/urdi_reference_provider.py` fetch spine. Fixed the one standalone URDI-scoped stale
      ref — README flow step 1 cited `urdi_reference_provider.fetch(venue, date)` but the real public API
      (`engine/urdi_reference_provider.py:71`) is `fetch_instruments_for_all_venues(venues, ...)` → `VenueFetchResult`
      (**instruments-service@3357250e**). The README architecture-table URDI-as-external-repo ref (L118
      `unified-reference-data-interface/`) was NOT half-fixed here: it is one row of a 4-row Concern/Location table
      where every row carries the same BIG-FINDING error class (archived-mirror + 3 nonexistent dep repos), and one
      row's correct target (L119 sports) is not trivially determinable — so the whole table + broader README rewrite is
      tracked as the follow-up todo below rather than left inconsistent.
- [x] ✅ [DOCS] P2. **instruments-service README/docs holistic BIG-FINDING FIX-STALE (beyond URDI — findings-closure
      from -013, slot-6 2026-07-31)** — **DONE 2026-08-01 (slot-5), instruments-service@c5ece372.** Reconciled all 7
      docs against `SETUP_GUIDE.md`/`ADAPTER_ARCHITECTURE.md`/live `pyproject.toml`+CLI as ground truth: README dep-repo
      list fixed to the real editable siblings **UTL+UAC only** (3 nonexistent repos removed);
      `InstrumentRecord`/`InstrumentGenerator`/`MockScenario` repointed to UAC `internal/{reference,testing,modes}`;
      stale CLI (`--CEFI`…/`--redo-all`) → `--operation instruments --mode batch --asset-group …`/`--force`; 4 archived
      `unified-trading-codex/` mirror refs → live `codex/` paths; corrected the stale header claims (the service DOES
      make external calls + manages creds + canonicalises) and the removed service-local mock seed script (now
      UAC-owned). `CONTRIBUTING.md` → LDR + `quickmerge --agent` + `quality-gates.sh` flow (dead `.cursorrules`/
      `unified-trading-deployment-v2` refs dropped). `.github/BRANCH_PROTECTION.md` → `quality-gates-v2` + ratcheted
      `MIN_COVERAGE` (was 35/65). `docs/SETUP_GUIDE.md` `--mode instruments`/`instruments-query` →
      `--operation instruments     --mode batch` / `--operation status`. `docs/SPORTS_INSTRUMENTS.md`
      `features-sports-{project}` → canonical `features-sports-{env}-{project}` (VERIFIED stale vs codex
      bucket-isolation-model L178, not env-agnostic). DELETED `scripts/README.md` (documented only the nonexistent
      `run_quality_gates.py`) + `.github/BRANCH_PROTECTION_SETUP.md` (dead manual how-to). **Grep-then-READ
      correction**: the plan's "nonexistent `make ci-local`" note is WRONG — the `Makefile` + `make ci-local` target DO
      exist, but the Makefile is ITSELF stale (see follow-up P3 below), so BRANCH_PROTECTION.md now points at the
      canonical `scripts/quality-gates.sh` entrypoint instead. Original scope preserved below: the instruments-service
      refreshed registry below (line ~802) classified the full repo but only the URDI slice shipped; the rest is a
      determinable, NOT-operator-gated reconciliation that was never a standalone dispatchable todo. Reconcile
      `README.md` against `SETUP_GUIDE.md`@2026-07-24 + `ADAPTER_ARCHITECTURE.md` @2026-07-19 as ground truth: the
      Concern/Location table (L116-119) cites the ARCHIVED mirror `unified-trading-codex/02-data/` (→ live PM
      `/codex/02-data/`) + 3 NONEXISTENT dep repos (`unified-internal-contracts`/UIC,
      `unified-reference-data-interface`/URDI [→ internal `reference_data/adapters/`],
      `unified-sports-reference-interface`) — actual editable siblings = UTL + UAC only; `InstrumentRecord`/
      `InstrumentGenerator`/`INSTRUMENTS_SCHEMA` live in UAC `.../internal/reference/`, not UIC; stale CLI
      `--CEFI/--TRADFI/--DEFI/--SPORTS`+`--redo-all` → real `--asset-group CEFI`+`--force`. Plus `CONTRIBUTING.md` +
      `.github/BRANCH_PROTECTION.md` FIX-STALE (retired `git checkout main`/`python -m pytest`/`quality-gates` check →
      `quality-gates-v2`, LDR flow), `docs/SETUP_GUIDE.md` `--mode instruments` →
      `--operation instruments --mode batch`, `docs/SPORTS_INSTRUMENTS.md` `gs://features-sports-{project}/` env-tier
      verify; + 2 DELETEs (`scripts/README.md` documenting only a non-existent `run_quality_gates.py`;
      `.github/BRANCH_PROTECTION_SETUP.md` dead manual how-to). All cited codex/UAC targets VERIFIED-EXIST (registry
      Verification notes, line ~792). Opus-gated editorial rewrite. (repo: instruments-service)
- [x] ✅ [CODE] P3. **instruments-service `Makefile` FIX-STALE** — instruments-service@563af797 (repoint) +
      instruments-service@d775054b (unrelated flaky-test fix surfaced en route). Repointed `ci-local`/`lint`/
      `type-check`/`test`/`lint-fix` to shell out to `bash scripts/quality-gates.sh` (`--lint`/`--test`/
      `QG_SLICE=typecheck` respectively) instead of calling `pytest`/`ruff`/`basedpyright`/`pip` directly; dropped the
      stale `--cov-fail-under=35` (real floor is `MIN_COVERAGE=88` in `scripts/quality-gates.sh`). Confirmed via grep no
      other repo doc/script referenced the old `make ci-local`/`make test` targets. Full-suite QG re-gate hit a
      pre-existing, unrelated intermittent failure
      (`test_orchestrator_sports_pipeline.py::     TestGwFalseEmptyWritePath20260714::test_skip_as_present_league_not_demoted_to_empty`)
      only reproducible under `--cov` instrumentation — root cause: the test never mocked `read_availability_index`/
      `_read_per_league_entity_df`, so it made a REAL unmocked GCS call that pytest-socket's `--allow-hosts` blocked,
      which the code's fail-safe `except Exception` path (correctly) treats as "cannot prove captured status" and skips
      empty-gap emission — nondeterministic because whether the real network attempt reaches the blocked-socket layer
      before another safe short-circuit fires is timing-dependent. Fixed by mocking both call sites (matching the
      pattern already used elsewhere in the same test file) in both affected tests
      (`test_skip_as_present_league_not_demoted_to_empty` +
      `test_presence_guard_protects_present_parquet_under_redo_all`); verified green across 3 consecutive full-suite
      runs post-fix before shipping. Surfaced while fixing `.github/BRANCH_PROTECTION.md` (which no longer cites
      `make ci-local`). (repo: instruments-service)
- [x] ✅ [DOCS] P2. **AUDIT-03 F-45 codex update** — VERIFIED already-correct 2026-07-27 (Phase-2), no codex change
      needed. `rg` across `codex/` finds NO doc claiming `correlation_id` keys/partitions the events GCS path; every
      `correlation_id` reference is a column / PubSub attribute / function param (matches the code). Original finding
      (from `archive/issues/audit03_ikenna_review_routing_2026_05_22.md`): "code wins — events GCS path keys on
      `instance_id`; `correlation_id` is a column, NOT a path key." Codex already reflects `instance_id` path semantics
      — nothing to migrate.
- [x] ✅ [DOCS] P2. **AUDIT-03 F-06** — RESOLVED as a stale finding 2026-07-27 (Phase-2), no codex change needed (the
      2026-05-22 recommendation is itself obsolete). (a) Entity-governance SSOT ALREADY exists and must NOT be grafted
      onto custody-providers.md: `/codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md`
      (`authoritative_for: org/fund/client… entity model`) +
      `/codex/04-architecture/capital-structure-and-regulatory.md`
      (`authoritative_for: per-category custody, regulatory posture, and onboarding structure`) already own the entities
      incl. Odum UK/Cayman; `/codex/04-architecture/custody-providers.md` is
      `authoritative_for: custody provider     protocol` only — declaring it a second entity SSOT would VIOLATE this
      plan's no-duplicate-SSOT principle. (b) The remaining `Elysium` codex refs are the **client POD**
      (`elysium-managed-sla`, `pod-elysium-client-onboarding`), NOT the removed data provider — custody-providers.md's
      sole Elysium ref is a legit link to the client-pod onboarding doc. Nothing to scrub.
- [x] ✅ [DOCS] P2. **gcs_hive partition-path doc FIX-STALE** — VERIFIED already-canonical 2026-07-27 (Phase-2), no
      codex change needed. Sampled the codex hive-partition path examples
      (`/codex/02-data/sports-data-source-coverage-matrix.md`, `sports-data-types-catalog.md`, et al.); all use
      canonical `key=value` segments (`by_date/day=…/entity=…/league=…`, `data_type=odds`). No malformed non-`key=value`
      example survives in codex. (Operator note preserved from
      `archive/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`: doc-fix only; the GCS DATA
      remediation stays operator-deferred and is out of scope here.)
- **Parked — features-service**: another agent active; LDR branch-protected. Docs commit `b9b4103e` on
  `origin/tab/hk/10`; PR #4 bundles a foreign commit (`603c2b9c`) — do NOT merge as-is. Left for the owning agent; no
  git surgery.

### 8-repo read-only audit registry (DELETE / FIX-STALE / REDIRECT / KEEP)

**deployment-service (~52)** — DELETE: MASTER_ML_IMPLEMENTATION_PLAN, ML_IMPLEMENTATION, MASTER_IMPLEMENTATION_INDEX,
GCS_LIFECYCLE_AGGRESSIVE_STRATEGY, GCS_LIFECYCLE_COST_OPTIMIZATION, BIGQUERY_INTEGRATION_GUIDE,
MAX_WORKERS_UNIFIED_IMPLEMENTATION_PLAN, IMPLEMENTATION_MAX_WORKERS, RESOURCE_MONITORING_AND_RIGHTSIZING, SPECS,
UI_TYPESCRIPT_TYPES, specs/PLANS_ALIGNMENT, specs/README, archive/\*. FIX-STALE: TESTING, setup, INFRASTRUCTURE,
local-dev/local-run-guide, INDEX, README. REDIRECT: COST, HARDENING, MIGRATION, CLOUD_AGNOSTIC_MIGRATION, RUNBOOKS,
GCS_PATHS, SCHEMA_VALIDATION, GCS_AND_SCHEMA, CACHE_AND_STATE, LIVE_MODE, CLOUD_BUILD_SUCCESS_CHECKLIST,
GITHUB_TOKEN_CLOUD_BUILD, STANDARDIZED_EVENT_LOGGING, COMPREHENSIVE_SERVICE_AUDIT_FRAMEWORK, E2E_SPECS, UI_SPEC. KEEP:
SHARDING_AND_DATA_ALIGNMENT, VM_HEALTH_AND_GCSFUSE_OPTIMIZATION, hybrid-live-seam, dev-environment, CONFIGURATION,
ARCHITECTURE, DEPLOYMENT_GUIDE, cli, service-bundling-review, resource-profiles/\*.

**unified-api-contracts (36)** — FIX-STALE: SCHEMA_GOVERNANCE (deleted `canonical/normalize/`+`schemas/`), MOCKS_AND_VCR
(old cassette path), SCHEMA_CHANGELOG (deleted flat modules). DELETE: ICLOUD_REPO_MIGRATION_PROMPT,
SCHEMA_NORMALIZATION_GAPS_AUDIT, UAC_FULL_GAP_ANALYSIS_AND_BATCH_LIVE_SYMMETRY, VIX_LIVE_RESEARCH. REDIRECT:
PACKAGE_LAYOUT_AND_SCOPE, BATCH_LIVE_SYMMETRY, canonical-instrument-ids. KEEP: README, ARCHITECTURE, SCHEMA_AUDIT_MATRIX
(generated), TESTING, archive/\*.

**market-data-processing-service (22)** — FIX-STALE: DEPLOYMENT_GUIDE_FEMI (un-tiered + hyphen partitions), GCS_PATHS
(un-tiered), DEPENDENCIES (`{category}` vocab + un-tiered). DELETE: REFACTORING_STANDARDS_COMPLIANCE,
specs/PLANS_ALIGNMENT, DEPLOYMENT_GUIDE (stub), TESTING (stub). REDIRECT: SCHEMA_VALIDATION_AND_TIMEFRAME_SUFFIXING_E2E,
UNIFIED_SCHEMA_AND_CLIENT_USAGE_GUIDE, TIMEFRAME_AGGREGATION_SPECIFICATION.

**execution-service (20)** — DELETE: UNIFIED_BATCH_LIVE_ARCHITECTURE (deleted codex file),
CLEAN_ALGORITHM_INTERFACE_DESIGN, DEFI_INTEGRATION_TODO. FIX-STALE: ARCHITECTURE (split execution-store-\* bucket
literals), README (py3.11 vs 3.13), BACKTEST_DEPLOYMENT (SHAHRIYAR spec). REDIRECT: GCS_PATHS, ROUTING_MATRIX,
CONFIGURATION, ERROR_HANDLING, DEPLOYMENT_GUIDE. KEEP: TESTING, SCHEMA_VALIDATION, BACKTEST_QUICKSTART, DEPENDENCIES,
TROUBLESHOOTING, TRADE_ANALYTICS_INTEGRATION, VISUALIZER_QUICKSTART, specs/\*.

**instruments-service (19)** — FIX-STALE: instrument-catalogue (un-tiered + URDI + `category=`), README (URDI ×9).
DELETE: specs/CLOUD_OPERATIONS, specs/COMMAND_FLOW_ANALYSIS, specs/COMMAND_FLOW_DIAGRAM (dead
`unified-trading-services`), specs/CORPORATE_ACTIONS, specs/SETUP_GUIDE, specs/TEST_ALIGNMENT. REDIRECT:
specs/MVP_INSTRUMENTS, specs/SECRETS_SETUP, specs/INSTRUMENT_SPECIFICATION. KEEP:
{CEFI,DEFI,TRADFI,SPORTS}\_INSTRUMENTS, POLYMARKET_PREDICTION, ARCHITECTURE.

**unified-trading-library (15)** — FIX-STALE: CLOUD_API_PATTERNS (`client.bucket()` anti-pattern), README
(`setup_cloud_logging` + pip). REDIRECT: ERROR_HANDLING, ARCHITECTURE, PATTERNS, ID_NAMING_CONVENTIONS, DEPENDENCIES,
CONFIGURATION, DEV_SETUP, data-sink-validation. DELETE: specs/README (stub). KEEP: TESTING, CLOUD_BUILD_TRIGGER_SETUP,
UTL_ADOPTION_MATRIX, README, specs/PLANS_ALIGNMENT.

**strategy-service (15)** — FIX-STALE/REDIRECT: STRATEGY_MODES (retired `basis-strategy-v1` + dead links), CLI_REFERENCE
(`batch only` violates batch=live). DELETE: BACKTEST_ENGINE (dup). REDIRECT: BACKTESTS, ARCHITECTURE, GCS_PATHS. KEEP:
archetype_registry_discovery, DEPLOYMENT_GUIDE, CONFIGURATION, CONFIG_SCHEMA, SCHEMA_VALIDATION, DEPENDENCIES, TESTING,
ERROR_HANDLING, specs/\*, README.

**e2e-testing (21)** — DELETE: defi/UI_DEMO_WALKTHROUGH (Elysium/removed-provider creds). FIX-STALE: VM_BACKFILL_GUIDE
(missing lifecycle_class + gsutil), sports/ROADMAP (past trial dates → migrate to epic). REDIRECT:
defi/PAPER_LIVE_CONVERGENCE, E2E_PIPELINE_GUIDE, architecture. KEEP: sports/LIVE_ODDS_PROVIDERS, \*/progress, \*/issues,
coverage-matrix, \*/per-strategy-acceptance, \*/smoke-test-baseline.

---

## Appendix B — Phase 1 remaining-12-repo read-only audit registry (2026-07-27)

> Read-only audit of the remaining repos via 7 parallel opus sub-agents (`.claude/*` symlinks to
> `unified-trading-pm/cursor-configs/` excluded as vendored mirrors in every repo; `issues/*`, generated test artifacts,
> and `docs/archive/*` excluded per method). **Headline: near-zero codex DUPLICATION** — almost every living repo doc is
> legitimately service-local; the dominant issue is stale codex _references_ (pointing at the archived
> `unified-trading-codex/` mirror instead of PM `/codex/`) + FIX-STALE literals, not content that duplicates codex. Only
> `client-reporting-api` carries genuine MIGRATE-TO-CODEX deltas.

**agent-orchestrator (10 living; 32 total incl. 16 test fixtures, 4 generated, 2 symlinks)** — FIX-STALE:
`API_REFERENCE.md` (RETIRED tab-branch literals `tab/hk/4` / `tab/<op>/<slot>` at L53/294/313/323/625 +
`/api/slots/{id}/bootstrap` "each on branch tab/…" — slots commit directly on `live-defi-rollout`), `AUTH_INVENTORY.md`
(prod-cutover status stale + retired `agents/worker.md`/`main.md` paths, now under `unified-trading-pm/agents/`). KEEP:
`README.md` (freshly rewritten 2026-07-24, fully single-VM aligned — the REOPENED-audit README fix ALREADY LANDED),
`ENV_VARS.md`, `REPO_PROVENANCE.md`, `SLOTS_AGENTS_AND_FLEET.md`, `WORKER_SPAWN_PREREQUISITES.md`,
`BACKLOG_RELATIONS_UX_BRIEF.md`, `DESIGN_BRIEF.md`, `DESIGN_HANDOFF.md`. NO DELETE/REDIRECT/MIGRATE — repo-local impl
refs are cited BY `/codex/04-architecture/agent-orchestrator-overview.md` as the repo-local detail SSOT (KEEP +
fix-in-place, not redirect). No port-8026 refs anywhere (all 8765). `DESIGN_BRIEF`/`DESIGN_HANDOFF` (2026-05-19) are
archival candidates if the redesign is complete.

**deployment-api (10)** — DELETE: `docs/specs/PLANS_ALIGNMENT.md` + `docs/specs/README.md` (dead plan-alignment dumps;
all 5 referenced plans archived; cite deprecated `event-logging.mdc`). FIX-STALE: `README.md` (WRONG "…v3 — ARCHIVED, do
not use" banner though this IS the live deploy/launch backend for both UIs — owner rewrite, not a one-liner),
`docs/TESTING.md` (`pytest tests/` direct → violates never-run-pytest QG rule), `docs/DEPLOYMENT_GUIDE.md` (`gcr.io/`
Container Registry deprecated vs Artifact Registry). KEEP: `QUALITY_GATE_BYPASS_AUDIT.md`,
`docs/{CONFIGURATION,ARCHITECTURE,SCHEMA_VALIDATION,GCS_PATHS}.md` (thin repo-specific stubs). NO REDIRECT/MIGRATE.

**client-reporting-api (10)** — FIX-STALE: `docs/GCS_PATHS.md` ("does not read/write GCS" is stale — newer
`CLIENT_OPERATIONS_GUIDE` documents live GCS persistence), `docs/TESTING.md` (`pytest -n auto` direct),
`docs/DEPLOYMENT_GUIDE.md` (`gcr.io/` deprecated). **MIGRATE-TO-CODEX**: `docs/PNL_AND_INVOICING_GUIDE.md` (three-HWM
operational model TWR/Notional/PnL-recovery + exact field names + per-client fee numbers — NOT in codex),
`docs/CLIENT_OPERATIONS_GUIDE.md` (full client roster w/ real client IDs + fee tiers + org hierarchy +
onboarding/backfill/Cloud-Run-jobs runbook — NOT in codex). KEEP: `README.md`, `QUALITY_GATE_BYPASS_AUDIT.md`,
`docs/{CONFIGURATION,ARCHITECTURE,SCHEMA_VALIDATION}.md`. NO DELETE/REDIRECT. **⚠️ BIG FINDING (see Phase-2 todos
below).**

**alerting-service (10)** — DELETE: `docs/specs/PLANS_ALIGNMENT.md` + `docs/specs/README.md` (stale snapshots; all 5
mapped plans archived; cite retired cursor `.mdc` rules). FIX-STALE: `docs/TESTING.md` (`pytest tests/` +
`.venv activate` vs QG rule; low-pri). KEEP: `README.md` (notes standalone codex archived→PM SSOT),
`docs/{ARCHITECTURE,CONFIGURATION,GCS_PATHS,SCHEMA_VALIDATION,DEPLOYMENT_GUIDE}.md`, `QUALITY_GATE_BYPASS_AUDIT.md`. NO
REDIRECT/MIGRATE.

**trading-agent-service (10)** — FIX-STALE: `README.md` (stale archived-mirror codex ref →
`/codex/04-architecture/tier-and-import-architecture.md`; ALSO "Key Dependencies" list contradicts
`DEPENDENCIES.md`/`ARCHITECTURE.md` interface names — a reader could import the wrong ones), `docs/CONFIGURATION.md`
(`min_signal_strength` 0.20 vs 0.25 elsewhere; `data_refresh` 60 vs 300 — CONFIGURATION is the outlier),
`QUALITY_GATE_BYPASS_AUDIT.md` (stale archived-mirror SSOT ref). KEEP:
`docs/{ARCHITECTURE,DEPENDENCIES,DEPLOYMENT_GUIDE,GCS_PATHS,SCHEMA_VALIDATION,TESTING}.md`,
`.coverage-floor-exception.md`. NO REDIRECT/MIGRATE.

**ibkr-gateway-infra (8 living)** — FIX-STALE: `QUALITY_GATE_BYPASS_AUDIT.md` (says repo "archived" — contradicts newer
`.coverage-floor-exception.md`@2026-06-01 live 51% floor + active README), `ibkr-gateway/FIRST_TIME_LOGIN.md` (documents
manual IB-Key 2FA fallback as canonical — contradicts README/ARCHITECTURE IBGA+TOTP "no human 2FA"),
`docs/DEPLOYMENT_GUIDE.md` (Step 3 "interactive credential entry" contradicts README "fully automated"),
`docs/ARCHITECTURE.md` (broken archived-mirror ref). KEEP: `README.md`, `docs/LOCAL_DOCKER_GATEWAY.md`,
`docs/FULLY_AUTOMATED_2FA_OPTIONS.md`, `.coverage-floor-exception.md`. No codex SSOT for IBKR gateway → nothing to
REDIRECT/MIGRATE. **⚠️ BIG FINDING (see Phase-2 todos below).**

**batch-live-reconciliation-service (2 living)** — FIX-STALE: `docs/GCS_PATHS.md` (KEEP content — repo-specific
`t1-recon/recon/` layout not in codex — but its `## References` points to an archived-mirror path that no longer exists;
recon SSOT is `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`). KEEP:
`QUALITY_GATE_BYPASS_AUDIT.md`. NO DELETE/REDIRECT/MIGRATE.

**system-integration-tests (4 living)** — FIX-STALE: `README.md` (KEEP content — SIT scope table/env/coverage-matrix — 3
stale literals: "manifest v5 schema" [codex is v9 since 2026-05-30]; cites MISSING
`/codex/02-data/per-asset-group-bucket-layouts.md` [actual: `/codex/02-data/per-asset-group-bucket-layouts.md`];
archived-mirror operational-modes-matrix ref [actual:
`/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`]), `docs/portable-backtest-criteria.md`
(KEEP content — archived-mirror ref → `/codex/06-coding-standards/integration-testing-layers.md`; §3 overlaps
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — cross-link, not merge). KEEP:
`QUALITY_GATE_BYPASS_AUDIT.md`, `.coverage-floor-exception.md`. NO DELETE/REDIRECT/MIGRATE.

**deployment-ui (8 audited)** — DELETE: `src/README.md` (stock Vite+React template boilerplate). FIX-STALE:
`README.md` + `docs/ARCHITECTURE.md` (repo-internal drift only — env-var name inconsistency `VITE_API_URL` vs
`VITE_DEPLOYMENT_API_URL`, tab-count 7 vs 8; no codex target). KEEP: `docs/{ARCHITECTURE,DEPLOYMENT_GUIDE,TESTING}.md`,
`README.md`, `public/design-mocks/README.md` (self-deleting marker), `QUALITY_GATE_BYPASS_AUDIT.md`,
`src/docs/consolidators-help.md` (in-app help, VERIFIED codex-consistent w/
`/codex/05-infrastructure/manifest-consolidator-ssot.md`). NO REDIRECT/MIGRATE — all deploy-flow docs legitimately
UI-repo-local.

**features-service (121 md; ~88 audit-scope after excluding 33 `delta_one/docs/archive/*` + noise)** — DELETE:
`{volatility,sports}/docs/specs/PLANS_ALIGNMENT.md` (list RETIRED plan names as live) +
`{volatility,sports}/docs/specs/README.md`. FIX-STALE + REDIRECT: the 8 `*/docs/GCS_PATHS.md`
(non-canonical/inconsistent bucket literals — placeholder `my-features-bucket`, non-canonical
`sports_features/`/`features-mtf/` prefixes, timestamped filenames vs canonical `by_date/day`, missing `{env}` tier,
`{category}`→asset_group legacy note) → trim to redirect to `/codex/05-infrastructure/bucket-isolation-model.md` +
`/codex/05-infrastructure/gcs-object-operations.md`. REDIRECT: 8 `*/docs/SCHEMA_VALIDATION.md` (SSOT = UAC feature
schemas; describe not define → redirect-header). KEEP: `README.md` + per-family
`docs/{ARCHITECTURE,CONFIGURATION,DEPENDENCIES,DEPLOYMENT_GUIDE,TESTING,ERROR_HANDLING}` (~48 service-local dev docs),
`delta_one/docs/*` + `cross_instrument/FEATURE_SPECIFICATION` + `volatility/TRADFI_VOL_SURFACES` +
`sports/docs/specs/{features_improvements,halftime_data_architecture}` family specs, coverage/changelog artifacts.
OUT-OF-SCOPE: `delta_one/docs/archive/*` (33). NO MIGRATE. Duplication vs codex LOW; `POST_PLAN_BANNER_2026_05_06_FINAL`
targets `/codex/POST_PLAN_REALITY_2026_05_06.md` which STILL EXISTS (not broken).

**unified-trading-system-ui (data/path/contract subset: 1 actionable of ~292 non-vendored; 558 total)** — FIX-STALE:
`docs/audits/dart-v2-audit-context.md` (§10.1 cites MISSING `/codex/02-data/per-asset-group-bucket-layouts.md`; layout
SSOT is `/codex/05-infrastructure/bucket-isolation-model.md` → repoint). KEEP:
`docs/audits/{backend-feature-requests,dart-v2-audit-context,global-filters-v2}.md`,
`docs/trading/platform-review/tabs/03-positions.md`, strategy widget filter/color config,
`widget-certification-deferred-questions.md`. NO DELETE/REDIRECT/MIGRATE. Scanned all 292 non-vendored; ~8 real
data/path candidates, 7 genuine UI-consumption. No doc duplicates codex GCS-bucket structure / canonical-path templates
/ manifest v9 / `capture_status` / `pipeline_mode`. Rest (widget/typography/a11y/UX/audit-scripts/routing/UI-deploy)
genuine-UI, out of scope.

### Phase-1 cross-cutting findings → Phase 2+ tracked todos

- [x] ✅ [DOCS] P1. **Corpus-wide archived-mirror reference fix (dominant Phase-1 remediation)**: multiple repos
      (`trading-agent-service`, `ibkr-gateway-infra`, `batch-live-reconciliation-service`, `system-integration-tests`,
      `agent-orchestrator/AUTH_INVENTORY.md`) carry stale codex refs pointing at the archived `unified-trading-codex/`
      mirror; SSOT is now PM `/codex/`. Grep each repo's `docs/` for `unified-trading-codex/` and repoint to the live
      `/codex/…` equivalent (this is FIX-STALE, feeds Phase 3). (repo: all listed) — **DONE 2026-07-27** (sonnet-scoped
      mechanical FIX-STALE literal sweep, plan §"Execution model" permits sonnet for FIX-STALE literal sweeps; operator
      hold PERMITS FIX-STALE, per BLK-d1b29089 split-decision answer). Grepped `*.md` docs (excl. vendored `.claude/*`
      mirrors + `docs/archive/*`) in all 5 named repos for `unified-trading-codex/`: **3 refs fixed across 2 repos** —
      `trading-agent-service` (`README.md` `TIER-ARCHITECTURE.md`→`tier-and-import-architecture.md` +
      `QUALITY_GATE_BYPASS_AUDIT.md` SSOT ref; both repointed to `../unified-trading-pm/codex/…`) **@`b481cf9`** and
      `ibkr-gateway-infra` (`docs/ARCHITECTURE.md`
      `vcr-cassette-ownership.md`→`../../unified-trading-pm/codex/02-data/…`) **@`2496fcb`**, both landed on LDR via
      QG-green + `quickmerge --agent`. The other 3 named repos carry **ZERO** remaining archived-mirror
      `unified-trading-codex/` refs in their `.md` docs: `batch-live-reconciliation-service` (`docs/GCS_PATHS.md`) +
      `system-integration-tests` (`README.md`, `docs/portable-backtest-criteria.md`) already use the live
      `unified-trading-pm/codex/…` form; `agent-orchestrator` has none in `.md` docs. NOTE:
      `agent-orchestrator/AUTH_INVENTORY.md`'s staleness (retired `agents/worker.md`/`main.md` PATHS — now under
      `unified-trading-pm/agents/`) is a **separate non-archived-mirror FIX-STALE** tracked in the Appendix-B
      agent-orchestrator entry, NOT this `unified-trading-codex/`-repoint todo's scope.
- [x] ✅ [DOCS] P1. **client-reporting-api commercial-facts migration into codex — RULED, cleared to execute (operator
      confirmed 2026-07-28: "Yes, the client roster/fee numbers ARE still current. Confirmed, no re-check needed.").**
      The committed client roster + org hierarchy + per-client trader/Odum/introducer fee %s + three-HWM invoicing model
      live ONLY in `client-reporting-api/docs/{CLIENT_OPERATIONS_GUIDE,PNL_AND_INVOICING_GUIDE}.md`, NOT in
      `/codex/14-customer-journeys/commercial-model/` — directly undercuts CLAUDE.md's "grep codex before asking the
      operator for committed numbers." Migration target = `/codex/14-customer-journeys/commercial-model/` (new
      roster+fees SSOT), with `client-reporting-architecture.md` cross-referencing it; the onboarding/backfill/Cloud-Run
      runbook portion stays repo-local (must gain `owner/cadence/verifier/last_executed` runbook frontmatter).
      `CLIENT_OPERATIONS_GUIDE.md` also hardcodes real project id `central-element-323112` (L378) — a `{project_id}`
      placeholder violation to fix on migration. Full-completion mandate: migrate the commercial facts into codex FIRST
      (this plan's own Principle 2 — never lose the delta), then convert the repo docs to S5.11 redirects; no partial
      migration that leaves half the commercial facts still repo-local-only. (repo: client-reporting-api,
      unified-trading-pm) — **DONE 2026-07-29.** Migrated ALL commercial facts (roster + orgs + tranches + pooled IK
      weights + per-client Odum/trader/introducer fee %s + four-tier HWM model + three HWM methods + per-client HWM
      seeds/GP-pnl_based/nuances + committed Apr-9 invoice + refund history) into the new codex SSOT
      `/codex/14-customer-journeys/commercial-model/client-roster-and-fee-model.md` FIRST (never-lose-the-delta),
      verified against the live machine SSOT `execution-service/configs/credentials-registry.yaml` (all fee %s + pool
      weights + underwater flags match). Cross-referenced from `client-reporting-architecture.md` (pipeline-vs-numbers
      split) + listed in the commercial-model README. THEN converted both repo docs to S5.11 redirect form keeping only
      the repo-local ops runbook + code-file map, added `owner/cadence/verifier/last_executed` runbook frontmatter, and
      replaced hardcoded `central-element-323112` with `{project_id}`. unified-trading-pm@codex-doc-commit +
      client-reporting-api@77b2d54 (quickmerge, landed LDR). Doc gates: prettier-clean, doc-body-links clean, my refs
      add 0 danglers.
- [ ] [DOCS] P2. **[OPERATOR-DECISION] ibkr-gateway-infra internal contradictions (⚠️ ground-truth needed)**: the repo
      contradicts itself on (a) archived-vs-live status (`QUALITY_GATE_BYPASS_AUDIT.md` says archived;
      README/docs/coverage-floor treat it as live) and (b) 2FA automation (README/ARCHITECTURE claim IBGA+TOTP "no human
      2FA"; `DEPLOYMENT_GUIDE`/`FIRST_TIME_LOGIN` describe manual GUI/IB-Key login). Needs an operator/owner call on the
      repo's actual status + the canonical 2FA path before the FIX-STALE rewrite can land. (repo: ibkr-gateway-infra)
      **⏸ PARKED 2026-07-31 (main, Option A of BLK-273ddfda — false prereq `ibkr-owner-decision-made`, priority:999):**
      dispatch-scope mismatch — this is an owner decision, not worker/main-determinable, so it was churning through
      workers. Ground-truth captured for the owner (slot-6, so the eventual rewrite need not re-derive it): (a)
      **STATUS** — every objective signal says LIVE (active README describing a live deployed gateway;
      actively-maintained `.coverage-floor-exception.md` @2026-03-08, floor 51% / actual 52.38%; on `live-defi-rollout`;
      active workspace scope); the lone dissent is `QUALITY_GATE_BYPASS_AUDIT.md` L7 "Repo is archived", which reads
      STALE — but status was deliberately owner-gated (an intent to wind IBKR down would not be visible in code), so NOT
      overridden. (b) **2FA** — the README already reconciles the layering (`docker-compose.ibga.yml` IBGA
      fully-automated TOTP = primary L62; `docker-compose.yml` gnzsnz manual 2FA = fallback L63; `DEPLOYMENT_GUIDE` Step
      3 frames GUI login as First-Time / One-Time); the one residual is whether the IBGA path is truly zero-touch or
      still needs that one-time GUI bootstrap (`DEPLOYMENT_GUIDE` L58/L189 + `FIRST_TIME_LOGIN.md` say a first-login IS
      required on first start / re-provision). **UNPARK**: owner answers (a)+(b) → set `ibkr-owner-decision-made=true`,
      restore priority 50 + `priority_override:     false`, reload → apply the FIX-STALE rewrite reconciling all 4 ibkr
      docs per their call. Do NOT proceed before that.

### deployment-service refreshed registry (2026-07-27) — supersedes the stale Appendix-A `(~52)` entry

> Read-only re-audit of the highest-duplication repo via 2 parallel opus sub-agents (core docs +
> infra/profiles/runbooks). 89 repo-owned docs (47 core + 42 infra/profiles/runbooks); OUT-OF-SCOPE: `docs/archive/*`
> (13), vendored `terraform/**/.terraform/providers/*` provider CHANGELOGs (10). **REDIRECT half SHIPPED**
> (`deployment-service@07ba33fc2`, verified ancestor of `origin/live-defi-rollout` 2026-08-06; live `docs/GCS_PATHS.md`
> etc. confirmed converted to S5.11 "Canonical SSOT:" redirect stubs) — **DELETE half NOT shipped**
> (`docs/{MASTER_ML_IMPLEMENTATION_PLAN,ML_IMPLEMENTATION,MASTER_IMPLEMENTATION_INDEX}.md` +
> `docs/specs/PLANS_ALIGNMENT.md` still live on disk, re-verified 2026-08-06); the Phase-3/4 hold itself LIFTED
> 2026-07-28 (GATE-1 banner above) — corrected 2026-08-06 (/plan-reconcile ao). This entry is the classification the
> phases consume. All REDIRECT targets VERIFIED-EXIST in current PM `/codex/` — none need creating.

**deployment-service [core docs] (47)** — DELETE: `IMPLEMENTATION_MAX_WORKERS`, `MASTER_IMPLEMENTATION_INDEX`,
`MAX_WORKERS_UNIFIED_IMPLEMENTATION_PLAN`, `MASTER_ML_IMPLEMENTATION_PLAN`, `ML_IMPLEMENTATION` (dead Feb-2026 "ready to
implement" dumps, ~6.7k lines), `UI_TYPESCRIPT_TYPES`, `GCS_LIFECYCLE_COST_OPTIMIZATION` (dup of AGGRESSIVE_STRATEGY),
`docs/SPECS.md` (historical contractor spec dump), `docs/specs/{PLANS_ALIGNMENT,README}` (archived 2026-05-06 plans),
`CONFIGURATION` (near-empty stub), `service-bundling-review` (completed 2026-03 one-off). FIX-STALE: `CONTRIBUTING`
(mis-titled "Contributing to Instruments Service"; prescribes retired `git checkout main`/`python -m pytest`/plain
quickmerge), `INDEX` (links ARCHIVED `unified-trading-codex/` mirror + broken targets), `MIGRATION` (archived 2026-05-06
plans as "active" + archived-mirror), `LIVE_MODE` (archived-mirror batch-live-symmetry ref), `HARDENING` (broken
BIGQUERY_HIVE ref), `CLOUD_BUILD_SUCCESS_CHECKLIST` (retired merge-to-main-triggers-CloudBuild vs LDR→main + qg-v2).
REDIRECT (targets exist): `docs/ARCHITECTURE` (→ `/codex/05-infrastructure/deployment-clusters-live-vs-batch.md`),
`GCS_PATHS` (→ `/codex/05-infrastructure/path-registry.md`), `SCHEMA_VALIDATION` + `GCS_AND_SCHEMA` (→
`/codex/02-data/availability-manifest-and-data-status.md`), `DEPLOYMENT_GUIDE` (→
`/codex/05-infrastructure/vm-tarball-deployment.md`), `CLOUD_AGNOSTIC_MIGRATION` (→
`/codex/05-infrastructure/cloud-agnostic-script-pattern.md`), `INFRASTRUCTURE` (→
`/codex/05-infrastructure/auth-setup.md`), `COST` (→ `/codex/05-infrastructure/billing-cost-observability.md`),
`GCS_LIFECYCLE_AGGRESSIVE_STRATEGY` (→ `/codex/05-infrastructure/gcs-lifecycle-policies.md`), `GITHUB_TOKEN_CLOUD_BUILD`
(→ `/codex/05-infrastructure/cicd-setup.md`), `UI_SPEC` (→ `/codex/05-infrastructure/deployment-ui-architecture.md`),
`COMPREHENSIVE_SERVICE_AUDIT_FRAMEWORK` (→ `/codex/11-project-management/` citadel standards). KEEP: root
`{README,ARCHITECTURE,QUALITY_GATE_BYPASS_AUDIT}`, `RUNBOOKS`, `hybrid-live-seam`, `cli`, `SHARDING_AND_DATA_ALIGNMENT`,
`STANDARDIZED_EVENT_LOGGING`, `TESTING`, `BIGQUERY_INTEGRATION_GUIDE`, `RESOURCE_MONITORING_AND_RIGHTSIZING`,
`VM_HEALTH_AND_GCSFUSE_OPTIMIZATION`, `CACHE_AND_STATE`, `E2E_SPECS`, `setup`, `dev-environment`, `local-run-guide`,
`CLI_REFERENCE_TEMPLATE`. ~~Marginal MIGRATE: `SHARDING_AND_DATA_ALIGNMENT` shard-atom taxonomy…~~ **RESOLVED no-op
2026-07-27 (Phase-2): VERIFIED already present verbatim** in `/codex/02-data/availability-manifest-and-data-status.md` —
the shard-atom taxonomy (sports `(league_id,day)` codex L53-54/302-327, prediction `(canonical_question_group,day)`
codex L58-60/302-318, v7 `job_id` col codex L65-67/521-529) matches the deployment-service doc's own "Multi-axis
correction (2026-05-06)" callout, and that doc already declares codex the "Canonical SSOT for shard atoms + manifest
semantics" (L18). Not a migrate source — a REDIRECT-class doc for Phase 3. No codex write.

**deployment-service [infra/profiles/runbooks] (42)** — DELETE:
`audit/{CURRENT_AUDIT,ARCHIVE,DEPLOYMENT_SPLIT_AUDIT_REPORT}.md` (the whole `audit/` dir — stale 2026-03 point-in-time
snapshots, resolved P0s / completed migration). FIX-STALE: `resource-profiles/*` (all 22 carry
`POST_PLAN_BANNER_2026_05_06` w/ a wrong-depth `../`-relative link + refs to archived May plans; `execution-service.md`
uses stale `.plan` ext), `terraform/README.md` + `terraform/modules/README.md` (broken `unified-trading-codex/` refs —
mirror archived/gone), `configs/RUNTIME_TOPOLOGY_DECISIONS.md` (broken archived-mirror refs + Feb-dated gap tables),
`templates/branch-protection-template.md` (names `quality-gates` — actual `quality-gates-v2`; cites nonexistent
`make ci-local`). REDIRECT: `templates/branch-protection-template.md` (→ `/codex/08-workflows/ci-cd-flow.md`),
`configs/RUNTIME_TOPOLOGY_DECISIONS.md` (redirect-with-migration →
`/codex/04-architecture/runtime-deployment-topology.md`). KEEP: `resource-profiles/*` (22 — repo-specific
CPU/mem/timeout/cost/VM-override per service incl. COINBASE c2-standard-60; content KEEP, only the banner is stale),
`scripts/{vm,recovery,cloud-run}/README.md`, `configs/{README,BUCKET_CONFIG_SCHEMA}.md`,
`packer/agent-orchestrator/README.md`, `deployment_service/backends/README.md`, `terraform/{README,modules/README}.md`
(KEEP content, fix refs), `infra/ibkr-gateway/FIRST_TIME_LOGIN.md`. **Runbooks: 4/4 FULLY frontmatter-compliant**
(`owner`/`cadence`/`verifier`/`last_executed`; two staging runbooks carry `last_executed: never` but the field is
present).

### market-data-processing-service refreshed registry (2026-07-27) — supersedes the Appendix-A `(22)` entry

> Read-only re-audit verifying the initial-pass classification against current repo docs + codex. Count corrected 22→25.
> All REDIRECT targets VERIFIED-EXIST. **REDIRECT half SHIPPED** (`market-data-processing-service@0e9656c`, verified
> ancestor of `origin/live-defi-rollout` 2026-08-06; live `docs/TIMEFRAME_AGGREGATION_SPECIFICATION.md` confirmed
> converted to an S5.11 "Canonical SSOT:" redirect stub) — DELETE/FIX-STALE halves not independently re-verified this
> pass; the Phase-3/4 hold itself LIFTED 2026-07-28 (GATE-1) — corrected 2026-08-06 (/plan-reconcile ao).

**market-data-processing-service (25)** — DELETE: `DEPLOYMENT_GUIDE.md` (stub → FEMI), `TESTING.md` (stub, `pytest`
direct → TESTING_GUIDE), `REFACTORING_STANDARDS_COMPLIANCE.md` (one-off + archived-mirror refs),
`specs/PLANS_ALIGNMENT.md` + `specs/README.md` (stale plan map — archived plans). FIX-STALE: `DEPENDENCIES.md`
(`{category}` vocab + `gs://market-data-tick-{category}`), `DEPLOYMENT_GUIDE_FEMI.md` (`{category}` + hyphen partition
`day-{date}/`; its `{env}` bucket refs ARE tiered), `CONFIGURATION.md` (`{category}` + un-tiered processed bucket),
`ERROR_HANDLING.md` (`category="CEFI"` arg), `SCHEMA_VALIDATION.md` (`category` schema-column "spot/perp/future" retired
vocab), `GCS_PATHS.md` (inline `gs://`/`gsutil ls` vs `resolve_bucket_name` — NO LONGER un-tiered, now `{env}`-carrying
since 2026-07-21), root `README.md` (archived-mirror ref). REDIRECT (targets exist):
`TIMEFRAME_AGGREGATION_SPECIFICATION.md` (→ `/codex/02-data/bar-boundary-candle-edge-convention.md` +
`/codex/02-data/mdps-candle-canonical-reconciliation.md`), `SCHEMA_VALIDATION_AND_TIMEFRAME_SUFFIXING_E2E.md` (→
`/codex/02-data/schema-governance.md` + `/codex/02-data/canonical-schema-groups.md`),
`UNIFIED_SCHEMA_AND_CLIENT_USAGE_GUIDE.md` (→ `/codex/02-data/canonical-schema-groups.md`). KEEP: `ARCHITECTURE.md`,
`HFT_FEATURES_TIER1_ADDITIONS.md`, `batch_processing/NAN_HANDLING_DESIGN_SPECIFICATION.md`, `SETUP_GUIDE.md`,
`USAGE_GUIDE.md`, `TESTING_GUIDE.md`, `VERIFICATION_GUIDE.md`, `CONTRIBUTING.md`, `QUALITY_GATE_BYPASS_AUDIT.md`,
`docs/README.md`. No MIGRATE (candle-edge/schema material codex needs already lives in the REDIRECT targets).
`TIMEFRAME_AGGREGATION`'s `resample(closed='right', label='right')` is ALIGNED with the codex right/close-edge
convention (genuine duplication → REDIRECT, not FIX-STALE).

### instruments-service refreshed registry (2026-07-27) — supersedes the stale Appendix-A `(19)` entry

> Read-only re-audit via opus sub-agent (`.claude/*` symlink mirrors, `.pytest_cache/`, `.git/` excluded as
> vendored/generated). 13 repo-owned docs. The Appendix-A `(19)` entry is FULLY superseded — its `specs/` dir,
> `instrument-catalogue`, and `POLYMARKET_PREDICTION` no longer exist (consolidated into `docs/ADAPTER_ARCHITECTURE.md`
>
> - the 5 per-asset-group `*_INSTRUMENTS.md` docs). All cited REDIRECT/repoint targets VERIFIED-EXIST — none need
>   creating. **Phase-3/4 hold itself LIFTED 2026-07-28 (GATE-1) — corrected 2026-08-06 (/plan-reconcile ao): "stays
>   Phase-3/4" no longer describes a live operator block; whether apply (deletes/fixes; no REDIRECT class exists for
>   this repo) has shipped was not independently re-verified this pass.**

**instruments-service (13)** — DELETE: `scripts/README.md` (documents ONLY a non-existent `run_quality_gates.py`; cites
retired `../unified-cloud-services` monorepo + stale 65% coverage [actual 88] + `GH_PAT`-in-`.env` flow; zero index
value — never lists the ~90 real scripts), `.github/BRANCH_PROTECTION_SETUP.md` (dead manual GitHub-clicks how-to,
superseded by centralized ruleset/template rollout from PM per CLAUDE "branch protection = ruleset + classic BOTH";
names retired `quality-gates` check + 65% coverage). FIX-STALE: `README.md` (HEAVY — 4 archived-mirror
`unified-trading-codex/` refs [L35/116/123/124]; cites 3 NON-EXISTENT dep repos
`unified-internal-contracts`/`unified-reference-data-interface`/`unified-sports-reference-interface` [actual siblings =
UTL+UAC only]; attributes `InstrumentRecord`/`InstrumentGenerator`/`MockScenario` to "UIC" though they live in UAC
`.../internal/reference/`; stale CLI `--CEFI/--TRADFI/--DEFI/--SPORTS`+`--redo-all` vs real
`--asset-group CEFI`+`--force`; `urdi_reference_provider.fetch(venue,date)` vs real
`fetch_instruments_for_all_venues()`), `CONTRIBUTING.md` (retired `git checkout/pull/push origin main`,
`python -m pytest`, plain `quickmerge "msg"` [no `--agent`/`--files`], PR-auto-merge-to-main [no LDR],
branch-protection-on-main, dead `.cursorrules`/`unified-trading-deployment-v2/` refs), `.github/BRANCH_PROTECTION.md`
(required check `quality-gates` → actual `quality-gates-v2`; nonexistent `make ci-local`; coverage 35%/65% → actual 88;
1-approval model), `docs/SETUP_GUIDE.md` (CLI examples `--mode instruments`/`--mode instruments-query` [L38/476/477] use
`--mode` as an OPERATION name — violates the CLI-convention SSOT; real form `--operation instruments --mode batch`),
`docs/SPORTS_INSTRUMENTS.md` (LOW-CONFIDENCE — `gs://features-sports-{project}/` [L432/501-502] lacks the `{env}` tier
its siblings carry; verify vs codex before treating as stale — may be a legit folded env-agnostic bucket). REDIRECT:
none strictly required (`CONTRIBUTING.md` + `.github/BRANCH_PROTECTION.md` are REDIRECT-eligible →
`/codex/08-workflows/ci-cd-flow.md`, but classified FIX-STALE to match the deployment-service
`CONTRIBUTING`/branch-protection-template precedent; owner's Phase-3 call). MIGRATE-TO-CODEX: none. KEEP-ESSENTIAL:
`QUALITY_GATE_BYPASS_AUDIT.md`, `docs/ADAPTER_ARCHITECTURE.md`, `docs/{CEFI,DEFI,PREDICTION,TRADFI}_INSTRUMENTS.md`, +
`docs/SETUP_GUIDE.md`/`docs/SPORTS_INSTRUMENTS.md` (KEEP content, fix the one literal each above) — all rich, current,
repo-specific (per-asset-group instrument-type catalogs + real GCS audit findings + module map / 8-stage command flow /
canonical-id current-vs-target spec), correctly citing LIVE PM `/codex/` + UAC ownership. **Net: duplication LOW;
dominant remediation FIX-STALE (README dep/CLI/mirror drift) + 2 DELETEs; no MIGRATE; no codex target needs creating for
confirmed items.**

Verification notes (all cited targets ground-truthed):

- `/codex/08-workflows/ci-cd-flow.md`, `/codex/06-coding-standards/quality-gates.md`,
  `/codex/06-coding-standards/cli-convention.md` — **VERIFIED-EXIST** (CONTRIBUTING/BRANCH_PROTECTION repoint;
  scripts/README's real QG replacement; SETUP_GUIDE `--mode` fix authority).
- README L35 `unified-trading-/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` →
  `/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` — **VERIFIED-EXIST** (note the
  `architecture-v2/` path drift). L116/L123 `unified-trading-codex/{02-data,06-coding-standards}/` → live `/codex/…`
  dirs — **VERIFIED-EXIST**. L124 `unified-trading-codex/09-strategy/defi/` — **NEEDS-MANUAL-PICK** (no 1:1 live target;
  `/codex/09-strategy/defi/` absent — closest live SSOTs `/codex/04-architecture/defi-execution-overview.md` or
  `/codex/02-data/defi-canonical-naming-ssot.md`; Phase-3 editorial choice, NOT a codex create).
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
  `/codex/04-architecture/instrument-universe-registry-consolidation.md` — **VERIFIED-EXIST** (already cited correctly
  by `ADAPTER_ARCHITECTURE`; no change needed).
- **URDI (plan finding 369) — CONFIRMED not a doc-staleness problem**: `ADAPTER_ARCHITECTURE.md` (L54-58) +
  `TRADFI_INSTRUMENTS.md` (L75) describe URDI correctly as the load-bearing internal
  `reference_data`/`urdi_reference_provider.py` module, aligned with codex. No URDI doc rename recommended (README's
  URDI staleness is only its framing of URDI-as-external-repo, folded into the README FIX-STALE).
- Code-truth false-positives avoided: `unified_api_contracts.canonical.canonical_mappings` (SETUP_GUIDE L282) STILL
  EXISTS (the plan's "canonical/ deleted" note was specifically `canonical/normalize/`); PREDICTION `category=` (L98) is
  a live Kalshi API query param, not retired partition vocab.
- **BIG FINDING (determinable FIX-STALE → Phase-3, owner-routed, not operator-gated)**: `instruments-service/README.md`
  (mtime 2026-07-03) — the repo front-door — contradicts its two newer authoritative docs (`SETUP_GUIDE.md`@2026-07-24,
  `ADAPTER_ARCHITECTURE.md`@2026-07-19) and live `pyproject.toml` on the dependency graph: it tells a reader IS depends
  on / imports from `unified-internal-contracts`, `unified-reference-data-interface`,
  `unified-sports-reference-interface` — none of which exist in the workspace (actual editable siblings = UTL + UAC
  only). A reader following README would import nonexistent packages. The Phase-3 README rewrite must cite
  `SETUP_GUIDE`/`ADAPTER_ARCHITECTURE` as the reconciliation ground truth.

### e2e-testing refreshed registry (2026-07-29) — supersedes the stale Appendix-A `(21)` entry

> Ground-truth re-audit (slot-12, opus) of the actionable docs the Appendix-A pass-1 entry named. Applied + shipped:
> **e2e-testing@7af2dd3** (PAPER_LIVE_CONVERGENCE redirect already landed @e00ee80, slot-10). Headline matches
> Appendix-B: e2e-testing docs are **legitimately service-local — near-zero codex duplication**; the pass-1
> DELETE/REDIRECT calls OVER-classified genuine operational content. All cited codex targets VERIFIED-EXIST.

**e2e-testing (21)** — REDIRECT: `docs/defi/PAPER_LIVE_CONVERGENCE.md` (→ S5.11 redirect to
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`, keeps DeFi-specific seams; DONE @e00ee80).
FIX-STALE / cross-link (KEEP content): `docs/E2E_PIPELINE_GUIDE.md` (`{category}`→`{asset_group}` log-path literal;
otherwise repo-specific run-guide, edited 2026-07-16), `docs/VM_BACKFILL_GUIDE.md` (cross-link →
`/codex/05-infrastructure/vm-launcher-runbook.md` + `spot-vms-for-backfill.md`; buckets already tiered-canonical, gsutil
lines are human-inspection only), `docs/architecture.md` (cross-link → the batch=live determinism-spine SSOT; the rest
is e2e-specific "laptop is the cloud" local-run topology — KEEP not REDIRECT), `docs/sports/ROADMAP.md` (expired
`~2026-04-03` trial dates annotated historical + STALE banner; epic-migration tracked as a P3 follow-up todo).
**RECLASSIFIED DELETE→KEEP**: `docs/defi/UI_DEMO_WALKTHROUGH.md` — pass-1 "Elysium/removed-provider creds" rationale is
ground-truth WRONG (`demo`/`demo` login + `patrick@bankelysium.com` = the Elysium **client POD**, not the removed data
provider; it is a genuine 846-line DeFi UI UAT walkthrough). KEEP (unchanged): the rest (`*/progress`, `*/issues`,
`coverage-matrix`, `*/per-strategy-acceptance`, `*/smoke-test-baseline`, `LIVE_ODDS_PROVIDERS`, scripts READMEs). No
MIGRATE-TO-CODEX; no codex target needs creating.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped the superseded consolidation issue for
  the Phase-5 enforcement checker `check_repo_docs_ssot.py`, this plan's own real deliverable, since prior scope was
  codex/plan-only.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
