# Unified Trading System — Claude Code Instructions

> **Lean index of workspace rules — and the rules for maintaining THIS file.**
>
> **Format**: each rule = 1-line essence + SSOT pointer; **condense, don't drop** (push detail to codex, keep the
> directive + pointer here); honour the size budget below.
>
> **Conditional format**: body splits into **always-on** (every task) and a **conditional domain index**
> (`§ When your task touches X`) — open a codex SSOT only when the task touches that domain, then read it in full. **New
> rule**: always-on only if it applies to EVERY task, else a one-liner under the matching `§` (+ codex SSOT).
>
> **Durable facts live in codex + a one-liner here, NEVER in agent `memory/` (HARD RULE)**: memory is per-cwd,
> local-only, NOT inherited by sub-agents — they reach topic-parity via `SUB_AGENT_MANDATORY_RULES.md`.
>
> **Agent memory writes are BANNED (HARD RULE)**: never write to `memory/` or `MEMORY.md`. Session findings go to the
> plan's **Progress Log**; the only exception is operator-written personal/secrets state. Session start: delete any
> memory files and reset `MEMORY.md` to an empty index — never carry forward stale memory.
>
> **SSOT direction (HARD RULE)**: SSOT for a durable rule is a **codex doc — never an active plan** (plans archive). A
> plan **references** codex, never duplicates it; CLAUDE.md references an active plan only for _in-flight_ work — so
> pointers below resolve to `codex/…`, and `plans/active/…` only where genuinely in flight.
>
> **Size budget — QG-ENFORCED**: CLAUDE.md ≤ **40 KB**; `SUB_AGENT_MANDATORY_RULES.md` ≤ **10 KB**.
> `check_agent_rules_size_cap.py` fails PM QG on breach — condense + migrate to codex, **never raise the cap.**

---

# Always-on (every task)

## Model tier

Default **Sonnet**; model tier (sonnet/opus/fable) and effort (`low<medium<high<xhigh<max`) are INDEPENDENT axes (ground
truth: `agent-orchestrator/server/model_tier.py`). **`opus-required` = ZERO categories** — opus is manual-only
(`main.md` is sonnet+`default`). **`sonnet_variant: light|default` picks sonnet-4.6 vs sonnet-5** — **sonnet-5 is the
default for EVERYTHING** (2026-08-08 ruling); `light` is an explicit opt-in nothing declares — re-check pricing before
re-arming it. Every `assigned_vm: planning` plan defaults to `effort: max`. **Effort default (2026-07-22)**: no declared
tier → todo-count-derived (`xhigh`/`max` past `LARGE_PLAN_TODO_THRESHOLD`), not silent "medium". Sub-agent `Agent` calls
MUST set `model=` explicitly. Self-check every task start: Sonnet on opus-required → STOP; effort mismatch → HARD STOP.
SSOT: `/codex/06-coding-standards/model-tier-selection.md`.

## Environment + how to run quality gates

QG / tests → repo `.venv` via `cd <repo> && bash scripts/quality-gates.sh` (no activation); IDE → `.venv-workspace`.
**Never run `pytest` directly.** Per-family layouts (`tests/<family>/unit/`) need `PYTEST_UNIT_DIR="tests/"` before
`source base-service.sh`. SSOT: `/codex/06-coding-standards/quality-gates.md`.

## Writing code → coding standards (QG-enforced; no regressions)

When you write code, follow the coding standards — and a **`quality-gates.sh`-green tree is the contract**. The gate
ENFORCES the bans, so you don't memorise them: no `os.getenv()` (use `UnifiedCloudConfig`) / `Any` / `# type: ignore` /
`try/except ImportError` / hardcoded `"/tmp"` / inline `gs://` / direct `google.cloud`/`boto3`; UTC datetimes only;
`basedpyright` clean; lazy-import heavy ML deps; file/complexity limits; **DTZ / TID251 / fallback-import baselines only
go DOWN (no new violations on shipping)**. SSOT: `codex/06-coding-standards/` (README + quality-gates.md). Use UAC SSOT
types (`unified_api_contracts.{domain}` only — never `canonical.*`/`normalize_utils.*`/deleted dirs); deep paths are
UAC-internal. **Removed vendors — FLEET-WIDE ban, not DeFi-only: Elysium · Arkham · Bloxroute · Infura · Kaiko ·
Massive-fka-Polygon.io** (`polygon` = the CHAIN).

## Git discipline + shipping pipeline

- **Ship via `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'`** — always `--agent`, scope `--files` by name.
  **CODE reaches the integration branch ONLY via quickmerge** (a raw `git push` of code is BANNED — it dodges the dep
  gates + early-exits on a clean tree so commits pile up behind main). Closed carve-out direct pushes: (1) dirty-deps;
  (2) the FF-pull-in & cross-repo PM `docs(plans):` flip; (3) any `.github/**` & the GATE-INFRA subset of `scripts/`
  (`quality_gates/`, `quality-gates-base/`, `hooks/`, `cicd/`) that must reach `main` to unblock the pipeline (all-repos
  D16 2026-08-08; **NARROWED from blanket `scripts/**` 2026-08-10** — other `scripts/*.py` = gated source, it runs on
  PROD data). Machine guard: `Quickmerge:` trailer + hook; per-repo `quickmerge.sh` are SYMLINKS to the PM SSOT.
- **Quality gates BEFORE COMMIT — the commit is the per-repo quality boundary (HARD RULE)**: commit only from a
  `quality-gates.sh`-green tree (not just prek). **QG-sweep batching** — gate once over a batch → per-unit commits;
  committing own named files → `quality-gates.sh --no-fix` (no tree reformat); deliberate tree-wide reformat you own →
  ship mode; pure doc/plan-flip → `scripts/dev/safe-doc-push.sh` (runs prek; bare git races the shared index). **Ship
  scripts COMMIT FROM AN ISOLATED WORKTREE** so a peer sharing your checkout can't revert your edits (0/6→6/6 measured):
  always-on in safe-doc-push, laptop-only in quickmerge (`--isolated`/`--no-isolated`, auto-OFF on the AO VM). They bake
  in retry/mutex/flock/drift — never re-improvise reconcile-retry. **`ahead=0` + clean tree ≠ landed** (≡ work DESTROYED
  — verify `git show HEAD:<f>`; Write+`git add` in ONE step, where every measured loss sat). Ship scripts assert it:
  **quickmerge 10 / safe-doc-push 12 (nothing of yours to ship) · 13 (pushed, change absent) = RECOVER from the printed
  ref, never plain re-run**; 11=script defect; 5=safe. SSOT: `/codex/05-infrastructure/per-tab-worktrees.md`. **QG
  concurrency is RESOURCE-based, not a fixed count** (default `reservation`, 2026-08-10): admission weighs measured peak
  RSS vs live RAM + CPU under one ledger lock — just invoke `quality-gates.sh`, it queues. **Never quote a fixed cap
  number** — those are legacy `token`-mode only; read the SSOT. Never bulk-kill a peer's `pytest`/QG. Both ship scripts
  reconcile against origin before every commit and hard-fail on a genuine unresolvable conflict (never silently
  proceed); `check-quickmerge-provenance` catches a missing trailer at COMMIT time too (WARN-only until
  `QUICKMERGE_PROVENANCE_BLOCK=1`). SSOT: `/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md`.
- **Commit attribution = slot + host**: author NAME `ikennaigboaka [slot-<N>·<host>]`, email = operator's GitHub account
  (Ikenna `…@gmail.com`, Harsh `…@odum-research.com`); each slot clone has its own `.git/config`. Derivation SSOT
  `scripts/hooks/slot-identity-lib.sh` (slot-N from the PATH); audit/stamp a host via
  `scripts/dev/check-slot-commit-identity.sh [--fix]`.
- **quickmerge lands on LDR**; **default promote is LDR→`main` DIRECT — staging DORMANT** (per-repo
  `promotion_model: ldr_main` toggle; standing `ldr-to-main-promote-fleet.yml` + PM's `ldr-to-main-promote.yml`, `*/15`,
  auto-merge). **The LDR→main gate set is exactly THREE**: `sit-gate/fleet-green` (fleet-shared SIT signal, REQUIRED
  check on `ldr_main` repos) + `quality-gates-v2` (promote PR) + quickmerge-provenance — label-check / SIT-digest /
  dep-order are RETIRED/advisory, NOT blocking. `staging` KEPT + REVERSIBLE (major/breaking bump or operator decision
  routes THROUGH it; gates unchanged). **LDR never runs server QG**; `main` = reconciled projection back-merged to LDR
  (`main-backmerge-to-ldr`) — **landing on `main` DEPLOYS NOTHING**: AO self-pulls LDR (`ao-self-pull.sh`, 15-min cron,
  restarts on HEAD move), other services deploy via Cloud Build → `…/runtime-deployment-topology.md` §5. `--hotfix`
  needs `[hotfix]`. **Release**: semver-agent on `push:[main]` → git-tag mint + `publish-package` wheel to AR;
  major/1.0.0 via human staging; `reconcile_release_tags.py` = stall detector, not minter. `unified-trading-codex`
  ARCHIVED (SSOT = PM's `codex/`).
- **Behind-remote / tag conflict**: `git pull --rebase --autostash` (quickmerge STAGE 0.4 auto-reconciles); genuine
  same-file conflict → `rebase --abort` + structured `QUICKMERGE_BLOCKED` exit, recover per the autostash recipe, never
  blind-overwrite; tag clobber → `git fetch origin --tags --force` + `git pull --ff-only`. **NEVER force-push a shared
  branch.**
- SSOTs: `/codex/08-workflows/ci-cd-flow.md` (gate set / quickmerge / strict-quickmerge / LDR-is-SSOT /
  branch-protection / semver + wheel release / deployment flow) + `/codex/05-infrastructure/per-tab-worktrees.md`
  (commit attribution) — codex holds every contract now; no in-flight plan-of-record.

## CI verification after every push

Pushes to `main`/PRs run CI — verify `gh run list --branch <b> --repo <o>/<r> --limit 5`; required check (all repos) =
`quality-gates-v2`; branch protection = ruleset + classic BOTH. **Never `[skip ci]` a v2-gated promotion-PR head**
(required check goes MISSING → PR permanently BLOCKED; the literal marker ANYWHERE in the message — **incl. the commit
BODY**, even when only describing it — triggers it, so write `skip-ci`; recovery
`gh workflow run quality-gates-v2.yml --ref <branch>`); the v2-never-reported deadlock auto-recovers in-band
(`ci-failure-watcher --auto-recover`), do NOT escalate. **Force-push** (relax→do→RE-ENABLE) is initial-clean-slate only.
A scheduled/`push` workflow fires ONLY from the DEFAULT branch. **Never hand-edit a per-repo workflow copy** — edit the
template + `rollout-workflow-templates.sh` (rollout done only when every copy is committed + pushed); **bumping a GHA
action version: VERIFY the ref RESOLVES**. **Breaking-detection is CONTENT-based** (AST differ
`scripts/cicd/detect_breaking_change.py`; a 0.x-minor/docstring/refactor is NOT breaking; `feat!:` is the human
override). On fail: `gh run view --log-failed`, fix root cause in real time. **Green deploy ≠ live traffic**: a stray
Cloud Run revision pin can freeze deploys at 0% — verify `status.traffic`. **`ci_status` is Firestore-SSOT** (WS-A
Phase-3): `ci-status-update.yml` writes Firestore only (per-repo-doc CAS + `is_stale_write` ordering) — NEVER re-add a
per-transition manifest commit, the `manifest-update` concurrency group, or the retired `ci-status-reconciler`; the
hourly `ci-status-consolidator` owns the manifest-cache projection (manifest stays a fallback cache, read Firestore for
live state). **Never `gh workflow run ldr-to-main-promote-fleet.yml` to check your own promotion** — shared
single-concurrency slot; ad-hoc dispatches starve it (measured 2+ h livelock 2026-08-07). Read
`scripts/cicd/promotion_lag_monitor.py` or `gh pr list --search "chore(promote)"`. SSOT:
`/codex/08-workflows/ci-cd-flow.md`.

## Commit + Push + Flip plan checkboxes as you ship (HARD RULE)

> #1 source of false-progress. Half-1 without Half-2 in the SAME turn is a violation.

**Half 1 — commit + push at every shippable unit**: pre-commit MANDATORY `git status && git diff --cached --stat` (NO
path arg); `git restore --staged` anything not yours; stage by name, never `git add .`/`-A`. **Half 2 — flip the plan
checkbox in the SAME turn**: `N. ✅ [item] — <repo>@<sha> + evidence`, commit with the MANDATORY `docs(plans):` prefix.
**Half 3 — session-end**: non-final multi-item sessions get a `## Deferred work after <date>` table. SSOT:
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Multi-agent safety (per-slot worktrees)

Each slot = a `git clone --reference` with its OWN `.git` on `live-defi-rollout` (`tab/<op>/N` RETIRED — ignore stale
refs to it); stay current `git pull --ff-only origin live-defi-rollout`; one invariant = HEAD ancestor-or-equal of
`origin/live-defi-rollout` (`slot_drift_check.py`). **Never** edit unfamiliar/untracked/recently-pushed files,
`git checkout origin/<b> -- .` / `… HEAD -- <file>` a dirty file you don't own, verify against `FETCH_HEAD` (use
`git merge-base --is-ancestor`), or force-push a shared branch. LDR push rejected → ahead=0 ff-only-only; ahead>0
`--rebase --autostash`+`restore --staged .` pre-add — same after a failed commit: restore-staged first, else a peer
session absorbs it; conflict `rebase --abort` + stash by name (never `git stash drop` foreign WIP). Inherited-dirty-WIP
is **LIVENESS-gated** (dead claim → inherit + commit; live claim / mtime <120s → PROTECT). An interactive session IS
slot N (long uncommitted WIP = stale-worker anti-pattern; `slot-cron-ff-pull.sh` + `slot-git-status-report.sh` every 5
min). **Distinct failure mode — two operators/sessions sharing ONE slot's checkout** (interactive sessions have no
allocation mechanism, unlike AO-dispatched workers): shared index/`user.name`/`user.email` → contention + wrong commit
attribution; WARN-only `.agent-claim` liveness heartbeat + `SessionStart` collision hook mitigate (never hard-block).
SSOT: `/codex/05-infrastructure/per-tab-worktrees.md`.

## Agent behavior

- **Context7** for external-lib questions; **max 5 parallel agents** (different repos safe; same file never) —
  **parallelise AUTHORING ONLY: gate+ship stay SERIAL, deps first** (laptop-only, never AO) →
  `…/host-concurrency-and-commit-provenance.md` §5; sub-agents ~10× cheaper — paste `SUB_AGENT_MANDATORY_RULES.md` at
  spawn top (if injection fails, the agent MUST NOT proceed). **Finish-to-DONE / `/autonomous`** = also apply
  `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + drive to completion on a self-paced loop (handoff doc = the plan's
  Progress Log; termination condition + climbing metric; inherits every safety rule).
- **Rule-amnesia stop** — halt on `os.getenv()`/`pip install`/direct `git push`/skip-test suggestions. **No
  `python3 << EOF` for file analysis** (`re`-backtracking runaways) — use `rg`/`grep`. **CLAIM ≤ MEASUREMENT**: 0 hits ≠
  missing (runtime-resolved — READ the consumer; uncertain → ASK); a PROXY (line count, exit 0, green test, cached
  `origin/`) ≠ the property — measure or say you didn't → `/codex/12-agent-workflow/measurement-claims-discipline.md`.
  **Pane deep** (`tmux capture-pane -S -50`).
- **Async-wait / poll / background-task discipline (HARD RULE — recurring "found asleep" class)**: never report a
  backgrounded task done before its real exit; rely on the tracked-task auto-re-invoke (don't poll harness tasks); poll
  only external work on a **progress metric** (flat = STALL → diagnose); don't over-watch / no-sawtooth / don't poll
  what you can direct-check; **backfill/migration progress = count of TARGET artifacts created (entity-scoped,
  `time_created` not `updated`), NEVER activity** — an entity-agnostic check passes for hours while the target writes
  ZERO rows; monitors read terminal `exit_code` + manifest counts + log-mtime → a TERMINAL **measured** verdict
  (liveness `kill -0 <PID>`, no self-match); `ScheduleWakeup` / a dispatched sub-agent are NOT reliable wakes — arm your
  OWN `run_in_background` heartbeat watchdog (size-to-job — unbounded work ≤30-min, a KNOWN-duration VM job gets ONE
  monitor sized to its own documented duration, never a ≤30-min re-arm chain) in the SAME turn. SSOT:
  `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`.
- **Batch independent tool calls — the trigger is PRE-call**: before any Bash/Read/Grep ask _what else will I want to
  know regardless of this answer_, and fold it into the SAME call (compound `&&`/`;`, several `tool_use` blocks per
  message, `replace_all` over serial Edits); only result-dependent calls stay sequential. Stating it as an outcome fails
  — a reminder acknowledged ~88×/session changed nothing. Measured: 57.3% collapsible, each a ~406k prefix re-read.
  SSOT: `/codex/06-coding-standards/tool-call-batching.md`.
- **Grep codex before asking the operator for committed numbers** (`codex/14-customer-journeys/commercial-model/`).
- **Pre-task plan/issue conflict check (HARD RULE)** — before ANY task grep `plans/active/`+`issues/`: plans go
  stale/superseded between daily `/plan-reconcile` sweeps: no-flag≠current; 0 hits ≠ clear (grep-then-read) — check
  status/supersedes. Context economy: scope reads + Bash output (`grep -c`/`tail -5`, not full dumps), terse replies.
  SSOT: `/codex/12-agent-workflow/pre-task-plan-conflict-check.md`, `…/context-economy.md`.

## Doc retrieval — retrieve less but right (L0→L4, grep-native)

Finding any doc/rule/SSOT: **grep the L0 index FIRST** — `unified-trading-pm/DOC_INDEX.generated.md` (per-clone,
gitignored; absent/stale → `bash scripts/docs/refresh-doc-index.sh`; NEVER read it whole, ~200k tok — grep it). Narrow
with L1 frontmatter facets: `rg -l '^authoritative_for:.*<topic>' codex/` lands THE one SSOT; compose axes for broader
cuts (`doc_type` / `asset_group` / `stage` / `repos` / `status` / `nature` / `tags`, e.g.
`rg -l '^doc_type: codex-ssot' codex/ | xargs rg -l '^asset_group:.*defi'`). Confirm relevance via `summary:` (L2)
before opening; open ONLY the confirmed doc (L3); jump doc→code via its `code_refs` (L4, module-dir granularity). The
domain index below is the shortcut for known domains; L0/L1 grep covers everything else. SSOT:
`/codex/11-project-management/doc-frontmatter-schema.md` §1 + epic `agent_operating_framework_master` § "Target
architecture (L0–L4)".

## Plans — format + authoring discipline

- **Authoring a plan? READ `plans/active/task_template.md` FIRST (HARD RULE)** — it carries the LOCAL (`assigned_vm: NA`
  - `execution_scope: local-only`, never ingested) vs AO-DISPATCHED (`planning`) tracks and the full authoring rules.
    Headlines: **10-100 todos**; independent same-priority todos run CONCURRENTLY by default (the ONE rule: they MUST
    touch different files); `sequential: true` serialises the WHOLE plan — don't reflex-set it; partial parallelism
    isn't expressible in one plan → **SPLIT** (gated step in Plan B via `depends_on` + `gate_on_depends: true`); no
    per-todo prereq syntax; per-task `[TAG]` roles route each todo; **any AO todo with a GCS delete/`--apply` or VM
    launch needs `[OPERATOR]`+delete-safety-cite OR a stated safe-idempotent justification** (pre-filter
    `check_delete_vm_launch_gating.sh`, SSOT delete-safety codex §3a); **AO-eligible = outcome DETERMINABLE by the
    worker alone**, never an open-ended judgment/design call — resolve that first as a LOCAL plan, then dispatch against
    its outcome (SSOT `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope
    eligibility"); draft-gated phase chains. **Never hand-edit `backlog.yaml`** — author plans, the backend derives it.
- **Plan destination — ASK BEFORE CREATING (HARD RULE)**: before writing any new plan, ask the operator: _"Should this
  be an agent-orchestrator plan (picked up and executed by background agents) or a human plan (operator-driven, not
  auto-dispatched)?"_ **Default is human** (`assigned_vm: NA`) unless the operator explicitly says otherwise. **Valid
  `assigned_vm` values = `{planning, NA}` only** (multi-VM dispatch deprecated 2026-06-27). Automation work routes by
  `assigned_role` (skill-based), not VM.

- **Format**: every todo `- [x] [SCRIPT] P0. …`. **Frontmatter SSOT: `plans/PLAN_FORMAT.md`** (canonical schema via
  `/codex/11-project-management/doc-frontmatter-schema.md`) — read it for the required-key list; a copy here only rots.
  Semantics not to guess: **`status: draft`** = WIP → NOT ingested (flip to `active` to dispatch); **`depends_on`**
  documents ordering + gates archival, does NOT affect dispatch. SSOTs: `plans/PLAN_FORMAT.md`,
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.
- **A plan REFERENCES codex, it does not duplicate it (HARD RULE)**: the durable rule's SSOT is the codex doc; the plan
  links to it. **When authoring or touching a plan, READ the codex docs it depends on and check the plan against them**
  — plan↔codex drift is review-blocking (this is why plans cite a `Codex SSOTs:` section). After a major phase, run the
  **post-phase codex audit** (update changed contracts / stub new patterns / SUPERSEDED-banner invalidated docs; codex
  paths enumerated in the plan or it's review-blocking).
- **Estimate calibration** (apply at plan-write time): `refactor` 0.4× · `design` 0.6× · `infra` 0.8× · `brand-new` 1.0×
  · `research` 1.2×. **HARD RULE — every follow-up is a `- [ ]` todo, never prose** (P0-P3 + provenance; never
  auto-memory/chat-summary/a prose "next steps" note — a recurring violation). **Fanning out work = a tracked plan
  todo** (target repo named; never verbal dispatch). **A plan with every todo done + unlocked MUST be archived
  immediately (HARD RULE, recurring gap)** — don't leave it sitting `active`; `locked_by:` blocks archival without
  `[unlock-plan]` (ASK, never autonomous). SSOT for both (incl. the 6-step ritual + fact-vs-path referrer rule):
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. **Cross-doc references** are
  `/plans/...`/`/codex/...` leading-slash, repo-root-relative — never a bare filename, never `../`-relative (fragile:
  breaks if the CITING file ever moves, even though the target didn't); enforced hard via a shrinking-ratchet baseline
  (`check_reference_paths.py`, corpus-wide migration done 2026-07-23) — `depends_on`/`parent_epic`/`supersedes`/
  `superseded_by`/`entry_point_for` stay bare slugs (machine-parsed, out of scope). **Plan hygiene**
  `run_hygiene_sweep.sh`; inventory `regenerate_active_plan_inventory.py` (orphan count >0 is review-blocking).
  **NA-backlog ratchet**: `check_na_corpus_ratchet.py` (hygiene sweep) caps `assigned_vm:NA` size (docs+todos); shrink
  via `/na-eligibility-audit`. **Line caps** (plans 500 soft/1000 hard; epics `plans/epics/*.md` 2000 hard flat — NO
  `umbrella:`/`locked_by`+todos exemption, 2026-07-24 ruling) are a REAL hard gate (ratchet-baselined,
  `check_line_caps.sh`) in the sweep AND prek `--precommit`: a plan/epic you stage must not be over its cap. SSOTs:
  `codex/11-project-management/`, `/codex/08-workflows/estimation-calibration.md`,
  `/codex/11-project-management/cross-reference-path-convention.md`.

## Governance + safety HARD RULES

- **Plans run to actual completion, not smoke-test green** — backfills/migrations run on real infra with
  manifest-verified rows (both cloud identities are IAM-self-service — grant a missing role yourself, don't pause).
  **Hard-stops (human-only)**: wallet keys, force-push main, 1.0.0 graduation. **Maintenance-window restarts (e.g.
  orchestrator) skip operator scheduling pre-live-trading (2026-07-28)** — group + do now, brief downtime OK; real
  scheduled windows resume once live trading starts. **A confirmed runaway process endangering the host (`ps`/cgroup
  stats) may be killed the same way (SIGTERM→SIGKILL)** — investigate + doc it, don't wait on approval (2026-07-30).
  **Kill-switch is direction+scope-aware**: protective arming always autonomous; resume only within the auto-recovery
  matrix (`manual_unkill`=human-only). SSOTs: `/codex/04-architecture/autonomous-recovery-matrix.md`,
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`.
- **Data pipeline correctness is the heartbeat** — an audit's issues are fixed in FULL (no deadline deferrals, no
  asset_group skipped); only operator-gated `BLOCKED-CREDENTIALS`/`-OPERATOR-DECISION`/`-UPSTREAM-OUTAGE` defer; a RED
  data audit FREEZES layer-N+1 work (foundation-completion-gate). **External data is always available** — exhausting the
  free path = a credential ask, NOT a descope; build the adapter scaffold anyway + status `BLOCKED-CREDENTIALS`. SSOTs:
  `/codex/02-data/data-pipeline-correctness-hard-rule.md`, `…/external-data-always-available-rule.md`.
- **A doc/comment/pointer that MISLED you is a finding — fix it in the same turn.** Stale path, wrong claim, rotted
  count, dead reference: you already paid the search; leaving it makes every future agent pay it again. Correct it where
  it lives, state what you verified, and delete the number/name that rotted rather than updating it (counts like "the 2
  hooks" re-rot). Too big for a line → `- [ ]` todo. Confirm the doc is really wrong first — a truncated `head` read is
  not evidence of absence.
- **Findings triage**: in your file → fix in same commit; adjacent → fix in YOUR plan; outside-plan small+clear → ≤30
  min; ambiguous → diagnose both sides; audit-scope → wrapper plan → epic VM; outside every plan →
  `plans/active/issues/<slug>_<date>.md` — issue resolves to folded-in-plan/AO-scope/operator-gated, never passive.
  **The moment an `[OPERATOR]`/`BLOCKED-OPERATOR` tag resolves, retag to the reflecting tag in the SAME edit — never
  leave it stale** (07-28: 65/214 stale; don't write "was BLOCKED-X" — ao_non_dispatchable_regex_2026_07_29). **big
  finding** (data-correctness / May-23 critical path / cross-repo / SSOT contradiction) → NOTIFY OPERATOR + issue doc.
  "Pre-existing" is NOT a triage criterion. **Priority**: CI/audit > tier (cross-cutting>cefi>defi>sports>tradfi +
  carve-out) > pipeline stage. SSOT: `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md`.
- **Version graduation**: `feat!` on 0.x = MINOR; NEVER bump manually (semver-agent); graduate via
  `request-major-bump.yml`. **No summary docs** (`*_SUMMARY.md` etc.) — finish with text. **Prettier** via
  `prettier-autostage.sh` only, never bare `npx prettier` (unpinned <3.9.5 mangles `_`→`*`; SSOT quality-gates.md).
  **Delete deprecated code** (no shims). **Never** `git reset --hard`/`clean -fd`/`restore` uncommitted work. **Runtime
  verification** — never "done" without running the code; a `- [x]` Cloud Build / deploy / promote-green claim MUST cite
  `Evidence: cloudbuild=<id>` that resolves SUCCESS via `gcloud builds describe` (QG
  `check_evidence_backed_completion.py` fails on a non-SUCCESS build; SSOT `plans/PLAN_FORMAT.md` § 8b). **Citadel
  planning standards** (pre-audit / phased DAG / no tech debt / SSOT in UAC / foundation-gate / issue-doc-lifecycle) →
  `codex/11-project-management/`.

---

# Conditional domain index — read a target's codex SSOT ONLY when your task touches it

- **Working on a SERVICE?** Read that service's architecture doc first, skip the rest. Always-true:
  **instruments-service owns reference data** (`InstrumentRecord` carries `source_archive_url_template` + coverage
  windows; live REST/WS endpoints are in UAC registries, not InstrumentRecord); venue lists + adapter KEYS are UAC
  data** (`VENUE_TO_ADAPTER_KEY`; IS is the thin resolver —
  `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `…/instrument-universe-registry-consolidation.md`);
  **MTDS is market-data only**; service CLIs use `--operation`/`--mode`/`--asset-group`
  (`/codex/06-coding-standards/cli-convention.md`); shard-level failure isolation, no `raise` in per-shard loops,
  classify via UAC `classify_venue_error()` (`/codex/04-architecture/shard-level-failure-isolation.md`); service infra
  requirements (STEP 5.61 `ServiceBootstrap`, 5.62 `make_health_router`, `ApiKeyReloader`, typed config-reloaders, UAC
  schema provenance) → `/codex/06-coding-standards/config-reloader-pattern.md`. **NO service↔service deps** (T4 depends
  only on UTL/UAC/`unified-*-interface`; integrate by API contract + mocks; SIT fires at the staging boundary) →
  `/codex/04-architecture/tier-and-import-architecture.md`, `/codex/06-coding-standards/integration-testing-layers.md`.
- **Working on DATA / manifest / pipeline?** 4-state `capture_status`; canonical schema v9 but **trust the actual
  distribution, not the constant**; `expected_unattempted` materialised by the WRITER (never re-derived); `source=` is
  crosscutting (`record_captured(source=…)` required); never silent placeholders; **single-walk discipline** (any new
  whole-corpus GCS walk is review-blocking); **shard atom identical across writer/manifest/status/gate/UI**;
  phantom-audit `--apply` only after `prefix_tpls` cover the new shape. **Renaming/splitting an entity**
  (data_type/instrument_type/venue/axis/path segment) MUST enumerate + migrate every consumer in the SAME change — a
  token grep misses path-prefix/filename/registry-membership binders. SSOTs:
  `/codex/02-data/availability-manifest-and-data-status.md`, `…/honest-absence-downstream-handling.md`,
  `…/pipeline-mode-partition.md`, `…/entity-rename-and-split-consumer-migration-rule.md`,
  `plans/epics/infrastructure_master.md`. **Honest Coverage v2 (two-layer / two-view / instrument-gates-download
  model)** → `/codex/02-data/honest-coverage-model.md`. **Sports 2020-06 DATA FLOOR** (odds start 2020-06-06; pre-floor
  is fabrication-by-construction — WIPED from GCS + manifest, denominators/launchers/gates clamp to it) →
  `/codex/02-data/sports-2020-06-data-floor.md`.
- **RECONCILING an AG's estate against canonical (paths ↔ manifest ↔ catalogue)?** READ
  `/codex/02-data/four-surface-reconciliation-procedure.md` FIRST (it + siblings carry the oracle's full blind spots,
  the census/compute-tier split, the C2a casing ruling, and closed-out incidents — not repeated here). Use
  `/data-pipeline-reconciliation` (per-AG, PROD-only, read-only; deletes are SUGGESTIONS on a 5-part proof, prod-bucket
  deletes human-only unless reversibility-qualified). Canonical/non-canonical is the UAC `canonical_path_violations()`
  MACHINE ORACLE, never a re-implemented rule — but it's **PATH-STRUCTURE-ONLY** (doesn't validate the filename
  instrument_id) and **VALUE-BLIND** (doesn't check `instrument_type`/`data_type`/`venue`/`chain` VALUES): check
  id-form + values separately or say they weren't checked. **An absence result is evidence ONLY once you've confirmed
  you probed the vocabulary the WRITER actually emits** — a wrong-vocabulary probe already produced one false "twin
  absent" verdict. SSOTs: `/codex/02-data/four-surface-reconciliation-procedure.md`,
  `…/reconciliation-finding-taxonomy.md`, `…/gcs-and-manifest-delete-safety-protocol.md`,
  `…/non-canonical-path-inventory.md`, `…/canonical-cutover-register.md`, `…/orphan-object-detection.md`,
  `…/reconciliation-census-and-compute-tiers.md`.
- **`pipeline_mode` / sourcing?** SOURCE-AWARE `{mode}_{source}[_{transport}]` (`source`=VENDOR only; GCS paths carry it
  left of `asset_group=`, readers PREFIX-MATCH) → `/codex/02-data/pipeline-mode-partition.md`. **TradFi/Databento** (3
  datasets billing-fail-closed; `SOURCE_PRIORITY` databento-first; backfill silent-0-row gotchas; VIX=VX-futures via
  XCBF.PITCH, Barchart RETIRED; Massive/Polygon.io removal ruled 2026-07-19, **all-repos COMPLETE only 2026-08-03**) →
  `/codex/02-data/tradfi-databento-sourcing-ssot.md`. **DeFi data gotchas** →
  `/codex/02-data/defi-canonical-naming-ssot.md`. **Sports paths** `candidate_parquet_paths()`. **Manifest
  consolidator** = Cloud Run / Batch-Fargate (NOT a VM; loud-fails on stale index) →
  `/codex/05-infrastructure/manifest-consolidator-ssot.md`. **Feature versioning** →
  `/codex/02-data/feature-formula-versioning.md`. **Live = batch** (same code path; no live-only data_types).
- **Live = batch (event-log spine)**: MTDS/MDPS/features/ml/execution all publish/read via the UTL `EventTransport`
  facade (`unified_trading_library.streaming.event_facade`); `InMemoryTransport` for paper/colocated, Pub/Sub for live —
  same code path gives `paper(W)==batch-rerun(W)` epsilon=0. SINK_MATRIX classifies all 52 shards. SSOT:
  `/codex/02-data/live-data-persistence-and-event-log.md`.
- **Writing STORAGE code?** Every bucket via `resolve_bucket_name(...)`, never inline `gs://` (QG 5.69); GCS object ops
  via UTL `gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object`, never subprocess `gcloud`/`gsutil`. SSOTs:
  `/codex/05-infrastructure/bucket-isolation-model.md` (naming/tiers/folded Group-B, IAM write-protection enforced via
  per-tier SAs), `/codex/05-infrastructure/gcs-object-operations.md`.
- **Touching UI?** No Python tools (tsc/ESLint/Vitest/Playwright only); TS strict; **playwright gate** — no tick without
  `[UI]` + `pw:L2 ✓` + a cited regression spec. SSOT: `/codex/06-coding-standards/ui-testing-layers.md`.
- **Launching VMs / infra?** READ `/codex/05-infrastructure/vm-launcher-runbook.md` FIRST (full gotchas + measured
  incidents live there, not here). Headline HARD RULES: heavy I/O (full-corpus GCS walks, manifest rewrites, bulk
  renames) NEVER runs on the operator's local machine, always a VM in-region; **no fire-and-forget** (verify STARTED +
  ongoing progress + a terminal state); name/register every launcher via the `VM_PREFIX_TO_BUCKET` registry, never
  hand-roll; **backfill VMs default SPOT**, preemption recovery resumes from measured PROGRESS, never replays
  `START_DATE`; **Tardis: hard cap 1 concurrent VM, both clouds** (N>1 storms the API — count the fleet before
  launching); regularly audit for preemption-without-recovery + billing-waste (`/vm-preemption-billing-waste-audit`).
  **Rightsizing HARD RULE (2026-08-10)**: any VM running >30min gets `/vm-resource-rightsizing-check` (CPU+mem-growth) —
  skip only if a cited doc justifies the sizing. SSOTs: `/codex/05-infrastructure/vm-launcher-runbook.md`,
  `…/spot-vms-for-backfill.md`, `…/vm-tarball-deployment.md`, `…/deployment-observability.md`,
  `…/vm-preemption-and-billing-waste-monitoring.md`, `…/data-pipeline-alerts.md`.
- **A critical service (AO first) looks idle/broken?** Diagnose before restarting — READ the runbook's fix-vs-not table
  FIRST. **Escalation stuck/looping → `escalation_queue.last_error` names the reason**; quota alone does NOT stall
  sonnet-tier dispatch (DeepSeek = baseline fallback). SSOT: `/codex/15-runbooks/safe-service-restart-procedures.md`.
- **AO scheduled jobs (systemd timers / status model / capacity queue)?** `dispatched` = spawn receipt, NOT completion
  (`agent_exit_reason == "lifecycle-complete"` is done); `git pull` does NOT reinstall a timer — re-run
  `bash scripts/install-<job>-timer.sh` (**no `sudo`** — CORRECTED 2026-08-12 (/plan-reconcile): all 8 installers
  converted to `systemd --user` units 2026-08-08 (`agent-orchestrator@c3a85c3b4`) and now hard-fail under `sudo`, per
  the codex SSOT below); `no_capacity` is legacy (queue-on-no-capacity default); `quarantined/timeout/error` page,
  `dispatched/queued` don't. SSOT: `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md`.
- **Working on DeFi EXECUTION?** Credential convention; `DefiErrorCode` (35 codes);
  IS→MTDS→features-onchain→strategy→execution; Pyth Solana-only; custody `CLOUD_KMS_ENCRYPTED`. SSOT:
  `/codex/04-architecture/defi-execution-overview.md`.
- **Touching TRANSFERS / funds / clients?** **HARD: funds NEVER move between clients** — every transfer scoped to one
  `client_id` (`TransferCoordinator` raises `CrossClientTransferForbiddenError`); "cross-client rebalancing" framing is
  review-blocking. Per-client isolation = one subprocess per client. SSOTs:
  `/codex/04-architecture/client-funds-isolation.md`, `…/per-client-isolation-architecture.md`.
- **Strategy / PnL / HWM / promote?** **HWM is never raw equity** (TWR / Notional / PnL-recovery) →
  `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`. **Batch=Live determinism spine** — paper(W)
  MUST equal batch-rerun(W) trade-for-trade (ε=0 PROOF); four ledgers; integrate via canonical `InstrumentKey`
  derivation → `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`. **Promote** (CLI primary / UI
  secondary; `paper_1d`→`live_early` only pre-May-23) → `/codex/04-architecture/promote-workflow-architecture.md`.
- **Peripheral script dir / one-off?** Wire into the primary-consumer's `quality-gates.sh`; one-offs are TEMPORARY
  (delete after prod-run); **lifecycle marker** (`# Epic:` / `# Lifecycle:` / `# Delete-when:`) on every `scripts/`
  file. SSOT: `/codex/06-coding-standards/script-homes.md`.
- **AO alerts / Slack notifications?** The `agent-orchestrator-alerts` channel is **actionable-only** — automatic
  lifecycle events (dispatches / respawns / recoveries) log + feed the daily digest, they NEVER page; failures + worker
  BLOCKED questions page; standing conditions dedup by state-transition (fire on change / RESOLVED / re-remind), never
  every tick. **Every actionable alert that paged an OPEN gets a ✅ CLOSE bookend in-channel** (BLOCKED answered/auto-
  resolved · git RECOVERED · escalation resolved-if-it-paged; webhook-only correlation via opened-at ts, no threading).
  SSOT: `/codex/04-architecture/agent-orchestrator-alerting.md`. **CI alerts (`ci-failures` channel)** route through the
  reusable `notify-slack.yml` carrier (read-back dedup: `dedup_key`+`cooldown_min`, `recovery`-gated all-clears,
  fail-open); cooldowns track a condition's MEASURED delivery cadence, not its declared cron (GH throttles `schedule:`
  well below the declared rate — measured rates + dates in the SSOT, re-measure before trusting an old %). SSOT:
  `/codex/04-architecture/ci-alerting.md`. **Need to READ a channel directly (not just receive alerts)?**
  `scripts/dev/slack-read-channel.py` already has it (GSM + gcloud ADC, zero setup, every slot/VM/AO) — check before
  assuming no access. SSOT: `/codex/05-infrastructure/agent-slack-read-access.md`.
- **Runbooks**: declare `owner`/`cadence`/`verifier`/`last_executed` (missing = review-blocking). **Cross-plan
  banners**: launching a VM / in-flight refactor → add `> **🟢/🟡 …**` to every affected plan.

---

## System map + workspace configs

Repo map: events→UTL · schemas→UAC · cloud→unified-cloud-interface · market data→MTDS · execution→execution-service ·
reference data→instruments-service (URDI is a live internal module — "phantom" label retired 2026-07-12; no NEW URDI
refs in docs) · UI→`unified-trading-system-ui` (incl. DART) + `deployment-ui` (devops + launch consoles;
`user-management-ui` ARCHIVED) · orchestration→`agent-orchestrator` (uvicorn :8765). **deployment-api** = single
deploy/launch+subscriptions backend for both UIs. **Architecture**: Central orchestrator VM (id `planning`, EIP
13.113.200.22) with N slot workers, role-based dispatch (no per-epic VMs; single-VM architecture 2026-06-27).
**`planning` is the ONLY VM** (human-planning TERMINATED 2026-08-03). Workspace configs canonical in
`unified-trading-pm/cursor-configs/` (setup `scripts/workspace/setup-workspace-config-symlink.sh`; strict basedpyright).
Claude Code TEAM settings = git-TRACKED `cursor-configs/settings.json`, inherited via the per-slot
`.claude/settings.json` symlink (`link-claude-skills.sh`, run by workspace-bootstrap + `quality-gates.sh`), so a hook
registered there reaches every slot/machine on an LDR pull; `~/.claude/settings.json` is PERSONAL, never tracked, NOT a
symlink → `/codex/05-infrastructure/claude-code-settings-symlink.md`. **Personal per-tab context-checkpoint automation**
(tmux `send-keys`-forced `/pre-compact` then `/compact`; needs a terminal-hosted `claude` session — the Cursor/VS Code
chat panel isn't tmux-reachable, its terminal tab is) → `/codex/05-infrastructure/local-tmux-precompact-watcher.md`.
Analysis: `rg --glob '!.venv*' --glob '!build' --glob '!tests'`. **Workflow-capable `GH_TOKEN`**:
`source scripts/workspace/load-gh-token.sh`. **agent-orchestrator auth**: dashboard JWT HS256 (central only) / internal
proxy ES256 / accounts via GSM, never `.credentials.json`; backlog plan-driven (`regen_backlog_from_plan.py`, never
hand-edit `backlog.yaml`); role-dispatch routes tasks to spawned workers by skill (central + role registry); runtime
self-heals (AutoSpawn/failover/watchdog ON — never manually kill tmux). **Orchestrator `tuning.*` knobs are env-free**
(`TuningDefaults`) — change the code default + redeploy; `.env.local` silently no-ops. **Checking live backlog/dispatch
status from a dev checkout** (no JWT, VM:8765 has no inbound rule): `/check-agent-orchestrator` skill or
`agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` — read-only via AWS SSM, never a manual
API-guessing session. SSOTs: `/codex/04-architecture/runtime-deployment-topology.md`,
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.
