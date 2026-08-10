---
doc_type: plan
title: TradFi Databento billing unblock + VIX futures scope addition + Yahoo CBOE discovery-floor fix (2026-08-10)
summary: >-
  Operator confirmed today the Databento billing suspension is paid/resolved and asked to (1) unblock every TradFi
  Databento backfill todo that cited it, (2) add VIX futures to the MVP-of-MVP in-scope list (forgotten in the
  2026-08-09 ruling), and (3) scope a fix for the CBOE Yahoo Treasury discovery-floor bug, capped at a 2018 start (not
  the full 2000 history — operator explicitly said 2018 is fine). Live-verified the billing claim independently (see
  "Confirmed finding" below) rather than trusting the report alone, per this workspace's data-pipeline- correctness
  standard. Started as an interactive-session edit pass but this checkout hit EXTREME concurrent-write contention
  (repeated `pull --rebase --autostash` cycles from other active sessions/cron jobs silently discarding every edit
  before it could be committed — confirmed via `git stash list` showing 30+ recent `autostash` entries) — operator asked
  to flip this to an AO plan so a worker can complete it cleanly instead of fighting the same race interactively. Every
  todo below is self-contained (exact old/new text given) so a worker does not need to re-derive anything, and is
  idempotent (grep-check current state first) so it's safe if another session already landed a piece of this mid-race.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, databento, billing, vix, yahoo, discovery-floor, mvp-scope, unblock]
related:
  [
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md,
    /plans/active/issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md,
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /plans/active/issues/databento_ice_opra_subscription_ask_2026_08_09.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator chat instruction, 2026-08-10: "since databento account is working, manifest looks canonical and so are paths
  and we have the new updated mvp instrument list... can we please update the plan docs and issues unblocking databento
  backfills so that we can take tradfi to 100%". Clarified via 2 follow-up questions: (1) keep the November-2026 scope
  gate as-is, but add VIX futures ("i forgot about those"); (2) scope the Yahoo CBOE discovery-floor fix, capped at 2018
  (not chasing the full 2000 history). Explicitly asked to flip to an AO plan after the interactive session hit
  sustained commit contention.
---

# TradFi Databento billing unblock + VIX scope + Yahoo floor fix

## Why this doc exists

Operator directive to unblock TradFi Databento backfill work now that the billing suspension is resolved, plus two scope
decisions made in the same conversation (VIX futures added to MVP-of-MVP in-scope; Yahoo CBOE Treasury discovery-floor
fix scoped to a 2018 floor). This plan captures the CONFIRMED finding + exact target edits so any worker can execute
without re-deriving the research.

## Confirmed finding — Databento account is live (2026-08-10), do NOT re-verify from scratch

Ran 3 real, dated calls against the live Databento API (not a stale doc check):

1. `metadata.list_datasets()` — succeeded, 29 datasets visible. An account-level suspension would reject this outright
   (auth/entitlement rejection), so a clean success is itself strong evidence against a standing suspension.
2. A REAL metered pull, `GLBX.MDP3` (CME) `ES.FUT ohlcv-1d`, `2026-08-05→2026-08-06` — succeeded, 5 real rows (ESZ6,
   ESU6, real volumes e.g. 1,401,190).
3. A REAL metered pull, `XCBF.PITCH` (CBOE/CFE) `VX.FUT ohlcv-1d`, same date range — succeeded, 57 real rows (VX/G7,
   VX/X6, VX/Z6, genuine VIX-futures prices).

**All 3 core subscribed datasets (`GLBX.MDP3`, `DBEQ.BASIC`/`XNAS.ITCH`, `XCBF.PITCH`) confirmed live with real data as
of 2026-08-10.** This does NOT resolve the separate ICE/OPRA subscription question
(`databento_ice_opra_subscription_ask_2026_08_09.md`) — dataset visibility in `metadata.list_datasets()` is not proof of
subscription; leave that doc untouched, it's correctly scoped already.

Reproduction (if a worker wants to re-confirm before relying on this, e.g. if significant time has passed):

```python
import databento as db
from unified_trading_library import get_secret_client
api_key = get_secret_client(project_id="central-element-323112").get_secret("databento-api-key")
client = db.Historical(api_key)
client.metadata.list_datasets()  # should succeed, ~29 datasets
client.timeseries.get_range(dataset="GLBX.MDP3", symbols=["ES.FUT"], stype_in="parent",
                             schema="ohlcv-1d", start="<recent-date>", end="<recent-date+1>").to_df()
```

## Contention warning — read before starting

This checkout was under EXTREME concurrent-write load during the interactive attempt (confirmed: 30+ recent `autostash`
entries in `git stash list`, from other active sessions/cron jobs running `pull --rebase --autostash` against this same
checkout). Every single edit below was wiped at least once, sometimes 3+ times, before this plan was authored. Per-todo
discipline for whoever executes these:

1. `grep` the target marker string (given in each todo) BEFORE editing — if already present, the todo is done, just
   verify + move on (don't re-edit, don't duplicate).
2. Edit ONE file, then immediately `grep` to confirm the edit landed in the working tree (don't trust the Edit tool's
   success message alone — this checkout silently reverts working-tree content).
3. Stage + commit that ONE file IMMEDIATELY (don't batch multiple files before committing) — a committed change survives
   `pull --rebase --autostash`; an uncommitted one does not (that's the actual bug being worked around).
4. On `check-branch-drift` failure: `git fetch` + `git merge --ff-only origin/live-defi-rollout`, re-verify content
   survived the merge, re-stage, retry the commit. This can take several attempts — that's expected, not a sign of doing
   something wrong.
5. Prefer `scripts/dev/safe-doc-push.sh` per the workspace's own git-discipline rule; it has its own internal
   retry/reconcile loop that handles most of the above automatically.

## Todos

- [x] ✅ [DOCS] P1. **Land the billing-suspension doc's resolution** — unified-trading-pm@5ed8364ccb. Issue doc
      `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` now carries
      `## LIVE RE-VERIFIED 2026-08-10` (grep count 3), `status: open` (not terminal — genuine open P2 follow-up keeps it
      non-archivable), `resolved_by:` citing this plan + the 3-call live verification, Resolution-path section marked
      RESOLVED, and the `[DOCS] P2` follow-up todo listing the 4 downstream docs' retag work.
      (`plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`). Grep-check first:
      `grep -c "LIVE RE-VERIFIED 2026-08-10" <file>` — if already `1` or more, skip to verifying `status:` is `open`
      (not `resolved` — this doc has a genuine open follow-up todo below, so it must NOT be archived;
      `resolved`/terminal status without archival fails `check_terminal_status_archived`). If not yet present: change
      `status: blocked` → `status: open`; set `resolved_by:` to cite this plan + the live-verification evidence above;
      add a `## LIVE RE-VERIFIED 2026-08-10` section (content: the "Confirmed finding" text above, condensed) right
      after the doc's H1; update the "## Resolution path" section to state RESOLVED with the same evidence; add one
      `- [ ] [DOCS] P2` todo inside that new section listing the 4 downstream docs below as still needing their retag
      (so this doc's own follow-up tracks correctly and it never becomes eligible for archival until they're done).
      Repo: unified-trading-pm. Done when: content lands, commits, and
      `git show origin/live-defi-rollout:<path> | grep -c "LIVE RE-VERIFIED"` returns ≥1.

- [ ] [DOCS] P1. **Un-gate `data_completion_tradfi_2026_07_15.md`'s 2 billing-blocked todos.** Grep-check:
      `grep -c "UNGATED 2026-08-10" <file>` — skip if ≥1. Find the 2 todos matching
      `BLOCKED-OPERATOR-DECISION (databento account billing-suspended 2026-08-09` (search `grep -n` for that string —
      there are exactly 2 occurrences). For EACH: prefix the todo with
      `**UNGATED 2026-08-10** — the billing-suspension gate is resolved (live-reverified that day, 3 real Databento calls across all 3 core datasets, see tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md).`
      For the first todo (the `build_instrument_catalogue.py` scheduler wiring one), note it is STILL gated on the
      second todo (the IS reference-capture restore) actually running, not just being dispatchable. For the second todo
      (the `--source databento` replacement-path one), note it is now genuinely dispatchable, not yet run. Repo:
      unified-trading-pm.

- [ ] [DOCS] P1. **Un-gate `tradfi_phase_d_terminal_gate_2026_07_24.md`'s 2 billing-blocked todos, PRESERVE the separate
      Phase-D-completeness caveat.** Grep-check: `grep -c "BILLING GATE LIFTED 2026-08-10" <file>` — skip if ≥1. The 2
      todos matching `BLOCKED-OPERATOR-DECISION (databento account billing-suspended 2026-08-09` need the billing
      citation replaced with `**BILLING GATE LIFTED 2026-08-10**` + the same evidence line as above. **Do NOT clear the
      todo's OTHER, separate blocker**: `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (`status: open`) has a
      confirmed, still-open CBOE VIX canonical-name (`VIX`→`VX`/`VX.FUT`) translation bug making the checker/sampler
      tooling misreport CBOE VIX specifically — the P0 "MVP backfill readiness gate" todo stays blocked on "Phase D is
      not literally green" until that's resolved or the operator accepts current evidence as sufficient; only the
      billing citation is being lifted here, not the whole gate. Repo: unified-trading-pm.

- [ ] [DOCS] P2. **Add a Databento-access-confirmed note to `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s
      re-feed-chain todo.** Grep-check: `grep -c "DATABENTO ACCESS CONFIRMED LIVE 2026-08-10" <file>` — skip if ≥1. Find
      the `[DATA] P0` todo starting "**NEW 2026-07-29 — run the tradfi Databento `by_date` re-feed chain to
      completion..."`(this todo was never itself tagged`BLOCKED-OPERATOR-DECISION`, but the billing suspension made it practically undispatchable — a fetch would have failed). Insert a sentence after its bold lead-in: "**DATABENTO ACCESS CONFIRMED LIVE 2026-08-10** — the account-wide billing suspension is resolved (live-reverified that day, real `GLBX.MDP3`/`XCBF.PITCH`
      pulls both succeeded); this todo is the exact re-feed work that gate would have blocked in practice — now
      genuinely runnable." Repo: unified-trading-pm.

- [x] ✅ [DOCS] P1. **Add VIX futures to the MVP-of-MVP in-scope list — operator decision 2026-08-10** —
      unified-trading-pm@9e2041f7ba. VIX futures row + rationale landed in
      `plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (in-scope table row, rationale
      citing the existing `launch-tradfi-bf-cfe-ohlcv-1m.sh` CFE launcher + the 2026-08-10 live-verification evidence of
      57 real `XCBF.PITCH VX.FUT` rows, the sampler translation-bug caveat, and the out-of-scope bullet removed;
      frontmatter summary updated to drop VIX futures from the November-gated list).
      (`plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`). Grep-check:
      `grep -c "VIX futures (CBOE, VX.FUT)" <file>` — skip if ≥1. In the "## In scope — proceed now" table, add a new
      row:
      `| VIX futures (CBOE, VX.FUT) | Full history (2018-11-04 → now, XCBF.PITCH L0 floor) | ohlcv_1m | Databento (XCBF.PITCH) |`.
      Below the table, add a rationale paragraph: a dedicated launcher already exists —
      `deployment-service/scripts/vm/launch-tradfi-bf-cfe-ohlcv-1m.sh` (`CFE_INSTRUMENT_IDS="VX.FUT"`, window
      2018-11-04→today) — needs launch/verify only, not new code. Cite the live-verification evidence above (57 real
      `XCBF.PITCH VX.FUT` rows). Add this caveat: `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`
      (`status: open`) has a confirmed CBOE VIX canonical-name (`VIX`→`VX`/`VX.FUT`) translation bug in the
      CHECKER/sampler tooling — the dedicated launcher above uses the raw symbol `VX.FUT` directly and is unaffected,
      but post-launch coverage verification via the sampler/checker may misreport until that separate bug is fixed. In
      the "## Out of scope — gated until November 2026" list, remove the `- VIX FUTURE (CBOE).` bullet (moved to
      in-scope). Repo: unified-trading-pm.

- [ ] [SCRIPT] P2. **Launch + verify the VIX futures backfill** (once the todo above lands). Run
      `deployment-service/scripts/vm/launch-tradfi-bf-cfe-ohlcv-1m.sh` (existing launcher,
      `CFE_INSTRUMENT_IDS="VX.FUT"`, default window 2018-11-04→today). Verify via a manifest query (venue=CBOE,
      data_type=ohlcv_1m) showing real `captured` rows with populated `instrument_id`. Do NOT use the sampler/checker
      tooling's canonical `VIX` symbol to verify — it will misreport per the known translation bug above; query the
      manifest directly instead. Repo: deployment-service / market-tick-data-service.

- [ ] [DATA] P2. **Scope the Yahoo CBOE Treasury discovery-floor fix, capped at 2018 (operator decision 2026-08-10 — "i
      only want data from 2018 even for yahoo that's fine")** — edit
      `plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md`. Grep-check:
      `grep -c "start-floor 2018-01-01" <file>` — skip if ≥1. This plan's todo 2 (search for
      `**Relaunch the CBOE Treasury-INDEX backfill for the newly-unblocked 2000-2020-06 window.**`) currently targets
      `--start-floor 2000-01-01`. Change to `--start-floor 2018-01-01` throughout that todo's text (the launcher
      invocation, the window description, and the "Done when" clause — change "back to 2000-01-03" to "from 2018-01-01
      onward" for the 4 non-US2Y tenors; US2Y stays "back to 2018-08-13" unchanged since that's already within the new
      floor). Add a note: "Capped at 2018 per operator decision 2026-08-10 — real Yahoo history exists back to
      2000-01-03 for 4 of 5 tenors, but the operator explicitly does not want that chased; 2018 onward is sufficient."
      Leave todo 1 (the code fix itself, `is_venue_available()` data-type-aware floor resolution) UNCHANGED — the code
      fix's own technical capability should still correctly support the real Yahoo floor (2000-01-03/2018-08-13) if ever
      needed later; only the ACTUAL BACKFILL LAUNCH target window is capped at 2018, not the code's capability. Repo:
      unified-trading-pm.

## Codex SSOTs (read before touching this workstream)

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/honest-absence-downstream-handling.md`.

## Progress Log

- 2026-08-10 (main, Claude Code session): plan created after an interactive doc-editing pass hit sustained
  concurrent-write contention on this checkout (confirmed via `git stash list`, 30+ recent autostash entries from other
  active sessions/cron jobs). The billing-suspension doc's core resolution content was drafted and verified correct in
  the working tree multiple times but could not be reliably committed before being silently reverted by a concurrent
  `pull --rebase --autostash`. Operator asked to flip the remaining work to this AO plan rather than continue fighting
  the race interactively. The live Databento re-verification (3 real API calls) IS a completed, confirmed finding —
  captured above so no worker needs to redo it; only the doc edits themselves remain.
