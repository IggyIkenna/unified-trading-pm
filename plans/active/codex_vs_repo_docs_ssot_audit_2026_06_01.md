---
name: codex_vs_repo_docs_ssot_audit
title: "Codex-vs-repo-docs SSOT audit + consolidation (all active repos)"
parent_epic: plan_hygiene_master
assigned_vm: vm-ml
created: 2026-06-01
author: harsh + claude (session 67c17024)
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
status: active
locked_by: live-defi-rollout
model_tier: opus-required
execution_model: opus-1m
thinking: high
source:
  - unified-trading-pm/codex/06-coding-standards/documentation-standards.md
  - unified-trading-pm/codex/00-SSOT-INDEX.md
  - unified-trading-pm/plans/active/issues/repo_docs_codex_ssot_consolidation_2026_06_01.md
---

# Codex-vs-repo-docs SSOT audit + consolidation

> **Goal**: `unified-trading-pm/codex/` is the single source of truth for all canonical / cross-cutting documentation.
> Every repo `docs/` folder is audited against it; duplicated content is removed and replaced with a link to the codex
> SSOT; genuinely repo-specific essentials stay (kept light); any unique info found only in a repo doc is migrated INTO
> codex first (never lost). End state: **zero documentation duplication between codex and repo docs.** Contract:
> `codex/06-coding-standards/documentation-standards.md` **§ S5.11** (codified 2026-06-01).

## Execution model — **opus-1m** (suggested)

**Run this plan on `claude-opus` with the 1M-token context window (`opus-1m`), `thinking: high`.** Rationale (per
`codex/06-coding-standards/model-tier-selection.md`, this is `opus-required`, not `sonnet-doable`):

- **Large working set**: each repo's consolidation requires holding the relevant slice of the **800-doc codex corpus** +
  the repo's **full `docs/` tree** in context simultaneously to decide, per doc, "is this canonical content that already
  lives in codex doc X, or a genuine repo-specific delta?" — a 200k window forces lossy chunking and mis-classification.
- **Cross-repo + governance judgment**: migrate-vs-redirect-vs-delete + "migrate unique delta into codex" are
  irreversible-ish editorial calls across 20 repos. This is cross-cutting architecture/governance work — Opus-grade
  reasoning, not Sonnet.
- **Sub-agents**: per-repo audit/consolidation may fan out to sub-agents; those `Agent` calls MUST set `model`
  explicitly (`opus` for the migrate/redirect judgment passes; `sonnet` acceptable only for the mechanical FIX-STALE
  literal sweeps).
- **Self-check at task start** (mandatory per model-tier rule): confirm running model == `opus-1m`. Sonnet on this plan
  → STOP.

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
`codex/06-coding-standards/documentation-standards.md` § S5.11.

## Scope — all active repos with docs (20)

Service/library/infra (codex-overlap heavy → audit first): `deployment-service`, `unified-api-contracts`,
`market-data-processing-service`, `execution-service`, `instruments-service`, `market-tick-data-service`,
`strategy-service`, `unified-trading-library`, `e2e-testing`, `agent-orchestrator`, `deployment-api`,
`client-reporting-api`, `alerting-service`, `trading-agent-service`, `ibkr-gateway-infra`,
`batch-live-reconciliation-service`, `system-integration-tests`, `features-service` (per-family doc dirs). UI (mostly
UI-specific — audit only the data/path/contract docs, leave genuine UI docs): `unified-trading-system-ui`,
`deployment-ui`, `user-management-ui`.

> `unified-trading-pm` itself is NOT a target — it _is_ the codex/plans SSOT. Its `plans/*` are historical records (do
> not rewrite). Repo `issues/*` + `*_LOG-REVIEW.md` + vendored `context/codex|pm/*` mirrors are records/mirrors, not
> living docs — out of scope (mirrors re-sync from canonical codex).

## Phases

- **Phase 0 — already shipped (2026-06-01)**: S5.11 contract codified; read-only audit registry for 8 core repos +
  FIX-STALE pass-1 (~340 literal fixes across 9 repos on `live-defi-rollout`). Evidence + 8-repo registry:
  [`issues/repo_docs_codex_ssot_consolidation_2026_06_01.md`](issues/repo_docs_codex_ssot_consolidation_2026_06_01.md).
- [ ] [DOCS] P0. **Phase 1 — audit-complete the remaining 12 repos** (read-only): agent-orchestrator, deployment-api,
      client-reporting-api, alerting-service, trading-agent-service, ibkr-gateway-infra,
      batch-live-reconciliation-service, system-integration-tests, deployment-ui, user-management-ui,
      unified-trading-system-ui (data/path docs only), + finish features-service audit. Produce the full per-doc
      registry (extend the pass-1 registry).
- [ ] [DOCS] P0. **Phase 2 — migrate unique deltas into codex.** For every MIGRATE-TO-CODEX doc (mtime-newer +
      codex-missing), write/extend the codex SSOT doc first. Commit codex changes. This must precede any
      REDIRECT/DELETE.
- [ ] [DOCS] P1. **Phase 3 — redirect + slim.** Convert REDIRECT docs to the S5.11 template; slim KEEP-ESSENTIAL docs to
      repo-local + codex links. Per-repo commit + push (PR where LDR is branch-protected — e.g. features-service).
- [ ] [DOCS] P1. **Phase 4 — delete pure-dups.** Remove DELETE-class docs (migration already done in Phase 2). Update
      any `INDEX.md` / README doc-index links.
- [ ] [DOCS] P2. **Phase 5 — verify + enforce.** Run S5.7 audit per repo; add a QG/CI check that flags repo docs
      duplicating a codex table/contract (or hardcoding a resolver-owned literal); confirm all redirect links resolve.

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
