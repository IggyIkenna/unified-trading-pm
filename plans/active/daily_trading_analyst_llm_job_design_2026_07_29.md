---
doc_type: plan
title: Daily cross-cutting LLM "trading analyst" job — design
summary:
  Design for a new daily-scheduled LLM job (operator ruling on /plans/archive/issues/blrs_g3_g10_rescope_2026_07_28.md's
  G3) that diagnoses WHY trades, PnL, ML signals, strategy decisions, and data-quality gaps happened the way they did
  across batch, live, and paper — and files issue docs when it finds real problems. Scopes it as the mechanism that
  completes BLRS Stage 4's never-built LLM-dispatch leg, verifies (and REJECTS) the operator's "pipeline_mode is the
  only cross-mode differentiator" assumption with code evidence, and specifies the concrete scheduling/account/slot
  mechanics by tracing the 4 live systemd-timer reconciler jobs.
status: active
nature: design
asset_group: [cross-cutting]
stage: [strategy, data]
repos:
  [
    batch-live-reconciliation-service,
    trading-agent-service,
    agent-orchestrator,
    unified-trading-pm,
    strategy-service,
    execution-service,
    ml-service,
    deployment-api,
  ]
scope: [engineer, admin]
tags: [llm, trading-analyst, design, blrs, scheduled-job, cross-cutting, pipeline-mode]
related:
  [
    /plans/archive/issues/blrs_g3_g10_rescope_2026_07_28.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-29
last_updated: 2026-08-20
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role:
drift_direction: advance-code
depends_on: []
source: [blrs_g3_g10_rescope_2026_07_28]
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/issues/blrs_g3_g10_rescope_2026_07_28.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    batch-live-reconciliation-service/batch_live_reconciliation_service/stages/stage4_agent_analysis.py,
  ]
---

# Daily cross-cutting LLM "trading analyst" job — design

> Authored per `blrs_g3_g10_rescope_2026_07_28.md`'s 2026-07-29 `[OPERATOR]`-ruled G3 todo. That ruling is the
> requirements source; this doc is the design. Three research passes (scheduling mechanics, data-source/pipeline_mode
> verification, BLRS Stage 4 relationship) grounded every section below in the actual current code — not the stale codex
> table or the operator's stated assumption, both of which turned out to need correction (see §0 and §2).

## 0. Scoping question, answered up front (per the todo's explicit requirement)

**This job is the mechanism that completes BLRS Stage 4's never-built LLM-dispatch leg — it is neither a strict superset
of BLRS nor a fully separate parallel system.**

Verified by direct code read (`batch_live_reconciliation_service/stages/stage4_agent_analysis.py`, full file): Stage 4
today only builds a markdown prompt (`_build_agent_prompt()`) aggregating every reconciliation stage's deviations, and
writes it to `t1-recon/recon/agent_report_{date}.md`. **It never calls an LLM, never dispatches anywhere, and nothing
downstream reads the file's content** — the module docstring's claim ("Dispatches ... to trading-agent-service ...
Publishes ... alert to alerting-service → Slack") is stale/aspirational, contradicted by the code and independently
confirmed by the parent audit (`plans/archive/2026_08/issues/batch_live_reconciliation_service_audit_2026_05_27.md:167`: "no
dispatch").

But BLRS's actual reconciliation engine (stages 0.5 through 3c) is not redundant with this new job — it answers a
structurally different question. Every metric in every BLRS stage (`alpha_pnl_gap`, `signal_direction_match_rate`,
`instruction_alignment_pct`, `file_count_match_rate`, …) is a **batch-vs-live (or paper-vs-live, or batch-vs-paper)
symmetry/determinism delta** — "did today's live run and its deterministic replay produce identical numbers." That is
valuable specifically for catching non-determinism/bit-rot in the replay path, and nothing else in the codebase does it.
This new job answers a different, **absolute-quality** question — was today's PnL good, were the ML signals accurate,
was execution sound, was the data actually complete — regardless of whether batch and live agreed with each other.

**Concretely, this job:**

- Consumes BLRS's Stage 5 output (`summary_{date}.json`, the consolidated, already-serialized deviation/metrics record —
  see `stages/stage5_results_writer.py:82-103`) as **one input among several**, not the only input.
- Retires the unbuilt half of Stage 4: once this job exists, `agent_report_{date}.md` (currently read by nothing) is
  fully redundant and can be deleted from Stage 4's write path — track that as its own follow-up todo (§5), not bundled
  into this design.
- Leaves BLRS's stages 0.5–3c (the actual diffing computation) untouched — they remain the batch=live determinism proof
  this workspace's "Batch=Live determinism spine" rule depends on.

## 1. Scheduling + AO account/slot mechanics

**Traced from the 4 live systemd-timer jobs, not assumed from the operator's "mirror the reconciler pattern" framing —
the codex table describing this (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`) is stale (says
"01:00 UTC daily" / "opus"; live reality per `plan_health.py:427-435` and the timer files is hourly retry-until-capacity
/ sonnet-forced, both flipped by 2026-07-28/29 operator rulings not yet reflected there — file that staleness as its own
doc-drift fix, §5).**

**The real mechanism**: a systemd timer on the AO's central "planning" VM fires an `OnCalendar` hourly retry (not a
literal once-daily cron — a once-daily fire that hits "no capacity" was silently losing a whole day, per operator
2026-07-29), `Persistent=true` + `RandomizedDelaySec=60`. The timer's service unit runs a
`/usr/local/bin/<job>-dispatch.sh` script that:

1. Reads `ORCHESTRATOR_INTERNAL_SECRET` from `agent-orchestrator/.env.local` (machine-to-machine header auth, not a
   JWT).
2. Idempotency-checks `GET /api/scheduled-jobs/recent` for a same-day success — skips (no slot spent) if today already
   landed.
3. `POST /api/plan-health/dispatch` with `{"pm_repo_path": ..., "mode": "<new-mode>"}`.
4. Reports outcome to `POST /api/scheduled-jobs/report`.

`plan_health.dispatch()` (`agent-orchestrator/server/plan_health.py:340-644`) maps `mode` → an `agents/<role>.md` boot
prompt (`_MODE_PROMPT_TEMPLATE`/`_MODE_AGENT_KIND`, `plan_health.py:79-92`), forces sonnet/effort-max/thinking-on for
every mode (not opus), picks a free slot + a headroom account, and spawns via the same `autospawn.do_spawn()` every
other dispatch path uses.

**Account layer** — no dedicated account. `pick_headroom_account` (`server/autospawn.py:842-885`) ranks the shared
6-account pool by `(lowest 5h%, lowest weekly%, fewest active slots)` — identical to every other spawn path. A new
`mode` gets this automatically; there is nothing to configure here.

**Slot layer** — this is where "don't collide with interactive/worker usage" actually lives, via two disjoint structural
reserves (`server/config.py:282-362`): `DEFAULT_CI_ESCALATION_SLOT_RESERVE=3` and
`DEFAULT_SCHEDULED_TASK_SLOT_RESERVE=2`. `plan_health.py`'s own `_pick_free_slot` excludes the CI reserve from what a
scheduled job may pick; the scheduled-task reserve is a **floor guarantee, not a ceiling** — a new job's dispatch can
also use general-pool slots when free, and inherits this exclusion automatically by being routed through `dispatch()`.
**No new slot config is needed for this job** — it shares the existing scheduled-task floor with the 4 current jobs.

**The one deliberate per-job choice**: the timer's fire-**minute** offset, purely to stagger dispatch POSTs.
`:00/:15/:30/:50` `:45` are taken (plan_reconciler/docs_reconciler/ag_closeout_auditor/na_eligibility_auditor) — this
job should use an unused offset, e.g. `:05`.

**Output-artifact shape — two existing precedents, this job should follow the FIRST**:

- **plan_reconciler's shape (the one to mirror)**: files a real, git-committed `doc_type: issue` doc
  (`plans/active/issues/plan_reconciler_findings_<date>.md`, narrative + checkboxed remediation todos), commits via a
  review-branch PR into `live-defi-rollout` (not a direct write), AND posts a structured JSON blob to
  `POST /api/plan-health/result` that drives dashboard/Slack surfacing. Since this job's explicit purpose is "diagnose +
  file issue docs" (operator's own words), this is the correct template — not the chat-only pattern below.
- **docs_reconciler/ag_closeout_auditor/na_eligibility_auditor's shape (do NOT mirror for the primary output)**: report
  only as chat text carried into the `/done` evidence field; no structured findings doc. Their actual file writes (when
  any) come from the underlying SKILL, not the role prompt. This job's diagnosis-and-file-issues mandate doesn't fit
  this shape.

**Build recipe** (concrete, traced from the 4 existing jobs — this is what a follow-up build-phase todo implements, not
this design doc itself):

1. A skill at `cursor-configs/skills/trading-analyst/SKILL.md` holding the actual diagnostic logic — mirror
   docs_reconciler/ag_closeout_auditor/na_eligibility_auditor's shape (skill holds logic; role file is a thin pointer),
   NOT plan_reconciler's older folded-in-prompt shape.
2. A thin `unified-trading-pm/agents/trading_analyst.md` role file that boots the worker, invokes the skill, and defines
   the plan_reconciler-style committed-findings-doc contract (frontmatter, sections, PR-not-direct-write).
3. A new `mode` string (`"trading_analyst"`) added to `plan_health.py`'s `_MODE_PROMPT_TEMPLATE`/`_MODE_AGENT_KIND`
   dicts + its `dispatch()` docstring/validation list.
4. A new `agent-orchestrator/scripts/install-trading-analyst-timer.sh`, copying the systemd timer+service+dispatch
   pattern at the `:05` offset.
5. Update `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`'s scheduled-jobs table: add this job's
   row, AND fix the stale plan_reconciler cadence/model wording while touching the table (§5).

## 2. Data sources per category — the pipeline_mode-uniformity assumption is VERIFIED FALSE

**The operator's structural claim — "since `pipeline_mode` is the only thing separating storage across batch/live/paper,
the same analysis logic/scripts should work uniformly across all three modes" — does not hold.** This was the single
most important thing to verify before designing the data-access layer, and the verification changes the design
materially (§2.6).

`PipelineMode` (`unified_api_contracts/canonical/crosscutting/pipeline_mode.py:44`) is a **market-data
capture-provenance enum** (`batch_tardis`/`live_databento`/`replay_onchain_rpc`/…) — it tags how a market-data row was
captured for MTDS/MDPS/features-service/instruments-service. It is not used for trades, PnL, positions, ML signals, or
strategy decisions. Direct code evidence, by category:

### 2.1 Trades

Three parallel storage locations across two repos, none `pipeline_mode`-keyed:

- **Ledger system** (the "four ledgers" determinism spine): `InstructionLedger` rows at
  `ledger/client_id={client_id}/run_id={run_id}/ledger_type=instruction/{run_id}.jsonl`
  (`unified-trading-library/unified_trading_library/ledger/run_writer.py:210-239,362-404`). Mode differentiator is an
  **opaque, informally-prefixed `run_id` string** (`f"paper-{...}"`,
  `strategy-service/strategy_service/cli/handlers/paper_run_handler.py:196`) plus a `TradingMode` enum field
  (`PAPER`/`BATCH`/`LIVE`) that lives INSIDE the JSON payload, not as a path partition
  (`unified-api-contracts/unified_api_contracts/internal/reconciliation.py:297-302,370-415`).
- **`execution_fills`** (`execution-store-prd-{project_id}`, `{category}/execution/by_date/day={date}/fills.parquet`,
  `unified-trading-library/.../config_interface/paths/registry.py:198-206`): the reader/writer both accept a `mode`
  kwarg (default `"live"`) but **the path template has no `{mode}` placeholder** — Python's `str.format` silently drops
  unconsumed kwargs, so **batch, paper, and live fills for the same `(date, category)` write to the identical object
  path today** (`registry.py:273-275`; this exact bug class — a template silently missing a placeholder a caller passes
  — was already caught once for a different dataset, per the comment at `registry.py:18-25`).
- **`backtest_results`** (`strategy-store-prd-{project_id}`,
  `backtest_results/strategy_id={strategy_id}/run_id={run_id}/instructions.parquet`, `registry.py:180-188`) —
  `run_id`-keyed, a third scheme.

### 2.2 PnL / positions

**Positions are never persisted as a file at all** — `materialize_position_ledger()`
(`unified_trading_library/ledger/materialize.py:447-454`) is a pure in-memory fold over `InstructionLedger` +
`PricingLedger` rows, recomputed at read time by client-reporting-api's `compute_ledger_views`. A script that expects to
"read the same pipeline_mode-partitioned position files across modes" cannot — it must either call client-reporting-api
or reimplement the fold. `PnLAttributionRow` (`unified_trading_library/pnl_attribution/emitter.py:76`) is partitioned by
`strategy_id`/`client_id`/`date`, not mode or `pipeline_mode`. A second, parallel legacy path (`positions`,
`pnl_attribution` in `PATH_REGISTRY`, `registry.py:222-235`) has the identical dead-`mode`-kwarg bug as
`execution_fills` above. HWM context: confirms the workspace's existing "HWM is never raw equity" rule
(TWR/Notional/PnL-recovery via `unified_trading_library/post_trade/hwm_invariants.py`, not `max(equities)`).

### 2.3 ML signals

`ml_predictions` (`ml-store-prd-{project_id}`, `predictions/predictions/by_date/day={date}/mode={mode}/{event_id}.json`,
`registry.py:140-148`) is the **one dataset in this survey with a genuinely working `mode=` hive segment** — batch and
live predictions land at different paths with the same schema. But: zero references to a `"paper"` mode value anywhere
in ml-service's inference code (confirmed via repo-wide grep); a second, incompatible legacy path shape coexists
(`PathRegistry.ML_PREDICTIONS`, `timeframe={timeframe}/instrument={instrument}.parquet`, no mode segment at all,
`registry.py:461`); and live-mode signals can bypass file storage entirely via a direct Pub/Sub publish
(`CascadePredictionPublisher.publish()`, `ml_service/inference/app/core/cascade_prediction_publisher.py:80-122`) — a
script reading only GCS would never see those.

### 2.4 Strategy execution decisions

`strategy_instructions` (`strategy-store-prd-{project_id}`,
`strategy_instructions/strategy_id={strategy_id}/day={date}/instructions.parquet`, `registry.py:173-179`) — same
dead-`mode`-kwarg pattern as §2.1/§2.2. The record schema (`StrategyInstruction`/`TradeInstruction`,
`unified-api-contracts/.../schemas.py:232`) carries sizing/risk fields on the instruction itself; there's no separate
"decision" table distinct from the instruction.

### 2.5 Data-quality gaps

**This already exists as a live API — do not reinvent it.** `deployment-api`'s `GET/POST /api/data-status/*` surface
(`deployment_api/routes/data_status/_status_core.py`) already answers "list current data-quality gaps": completion %,
missing shards (`POST /api/data-status/missing-shards`), coverage summary, coverage grid, catalogue, etc. This job's
data-quality-gaps input should be an API call to this existing surface, not a new manifest walk. Note the API's own
`mode` filter is a narrower binary `batch`/`live` string (`_status_core.py:38,91`), not the full `PipelineMode` enum,
and orthogonal to the paper/batch/live _trading_ axis the other 4 categories use — conflating the two axes would be a
category error.

### 2.6 Design implication

**A uniform "one script, filter by `pipeline_mode`" implementation is not viable as the operator described it.** The job
needs a **thin per-category adapter**, not one shared reader. The highest-leverage finding here:
**batch-live-reconciliation-service's own recon stages (0.5, 1, 2, 3, 3b, 3c) already implement working per-category,
per-mode adapters** — reading trades/PnL/ML-signals/strategy-decisions across batch/live/paper via their own bespoke
`{tag}/events/{date}/{service}/` archive-prefix convention (a 6th mode-differentiation scheme, used only inside BLRS:
`t1-recon/events/...` vs `live/events/...` vs `paper/events/...`). **This job's data-access layer should reuse BLRS's
existing per-stage readers** (or the already-consolidated `summary_{date}.json` they produce) rather than building six
new parallel adapters from scratch — consistent with §0's scoping (this job completes Stage 4, it doesn't duplicate
stages 0.5-3c).

## 3. LLM prompt/analysis contract + issue-doc creation

**Diagnosis, not detection** (operator's explicit requirement): the input to the LLM call is not raw metrics, it's the
ALREADY-COMPUTED deviations/gaps from §2's sources (BLRS's `summary_{date}.json` for the reconciliation-derived
categories, `/api/data-status/missing-shards` for data-quality) — the job's job is to explain WHY, not to re-implement
detection. This mirrors `stage4_agent_analysis.py`'s existing `_build_agent_prompt()` shape (per-stage `## {stage}`
sections, `Deviations:`/`Metrics:` bullets) as the input-assembly pattern, extended to cover the categories BLRS's own
stages don't reach (absolute PnL/signal/decision quality, not just symmetry).

**Prompt contract** (extends Stage 4's unused 4-item instruction block into a real, LLM-invoked analysis):

1. Identify the most significant findings across all 5 categories for the day (not just "largest deviation" —
   absolute-quality findings too, e.g. "ML signal accuracy dropped 15% vs the trailing 30-day baseline" even with zero
   batch/live deviation).
2. Classify each: data-quality issue / model drift / config change / execution slippage / genuinely-nothing-wrong.
3. For each classified-as-a-real-problem finding, produce a root-cause hypothesis + concrete suggested fix — this is the
   "diagnosis" the operator asked for, not a metrics dump.
4. Flag anything needing immediate operator review (severity gate — mirrors the workspace's own "big finding → notify
   operator" convention already used fleet-wide for findings triage).

**Issue-doc creation + dedup** (drawing directly on this workspace's own findings-triage convention, which every worker
— including the one authoring this doc — already follows):

- Frontmatter: `doc_type: issue`, `assigned_vm: planning` (or `NA` if the finding needs a human decision first, per the
  standard AO-eligibility test), `source: [daily-trading-analyst-<date>]`, `created: <date>`.
- Body: `## What I found` / `## Why it matters` / `## Recommended decision`, checkboxed remediation todos — same shape
  as plan_reconciler's existing findings docs and every issue doc in this corpus.
- **Dedup, so it doesn't re-file the same finding daily**: before filing, grep `plans/active/issues/` (and
  `plans/archive/issues/` for already-resolved instances of the SAME root cause recurring) for the same category+symptom
  signature — mirrors the exact pre-task plan/issue conflict check every worker in this workspace already performs
  (`/codex/12-agent-workflow/pre-task-plan-conflict-check.md`). If an open doc already covers the same finding, add a
  dated Progress Log entry to it ("still recurring as of <date>") instead of filing a new doc — this is the same "grep
  before writing a NEW todo" discipline `task_template.md` §3 already mandates for plan authors generally, applied to a
  machine author.
- **Escalation on repeat non-improvement**: if the SAME finding recurs N days running with no remediation landing (exact
  N is an implementation-time parameter, not a design-time constant — leave as a follow-up todo, §5), escalate severity
  rather than silently re-logging forever.

## 4. Relationship to BLRS's `agent_report_{date}.md` — restated as a concrete decision

Answered in full in §0; restated here as the concrete build-time decision: Stage 4's `_write_agent_report()` call should
be removed once this job ships (a §5 follow-up, NOT bundled into this design or into the job's own build), and Stage 4's
`_build_agent_prompt()` deviation-assembly LOGIC (not its markdown-writing side-effect) should be reused as one of this
job's per-category input adapters for the reconciliation-derived categories, per §2.6.

## 5. Follow-up todos (build-phase — not yet scoped for AO dispatch; each needs its own sizing pass)

> **Converted from prose bullets to tracked checkboxes 2026-07-31** (zero-checkbox sweep, all-9-tranches re-run —
> register: `/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md`). This doc's own Progress Log had
> already flagged the violation: follow-ups here were prose, which the "every follow-up is a `- [ ]` todo, never prose"
> HARD RULE forbids, and which made every item below invisible to every open-todo count. Content is unchanged — only the
> checkbox syntax and the per-item repo tag were added. This plan stays `assigned_vm: NA` (design doc, build-phase
> sizing not yet done), so these are tracked-but-not-dispatched.

- [ ] [BACKEND] P2. **Build the `trading-analyst` skill** implementing §2's per-category data adapters (reusing BLRS's
      existing stage readers per §2.6) + §3's prompt/dedup contract. (repo: `unified-trading-pm` (skill) +
      `batch-live-reconciliation-service` if any stage-reader refactor is needed to expose them for reuse)
- [ ] [INFRA] P2. **Wire the scheduling mechanics from §1**: new `agents/trading_analyst.md` role file, new `mode` in
      `plan_health.py`, new `install-trading-analyst-timer.sh` at the `:05` offset. (repo: `agent-orchestrator` +
      `unified-trading-pm`)
- [ ] [BACKEND] P3. **Remove BLRS Stage 4's `_write_agent_report()` write path** once the new job is confirmed live and
      its findings are landing — `agent_report_{date}.md` becomes fully redundant (§0, §4). (repo:
      `batch-live-reconciliation-service`)
- [x] ✅ [DATA] P2. Already filed: `plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md` (na-eligibility-audit 2026-08-17 stale-checkbox correction). **File the dead-`mode`-kwarg bug as its own issue doc** found in §2.1/§2.2/§2.4 (`execution_fills`,
      `positions`, `strategy_instructions`, `pnl_attribution` all accept a `mode=` parameter their path template
      silently drops, so batch/paper/live write to the SAME object path) — a real, independently-worth-fixing
      correctness bug this design's research surfaced. Explicitly NOT folded into this plan's scope: file it separately
      per the findings-triage rule, then this todo is done. (repo: `unified-trading-pm` for the issue doc;
      `unified-trading-library` for the eventual fix)
- [ ] [DATA] P2. **Fix the stale scheduled-jobs table** in
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (says opus/01:00-UTC-daily; live reality
      is sonnet/hourly-retry per the 2026-07-28/29 rulings) — do this at the same time as adding this job's row (§1
      build recipe step 5), not as a separate pass. (repo: `unified-trading-pm`)
- [x] ✅ [DATA] P2. **RESOLVED 2026-08-08 (operator ruling, NA-corpus blocker digest, cross-cutting round 5, id=48)** —
      cross-referenced in `/plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`: escalation-N = **3
      days** recurring unremediated before severity escalates (§3, "N days recurring before severity escalates");
      initial `assigned_vm` default for freshly auto-filed finding issue docs = **`planning`** (auto-dispatch to AO by
      default, not `NA`). Both policy calls now settled — wire these two constants into the §3 dedup/escalation logic
      and the §"Issue-doc creation + dedup" frontmatter template (§2.7's `assigned_vm: planning (or NA if...)` line
      above) when building todo 1's `trading-analyst` skill. (repo: `unified-trading-pm`)

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (scheduled-jobs architecture — flag as stale per
§1/§5), `/codex/04-architecture/agent-orchestrator-autospawn.md` (account-headroom gate contract),
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (batch=live determinism spine, the four ledgers),
`/codex/02-data/availability-manifest-and-data-status.md` (the existing data-quality-gaps API this job should call).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — design doc, 0 open `- [ ]` todos. FINDING for /plan-reconcile:
  its §5 'Follow-up todos' are prose bullets, not tracked checkboxes — violates the 'every follow-up is a `- [ ]` todo,
  never prose' HARD RULE, and one of them is an explicit [OPERATOR] policy call.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: fixed a duplicated entry (`blrs_g3_g10_rescope_2026_07_28.md` was listed twice, pushing
  the list to 8) and dropped the least-cited codex link (`agent-orchestrator-autospawn.md`, 2 body mentions vs.
  `agent-orchestrator-single-vm-architecture.md`'s 5) to land back at the 6-entry cap; kept the Stage-4 source path
  (`stage4_agent_analysis.py`) since it is the exact leg this design completes.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — the 2026-07-31 zero-checkbox sweep converted this doc's §5 prose
  follow-ups into 6 real tracked checkboxes (content unchanged, format-only fix), so the open-todo count moved from 0 to
  6 since the last pass, but the doc's own §5 banner still explicitly frames all 6 as "build-phase — not yet scoped for
  AO dispatch; each needs its own sizing pass", and item 6 is explicitly `[OPERATOR]`-tagged. NA remains correct.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged, 6 open todos, all in §5): items
  1-5 stay explicitly framed as "build-phase — not yet scoped for AO dispatch"; item 6 is `[OPERATOR]`-tagged
  (escalation-N + `assigned_vm` default for filed issue docs). Note for the record: this session was briefed that a
  "SIT-red-escalation" design question on this doc was RULED YES (escalate to a background worker) earlier in the parent
  session — grepped this doc + `plans/active/` + `plans/active/issues/` for "SIT-red" / "SIT red" and found no matching
  content anywhere in the corpus; item 6's actual open question (the escalation-N day-count + default `assigned_vm` for
  filed docs) shows no evidence of an operator ruling in this doc or its Progress Log. Treating item 6 as still
  genuinely open rather than assuming the cited ruling applies here — flagging the mismatch rather than guessing.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (6 entries) -- the only substantive change
  since the 2026-08-07 scout pass was item 6 (`[OPERATOR]`-tagged) resolving via a 2026-08-08 operator ruling
  (escalation-N=3 days, `assigned_vm` default planning) -- a checkbox flip, no new source/codex reference introduced;
  the Stage-4 source path + 5 plan/codex links remain accurate.
- **na-eligibility-audit 2026-08-17** [body-hash:691d5e3b57d01ef0]: KEEP-NA, stale-item corrected -- closed 1 of 5 open items (file the dead-mode-kwarg bug as its own issue doc): already filed, plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md (dated 2026-08-15) describes precisely this. Doc stays assigned_vm: NA for its 4 remaining items -- this is a design plan whose own S5 banner frames all follow-ups as build-phase, not yet scoped for AO dispatch. Cross-cutting tranche audit.
- **context-scout 2026-08-17**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Doc's own §5 banner: 'This plan stays assigned_vm: NA (design doc, build-phase sizing not yet done)' — repeatedly re-confirmed KEEP-NA by na-eligibility-audit on 2026-07-30, 08-04, 08-07 and 08-17 without reversal. (1/4 items tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for next-run reassessment.)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
