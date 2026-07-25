---
title: "Path to $100M — finalise commercial docs, strategy lock state, deck alignment"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - playbook_ssot_stage_2_doc_rewrite_2026_04_19
# Follow-on work:
#   - Finance numbers populate into pricing-building-blocks.md (separate commit, Odum finance owned)
#   - Stage 3B UAC combo registry enforcement of strategy lock_state
---

# Path to $100M — finalisation

## Context

Over three conversations across 2026-04-19 → 2026-04-20, we locked concrete commercial answers for Odum's 2026 run-plan:

- **Monthly burn**: £32-35k/month (Tardis academic licence £8k/yr, engineering $20k/mo, FCA £10k/yr, AML-only legal
  £1k/mo, no management team, AI agentic £2k/mo).
- **Revenue lines and timing**: existing baseline £8k/mo (Seed Reg Umbrella + mean-rev IM + BTC FoF wrapper), plus
  Elysium Phase A (Jun go-live, $35k remaining, £80-100k upsells through Dec), BTC ML directional (Jun, 10 × $500k),
  sports ML (Jun, 2 × $50-100k capacity-bound), CME S&P (Sept, asymmetric 70/10 co-invest), India Options (Oct, $100k
  onboarding), Desmond (May earliest, Reg Umbrella + DART signals-only £22k/mo + £25-50k upfront), signal leasing (2
  counterparties Q3-Q4).
- **Annual 2026 revenue projection**: ~£690k, net profit ~£190k. **Starting cash April 2026 £240k ($305k USD)**; cash
  remains >£195k all year; year-end projected ~£464k. No bridge capital required.
- **Strategy lock state**: strategies Odum is running for its own IM mandates must be `IM_RESERVED` so DART prospects
  never see them as available. BTC FoF is external (no system compute) — not in the catalogue.
- **CME co-invest structure**: Odum puts $50k skin-in-the-game, receives 70% of profits, bears only 10% of losses.
  Asymmetric because Odum brings the strategy IP.
- **IM platform fee**: client picks at mandate signing — {+5% perf fee} OR {$500/mo flat}.

This plan ships the full stack of commercial + strategy-lock + deck updates in coordinated, small commits to minimise
orchestrator collision risk and keep Stage 2's doc-only scope intact where possible.

## Decisions locked with user (2026-04-20)

| Decision                     | Chosen                                                                                                                     | Rationale                                                                  |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Elysium post-June mechanic   | 30% of what they make (profit-share-only; no cost-share layered on top)                                                    | Clean and simple; Elysium's revenue contribution scales with their success |
| IM platform fee              | Client-choice at mandate signing: {+5% perf fee uplift} OR {$500/mo flat}                                                  | Preserves alignment optionality; gives allocator agency                    |
| CME skin-in-the-game scaling | TBD — to be confirmed flat $50k vs pro-rata (document both options)                                                        | Pending commercial close                                                   |
| India Options split          | Same 30-35% framework as BTC ML, NOT higher                                                                                | $100k onboarding already covers new-venue cost premium                     |
| Signal leasing pricing       | TBD — document as either monthly licence ($15-30k/mo/counterparty) or per-signal metering; leave as pending in pricing doc | User to answer                                                             |
| Desmond upfront              | £25-50k range (£25k worst / £50k best)                                                                                     | User confirmed                                                             |
| Desmond monthly              | ~£22k (Reg Umbrella £12k + DART signals-only £10k)                                                                         | Based on rule-05 block composition                                         |
| Desmond start                | May 2026 earliest                                                                                                          | Calendar constraint                                                        |
| Strategy catalogue lock      | IM_RESERVED = strategies Odum is running for own IM; DART prospects never see them                                         | Rule 06 same-system enforcement                                            |
| BTC FoF classification       | External fund; NOT in strategy catalogue; surfaced only in client-reporting for the specific wrapper mandate               | Avoids over-engineering a dedicated lock state                             |

## Cross-references

- Stage 2 plan:
  [playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md](playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
- Investor deck (path-to-100M): `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts`
- Board deck:
  `unified-trading-system-ui/app/(platform)/investor-relations/board-presentation/components/board-presentation-data.ts`
- Strategy architecture-v2: `unified-trading-pm/codex/09-strategy/architecture-v2/`
- Persona fixtures: `unified-trading-system-ui/lib/auth/personas.ts`
- Strategy availability UI state: `unified-trading-system-ui/lib/architecture-v2/availability.ts` +
  `unified-trading-system-ui/lib/architecture-v2/availability-store.tsx`

## Mandatory read-set

1. This plan
2. [playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md](playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
3. All 10 files in `codex/14-playbooks/_ssot-rules/`
4. Stage 2 outputs already shipped: `experience/`, `shared-core/`, `commercial-model/`, `demo-ops/`,
   `implementation-mapping/`
5. `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` +
   `cross-cutting/strategy-availability-and-locking.md`
6. `unified-trading-system-ui/lib/auth/personas.ts` (current persona fixtures)
7. `unified-trading-system-ui/lib/architecture-v2/availability.ts` (current catalogue state model)
8. `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts` (path-to-100M slides)

## Out of scope (explicit)

- Populating real pricing numbers with finance sign-off (structure only; sensitive numbers in internal docs stay
  codex-private per rule 08)
- Stage 3B UAC combo registry enforcement of lock_state (this plan updates the canonical data; Stage 3B makes it
  runtime-enforced)
- Any changes to strategy archetype definitions themselves (we only add lock_state metadata to existing cells)
- FCA capital adequacy planning (separate treasury/compliance workstream)
- External fundraise planning (separate ops workstream)

## Execution DAG

```
Phase 1 (pre-audit) ──▶ Phase 2 (commercial + pricing docs)  ──┐
                  └───▶ Phase 3 (strategy catalogue lock data) ──┼─▶ Phase 5 (deck refresh)
                  └───▶ Phase 4 (architecture-v2 sync) ─────────┘      ↓
                                                                  Phase 6 (cross-link audit + verification)
                                                                        ↓
                                                                  Phase 7 (handoff)
```

Phases 2, 3, 4 are parallelisable. Phase 5 consumes all three. Phase 6 validates the whole.

---

## Phase 1 — Pre-audit manifest

- [ ] [AGENT] P0. Build file-level manifest of everything touching strategy lock_state, IM/DART/Reg pricing, or the
      path-to-100M narrative. Confirm no surprise consumers exist beyond the read-set above.
- [ ] [AGENT] P0. Check current UI lock_state enum values in
      `unified-trading-system-ui/lib/architecture-v2/availability.ts` to confirm `IM_RESERVED` is already supported (per
      Phase 10 UI shipped 2026-04-19). If missing, note the cross-repo enum extension scope.
- [ ] [AGENT] P0. Verify the existing Phase 10 catalogue filter actually hides non-PUBLIC rows for non-admin personas
      before relying on it. Read the catalogue page component + availability store.
- [ ] [AGENT] P0. Confirm persona `prospect-platform` + `prospect-regulatory` + `elysium-defi` fixtures existing in
      `personas.ts` — already reconciled doc-side on 2026-04-20; no UI enum changes needed.
- [ ] [AGENT] P0. Scan `board-presentation-data.ts` for existing "commercial stack" or "revenue composition" slide
      content — decide whether to add new slide or edit in place.
- [ ] [AGENT] P0. **Success gate**: pre-audit manifest captured, all read-set files accessible, no unknown blockers
      surfaced.

## Phase 2 — Commercial + pricing docs (Stage 2 scope, doc-only)

All edits inside `unified-trading-pm/codex/14-playbooks/`. Commits land as one unit per sub-batch to tolerate
orchestrator drift.

### 2A. New docs (shared-core + commercial-model)

- [ ] [AGENT] P0. Create `shared-core/dart-pricing-axes.md` — signals-only vs full-DART pricing dimensional model.
      Fixed-access layer + per-backtest metering + IP-power exclusivity tiers + venue/server cost pass-through formula.
      Cite rule 04, 05, 08, 10.
- [ ] [AGENT] P0. Create `shared-core/strategy-allocation-lock-matrix.md` — current snapshot (dated 2026-04-20) of
      IM_RESERVED vs PUBLIC cells. Concrete list: STAT_ARB_PAIRS_FIXED × crypto pairs (mean rev),
      ML_DIRECTIONAL_CONTINUOUS × BTC perp/spot on Binance/Coinbase/Hyperliquid, ML_DIRECTIONAL_CONTINUOUS × S&P futures
      on CME, VOL_TRADING_OPTIONS × NSE options India (delta-trading mode), ML_DIRECTIONAL_EVENT_SETTLED × specific
      sports fixtures. Note BTC FoF is external (not in catalogue).
- [ ] [AGENT] P0. Create `commercial-model/im-profit-share-structures.md` — all IM mechanics: standard 30-35%
      perf-share, platform-fee choice (A: +5% perf | B:
      $500/mo flat) at mandate signing, CME co-invest asymmetric (70%
      profits / 10% losses), India Options 30-35% with $100k
      onboarding, mean-rev migration path, BTC FoF wrapper (external, non-system).
- [ ] [AGENT] P1. Create `commercial-model/signal-leasing.md` — pricing model placeholder; document monthly-licence vs
      per-signal vs rev-share options; mark pending user answer.
- [ ] [AGENT] P0. Create `commercial-model/revenue-projection-2026-monthly.md` (codex-private internal) — the monthly
      revenue table, monthly P&L, cumulative cash curve starting April 2026 at £240k, min cash £198k (Apr), year-end
      cash ~£464k, scenarios (base / upside / downside), sensitivity to Desmond slippage + BTC ML performance + S&P ML
      signal timing.
- [ ] [AGENT] P0. Create `commercial-model/cash-deployment-plan.md` (codex-private internal) — starting cash April 2026
      £240k ($305k USD), burn components, startup proof-readiness costs (£25-50k), CME skin funding ($50k from operating
      cash), H1 2026 reserve (target ~£150k minimum buffer), deployment priorities. Frame as cash _deployment_ (how we
      use the buffer to fund growth) rather than cash _runway_ (survival).

### 2B. Updated docs (existing Stage 2 files)

- [ ] [AGENT] P0. Update `commercial-model/pricing-building-blocks.md` — populate all 13 rows with anchor numbers;
      internal-cost column codex-private per rule 08; add per-engagement special-structure notes (CME co-invest, Elysium
      profit-share, IM platform-fee choice, India Options onboarding-as-block-13-custom).
- [ ] [AGENT] P0. Update `commercial-model/dart-entry-points.md` — add worked examples: Elysium signals-only Phase A +
      Phase B + upsells to $200k+, Desmond Reg Umbrella + DART combined, India Options as `(Odum, full-pipeline)` IM
      engagement (NOT DART).
- [ ] [AGENT] P0. Update `commercial-model/im-vs-reg-reporting-logic.md` — refresh IM pricing shape: NO management fee,
      30-35% performance fee, platform-fee choice, mean-rev migration.
- [ ] [AGENT] P1. Update `commercial-model/exclusivity-and-noncompete.md` — add IP-power tier examples anchored to our
      actual strategies (ML directional BTC = commodity ~25%; ML directional S&P = specialised ~60%; India options
      delta-only = scarce ~100%; etc).
- [ ] [AGENT] P0. Update `shared-core/strategy-origin-vs-stack-depth.md` — add 5 named worked examples: CME (Odum
      strategy + asymmetric co-invest), India Options (Odum strategy, new venue, options), Elysium Phase A+B
      (client-downstream, DeFi yield), Desmond (client-downstream + reg cover combined), BTC FoF (external wrapper
      surfaced in client reporting only).
- [ ] [AGENT] P1. Update `shared-core/org-fund-client-entity-model.md` — add external-wrapper note for BTC FoF: Odum as
      allocator, not operator; appears only in client-reporting surface for the specific mandate.
- [ ] [AGENT] P1. Update `shared-core/venue-chain-instrument-scope.md` — refresh with actual 2026 venue scope: CEFI
      (Binance, Coinbase, Hyperliquid, CME-futures, NSE-options), DeFi chains (Ethereum L1, Arbitrum, Base, Solana),
      sports (specific league set capacity-bound), prediction (Polymarket).
- [ ] [AGENT] P0. Update `experience/im-decision-journey.md` — add platform-fee-choice mechanic to walkthrough (client
      decides at mandate signing); add BTC FoF external-wrapper footnote; reflect 30-35% perf-fee-only model.
- [ ] [AGENT] P0. Update `experience/dart-briefing.md` — extend signals-only-vs-full-DART comparison table with pricing
      dimensions (fixed vs metered); explicitly note IM_RESERVED cells are HIDDEN-ENTIRELY from DART prospects in pb3c.
- [ ] [AGENT] P0. Update `experience/dart-demo.md` §7 what-not-to-show — explicit list of IM_RESERVED archetypes that
      must not appear in DART prospect demos (BTC ML on BTC venues, S&P ML on CME, India options, etc).
- [ ] [AGENT] P0. Update `demo-ops/demo-restriction-profiles.md` — add explicit IM_RESERVED filter to every DART
      profile's catalogue filter set.
- [ ] [AGENT] P0. **Phase 2 success gate**: all docs committed + pushed; cross-references from experience layer to
      shared-core to commercial-model resolve; no dead links.

## Phase 3 — Strategy catalogue lock data (UI, minor scope-extend)

All edits inside `unified-trading-system-ui/`. This is UI code but narrowly scoped to data-only changes plus
persona/entitlement additions if needed.

- [ ] [AGENT] P0. Update `lib/architecture-v2/availability.ts` — set lock_state = IM_RESERVED on the concrete cells from
      the allocation-lock-matrix doc: - STAT_ARB_PAIRS_FIXED cells for crypto mean-rev (our existing IM) -
      ML_DIRECTIONAL_CONTINUOUS cells for BTC perp + BTC spot on Binance / Coinbase / Hyperliquid -
      ML_DIRECTIONAL_CONTINUOUS cells for S&P futures on CME (new; may need to ADD the cell if not present) -
      VOL_TRADING_OPTIONS cells for NSE options delta-trading (new; may need to ADD) - ML_DIRECTIONAL_EVENT_SETTLED
      cells for specific sports fixture leagues
- [ ] [AGENT] P0. Update the mock `AvailabilityStoreProvider` fixtures to match — so dev-mode rendering also reflects
      IM_RESERVED correctly.
- [ ] [AGENT] P1. Update `lib/mocks/fixtures/strategy-catalog-data.ts` — sync IM_RESERVED flags with availability.ts to
      keep all mock layers consistent.
- [ ] [AGENT] P0. Verify DART prospect personas (`prospect-platform`, `elysium-defi`) in
      `tests/e2e/playbooks/warm-prospect-demo.spec.ts` exercise the catalogue filter and confirm IM_RESERVED rows do not
      render. If the spec doesn't cover this, ADD the assertion.
- [ ] [AGENT] P0. Run `CI=true npm test -- --run` to confirm catalogue + filter unit tests still pass.
- [ ] [AGENT] P0. **Phase 3 success gate**: tests green; admin persona sees IM_RESERVED strategies; DART prospect
      personas do not; elysium-defi persona still sees their CARRY_BASIS_PERP / CARRY_STAKED_BASIS slots; catalogue test
      fixture data aligns with availability.ts.

## Phase 4 — Architecture-v2 strategy docs sync (doc-only)

- [ ] [AGENT] P0. Update `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` — add a "Current Odum
      Allocation" column or inline annotation on each cell indicating lock_state (IM_RESERVED / PUBLIC). Match the Stage
      2 allocation-lock-matrix exactly.
- [ ] [AGENT] P0. Update `/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md` — add a
      "Current Lock State Snapshot" section dated 2026-04-20 with the same concrete cell list, cross-linked to
      `/codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`.
- [ ] [AGENT] P0. **Phase 4 success gate**: codex strategy docs and playbook SSOT agree on which cells are IM_RESERVED;
      single snapshot date; no divergent wording.

## Phase 5 — Path-to-100M + board deck updates (UI data-only)

All edits inside `unified-trading-system-ui/app/(platform)/investor-relations/`. Data-file changes only; no UI logic /
component changes.

### 5A. Plan presentation (path-to-100M)

- [ ] [AGENT] P0. Update `plan-presentation/data.ts` slide 3 (trajectory) — refresh end-2026 / end-2027 / end-2028 AUM +
      deal-pipeline descriptors to reconcile against the concrete strategy × client mix (Elysium
      $200-230k upsold, BTC
      ML 10 clients, CME co-invest $5M Year-1 target, India Options, Desmond, signal
      leasing).
- [ ] [AGENT] P0. Update slide 4 (timeline-matrix `periods` + `strategies`) — replace generic "Options / volatility"
      with distinct rows for India Options (delta trading) and CME S&P ML directional; keep the Q3/Q4 2026 → Q2 2027
      timeline consistent with our deal calendar.
- [ ] [AGENT] P0. Update slide 9 (traction / "Next 30 months") — refresh end-2026 achieved list with the concrete deal
      pipeline (Elysium $200k+, BTC ML 10 × $500k, CME Sept, India Oct, Desmond live, signal leasing x2, baseline + Reg
      Umbrella). Refresh end-2027 and end-2028 to match revised trajectory.
- [ ] [AGENT] P1. Add a new doctrine slide (or expand slide 10 "Why this plan is realistic") — add the cashflow curve
      point: "April opens £240k → min £198k (Apr) → October step-up to £348k → December £464k" as a named operational
      milestone. Demonstrates the plan is self-funding; no external capital required for 2026.

### 5B. Board presentation

- [ ] [AGENT] P1. Audit `board-presentation-data.ts` for an existing "commercial stack" or "revenue composition" slide.
      If missing, add a new slide showing: IM perf-share + DART fixed-access + Reg Umbrella cover + Signal Leasing + CME
      co-invest. Matrix of strategy × commercial-mode.
- [ ] [AGENT] P1. Audit for an existing cashflow-shape slide. If missing, add one with the monthly revenue curve Jan →
      Dec 2026, cumulative-cash line, and key inflection points (April trough, October flip).
- [ ] [AGENT] P0. **Phase 5 success gate**: `npm test` green; `VITE_MOCK_API=true npx vite build` smoke-builds without
      errors; manual eyeball on the two presentations in dev server (tier-0 UI startup) confirms slides render correctly
      with the new data.

## Phase 6 — Cross-link audit + verification

- [ ] [AGENT] P0. Grep for orphaned or broken doc links: `grep -r "(\.\.\?/\([a-z-]*\))\]" codex/14-playbooks/` — every
      outbound link must resolve.
- [ ] [AGENT] P0. Verify the allocation-lock-matrix snapshot is cited consistently across:
      `/codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`,
      `/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`,
      `/codex/09-strategy/architecture-v2/category-instrument-coverage.md`,
      `unified-trading-system-ui/lib/architecture-v2/availability.ts`.
- [ ] [AGENT] P0. Verify CME asymmetric co-invest structure (70% profits / 10% losses) is consistent across:
      `commercial-model/im-profit-share-structures.md`, `commercial-model/pricing-building-blocks.md`,
      `shared-core/strategy-origin-vs-stack-depth.md`, `plan-presentation/data.ts`.
- [ ] [AGENT] P0. Verify platform-fee choice (Option A +5% perf | Option B $500/mo) is consistent across:
      `commercial-model/im-profit-share-structures.md`, `commercial-model/pricing-building-blocks.md`,
      `experience/im-decision-journey.md`.
- [ ] [AGENT] P0. Verify revenue-projection numbers in `commercial-model/revenue-projection-2026-monthly.md` reconcile
      with `plan-presentation/data.ts` slide 9 end-2026 claims.
- [ ] [AGENT] P0. Run `cd unified-trading-system-ui && CI=true npm test -- --run` one last time to confirm UI tests
      green.
- [ ] [AGENT] P0. Run `cd unified-trading-system-ui && npx tsc --noEmit` to catch any type errors in the
      availability.ts + deck data changes.
- [ ] [AGENT] P0. **Phase 6 success gate**: all consistency checks pass; UI tests green; typecheck clean.

## Phase 7 — Handoff

- [ ] [AGENT] P0. Summary report posted to the user covering: files created / modified per phase, commit SHAs,
      pre-revenue cashflow curve numbers, any open Stage 3 items (signal leasing pricing model, CME skin scaling, Stage
      3B runtime enforcement).
- [ ] [AGENT] P0. Update memory under
      `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/` with a
      project entry summarising the final 2026 run-plan + path-to-$100M deck alignment.
- [ ] [AGENT] P1. Add follow-up items to `/codex/14-customer-journeys/roadmap/next-waves.md` or equivalent: finance
      numbers populate (Odum finance owns), Stage 3B runtime enforcement of lock_state, signal-leasing pricing
      confirmation, CME skin-scaling confirmation, bridge-capital raise.

## Critical files

### New (8)

- `/codex/14-customer-journeys/shared-core/dart-pricing-axes.md`
- `/codex/14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`
- `/codex/14-customer-journeys/commercial-model/im-profit-share-structures.md`
- `/codex/14-customer-journeys/commercial-model/signal-leasing.md`
- `/codex/14-customer-journeys/commercial-model/revenue-projection-2026-monthly.md` (codex-private)
- `/codex/14-playbooks/commercial-model/runway-and-capital-plan.md` (codex-private)

### Updated — docs

- `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md`
- `/codex/14-customer-journeys/commercial-model/dart-entry-points.md`
- `/codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md`
- `/codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md`
- `/codex/14-customer-journeys/shared-core/strategy-origin-vs-stack-depth.md`
- `/codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md`
- `/codex/14-customer-journeys/shared-core/venue-chain-instrument-scope.md`
- `/codex/14-customer-journeys/experience/im-decision-journey.md`
- `/codex/14-customer-journeys/experience/dart-briefing.md`
- `/codex/14-customer-journeys/experience/dart-demo.md`
- `/codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md`
- `/codex/09-strategy/architecture-v2/category-instrument-coverage.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`

### Updated — UI data (minor scope-extend beyond Stage 2 doc-only)

- `unified-trading-system-ui/lib/architecture-v2/availability.ts`
- `unified-trading-system-ui/lib/architecture-v2/availability-store.tsx` (fixture data)
- `unified-trading-system-ui/lib/mocks/fixtures/strategy-catalog-data.ts`
- `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (add lock_state assertion)
- `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts`
- `unified-trading-system-ui/app/(platform)/investor-relations/board-presentation/components/board-presentation-data.ts`

## Commit strategy

Small per-phase commits to tolerate orchestrator drift observed during Stage 2 execution. Push after each commit.

1. **Commit A** (Phase 2A new docs, 6 files): `docs(codex/playbooks): Path-to-100M new commercial docs`
2. **Commit B** (Phase 2B updated docs, 11 files): `docs(codex/playbooks): Path-to-100M update existing commercial docs`
3. **Commit C** (Phase 3 UI data, 4 files): `feat(ui/arch-v2): IM_RESERVED lock state for Odum-IM strategies`
4. **Commit D** (Phase 4 architecture-v2, 2 files): `docs(codex/strategy): lock-state snapshot + allocation matrix`
5. **Commit E** (Phase 5A plan-presentation, 1 file): `docs(ui/investor-relations): path-to-100M deck refresh`
6. **Commit F** (Phase 5B board-presentation, 1 file):
   `docs(ui/investor-relations): board deck commercial-stack + cashflow slides`
7. **Commit G** (Phase 6 audit + fixes if found): `docs(codex/playbooks): cross-link audit + consistency fixes`

If any single commit rolls back / is absorbed by orchestrator, re-stage + re-commit with "(retry)" suffix. Do not batch
commits larger than ~15 files.

## Verification

1. **File count per dir check**: `ls codex/14-playbooks/commercial-model/*.md` = 9, `shared-core/` = 10, `experience/` =
   11, `demo-ops/` = 10.
2. **Link resolution**: every Markdown link with a `./` or `../` relative target resolves to an existing file (no broken
   relative links).
3. **Rule 01 grammar preserved**: every `experience/*.md` still has all 9 rule-01 sections.
4. **Rule 06 / IM_RESERVED consistency**: the 5 cell identifiers appear identically in all four canonical locations
   (codex playbook, codex strategy-v2, UI availability.ts, UI mock fixtures).
5. **Deck numerical consistency**: plan-presentation/data.ts end-2026 numbers match revenue-projection-2026-monthly.md
   cumulative end-of-year totals.
6. **UI tests green**: `npm test` pass.
7. **Typecheck clean**: `npx tsc --noEmit` clean on unified-trading-system-ui.
8. **Stage 2 scope respected** for Phases 2, 4, 5 (docs + data-only); Phase 3 is scoped UI data extension with explicit
   narrow blast radius (lock_state flags only; no UI logic changes).

## Success criteria (all phases)

- All 6 new docs exist and cross-link correctly to Stage 2 Stage 1 rules
- All 11 updated docs reflect the corrected commercial model
- Strategy catalogue renders IM_RESERVED correctly for admin vs demo personas
- Plan + board decks reflect reconciled 2026 trajectory, 2027 + 2028 adjusted, cashflow shape visible
- Commit SHAs pushed to origin/live-defi-rollout
- Memory updated
- Follow-up items queued in roadmap

## Risks + mitigations

| Risk                                                                    | Probability          | Mitigation                                                                                                                                      |
| ----------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Orchestrator drift wipes untracked files (observed in Stage 2)          | High                 | Small per-phase commits; push after each; recover from dangling blobs if wiped                                                                  |
| UI lock_state plumbing doesn't actually hide IM_RESERVED rows           | Medium               | Pre-audit verifies behaviour before marking Phase 3 complete                                                                                    |
| Plan doc exceeds 4k lines (compression risk)                            | Low                  | Split long docs; keep tables dense; use link hops for detail                                                                                    |
| Pricing numbers in revenue-projection doc leak to client-facing surface | High-impact-low-prob | Codex-private directory convention + explicit rule 08 note at top of doc                                                                        |
| Desmond slips past May                                                  | Medium               | Revenue slip ~£22-57k/month delay; cash buffer (£240k April opening) absorbs without stress                                                     |
| BTC ML strategy underperforms 2026                                      | Medium               | Platform-fee choice Option B ($500/mo floor) provides a partial hedge on 5 of 10 clients; year-end cash stays >£350k even in a flat BTC ML year |
| S&P ML signal slips past Sept                                           | Medium               | India Options $100k onboarding + CME Sept go-live both defer; pushes year-end cash from £464k to ~£330k; still healthy                          |
| CME client declines 70/10 asymmetric structure in negotiation           | Low-med              | Document flat-10%-of-both-sides fallback in `im-profit-share-structures.md`                                                                     |
