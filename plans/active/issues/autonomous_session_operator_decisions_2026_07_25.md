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
author: unknown
last_updated: "2026-07-31"
parent_epic: agent_operating_framework_master
assigned_vm: planning
priority: P1
archive_exempt: true # standing running log by design — accumulates entries as genuine judgment calls surface during an ongoing rollout (see its own final todo)
locked_by:
resolved_by:
source: >-
  Operator instruction 2026-07-25 immediately after /autonomous invocation: queue genuine decisions instead of silently
  deciding or blocking.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
  ]
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

`/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`'s follow-up todo ("does
the dex_pools-class fake-history-snapshot bug also affect Kamino/Solend Solana lending_indices in the `-prd-` bucket")
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
`/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` and dispatched as a
Todos-section item in `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (moved out of that plan's Deferred section).

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
2026-07-25 per `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`, DRIFT/PACIFICA already removed) and gate
the demote decision on its results — matches the original design's own evidence-first intent, no live-reader risk taken
without proof. [WORKER REC] B: Rule directly now that parity evidence is NOT required — proceed straight to
scoping/executing the demote-to-derived-view migration (re-home the MVP-gate accounting, migrate the features-onchain
bypass read, retire `perp_funding` raw capture). C: Rule directly now that `perp_funding` stays a permanently separate
captured raw type (keep dual-capture; close the DESIGN todo as "keep both — no parity check needed"). Other: operator
can type a custom answer

**Status**: resolved — option A. Filed the re-scoped HYPERLIQUID/ASTER cross-source funding-parity todo directly in
`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`, gating the DESIGN demote decision on its
results. `unified-trading-pm@2c61a8dc4`.

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

**Status**: resolved — option A. Dispatch the narrow golden-window-scoped Transfermarkt relaunch as originally scoped;
cheap, no conflict with Sports P2b whenever it eventually runs (smart-skip no-ops already-resolved cells). No file edit
needed — the candidate was already correctly scoped in `data_completion_sports_2026_07_24.md`.

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

**Status**: resolved — option A. Dispatch the ODDS+PREDICTIONS blank-reason measure-and-file candidate as scoped;
read-only/diagnosis-only, cannot regress or race the R1/R2/R3 gate. No file edit needed.

---

## 7. Fixtures legacy-path census vs. Track S/Track E/C1's entangled restamp residual (2026-07-25, sports)

`sports_legacy_fixtures_path_migration_2026_07_24.md` (archived at `/plans/archive/2026_08/`)'s one AO-eligible
candidate (a read-only, no-write per-date/ per-league census across all 2,319 post-floor dates, confirming the exact
load-bearing legacy-`entity=fixtures/` subset via real GCS object reads) carries 3 flagged conflicts against
`sports_consolidated_closeout_2026_07_19.md`'s own OPEN ground, all re-verified still open 2026-07-25:

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

**Status**: resolved — verified the census todo in `sports_legacy_fixtures_path_migration_2026_07_24.md` (archived at
`/plans/archive/2026_08/`) already requires a real GCS object read (not manifest-label-only) on the legacy side per its
own text — the scope correction option A called for was already present. Dispatch as-is.

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

**Status**: resolved — option A. Merge into one investigation: dispatch decision 16's day-partition root-cause dig first
(sports_consolidated_closeout Track S), fold the phantom-audit STANDINGS/TEAMS spot-check in as a corroborating data
point. No file edit made this pass — next sports dispatch should sequence accordingly.

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

## 10. Archive the 2 fully-done-but-soft-evidenced cross-cutting index docs, or keep them live? (2026-07-26, cross-cutting)

Surfaced by `/plan-reconcile cross-cutting` (autonomous). Two tranche docs are mechanically archival candidates —
`status: active`, `locked_by:` empty, **0 open todos** — but neither clears the skill's HARD-evidence bar for autonomous
archival, and both are still being READ as live reference surfaces, so this is a lifecycle call, not a fact.

- [`/plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md`](/plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md)
  — 0 open / **64 done**. Its own summary (line 12) says _"This doc is the tracking/index surface — the actual work
  happens by distributing each todo into its cited target plan"_, and each todo reads
  `✅ DONE 2026-07-24 — target: <file>` with evidence `pm@<commit-pending>` — a placeholder, not a sha (measured: only
  **4** lines in the whole doc carry a real `repo@sha`). So "done" here means "distributed", not "shipped". It is also
  the reference surface for `/plan-reconcile`'s own hunter 6 (SKILL.md: _"For each AG closeout, confirm every todo
  tagged for it has actually landed there"_) — an ongoing duty, which argues for keeping it live.
- [`/plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`](/plans/active/data_pipeline_reconciliation_skill_2026_07_20.md)
  — 0 open / **42 done** as of `unified-trading-pm@7ae64f4c2` (2026-07-26). But
  `cross_cutting_consolidated_closeout_2026_07_25.md` Track 13 says it is _"kept as a pure cross-reference, not
  something to close"_, and it is the cited home of the **D1/D2 rulings** that `cursor-configs/CLAUDE.md`'s
  reconciliation section leans on — archiving it moves an actively-cited SSOT pointer.

I did NOT archive either: the skill's Phase-4 rule is explicit that a fully-done plan with **any** todo only
soft-supported must be parked, never autonomous-archived — and 60 of 64 / most of 42 are soft.

A: **Keep both `status: active` in `plans/active/`** and add a one-line "standing reference surface, not an archival
candidate — 0 open todos is expected" note to each so future reconcile passes stop re-raising them. [WORKER REC] — both
are actively read by tooling/skills and by CLAUDE.md's own pointers; archiving buys nothing and costs discoverability.
B: **Archive both** via the 6-step ritual (accepting the `pm@<commit-pending>` placeholders as good enough), and repoint
every referrer — including `/plan-reconcile`'s hunter 6 and CLAUDE.md's D1/D2 pointer — at `plans/archive/`. C: **Split
the difference**: archive `data_pipeline_reconciliation_skill_2026_07_20.md` (its skill genuinely shipped), keep
`data_pipeline_e2e_milestones_gate_2026_07_24.md` live as the standing 14-criteria gate. Other: operator can type a
custom answer

**Status**: resolved — option A. Added a "standing reference surface, not an archival candidate" note to both
`data_pipeline_e2e_milestones_gate_2026_07_24.md` and `data_pipeline_reconciliation_skill_2026_07_20.md`; kept
`status: active`. `unified-trading-pm@2c61a8dc4`.

## 11. A `locked_by:` doc got archived with no `[unlock-plan]` — is the lock mandatory or advisory? (2026-07-26, cross-cutting)

**This entry changed shape mid-run — read the sequence, it is the point.** I found
`plans/active/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` terminal (`status: resolved`, all 4
todos `[x]`, baseline regenerated by `unified-trading-pm@ba098a7cc`) but carrying `locked_by: live-defi-rollout`, so I
**parked** the archival rather than doing it — `cursor-configs/CLAUDE.md` is explicit: _"`locked_by:` blocks archival
without `[unlock-plan]` (ASK, never autonomous)"_. While that park sat here, a concurrent escalation-driven remediation
(`unified-trading-pm@57ed9271c`, "plan_health gate auto-remediation — archive 11 terminal-status docs") **archived that
exact doc anyway** — no `[unlock-plan]` in the commit message, no block, and the archived copy at
`plans/archive/issues/` **still carries `locked_by: live-defi-rollout`** (archival-ritual step 6, "clear lock", also
skipped).

Root-caused and filed as
[`issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md`](/plans/archive/issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md):
the gate is real (`scripts/quality-gates.sh:406-422`) but lives ONLY in `quality-gates.sh`, and CLAUDE.md's own batching
rule routes "pure doc/plan-flip → prek only" — so the gate never executes on the one commit class that archives plans.
(The obvious `git mv`-shows-as-a-rename hypothesis was tested and **refuted**: `git diff --name-status` reports those
paths as `D`, so the filter would have matched had the gate run at all.)

So the question is no longer "may I archive it" — it is already archived. It is: **which side of this is the bug?**

A: **The lock is mandatory — fix the mechanism, retro-clean the lock.** Move the locked-plan check into the pre-commit
path (`run_hygiene_sweep.sh --precommit`, which already runs on every plan-touching commit), and clear the stale
`locked_by:` on the archived copy. [WORKER REC] — this keeps CLAUDE.md's two HARD-rule statements truthful; today a
rule-following agent parks and waits while an unaware automation archives the same doc unblocked in the same hour, which
teaches exactly the wrong lesson and quietly erodes the only un-automatable per-doc guardrail. B: **The lock is advisory
for terminal docs — narrow the rule instead.** Amend CLAUDE.md (and the `/plan-reconcile` routing table) to say
archiving a `status: resolved` doc with 0 open todos does NOT need `[unlock-plan]`, and delete the dead gate block
rather than relocating it. Cheaper, and arguably matches revealed practice — but it weakens the signal for the
non-terminal case too, so it wants your explicit sign-off, not mine. C: **Treat `@57ed9271c` as premature** — restore
the doc to `plans/active/issues/` pending a real `[unlock-plan]`, then do A. Most conservative; costs a revert and
re-fixes referrer paths corpus-wide. Other: operator can type a custom answer

**Status**: resolved — option A. Confirmed via
[`issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md`](/plans/archive/issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md):
that doc's own todo #1 records **RULED (a) 2026-07-26 — mandatory**; its P1/P2 mechanism-fix todos shipped
(`check-locked-plan-deletion.sh`, commit-msg stage, end-to-end verified; the dead `quality-gates.sh:406-422` block
removed); and its P2 retro-clean todo is marked done, citing `unified-trading-pm@2c61a8dc4` for clearing
`locked_by:`/`locked_since:` on the archived copy — independently re-verified here:
`plans/archive/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` now carries an empty `locked_by:` and
a "2026-07-26 — `locked_by:` cleared" dated note. No new operator input needed.

## 12. Fold target for the near-complete `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (2026-07-26, prediction)

`/plan-reconcile prediction` (2026-07-26, autonomous shard) flagged this plan as a **near-complete consolidation
candidate**: 1 open todo, 10 done. Per the skill's Phase-4 routing, WHERE a live remnant lives is a planning decision —
autonomous mode parks it with a named recommendation rather than auto-folding.

Side A — the remnant itself, `/plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md:129`:

> `- [ ] [SCRIPT] P1. **Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet — CONFIRMED`

Side B — an umbrella todo that already claims this ground,
`/plans/active/prediction_phase_ab_residuals_2026_07_24.md:178-180`:

> `- [ ] [BACKEND] P1. **Close the 12 residuals on Kalshi/Polymarket perpetual futures + live CLOB depth/quotes** (funding / basis / dispersion arb inputs). `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` (12 open of 85) — **split + archived 2026-07-24** (plan line-cap remediation) into …`

They do not contradict each other — B is the parent umbrella that A was split out of — but a 1-todo shell plan whose
single item is `BLOCKED-UPSTREAM` is exactly the "remnant too small to justify a standalone plan" case, and the shell
cannot archive while it holds live work.

A: Fold the single BLOCKED-UPSTREAM todo into `prediction_phase_ab_residuals_2026_07_24.md` § "A3 — Venue-perps + live
CLOB depth residuals", which already carries the umbrella todo for exactly this population, then archive the emptied
shell via the 6-step ritual. [WORKER REC] — keeps the venue-perps residuals in one place, removes a shell plan, and the
item is upstream-blocked so nothing is actively being worked in the shell today. B: Leave it standing as its own plan —
BLOCKED-UPSTREAM work is legitimately long-lived, and a dedicated doc keeps the Polymarket-perps upstream watch visible
rather than buried in a 345-line residuals plan. C: Fold it instead into
`/plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (2 open), the other Phase-A3 split sibling. Other:
operator can type a custom answer.

**Status**: resolved — option A. The lock is mandatory (CLAUDE.md's own text is unambiguous); sharpened the
mechanism-fix todo in `issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md` with the real
commit-msg-vs-pre-commit staging nuance found while scoping it, and retro-cleaned the stale `locked_by:` on the
already-independently-verified archived doc. `unified-trading-pm@2c61a8dc4`.

---

## 13. Out-of-lifecycle prediction cell — `empty_confirmed[EXPECTED_*]` (out-of-window) or `expected_unattempted`? (2026-07-26, prediction)

`/ag-closeout-audit prediction` (2026-07-26, autonomous, 2nd run of the day) Phase-3 conflict-check. Two open todos in
the prediction covering set prescribe **different target states for the same cell on the same MTDS emission path**, and
one of them additionally proposes undoing a shipped cross-repo canonical set. Data-correctness / honest-coverage
semantics, so it is not a style preference.

Side A — `/plans/active/prediction_phase_ab_residuals_2026_07_24.md:124-128`:

> `- [ ] [BACKEND] P1. **Adapters must apply lifecycle bounds BEFORE the network call** — today inactive days land as `SOURCE_RETURNED_ZERO`instead of an honest`EXPECTED_*` …`

Side B — `/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 1, legs (2) and (3):

> `only emit a cell (captured/empty/failed) for dates WITHIN [available_from, available_to]; outside the market's life = honest BLANK / `expected_unattempted`, NEVER `empty_confirmed``
> …
> `evaluate whether `EXPECTED_INSTRUMENT_NOT_LISTED`/`PRE_VENUE_LAUNCH`/`DELISTED`should be REMOVED from`EMPTY_CONFIRMED_REASONS` so out-of-lifecycle dates read as absence, not empty_confirmed`

A wants `EXPECTED_*` (which today _is_ an `empty_confirmed` reason); B wants explicitly NOT `empty_confirmed` and would
delete those very reasons. **Read from source**, all three named reasons are already members of
`OUT_OF_COVERAGE_WINDOW_REASONS`
(`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py:590-616`) — the
operator-directed coverage-denominator partition (2026-06-12, extended again by operator 2026-07-17) that clips them
from numerator AND denominator while keeping the raw rows honestly `empty_confirmed` + a visible reason badge, so "an
out-of-model range is always VISIBLE, never silently dropped". So B's stated goal appears **already delivered by a
different shipped mechanism**, and removing the enum members would break `record_empty(reason=...)` validation
(`UnknownEmptyConfirmedReasonError`) for every asset group that emits them. Either way this is a cross-repo
canonical-set change — outside dispatch-scope eligibility, so it should not be dispatched as written.

A: Strike leg (3) from batch4 todo 1 and replace it with "verify `OUT_OF_COVERAGE_WINDOW_REASONS` already excludes
prediction's out-of-lifecycle cells from the denominator"; keep legs (1)-(2) but align (2)'s target state to Side A
(`empty_confirmed[EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED]`, out-of-window-classified) rather than
`expected_unattempted`. [WORKER REC] — it is the only option that leaves one contract standing, matches the
most-recently-operator-affirmed mechanism (2026-07-17), and needs no enum change. B: Genuinely remove the three reasons
from `EMPTY_CONFIRMED_REASONS` — accept the corpus-wide blast radius (every AG's `record_empty` callsites + the UI
reason badges) because "blanks where we expected data" should mean a literal blank, not a classified empty. C: Keep both
todos as-is and rule that the two target states are for different layers (adapter pre-fetch gate vs manifest emission),
i.e. no conflict — but say which value each layer writes. Other: operator can type a custom answer.

**Status**: resolved — option A. Rewired `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 1 leg (3) to
verify `OUT_OF_COVERAGE_WINDOW_REASONS` already excludes these cells from the denominator instead of removing enum
members; aligned leg (2)'s target state to `empty_confirmed[EXPECTED_*]`, matching Side A
(`prediction_phase_ab_residuals_2026_07_24.md`) which was already correct. `unified-trading-pm@2c61a8dc4`.

---

## 14. Unmatched prediction market — `OTHER` (capture-and-flag) or `attempted_failed[ClassifierConfidenceLow]` (honest failure)? (2026-07-26, prediction)

Same audit run. **Three surfaces currently document/implement two different contracts** for a prediction market the cqg
classifier cannot map, and a fourth doc's shipped-and-ticked todo asserts the opposite of a fifth doc's open premise.

1. `unified-api-contracts/.../predictions/classifiers.py:21-24` (module docstring, still authoritative-looking):
   > `**Sub-threshold** — when neither path produces a group, return ``None``; caller marks the shard as ``attempted_failed[reason=ClassifierConfidenceLow]``.`
2. Same file, `classify_polymarket_to_canonical_group`:538-545 — the opposite:
   > `Previously returned ``None`` (caller routed to ``attempted_failed[reason=ClassifierConfidenceLow]``) — changed to ``OTHER`` so honest-absence capture replaces silent failure.`
3. `market-tick-data-service/.../scripts/rebuild_prediction_manifest.py:612` still implements contract (1) —
   `# Unclassified cids → attempted_failed[ClassifierConfidenceLow] (classifier contract).` — which now only bites
   KALSHI, since `classify_kalshi_to_canonical_group` still returns `None` for unmatched while the Polymarket path no
   longer does (callsite at `:409-429`).
4. `/plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:51-56` + its 4 shipped `[x]` todos
   (`unified-api-contracts@306923a`): "The classifier MUST map every Polymarket `conditionId` (and Kalshi ticker) to
   SOME canonical question group … Treating `OTHER` as a known catch-all is honest absence".
5. `/plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md:69-76` (open `[DATA] P1`) rests on the opposite premise
   — "94.5% route to `attempted_failed[ClassifierConfidenceLow]` under the operator-corrected contract (None → NOT
   bundled, no 'OTHER' fallback)" — measured 2026-06-11, i.e. five days before decision 338 landed.

Consequence today: prediction's honest-coverage numbers depend on which contract you believe, and the two venues take
different paths. Note this is a semantics question only — decision 338's _registry-extension_ half is provably already
ruled and implemented (2026-06-16, 10 in-code citations), which is why the dependent wiring is drafted as dispatchable
in `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch5_2026_07_26.md` (`status: draft`) todo 2.

A: Ratify `OTHER` as the single contract for BOTH venues — fix the stale module docstring (1), route KALSHI unmatched to
`OTHER` too (3), and re-base cqg_residual todo 1's premise. [WORKER REC] — it is the only contract with shipped consumer
surface behind it (the deployment-ui panel, the `OTHER_BUCKET_MEMBER_ADDED` audit loop, the manifest denominator), and
it is what the live Polymarket path already does. B: Ratify `attempted_failed[ClassifierConfidenceLow]` as the contract
— revert (2) so unmatched Polymarket markets fail honestly again, and treat the shipped `OTHER` bucket as the
regression. C: Keep them deliberately split per venue (Polymarket → `OTHER`, Kalshi → `attempted_failed`) and document
WHY, since Kalshi's `KXMVE*` parlay flood is a different population from Polymarket's long-tail novelty markets. Other:
operator can type a custom answer.

Related sub-question if A or C is chosen: `classify_polymarket_to_canonical_group` downgraded
`OTHER_BUCKET_MEMBER_ADDED` from INFO to DEBUG ("log-volume/latency noise", classifiers.py:540-542), but
`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`'s shipped `[x]` todo specified **INFO** precisely so "Operator
periodically queries the event stream to find candidate groups for promotion". That promotion-audit loop is effectively
off in production today, and the `[x]` now over-claims.

**Status**: resolved — option A, ratified. Verified at current HEAD: both `classify_polymarket_to_canonical_group` and
`classify_kalshi_to_canonical_group` are already non-Optional and route to `OTHER` for both venues
(`unified-api-contracts@d4523602` already shipped this) — the entry's premise (Kalshi still returns None) was stale.
Fixed the module docstring (`unified-api-contracts@f7aed74a`), re-scoped the now-stale 94.5%-ClassifierConfidenceLow
premise in `prediction_cqg_residual_2026_07_24.md`, and corrected the shipped INFO→DEBUG over-claim in
`predictions_other_bucket_and_ui_drilldown_2026_06_20.md`. `unified-trading-pm@2c61a8dc4`.

---

## 15. `matchday` recovery — regex patch vs. mandated re-run ordering (2026-07-26, sports)

Recover `matchday` via a cheap regex over `round_name` now, or let Track F's mandatory corpus-wide `derived_features`
re-run recompute it? Regex path: `sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md:780/739`. Mandated
re-run: `sports_consolidated_closeout_2026_07_19.md` Track F (P0). Unresolvable from evidence alone because run-order
matters: before the re-run = discarded work, after = redundant, during = write race.

A: Declare the regex patch superseded, delete that todo. [WORKER REC] — Track F is P0 for independent reasons and
recomputes matchday anyway; a second live mechanism only creates a race against a P0 data-correctness pass. B: Keep as a
gated interim fix with `depends_on` + an escape clause. C: Leave both open (status quo). Other: operator can type a
custom answer.

**Status**: resolved — option A. Declared the matchday regex-recovery todo superseded and closed it in
`sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md` — Track F's mandatory corpus-wide re-run
recomputes matchday anyway. `unified-trading-pm@2c61a8dc4`.

## 16. 55 open checkboxes in a split features-sweep doc — reconcile in place vs. archive (2026-07-26, sports)

The doc's own §Z section proves several rounds are TERMINAL STATE (corpus-re-scan-verified row counts), yet the
checkboxes closing that work sit unchecked above it — a lifecycle call, not an evidence gap (evidence is identical
either way).

A: Reconcile in place (already drafted as `sports_satellite_ao_dispatch_batch6_2026_07_26.md` todos 1-2). [WORKER REC]
B: Archive §§G-AA as history, re-file only live residue fresh. C: Do A then B once the surviving-open count is measured.
Other: operator can type a custom answer.

**Status**: resolved — option A. Already correctly drafted as `sports_satellite_ao_dispatch_batch6_2026_07_26.md` todos
1-2 (reconciling part2's 24 + part3's 31 open checkboxes). No further edit needed; becomes real dispatchable work once
sports's batch6 is flipped active.

## 17. Finalize-plan template gap — generalize workspace-wide? (2026-07-26, sports)

`sports_satellite_ao_dispatch_batch6_2026_07_26.md` todo 7 adds a missing source-doc-archival step to sports's 5
finalize plans only. The gap already caused a live incident: `run_hygiene_sweep.sh --ci` hard-failed at 10 violations
(baseline 0) at 02:15Z; auto-remediation via PR #1545 fixed it at 02:57Z. `task_template.md:340-354`'s 3-part rule never
mentions archiving _source_ docs — the defect is in the rule, not the sports plans.

A: Amend the template + codex + backfill into the other 4 AGs' finalize plans. [WORKER REC] — a sports-only fix leaves 4
AGs queued to reproduce the same failure. B: Sports-only fix (as drafted). C: Reject, rely on the CI-gate
auto-remediation as the intended mechanism. Other: operator can type a custom answer.

**Status**: resolved — option A. Amended `task_template.md` §4's finalize-plan-coverage rule to also check each
batch-extraction plan's SOURCE docs for archival eligibility, not just the plan itself — closes the gap workspace-wide
(all draft finalize plans reference the template generically, so no per-AG backfill needed).
`unified-trading-pm@2c61a8dc4`.

## 18. Orphan doc invisible to every tranche's membership rule (2026-07-26, sports/infra)

`sports_prediction_mvp_writetime_precompute_2026_07_24.md` (tagged `[cross-cutting]`, correctly — a full-fleet schema
bump) has zero citation hits in sports's 17 covering plans AND falls outside cross-cutting's own membership rule (its
`parent_epic: deployment_and_user_management_master` isn't in cross-cutting's 5-epic list). Its 1 open P2 todo
(`MANIFEST_SCHEMA_VERSION` 9→10 bump) has no owning tranche at all.

A: Assign to `infra`. [WORKER REC] — matches the skill's own epic-split note. B: Widen cross-cutting's membership rule
to admit the epic instead (fixes root cause, competitive with A — worth ruling on both). C: Leave unowned, rely on an
`all`-tranche run. Other: operator can type a custom answer.

**Status**: resolved — option A. `sports_prediction_mvp_writetime_precompute_2026_07_24.md` assigned to the `infra`
tranche in this session's earlier 9-tranche run (see plan-of-record). Option B (widen cross-cutting's membership rule)
filed as the follow-on via entry #32's scope-widening work.

## 19. Track 24 (strategy/execution determinism, ~121 open todos across 8 docs) — undrainable block (2026-07-26, cross-cutting)

Too large to ever fully drain in one closeout pass; already 748L vs. the 500 soft cap. `v2_engine_venue_buildout`'s 37
boxes are mostly already covered by its 2026-07-13 5-child split (3 archived, 2 still active) — over-counted as live
work today.

A: Extract into its own child plan, run one dedicated triage as a standalone exercise. [WORKER REC] B: Leave in place,
accept permanent orphan reporting on every future audit. C: Split by kind (research/strategy child vs. determinism-spine
home vs. drop the over-counted v2_engine reference) — fold into A regardless of split choice. Other: operator can type a
custom answer.

**Status**: resolved — option A. Extracted Track 24 (~121 todos, 8 source docs) out of
`cross_cutting_consolidated_closeout_2026_07_25.md` into its own child plan
`cross_cutting_strategy_execution_determinism_2026_07_26.md`, carrying the `v2_engine_venue_buildout` over-count caveat
forward. `unified-trading-pm@2c61a8dc4`.

## 20. Track 22 monitor-instance docs — retag to single-AG, or keep cross-cutting? (2026-07-26, cross-cutting)

4 docs (2× `manifest_hygiene_red`, 2× `phantom_captures_*`) are tagged `[cross-cutting]` because the _monitor_ is
shared, but each instance's content and fix are single-AG (defi/cefi/prediction/tradfi respectively).
`phantom_captures_tradfi` is already double-claimed (also named in tradfi's own batch2 Deferred);
`phantom_captures_prediction`'s 1 open todo has no dispatch owner anywhere except a non-dispatching digest citation.

A: Keep the cross-cutting tag, batch the fix from cross-cutting, add an explicit ownership note to Track 22. [WORKER
REC] — retagging mid-rollout while other agents audit those same tranches concurrently is the greater hazard. B: Retag
all 4 to their AGs, delete Track 22. C: Split — keep the 2 manifest_hygiene docs cross-cutting, retag the 2
phantom_captures docs to their AGs (defensible second choice, needs sign-off since it reassigns ownership of a live
data-correctness fix). Other: operator can type a custom answer.

**Status**: resolved — option A. Kept Track 22's `[cross-cutting]` tag (retagging mid-rollout was judged the greater
hazard) and added an explicit ownership note to `cross_cutting_consolidated_closeout_2026_07_25.md`.
`unified-trading-pm@2c61a8dc4`.

**PARTIALLY OVERRIDDEN 2026-08-07 (operator)** — re-asked independently via
`tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 6 (same question, tradfi-scoped framing, not knowing
this ruling already existed). Flagged back before applying; operator then explicitly overrode Option A for
`phantom_captures_tradfi_2026_06_28.md` specifically ("switch to tradfi") — retagged `[tradfi]`, Track 22 updated to a
cross-reference. **The other 3 docs (2× `manifest_hygiene_red`, `phantom_captures_prediction`) are UNCHANGED** — this
was a scoped, single-doc override, not a reversal of Option A's general rationale, which still holds for the rest
(concurrent-audit races are a standing condition of this workspace, not a one-time rollout risk).

## 21. WorkerLivenessWatchdog — harden vs. soften, and ordering (2026-07-26, ao)

Six docs touch the kick/escalation mechanism; two prescribe opposite directions —
`killed_slot_orphans_... 2026_07_21.md` wants faster hard-kill escalation (N=3 consecutive frozen reads), while
`host_saturation_false_worker_kicks_..._2026_07_26.md` has _measured_ evidence kicks are already firing falsely on live
progressing workers (zero fleet completions for over an hour on 2026-07-26). Landing harden-first would turn false kicks
into false hard-kills.

A: Soften first — dispatch host_saturation's two-window fix + completion-signal recognition + CPU-progress check as one
sequenced plan, then re-scope the harden todo against the corrected classifier. [WORKER REC] — the false-positive side
has measured active harm right now; the harden side's evidence is a single 5-day-old stuck slot, and hardening while the
classifier is known-wrong is actively dangerous. B: Author one unifying "liveness classification contract" plan first.
C: Widen `verify_window_s` as a config-only stopgap. Other: operator can type a custom answer.

**Status**: resolved — option A. Gated `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s
hard-kill-escalation todo on `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s two-window fix
landing first — measured active harm (false kicks on progressing workers) outweighs a single 5-day-old stuck-slot data
point. `unified-trading-pm@36c5433eb`.

## 22. Flip `ao_satellite_ao_dispatch_batch1_2026_07_26.md`/finalize to active? (2026-07-26, ao)

10-todo pair. Highest-value todo: the DB-pool `BEGIN IMMEDIATE`-on-every-transaction wedge, measured still-unfixed at
HEAD, 11 recorded occurrences, "a restart is NOT a durable mitigation."

A: Flip both now. B: Flip only the batch, hold the finalize per `task_template.md`'s draft-gated pattern (finalize
reconciles evidence — nothing to reconcile yet). [WORKER REC] C: Flip only a P1/P2 subset first. Other: operator can
type a custom answer.

**Status**: resolved — option B. Flipped `ao_satellite_ao_dispatch_batch1_2026_07_26.md` to `active`; held the finalize
sibling `draft` (already `gate_on_depends: true` — self-activates once the batch's todos land).
`unified-trading-pm@2c61a8dc4`.

## 23. Seven deleted `tab/rootm/*` branches — real work loss or already-superseded? (2026-07-26, ao)

The doc justifying keeping these branches ("deletion would lose the only copy") is now moot — all 7 confirmed gone from
all six repos, undated, no recorded review. Named at-risk work: a WorkerLivenessWatchdog commit, 5 deployment-service
commits, 5 MTDS commits, a strategy-service kill-switch fix, 2 UAC commits, a UTL messaging module.

A: Treat as most-likely-superseded, run batch1 todo 9's read-only presence-check, archive if all present. [WORKER REC] —
todo 9 already does this read-only, with explicit no-push/no-cherry-pick/no-delete guardrails. B: Treat as possible
work-loss, escalate any absent item for recovery attempt. C: Accept the loss without verifying. Other: operator can type
a custom answer.

**Status**: resolved — option A. Already correctly scoped as batch1's own read-only presence-check todo
(no-push/no-cherry-pick/no-delete guardrails already present); dispatched as part of flipping ao batch1 active. No
further edit needed.

## 24. Two "not AO-dispatched" docs whose remaining todo is now bounded — extractable? (2026-07-26, ao)

`agent_orchestrator_alert_channel_cleanup_2026_07_13.md`'s 24-48h verification window opened 13 days ago (blocker — a
Secret Manager permission error — confirmed gone); `ao_fleet_observability_kpis_2026_07_20.md`'s target date is tomorrow
with a named validated script. Both carry an explicit prose "NOT AO-dispatched" banner.

A: Lift the declaration for the KPI re-measure specifically (pure numeric re-run, nothing needs a human), extract into
batch 2; keep the alert-channel one LOCAL/manual (its real question — "is the channel actionable?" — is a taste call).
[WORKER REC] B: Keep both LOCAL, run manually. C: Rule generally that prose declarations always outrank batchN
extraction workspace-wide. Other: operator can type a custom answer.

**Status**: resolved — option A in principle (the KPI re-measure is a bounded numeric re-run, no human needed) — but not
extracted into a separate batch, since the target date (~2026-07-27) is only a day out and it's the last open item in an
otherwise-shipped LOCAL plan; the natural trigger is the date arriving. `unified-trading-pm@36c5433eb`.

## 25. AO tranche membership — the one covering plan sits outside the Sources list (2026-07-26, ao)

`ao_open_issues_consolidated_close_out_2026_07_17.md` (9 open/32 done) is the only active plan actually covering tranche
members, yet isn't in the AO closeout's Sources. 3 of the 6 watchdog-cluster docs (incl. the P1 creating the whole
directional conflict in #21) are 2026-07-26 docs one day outside the Sources list — a hand-maintained list lost the most
important doc in the tranche within 24 hours.

A: Add the doc to Sources now. B: Change the rule to an epic-based definition
(`parent_epic ∈ {orchestrator_master, agent_operating_framework_master}` — measured: 75 docs vs. 35 current Sources). C:
Do both — A now, B as a follow-on with the ~40-doc delta triaged explicitly. [WORKER REC] Other: operator can type a
custom answer.

**Status**: resolved — option C (do both). Added `ao_open_issues_consolidated_close_out_2026_07_17.md` to
`ao_consolidated_closeout_2026_07_25.md`'s Track 5 Sources now; filed the epic-based-membership-rule redefinition +
~40-doc delta triage as a new todo in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`. `unified-trading-pm@2c61a8dc4`.

## 26. Flip `ci_satellite_ao_dispatch_batch1_2026_07_26.md`/finalize — first-ever ci dispatch vehicle (2026-07-26, ci)

`ci_consolidated_closeout_2026_07_25.md` has zero todos ever and no `ci_*batch*` plan has ever existed before this run.

A: Flip both, leave the closeout hub as a pure digest (digest/dispatch split is the documented architecture). [WORKER
REC] B: Flip both + add the 5 Close-out criteria as verification todos to the hub. C: Leave draft, review the 29 todos
individually first. Other: operator can type a custom answer.

**Status**: resolved — option A (adapted). Flipped `ci_satellite_ao_dispatch_batch1_2026_07_26.md` to `active`, hub
stays a pure digest; held the finalize sibling `draft` for consistency with entries #22/#38 (`gate_on_depends: true`
already self-activates it). `unified-trading-pm@2c61a8dc4`.

## 27. `scripts/quickmerge.sh` claimed by 6 docs — is the dispatch order right? (2026-07-26, ci)

Only one can run concurrently (files must differ). Dispatched: the new-file-only no-op fix
(`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:224`). Held back: sentinel-config binding (P1, a gate-semantics change,
`qg_sentinel_environment_blind_2026_07_23.md:124`), the dormancy-aware gate, branch-check broadening, content-hash
fast-path, STAGE 0 cascade instrumentation.

A: Keep this order — the no-op fix is fully specified with no pending decision. [WORKER REC] B: Do the sentinel-config
binding first instead (more severe — a gate bypass, but alters gate semantics fleet-wide, worse to run concurrently with
28 other todos). C: Serialize all six in one dedicated quickmerge-only plan. Other: operator can type a custom answer.

**Status**: resolved — option A. Already correctly captured in `ci_satellite_ao_dispatch_batch1_2026_07_26.md` — only
todo 1 (the no-op-ship fix) touches `quickmerge.sh`, the other 5 claims deferred to batch 2+. No edit needed.

## 28. `digest-drift-sweep.yml` — three docs, one file, cost symptom in the least-related doc (2026-07-26, ci)

Doc 1 (`digest_drift_sweep_silent_noop_..._2026_07_16.md`) owns the hardening fixes (2 of 4 still open); doc 2
(`post_cutover_silent_assumption_sweep_2026_07_23.md` §F4) owns the actual live cost — the sweep never converges and
fans out to `ubuntu-latest` every tick; doc 3 asks why the fix didn't catch it.

A: Confirm doc-1 hardening (already dispatched as batch todo 3) as the sole edit now, fold F4's non-convergence into
batch 2 once todo 3 lands. [WORKER REC] — bundling now would put an unrooted investigation inside a bounded fix. B: Rule
doc 1 SSOT, merge everything into one combined todo. C: Dispatch the money-costing half first, defer hardening. Other:
operator can type a custom answer.

**Status**: resolved — option A. Already correctly captured in the same batch1 doc — todo 3 owns the digest-drift-sweep
hardening as the sole edit now; F4's non-convergence explicitly deferred to fold in once todo 3 lands. No edit needed.

## 29. MTDS `DEPLOYMENT_ENV` leak — fix the reproducer tests or preserve them? (2026-07-26, ci)

`qg_sentinel_environment_blind_2026_07_23.md:128` wants the two leak-coupled MTDS tests fixed now (UTL precedent already
shipped); `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` explicitly recommends instrumenting
quickmerge's cascade step _instead_, since fixing the tests destroys the only known reproducer (5 more reproductions
since, always via quickmerge, never via bare QG).

A: Instrument the cascade step first, hold the test-fix. [WORKER REC] — silencing the reproducer before instrumenting
risks making a real leak permanently invisible. B: Fix the tests now, re-reproduce later if needed. C: Do both — add
isolation AND an autouse ambient-leak detector (strong second choice). Other: operator can type a custom answer.

**Status**: resolved — option A. Ruled in `qg_sentinel_environment_blind_2026_07_23.md`: hold the MTDS test-fix
specifically until quickmerge's cascade-step is instrumented (the 2 MTDS tests are the only known reproducer);
deployment-api/strategy-service proceed independently. `unified-trading-pm@36c5433eb`.

## 30. STEP 2d — is the operator HOLD (D3) now discharged by events? (2026-07-26, ci)

D3 held STEP 2d pending a decision on 3 dead workflows. Since: `reconcile-release-tags` was repurposed (not deleted) and
codex-ratified; `digest-drift-sweep`'s token was fixed (1 of 4 fixes); `cassette-drift-check` was fixed same-day.

A: Declare D3 fully discharged, unblock STEP 2d now. B: Partially discharged — unblock STEP 2d only once batch todo 3's
hardening lands (item #28). [WORKER REC] — "fix digest-drift-sweep" is measurably still open at named lines, so
declaring full discharge overstates the evidence. C: Re-scope STEP 2d as its own design pass first. Other: operator can
type a custom answer.

**Status**: resolved — option B. Already correctly captured in `ci_satellite_ao_dispatch_batch1_2026_07_26.md` — D3
treated as partially discharged, STEP 2d unblocks once todo 3's digest-drift hardening lands. No edit needed.

## 31. A dispatched todo asks a worker to move a published git tag (2026-07-26, ci)

`hatch_vcs_main_tag_ancestry_gap_...2026_07_26.md` todo 2 asks a planning-VM worker to choose between re-tagging
convention vs. re-tagging `v0.72.0` onto current HEAD — against CLAUDE.md's "never bump manually" rule. The bump-rate
circuit breaker has also tripped (≥3 pending bumps), so no self-heal path exists currently.

A: Tag `[OPERATOR]`, split — dispatch only the convention-fix half, hold the tag-move half, open a separate todo to
clear the tripped breaker. [WORKER REC] — "decide the fix direction" between two options, one of which mutates a
published release identity, is a design call live right now on a worker. B: Leave dispatched as-is (todo has its own
warning text). C: Leave the todo, just add both docs to ci's Sources. Other: operator can type a custom answer.

**Status**: resolved — option A, independently reached and already executed by concurrent workers before this ruling
landed: filed as `/blocked` question `BLK-2d9aae3f` rather than force-moving the tag; operator answered PARTIAL —
direction B (ancestry-aware idempotency guard) authorized now, direction A (force-retag) held pending operator
authorization. Confirms this ruling's direction; no further action needed.

## 32. ~48 active docs sit in NO consolidated closeout (2026-07-26, ci)

The 9-tranche partition only sweeps `asset_group: cross-cutting`, but `plans/PLAN_FORMAT.md:88` also declares
`infrastructure` and `meta` as valid values — sweeping those returns ~48 unlisted docs, 4 unambiguously ci (one,
`/plans/archive/issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` (archived 2026-07-30), had
zero referrers corpus-wide). `check_ag_closeout_linkage.py` doesn't catch this class either.

A: Widen the skill's rule to sweep all 3 values, run one corpus-wide triage plan for all ~48. [WORKER REC] — the
partition's stated value is total coverage, and that claim is currently false by ~48 docs. B: Fix only the 4 ci-obvious
docs now. C: Declare `meta`/`infrastructure` deliberately out-of-scope, document it. Other: operator can type a custom
answer.

**Status**: resolved — option A. Widened `/ag-closeout-audit`'s membership rule
(`cursor-configs/skills/ag-closeout-audit/SKILL.md`) to also sweep `asset_group: infrastructure`/`meta` (~48-doc gap);
filed `issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md` to track the remaining corpus-wide triage (4 of ~48
already resolved by ci tranche's own audit). `unified-trading-pm@36c5433eb`.

## 33. `stale_staging_versions_manifest` — confirm option 1 (dormancy-aware gate)? (2026-07-26, ci)

The doc's own blocking gate ("versions must be advancing since 2026-07-23") is now measured satisfied (14 entries,
newest 2026-07-26). The doc pre-committed: "at that point... option 1 becomes correct." Item is tagged `[OPERATOR]`.

A: Confirm option 1, queue as the batch-2 quickmerge.sh slot. [WORKER REC] B: Option 3 instead (retire the gate input
entirely, needs checking 2 other consumers first). C: Do nothing — drift is down to 1 repo, no longer a live hazard.
Other: operator can type a custom answer.

**Status**: resolved — option A. Confirmed in `stale_staging_versions_manifest_2026_07_23.md`: the doc's own
pre-committed gate (versions advancing since 2026-07-23) is now measured satisfied; queued as a `quickmerge.sh`-touching
todo for ci's batch 2. `unified-trading-pm@36c5433eb`.

## 34. MTDS `PYTEST_UNIT_DIR` — two competing widenings (2026-07-26, infra/cefi)

infra's `codex_violations_ratchet_to_five_2026_06_10.md` wants the whole `tests/` tree collected, absorbing 22
newly-collected failures in the same unit; cefi's `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md` wants
a narrower subdir list, and only after fixing those same 22 failures first (opposite order).

A: cefi's doc wins on both counts — narrower target, fix-first ordering; rewrite the infra todo as a pointer. [WORKER
REC] — turning on 70 uncollected files with 22 known failures unfixed would red every unrelated MTDS commit. B: infra's
doc wins — stricter, permanent, but reds MTDS until all 22 land. C: Land cefi's fixes first, then apply infra's
whole-tree value, plus promote a fleet-wide PM check for this class. Other: operator can type a custom answer.

**Status**: resolved — option A. cefi's `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md` wins (narrower
target + fix-the-40-known-failures-first ordering); rewrote the infra todo in
`codex_violations_ratchet_to_five_2026_06_10.md` as a pointer to it. `unified-trading-pm@36c5433eb`. **Both docs' work
is now done** — cefi's doc archived 2026-07-31 (all 5 todos), infra's pointer todo flipped `[x]` same date
(na-eligibility-audit ci tranche).

## 35. `DataStatusTab.tsx` claimed by two tranches for two different changes (2026-07-26, infra/cross-cutting)

cross-cutting batch1 (already active) wants a 3-value UI split; infra's `issue_docs_remediation_sweep_2026_06_02.md`
§G-UI wants the hardcoded service list made UAC-driven. Same file, same-priority concurrent-todo file-collision risk.

A: Let cross-cutting batch1 land first (already active), pick up G-UI in infra batch2 once quiet. [WORKER REC] — the
finalize plan already re-checks this exact conflict. B: Merge into one todo, one shared regression spec. C: Move G-UI
permanently into cross-cutting (retag). Other: operator can type a custom answer.

**Status**: resolved — option A. Sequenced: let cross-cutting batch1 (already active) land `DataStatusTab.tsx` first,
infra picks up the G-UI change once quiet — annotated in `issue_docs_remediation_sweep_2026_06_02.md`.
`unified-trading-pm@36c5433eb`.

## 36. PM `base-service.sh`/`base-library.sh` — multi-tranche edit hotspot, no ownership rule (2026-07-26, infra)

4 infra items (domain-client retarget, pip floor bump, cryptography/idna re-check, uv drift-guard) all edit these
fleet-wide files; 2 other tranches' active batches (cross-cutting batch1b, tradfi batch4) also claim them. A bad
concurrent edit reddens all 25 repos' QG at once.

A: Declare the files a serialized resource (one owning plan at a time, enforced by a plan-hygiene check), batch the 4
deferred infra items into one unit. [WORKER REC] — the measured cost of no rule is already 4 held-back items in a single
batch. B: Give infra sole ownership, other tranches file requests against it. C: Accept contention, rely on quickmerge
rebase + QG to catch collisions. Other: operator can type a custom answer.

**Status**: resolved — option A. Declared `base-service.sh`/`base-library.sh` a serialized resource; batched the 4
deferred infra items into one `sequential: true` unit for the next infra batch, annotated in
`infra_satellite_ao_dispatch_batch1_2026_07_26.md`. `unified-trading-pm@36c5433eb`.

## 37. `human_led_audit_pool`'s 12 seeded rows — human-only justification now retired (2026-07-26, infra)

The doc's human/agent split is explicitly grounded in "Opus 4.7 1M context" being required for audit work; CLAUDE.md now
states Sonnet 5 also has 1M context and retires context-size as an opus-escalation trigger entirely (operator ruling
2026-07-23). 12 of 14 rows still unstarted after 9 weeks.

A: Re-test each of the 12 rows against the current qualitative dispatch-scope rule — determinable-outcome rows become
normal Sonnet-5-max batch candidates, genuinely open-ended ones stay human on qualitative grounds. [WORKER REC] — 9
weeks at 12/14 unstarted is the shape of work that is not going to happen while it waits for a human. B: Keep all 12
human-only, since the real claim may be qualitative just phrased in context-size language. C: Split by priority,
dispatch lower-priority rows as a test. Other: operator can type a custom answer.

**Status**: resolved — option A. Annotated `human_led_audit_pool_2026_05_21.md`: the context-size justification is
retired per CLAUDE.md's 2026-07-23 ruling; queued the 12-row re-test against the current qualitative dispatch-scope rule
(not executed row-by-row this pass). `unified-trading-pm@36c5433eb`.

## 38. Flip `infra_satellite_ao_dispatch_batch1_2026_07_26.md`/finalize — first-ever infra dispatch vehicle (2026-07-26, infra)

The hub is a zero-todo digest by construction. Note: batch1 todo 19 is separately `[OPERATOR]`-tagged (deletes a live
prod Cloud Run job + scheduler + terraform, needs its own separate go-ahead regardless of this decision).

A: Flip both, give the hub real todos (its 4 Track close-out criteria) so future audits measure a real covering set.
[WORKER REC] — without this, the next infra audit re-derives the same 29-orphan verdict no matter how much batch1 ships.
B: Flip both, keep hub a pure digest, add an `aggregated_sources` sibling doc instead. C: Don't flip yet — review the 25
todos first (5 touch prod/fleet-wide surfaces). Other: operator can type a custom answer.

**Status**: resolved — option A. Flipped `infra_satellite_ao_dispatch_batch1_2026_07_26.md` to `active`; added the 4
Track close-out criteria to `infra_consolidated_closeout_2026_07_25.md` as verification todos; held the finalize sibling
`draft` (gate_on_depends self-activates); todo 19 stays gated by its own `[OPERATOR]` tag regardless.
`unified-trading-pm@2c61a8dc4`.

---

## Todos

- [x] [REVIEW] P1. **2026-07-28 retag** (was `[OPERATOR]` — already resolved, tag left stale). **Rule which side of
      entry 11's `locked_by:` archival gap is the bug, and clear the stale `locked_by: live-defi-rollout` on the
      already-archived copy** — `plans/archive/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` was
      archived without `[unlock-plan]` by a concurrent auto-remediation while this session had parked the exact same
      archival per CLAUDE.md's lock rule. **RESOLVED**:
      `issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md` ruled option (a) — the lock is
      mandatory, an enforcement gap, not a policy choice — shipped the mechanism fix (commit-msg-stage
      `check-locked-plan-deletion.sh`), and its own retro-clean todo is done: the archived copy's
      `locked_by:`/`locked_since:` are empty, independently re-verified here. See entry 11 above for the full citation.
- [x] [DOC] P3. **CONFIRMED 2026-07-31 — still ongoing, `status:` left `open`.** Checked
      `ag_closeout_audit_rollout_2026_07_25.md` at current HEAD: `status: active` with 1 open todo (line 105, "Finish
      applying the 70-item batch + the remaining mass-flip" — cefi/defi/prediction/sports batch/finalize pairs "not
      re-verified" per Round 8's own Deferred table), and its own most recent entry (2026-07-30 na-eligibility-audit
      pass) independently re-verified `KEEP-NA, valid` with the note "remaining item is a human-supervised
      re-verification, not a bounded fact" — i.e. the rollout is not concluded, it is still the standing home for this
      class of question. All 38 logged entries above ARE resolved (verified via grep — 0 remaining `**Status**: open`
      outside the closing template block), but the parent rollout plan itself is not, so this doc correctly stays
      `status: open` per its own stated purpose rather than moving to the archival ritual. No frontmatter change needed.

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

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: re-verified context_scope (3 entries — corrects the 2026-08-01 marker's stale count, the
  list itself already carried 3) — all still resolve; this is a code-free standing decision-log (all 38 entries
  resolved, kept `open` only because the parent rollout plan is still active), so no source path applies.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
