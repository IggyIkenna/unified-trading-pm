# Unified Trading System — Claude Code Instructions

> **This is the lean index of workspace rules — and the rules for maintaining THIS file. Editing CLAUDE.md? Keep this
> shape.**
>
> **General format**: each rule = a 1-line essence + a pointer to its SSOT; **condense, don't drop** (push detail to the
> codex SSOT, leave the directive + pointer here); honour the size budget below.
>
> **Conditional format (the organizing rule)**: the body splits into **always-on** (apply to every task — read it) and a
> **conditional domain index** (`§ When your task touches X`). **Only open a codex SSOT when your current task actually
> involves that rule/domain** — don't read the service / data / UI / DeFi / infra codex for a task that doesn't touch
> it. A grep-0 on a domain you're not working in is irrelevant; a rule you ARE working under, you read in full first.
> **Placing a new rule**: always-on block only if it applies to EVERY task; otherwise a one-liner under the matching
> conditional `§` (+ its codex SSOT).
>
> **Durable facts live in codex (SSOT) + a one-liner here, NEVER in agent `memory/` (HARD RULE)**: memory is per-cwd,
> local-only (never git-tracked, never reaches a VM/teammate), NOT inherited by sub-agents. Sub-agents reach
> topic-parity via `SUB_AGENT_MANDATORY_RULES.md`.
>
> **Agent memory writes are BANNED (HARD RULE)**: agents MUST NOT write to the `memory/` directory or `MEMORY.md`.
> Session-scoped findings go into the active plan's **Progress Log** section; personal/secrets-adjacent state is the
> only permitted use (operator-written only, never agent-written). At session start: if any memory files exist, delete
> them and reset `MEMORY.md` to an empty index — do not read or carry forward stale memory state.
>
> **SSOT direction (HARD RULE)**: the SSOT for a durable rule is a **codex doc — NEVER an active plan** (plans archive).
> An active plan **references** codex (it does not duplicate heavy content); CLAUDE.md references the active plan only
> for _in-flight_ work. So pointers below resolve to `codex/…`; `plans/active/…` appears only where the work is
> genuinely in flight.
>
> **Size budget — QG-ENFORCED**: CLAUDE.md ≤ **40 KB / ~10k tok**; `SUB_AGENT_MANDATORY_RULES.md` ≤ **10 KB / ~2.5k
> tok**. `scripts/quality_gates/check_agent_rules_size_cap.py` fails PM QG on breach. Hit the cap → condense a rule +
> migrate detail to codex, **never raise the cap.**

---

# Always-on (every task)

## Model tier

Default **Sonnet 4.6 / thinking: medium**; `model_tier: opus-required` only for main orchestrator / cross-repo arch
/ >200k ctx; `thinking: max` requires Opus (`medium` on Opus is always wrong); sub-agent `Agent` calls MUST set `model=`
explicitly. Self-check every task start: Sonnet on opus-required → STOP; thinking mismatch → HARD STOP. SSOT:
`codex/06-coding-standards/model-tier-selection.md`.

## Environment + how to run quality gates

QG / tests → repo `.venv` via `cd <repo> && bash scripts/quality-gates.sh` (no activation); IDE → `.venv-workspace`.
**Never run `pytest` directly.** Per-family layouts (`tests/<family>/unit/`) need `PYTEST_UNIT_DIR="tests/"` before
`source base-service.sh`. SSOT: `codex/06-coding-standards/quality-gates.md`.

## Writing code → coding standards (QG-enforced; no regressions)

When you write code, follow the coding standards — and a **`quality-gates.sh`-green tree is the contract**. The gate
ENFORCES the bans, so you don't memorise them: no `os.getenv()` (use `UnifiedCloudConfig`) / `Any` / `# type: ignore` /
`try/except ImportError` / hardcoded `"/tmp"` / inline `gs://` / direct `google.cloud`/`boto3`; UTC datetimes only;
`basedpyright` clean; lazy-import heavy ML deps; file/complexity limits; **DTZ / TID251 / fallback-import baselines only
go DOWN (no new violations on shipping)**. SSOT: `codex/06-coding-standards/` (README + quality-gates.md). Use UAC SSOT
types (`unified_api_contracts.{domain}` only — never `canonical.*`/`normalize_utils.*`/deleted dirs); deep paths are
UAC-internal.

## Git discipline + shipping pipeline

- **Ship via `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'`** — always `--agent`, scope `--files` by name.
  **CODE reaches the integration branch ONLY via quickmerge** (a raw `git push` of code is BANNED — it dodges the dep
  gates + early-exits on a clean tree so commits pile up behind main). Closed carve-out direct pushes: (1) dirty-deps;
  (2) the FF-pull-in & cross-repo PM `docs(plans):` flip; (3) PM `scripts/**` & any `.github/**` change that must reach
  `main` to unblock the pipeline. Machine guard: `Quickmerge:` trailer + `check_strict_quickmerge.py` pre-push hook;
  per-repo `quickmerge.sh` are SYMLINKS to the PM SSOT.
- **Quality gates BEFORE COMMIT — the commit is the per-repo quality boundary (HARD RULE)**: commit only from a
  `quality-gates.sh`-green tree (not just prek). **QG-sweep batching** — gate once over a batch → per-unit commits;
  committing own named files → `quality-gates.sh --no-fix` (no tree reformat); deliberate tree-wide reformat you own →
  ship mode; pure doc/plan-flip → prek only. Shared-host ≤2 full QGs at once (`max(2, floor(cores/4))`); never bulk-kill
  another slot's `pytest`/QG.
- **Commit attribution = slot + host**: author NAME `ikennaigboaka [slot-<N>·<host>]`, email = operator's GitHub account
  (Ikenna `…@gmail.com`, Harsh `…@odum-research.com`); each slot clone has its own `.git/config` (set at clone time by
  `setup-tab-worktrees.sh`).
- **quickmerge lands on LDR + stops for a service repo**; the Tier-C `ldr-to-staging-promote` drain (every 15 min)
  carries the server `quality-gates-v2` gate — **LDR never runs QG**; `--hotfix` needs a `[hotfix]` marker. **PM →
  `main` directly, NO staging** (the standing `ldr-to-main-promote.yml` PR, `*/15`, ~30-min SLA; verify by CONTENT
  `gh api …/compare/main...live-defi-rollout`, not squash-inflated `ahead_by`). `unified-trading-codex` ARCHIVED (live
  SSOT = PM's `codex/`).
- **Behind-remote / tag conflict**: `git pull --rebase --autostash` (quickmerge STAGE 0.4 auto-reconciles); genuine
  same-file conflict → `rebase --abort` + structured `QUICKMERGE_BLOCKED` exit, recover per the autostash recipe, never
  blind-overwrite; tag clobber → `git fetch origin --tags --force` + `git pull --ff-only`. **NEVER force-push a shared
  branch.**
- **LDR is the SSOT**; `staging`/`main` are projections — zero-content-delta divergence is noise to collapse, real
  main/staging-only content is back-merged DOWN to LDR first. **agent-orchestrator = STANDARD** LDR→staging→SIT→main
  (the `→main` base override stays REMOVED).
- SSOTs: `codex/08-workflows/ci-cd-flow.md` (quickmerge / strict-quickmerge / LDR-is-SSOT / branch-protection /
  deployment flow) + `codex/05-infrastructure/per-tab-worktrees.md` (commit attribution).

## CI verification after every push

Pushes to `main`/PRs run CI — verify `gh run list --branch <b> --repo <o>/<r> --limit 5`; required check (all repos) =
`quality-gates-v2`; branch protection = ruleset + classic BOTH. **Never `[skip ci]` a v2-gated promotion-PR head**
(required check goes MISSING → PR permanently BLOCKED; the literal marker ANYWHERE in the message — **incl. the commit
BODY**, even when only describing it — triggers it, so write `skip-ci`; recovery
`gh workflow run quality-gates-v2.yml --ref <branch>`); the v2-never-reported deadlock auto-recovers in-band
(`ci-failure-watcher --auto-recover`), do NOT escalate. **Force-push** (relax→do→RE-ENABLE) is initial-clean-slate only.
A scheduled/`push` workflow fires ONLY from the DEFAULT branch. **Never hand-edit a per-repo workflow copy** — edit the
template + `rollout-workflow-templates.sh` (rollout done only when every copy is committed + pushed); **bumping a GHA
action version: VERIFY the ref RESOLVES** (`setup-uv` has no `@v8`). **Breaking-detection is CONTENT-based** (AST differ
`scripts/cicd/detect_breaking_change.py`; a 0.x-minor/docstring/refactor is NOT breaking; `feat!:` is the human
override). On fail: `gh run view --log-failed`, fix root cause in real time. **`ci_status` is Firestore-SSOT** (WS-A
Phase-3): `ci-status-update.yml` writes Firestore only (per-repo-doc CAS + `is_stale_write` ordering) — NEVER re-add a
per-transition manifest commit, the `manifest-update` concurrency group, or the retired `ci-status-reconciler`; the
hourly `ci-status-consolidator` owns the manifest-cache projection (manifest stays a fallback cache, read Firestore for
live state). SSOT: `codex/08-workflows/ci-cd-flow.md`.

## Commit + Push + Flip plan checkboxes as you ship (HARD RULE)

> #1 source of false-progress. Half-1 without Half-2 in the SAME turn is a violation.

**Half 1 — commit + push at every shippable unit**: pre-commit MANDATORY `git status && git diff --cached --stat` (NO
path arg); `git restore --staged` anything not yours; stage by name, never `git add .`/`-A`. **Half 2 — flip the plan
checkbox in the SAME turn**: `N. ✅ [item] — <repo>@<sha> + evidence`, commit with the MANDATORY `docs(plans):` prefix.
**Half 3 — session-end**: non-final multi-item sessions get a `## Deferred work after <date>` table. SSOT:
`codex/12-agent-workflow/commit-push-flip-rule.md`.

## Multi-agent safety (per-slot worktrees)

Each slot = a `git clone --reference` with its OWN `.git` on `live-defi-rollout` (the `tab/<op>/N` model is RETIRED —
any such instruction is STALE); stay current `git pull --ff-only origin live-defi-rollout`; one invariant = HEAD
ancestor-or-equal of `origin/live-defi-rollout` (`slot_drift_check.py`). **Never** edit
unfamiliar/untracked/recently-pushed files, `git checkout origin/<b> -- .` / `… HEAD -- <file>` a dirty file you don't
own, verify against `FETCH_HEAD` (use `git merge-base --is-ancestor`), or force-push a shared branch. LDR push rejected
→ rebase + keep the MERGED combination; autostash conflict → `rebase --abort` + stash by name (never `git stash drop`
foreign WIP). Inherited-dirty-WIP is **LIVENESS-gated** (dead claim → inherit + commit; live claim / mtime <120s →
PROTECT). An interactive session IS slot N (long uncommitted WIP = stale-worker anti-pattern; `slot-cron-ff-pull.sh` +
`slot-git-status-report.sh` every 5 min). SSOT: `codex/05-infrastructure/per-tab-worktrees.md`.

## Agent behavior

- **Context7** for external-lib questions; **max 10 parallel agents** (different repos safe; same file never);
  sub-agents ~10× cheaper — paste `SUB_AGENT_MANDATORY_RULES.md` at spawn top (if injection fails, the agent MUST NOT
  proceed). **Finish-to-DONE / `/autonomous`** = also apply `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + drive to
  completion on a self-paced loop (handoff doc = the plan's Progress Log; termination condition + climbing metric;
  inherits every safety rule).
- **Rule-amnesia stop** — halt if an agent uses `os.getenv()` / `pip install` / direct `git push` / suggests skipping
  tests. **No `python3 << EOF` for file analysis** (`re`-backtracking runaways) — use `rg`/`grep`. **Grep-then-READ, not
  grep-then-conclude** (0 hits ≠ missing — features are runtime-resolved; READ the candidate consumer; uncertain → ASK).
  **Inspect an agent's pane with depth** (`tmux capture-pane -S -50`).
- **Async-wait / poll / background-task discipline (HARD RULE — recurring "found asleep" class)**: never report a
  backgrounded task done before its real exit; rely on the tracked-task auto-re-invoke (don't poll harness tasks); poll
  only external work on a **progress metric** (flat = STALL → diagnose); don't over-watch / no-sawtooth / don't poll
  what you can direct-check; monitors read terminal `exit_code` + manifest counts + log-mtime + a TERMINAL **measured**
  verdict (liveness `kill -0 <PID>`, no self-match); `ScheduleWakeup` / a dispatched sub-agent are NOT reliable wakes —
  arm your OWN `run_in_background` heartbeat watchdog (≤30-min) in the SAME turn. SSOT:
  `codex/12-agent-workflow/async-wait-and-poll-discipline.md`.
- **Grep codex before asking the operator for committed numbers** (`codex/14-customer-journeys/commercial-model/`,
  plans, memory).

## Plans — format + authoring discipline

- **Plan destination — ASK BEFORE CREATING (HARD RULE)**: before writing any new plan, ask the operator: _"Should this
  be an agent-orchestrator plan (picked up and executed by background agents) or a human plan (operator-driven, not
  auto-dispatched)?"_ **Default is human** (`assigned_vm: NA`) unless the operator explicitly says otherwise. Never
  create a plan and set `assigned_vm` to a live VM id without the operator confirming they want background agents to
  execute it. A plan with a real `assigned_vm` is immediately ingested and dispatched — there is no undo without
  operator intervention.

- **Format**: every todo `- [x] [SCRIPT] P0. …`. Epics in `plans/epics/<slug>.md` are everlasting (no date/estimate
  fields; require `assigned_vm`+`tier`+`priority`); active/wrapper plans `plans/active/<slug>_YYYY_MM_DD.md` carry
  `parent_epic:` + 3 estimate fields (**orphans review-blocking**); `assigned_vm:` MUST resolve in
  `orchestrator_vm_registry.yaml`. **Strict VM matching (always-on)**: a backend ingests a plan's tasks iff
  `assigned_vm == backend_id` exactly (fail-closed; no fuzzy / no env opt-out; domain = registry ids ∪ `NA`=unassigned);
  reassign = edit `assigned_vm` + push to LDR (old backend prunes, new ingests next regen tick); the
  `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` env var is RETIRED (don't re-add). **`status: draft`** = WIP / not-finalised →
  the orchestrator does NOT ingest its todos (skips ingestion + GCs already-queued tasks on a flip-to-draft); **flip to
  `active` to green-light dispatch.** SSOTs: `plans/PLAN_FORMAT.md`, `plans/epics/README.md`,
  `plans/active/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md`.
- **A plan REFERENCES codex, it does not duplicate it (HARD RULE)**: the durable rule's SSOT is the codex doc; the plan
  links to it. **When authoring or touching a plan, READ the codex docs it depends on and check the plan against them**
  — plan↔codex drift is review-blocking (this is why plans cite a `Codex SSOTs:` section). After a major phase, run the
  **post-phase codex audit** (update changed contracts / stub new patterns / SUPERSEDED-banner invalidated docs; codex
  paths enumerated in the plan or it's review-blocking).
- **Estimate calibration** (apply at plan-write time): `refactor` 0.4× · `design` 0.6× · `infra` 0.8× · `brand-new` 1.0×
  · `research` 1.2×. **Capture discoveries as plan todos immediately** (P0-P3 + provenance; never
  auto-memory/chat-summary; every deferral in a summary must already be a `- [ ]` todo). **Fanning out work = a tracked
  plan todo** (target repo named; never verbal dispatch). **Plan locking** `locked_by:` blocks archival without
  `[unlock-plan]` (ASK, never autonomous); archival = the 5-step ritual (migrate DEFERRED → banner → codex-alignment
  check → update CLAUDE.md/codex on a new contract → clear lock). **Plan hygiene** `run_hygiene_sweep.sh`; inventory
  `regenerate_active_plan_inventory.py` (orphan count >0 is review-blocking). SSOTs: `codex/11-project-management/`,
  `codex/08-workflows/estimation-calibration.md`.

## Governance + safety HARD RULES

- **Plans run to actual completion, not smoke-test green** — backfills/migrations run on real infra with
  manifest-verified rows (ADC admin on GCP `central-element-323112` + AWS `427895769566`; don't pause on infra ops).
  **Hard-stops (human-only)**: wallet keys, force-push main, 1.0.0 graduation. **Kill-switch is direction+scope-aware**:
  protective arming always autonomous; resume/un-kill autonomous only within the auto-recovery matrix (`manual_unkill` =
  human-only). SSOT: `codex/04-architecture/autonomous-recovery-matrix.md`.
- **Data pipeline correctness is the heartbeat** — an audit's issues are fixed in FULL (no deadline deferrals, no
  asset_group skipped); only operator-gated `BLOCKED-CREDENTIALS`/`-OPERATOR-DECISION`/`-UPSTREAM-OUTAGE` defer; a RED
  data audit FREEZES layer-N+1 work (foundation-completion-gate). **External data is always available** — exhausting the
  free path = a credential ask, NOT a descope; build the adapter scaffold anyway + status `BLOCKED-CREDENTIALS`. SSOTs:
  `codex/02-data/data-pipeline-correctness-hard-rule.md`, `…/external-data-always-available-rule.md`.
- **Findings triage**: in your file → fix in same commit; adjacent → fix in YOUR plan; outside-plan small+clear → ≤30
  min; ambiguous → diagnose both sides; audit-scope → wrapper plan → epic VM; outside every plan →
  `plans/active/issues/<slug>_<date>.md`; **big finding** (data-correctness / May-23 critical path / cross-repo / SSOT
  contradiction) → NOTIFY OPERATOR + issue doc. "Pre-existing" is NOT a triage criterion. SSOT:
  `codex/11-project-management/`.
- **Version graduation**: `feat!` on 0.x = MINOR; NEVER bump manually (semver-agent); graduate via
  `request-major-bump.yml`. **No summary docs** (`*_SUMMARY.md` etc.) — finish with text. **Prettier**
  `.md/.json/.yaml/.ts*` before commit. **Delete deprecated code** (no shims). **Never**
  `git reset --hard`/`clean -fd`/`restore` uncommitted work. **Runtime verification** — never "done" without running the
  code. **Citadel planning standards** (pre-audit / phased DAG / no tech debt / SSOT in UAC / foundation-gate /
  issue-doc-lifecycle) → `codex/11-project-management/`.

---

# Conditional domain index — read a target's codex SSOT ONLY when your task touches it

- **Working on a SERVICE?** Read that service's architecture doc first, skip the rest. Always-true:
  **instruments-service owns reference data + venue URLs/universe**
  (`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`); **MTDS is market-data only**; service CLIs use
  `--operation`/`--mode`/`--asset-group` (`codex/06-coding-standards/cli-convention.md`); shard-level failure isolation,
  no `raise` in per-shard loops, classify via UAC `classify_venue_error()`
  (`codex/04-architecture/shard-level-failure-isolation.md`); service infra requirements (STEP 5.61 `ServiceBootstrap`,
  5.62 `make_health_router`, `ApiKeyReloader`, typed config-reloaders, UAC schema provenance) →
  `codex/06-coding-standards/config-reloader-pattern.md`. **NO service↔service deps** (T4 depends only on
  UTL/UAC/`unified-*-interface`; integrate by API contract + mocks; SIT fires at the staging boundary) →
  `codex/04-architecture/tier-and-import-architecture.md`, `codex/06-coding-standards/integration-testing-layers.md`.
- **Working on DATA / manifest / pipeline?** 4-state `capture_status`; canonical schema v9 but **trust the actual
  distribution, not the constant**; `expected_unattempted` materialised by the WRITER (never re-derived); `source=` is
  crosscutting (`record_captured(source=…)` required); never silent placeholders; **single-walk discipline** (any new
  whole-corpus GCS walk is review-blocking); **shard atom identical across writer/manifest/status/gate/UI**;
  phantom-audit `--apply` only after `prefix_tpls` cover the new shape. SSOTs:
  `codex/02-data/availability-manifest-and-data-status.md`, `…/honest-absence-downstream-handling.md`,
  `…/pipeline-mode-partition.md`, `plans/epics/infrastructure_master.md`.
- **`pipeline_mode` / sourcing?** SOURCE-AWARE `{mode}_{source}[_{transport}]` (`source`=VENDOR only; GCS paths carry it
  left of `asset_group=`, readers PREFIX-MATCH) → `codex/02-data/pipeline-mode-partition.md`. **TradFi/Databento** (3
  datasets billing-fail-closed; `SOURCE_PRIORITY` databento-first; backfill silent-0-row gotchas; VIX=VX-futures via
  XCBF.PITCH, Barchart RETIRED) → `codex/02-data/tradfi-databento-sourcing-ssot.md`. **DeFi data gotchas** →
  `codex/02-data/defi-canonical-naming-ssot.md`. **Sports paths** `candidate_parquet_paths()`. **Manifest consolidator**
  = Cloud Run / Batch-Fargate (NOT a VM; loud-fails on stale index) →
  `codex/05-infrastructure/manifest-consolidator-ssot.md`. **Feature versioning** →
  `codex/02-data/feature-formula-versioning.md`. **Live = batch** (same code path; no live-only data_types).
- **Live = batch (event-log spine)**: MTDS/MDPS/features/ml/execution all publish/read via the UTL `EventTransport`
  facade (`unified_trading_library.streaming.event_facade`); `InMemoryTransport` for paper/colocated, Pub/Sub for live —
  same code path gives `paper(W)==batch-rerun(W)` epsilon=0. SINK_MATRIX classifies all 52 shards. SSOT:
  `codex/02-data/live-data-persistence-and-event-log.md`.
- **Writing STORAGE code?** Every bucket via `resolve_bucket_name(...)`, never inline `gs://` (QG 5.69); GCS object ops
  via UTL `gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object`, never subprocess `gcloud`/`gsutil`. SSOTs:
  `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`, `codex/05-infrastructure/gcs-object-operations.md`.
- **Touching UI?** No Python tools (tsc/ESLint/Vitest/Playwright only); TS strict; **playwright gate** — no tick without
  `[UI]` + `pw:L2 ✓` + a cited regression spec. SSOT: `codex/06-coding-standards/ui-testing-layers.md`.
- **Launching VMs / infra?** **No fire-and-forget** (STARTED <60s + ≥1 progress/hr + STOPPED/FAILED; verify T+10min);
  launchers in `deployment-service/scripts/vm/` (name in `VM_PREFIX_TO_BUCKET` + `lifecycle_class`; zone
  `asia-northeast1-c`); per-VM shards `VM_NAME=<tag>` + `MANIFEST_PER_VM_SHARDS=true`; **pre-migration drain** (stop ALL
  VMs both clouds, consolidate, snapshot before any GCS cutover); every compute unit is a classified DEPLOYMENT TARGET
  (`classify_deployment_target`). SSOTs: `codex/05-infrastructure/vm-tarball-deployment.md`,
  `…/deployment-observability.md`.
- **Working on DeFi EXECUTION?** Credential convention; `DefiErrorCode` (35 codes);
  IS→MTDS→features-onchain→strategy→execution; removed providers (Elysium/Arkham/Bloxroute/Infura/Kaiko/Polygon.io) — do
  NOT reference; Pyth Solana-only; custody `CLOUD_KMS_ENCRYPTED`. SSOT:
  `codex/04-architecture/defi-execution-overview.md`.
- **Touching TRANSFERS / funds / clients?** **HARD: funds NEVER move between clients** — every transfer scoped to one
  `client_id` (`TransferCoordinator` raises `CrossClientTransferForbiddenError`); "cross-client rebalancing" framing is
  review-blocking. Per-client isolation = one subprocess per client. SSOTs:
  `codex/04-architecture/client-funds-isolation.md`, `…/per-client-isolation-architecture.md`.
- **Strategy / PnL / HWM / promote?** **HWM is never raw equity** (TWR / Notional / PnL-recovery) →
  `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`. **Batch=Live determinism spine** — paper(W) MUST
  equal batch-rerun(W) trade-for-trade (ε=0 PROOF); four ledgers; integrate via canonical `InstrumentKey` derivation →
  `codex/09-strategy/operational/paper-batch-live-reconciliation.md`. **Promote** (CLI primary / UI secondary;
  `paper_1d`→`live_early` only pre-May-23) → `codex/04-architecture/promote-workflow-architecture.md`.
- **Peripheral script dir / one-off?** Wire into the primary-consumer's `quality-gates.sh`; one-offs are TEMPORARY
  (delete after prod-run); **lifecycle marker** (`# Epic:` / `# Lifecycle:` / `# Delete-when:`) on every `scripts/`
  file. SSOT: `codex/06-coding-standards/script-homes.md`.
- **Runbooks**: declare `owner`/`cadence`/`verifier`/`last_executed` (missing = review-blocking). **Cross-plan
  banners**: launching a VM / in-flight refactor → add `> **🟢/🟡 …**` to every affected plan.

---

## System map + workspace configs

Repo map: events→UTL · schemas→UAC · cloud→unified-cloud-interface · market data→MTDS · execution→execution-service ·
reference data→instruments-service (`URDI` phantom) · UI→`unified-trading-system-ui` (incl. DART) + `deployment-ui`
(devops + launch consoles; `user-management-ui` ARCHIVED) · orchestration→`agent-orchestrator` (uvicorn :8765).
**deployment-api** = single deploy/launch+subscriptions backend for both UIs. **TWO LIVE VMs**: Central/Orchestrator (id
`planning` = `i-0c9b283b31d6b5ca7`, EIP 13.113.200.22 — only this VM's health matters) + Human-Planning
(`i-0dd9812a96cdda5dc`, interactive only); per-epic fleet NOT running. Workspace configs canonical in
`unified-trading-pm/cursor-configs/` (setup `scripts/workspace/setup-workspace-config-symlink.sh`; strict basedpyright).
Claude Code settings inherited by symlinking `~/.claude/settings.json` + per-slot `.claude/settings.json` →
`cursor-configs/settings.json` (don't commit personal `model`/`theme` drift in it) → `codex/05-infrastructure/claude-code-settings-symlink.md`.
Analysis: `rg --glob '!.venv*' --glob '!build' --glob '!tests'`. **Workflow-capable `GH_TOKEN`**:
`source scripts/workspace/load-gh-token.sh`. **agent-orchestrator auth**: dashboard JWT HS256 (central only) / internal
proxy ES256 / accounts via setup-token env files, never `.credentials.json`; backlog plan-driven
(`regen_backlog_from_plan.py`, never hand-edit `backlog.yaml`); runtime self-heals (AutoSpawn/failover/ watchdog ON —
never manually kill tmux). SSOTs: `codex/04-architecture/runtime-deployment-topology.md`,
`…/agent-orchestrator-overview.md`.
