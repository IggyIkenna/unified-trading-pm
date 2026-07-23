---
title: Refactor G3.2 — Pricing-numbers populated from Odum finance
status: active
priority: P1
owner: finance + agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §3.2
# Wave G3-α — independent, parallel with G3.3/3.4/3.5/3.6. Gates G3.1 pricing-engine service.
---

# Refactor G3.2 — Pricing-numbers populated from Odum finance

## Context

Stage 3E §3.2 populates the internal-cost + Tier A + Tier B numeric columns in
`/codex/14-playbooks/commercial-model/pricing-building-blocks.md`. Stage 2 already locked the 13-row × 3-column
structure + sales anchor ranges. The numeric cells that sit inside sit only in Odum finance dashboards and leadership
decks today.

This is primarily an organisational workflow — finance populates numbers via Google Sheet → export → commit. Engineering
owns the doc structure, validation tooling, and leak-prevention guardrails. Quarterly cadence.

## Decisions locked with user (2026-04-20)

| Decision                                                          | Chosen                                                               | Source                               |
| ----------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------ |
| Populate via non-codex workflow (finance Sheet → export → commit) | Finance team owns the numbers; engineering owns the doc structure    | Stage 3E §3.2 (organisational)       |
| Update cadence: quarterly                                         | Balances freshness vs noise; leadership reviews quarterly anyway     | Stage 3E §3.2                        |
| Internal-column leakage guard via rule 08                         | Only finance-authorised commits land on `pricing-building-blocks.md` | Rule 08 + cost-leakage invariants    |
| Structure (13 × 3) stays frozen                                   | No schema drift during number population                             | Stage 2 commercial model + plan §3.2 |

## Cross-references

- **Upstream:** Stage 2 commercial-model numeric locks
- **Downstream Wave G3-β:** G3.1 pricing-engine service (consumes populated numbers)
- **Codex:** `/codex/14-playbooks/commercial-model/pricing-building-blocks.md`,
  `/codex/14-playbooks/_ssot-rules/08-internal-cost-leakage.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §3.2
2. `/codex/14-playbooks/commercial-model/pricing-building-blocks.md` — current 13-row × 3-col structure
3. `/codex/14-playbooks/_ssot-rules/08-internal-cost-leakage.md` — leakage rules
4. Odum finance Google Sheet (off-codex; operator provides link when executing)

## Out of scope

- Building the pricing-engine service (G3.1)
- Exposing numbers externally (rule 08 — internal-only)
- Changing the 13-row × 3-col structure (frozen)
- Automating the finance Sheet → codex sync (manual commit cadence is acceptable for quarterly updates)
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Finance workflow setup (operator-heavy)

- [ ] [OPERATOR] P0. Identify canonical finance Google Sheet that holds the numeric cells (leadership + finance ops
      team).
- [ ] [OPERATOR] P0. Document export process: Sheet → CSV → format → paste into `pricing-building-blocks.md` table.
- [x] [AGENT] P0. Validation script `scripts/validation/check_pricing_building_blocks.py` — asserts 13-row main table
      present + populated, no `codex-private (TBD)` sentinels after population, block-5 depth sub-table has 3 populated
      rows, block-12 exclusivity table has 4 IP-power rows. Shipped 2026-04-20.

### Phase B — Leak-prevention guardrails

- [x] [AGENT] P0. Rule 08 enforcement: `scripts/validation/check_cost_leakage.py` scans 46 external-audience surfaces
      (UI `app/(public)/**`, `marketing-static/`, `codex/14-playbooks/briefings/`, `codex/14-playbooks/cross-cutting/`)
      for 13 internal-cost patterns (block-by-block numbers + prose markers). Shipped 2026-04-20.
- [ ] [AGENT] P0. Codex doc `/codex/14-playbooks/commercial-model/_pricing-building-blocks-workflow.md` — describes the
      quarterly cadence + finance hand-off.

### Phase C — Initial population (agent-led draft; finance owns quarterly refresh)

- [x] [AGENT] P0. Initial population 2026-04-20: internal-cost column populated from the ~£34k/mo base burn in
      `revenue-projection-2026-monthly.md` using a 3-layer allocation methodology (corporate overhead / data licences /
      engineering+cloud). Landed on `live-defi-rollout` as commit `eacd2f8f`.
- [ ] [FINANCE] P0. Next quarterly export: refresh internal-cost column if base burn moves ±15% or FTE/vendor changes.
- [ ] [FINANCE] P0. Commit via workflow with `[finance]` tag in commit message to satisfy rule 08 audit.
- [ ] [OPERATOR] P0. Review + leadership sign-off on the quarterly refresh.

### Phase D — QG + verification

- [x] [SCRIPT] P0. `python scripts/validation/check_pricing_building_blocks.py` returns 0 — 13-row structure +
      population OK.
- [x] [SCRIPT] P0. `python scripts/validation/check_cost_leakage.py` returns 0 — 46 external surfaces free of leaks.
- [ ] [AGENT] P0. Update G3.1 pricing-engine plan to reference the populated numbers as the canonical source.

## Critical files to be modified

- `/codex/14-playbooks/commercial-model/pricing-building-blocks.md` — MODIFY (populate cells)
- `/codex/14-playbooks/commercial-model/_pricing-building-blocks-workflow.md` — NEW (process doc)
- `scripts/validation/check_pricing_building_blocks.py` — NEW
- `scripts/validation/check_cost_leakage.py` — NEW (or extend existing leak-guard)
- `.github/workflows/check-pricing-cost-leak.yml` — NEW (CI hook)

## Execution DAG

```
A (finance workflow + validation script) → B (leak guardrails)
                                              ↓
                                            C (finance populates numbers)
                                              ↓
                                            D (QG + hand-off to G3.1)
```

## Verification

1. `pricing-building-blocks.md` 13 × 3 cells populated (no TODO sentinels after first quarter).
2. `check_cost_leakage.py` returns 0 matches on external docs.
3. CI leak-guard job green.
4. G3.1 plan referenced from §3.2.

## Handoff

Unblocks:

- **G3.1 pricing-engine service** — numbers exist to serve.
- **Future commercial-ops automation** — proposals gen can read canonical numbers.

## Playwright test coverage (mandatory)

**MCP Playwright:** not primarily a UI surface. Any admin UI that surfaces pricing-building-blocks content (future G3.1)
will have its own spec. This plan's "test" is the validation script + leak-guard CI.

**Durable spec for CI:** `scripts/validation/check_pricing_building_blocks.py` +
`.github/workflows/check-pricing-cost-leak.yml`:

1. `check_pricing_building_blocks.py` asserts structure invariants + populated-cell counts.
2. `check_cost_leakage.py` scans external docs for internal-cost leakage.
3. CI workflow runs both on every PR touching `commercial-model/` or `marketing-static/`.
4. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G3.2 (Wave G3-α, ops-heavy).**

---

You are executing **Refactor G3.2 — Pricing-numbers populated from Odum finance** for the Unified Trading System at Odum
Research. Wave G3-α; primarily organisational + validation tooling. Phase C is finance-led.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git checkout live-defi-rollout && git pull
ls /codex/14-playbooks/commercial-model/pricing-building-blocks.md
ls /codex/14-playbooks/_ssot-rules/08-internal-cost-leakage.md
```

All must exist. STOP if missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute Phases A, B, D of this plan (Phase C is finance-led):
`plans/active/refactor_g3_2_pricing_numbers_from_finance_2026_04_20.plan.md`

### Read-set (mandatory)

All 4 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 5 files in PM repo.

### MCP Playwright clause (verbatim — REQUIRED)

This plan is primarily validation tooling (not UI). Use MCP Playwright only if any admin UI surface is added to display
pricing-building-blocks data; otherwise, the `check_pricing_building_blocks.py` + `check_cost_leakage.py` scripts + CI
workflow serve as the verification surface.

### Commit strategy

One commit in PM repo.

```
cd unified-trading-pm && bash scripts/quickmerge.sh "feat(commercial-model): G3.2 — pricing numbers validation + leak guardrails + finance workflow doc" --agent
```

Manual-git fallback. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Validation script green on populated + TODO-marked cells.
2. ✅ Leak-guard green on external surfaces.
3. ✅ CI workflow wired.
4. ✅ Workflow doc committed.
5. ✅ 1 commit SHA pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT surface internal-cost numbers externally — rule 08 is absolute.
- Do NOT change the 13-row × 3-col structure — frozen per Stage 2.
- Do NOT commit numbers yourself — finance populates (Phase C).
- Do NOT automate Sheet → codex sync — manual quarterly cadence is sufficient.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Validation script test cases.
- Leak-guard exclusion rules.
- CI workflow job ID.
- 1 commit SHA pushed.
- Finance hand-off checklist for Phase C.
