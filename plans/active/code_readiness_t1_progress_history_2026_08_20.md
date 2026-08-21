---
doc_type: plan
title: Code readiness T1 — progress history (2026-08-19 to 2026-08-20)
summary: >-
  Pure historical record, split out of code_readiness_t1_contracts_library_externalapi_2026_08_19.md when the parent
  hit its 1000-line hard cap (2026-08-21). Carries the plan-authoring entry plus the 2026-08-19/2026-08-20 Progress
  Log entries (pre-compact checkpoints, contract-edge landings, registry P0 fixes, a session handover, cross-tranche
  redirects) verbatim. No open todos live here — the parent plan's `## Todos` section is the live, authoritative
  list; this doc exists so the audit trail survives without re-inflating the active plan. Mirrors the T2/T3/T5
  sibling plans' identical split.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [code-readiness, contracts, external-api, tranche-1, history]
related:
  [
    /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
context_scope: [/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md]
supersedes:
superseded_by:
depends_on: []
source: >-
  Line-cap split of code_readiness_t1_contracts_library_externalapi_2026_08_19.md (1005 lines, over the 1000-line
  hard cap) during 2026-08-21 T2 cross-tranche activity — moved the oldest, fully-historical Progress Log content
  out so the parent plan's live todos stay under the cap without losing the audit trail. Performed by T2 (not T1)
  because a T2-authored inbound-request addition was what pushed the parent over cap, but the parent was already at
  999 lines beforehand — this split was going to be needed regardless of that addition.
assigned_role: backend_engineer
effort: low # pure archival split, zero new work
drift_direction: none
---

# Code readiness T1 — progress history (2026-08-19 to 2026-08-20)

> Pure historical record. See
> `/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md` for the live todo list and current
> Progress Log.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.
- 2026-08-20 — **PRE-COMPACT CHECKPOINT.** Context hit 67%; ran `/pre-compact` per the harness hook. Two significant
  finds during the audit, both from earlier (compacted-out) work in this same session:
  1. **Shipped**: 180 lines of FACTOR-STATE MODEL design work on the delta-proxy repricer issue doc
     (`execution_delta_proxy_repricer_generalization_2026_08_18.md` §11-15) were sitting uncommitted —
     unified-trading-pm@(latest, verified via `grep FACTOR-STATE` on origin post-push). Covers the unified
     fair-value function, canonical factors vs per-venue prices, snapshot watermarks, currency/numeraire ruling,
     rebase-without-jaggedness, and a placement ruling (anchor estimator lives in features-service, not
     strategy-service). Carries its own 3 tracked todos (`[DOC]`/`[REVIEW]`/`[BACKEND]`) plus 5 open items for
     the next operator session (§15) — READ THAT SECTION before touching `reference_position`/`credit` again;
     it may supersede the Q12-Q16 framing this plan cites elsewhere. The ship hit a self-healing collision
     (safe-doc-push detected its own corruption attempt from a concurrent peer edit, restored my content from a
     snapshot, verified zero conflict markers before proceeding) — landed clean, verified on origin.
  2. **UPDATE, same session, post-checkpoint: item 2 below was a FALSE ALARM, not real loss — recorded because
     the diagnostic trail is worth keeping.** After writing this checkpoint, the local working-tree copy of
     `TransferCapabilityV2` genuinely disappeared from `schemas.py` (confirmed: 0 matches, clean `git status`),
     and the gate run launched against it failed with `ImportError: cannot import name 'TransferCapabilityV2'`
     — indistinguishable from real data loss at the time. Reconstructed the change from the diff already
     captured in-session, re-verified 5/5 tests, re-gated (green, 377s), and went to ship it — at which point
     quickmerge's own Not-Behind Gate reported `unified-api-contracts@45a545e5ad` (this SAME slot, an EARLIER
     part of this compacted-out session) had **already landed the identical change** minutes before the
     checkpoint was written. The "revert" was never a revert: the working tree had simply reset to
     post-commit-clean state after that earlier successful ship, and re-reading it without re-checking `git log`
     first made it look like loss. Diffed the reconstruction against origin's landed version — byte-identical —
     then discarded the local duplicate and `pull --ff-only`'d clean (0 ahead/behind). **Lesson for next time**:
     before treating a missing local change as reverted, check `git log HEAD..origin/<branch>` FIRST — a
     same-slot earlier-session commit reads identically to a hostile revert until you do.
  (The original item-2 text this replaced described the pre-resolution "in flight, not yet shipped" state — moot
  now; the todo at line 376 already carries the correct landed sha.)
  **Standing state, unaffected by either item above**: 22 of T1's remaining todos need no gate finished, no
  outstanding uncommitted work exists in `unified-trading-library` (clean, 0 ahead) or `unified-trading-pm`
  (clean, 0 ahead, 0 behind after the restore above). All prior Progress Log entries in this file remain the
  authoritative record of what shipped before this checkpoint — do not re-derive.
- 2026-08-20 — **PATH_REGISTRY mode= fix landed — unified-trading-library@783d98ec73.** batch/paper/live rows
  for 5 datasets no longer collide on one GCS object path. Full details in the todo flip; noted here because it
  had TWO recoveries worth remembering: (1) a `check_todo_regression` gate catch of my own doing — a perl splice
  glued a following P1 todo onto the flip block with no newline, silently dropping it from the count (32->31);
  re-diffed against origin line-by-line, restored the newline, re-verified 32=32 before shipping. (2) a shared-
  checkout collision — running quality-gates.sh surfaced an 8-hour-stale, uncommitted peer edit on
  `unified_trading_library/cloud_interface/providers/gcp.py` (a `__getattr__` loud-fail guard for the GCS-
  client-silent-write-failure P0, this tranche's own NEXT todo) that was failing the gate on a 900-line file
  cap purely by co-residence. Confirmed dead (no live process, mtime 8h+ stale) before touching it, then set
  aside via a NAMED stash rather than fixed, discarded, or force-committed:
  `stash@{0}: inherited-dead-wip-gcp-blob-getattr-guard-2026-08-20` in the UTL checkout — recovered next.
- 2026-08-20 — **Oracle VALUE blindness closed — unified-api-contracts@03e8e90f.** Third violation class
  (`CanonicalViolationClass.VALUE`) answers "does this partition value name a real entity", checked against the
  venue / data_type / instrument_type / chain registries. CLAUDE.md's own conditional index warns agents that the
  oracle is "VALUE-BLIND"; that warning can now be narrowed to "value-blind BY DEFAULT, on purpose".
  **The design decision to re-read before changing anything here**: VALUE is OPT-IN. I measured the caller graph
  before writing a line — `canonical_path_violations()` feeds a WRITE boundary that RAISES
  (`market-tick-data-service/.../symbol_rules.py:517`), and the module already carries an inline account of the
  2026-06-23 incident where an over-eager venue guard flagged the legitimate `BINANCE-FUTURES` token and froze the
  deribit/hyperliquid/binance live VMs for hours. A registry that lags reality must degrade to a quiet audit
  finding, never a write outage — so `violation_classes=None` still answers exactly STRUCTURAL + ID_FORM, pinned by
  the named `DEFAULT_VIOLATION_CLASSES` constant AND by a regression test that asserts a path with a fictional
  venue still returns `[]` by default. The classified/audit view reports VALUE unconditionally, since an audit has
  no write path to break. **If someone later "tidies" VALUE into the default, that is the live-VM outage
  re-armed** — the constant's docstring says so in place.
  **Two limits stated rather than glossed**: membership is case-INSENSITIVE (measured: `ALL_VENUES`/`InstrumentType`
  UPPERCASE, `ChainKind` lowercase, `ALL_DATA_TYPES` genuinely mixed — case-sensitive comparison would manufacture
  violations on correct paths), and a missing axis is silent (absence is already STRUCTURAL; double-reporting it
  would inflate every audit). So "0 VALUE violations" means "every value present names something real", NOT "every
  value is correctly cased" and NOT "every required axis is present".
  Probed live before shipping: bogus `venue=NOT_A_VENUE` returns `[]` under the default and is caught under VALUE.
- 2026-08-20 — **Oracle filename-stem todo was STALE — closed by measurement, not by new code.** The plan listed
  `canonical_path_violations()` filename-stem validation as an open P0; it shipped weeks earlier
  (`unified-api-contracts@d40c5d7d`/`@502ef57e`). Confirmed against the CODE, not the issue doc's self-report:
  `CanonicalViolationClass.ID_FORM` is documented as "The FILENAME STEM", `id_form` is populated at 4 sites, and
  structure-only is now an explicit opt-in rather than the silent default. The source issue reads `status: open`
  only because 2 unrelated `[DATA]` findings from 2026-08-17 remain on it — a reminder that an issue's status
  field is not a verdict on any single todo inside it. **Still genuinely open**: the sibling VALUES todo — the
  oracle remains blind to `instrument_type`/`data_type`/`venue`/`chain` VALUES, which CLAUDE.md itself warns
  agents about, so "0 violations" still does not mean "canonical" on that third axis.
- 2026-08-20 — **Contract edge #3 landed: `OrderStatus` is now the 9-state machine — unified-api-contracts@a3c572f8.
  T4 unblocked.** Verified on origin, not by exit code: 9 canonical members + 2 aliases present in the landed blob,
  transition map + test file present, top-level export present, and `a3c572f8` confirmed via
  `merge-base --is-ancestor`. QG real exit 0 (273s), captured WITHOUT a pipe.
  **Design call worth re-reading before anyone "cleans up" the aliases**: option A (rename in place) was ruled and
  twice reconfirmed, but a literal rename breaks 24 execution-service call sites, and the entity-rename SSOT
  requires consumers to migrate in the SAME change — impossible from a tranche forbidden to edit that repo. The
  aliases resolve that conflict without shipping the rejected alternative: they are enum aliases (identity, not
  copies), so the state space cannot split in two. Removal is a filed `[FROM-T1]` todo on T4's plan, not a
  someday-note. MEASURED before choosing this: zero `.name`-based / `OrderStatus[...]` / `len()` / iteration
  coupling fleet-wide — that measurement is the whole basis for calling it behaviour-preserving, so if it is ever
  refuted the alias decision must be revisited.
  **What I deliberately did NOT do**: widen `PARTIALLY_FILLED` beyond the single edge the codex diagram draws.
  Real venues cancel partially-filled orders, so the map is probably incomplete — but the doc is the SSOT and this
  map is its projection, so the fix is a codex amendment first. Filed as a P2 question on T4's plan.
- 2026-08-20 — **Cross-tranche handoffs shipped — unified-trading-pm@617670c965.** T4 got three `[FROM-T1]` items
  (alias migration, the never-written `test_state_machine.py` verifier the codex doc has declared since 2026-05-12,
  and the `PARTIALLY_FILLED` edge question). T3 got a warning NOT to wait on `reference_position`/`credit`, since
  that edge is operator-gated on Q12-Q16 and will not clear on its own — with the two points that ARE settled
  (`credit` optional; strategy-owned/strategy-computed) called out so T3 can design against them today.
  **Also rescued 3 issue docs that existed ONLY in this slot's local clone** (defi SCE-suffix strategy_ids,
  health-factor monitor with no production entrypoint, MTDS availability data_type-without-venue) — they were
  sitting in an unpushed local commit the outgoing agent never landed, one `git` accident from gone.
  **Process findings, recorded because they cost real time tonight**: (1) `exit 0` lied THREE times — a
  safe-doc-push refusal, a failed lint, and a plan-hygiene block all surfaced as exit 0 through a pipe. Capture
  `$?` directly and grep the log for the verdict; never `| tail` a ship command, which is also how the first
  hygiene failure's own detail got truncated out of view. (2) The PM checkout carries **67 autostash entries** and
  safe-doc-push now calls that "extreme" — it is what produced tonight's merge conflict. (3) Writing
  `BLOCKED-OPERATOR` mid-sentence in a todo silently HOLDS that todo; the hygiene gate is right to fail it. Say
  "gated on an operator ruling" in prose and keep the marker in the leading tag cluster.
- 2026-08-20 — **T1 SESSION HANDOVER — second agent took over the tranche under an explicit operator ruling.**
  Not a normal resume: two Claude sessions were live in slot 6 at once. MEASURED at takeover — the incumbent T1
  agent (PID 19387, started 23:13:08) was mid-`quickmerge` (children 26702/26708/27231) shipping the
  QuoteInstruction edge, with `--isolated` holding `schemas.py` evacuated into `stash qm-iso-evac-26708`. The
  incoming agent did NOT edit anything while that was true — it armed a watchdog on the ship's real terminal
  state, confirmed `6be4b136` landed on `origin/live-defi-rollout` and the evac stash cleared, and only then
  retired PID 19387 (SIGTERM, confirmed gone, no orphaned ship children). Operator answered "take over T1, retire
  the peer" when asked; the takeover was not autonomous.
  **Nothing was lost, and that is measured, not assumed**: every tracked file in the UAC tree was byte-identical
  to `origin/live-defi-rollout`, 2 of 3 untracked test files identical, the third differing only by a
  one-character docstring-formatting artifact (`""" "coinbase"` vs `""""coinbase"`). The tree was synced
  `--ff-only` to `6be4b136` (0 ahead / 0 behind) behind a retained safety stash
  `t1-takeover-safety-20260819T230423Z` — deliberately NOT dropped. The older `qm-iso-evac-56777` residue from the
  documented SIGTERM recovery was left alone (never drop foreign WIP).
  **Standing warning for whoever reads this next**: slot 6 still hosts 3 other live `claude` sessions
  (PIDs 2749, 32709, 97270 — two of them ~1d14h old). They share this checkout's `.git/index` and `.git/config`.
  Re-check for a live peer before assuming this tranche is yours.
- 2026-08-19 — **Contract edge #1 landed: `QuoteInstruction` carries the sensitivity triple —
  unified-api-contracts@6be4b136d7. T4 IS UNBLOCKED on this edge.** Shipped by the outgoing agent; VERIFIED
  independently by the incoming one before adopting the claim: `6be4b136` is on `origin/live-defi-rollout`, and
  the landed `schemas.py` blob carries `underlying_instrument_id` (line 328), `delta` (335) and `gamma` (344), all
  three optional. The suite claim was re-measured too — 5 test functions, and the JSON round-trip is real
  (`QuoteInstruction.model_validate_json(original.model_dump_json())` at line 97), which matters because the
  instruction crosses the `EventTransport` seam. NOT re-measured by the incoming agent: the assertion that all 5
  pass (running `pytest` directly is banned, and the outgoing agent's own note records that UAC's gate suppresses
  pytest output on success) — they are on origin and inside the standing suite, so the next `quality-gates.sh` run
  in this repo covers them.
- 2026-08-19 — **Registry P0 #2 landed: chain registries reconciled — unified-api-contracts@27ebc544b2.** Verified
  landed (`27ebc544b2` an ancestor of `origin/live-defi-rollout`; landed blobs re-read). The issue's "three
  registries, three answers" framing is partly a CATEGORY ERROR — measured, they own three different concerns, so
  they were bound by containment invariants rather than merged (merging would have destroyed real distinctions;
  `VENUE_CHAIN_MAP`'s "4 chains" is its scope, not a gap). The REAL defect underneath was worse than under-reporting:
  4 live DeFi venues (`AAVE_V3-SCROLL`, `COMPOUND_V3-SCROLL`, `AAVE-PLASMA`, `FLUID-PLASMA`) parsed to chain tokens
  `KNOWN_CHAINS` did not contain, so every `if chain in KNOWN_CHAINS:` consumer silently else-branched on them.
  Three of the issue's own claims corrected by measurement: `KNOWN_CHAINS` was 12 not 10; `starknet` has NO DeFi
  venue justifying it (`EXTENDED-STARKNET` is CeFi and absent from `ALL_DEFI_VENUES`) so it was deliberately NOT
  added; and `PLASMA` was missing from `KNOWN_CHAINS` too, which the issue did not mention.
  **Process note**: this ship needed a recovery — the first `quickmerge` attempt was SIGTERM'd at the 2-minute
  foreground cap while `--isolated` had the files evacuated from the caller tree. Nothing was lost: the edits were
  in quickmerge's own `qm-iso-evac-<pid>` stash, restored via `git stash apply` and content-verified before the
  re-ship. Run quickmerge in the BACKGROUND in this repo — its pre-commit hooks exceed 120s.
- 2026-08-19 — **Registry P0 #1 landed: `get_venue_asset_group()` fails closed — unified-api-contracts@d4cded41b8.**
  MEASURED, not assumed: the old lookup held 55 capability-declaration `source` keys (`binance`, `databento`) and
  callers pass venue slugs (`BINANCE-SPOT`) — zero overlap, so all 209 registered venues fell through to the
  hardcoded `"cefi"`. Blast radius measured at ZERO code callers fleet-wide, so nothing stored or published was
  corrupted. Verified landed: `d4cded41b8` confirmed an ancestor of `origin/live-defi-rollout`, and the landed blobs
  re-read from that commit carry the raise + the COINBASE fix. QG green (exit 0, full log captured); the gate
  suppresses UAC's own pytest output on success, so I additionally executed both new test files' assertions
  directly as standalone probes — all passed. Second defect found and fixed in the same commit: bare `COINBASE`
  resolved to `defi` (false-match on `COINBASE-ETHEREUM`), the same trap already documented for `BINANCE`.
- 2026-08-19 — **T1 CLAIMED by slot-6·laptop.** No other slot had claimed a tranche (checked: slots 2-5 running
  unrelated work; no tranche plan referenced in any other slot's session). Taking T1 per the coordinator's
  "launch T1 first — four blocking edges terminate here". If another agent is also on T1, that agent should
  re-read this log before editing UAC/UTL.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- 2026-08-20 — **SECOND PRE-COMPACT CHECKPOINT — merges an audit run by a concurrent peer session sharing this
  slot with this session's own subsequent work.** 18 done / 19 open on this plan as of this entry (peer's own
  snapshot read 16/21 — three items it listed "actionable now" were closed by this session AFTER that snapshot:
  venue→chain SSOT + VenueFeature/VenueCapability overlap (`unified-api-contracts@0d7afa29e`) and the
  coverage-floor-registries P1 (`unified-trading-pm@26b8b3ed64`, closed by measurement — already resolved weeks
  earlier). **Do not re-open or re-work those three** — the peer's "actionable now" list is stale on exactly
  those items; everything else in it still stands.
  **Audit (Step 1)**: all three touched repos (`unified-api-contracts`, `unified-trading-library`,
  `unified-trading-pm`) confirmed clean, `ahead=0`, verified against `origin` content directly (not exit codes).
  53 scratchpad files, all disposable probe scripts/QG-log captures — every finding already landed in a commit
  message or this Progress Log; none referenced by path from any committed doc. No secrets, no chat-only findings.
  **Lessons carried forward from the peer session's audit (verified still accurate, not re-derived)**:
  - The plan's own citations of "Q12-Q16" for `reference_position`/`credit` are STALE. The actual current
    blocker is `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` §15 ("OPEN —
    needs an operator ruling next session"), which supersedes Q12-Q16 with a full FACTOR-STATE MODEL (§11-14,
    shipped this session) and its own 4 named open questions plus 5 outstanding Wave-0 rulings. Read §11-14
    before touching that todo again — it is a real design, not a stub. Worth checking (not yet done): whether
    the `delta`/`gamma`/`underlying_instrument_id` fields already shipped on `QuoteInstruction`
    (`unified-api-contracts@6be4b136d7`) are a valid special case of the §11 model or need revisiting once it's
    formally adopted.
  - `unified-api-contracts` quality-gates.sh runs 180-1076s (contention-dependent) — ALWAYS background it, never
    foreground (this session independently hit the same 120s-foreground-cap lesson via a SIGTERM'd first attempt
    early on).
  - **This slot has a genuinely concurrent peer session actively working the SAME T1 plan.** `git pull --ff-only`
    immediately before every plan edit; expect conflicts; resolve ADDITIVELY (never blind-overwrite) — this
    session hit and cleanly recovered from exactly this twice (a `check_todo_regression` catch on its own
    provenance-preservation edits, and a `SELF-INFLICTED CONFLICT MARKER` auto-recovery on the FACTOR-STATE MODEL
    ship). `VenueType = {SINGLE_VENUE, META_BROKER, DATA_AGGREGATOR}` vs `VenueCategoryV2 = {CEFI, DEFI, ...}` are
    easy to confuse in test fixtures — cost the peer session one failed run.
  - **This session's own lesson, not yet in the peer's list**: before treating a locally-missing change as a
    revert/data-loss event, run `git log HEAD..origin/<branch>` FIRST. This session spent real effort
    reconstructing `TransferCapabilityV2` from a diff already in context after it "disappeared" locally — it had
    actually already landed via this SAME slot's earlier (compacted-out) work (`unified-api-contracts@45a545e5ad`)
    minutes before this checkpoint's predecessor was written; the "revert" was just the working tree resetting to
    post-commit-clean state. A same-slot earlier-session commit reads identically to a hostile revert until you
    check the log.
  **Verdict: Safe to compact: YES.** All shipped work committed and pushed, `ahead=0` on every touched repo,
  verified against actual trunk content.

- 2026-08-20 — **THIRD PRE-COMPACT CHECKPOINT — lightweight, since the second checkpoint landed only minutes
  earlier and this session's only work since was one closure.** 19 done / 18 open on this plan as of this entry.
  **Closed since the second checkpoint**: the `(venue, instrument_type) -> data_types` combinator P1 —
  STALE, already resolved weeks earlier (`unified-api-contracts@fa9cece5`, confirmed a real ancestor of
  `origin/live-defi-rollout`, not a doc claim taken on faith); every `[CODE]`/`[DESIGN]` todo in the source issue
  was already checked, only 2 out-of-scope `[DATA]` backfill items remain open there.
  **Audit**: `unified-api-contracts` and `unified-trading-library` clean, `ahead=0`. `unified-trading-pm` was
  momentarily 9 commits behind (routine fleet activity — T4's own plan + manifest housekeeping, unrelated to
  T1) and carried one stale staged artifact (matched HEAD byte-for-byte, unstaged harmlessly) — `ff-only` pulled
  clean, now `ahead=0` / status empty. **Observed but deliberately NOT touched**: the concurrent peer session
  sharing this slot is actively mid-edit on `execution_delta_proxy_repricer_generalization_2026_08_18.md`
  (mtime <2 min at observation time) and had a new `/codex/04-architecture/cross-domain-state-fabric.md` doc
  in progress — that is their own live WIP, not mine to commit, stage, or promote. If a future session finds
  this file dirty again, check its own commit/push status before assuming loss — the same "check git log before
  panicking" lesson from the prior checkpoint applies.
  **In-progress, not yet started**: the W8 weightings SSOT todo (line ~416) — read-only investigation only so
  far (`strategy-service/strategy_service/portfolio_allocator/__init__.py`'s docstring: three real weighting
  concepts exist — generic portfolio-statistic weighting engines (axis-agnostic: FIXED/PNL_WEIGHTED/
  SHARPE_WEIGHTED/RISK_PARITY/KELLY/MIN_CVAR/REGIME_AWARE/MANUAL) vs per-archetype RANK allocators that weight
  along a named axis (coin/venue/protocol/expiry/LST) — no UAC-side code written yet. Next step: read
  `archetypes_simple.py` + `archetypes_rank.py` + `param_schema.py` for the exact current field/param names
  before declaring the SSOT, so the declaration uses real terminology, not invented names.
  **Verdict: Safe to compact: YES.** Zero uncommitted work of this session's own exists anywhere; the one
  dirty file observed belongs to a different, live session.

- 2026-08-20 — **`VenueCapabilityV2.collateral_rules`/`MarginSpec` population (W5) — flagged, deliberately NOT
  fabricated.** Per `plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md`, the schema is
  real and already consumed but populated for zero venues — the doc itself labels this "Population, not schema
  design." This is real per-venue collateral/margin data (LTV ratios, haircuts, margin tiers) for 192+ venues,
  feeding a live risk system. T1 will not invent financial risk parameters; getting these wrong could cause real
  harm. Left as `BLOCKED-OPERATOR-DECISION` in the plan (real data-research required, not code) rather than either
  fabricating values or silently skipping the line item.
- 2026-08-20 — **"External API surface" section re-triaged; 3 of 7 items were misassigned to T1, 1 shipped, 1 held
  on a genuine design question, 1 (wizard) left untouched.** Investigated the P0 "replace HTTP 501s with
  transfer/bridge/atomic/cancel" todo starting from `unified-trading-api/routes/execution.py` (T1-owned) —
  confirmed that repo has NO `/external/*` surface and no `501`s anywhere (grep, `.venv` excluded). Traced the
  artefact's actual citation (line 1361: `execution-service/execution_service/api/external_instruction_api.py`) —
  `execution-service` is T4-owned, not T1's. Same pattern held for the counterparty-facing-surface item
  (`strategy-service`, T3-owned), the API-surface-enumeration item (spans `instruments-service`+
  `market-tick-data-service`, T2-owned, and `execution-service`, T4-owned — redirected to T5 as read-only
  doc-generation, matching its existing `instruction_actions.py` tooling), and the Ceffu item
  (`execution-service/transfer_coordinator.py`, T4-owned, confirmed by the artefact's own file citation).
  Redirected all four via `[FROM-T1]` inbound flags (`unified-trading-pm@3837c66bbf`) with full measured context
  so the receiving tranche doesn't re-derive it, and closed T1's own copies as SUPERSEDED (kept for provenance,
  not deleted — the `check_todo_regression` conservation rule).
  **Kill-switch/flatten-position instruction todo** — genuinely half-T1 (adding them to
  `StrategyInstructionType` as caller-submittable actions, not just internal system behaviour) but is an open
  design call, not a mechanical enum fill: `INSTRUCTION_TYPE_TO_OPERATIONS` is a total mapping and control
  instructions may not decompose into `OperationType` steps the way trade/DeFi ones do. Held open, pending T4's
  answer on the needed shape (asked in the same inbound flag) — did not guess and ship a contract T4 would have
  to rework.
  **W17 fee/gas modelling (contracts side) — shipped `unified-api-contracts@01a595d3aa`.** Read
  `plans/epics/system_readiness_master.md` § W17 first (need was "clearing, broker, exchange, gas, and other";
  `exchange_fee_bps`/`gas_cost_usd` already existed on `ExecutionCostEstimate`). Added
  `clearing_fee_bps`/`broker_fee_bps`/`other_fee_bps`, all defaulting to `Decimal("0")` (zero existing/future
  construction call sites broken — none exist yet in this repo, confirmed by grep), deliberately NOT folded into
  `total_cost_bps` (documented, and locked in by a test) so no producer's total silently drifts. 3 tests in
  `tests/internal/unit/domain/execution_service/test_cost_estimate_fee_breakdown.py`, verified passing standalone
  before the full-repo gate (202s, clean — only pre-existing WARN-level findings, no new ones). The
  strategy-service/execution-service wiring ("bake into the decision" / "bake into alpha PnL") is T3/T4's, per the
  todo's own original framing — not redirected, since it already said so.
  **Wizard UI item (P1) left untouched** — genuinely T1-owned (`unified-trading-system-ui`) but not started this
  turn; next session should pick it up, needs `[UI]` + `pw:L2 ✓` + a cited regression spec per the plan's own note.
  **Lesson for future sessions**: a plan-authored P0 naming a specific artefact section is not proof the target
  repo is yours — the artefact cites its own source file per claim (grep the artefact around the todo's exact
  wording before writing code against your own repo's same-named-but-unrelated file).
