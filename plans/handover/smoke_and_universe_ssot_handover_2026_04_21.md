# Handover: Smoke Dep-Chain + Universe SSOT Architectural Fix — 2026-04-21

## Context (read this first)

Two plans landed 2026-04-21 under `plans/active/`:

1. **`smoke_dep_chain_tactical_fixes_2026_04_20.plan.md`** — Phase A tactical (SIT manifest filter, path-layout SSOT
   reconcile, launcher extensions for SPORTS+PREDICTION, stale default date, VM auto-shutdown, SIGKILL investigation,
   manifest v5 semantic docs, QG on all touched repos).

2. **`universe_ssot_fix_2026_04_20.plan.md`** — Phase B architectural drift. Instruments-service must be the SSOT for
   every venue's universe across all 5 categories. No MTDS adapter discovers symbols/markets at download time. Filters
   (UAC `capability_declarations` + `service_config`) apply ON TOP of the full universe — not as a replacement for
   universe discovery. Coverage = fetched / filtered_universe stays honest (100% possible even with a small MVP filter).

### Background — why these plans exist

2026-04-20 institutional smoke canary (first run of `launch-instruments-smoke-vm.sh` + `launch-canonical-smoke-vm.sh`
dep chain) surfaced 11 issues. 5 bucket-naming sites were fixed inline (commits: instruments-service@e6e50c7,
UTL@4ee91009, deployment-service@2163ec3, MTDS@1363e3f + @81b1b6f). CEFI × BINANCE-FUTURES × 2026-04-19 proved green
end-to-end (131 parquet written via Tier-0 → Tier-1 dep chain).

Remaining issues split into **tactical** (Phase A, in-session-shippable) and **architectural** (Phase B, multi-day per
venue class).

Critical architectural clarification from the operator:

- Filters (MVP subset) are correct as-is — NOT the problem
- Universe discovery happening at MTDS-runtime (via `/markets`, `/sports`, hardcoded SYMBOL arrays, inline UAC registry
  walks) is WRONG
- Every universe discovery should happen in instruments-service once per date and be written to GCS parquet; every
  downstream reads that parquet

## Phase A execution (single agent, ~2-3 hr)

**Prompt for Phase A agent:**

```
You are executing Phase A of the 2026-04-21 smoke dep-chain fixes plan at
unified-trading-pm/plans/active/smoke_dep_chain_tactical_fixes_2026_04_20.plan.md

Read that plan in full before starting. Execute the pending todos in order:

1. phase-a-sit-manifest-filter-tier-aware
2. phase-a-path-layout-ssot-reconcile
3. phase-a-launcher-sports-prediction
4. phase-a-stale-default-date
5. phase-a-vm-auto-shutdown
6. phase-a-sigkill-investigation
7. phase-a-tier-semantic-doc
8. phase-a-qg-all-touched-repos

Skip phase-a-verify-chain-all-categories — that's blocked on Phase B.

For each todo:
  - Read the current state of the referenced files
  - Ship code changes + corresponding test updates in the same commit
  - Run `bash scripts/quality-gates.sh` on the repo before committing
  - Commit with conventional-commit prefix (fix/docs/feat/chore as appropriate)
  - Push to live-defi-rollout branch
  - Flip the plan checkbox from `[ ]` to `[x]` and update the note field

Constraints:
  - DO NOT launch any VMs (those are Phase B verification only)
  - DO NOT do backwards compat — clean breaks per Citadel standards
  - DO NOT touch universe-discovery code (that's Phase B)
  - Inject SUB_AGENT_MANDATORY_RULES.md contents at top of every sub-agent prompt
    if you dispatch sub-agents
  - If you touch UAC/UTL/UCI/UEI, pre-audit downstream consumers per
    Citadel-Grade Planning Standards §6
  - Test-bucket convention: `-test-` in MIDDLE (between category and
    project_id) — SSOT: /codex/02-data/per-category-bucket-layouts.md

Deliverables on completion:
  - Every Phase A todo flipped to [x]
  - QG green on all touched repos
  - Commit list summary in chat with one line per commit (repo@sha → what)
  - Brief note flagging any issues discovered that are out-of-scope for
    Phase A (likely candidates for Phase B or a follow-up plan)

When done, post a comment on the plan file's frontmatter bumping status
from `active` to `active-phase-a-complete` (blocking further flip to
archive until Phase B green).
```

## Phase B execution (parallel sub-agents, ~3-7 days)

Phase B has 9 todos, 6 of which split cleanly per venue class and can run **in parallel** (B1 TradFi, B2
Hyperliquid+Aster, B3 Polymarket, B4 Kalshi, B5 Sports-bookmakers). B6 (remove preflight bypass) must run AFTER B1-B5.
B7 (DeFi pool universe) can run parallel with B1-B5. B8 (filter audit) can run any time. B9 (verification) is terminal.

### Parallelization graph

```
         ┌─ B1 (TradFi/Databento)      ─┐
         ├─ B2 (Hyperliquid + Aster)   ─┤
         ├─ B3 (Polymarket)            ─┤
         ├─ B4 (Kalshi)                ─┼─→ B6 (remove _VENUES_NEEDING_INSTRUMENT_PREFLIGHT) ─→ B9 (verify all 5 cats)
         ├─ B5 (Sports bookmakers)     ─┤
         └─ B7 (DeFi pools)            ─┘
                  ↕
         B8 (filter-model audit) ───────→ B9
```

### Per-venue-class agent prompt template (use for B1, B2, B3, B4, B5, B7)

Substitute `{VENUE_CLASS}` + `{TODO_IDS}` + `{ADAPTER_FILES}` per class.

```
You are executing {VENUE_CLASS} (todos {TODO_IDS}) of
unified-trading-pm/plans/active/universe_ssot_fix_2026_04_20.plan.md

ARCHITECTURAL PRINCIPLE (read carefully):
  instruments-service is the SSOT for every venue's instrument universe.
  No MTDS adapter should discover symbols/markets at download time. Every
  adapter reads pre-written instruments.parquet from GCS via
  `get_write_bucket_name("instruments", {category})`. Filters (UAC
  capability_declarations + service_config) apply ON TOP of the loaded
  universe — they DO NOT replace universe discovery.

Your scope — two commits per class:

  Commit 1 (instruments-service repo):
    - Add a new adapter under instruments_service/reference_data/adapters/{category}/{venue_class}_adapter.py
    - Adapter calls the venue's symbol/market API ONCE per batch, returns
      list[InstrumentRecord] with canonical instrument_key via UAC
      build_instrument_id(...), available_from_datetime, available_to_datetime
    - Wire adapter into the URDI factory (instruments_service/engine/urdi_reference_provider.py
      or the venue-specific factory site)
    - Honours IS_TEST_RUN=true → writes to -test- bucket via
      get_write_bucket_name
    - Output parquet at canonical path
      `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`
      (SPORTS is different — see /codex/02-data/per-category-bucket-layouts.md
      for the sports_reference/.../entity= tree)
    - Unit tests covering: happy path write, IS_TEST_RUN=true bucket
      routing, 0-row venue returns empty-confirmed not attempted-failed

  Commit 2 (market-tick-data-service repo):
    - Update MTDS adapter(s) at {ADAPTER_FILES} to read universe from
      `gs://instruments-store-{cat}-{test-or-prod}/instrument_availability/
      by_date/day={date}/venue={venue}/instruments.parquet` via
      get_write_bucket_name(..)
    - Delete any existing runtime API calls used for universe discovery
      (/markets, /sports, hardcoded SYMBOLS arrays, inline UAC walks)
    - Filters (UAC + service_config) apply post-read. If the venue has no
      filter configured, use the full loaded universe.
    - Do NOT touch tick-fetch logic — that keeps calling the venue's data
      endpoint as before
    - Update `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` frozenset to include
      your venue(s) if not already present
    - Unit + integration tests updated

Citadel rules:
  - Flat deps only (no [project.optional-dependencies])
  - No try/except ImportError fallbacks for library imports
  - No # type: ignore for architectural issues
  - basedpyright strict — fix types at the boundary
  - SSOT check: verify per-category-bucket-layouts.md reflects your new
    writes; update docs if your path layout differs
  - QG gate: `bash scripts/quality-gates.sh` must pass on both repos
    before commits

Deliverables:
  - 2 commits pushed to live-defi-rollout (one per repo)
  - Plan todos flipped to [x] with commit SHAs in the note field
  - Sub-agent report: what was built, what tests pass, any venues that
    can't be fetched automatically (e.g. paid API requires key that isn't
    in ApiKeyReloader — flag as follow-up todo)
```

### B6 handover prompt (runs after B1-B5 all green)

```
All of B1-B5 are green. Every venue class now has instruments.parquet
writes + MTDS reads via get_write_bucket_name.

Remove `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` from
market-tick-data-service/market_tick_data_service/engine/orchestrator.py.
Replace with unconditional per-venue pre-flight via
`_check_instruments_available(venue, date)`. Shard-level isolation still
applies (raise-never inside the venue loop) — a missing instruments.parquet
for one venue must not abort the others; log + record_failed + continue.

Update the orchestrator pre-flight call site to run for every active
venue in the batch. Keep `force=True` CLI flag wired through to bypass
the check when an operator explicitly wants to ignore missing upstream.

Tests: update or add unit tests that verify:
  1. All venues (sampled across 5 categories) hit pre-flight
  2. Missing instruments.parquet for venue X fails ONLY venue X (not the batch)
  3. force=True bypasses per-venue (not per-batch)

QG green + commit + push + flip plan checkbox.
```

### B7 (DeFi pool universe) — follow-up

Parallel-safe with B1-B5. See plan todo `phase-b7-defi-pool-universe` for scope. DeFi lending_indices already works;
this adds the pool/swap universe needed for Uniswap/Balancer tick ingest.

### B8 (filter-model audit + new doc)

Can run any time — creates a new codex doc at `/codex/02-data/universe-and-filter-model.md` documenting the canonical
pattern (universe discovery → filter → fetch → coverage). Also audits all filter call sites to confirm they run AFTER
universe load, not IN the adapter.

### B9 (verification)

**OPERATOR task** — runs from a laptop with gcloud ADC:

```bash
# 1. Refresh tarballs (instruments + MTDS)
/opt/homebrew/bin/bash deployment-service/scripts/vm/create-code-tarballs.sh --all

# 2. Launch Tier-0 for each of 5 categories (parallel, ~15 min)
bash deployment-service/scripts/vm/launch-instruments-smoke-vm.sh all 2026-04-20

# 3. Wait for all 5 Tier-0 VMs to exit — see phase-a-vm-auto-shutdown item
#    (after Phase A this is automatic; until then poll via gsutil)

# 4. Launch Tier-1 for each of 5 categories (parallel, ~20 min)
bash deployment-service/scripts/vm/launch-canonical-smoke-vm.sh all 2026-04-20

# 5. For each category, assert:
#    - instruments.parquet exists at day=2026-04-20 canonical path
#    - ticks.parquet(s) exist at day=2026-04-20 canonical path
#    - Manifest row for (date, venue, data_type) has
#      capture_status in {captured, empty_confirmed}
```

Expected cost: ~$3-5 in VM-hours for full 5-category × 2-tier matrix run.

## Cross-cutting rules for every agent

- **Branch**: live-defi-rollout
- **Commit style**: conventional commits (feat / fix / docs / chore / refactor)
- **Commit co-author footer**: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
- **No `--dep-branch`, no `--force-push`** (rule from workspace CLAUDE.md)
- **Pre-commit hook failures**: investigate + fix the underlying issue; do NOT use `--no-verify` unless explicitly
  authorised
- **Concurrent agents**: `git pull --rebase origin live-defi-rollout` before push. Stash local uncommitted first if
  needed.
- **Plan lock**: both plans have `locked_by: live-defi-rollout`. Do NOT archive or delete plan files without
  `[unlock-plan]` tag in commit.

## Report back

Each agent: on completion, post to this file (append under `## Agent Reports`) with format:

```
### {Agent ID} — {date} — {status}
Phase: {A | B1 | B2 | ...}
Commits:
  - {repo}@{sha} — {one-line description}
  - ...
Outcomes:
  - {what works now}
Open issues:
  - {what broke / what's blocked / what needs a follow-up plan}
```

## Agent Reports

(agents append below)
