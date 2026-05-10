---
title: Main Agent Ledger — Harsh side, daily-evolving
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> **The communication bus** between Harsh's main orchestrator agent (this session) and the spawned tab agents (Tab 1-5
> today). Daily-evolving live state — tab registry, today's status, recent done, open questions across plans. Workflow
> rules + onboarding spec live in [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) and
> [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md) § "Daily Work-Split Process".

## Spawned tab — boot path

If Harsh just opened a fresh Cursor / Claude Code tab and pointed you at this doc with _"work on Tab N, you are the
implementor agent, please read the instructions carefully"_:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) **first** — it has the canonical reading order + communication-bus
   rules + push discipline + pre-commit check + plan-of-record curation duties. Do not skip; the orchestration mechanics
   live there.
2. Then come back here and find your **Tab N entry** below under "Today's status → Tab registry". Your Tab N entry has:
   theme, plan-of-record paths, AI-day budget, tab-specific CLAUDE.md focus sections, sub-agent fan-out hint,
   cross-tab + cross-side handshakes, pointer to today's work-split § "TAB N" for full task brief (scope items + repos
   owned + collision boundaries + done-definition).
3. Follow the rest of the AGENT_ONBOARDING.md reading order (CLAUDE.md → SUB_AGENT_MANDATORY_RULES.md → work-split § TAB
   N → plan-of-record).
4. Boot ack: append a one-liner to [`_agent_pings.md`](_agent_pings.md) per the AGENT_ONBOARDING.md template, then start
   work.

## Bootstrap — fresh main-agent chat

If this conversation just started — Harsh's previous main-agent chat died, ran out of context, or was reset — and you're
being asked to be the main orchestrator:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) for the role definition + reading order (a fresh main reads the
   same docs as a spawned tab, just with different scope: orchestration not implementation).
2. Read [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md) § "Daily Work-Split Process" — full spec for Model
   A / Model B work-splits + universal mechanics.
3. Read today's work-split:
   [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) — the 5-tab
   assignment table + cross-side handshakes + spawn prompts.
4. Run boot checklist:
   - From `unified-trading-pm/`: `git status`, `git rev-list --left-right --count HEAD...origin/live-defi-rollout`,
     `git log --oneline -5 origin/live-defi-rollout` — see local-ahead state + recent origin activity.
   - `cat harsh_orchestrator/_agent_pings.md` — see active pings.
   - Skim "Today's status" below for the tab registry + open questions.
5. Ack to Harsh: _"Main agent online. State: N tabs in flight, M pings open, K local commits queued for push. Today's
   plan = X, Y, Z. Standing by."_

**Polling cadence**: check [`_agent_pings.md`](_agent_pings.md) every **~1 min** while Harsh is active. Stretch to ~5
min when ledger empty for 30+ min. Empty cycles produce no chat output (no flooding).

**Your role**: direction-setting + Q&A dispatch + plan-of-record curation + ping triage. **Implementation work is NOT
yours** — that's spawned tabs.

## Tab numbering convention (today: Model A 5-tab thematic)

Today's [`work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) uses Model A — **5 fixed
thematic tabs** (Tab 1-5), each with its own theme + scope + plan-of-record. **Main agent = this session, no integer
slot today**; spawned tabs use the work-split's Tab 1-5 numbering directly. Operator opens a fresh Cursor / Claude Code
tab and tells that agent _"work on Tab N tasks"_ — agent reads [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) → this
LEDGER's Tab N entry → work-split § "TAB N" → plan-of-record.

(Yesterday — D2 morning — used Model B with Tab 1 = main, Tab 2-14 = spawned. Different convention; today is Model A.
Both are valid per CLAUDE.md "Daily Work-Split Process". Convention follows the day's work-split shape.)

---

## Today's slot assignments

> **Per-tab worktree model** (codified 2026-05-10, see
> [`../codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md)). Each slot is a
> permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/<harsh-user>/<N>` (replace `<harsh-user>` with the
> actual `$USER` on Harsh's machine — set via `--operator` flag if needed). Slot is durable identity; theme rotates
> daily. Before reassigning a slot to a new theme, run `bash scripts/dev/setup-tab-worktrees.sh --reset-slot <N>`
> (verify clean + rebase onto `origin/live-defi-rollout`).

**Slot count:** TBD (Harsh declares at first `--init`; recommended 6-8 to start).

| Slot | Theme                       | Plan-of-record / scope                                         |
| ---- | --------------------------- | -------------------------------------------------------------- |
| 1    | main orchestrator + on-call | (this LEDGER) — direction-setting + Q&A dispatch + ping triage |
| 2    | (unassigned)                | —                                                              |
| 3    | (unassigned)                | —                                                              |
| 4    | (unassigned)                | —                                                              |
| 5    | (unassigned)                | —                                                              |
| 6    | (unassigned)                | —                                                              |

The daily work-split plan (`plans/active/work_split_<YYYY_MM_DD>_harsh.md`) is the authoritative source for today's
themes. This LEDGER's table mirrors that assignment for fresh tab-agents bootstrapping outside chat scrollback. When the
work-split plan flips a slot to a new theme, Harsh (or main orchestrator) updates the row above + runs
`--reset-slot <N>` before the new theme begins.

---

## Today's status (2026-05-08 D2 — afternoon reset for new 5-tab work-split)

### Tab registry

#### Tab 1 — `instruments-live-tab` 🟢 IN FLIGHT — Q1 ✅ RESOLVED 14:30 UTC; Phase 2 adapter work resuming

- **Status (last update 2026-05-08 ~14:30 UTC)**: Phase 1 instruments-service half ✅ SHIPPED. Q1 RESOLVED — operator
  picked option (a): manifest-layer re-bundling by `canonical_question_group` mirroring `instruments-service@b904785`
  shape. **Tab 1 immediate actions**: (1) resume Phase 2 adapter-level lifecycle gating (Polymarket + Kalshi adapters +
  UMI tick provider rename — all independent of writer migration); (2) defer the MTDS writer migration to next cycle
  until Ikenna locks cross-cutting [UAC]+[UTL] helper signature (operator will flag via cross-side handshake).
- **DONE 2026-05-08**:
  - `instruments-service@98bb167` — feat(predictions) per-market lifecycle ingestion in Polymarket+Kalshi adapters + 14
    unit tests.
  - `instruments-service@b904785` — orchestrator emits `prediction_canonical_question_group` shard atom + 9 unit tests +
    ManifestWriter cluster gate consuming UAC `BUNDLED_DATA_TYPES`.
  - `unified-trading-pm@7343b93` — plan-flip Phase 1 lifecycle-ingestion checkbox.
- **✅ RESOLVED Q1 in `plans/epics/predictions_master_2026_05_07.md` § Open questions** (operator picked option (a)
  14:30 UTC): manifest-layer re-bundling by `canonical_question_group` mirroring `instruments-service@b904785` shape.
  Per-row tick `data_type="trades"` stays unchanged on disk; manifest layer bundles Polymarket+Kalshi rows per
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` with
  cluster-validation gate counting market_ids active per (canonical_question_group, day). **Cross-side ordering**:
  cross-cutting [UAC]+[UTL] helper signature is Ikenna-side — operator will flag to Ikenna; Tab 1 ships per-service
  migration once helper locked. Writer migration DEFERRED to next cycle.
- **Phase 2 deferrals (named successor)**: MTDS Polymarket/Kalshi adapter lifecycle gating; `umi_tick_provider.py:225`
  data_type rename; `MARKET_LIFECYCLE` separate parquet emit; per-market_id manifest rows with cluster-coverage gate.

- **Theme**: Instruments-live + lifecycle ingestion (Phase A-E across 5 asset_groups + Predictions Phase 2+3
  - catalog-aware writer-guard).
- **Plan-of-record**:
  [`../plans/epics/instruments_live_master_2026_05_08.md`](../plans/epics/instruments_live_master_2026_05_08.md)
  - [`../plans/epics/predictions_master_2026_05_07.md`](../plans/epics/predictions_master_2026_05_07.md) Phase 2+3.
    Note: `instruments_and_market_tick_data_completion_2026_05_01` was archived 2026-05-08
    (`plans/archive/instruments_and_market_tick_data_completion_2026_05_01.plan.md`); writer-guard work item rolled into
    Tab 1's scope per work-split.
- **AI-day budget**: ~10.
- **Tab-specific CLAUDE.md sections to focus on** (in addition to § Daily Work-Split Process + the rest of CLAUDE.md): §
  "Prediction market lifecycle timing", § "Per-asset-group shard-key matrix", § "Honest absence vs fake placeholders", §
  "Four-category empty-output decision", § "Cluster validation MANDATORY at record_captured".
- **Sub-agent fan-out hint**: Phase A-E = 5 parallel sub-agents (one per asset_group) in ONE message. Predictions Phase
  2 = 3 parallel (Polymarket adapter, Kalshi adapter, UMI tick provider rename). Predictions Phase 3 = 3 parallel
  (features-prediction calculator, strategy-service archetype, reader fallback). Master integrates between phases.
- **Cross-side handshake**: HARD-ORDERS Ikenna Tab 1 lending-indices Bug 3 fix — Phase D (defi instrument lifecycle
  activation) + catalog-aware writer-guard land first; Ikenna's Bug 3 fix reads the new catalog.
- **Cross-tab handshake**: Tab 3 lands lifecycle-tabs UAC SSOT (Phase A) before you wire instruments-live UI tab content
  on top.
- **Full task brief** (scope items with priority + repos owned + collision boundaries + done-definition):
  [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) § "TAB 1 —
  Instruments-live + lifecycle ingestion".

#### Tab 2 — `features-consolidation-tab` 🟢 IN FLIGHT — Phase 0+1A+1B+2A SHIPPED; Phase 2B push-pending

- **Status (last update 2026-05-08 EOD)**: Phase 0 pre-audit + Phase 1A UAC FeatureFamily enum + Phase 1B UTL
  ManifestWriter feature_family kwarg + Phase 2A PARTIAL evidence ✅ SHIPPED. Phase 2B local skeleton committed locally;
  remote ready at `git@github.com:CosmicTrader/features-service.git`; **push pending operator authorization** +
  workspace-manifest entry registration.
- **DONE 2026-05-08** (5 commits + 1 local-only):
  - `unified-trading-pm@1de574b4` — Phase 0 pre-audit manifest (1286 lines / 152 KB; 503 py source files; 11 ext
    imports + 51 string refs).
  - `unified-api-contracts@7f63ca3` — Phase 1A `FeatureFamily(StrEnum)` + `FEATURE_GROUP_TO_FAMILY` registry; 83
    feature_groups mapped, no cross-family collisions, 9 unit tests.
  - `unified-trading-library@c16cef3` — Phase 1B `ManifestWriter feature_family` kwarg + `MissingFeatureFamilyError`
    gate; 4 record\_\* methods; 10 unit tests; production-safe.
  - `unified-trading-pm@0c8800b8` — Phase 2A PARTIAL evidence + F8 audit finding (rebased equivalent of original local
    commit `6eba7e4a`).
  - `features-service@1f2bc16` — Phase 2B LOCAL skeleton (31 files / 5425 lines / 46 deps unioned / smoke + 2/2 tests +
    basedpyright clean). **Push pending**.
- **F9 audit finding flagged**: features-service repo created under `CosmicTrader` org rather than `IggyIkenna`
  convention used by every other workspace repo — operator authorized this temporarily; long-term ownership transfer to
  IggyIkenna planned.
- **Pending operator action items** (per plan body's "Phase 2 hand-off" section):
  1. ✅ Empty GitHub remote created.
  2. ⏸ Register `features-service` in PM `workspace-manifest.json` (use `CosmicTrader` URL until F9 resolved).
  3. ⏸ Push `features-svc@1f2bc16` to origin (main agent timing).

- **Theme**: Features-repo consolidation Phase 0-7 (deadline 2026-05-13 = 5 days) + ml/features Phase 2A/2B 8-service
  `assert_no_lookahead_for_feature_group` wires + Phase 3 parquet column-pruning.
- **Plan-of-record**:
  [`../plans/active/features_repo_consolidation_2026_05_08.md`](../plans/active/features_repo_consolidation_2026_05_08.md)
  - [`../plans/epics/ml_and_features_master_2026_05_07.md`](../plans/epics/ml_and_features_master_2026_05_07.md) Phase
    2A/2B + 3.
- **Read-also (cross-side dep surface)**:
  [`../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
  (Ikenna Tab 2's plan — Phase 4-7 wires the consolidated features repo).
- **AI-day budget**: ~10. **Deadline**: 2026-05-13 (5 days from today) for Phase 0-7.
- **Tab-specific CLAUDE.md sections to focus on**: § "ARCHITECTURE 2026-05-08 — Live pipeline" (in the "Plans must
  capture full codebase impact upfront" rule context), § "Shard-granularity SSOT" ([UAC] vs [UTL] vs [per-service]
  discipline), § "Post-Plan-Phase Codex Audit HARD RULE".
- **Sub-agent fan-out hint**: Phases 0-3 = 4 parallel (pre-audit, scaffold, sub-package extract, import-rewrite); Phases
  4-7 = 5 parallel per source repo migration + 1 codex SSOT updater + 1 deprecation-banner sweeper; Phase 2A/2B
  8-service wires = 8 parallel (one per service); Phase 3 column-pruning = 1 sub-agent profiles + drops + verifies.
  Master integrates between phase boundaries.
- **Cross-side handshake**: announce Phase 4 ship in plan-of-record `## Open questions`; Ikenna pulls + starts
  live-pipeline Phase 4-7 wiring. Also: Phase 2A/2B wires couple to Ikenna Tab 2 Phase 11 ServiceEmissionPolicy slice b
  — coordinate via plan-of-record.
- **Cross-tab handshake**: features_sports_reconcile_available_at lives in features-sports-service today; during Phase 4
  import-path migration, update Tab 4's hook reference (Tab 4 wires it against current path, you update during sweep).
- **Full task brief**:
  [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) § "TAB 2 —
  Features-repo consolidation + ml/features wiring".

#### Tab 3 — `deployment-ui-tab` 🟡 PARTIAL — Q1 ✅ RESOLVED 14:50 UTC (template-edit-shipped, rollout pending Ikenna)

- **Status (last update 2026-05-08 EOD)**: Phase A foundation 4 of 5 SHIPPED (A.1 + A.3 + A.4 + A.5); A.2 ⚠️ DEFERRED to
  next Tab 3 session per operator priority direction. Phases B-H + BB ⏳ PENDING (gated on A.2 + Q1 resolution).
  **Earlier scope-vs-estimate concern** (~37 todos / 8 phases / 6 repos vs work-split ~10 AI-day estimate) was
  implicitly resolved by operator picking Phase A foundation only this session.
- **DONE 2026-05-08** (4 commits):
  - `unified-api-contracts@ba94d05` — Phase A.1 + A.5: `LifecycleClass(StrEnum)` 4 closed members + `VmPrefixSpec`
    frozen dataclass + 4 helpers + `CloudTarget(StrEnum)` GCP/AWS + `EnvironmentTier(StrEnum)` DEV/STAGING/PROD +
    hostname/env resolvers; 8 files / 817 lines / 43 unit tests; facade re-exports at 3 levels.
  - `unified-trading-pm@ebe5cc09` — Phase A.3: NEW codex `deployment-ui-architecture.md` SSOT (318 lines / 13 H2
    sections) capturing 6 top-level tabs + 4 Monitor sub-tabs + 4 orthogonal axes (lifecycle / cloud / env / service) +
    env-resolution-by-domain + cross-mode prefetch policy + auth-always-available contract.
  - `unified-trading-pm@eb8a96ca` — Phase A.4: codex `batch-live-symmetry.md` `## UX surface` section (+42 lines)
    documenting identical UX shape with single-difference Data-Status mode-toggle.
  - `unified-trading-pm@4d6f2731` — plan-flip Phase A foundation + Open Q1 entry.
- **🟡 BLOCKED Q1 case-5 BIG in `plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md` § Open questions**: STEP
  5.11 + 5.12 of workspace QG template
  (`unified-trading-pm/codex/06-coding-standards/quality-gates-template.sh:357,374`) list `CloudTarget` as banned
  protocol-specific symbol; Phase A.5 makes `CloudTarget` UAC SSOT. Once Phase B+ consumers import `CloudTarget` from
  UAC, every consumer's QG fires. **Recommendation**: option (1) — add UAC-source-dir exemption to STEP 5.11 + 5.12 then
  propagate via `rollout-quality-gates-unified.py`. Phase A.5 sub-agent flagged the same finding + same fix in commit
  message. **Routing**: Ikenna or main governance call. **Blast radius if unresolved**: Phase B+ consumers fail QG
  locally on import line; CI unaffected (feature-branch pushes don't trigger CI). Deferred routing OK ~1-2 days; should
  land before Phase B starts wiring `CloudTarget` consumers.
- **Carryover for next Tab 3 session**: A.2 typed-spec migration (mechanical; A.1 dataclass shape locked) + Q1 routing
  landing + Phase B fan-out (8 PARALLEL items: 6-tab shell + Monitor 4-sub-tab structure + Data-Status mode toggle +
  LiveFreshnessPanel + StreamingLogsPanel + LifecyclePrefetchContext + scope reduction + Deploy-fresh-only).

- **Theme**: Deployment-UI lifecycle tabs Phase A-E (UAC SSOT + 4 tab refactors + cloud-toggle + auth +
  env-resolution) + deploy_missing Phase 1+2 (Phase 2 gated on Ikenna Tab 5 IAM decision).
- **Plan-of-record**:
  [`../plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md`](../plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md)
  - [`../plans/active/deploy_missing_auto_launch_2026_05_07.md`](../plans/active/deploy_missing_auto_launch_2026_05_07.md)
    Phase 1+2.
- **Read-also (codex SSOTs)**:
  [`../codex/14-playbooks/authentication/firebase-local.md`](../codex/14-playbooks/authentication/firebase-local.md)
  - [`../codex/05-infrastructure/runtime-tiers-and-deployment.md`](../codex/05-infrastructure/runtime-tiers-and-deployment.md).
- **AI-day budget**: ~10.
- **Tab-specific CLAUDE.md sections to focus on**: § "Local Development" (full body for tier 0/1/2 + Firebase emulator +
  dev-start / dev-tiers scripts), § "Workflow Templates", § "Deploy_missing UI" (in DeFi Execution Architecture
  context).
- **Sub-agent fan-out hint**: Phase A+B = 5 parallel (UAC SSOT lifecycle column, data-status tab refactor,
  deployment-flow tab refactor, operator-actions tab refactor, alerts tab refactor). Phase C+D+E = 3 parallel
  (cloud-toggle, auth, env-resolution). Deploy_missing Phase 2 = blocked until Ikenna Tab 5 IAM decision; while blocked,
  prep test scaffold + integration test fixtures + endpoint draft (no IAM-dependent code yet).
- **Cross-side handshake**: ship auth re-shape Phase D first; Ikenna Tab 5 audit-log integration wraps it.
- **Cross-tab handshake**: Phase A UAC SSOT lifecycle column lands first; Tab 1 wires instruments-live tab content on
  top.
- **Full task brief**:
  [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) § "TAB 3 —
  Deployment-UI lifecycle tabs + deploy_missing".

#### Tab 4 — `vm-ops-tab` 🟢 IN FLIGHT — cefi sweep #40 SHIPPED; mdps-tradfi P0 issue filed; data-loss recovered

- **Status (last update 2026-05-08 ~11:54 UTC)**: cefi drain monitoring continuing (no blocking finding at probe time).
  Recovered from Tab 5 `pull --rebase` data-loss event ~11:40-11:43 UTC (auto-stash conflict on renamed paths silently
  dropped 23 sweep entries + tradfi annotation + boot-ack ping; recovered from conversation memory + pushed as
  `a736910a`).
- **DONE 2026-05-08**:
  - cefi sweeps #16-#40 (condensed iteration log appended into `cefi_master_2026_05_07.plan.md` body).
  - `unified-trading-pm@a736910a` (now rebased to `971c7a1f` post-pull) —
    `ops(tab4): cefi sweep #40 + tradfi issue-doc update — wall-clock-cap hypothesis disproven`. Local-ahead, push
    pending operator authorization.
  - **Filed P0 issue doc**: `plans/active/issues/mdps_tradfi_silent_partial_drain_2026_05_08.md` — 4
    mdps-tradfi-{2021,2022,2023,2024} VMs silent-exited 2026-05-07 ~14:00 UTC within a 3-min window with NO
    `STOPPED`/`FAILED` events, mid-processing (validation / processing-started / processing-completed /
    persistence-started). GCE instance records fully deleted. mdps-tradfi-2025 (different launch batch) is STILL RUNNING
    at T+30h+ — wall-clock-cap hypothesis DISPROVEN. **Hypothesis ranking**: (1) external force-kill at exactly 14:00
    UTC (zombie watchdog batched cull / host maintenance / coordinated operator action — strongest signal: 3-min
    coordinated exit); (2) workload-specific OOM (less likely given coordinated timing); (3) preemption (rare for
    non-spot 4-of-4 simultaneous); (4) scheduled job kill (cron culling stale-looking VMs).
- **Open / handshakes**:
  - **No 🟡 BLOCKED Q on plan body** — TradFi MDPS partial-drain is in issue doc (operator triage), not blocking
    ambiguity. defi_988 priority #3 + #4 are ⚪ DEFERRED (require operator direction on archetype scope) but Tab 4 has
    plenty of in-scope work without them.
  - **Cross-tab handshake**: Tab 5 ships any new launcher prefix in `VM_PREFIX_TO_BUCKET` BEFORE Tab 4 launches a VM
    with that prefix. Cefi drain done → Tab 5 data_status integration tests rerun.
  - **Cross-side handshake**: cefi drain report goes to Ikenna Tab 5 (master plan refresh) at EOD; cross-asset rescan:
    Ikenna Tab 3 designs schema flip + ships rescan launcher, Tab 4 operates it.

- **Theme**: Per-asset_group VM ops + reconcilers + targeted backfill — cefi drain monitoring (absorbs yesterday's
  `cefi-babysit-tab` carryover) + TradFi MDPS post-drain ES.OPT 11-cluster validation + cross-asset manifest rescan +
  sports reconciler hook + defi_988 13,632-row targeted backfill.
- **Plan-of-record**: [`../plans/epics/cefi_master_2026_05_07.md`](../plans/epics/cefi_master_2026_05_07.md)
  - [`../plans/epics/tradfi_master_2026_05_07.md`](../plans/epics/tradfi_master_2026_05_07.md)
  - [`../plans/epics/manifest_migration_master_2026_05_07.md`](../plans/epics/manifest_migration_master_2026_05_07.md)
    Stage 4
  - [`../plans/epics/sports_master_2026_05_07.md`](../plans/epics/sports_master_2026_05_07.md) Tab 3B
  - defi_988 audit (archived 2026-05-08; reference `plans/archive/issues/defi_988_missing_dates_audit_2026_05_08.md`).
- **AI-day budget**: ~8.
- **Carryover note (CRITICAL — read before starting)**: a stale `cefi-babysit-tab` Cursor / Claude Code session from
  yesterday may still be running on this PC, with uncommitted edits to `plans/epics/cefi_master_2026_05_07.plan.md`
  (sweeps #16-#36 of the iteration log; 16/24 alive, 67% drained as of 10:15 UTC sweep #36, no blank-reason RED ALERT
  triggered). FIRST ACTION: `git status` — if `cefi_master.md` is dirty, those edits are the prior session's WIP. **Do
  NOT clobber.** Default action: commit them yourself with attribution to the prior tab's iteration log + push (Tab 4
  absorbs the cefi monitoring scope today, so the WIP is in your scope to ship). Otherwise: ping operator via
  `_agent_pings.md` and wait for direction.
- **Tab-specific CLAUDE.md sections to focus on**: § "VM tarball deployment", § "VM Naming Convention", §
  "Singleton-locked launchers", § "No fire-and-forget VM launches", § "Manifest concurrency principle", § "Manifest
  phantom audit", § "Per-VM shard isolation".
- **Sub-agent fan-out hint**: cefi drain monitoring = 1 monitoring sub-agent tails events bucket + flags stalls every
  10-15 min; cross-asset rescan = 5 parallel sub-agents (one per asset_group) running scan-only + reporting CSV;
  defi_988 backfill = 5 parallel sub-agents launching VMs per top-5 priority (each launch = its own VM with proper
  VM_NAME prefix + watchdog-registered prefix + per-VM-shard isolation).
- **Cross-tab handshake**: Tab 5 ships any new launcher prefix in `VM_PREFIX_TO_BUCKET` BEFORE you launch a VM with that
  prefix. Cefi drain done → Tab 5 data_status tests rerun.
- **Cross-side handshake**: cefi drain report goes to Ikenna Tab 5 (master plan refresh) at EOD. Cross-asset rescan:
  Ikenna Tab 3 designs schema flip + ships rescan launcher; you OPERATE the launcher (run dry-run first, operator-review
  CSV, then `--apply-write`).
- **Full task brief**:
  [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) § "TAB 4 —
  Per-asset_group VM ops + reconcilers + targeted backfill".

#### Tab 5 — `mechanical-refactor-tab` 🟢 IN FLIGHT — 5 of 7 plans shipped partial; hard_schema fully BLOCKED

- **Status (last update 2026-05-08 EOD)**: 5 of 7 plans have DONE blocks for today's cycle; 1 plan
  (`hard_schema_enforcement`) fully BLOCKED per frontmatter `blocked_by: tradfi-master-2026-05-07`; 1 plan
  (`mtds_databento_path_streaming`) Phase 1 already done by Tab 7 yesterday + Phases 2-3 P2-optional + Phase 4 = Tab 4
  ops territory. **Tab 5 also caused a data-loss event** for Tab 4 + main agent ~11:35-11:43 UTC via `pull --rebase`
  auto-stash on shared dirty tree — driver of the new git HARD RULE codified after.
- **DONE 2026-05-08** (per plan):
  - **launcher_consolidation**: Tab 5 follow-up cycle (1 fresh launcher + Phase 2 unit test + Phase 4 codex doc) on top
    of Tab 11 yesterday's 10-of-30 cycle.
  - **data_status_comprehensive_test_coverage**: Wave 1 — 5 of 30 todos shipped (deployment-api regression net).
  - **mtds_databento_path_streaming**: Phase 1 already shipped Tab 7 yesterday; today's cycle marked
    no-additional-shippable-scope.
  - **mtds_per_instrument_download_api**: Phase 1.5 chain axis only (prediction `canonical_question_group` axis DEFERRED
    — collides with Tab 1's Predictions Phase 3 reader migration).
  - **api_football_minimal_flattening_removal**: Phases 1-3 + 5 shipped (`unified-trading-pm@36c40a10` flips +
    `1966b572` DONE block; rebased equivalents on origin).
  - **cme_polymarket_arb**: Phase 1 EVENT_CONTRACT enum + codex stub only; Phases 2-5 BLOCKED on predictions_master
    Phase 5 + tradfi_master (`unified-trading-pm@2d7fb6bf`).
- **⚪ BLOCKED**: `hard_schema_enforcement_2026_05_08.md` — frontmatter `blocked_by: tradfi-master-2026-05-07`
  (sequenced AFTER tradfi_master Q1+Q2 per operator decision 2026-05-08). Tab 5 cannot ship anything here this cycle.
- **No 🟡 BLOCKED Q on plan bodies** — Tab 5 made closed-set decisions about deferrals based on existing plan-body
  annotations + frontmatter blocks, not ambiguity that needed main routing.

- **Theme**: 7 plans of mechanical / parallel-safe / scoped refactor — launcher consolidation 20-of-30 + data-status
  tests (5 cats × 6 repos = 30 todos) + databento Phases 2-4 + per-instrument Phase 1.5 + hard_schema migrations × 5
  asset_groups + api_football flattening removal + cme_polymarket_arb 6 phases.
- **Plans-of-record (7)**:
  1. [`../plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`](../plans/active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md)
     (remaining 20 of 30; Tab 11 yesterday migrated 10).
  2. [`../plans/active/data_status_comprehensive_test_coverage_2026_05_07.md`](../plans/active/data_status_comprehensive_test_coverage_2026_05_07.md)
     (5 cats × 6 repos = 30 todos).
  3. [`../plans/active/mtds_databento_path_streaming_2026_05_07.md`](../plans/active/mtds_databento_path_streaming_2026_05_07.md)
     (Phases 2-4; Phase 1 shipped yesterday).
  4. [`../plans/active/mtds_per_instrument_download_api_2026_04_24.md`](../plans/active/mtds_per_instrument_download_api_2026_04_24.md)
     (Phase 1.5 chain axis; CRITICAL-PATH for DeFi instrument download).
  5. [`../plans/active/hard_schema_enforcement_2026_05_08.md`](../plans/active/hard_schema_enforcement_2026_05_08.md)
     (Phases 1-5 mechanical migration scripts per asset_group).
  6. [`../plans/active/api_football_minimal_flattening_removal_2026_05_07.md`](../plans/active/api_football_minimal_flattening_removal_2026_05_07.md)
     (16 todos; UAC normalize.py:377-381 fix + re-fetch VM + manifest flip).
  7. [`../plans/active/cme_polymarket_arb_2026_05_08.md`](../plans/active/cme_polymarket_arb_2026_05_08.md) (6 phases;
     new archetype RFC).
- **AI-day budget**: ~12.
- **Tab-specific CLAUDE.md sections to focus on**: § "VM launcher script SSOT", § "Manifest migration, NOT fallback", §
  "Per-asset-group shard-key matrix".
- **Sub-agent fan-out hint**: at boot, send a SINGLE message with 7 `Task` tool blocks (one per plan). **Paste the
  contents of `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the TOP of every Task prompt** per CLAUDE.md "Sub-Agents
  & Autonomous Agents: Full Rules Required". Each sub-agent further fans out within its plan as the plan dictates (e.g.
  data_status_test 30 todos = 30 sub-sub-agents in one message; launcher consolidation 20 launchers = 20
  sub-sub-agents).
- **Cross-tab handshake**: ship any new launcher prefix in `VM_PREFIX_TO_BUCKET` BEFORE Tab 4 launches a VM with that
  prefix. data_status integration tests assume cefi drain complete (Tab 4 reports done first).
- **Cross-side handshake**: UAC additions (api_football + cme_polymarket_arb + hard_schema_enforcement) land in distinct
  files/lines vs Ikenna Tab 1 PROTOCOL_LAUNCH_DATES flips — surgical `git add -p` mandatory if both edit UAC in the same
  window.
- **Full task brief**:
  [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) § "TAB 5 —
  Mechanical refactors + audit cluster (the dragon)".

### 🟢 All 5 tabs booted; status snapshot above per Tab N entry

Tabs 1, 2, 3, 4, 5 all booted today between 11:13-13:19 UTC. Per-tab status (DONE blocks + BLOCKED Qs + deferrals)
embedded in each Tab N entry above.

### ⚪ Main agent (this session) doing now

- Polling [`_agent_pings.md`](_agent_pings.md) ~1 min while operator active.
- Holding all push/pull/rebase ops per the new HARD RULE (`AGENT_ONBOARDING.md` § 🚨 HARD RULE).
- Standing by to: (a) ack STARTED pings + flip QUEUED → IN FLIGHT, (b) verify DONE pings + flip IN FLIGHT → ✅ DONE, (c)
  answer 🟡 BLOCKED Qs in plan-of-record, (d) field new direction from Harsh, (e) flag any push-race or rebase
  situation, (f) escalate case-5 BIG findings.

### ❓ Open questions across active plans (operator decisions pending)

| Tab   | Plan                                                              | Q                                                                                                                                                                                                          | Status                                                                                                                                                      | Action needed                                                                                                                                                      |
| ----- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Tab 1 | `predictions_master_2026_05_07.md` Q1                             | "Replace POLYMARKET writer" todo re-scope — manifest-layer re-bundling by canonical_question_group mirroring `instruments-service@b904785`                                                                 | ✅ RESOLVED 14:30 UTC                                                                                                                                       | Tab 1 ships adapter gating now; writer migration deferred until Ikenna locks helper signature                                                                      |
| Tab 3 | `deployment_ui_lifecycle_tabs_2026_05_08.md` Q1 ⚠️ case-5 BIG     | STEP 5.11+5.12 QG template lists `CloudTarget` as banned but Phase A.5 makes it UAC SSOT                                                                                                                   | ✅ RESOLVED 14:50 UTC (template edit shipped locally with narrow per-file exemption `!**/canonical/crosscutting/cloud_target.py`); rollout routed to Ikenna | Ikenna runs `scripts/propagation/rollout-quality-gates-unified.py` OR amends fix shape; UAC clean locally; Phase B+ consumer repos unblock when rollout propagates |
| Tab 4 | `issues/mdps_tradfi_silent_partial_drain_2026_05_08.md`           | All 4 hypotheses ruled out; leading hypothesis = manual `gcloud delete` 2026-05-07 14:00 UTC. Tab 4 running Cloud Logging audit-log query first per operator direction; will update plan doc with findings | 🟡 IN FLIGHT (Tab 4 querying)                                                                                                                               | Wait for Tab 4's audit-log findings; then decide (a) relaunch with `--clip-after` vs (b) accept partial                                                            |
| Tab 4 | `defi_master_2026_05_07.md` Q1 — defi_988 priorities #3 + #4 + #5 | UAC SSOT changes (`PROTOCOL_LAUNCH_DATES` tightening + ASTER chain genesis) + lending-indices LINEA/BSC routing config                                                                                     | 🟡 BLOCKED — routed to Ikenna for decision per cross-side handshake                                                                                         | Ikenna-side governance call; operator flagged 2026-05-08 ~13:00 UTC. Tab 4 holds defi_988 VM launches until Ikenna resolves                                        |
| Tab 2 | `features_repo_consolidation_2026_05_08.md` F9                    | features-service repo created under `CosmicTrader` rather than `IggyIkenna` workspace convention; transfer planned per operator                                                                            | Operator confirmed                                                                                                                                          | Future transfer + workspace-manifest registration step                                                                                                             |

### ✅ Done today (2026-05-08 D2 — afternoon 5-tab cycle)

**13 commits across 4 repos** (some local-ahead pending push):

| Repo                    | Sha                     | Tab   | What                                                                                           |
| ----------------------- | ----------------------- | ----- | ---------------------------------------------------------------------------------------------- |
| instruments-service     | `98bb167`               | Tab 1 | Predictions Phase 1: Polymarket+Kalshi adapter lifecycle ingestion + 14 unit tests             |
| instruments-service     | `b904785`               | Tab 1 | Orchestrator emits prediction_canonical_question_group shard atom + 9 unit tests               |
| unified-api-contracts   | `7f63ca3`               | Tab 2 | FeatureFamily enum + FEATURE_GROUP_TO_FAMILY registry + 9 unit tests                           |
| unified-trading-library | `c16cef3`               | Tab 2 | ManifestWriter feature_family kwarg + MissingFeatureFamilyError gate + 10 unit tests           |
| unified-api-contracts   | `ba94d05`               | Tab 3 | LifecycleClass + CloudTarget + EnvironmentTier UAC SSOTs + 43 unit tests (8 files / 817 lines) |
| features-service        | `1f2bc16`               | Tab 2 | LOCAL skeleton (31 files / 5425 lines / 46 deps unioned) — **PUSH PENDING**                    |
| unified-trading-pm      | `7343b93`               | Tab 1 | Plan-flip Phase 1 lifecycle-ingestion                                                          |
| unified-trading-pm      | `1de574b4`              | Tab 2 | Phase 0 pre-audit manifest (1286 lines)                                                        |
| unified-trading-pm      | `0c8800b8`              | Tab 2 | Phase 2A PARTIAL evidence + F8 audit finding (rebased equiv of original `6eba7e4a`)            |
| unified-trading-pm      | `ebe5cc09`              | Tab 3 | NEW codex `deployment-ui-architecture.md` SSOT (318 lines)                                     |
| unified-trading-pm      | `eb8a96ca`              | Tab 3 | codex `batch-live-symmetry.md` UX surface section (+42 lines)                                  |
| unified-trading-pm      | `4d6f2731`              | Tab 3 | Plan-flip Phase A foundation + Open Q1                                                         |
| unified-trading-pm      | `36c40a10` + `1966b572` | Tab 5 | api_football Phases 1-3+5 flips + DONE block                                                   |
| unified-trading-pm      | `2d7fb6bf`              | Tab 5 | cme_polymarket Phase 1 flips + codex stub                                                      |
| unified-trading-pm      | `971c7a1f`              | Tab 4 | cefi sweep #40 + tradfi issue-doc — **LOCAL-AHEAD, PUSH PENDING**                              |

Plus: Tab 5 launcher_consolidation 1 fresh launcher + Phase 2 unit test + Phase 4 codex doc; Tab 5 data_status Wave 1 (5
of 30 todos); Tab 5 mtds_per_instrument Phase 1.5 chain axis; Tab 4 cefi sweeps #16-#40 condensed iteration log into
cefi_master plan body.

### 📦 Push-pending (local-ahead, awaiting operator authorization)

| Repo               | Sha                                                                                                             | Owner | Awaiting                                                                                                |
| ------------------ | --------------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------- |
| unified-trading-pm | `0c8800b8` (Tab 2 Phase 2A) — already rebased equivalent of `6eba7e4a` on origin, push state needs verification | Tab 2 | Per Tab 2's plan body section: ✅ pushed                                                                |
| unified-trading-pm | `971c7a1f` (Tab 4 cefi sweep #40 + tradfi issue-doc)                                                            | Tab 4 | Operator authorize push                                                                                 |
| features-service   | `1f2bc16` (Tab 2 Phase 2B local skeleton)                                                                       | Tab 2 | Operator authorize push to `CosmicTrader/features-service`; workspace-manifest entry registration first |
| harsh_orchestrator | `LEDGER.md` + `AGENT_ONBOARDING.md` (this session's main-agent edits)                                           | Main  | Operator authorize commit + push                                                                        |

---

## Plan rename — PULLED 2026-05-08 PM (workspace-wide notice)

**Status**: `.plan.md → .md` rename + cross-reference rewrite have all landed on origin and been pulled locally.
Ikenna's commit chain: `aa72177` (rename, 34 files) → `994da1b` (.md.md double-suffix damage fix) → `cca954f`
(workspace-wide cross-reference rewrite) → `79adb5b` (Phase C codified .md filename convention) → `4ad5714` (Phase B
fold of 6 May-23 epics into masters) → `c76bc78` (reconcile 2026-05-08 daily splits with plans/epics/ restructure). All
on `live-defi-rollout`.

**For spawned tabs**: use `.md` paths (no `.plan.md` segment) when referencing files in `plans/active/` or
`plans/epics/`. `plans/archive/` + `plans/ai/` continue to use `.plan.md` (frozen historical state). The LEDGER above
uses the new `.md` paths consistently.

## Daily reset (each morning)

Per CLAUDE.md "Daily Work-Split Process" § "Daily reset (each morning)" — see that section for the full 6-step protocol.
In short:

1. Fetch + summarise incoming commits (don't auto-pull).
2. Re-read yesterday's work-split + this ledger's "Today's status" + `_agent_pings.md` for overnight pings.
3. Daily ledger sweep — remove ✅ RESOLVED Q&As >24h old; verify no stale 🟡 BLOCKED >24h.
4. Draft today's work-split items (carryover + new emergence).
5. Report to operator: "Today's plan = X, Y, Z. N items / M AI-days. Ping ledger has K open."
6. Wait for operator direction.

## Historical log

### 2026-05-08 morning (D2 Model B — 12 tabs)

Folded into [`../plans/archive/work_split_2026_05_07.md`](../plans/archive/work_split_2026_05_07.md) (parent D1-D5
split, archived 2026-05-08 by Ikenna's plan consolidation). Headline: 12 spawned tabs all ✅ DONE (Tabs 3-14:
deployment-api Phase 2 / deploy-missing Phase 1 / lending-indices 3 P0 bugs end-to-end / defi_988 audit / mtds_databento
Phase 1 / audit_followups / lending-indices VM relaunch validation / predictions Phase 1 / launcher consolidation 10 of
30 / ml-features-phase2a deferred / deploy-missing IAM proposal / defi_fork1_prep audit). Tab 2 `cefi-babysit` continued
into D2 afternoon (drain ETA 2026-05-09).

### 2026-05-07 (D1)

Folded into [`../plans/archive/work_split_2026_05_07.md`](../plans/archive/work_split_2026_05_07.md).

---

## Cross-references

- **Today's work-split**:
  [`../plans/active/work_split_2026_05_08_harsh.md`](../plans/active/work_split_2026_05_08_harsh.md) (5-tab assignment +
  cross-side handshakes + spawn prompts).
- **Workflow rules + spawn-prompt template**: [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) (read first by spawned tabs).
- **Workspace coding standards + Daily Work-Split Process spec**:
  [`../cursor-configs/CLAUDE.md`](../cursor-configs/CLAUDE.md).
- **Active pings**: [`_agent_pings.md`](_agent_pings.md).
- **Master plan**:
  [`../plans/active/master_to_live_defi_2026_05_23.md`](../plans/active/master_to_live_defi_2026_05_23.md).
- **Findings Triage Discipline**: CLAUDE.md § "Findings Triage Discipline (HARD RULE)".
- **Push discipline (conditional rule)**: CLAUDE.md § "CI Verification After Every Push (HARD RULE)" + "Daily Work-Split
  Process" § "Conditional push (the multi-agent safety valve)".
