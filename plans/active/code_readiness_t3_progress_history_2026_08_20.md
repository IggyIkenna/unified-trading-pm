---
doc_type: plan
title: Code readiness T3 — progress history (sessions 1-6)
summary: >-
  Pure historical record, split out of code_readiness_t3_features_ml_strategy_2026_08_19.md when the parent hit its
  1000-line hard cap (2026-08-20). Carries the original Progress Log plus sessions 2-6 and the session-2 deferred-work
  table, verbatim. No open todos live here — the parent plan's `## Todos` section is the live, authoritative list;
  this doc exists so the audit trail (incidents, corrections, lessons) survives without re-inflating the active plan.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [features-service, ml-service, strategy-service]
scope: [engineer]
tags: [code-readiness, strategy, features, tranche-3, history]
related: [/plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md, /plans/epics/system_readiness_master.md]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
context_scope: [/plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md]
supersedes:
superseded_by:
depends_on: []
source: >-
  Line-cap split of code_readiness_t3_features_ml_strategy_2026_08_19.md (1021 lines, over the 1000-line hard cap)
  during 2026-08-20 session 9 — moved the oldest, fully-historical Progress Log content out so the parent plan's
  live todos stay under the cap without losing the audit trail.
assigned_role: backend_engineer
effort: low # pure archival split, zero new work
drift_direction: none
---

# Code readiness T3 — progress history (sessions 1-6)

> **This doc has zero open todos and is not independently dispatched.** It exists purely so
> `code_readiness_t3_features_ml_strategy_2026_08_19.md` — the live plan — could shed its oldest Progress Log
> content and stay under the 1000-line hard cap. Read the parent plan for current status; read this doc only for
> the incident/lesson detail behind an item the parent plan references but doesn't re-explain.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.

- 2026-08-20 — **Archetype registration wave. `strategy-service@1bda20fb` + `strategy-service@3eb96f35`.**

  MEASURED, `/archetype-code-completeness` on the landed tree (`3eb96f35`, clean, == origin):

  | leg (of 180 rows) | before | after |
  | --- | --- | --- |
  | `engine_factory` | 96 ready / 84 not_ready | **177 ready / 0 not_ready** / 3 excluded |
  | `target_universe_catalog` | 96 ready / 84 not_ready | **177 ready / 0 not_ready** / 3 excluded |
  | `param_schema` | 105 ready / 75 not_ready | 120 ready / 57 not_ready / 3 excluded |
  | overall BATCH | 6 ready / **47 not_ready** / 7 unverified | 6 ready / **19 not_ready** / 1 excluded / 34 unverified |

  `ARCHETYPE_ENGINE_REGISTRY` 32 -> 59; `TARGET_UNIVERSE` 549 -> 630 rows; `PARAM_SCHEMA_REGISTRY` 35 -> 40.
  `tests/unit` 3757 passed. The remaining 19 `not_ready` are EXACTLY the schema-less-but-registered set — every
  other mode-invariant leg is clean, so the next unit is a single well-defined job.

  What was actually wrong, and is worth not re-learning:

  * **22 of the 28 "missing" engines were never missing.** They were code-written AND unit-tested, deliberately
    withheld from the registry by a policy requiring a passing backtest first. The matrix read that absence as
    "no engine exists". Three tests asserted the withholding as an invariant; all three are now
    `_assert_code_complete` (registration + schema + catalog + Kelly together, so a partial wiring cannot pass).
    **Never infer "is it backtested" from registry absence again.**
  * **Two real engine<->schema key drifts**, found by making the systemic construct-and-fire test exercise the newly
    registered engines: `VOL_SPREAD_STRUCTURES` read `atm_call`/`otm_put`/... (6 keys) and `VOL_VARIANCE_SWAP` read
    `atm_straddle_call`/`_put` (2) — spellings their own `PARAM_SCHEMA_REGISTRY` entries never declared. Sibling
    `VOL_RATIO_SPREAD` already used the schema names, so the schema was right and the engines had drifted. Any slot
    configured through the wizard surface would have silently no-op'd forever. **A4 cannot catch this class**: it
    compares CATALOGUE keys against the schema, and both can agree while the engine reads a third spelling. The
    method that found it — make the engine actually fire on a plausible tick — is the one that generalises.
  * **`ARBITRAGE_MEV_SANDWICH` is a policy exclusion, not a gap.** Added an `excluded_by_policy` verdict state to
    the skill so it reports on every leg rather than sitting permanently red. Honest denominator: 59 in scope, 1
    out of scope by decision. Adding an entry to `POLICY_EXCLUDED_ARCHETYPES` is a policy claim needing a cited
    decision + an enforcing test — never a way to silence a red cell.
  * **A4 gate improved, baseline shrunk 166 -> 106** (-60): taught it `key_template` hierarchy prefixes and exempted
    `venue`/`instrument_type`/`asset_group` (structural keys stamped on every row by the shared constructors, never
    read by a named engine `_param` call). Every retired entry was a false positive the module docstring had already
    predicted. Its "119 pairs" comment was itself stale — it measured 166.

  **Shipping incidents — read before trusting a quickmerge result:**

  * `quickmerge.sh` **exits 0 when the re-gate FAILS**. Three consecutive attempts reported exit 0 and landed
    NOTHING (lint; codex-compliance; the empty-string-fallback ratchet). Only checking origin's tree caught it.
  * Worse, `--files` given a DIRECTORY path stages nothing for it, silently. `1bda20fb` therefore landed the source
    registration WITHOUT the `portfolio/` package or the test updates, and quickmerge's recovery pass then reverted
    the unstaged test edits in the working tree. LDR was briefly inconsistent: `factory.py` referenced an absent
    module and the old tests asserted the opposite of the new code. Repaired by `3eb96f35` with every path named
    individually. Note `safe-doc-push.sh` REFUSES a wildcard outright; quickmerge accepting a directory and
    dropping it is the more dangerous behaviour because it produces a PARTIAL commit.
  * **`git diff FETCH_HEAD` reported no differences during the broken window** — because the local test edits had
    been reverted to match origin, so both sides agreed on the wrong content. Exit code, "✅ Landed", clean
    `git status` and an empty diff ALL passed. Only a per-file `git cat-file -e FETCH_HEAD:<path>` found it.

  Cross-tranche: 27 `clients.yaml`/waiver files filed to T5 (`unified-trading-pm@96d5d2e1f1`);
  `PENDING_CROSS_REPO_WAIVER` in strategy-service is the shrinking worklist.

- 2026-08-20 — **Param schemas for the last 19 archetypes. `strategy-service@37989f99`.**

  MEASURED on the landed tree (content-verified in origin, not just file presence — the file pre-existed):

  | leg (of 180 rows) | after registration wave | now |
  | --- | --- | --- |
  | `engine_factory` | 177 ready / 0 not_ready | 177 ready / 0 not_ready |
  | `param_schema` | 120 ready / **57 not_ready** | **177 ready / 0 not_ready** |
  | `target_universe_catalog` | 177 ready / 0 not_ready | 177 ready / 0 not_ready |
  | overall, per mode | 19 not_ready | **0 not_ready** |

  `PARAM_SCHEMA_REGISTRY` 40 -> 59. `_SCHEMA_COVERAGE_BASELINE_MISSING_SCHEMA` -> `frozenset()`, kept not deleted:
  an empty baseline is what makes the A1 gate fire on the NEXT archetype registered without a schema, and keeps its
  message saying "a NEW archetype has no schema". Full `quality-gates.sh` green before the push; 1755 v2 tests.

  Method worth reusing: every default was extracted from the engine's real
  `*_param(self.params, "<name>", <default>)` call with its `file:line`, then written table-driven.
  `test_param_schema.py` asserts the declared default equals the engine's, so this is not a place where a
  plausible-looking guess survives — it fails the gate.

  **Headline: 0 not_ready per mode, from 47 at plan authoring.** State it precisely — it means no archetype FAILS a
  machine check. 51-53 rows/mode remain `unverified` and are genuinely different work: `allocator_rank` is a
  per-archetype RULING (generic allocator vs dedicated rank engine), and batch/paper dispatch need a registry lookup
  built before they can be checked at all. Neither is closed by this commit.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)

## Deferred work after 2026-08-20 (session 2)

> Superseded by later sessions' Progress Log entries in the parent plan — kept here verbatim for the incident
> detail. Do not treat this table as current status; the parent plan's `## Todos` section is authoritative.

**Archetype code-completeness is now FULLY CLOSED** — every leg, every mode: 59/59 ready (or `excluded_by_policy`
for `ARBITRAGE_MEV_SANDWICH`). Zero `not_ready`, zero `unverified`. Started this tranche at ~6 ready / ~47 not_ready
/ ~7 unverified per mode. This was the plan's headline metric and its entire "Archetype code completeness" todo
section is now done.

| Area | State | Next concrete step |
| --- | --- | --- |
| Archetype code-completeness (all 7 legs, all 3 modes) | **DONE — 59/59 ready every leg/mode** | Nothing. |
| `CARRY_FUNDING_DISPERSION` vs `_DISPERSION_RANK` ambiguity | **DONE — operator decided 2026-08-20**: wired to `CARRY_FUNDING_DISPERSION_RANK` (matches the archetype's own cross-sectional design). `CARRY_FUNDING_RANK` is now the pinned-unreachable legacy alias instead. `strategy-service@ed9ff26875` (corrected 2026-08-20 — this cell had reverted to a stale placeholder, likely during an earlier stash-conflict incident, and a blanket SHA-fill script mistakenly overwrote it with the wrong commit; fixed against `git log`, the authoritative source). | Nothing. |
| DeFi/vol/sports/ML/MM config-key contract drift | **DONE — sweep was already comprehensive, not vol-scoped.** The systemic construct-and-fire test parametrizes all 59 registered archetypes, confirmed green (143 passed/3 xfailed with `GCP_PROJECT_ID` set). 2 genuine remaining bugs, both `[DESIGN]`-blocked not mechanical: `RULES_DIRECTIONAL_EVENT_SETTLED`, `MARKET_MAKING_EVENT_SETTLED` (real per-row threshold/instrument-ID decisions, not derivable). | Nothing agent-executable. The 2 xfails need a human to pick real DSL thresholds / Betfair-Matchbook instrument IDs — don't fabricate plausible-looking values for live financial strategies. |
| W6 wizard / config | Untouched | rank-buffer hysteresis, no-trade band, beta-hedge overlay, vol-target-at-book-layer. The PORTFOLIO engines already ship a working no-trade band (`rebalance_band`) — reuse that shape. |
| W9/W10/W13 PnL, risk, exposure | **Genuinely open, re-scoped, with a correction.** Session 4's "`paper_run_attribution.py`/`paper_run_passive.py` confirmed real, shared batch=paper=live path" claim is RETRACTED (session 6) — zero production callers found on direct grep, was an unverified second-hand relay. The real live/paper driver is `GroupBRunner` (`engine/backtest/runner.py`); what it uses for attribution is unidentified. `compute_pnl` confirmed dead (formula may still hold unique sports/interest logic — verify before deleting); `compute_handler`'s CLI op is code-reachable but has no deployment trigger anywhere in-repo. HWM confirmed compliant in the live path. | Identify `GroupBRunner`'s real attribution path (not `paper_run_attribution.py`/`paper_run_passive.py` — those are dead code candidates now, not the answer) before touching PnL surfaces further. Decide `compute_handler`'s fate and confirm `compute_pnl`'s 3 capabilities are covered elsewhere before retiring it. |
| W16/W18 preflight + canonical paths | Untouched | Fail-closed startup readiness check; canonical output paths (needs T1's `PATH_REGISTRY` `mode=` fix). |
| Position adapters / venue coverage | **DONE — whole section found already resolved** (all 4 sub-items: CeFi dispatch, asymmetry, hot-swap, orphan-coverage), all shipped 2026-08-14 through 17 by prior sessions, predating this plan's 2026-08-19 authorship. This plan section was written stale from birth. Residue is entirely non-agent-executable: 2 `[OPERATOR]` decisions (instrument hot-swap A/B, out-of-mandate adapter disclosure) + 1 `[AGENT]` Solana-SDK item in execution-service (T4's repo). | Nothing. If picking this back up, it's an operator-decision chase (hot-swap A/B, disclosure), not new engineering. |
| features-service | **Swept 2026-08-20 — every item already correctly gated, not "untouched-and-actionable" as this row implied.** Onchain featureless shards: mechanical part shipped 2026-07-30, remaining scope independently reconfirmed 5x as needing human data-source scoping (not a build task — see session 9's correction in the parent plan: this framing was too broad, most of it turned out to be a wiring bug + a governance-parameter research gap, not a design question). `corporate_actions`: zero live blast radius (built-but-never-run) + genuinely `[OPERATOR]`-gated vendor decision. Calendar manifest gap: gated on a `[REVIEW]` shard-atom design decision. `delta_one` PREDICTION-bucket bug: already fixed (`features-service@09be801b`); one test-mode-only caveat noted. Settlement-suffix (P2): already fully resolved. | See the parent plan's session 8/9 entries for current status. |
| ml-service | Confirmed 2026-08-20: the MEV opportunity-detection gap is strategy-service + features-service scoped (3 calculators reading `features.get(key, 0.0)`), not a separate ml-service item — no distinct ml-service-only gap found in this tranche's allocated corpus. Correctly not agent-attempted: the issue doc's own author scoped all 3 calculator-builds as needing "a design decision on exact derivation, not a blind guess." | Nothing agent-executable found. ml-service itself was not otherwise touched this session — its allocated corpus may still have unswept non-spine docs (see the Close-out section's non-spine-tail todo). |
| Both strategy-service artefacts | Not re-derived | Re-derive markers only AFTER the W-items close; never hand-edit the HTML. |

**Cross-tranche**: T5 still owes 27 `clients.yaml`/waiver files (`PENDING_CROSS_REPO_WAIVER` in strategy-service is
the shrinking worklist) and the two `quickmerge.sh` defects
(`/plans/active/issues/quickmerge_exit_zero_on_failed_regate_and_silent_directory_files_2026_08_20.md`).

**Recommended next item (superseded 2026-08-20 session 3 — see Progress Log)**: position adapters/venue coverage
and config-key drift are both now DONE (found already-resolved or already-comprehensive). What's left with real
agent-executable scope: **W6 wizard/config** (untouched — rank-buffer hysteresis, no-trade band, beta-hedge
overlay, vol-target-at-book-layer; the PORTFOLIO engines' `rebalance_band` is a reusable shape) and **W16/W18
preflight + canonical paths** (untouched, blocked on T1's `PATH_REGISTRY` `mode=` fix for the paths half, but the
fail-closed startup readiness check has no such dependency). The PnL item is real but narrower than it reads —
see its row above; `compute_handler`'s cron-trigger decision and `compute_pnl`'s formula-uniqueness check are the
actual next actions there, not a from-scratch unification.

## Progress Log — 2026-08-20 session 2

- **Wired 5 orphaned rank allocators + corrected 2 wrong skill verdicts. `strategy-service@583a2a79`,
  `strategy-service@9c11ab8b` (already landed pre-checkpoint), `unified-trading-pm@a4609ff2be`.**

  MEASURED, final state, every leg of `/archetype-code-completeness`, all 3 modes:

  | leg | before this entry | now |
  | --- | --- | --- |
  | `allocator_rank` | 24 ready / 153 unverified | **177 ready / 0 unverified** |
  | `paper_dispatch` | 12 ready / 47 unverified | **59 ready / 0 unverified** (from session start of this checkpoint) |
  | `batch_dispatch` | 17 ready / 42 unverified | **59 ready / 0 unverified** |
  | **overall, every mode** | ready=6-8 / unverified=42-53 | **59/59 ready, 0 unverified, 0 not_ready** |

  Two skill verdicts were **wrong about the system**, not just cautious — measuring settled both:
  1. `allocator_rank`'s `unverified` reasoning ("which generic allocator is configured is not statically derivable")
     was true of the old private-dict lookup, not of the system: resolution is total
     (`archetype_allocator.resolve_allocator` never raises) and `FIXED` is a documented equal-weight policy.
  2. `batch_dispatch`'s `unverified` reasoning ("batch_rerun's replay path may still cover it; not independently
     confirmable") was provably false: `archetype_for_slot_label()` round-trips all 630 catalogue rows. Measured,
     not assumed.

  **Real bug found wiring the first one**: `ALLOCATOR_ARCHETYPE_REGISTRY` implements 9 dedicated `*_RANK` engines;
  the private dict selecting one mapped only 4. Five purpose-built rankers were dead code — their archetypes
  silently earned equal-weight `FIXED` instead of the metric built for them. Wired 4; left the 5th
  (`CARRY_FUNDING_DISPERSION_RANK`) deliberately unreachable pending an operator decision (see deferred table).

  **Shipping this required real incident handling — read before your first ship of a session on a busy checkout:**

  1. **Host-wide QG contention (7-18 concurrent `quality-gates.sh` processes measured)** caused a resource-timing
     gate to fail ("`Quality gates must complete in <300s`") on content that was independently verified clean
     (ruff, full pytest run, separately). Diagnosed as environmental, not content — retried, landed clean next
     attempt. **The absolute 300s wall-clock budget doesn't account for host-wide load** — worth its own issue if it
     recurs.
  2. **A DIFFERENT live session is sharing this exact slot's checkout right now** (the SessionStart hook warned
     about this at the very start of the session — it was real, not a false positive). Their in-progress
     agent-orchestrator plan edit showed up as unfamiliar dirty content under MY git identity (`slot-4·laptop` — the
     identity is derived from the slot path, not the process, so two sessions in one slot commit as the same
     "person"). **Never touched their file.** Confirmed via `git log -1 --format=%an` that the file's last real
     author was consistent with a peer session, and left it exactly as found.
  3. **My own unstaged edits got swept into `git stash` TWICE** by concurrent sessions' "pre-reconcile quarantine"
     autostashes — quickmerge's own forensic tooling caught the second instance itself ("Do NOT cite `<sha>` as
     evidence for these paths — it does not carry them... recover from the stash BEFORE re-running") and named the
     exact stash + recovery commands. **Recovery method**: `git stash show --stat stash@{N}` to confirm the stash
     is EITHER cleanly mine OR bundles a peer's file alongside mine (both happened, once each), then
     `git checkout stash@{N} -- <my-paths-only>` — never a blanket `pop`/`apply`, which would have also restored
     the peer's file into my working tree.
  4. **`--isolated` is the documented fix for exactly this symptom** ("pass it once edits keep reverting under
     contention, that IS the fix") — used it for the final successful ship after two content losses on the same
     two files. Content-verified in origin afterward (grepped for a distinctive string in `origin`'s blob, not just
     checked the SHA matched — a matching SHA after a contended reconcile is not proof of content, only of Git
     state).

  **The general lesson, stated once so it isn't re-learned**: on a heavily contended shared checkout, `local HEAD
  == origin HEAD` and `git status` clean are NOT proof your change landed — a peer's autostash can quarantine your
  unstaged edits while a `git pull --ff-only` cleanly fast-forwards past them, leaving both checks green while your
  content is sitting in an unnamed stash. The only real proof is grepping ORIGIN's blob content for something
  distinctively yours, every time, on a contended checkout.

## Progress Log — 2026-08-20 session 3

**Operator decision landed**: `CARRY_FUNDING_DISPERSION` → `CARRY_FUNDING_DISPERSION_RANK`, not the previously-wired
legacy `CARRY_FUNDING_RANK` alias. Evidence for the recommendation: the archetype engine's own docstring
(`funding_dispersion.py`) describes a flat cross-sectional rank with no venue/LST hierarchy, arriving as an
upstream `funding_rank_pct` feature — near-verbatim the same language as `CarryFundingDispersionRankAllocator`'s
own docstring, while `CARRY_FUNDING_RANK` is explicitly a legacy alias for the unrelated hierarchical
`CarryBasisPerpRankAllocator`. **Shipped — `strategy-service@06253843`**, content-verified at origin. First ship
attempt hit a real line-length lint failure (fixed); a second, harmless artifact along the way: a file-watcher
system-reminder caught the working tree mid-quickmerge showing the OLD content — this was quickmerge's own
internal stash/checkout mechanics transiently touching the file, not a real revert or a peer-session collision (no
stash existed afterward, no other session's quickmerge was touching this repo, and the final staged/pushed content
was correct throughout). Pinning test
inverted: `test_only_the_ambiguous_rank_engine_remains_unreachable` → `test_only_the_legacy_alias_rank_engine_remains_unreachable`,
now pinning `CARRY_FUNDING_RANK` (the harmless deprecated alias) as the sole unreachable rank engine instead.

**Major finding — the entire "Position adapters and venue coverage" plan section was stale from birth.** All 4 of
its todos (asymmetry, CeFi dispatch, hot-swap contradiction, orphan-coverage) turned out to already be resolved by
prior sessions dated 2026-08-14 through 17 — before this plan was even authored on 2026-08-19. Discovered while
starting the CeFi-dispatch todo the user prioritized: `git log` on the target file showed a commit
(`strategy-service@c44322ddc0`, `slot-29·planning`, 2026-08-17) already fixing the exact bug the todo described.
Pulling that thread through the section's 3 sibling issue docs found the same pattern in all of them — 20/20,
1/1, and 4/5 todo items already checked `[x]` respectively, each with real shipped SHAs. **Root cause: this plan
section was authored without checking `git log` / the issue docs' own todo-completion state against the plans that
were actively being worked in parallel the week before.** The general lesson: before writing a plan todo from an
issue doc's headline finding, read the issue doc's OWN todos/Progress-Log section first — a finding can be true
and its fix can already be shipped, and only the plan text is what's stale. All 4 todos corrected in place (flipped
to `[x]` with the discovery evidence, not silently deleted) rather than left to mislead the next session into
redoing already-done work. Zero net-new code was needed for this entire plan section; what shipped this session
(2 commits) is the checkbox-currency-correction, plus the one genuine ranker decision above.

## Progress Log — 2026-08-20 session 4

**Real code shipped**: W6 overlays — `strategy-service@ed9ff26875` (rank-buffer hysteresis + no-trade band, both
new tested guard-rail mechanisms; `funding_dispersion.py`'s misleading overlay-status docstring corrected). Full
detail in the sibling plan (`strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md`), summarized in
this plan's own W6 todo.

**Second major stale-plan sweep, this time the features-service/ml-service section.** Same method as session 3's
position-adapter sweep (read the cited issue doc's own todos/Progress-Log before treating a plan headline as
current), applied to all 6 items in "features-service and ml-service". Result: **every single item was either
already resolved or correctly gated on a human decision that predates this plan** — none were genuinely
agent-actionable "just go build it" work:

- Delta_one PREDICTION-bucket bug: already fixed (`features-service@09be801b`) via a features-service-side
  override (`_resolve_mdps_bucket`) that special-cases the one real upstream dependency — the underlying naive
  method it works around (`_format_template_vars`) lives in `unified_trading_library` (T1's repo), confirmed still
  naive there but correctly not touched (cross-repo, and already effectively mitigated at the real call site).
- Universe-filter settlement-suffix claim (P2): fully resolved, 5/5 todos done, dated back to 2026-08-06.
- Onchain featureless shards: mechanical piece shipped 2026-07-30; the remaining scope (building 5 new
  protocol-specific MTDS chain-field collectors) has been independently re-confirmed FIVE times by different
  na-eligibility-audit passes as needing a human data-source-per-protocol scoping decision, not a mechanical build.
  A sixth re-derivation of that same conclusion would have wasted exactly the effort those audits exist to save.
  **Superseded 2026-08-20 session 9 in the parent plan**: this framing turned out to be too broad — most of it was
  a wiring bug (dead-code calculators never called by the live dispatch) and a governance-parameter research gap,
  not a design question. See the parent plan's session 9 entry.
- MEV opportunity-detection producers (BACKRUN/JIT_LIQUIDITY/LIQUIDATION_BUNDLE): the issue doc's own author
  already scoped all 3 calculator-builds as needing "a design decision on exact derivation, not a blind guess" —
  inventing plausible MEV-opportunity formulas for a live strategy would be fabrication. Also confirmed this is
  NOT a distinct ml-service item as this plan's deferred table previously implied — it's strategy-service +
  features-service scoped, no separate ml-service gap found.
- Calendar domain manifest-tracking gap: gated on an unresolved `[REVIEW]` design question (do calendar
  data_types even belong in the Layer-1 EXPECTED universe) that must land before the mechanical `record_captured`
  wiring makes sense.
- `corporate_actions` banned-vendor removal: confirmed ZERO live production blast radius (built-but-never-run, no
  scheduler/Cloud-Run-job/orchestrator dispatch anywhere) and genuinely `[OPERATOR]`-gated on a vendor
  data-quality decision (yfinance vs. a paid contract), not a credentials gap — did not unilaterally pick a
  vendor for live financial data without that sign-off.

**The pattern holds across two independent sweeps now (session 3: position adapters/venue coverage; session 4:
features-service/ml-service)**: this plan's per-item descriptions were written from issue-doc HEADLINES without
reading those docs' own todo-completion state or their own author's design-decision gating. All corrections are
now in place with evidence rather than left to mislead. **Practical implication for whoever resumes this plan**:
before starting ANY remaining unchecked todo in this file, grep the cited issue doc's own `## Todos` and
`## Progress Log` sections first — the plan text alone is not reliable evidence of current state.

**What's left with genuinely new agent-executable scope in this plan, after two full sweeps**: none found this
session. Everything remaining is either `[OPERATOR]`-gated (corporate_actions re-sourcing, calendar shard-atom
question, `CARRY_FUNDING_DISPERSION_RANK`-class rulings), needs real design work before any code can be written
(beta-hedge/vol-target book-layer overlays, MEV calculators, onchain MTDS collectors), or depends on another
tranche (T1's `PATH_REGISTRY` `mode=` fix for W16/W18's canonical-paths half). The Close-out section's non-spine-tail
sweep and the two-artefact re-derivation remain legitimate next steps, but are sweep/verification work, not new
builds.

## Progress Log — 2026-08-20 session 5

**Operator directive mid-session: "did you recheck plans at LDR because several rulings landed today."** Had not —
pulled LDR (17 commits behind) and found a real, materially-relevant batch: `PATH_REGISTRY {mode}` ruled (migrate,
not quarantine — the W16/W18 blocker), `corporate_actions` vendor ruled (Yahoo Finance — my own P0 item marked
`[OPERATOR]`-gated last session), plus a large new architecture doc
(`/codex/04-architecture/cross-domain-state-fabric.md`, R1-R27) with real strategy-service implications (position
vectors R22, kill-switch declare/detect split R21) not yet built anywhere. **Lesson carried forward**: mid-session
LDR re-pulls for operator rulings are not optional on a long session — this workspace ships rulings continuously
and a plan's "blocked" state can go stale hours into the same session, not just across sessions.

**Collision risk found and handled, not silently worked around.** A separate, freshly-created 8-tranche
"state-fabric reconciliation audit" dispatch
(`/plans/audit/results/state_fabric_reconciliation_dispatch_2026_08_20.md`) has its OWN T3 (features-service +
greeks-service) / T4 (strategy-service) numbering, colliding with this plan's T3 identity, and its own
collision-check safety item was unchecked before dispatch. Live AO-backlog check for a dispatched job failed
(orchestrator `:8765` connection refused — infra issue, not routed around). Per operator decision: continued this
session's work (audit-only tranches don't refactor code, worst case is a finding filed against a stale snapshot —
a cheap, familiar class of problem this session has fixed a dozen times already) and left an honest partial-data-
point note on that dispatch doc's collision-check item rather than either checking it off (would overclaim — I only
know my own slot's state) or ignoring it (the next reader gets no signal at all).

**Shipped**: `features-service@fa78040e30` — Yahoo Finance replaces the banned-vendor Polygon.io
`corporate_actions` adapter (full detail on the flipped checkbox above). `unified-trading-pm@ebaa20df4d` — corrected
`tradfi-databento-sourcing-ssot.md`'s stale removal-complete banner (third time this exact claim needed correcting).

## Progress Log — 2026-08-20 session 6

**Worked the `## Inbound requests` section for the first time** — 2 of T1's `[FROM-T1]` items were small, well-scoped,
mechanical fixes; both shipped `strategy-service@8a7f80e8`: (1) `gcs_storage_service.py::write_instructions` was
hand-rolling its own `strategy_instructions` path, bypassing T1's `mode=` PATH_REGISTRY fix — now routes through
`build_path()`, byte-parity with the read side (`pnl/adapters/domain_adapter.py`), zero behavior change since it had
zero callers. (2) `staked_basis.py`'s 8-entry hardcoded `_STAKING_PROTOCOL_CHAIN` dict deleted, replaced with UAC's
`get_chain_for_protocol()` — a cross-repo parity test on the UAC side already pins all 8 of this repo's exact values.

**The P0 item (counterparty-facing surface + messaging bridge) got a real, evidence-based re-scoping, not a build.**
Traced the actual code: a working publish→subscribe→execute bridge already exists via UTL `EventTransport` but is
scoped narrowly to 3 multi-leg strategy families (`AtomicInstruction`/"Group B"). For the other ~56 archetypes
(`StrategyInstructionEnvelope`, the general type), the live/paper caller of the orchestrator's tick loop could not be
located — one candidate (`Phase6Driver`) is itself unwired dead code, the other (`V2BatchHarness`) is batch-only. This
is a genuine open question (not yet a design decision, not yet buildable) rather than a straightforward "add a publish
call" — routes real trading decisions once live, so traced rather than guessed. Full detail + the recommended next
trace (follow `paper_run_attribution.py`'s real call chain) on the flipped-but-still-partially-open checkbox above.
Did not attempt the HTTP/WebSocket counterparty surface (needs real product/security design, not mine to invent).

**Same-session correction, immediately after**: did the recommended trace myself rather than leave it for later,
and found a DIFFERENT answer than the "no live/paper caller found" claim just written above — corrected in place
on both the inbound-request item and the W9/W10/W13 deferred-table row, not left to mislead. Real driver:
`GroupBRunner` (`engine/backtest/runner.py`); `paper_run_attribution.py`/`paper_run_passive.py` have zero
production callers and are retracted as "the shared path." Lesson worth stating plainly: a subagent's relayed
claim ("confirmed real, wired") was carried forward and re-asserted twice this session without independently
re-checking the literal call site each time — the fix each time was a direct grep, seconds of work. Cite a
subagent's finding as ITS finding until independently re-verified, not as an established fact.

## Session 2026-08-21 (evening wave) — agent-orchestration recovery + operator-decision resolution + backlog work

**Shipped this wave**: `strategy-service@aecc9866` (MONTH_ABBREV centralization, W7),
`execution-service@fca9b729fa` (stale-producer-detection kill-switch condition, T3's own todo — flipped in
main plan), `pm@4568d61096` (ARCHETYPE_CAPABILITY_REGISTRY fold-in to venue-eligibility resolver todo + 2 new
design docs), plus the earlier-in-session batch already cited in the main plan (Deribit margin model,
candidate-wallet liquidation scanner, Polymarket/Betfair paper-mode proofs, live Betfair streaming fix,
instrument hot-swap guard, real strategy_orders/positions/pnl producer).

**Two new operator-direction design docs filed** (verbatim architecture captured, NOT built — real follow-on
scoping work, next session should read these before touching position/subscription code):
- `/plans/active/issues/centralized_position_read_strategy_execution_2026_08_21.md` — one DB-backed position
  reader in strategy-service, execution-service forced to read the same way, eliminating cross-service
  position reconciliation (narrows to venue-subscription reconciliation + each service's own
  trades-vs-position-monitor check). First real todo: audit `strategy_service/position/storage/
  {database.py,position_store.py}` against this target — not investigated this session.
- `/plans/active/issues/three_layer_feature_subscription_model_2026_08_21.md` — archetype declares ALLOWED
  subscriptions, strategy instance SELECTS a subset, deployment layer AGGREGATES/dedupes across co-located
  instances. Replaces the dead `MeanReversionConfig.feature_subscriptions` field. Not designed in detail this
  session.

**Lesson — nested agent delegation is a real, recurring failure mode this session hit ~4 times**: dispatched
agents given explicit "do this yourself, don't spawn a sub-agent" instructions sometimes ignore it or have
already spawned a child before the correction arrives. One case produced a genuine near-miss (two agents
editing the same file, initially looking like a conflict — resolved by confirming they shared one working
tree, so it was one diff not two). Always verify via `ListAgents` after a "don't delegate" correction rather
than trusting the next report; check `git status`/`ps aux` for orphaned work before assuming loss.

**Lesson — shared-checkout dirty-dependency blocks usually resolve, but not always quickly**: waited 25+ min
on one `unified-api-contracts` foreign-session block that turned out to be a real, large, actively-live
refactor (landed as `e9bc03a9`). `--skip-preflight` is the right move once your own content is confirmed
QG-green and the blocker is confirmed foreign/unrelated — used successfully twice this session
(`execution-service@fca9b729fa`, `strategy-service@aecc9866`).

**Lesson — safe-doc-push exit 5 is a safe transient** (network/push-contention), not a content failure —
retry the identical command directly, no re-diagnosis needed. Exit 6 (plan-hygiene rejection) IS a content
failure — read the hook's own remedy line, don't blind-retry.

**Lesson — precision trap, recurring**: archetype (strategy-logic type) and asset_group/venue (defi/cefi/
tradfi) are orthogonal axes. "No tradfi archetype" is imprecise phrasing that implies tradfi needs its own
archetype type — the real gap is usually "no archetype INSTANCE wired with tradfi as its routed venue."
Caught and corrected once this session (`ibkr_place_order_guard_determinism_proof_infeasible_2026_08_21.md`)
— watch for the same conflation elsewhere.

**Session-limit disruption**: hit an API session limit mid-wave (multiple dispatched agents failed
simultaneously with "session limit resets 4:40pm Europe/London"). Recovered by working directly (Bash/Edit,
no further Agent dispatches) rather than waiting — most interrupted agents had left either nothing (features-
service health_factor/LTV/RADIANT task — confirmed clean tree, never got to writing code) or real
QG-verified work already reported back before failing (calendar-archival — redone directly; W7 constants —
already shipped by the time it failed).

**Still open, not started this session** (real remaining T3 scope, see main plan for full context):
health_factor/LTV/RADIANT on-chain sources (features-service), MEV opportunity-detection feature producers
(BACKRUN/JIT_LIQUIDITY/LIQUIDATION_BUNDLE — explicitly needs a design decision, not a blind build), wizard
UI/schema exposure for the 2 already-shipped overlay mechanisms, service-config-ownership typed schema
remainder.

## Session 2026-08-21 (later) — PnL-surfaces collapse + residual/Slack machinery (W9/W10/W13)

**Task 1 — collapse the 3 PnL surfaces, `strategy-service`.** Re-verified the claim before acting: read
`compute_pnl` (`pnl/engine/orchestrator.py:426`), `calculate_execution_alpha`
(`pnl/execution_alpha/calculator.py`), and `compute_handler.py`'s real wiring in full. Finding:
`calculate_execution_alpha` is a fill-vs-VWAP-benchmark **ratio** (dimensionless execution quality, not a
dollar PnL component) — it does NOT cover hold-day interest, DeFi lending PnL (Aave liquidity index +
rate-impact adjustment), or sports-settlement routing (`SportsPnLEngine`), all three of which live ONLY in
`compute_pnl`. Deleting `compute_pnl` would have silently lost real, non-duplicated logic — corrected the
plan's own "delete if safe" framing. Fix: wired `compute_pnl` as a second engine INSIDE
`compute_handler.py::_process_attributions`, merged per-strategy with the execution-alpha rows
(`_breakdown_to_frame` / `_merge_breakdown_into_attribution`), so a single persisted `pnl_attribution` row now
carries both dimensions. `compute_pnl` is no longer dead — it is the live engine behind the registered
`--operation pnl-attribution` CLI path. Also found and fixed a SEPARATE, pre-existing, load-bearing bug while
verifying the wiring end-to-end: `PnlComputeHandler.run()` (`pnl/cli/main.py`) re-parses the FULL original
`sys.argv` with `pnl/cli/parser.py`'s OWN parser, whose `--operation` choices were `["compute"]` only — the
top-level ServiceCLI's registered operation name is `"pnl-attribution"` (`cli/service_entry.py:1084`), so
every real invocation of `--operation pnl-attribution` was argparse-exiting(2) with "invalid choice" before
ever running. This is very likely WHY no cron ever got wired — the entry point was silently broken. Fixed by
widening `choices` to `["compute", "pnl-attribution"]` (`parser.py`) and the `batch_compute`/
`get_handler_for_operation` checks (`main.py`) to accept both spellings.

**Task 2 — PnL-residual + Slack-alerting machinery (new scope, `strategy-service`).** Read `compute_handler.py`
in full before assuming the gap — confirmed fresh: no residual computation, no alerting existed. Built
`pnl/engine/residual.py`: `attributed_total_by_strategy` / `instrument_breakdown_by_strategy` sum
`compute_pnl`'s real dollar-PnL factors (realized + unrealized + interest_rate + funding_rate − gas_cost,
deliberately excluding execution alpha as a unit mismatch); `total_pnl_change_from_positions` reads two
consecutive EOD `positions` snapshots (`account_key="all", snapshot_type="eod"`) and diffs summed
`notional_usd` per strategy_id as the "real account-balance delta" ground truth; `compute_residuals` /
`alert_on_residuals` compute `residual = total_pnl_change − attributed_total` and alert via the EXISTING
`strategy_service.risk.core.alert_manager.AlertManager` (`AlertMessage` → `log_event(ALERT_SENT)` →
alerting-service → confirmed Slack channel **`#uts-live-alerts`**, per
`/codex/05-infrastructure/deployment-observability.md`'s case-insensitive leading-`live` routing rule and
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`'s `AlertEvent → alerting-service →
#uts-live-alerts` pattern — reused rather than building new Slack infra). Wired into
`compute_handler.py::_check_and_alert_residuals`, called after persistence (never blocks it). Tolerance is a
new typed config field `PnlAttributionServiceConfig.pnl_residual_tolerance_usd` (placeholder default $50,
`PNL_RESIDUAL_TOLERANCE_USD` env override, no `os.getenv`).

**IMPORTANT caveat, load-bearing, written into `residual.py`'s module docstring**: there is no PATH_REGISTRY
-wired `account_balances`/`net_equity` dataset anywhere in the fleet today (grepped `unified-trading-library`
clean — those two schemas exist only in `models/output_schemas.py`, never wired to a reader/writer) — i.e. W9
("account balances as the single strategy I/O") genuinely has not landed. `total_pnl_change_from_positions`'s
EOD-positions-notional proxy is the best REAL, live-wired substitute available today, but it does NOT net out
deposits/withdrawals/transfers, so a transfer will misattribute as a residual until W9 lands. Swap that one
function for the real W9 reader once it exists; the rest (attributed-factor sum, residual math, alerting) is
source-independent and needs no change.

**Cron wiring, `deployment-service`.** New `terraform/gcp/pnl_attribution_scheduler.tf`, mirroring
`paper_stream_scheduler.tf`'s Cloud Run Job + `google_cloud_scheduler_job` pattern exactly (same
`local.strategy_image` / `local.t1_service_account_email`). Runs `--operation pnl-attribution --mode live
--interval 1440` (the batch path needs explicit `--start-date`/`--end-date` with no rolling-days convenience,
so `--mode live`'s self-contained "today" loop was used instead — same bounded-Cloud-Run-timeout-as-natural-
stop trick paper-stream already uses), daily 04:00 UTC (after the 02:30 paper-determinism reconcile). Gated by
`var.pnl_attribution_enabled` (default true). NOT applied (no `tofu apply` run this session — declaring the
Terraform is the deliverable per the task; applying infra changes is normally a separate, reviewed step).

**Task 3 — W9 (account balances as single strategy I/O) / W13 (PnL attribution across every dimension) —
scoped, NOT built.** Both are genuinely large, multi-session builds, confirmed by direct investigation, not
assumption:
- **W9** requires: (a) a real account-balance/net-equity WRITER wired to PATH_REGISTRY (none exists — the
  `account_balances`/`net_equity` schemas in `models/output_schemas.py` are unwired specs); (b) every strategy
  consumer that currently reads `positions`/fills/ad-hoc sources instead switched to read that one balance
  surface — an audit of every strategy I/O caller is its own multi-file undertaking, not scoped here.
- **W13** ("PnL attribution across every dimension the artefacts describe") needs the artefact-defined
  dimension list enumerated FIRST (asset_group / deployment / instrument / strategy / venue / share_class —
  `PnLBreakdown` already carries most of these as fields, per `unified-api-contracts/unified_api_contracts/
  internal/risk.py:224-269`, including a pre-existing `residual_pnl`/`mark_to_market_pnl` pair that anticipates
  exactly this session's residual concept) — then each dimension's real data source confirmed present or
  flagged absent. Not attempted blind this session; the real unlock is W9 landing first (a per-instrument/
  per-strategy attribution without a real balance ground truth cannot be validated against anything).

Evidence: `strategy-service` (pnl/cli/handlers/compute_handler.py, pnl/cli/parser.py, pnl/cli/main.py,
pnl/adapters/domain_adapter.py, pnl/config.py, pnl/engine/residual.py — new file), `deployment-service`
(terraform/gcp/pnl_attribution_scheduler.tf — new file). SHAs recorded in the main plan's W9/W10/W13 section
once shipped via quickmerge (see there for the final commit references).
