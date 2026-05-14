---
title: Workspace ruff auto-fix sweep — repo-by-repo, per-shippable-unit (Sonnet-suitable)
type: cleanup-plan
status: active
created: 2026-05-12
locked_by: live-defi-rollout
locked_since: 2026-05-12
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
effective_concurrent_slots: 1
companion_to: codex/06-coding-standards/ruff-discipline.md
---

# Workspace ruff auto-fix sweep

> **Sonnet-suitable mechanical cleanup.** Per-repo cadence: rebase → `ruff format .` → `ruff check . --fix` →
> `ruff check . --select RUF100 --fix --unsafe-fixes` → verify → commit → push → flip checkbox → next repo. SSOT:
> [`codex/06-coding-standards/ruff-discipline.md`](../../codex/06-coding-standards/ruff-discipline.md).

## Why this exists

Workspace audit (2026-05-12 ~11:50 UTC) found:

- **~1620 lint violations** across ~30 Python repos (1227 in `new-sports-batting-services` outlier, ~393 across the
  rest).
- **~720 unused-noqa flags** (RUF100) workspace-wide — ~570 are non-`qg-*` codes (cleanly removable).
- **~270 files** needing `ruff format` reformatting.
- Top noqa offenders: `unified-trading-library` (184 unused), `unified-api-contracts` (100), `execution-service` (98),
  `features-service (sports family)` (53), `market-data-processing-service` (38), `ml-training-service` (37),
  `e2e-testing` (37).
- Pattern: ~70-80% of `# noqa` flags in lint-noisy repos are unused — agents adding `# noqa` to ship past ruff instead
  of fixing.

Result: Telegram CI alerts are flooded with lint failures, masking real issues (type errors, test regressions, SSOT
drift).

## Done definition

Per in-scope repo:

- `ruff format .` clean (no `Would reformat` output).
- `ruff check .` either clean OR residual is un-auto-fixable (RUF003 unicode + un-wrappable E501) and itemized in plan
  body.
- `ruff check . --select RUF100` clean (no unused-noqa flagged).
- One commit per repo with `style: ruff format + check --fix + RUF100 cleanup (<repo>)`, pushed to `live-defi-rollout`.
- Checkbox in this plan flipped with `<repo>@<sha>` evidence.

## HARD RULES (agent MUST follow)

1. **One repo at a time.** Per shippable-unit cadence: rebase → format → fix → commit → push → flip → next. NEVER
   touch >1 repo per commit.
2. **Whole-repo `ruff format .` and `ruff check . --fix` ARE allowed inside an in-scope repo.** This is the deliberate
   exception to [`codex/06-coding-standards/ruff-discipline.md`](../../codex/06-coding-standards/ruff-discipline.md)
   rule-zero ("don't run ruff on whole repo") — because this plan IS the whole-repo sweep, and the DO-NOT-TOUCH list
   (rule 5) protects against agent collision. The exception applies ONLY to in-scope repos; foreign repos still get the
   standard rule-zero treatment.
3. **Before starting each repo: `git status --porcelain` MUST be empty.** If not empty: SKIP that repo + flag in plan
   body — that repo has an active agent's uncommitted WIP and is not yours to touch. Do NOT `git restore` or `git clean`
   foreign content (foot-gun #2 / CLAUDE.md "Two teammates × multiple parallel agents").
4. **Per-repo push: `git fetch origin && git rebase origin/live-defi-rollout` MUST succeed cleanly.** If a rebase
   conflict surfaces, the foreign change touched the same files you just modified — `git rebase --abort`, skip + flag in
   plan body, move on. Don't force.
5. **DO NOT TOUCH** these repos under any circumstance during this plan (active agents OR Ikenna-side Phase 6.3-6.8
   BUILD dispatch):
   - `unified-trading-pm` (slot-1 orchestrator's own home)
   - `unified-api-contracts` (Ikenna slot 2 + multi-slot UAC)
   - `unified-trading-library` (Ikenna slot 2 v8-manifestwriter)
   - `market-tick-data-service` (slot 2 Phase 3 + Ikenna slot 3 PipelineMode)
   - `market-data-processing-service` (Ikenna slot 2 writegate Phase 6.2)
   - `execution-service` (slot 4 + slot 5)
   - `instruments-service` (slot 2 + Ikenna slot 3 catalog BUILD)
   - `features-service` (slot 3 + Ikenna features-consolidation)
   - `risk-and-exposure-service` / `strategy-service` / `position-balance-monitor-service` / `alerting-service` (slot 5
     risk + DR)
   - `ml-training-service` (slot 6 BUILD #3 + Ikenna slot 8 BUILD dispatch)
   - `deployment-service` (slot 7 synbench), `deployment-api` (slot 5 endpoints)
   - `features-service (volatility family)` (Ikenna slot 6 Phase 6.3-6.8 dispatch)
   - `ml-inference-service` (Ikenna slot 7 Phase 6.3-6.8 dispatch)
   - `features-service (cross-instrument family)` (Ikenna slot 8 Phase 6.3-6.8 dispatch)
   - `new-sports-batting-services` (1227-violation outlier — needs dedicated session, NOT this plan)
6. **`--unsafe-fixes` ONLY for `--select RUF100`.** The unused-noqa removal is the only unsafe-fix this plan blesses.
   Never run `ruff check --fix --unsafe-fixes` un-scoped (string-to-fstring conversions + other rewrites that can change
   semantics).
7. **Per-repo commit message**: `style: ruff format + check --fix + RUF100 unused-noqa cleanup (<repo>)`.
8. **Plan-flip per repo**: tick the checkbox below with `<repo>@<sha>` evidence after push lands. NEVER batch
   checkboxes.
9. **Stop after the in-scope list.** Don't expand scope unilaterally. If a DO-NOT-TOUCH repo becomes idle later, the
   operator will update this plan + nudge.
10. **Residual hand-fix is NOT in scope.** RUF003 unicode + un-wrappable E501 are deliberately left for the operator or
    a follow-up session — they need judgment per the codex SOP's substitution table.

## In-scope repos (priority order — smallest first to build confidence)

Cadence: one repo per checkbox. Lint/format/noqa counts from 2026-05-12 ~11:50 UTC audit; rebase will refresh.

- [ ] `features-service (calendar family)` — lint=4 / format=1 / unused-noqa=1 (warm-up) **SKIPPED-PERMANENT** —
      `isArchived=true` on GitHub; repo read-only, cannot push
- [ ] `features-service (commodity family)` — lint=2 / format=1 / unused-noqa=3 **SKIPPED-PERMANENT** —
      `isArchived=true` on GitHub; repo read-only, cannot push
- [x] `trading-agent-service` — lint=2 / format=0 / unused-noqa=1 — **NO CHANGES** (already clean; residual: 1 C901 in
      .cursor/scripts/) (slot-7/tab/ikennaigboaka/7)
- [x] `ibkr-gateway-infra` — lint=5 / format=2 / unused-noqa=1 — ibkr-gateway-infra@3000860; residual: 1 SIM105
      (un-auto-fixable)
- [ ] `features-service (delta-one family)` — lint=3 / format=1 / unused-noqa=7 **SKIPPED-PERMANENT** —
      `isArchived=true` on GitHub; repo read-only, cannot push
- [ ] `features-service (multi-timeframe family)` — lint=2 / format=1 / unused-noqa=5 **SKIPPED-PERMANENT** —
      `isArchived=true` on GitHub; repo read-only, cannot push
- [ ] `features-service (onchain family)` — lint=4 / format=1 / unused-noqa=5 **SKIPPED-PERMANENT** — `isArchived=true`
      on GitHub; repo read-only, cannot push
- [x] `pnl-attribution-service` — lint=4 / format=2 / unused-noqa=5 — pnl-attribution-service@300c7fd; residual: 4 C901
      (un-auto-fixable)
- [x] `batch-live-reconciliation-service` — lint=3 / format=2 / unused-noqa=1 —
      batch-live-reconciliation-service@0494e39; residual: 0
- [x] `system-integration-tests` — lint=6 / format=0 / unused-noqa=10 — system-integration-tests@609704f; residual: 12
      C901+E741 (un-auto-fixable)
- [ ] `features-service (sports family)` — lint=1 / format=2 / **unused-noqa=53** (noqa-heavy; main payoff here)
      **SKIPPED-PERMANENT** — `isArchived=true` on GitHub; repo read-only, cannot push
- [x] `unified-trading-api` — lint=7 / format=3 / unused-noqa=16 — unified-trading-api@8e5f06e; residual: 15
      C901+E501+N812 (un-auto-fixable)
- [x] `client-reporting-api` — lint=51 / format=2 / unused-noqa=6 (lint-heavy; many residual hand-fixes expected —
      itemize residual count) — client-reporting-api@9258ad1; residual: 49 C901+SIM105+E501+RUF005 (un-auto-fixable)
- [x] `e2e-testing` — lint=54 / format=39 / unused-noqa=37 (BIGGEST in-scope; save for last; expect ~5000-line diff) —
      e2e-testing@5c79a82; residual: 57 C901+E501+F841+E741 (un-auto-fixable; sports scripts with deep complexity)

## Per-repo recipe (template)

```bash
cd /home/hk/unified-trading-system-repos/<repo>

# 0. Confirm clean (rule 3)
if [ -n "$(git status --porcelain)" ]; then
  echo "SKIP — pre-existing dirty (foreign WIP)"; exit 0
fi

# 1. Rebase fresh
git fetch origin --quiet && git rebase origin/live-defi-rollout

# 2. Run ruff (the deliberate whole-repo exception per rule 2)
ruff format .
ruff check . --fix
ruff check . --select RUF100 --fix --unsafe-fixes

# 3. Sanity-check the diff before committing
git status                            # only this repo's files
git diff --stat                       # spot-check magnitude
ruff check . --output-format=concise  # what's left (residual; record below)

# 4. Commit + push
git add -u
git commit --no-verify -m "style: ruff format + check --fix + RUF100 unused-noqa cleanup (<repo>)"
git fetch origin --quiet && git rebase origin/live-defi-rollout
git push origin HEAD:live-defi-rollout --no-verify

# 5. Capture <repo>@<sha> for the plan flip
git log -1 --pretty='%H'

# 6. Move to next repo
```

## Residual hand-fix scoreboard (agent fills in after the auto-fix pass)

Per the 2026-05-12 audit, ~570 residual violations are expected workspace-wide after auto-fix (mostly RUF003 unicode +
un-wrappable E501). Agent records the per-repo residual count after each ruff pass:

- [ ] `features-service (calendar family)` residual: **SKIPPED-PERMANENT** (isArchived=true on GitHub)
- [ ] `features-service (commodity family)` residual: **SKIPPED-PERMANENT** (isArchived=true on GitHub)
- [x] `trading-agent-service` residual: 1 violation (C901 in .cursor/scripts/ — un-fixable)
- [x] `ibkr-gateway-infra` residual: 1 violation (SIM105 — un-auto-fixable)
- [ ] `features-service (delta-one family)` residual: **SKIPPED-PERMANENT** (isArchived=true on GitHub)
- [ ] `features-service (multi-timeframe family)` residual: **SKIPPED-PERMANENT** (isArchived=true on GitHub)
- [ ] `features-service (onchain family)` residual: **SKIPPED-PERMANENT** (isArchived=true on GitHub)
- [x] `pnl-attribution-service` residual: 4 violations (C901 — un-auto-fixable)
- [x] `batch-live-reconciliation-service` residual: 0 violations ✅ fully clean
- [x] `system-integration-tests` residual: 12 violations (C901+E741 — un-auto-fixable)
- [ ] `features-service (sports family)` residual: **SKIPPED-PERMANENT** (isArchived=true on GitHub)
- [x] `unified-trading-api` residual: 15 violations (C901+E501+N812 — un-auto-fixable)
- [x] `client-reporting-api` residual: 49 violations (C901+SIM105+E501+RUF005 — un-auto-fixable; hand-fix follow-up
      needed)
- [x] `e2e-testing` residual: 57 violations (C901+E501+F841+E741 — un-auto-fixable; complex sports scripts)

When the auto-fix sweep is done, agent posts a final `harsh_orchestrator/pings/slot_N.md` summary with workspace-wide
residual count. Hand-fix is a separate follow-up plan, NOT this one's scope.

## Telegram-channel hygiene verification (post-sweep)

- [ ] After the sweep, all in-scope repos are GREEN on `live-defi-rollout` lint step.
- [ ] Over the next 24h, Telegram channel lint-alert volume drops to ~0 for in-scope repos.

## Out-of-scope (deliberate)

- All repos on the DO-NOT-TOUCH list (rule 5).
- `new-sports-batting-services` (1227 violations + 121 format files — needs its own session, not this).
- Residual hand-fix for RUF003 / un-wrappable E501 (follow-up plan).
- `# noqa` review for `qg-*` workspace-custom codes (those are intentional; never strip).
- `basedpyright` / type-check cleanup (separate concern; this plan is ruff only).

## Follow-up todos (not in this plan's sweep wave)

- [ ] [AGENT] P0. UAC residual lint: 130 non-RUF003 ruff errors remain in `unified-api-contracts` after Cluster A RUF003
      sweep (2026-05-14 audit). Run `cd unified-api-contracts && ruff check unified_api_contracts/ --fix` scoped to
      auto-fixable rules; for remainder add targeted `# noqa: <code>` with inline rationale per
      `codex/06-coding-standards/ruff-discipline.md` substitution table. QG (`bash scripts/quality-gates.sh`) must reach
      clean ruff exit. Assign to Harsh slot on next cycle once UAC multi-slot activity (Ikenna slots 2+3+6 May-23 push)
      clears.

## Cross-references

- [`codex/06-coding-standards/ruff-discipline.md`](../../codex/06-coding-standards/ruff-discipline.md) — workspace SOP
  (foot-gun #2, rule zero + this plan's exception, RUF003 substitution table, `# noqa` guidance, real-alert taxonomy).
- [`plans/active/issues/ci_lint_failures_ruff_fix_guidance_2026_05_12.md`](issues/ci_lint_failures_ruff_fix_guidance_2026_05_12.md)
  — original issue doc (promoted to codex `f4cff324`).
- `cursor-configs/CLAUDE.md` § "Two teammates × multiple parallel agents (CRITICAL)" — concurrency safety + foot-gun #2
  incident citation.
- `cursor-configs/CLAUDE.md` § "Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)" —
  per-shippable-unit cadence the agent must follow.

## Model directive

**Sonnet max** is the right tier. The work is purely templated (per-repo, same recipe), no design judgment needed. The
HARD RULES + DO-NOT-TOUCH list keep the agent safe. Escalate to operator (post 🟡 BLOCKED + ping the assigned slot's
ping file) only if:

- A DO-NOT-TOUCH repo somehow appears to need attention (don't take it yourself — flag).
- The residual count after auto-fix is wildly higher than the audit predicted (suggests an upstream issue).
- A rebase conflict during the per-repo push reveals a foreign agent simultaneously modifying the same in-scope repo
  (rare but possible — abort that repo + flag).
