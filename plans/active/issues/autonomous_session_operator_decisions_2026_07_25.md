---
doc_type: issue
title: Autonomous session 2026-07-25 — queued operator decisions
summary: >-
  Single running log of every genuine operator-decision-caliber question surfaced during the 2026-07-25 /autonomous
  session (plan-of-record: ag_closeout_audit_rollout_2026_07_25.md). Per the operator's explicit instruction at session
  start ("you have to ask me operator questions for decisions... so that i can answer when im back"), these are QUEUED —
  never blocked on — and the session keeps working on everything else. Each entry follows the
  SUB_AGENT_MANDATORY_RULES.md escalation format (options + a marked recommendation). Operator: answer inline under each
  entry (or via chat) when back; unanswered entries stay open.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction, sports, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [autonomous, operator-decision, ag-closeout-audit]
related:
  - /plans/active/ag_closeout_audit_rollout_2026_07_25.md
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: agent_operating_framework_master
assigned_vm:
priority: P1
locked_by:
resolved_by:
source: >-
  Operator instruction 2026-07-25 immediately after /autonomous invocation: queue genuine decisions instead of silently
  deciding or blocking.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Autonomous session 2026-07-25 — queued operator decisions

## 1. `git rm` 2 stale-duplicate stub files (2026-07-25, sports archival)

Not a judgment call — a mechanically-safe delete blocked by a hard guardrail
(`agent-orchestrator/scripts/hooks/block_destructive_commands.py`) that forbids `git rm` for autonomous workers,
correctly. A concurrent commit (`9aed72662`, unrelated tradfi work) picked up the ADD half of a `git mv` archival rename
but not the DELETE half, leaving stale full-content duplicates at the OLD paths alongside the correct archived copies.
Both stale files were overwritten with an explicit `⚠️ STALE DUPLICATE` stub + a queued `[OPERATOR]` todo (so they're
self-explanatory and harmless in the meantime) rather than left as confusing full duplicates.

A:
`git rm plans/active/sports_closeout_batch1_finalize_2026_07_24.md plans/active/data_completion_sports_history_2026_07_24.md`
— removes both stub files; the real content already lives at `plans/archive/2026_07/`. [WORKER REC] B: Leave the stubs
in place — they're self-documenting and harmless, just slightly noisy in `plans/active/`. Other: operator can type a
custom answer

**Operator answer (2026-07-25)**: A — delete both.

**Status**: resolved — both files `git rm`'d, real content confirmed intact at `plans/archive/2026_07/`.

---

## 2. `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` — locked doc, audit says resolved (2026-07-25, defi)

The defi orphan-audit classified this doc `archivable_now`: its own latest section (2026-07-12) claims one item still
open (`e2e-testing/staked_basis_funding_scan.py`'s `_lst_bucket()`/`_read_lst_exchange_rate` reader), but that claim
looks stale — sibling plan `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s Todo 3 (checked `[x]`, 2026-07-13)
explicitly fixed that exact function, with a live-verified post-deploy parity todo (2026-07-13/14: "e2e
`_read_lst_exchange_rate` LIDO 1.2333 + JITO 1.2766 ... zero reads left on the dedicated buckets"). I did NOT flip this
doc's frontmatter — it carries `locked_by: live-defi-rollout` (`locked_since: 2026-05-21`), an explicit human "not
yours" signal per CLAUDE.md's plan-locking rule, which I'm treating as applying here even though this is an issue-doc
status flip, not a plan archival — the lock predates this session and I have no context on why it's held.

A: `[unlock-plan]` + flip `status: resolved` with
`resolved_by: <the defi_dedicated_bucket_shared_migration commit that shipped Todo 3>` — the evidence looks solid, this
just needs the lock cleared first. [WORKER REC] B: Leave locked and open — the lock may be protecting something I don't
have context on (e.g. active investigation, pending a different fix). Confirm with whoever set the lock before touching
it. Other: operator can type a custom answer

**Operator answer (2026-07-25)**: A — unlock + mark resolved.

**Status**: resolved — unlocked, `status: resolved`,
`resolved_by: defi_dedicated_bucket_shared_migration_2026_07_13.md Todo 3 (e2e-testing@3d219d76)`, RESOLVED section
appended to the issue doc.

---

## 3. Kamino/Solend `lending_indices` `instrument_type` shape — writer code vs live GCS probe disagree (2026-07-25, defi)

`issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`'s follow-up todo ("does the
dex_pools-class fake-history-snapshot bug also affect Kamino/Solend Solana lending_indices in the `-prd-` bucket")
asserts the CORRECT real path shape to probe is `instrument_type=solana_lending`, citing
`market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py::resolve_lending_instrument_type()`
as ground truth (Kamino/Solend resolve to `InstrumentType.SOLANA_LENDING`). But
`defi_consolidated_closeout_2026_07_18.md`'s Track 2 independently reports a 2026-07-20 live GCS probe finding a KAMINO
`lending_indices` canonical twin (47 objects) actually sitting under `instrument_type=solana_amm_pool` at
`day=2026-04-14` — a THIRD, different path shape from both the already-known-wrong `instrument_type=pool` and this
todo's targeted `solana_lending`. Neither doc has cross-checked the discrepancy against the other. The conflict-check
run over the 2026-07-25 defi satellite AO-eligibility triage explicitly flagged this as needing operator sign-off rather
than a silent reconciliation — if a worker probes only `solana_lending` as originally scoped, it risks filing a false
"clean bill" finding while missing the population Track 2 actually found live under `solana_amm_pool`.

A: Widen the todo's scope to ALSO probe `instrument_type=solana_amm_pool` for KAMINO/SOLEND before filing any "clean
bill" finding, explicitly reconciling against Track 2's 2026-07-20 47-object finding. [WORKER REC] B: Dispatch the todo
exactly as scoped (probe only `solana_lending`) and accept the risk that the finding may be incomplete if real
Kamino/Solend `lending_indices` data actually lives under `solana_amm_pool` instead. C: Hold this todo out of any AO
batch entirely and rule directly on which `instrument_type` shape (`solana_lending` vs `solana_amm_pool`) is
authoritative for Kamino/Solend `lending_indices`, since the writer code and the live GCS probe currently disagree.
Other: operator can type a custom answer

**Operator answer (2026-07-25)**: A — widen scope to probe both paths before concluding.

**Status**: resolved — widened as item 6 in
`issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` and dispatched as a Todos-section item
in `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (moved out of that plan's Deferred section).

---

## 4. Whether/when to execute the `perp_funding` demote-to-derived-view design decision (2026-07-25, defi)

`issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`'s `[DESIGN] P1` todo (line
164-186) proposes demoting `perp_funding` from a captured raw data_type to a DERIVED interval view (computed from
`derivative_ticker`, now the canonical raw-funding home for all perps) — for interval-native sources (Hyperliquid REST,
GMX events) the two are literally the same rows written twice. The todo is explicitly self-tagged `[OPERATOR-DECISION]`
per its own 2026-07-25 reconciliation note: it was originally gated on a cross-source funding-parity check, but that
check (todo 4 in the same doc) closed `[x]` **MOOT 2026-07-16** (DRIFT removed platform-wide) with **no parity data ever
collected** — the gate can never resolve as literally written. Before executing the DESIGN decision, either (a) a fresh
re-scoped parity todo must be filed and its results awaited, or (b) the operator rules directly whether parity evidence
is still required before demoting `perp_funding`.

Blast radius if demoted: `perp_funding` is read live by `CanonicalPerpFundingProvider`
(`strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py`), instantiated by the live
paper-trading CLI (`paper_run_handler.py:931-932`); it's also one of `mvp_backfill_defi_onchain_v10`'s 6 MVP-gate
data_types with months of manifest history (re-homing the coverage denominator is non-trivial); and features-onchain's
`perp_funding` bypass read would need migrating. This decision also determines whether
`issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`'s own separate `[OPERATOR-DECISION] P3` todo
(whether `perp_daily_ctx`/mark-price should be folded into the same demotion) has an answer to fold into.

A: File the re-scoped cross-source funding-parity todo first (surviving venues: HYPERLIQUID/ASTER — GMX removed
2026-07-25 per `defi_gmx_venue_removal_2026_07_25.md`, DRIFT/PACIFICA already removed) and gate the demote decision on
its results — matches the original design's own evidence-first intent, no live-reader risk taken without proof. [WORKER
REC] B: Rule directly now that parity evidence is NOT required — proceed straight to scoping/executing the
demote-to-derived-view migration (re-home the MVP-gate accounting, migrate the features-onchain bypass read, retire
`perp_funding` raw capture). C: Rule directly now that `perp_funding` stays a permanently separate captured raw type
(keep dual-capture; close the DESIGN todo as "keep both — no parity check needed"). Other: operator can type a custom
answer

**Status**: open

---

## 5. Transfermarkt golden-window re-attempt vs. Sports P2b full-history extension (2026-07-25, sports)

`data_completion_sports_2026_07_24.md` carries an AO-eligible candidate: re-launch the instruments-service Transfermarkt
PLAYER_VALUES backfill scoped to the golden window (2025-09-01→2025-11-30) with skip-fresh so only the 256
`attempted_failed` cells (as of the 2026-06-24 measurement) are re-attempted, then re-measure. This sits on the exact
same ground as `sports_consolidated_closeout_2026_07_19.md`'s own OPEN todo "Sports P2b" (line ~869), which lists
transfermarkt among the 6 sources whose golden-window-proven honest-coverage recipe gets extended to full 2015→present —
a full-history re-fetch would necessarily re-attempt (and likely subsume) these same 256 cells, but via a much larger,
not-yet-started, differently-scoped sweep. Re-verified 2026-07-25 (batch4 re-triage): P2b is still `[ ]` open, no
transfermarkt-specific work has landed against it, and no other active/dispatched batch (batch2's 9 remaining todos,
batch3's 12) touches this ground.

`consolidated_todo_quote` (sports_consolidated_closeout_2026_07_19.md:869-872): "Sports P2b — reference sources + odds
history 2015→present, never started. Extend the golden-window-proven honest-coverage recipe (weather,
soccerfootball_info, transfermarkt, understat, footystats, odds-api) to full 2015→present within each source's own
`coverage_start`; season-aware smart-skip only (typed `EXPECTED_*` reasons, never blanket re-fetch)."

A: Dispatch the narrow golden-window-scoped relaunch now — it's cheap (256 cells, one launcher run), read-write only to
already-known-failed cells, and poses no correctness risk: whenever P2b eventually runs, its smart-skip logic will
simply no-op the cells this todo already resolved. The only cost of doing both is a few redundant re-attempts of cells
already `captured`, not a conflict. [WORKER REC] B: Hold this specific relaunch until P2b is actually scheduled/staffed,
so the golden-window fix and the full-history extension ship as one coherent pass instead of two. Other: operator can
type a custom answer

**Status**: open

---

## 6. ODDS+PREDICTIONS blank-reason golden-window measurement vs. Sports P2d/R1-R3 final gate (2026-07-25, sports)

`data_completion_sports_2026_07_24.md` also carries an AO-eligible candidate: re-measure the current golden-window
(2025-09-01→2025-11-30) ODDS+PREDICTIONS blank-reason `empty_confirmed` residual (~3,062/3,078 as of the 2026-06-24
measurement, later ~3,255 combined) against the live manifest, and file (not implement) a scoped issue doc capturing the
root cause + fix options. This sits on the same ground as `sports_consolidated_closeout_2026_07_19.md`'s own OPEN "FINAL
full-history zero-missing (R1/R2/R3)" gate (line ~897), whose explicit pass criterion includes "0 blank-reason" cells
for every (source, data_type) within coverage windows — the same defect class, but framed as part of the master plan's
full-history-gated final verification rather than a golden-window-scoped diagnostic. Re-verified 2026-07-25: the
R1/R2/R3 gate is still `[ ]` open, "BLOCKED-PREREQUISITES, bounced 6× as of last check" — nothing has re-run it.

`consolidated_todo_quote` (sports_consolidated_closeout_2026_07_19.md:897-900): "FINAL full-history zero-missing
(R1/R2/R3) — BLOCKED-PREREQUISITES, bounced 6× as of last check. Gate: 0 `expected_unattempted_pending_fetch`, 0
blank-reason, 0 un-evidenced `attempted_failed` for every (source, data_type) within coverage windows, plus features
ML-ready."

A: Dispatch the measure-and-file candidate now — it is explicitly read-only/diagnosis-only (no code or manifest change,
per the candidate's own scope), and its output (a scoped issue doc with root cause + undecided fix options) is a strict
superset of useful input for whoever eventually re-runs the R1/R2/R3 gate — it cannot regress or race that gate. [WORKER
REC] B: Hold until the R1/R2/R3 gate is actually re-run, so the diagnosis happens in the context of the full gate re-run
rather than as a standalone golden-window snapshot that may need re-doing. Other: operator can type a custom answer

**Status**: open

---

## 7. Fixtures legacy-path census vs. Track S/Track E/C1's entangled restamp residual (2026-07-25, sports)

`sports_legacy_fixtures_path_migration_2026_07_24.md`'s one AO-eligible candidate (a read-only, no-write per-date/
per-league census across all 2,319 post-floor dates, confirming the exact load-bearing legacy-`entity=fixtures/` subset
via real GCS object reads) carries 3 flagged conflicts against `sports_consolidated_closeout_2026_07_19.md`'s own OPEN
ground, all re-verified still open 2026-07-25:

1. Track S (line 419-420): "Eliminate (or document) the legacy bare `entity=fixtures/` (no `pipeline_mode=`) write path
   still active today alongside the canonical split writer (5-league subset)." — if this writer is still live, newly
   written legacy data could repopulate the path after any migration completes.
2. Track E (line 444-449): "Repoint the remaining stale `entity=fixtures` consumers (sweep §R's ~9-file list: ...)." —
   worth confirming these are genuinely disjoint call sites from the target doc's own `sports_fixtures.py` fallback-
   removal work, not two plans independently repointing overlapping consumers.
3. Track C1 (line 274-282, checked `[x]` but explicitly PARTIAL): "C1 — migrated the fixtures manifest atom ... PARTIAL
   — 282,231/337,464 legacy rows restamped; 55,233 dedup-key collisions could NOT be safely restamped — tracked open:
   `issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md` (both open, correctly not resolved)." — the
   census's population (filtered on the now-shrunk `data_type=="FIXTURES"` set) could systematically miss load-bearing
   rows already bulk-relabeled to `FIXTURES_SCHEDULE` without their physical GCS object ever moving; re-verified
   2026-07-25 that `fixtures_manifest_duplicate_collision_residual_2026_07_24.md` is still `status: open` with no
   operator DELETE-policy ruling yet made.

The candidate task itself is read-only (no PROD write/delete), so dispatching it carries no direct correctness risk to
Track S/E's still-unwritten migration work — but its census methodology needs to correctly account for the C1
partial-restamp population (point 3) to avoid producing a misleading "load-bearing" count, and its output is the direct
input the eventual gated migration (human-only, already excluded from AO dispatch) will consume.

A: Dispatch the census now, WITH an explicit scope correction folded into its Done-when: the census must count a
manifest row as "canonical empty" only after confirming via a real GCS object read (not the manifest's
`data_type=="FIXTURES_SCHEDULE"` label alone) — this closes the exact gap point 3 flags, since a label-only restamped
row with no physical object move would otherwise be miscounted as "already covered." [WORKER REC] B: Hold the census
until the operator rules on the 55,233-row DELETE-policy question in
`fixtures_manifest_duplicate_collision_residual_2026_07_24.md` first, so the census's scope and the eventual migration
plan are designed together in one pass instead of the census possibly needing a re-run. Other: operator can type a
custom answer

**Status**: open

---

## 8. Phantom-audit STANDINGS/TEAMS residual vs. Track S2 decision-16 day-partition investigation (2026-07-25, sports)

`sports_phantom_audits_reference_not_marketdata_2026_07_14.md`'s one AO-eligible candidate (spot-check + classify the
1,229-row phantom residual across STANDINGS/TEAMS/XG/MATCHES/FIXTURES as false-positive vs. genuine-phantom) may share a
root cause with `sports_consolidated_closeout_2026_07_19.md`'s own still-OPEN Track S "decision 16" item (line 430-434),
which investigates STANDINGS/TEAMS season-2026 data being written under historical `day=` partitions across ~3,050 days
in both buckets — a write-side day-mismatch would produce exactly the kind of exact-day phantom flags the target doc's
residual describes. Re-verified 2026-07-25: decision 16 is still `[ ]` open, no root-cause investigation has landed
against it, and the target doc's own STANDINGS (460)/TEAMS (460) rows are still explicitly "not checked" (no dated
update since the 2026-07-23 RE-TRIAGE). No cross-reference exists between the two docs.

`consolidated_todo_quote` (sports_consolidated_closeout_2026_07_19.md:430-434): "NEW 2026-07-23 (decision 16) —
investigate 2 unfiled loose ends from the OR-1 investigation. (1) standings/teams season-2026 data being written under
historical `day=` partitions across ~3,050 days in both buckets; (2) an unidentified writer producing a cartesian-junk
`player_values` object on 2026-06-22. Root cause unknown for both — operator decision: investigate now rather than
deferring, since both are currently unowned and could be actively recurring."

This is a genuine ambiguity (same population, two different framings, no evidence either way to say whether they're the
same defect) — not resolvable from evidence alone.

A: Merge into one investigation — dispatch decision 16's day-partition root-cause dig FIRST (it's the deeper, causal
question), and fold the phantom-audit doc's STANDINGS/TEAMS spot-check into it as a corroborating data point rather than
a separate classification pass. [WORKER REC] B: Keep them as two separate, independently-dispatchable investigations
(the phantom-audit spot-check is narrower/cheaper and could surface useful signal before decision 16's deeper dig
starts). C: Dispatch the phantom-audit spot-check now as originally scoped, and treat any STANDINGS/TEAMS finding it
produces as an input to decision 16 rather than a competing conclusion. Other: operator can type a custom answer

**Status**: open

---

## 9. `sports_consolidated_closeout_2026_07_19.md` is over the 1000-line hard cap — split or promote to epic? (2026-07-25, sports)

`plans/active/sports_consolidated_closeout_2026_07_19.md` is 1002 lines
(`bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_consolidated_closeout_2026_07_19.md` →
`HARD sports_consolidated_closeout_2026_07_19.md 1002L todos=104` →
`❌ check_line_caps: 1 staged plan(s)/epic(s) over cap`) despite already having been through **two** prior line-cap trim
passes (its own line 964-971 banner: "2026-07-24 line-cap trim (2nd pass, umbrella-exemption removal ruling)"). It still
carries `umbrella: true` in frontmatter (line 12), but CLAUDE.md's 2026-07-24 ruling states flatly: "Line caps ... NO
`umbrella:`/`locked_by`+todos exemption" — that field grants no exemption anymore and is now vestigial/misleading.
**This is a genuine hard blocker, not just an advisory finding**: the prek pre-commit hook's `check_line_caps.sh` gate
is an ABSOLUTE per-staged-file bar (not a ratchet against a baseline) — ANY edit to this specific file is currently
uncommittable via the normal path, confirmed directly this session when 3 small, purely-factual doc-comment fixes (see
below) could not be shipped and had to be reverted.

Per `/plan-reconcile`'s own routing rule, a line-cap SPLIT decision is explicitly operator-gated (not something to
auto-resolve): the doc is a genuine large hub/coordinator doc (`umbrella: true`, absorbs ~7 fold-in sports plans + ~17
issue docs per its own summary), so the real choice is HOW to bring it back under a cap, not WHETHER.

**3 ready-to-apply fixes are queued and blocked on this decision** (drafted, verified correct, then reverted this
session because the line-cap gate blocks any commit to this file): (1) the `superseded_by` field's inline comment claims
"51 open/11 done todos" — stale by 4 days and 2 reconciliation sessions; the real current count is 65 open/39 done
top-level (78 open/41 done incl. nested sub-todos). (2) the `estimate_baseline_ai_days` comment's own 19+37+33+5=94
P0/P1/P2/P3 breakdown doesn't match its stated "96" total — an arithmetic slip. (3) Track C's casing-revert gating (line
142-143, "NOT YET EXECUTED... per operator instruction") has no cross-reference to
`issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md` (resolved), which documents this
exact gating already having caught one real contradiction — worth linking so the next reader sees the gate isn't
theoretical.

A: **Split into a coordination-index parent (kept under `plans/active/`, trimmed to a Tracks-summary + links) + N child
plans per Track/phase**, each independently under the 1000L cap, wired via `depends_on`/`gate_on_depends` per
`task_template.md` finding I's pattern (already the established workspace pattern for exactly this situation — see
`check_line_caps.sh`'s own doc comment: "a genuinely large hub belongs in `plans/epics/`... or splits"). Apply the 3
queued fixes to whichever child inherits the frontmatter/estimate fields and Track C respectively, in the same pass.
[WORKER REC] B: **Promote to a real epic** (`plans/epics/sports_consolidated_closeout.md`, 2000L hard cap flat, no
further split needed at current size) — simpler (one move, no multi-doc wiring), but epics are meant for genuinely
epic-scale coordination docs, not a workaround to avoid splitting; worth operator judgment on whether this doc's nature
fits that bar. C: **Leave as-is for now, do nothing** — the doc still functions as documentation (only the COMMIT path
via this specific checkout is blocked; reads work fine), and this is queued as a known, tracked papercut rather than
urgent. The 3 ready fixes stay queued/unapplied until a future session picks this up. Other: operator can type a custom
answer

**Operator answer (2026-07-25)**: the operator's broader directive to split all 5 AG consolidated plans (not just
sports) into parent+child implicitly ratified option A for sports too.

**Status**: resolved — option A executed. `sports_consolidated_closeout_2026_07_19.md` trimmed 986L→753L (well under the
1000L hard cap); split into 3 new AO-dispatch children (`sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`,
`sports_closeout_track_x_hygiene_2026_07_25.md`, `sports_closeout_track_s2_foldin_2026_07_25.md`) + their gated finalize
plans, wired via `depends_on`/`gate_on_depends`/`related:`. The 3 queued fixes (stale `51/11`→`65/39` count, the
`96`→`94` arithmetic slip, the missing casing-contradiction cross-reference) were applied to the parent in the same
pass. Commits: `647987de1`, `474296235`, `c24129ea7`, `95b9d2327`, `32fad89bb`, `dfbee37ef` — all verified durable on
`origin/live-defi-rollout`.

---

This doc will accumulate entries as genuine judgment calls surface during the cefi/defi/tradfi/prediction/sports
closeout-audit rollout. Format for each entry:

```
## <N>. <short title> (<date>, <AG/doc context>)

<question text — both sides cited as path:line + quote, why they conflict, which side looks authoritative and why>

A: <option — recommendation marked here if applicable> [WORKER REC]
B: <option>
Other: operator can type a custom answer

**Status**: open
```
