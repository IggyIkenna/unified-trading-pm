# Sub-Agent Mandatory Rules — Full Workspace Standards

**You are a sub-agent. You MUST follow ALL rules below. Read this entire document before any action.**

Sub-agents start with FRESH context and do NOT inherit the parent's rules. This file is the SSOT for workspace
standards.

---

## 0. System-First Architecture (MANDATORY — No Ad-Hoc Solutions)

The Unified Trading System is a comprehensive, Citadel-grade multi-repo platform. It already has repos covering every
domain. Before implementing ANYTHING — a feature, a fix, a refactor, a new capability — **look at the existing system
first**. Do NOT build ad-hoc solutions, duplicate sources of truth, or create unnecessary repos/files.

### Decision Tree (follow in order):

1. **Events/logging?** → Use `unified-events-interface` (`setup_events`, `log_event`). Do NOT create custom loggers or
   event systems.
2. **New schema/data model?** → Use `unified-internal-contracts` (internal) or `unified-api-contracts` (external APIs).
   Do NOT define schemas inline in service code.
3. **External API/SDK integration?** → Use `unified-api-contracts` for contract definitions. Do NOT scatter API clients
   across services.
4. **Cloud infrastructure?** → Use `unified-cloud-interface` (`get_storage_client()`, `get_pubsub_client()`,
   `UnifiedCloudConfig`). Do NOT import cloud SDKs directly in services.
5. **Market data / venue adapters?** → Use `unified-market-interface`. Do NOT build one-off venue connectors.
6. **Trade execution?** → Use `unified-trade-execution-interface`. Do NOT build separate execution paths.
7. **Configuration?** → Use `unified-config-interface` / `UnifiedCloudConfig`. Do NOT use `os.getenv()` or create config
   helpers.
8. **Domain utilities?** → Check `unified-domain-client` and `unified-trading-library` first. Do NOT duplicate utilities
   that already exist there.
9. **Reference data?** → Use `unified-reference-data-interface`. Do NOT hardcode instrument metadata.
10. **ML models/features?** → Use `unified-ml-interface` / `unified-feature-calculator-library`. Do NOT create ad-hoc
    feature pipelines.
11. **Position/balance tracking?** → Use `unified-position-interface`. Do NOT build separate position stores.
12. **DeFi execution?** → Use `unified-defi-execution-interface`. Do NOT build standalone DeFi adapters.
13. **UI needed?** → Check existing 13 UIs first. Can the feature go into an existing UI? Only create a new UI if no
    existing UI covers the domain.
14. **New repo needed?** → Almost certainly NOT. The 67-repo system covers every domain. If you think you need a new
    repo, explain why no existing repo works. The burden of proof is on justifying a new repo, not on reusing existing
    ones.

### The Rule:

**If the system already has a repo/interface/library for a capability, USE IT.** If the library is missing a feature you
need, ADD the feature to the library (via PR to that repo). If the library's approach is wrong, FIX the library. Do NOT
work around it by building a parallel solution in a service repo.

This applies to ALL agents — autonomous GHA agents, Cursor background agents, Claude Code sessions, sub-agents. No
exceptions.

---

## 1. Environment & Tooling

- **Flat deps only** — every `pyproject.toml` has ONE list: `[project.dependencies]`. There is NO
  `[project.optional-dependencies]` anywhere. Never add `[dev]`, `[test]`, or any optional group. Never reference
  `.[dev]` or any extra (e.g. `uv pip install -e ".[dev]"` → use `uv pip install -e .`). Reason: tests run locally,
  Cloud Build, Code Build, and GHA — all environments need all deps. Optional groups create silent omissions and
  conflicts with zero benefit.
- **uv not pip** — always `uv pip install`
- **basedpyright not pyright** — run as `timeout 120 basedpyright <source_dir>/` — NEVER `basedpyright .` or
  `basedpyright` (no args)
- **quickmerge not git push** — `bash scripts/quickmerge.sh "message"` — never `git push`, never standalone
  `scripts/quality-gates.sh`
- **Tests:** `bash scripts/quality-gates.sh` — never `pytest` or `python -m pytest` directly (uses wrong venv)
- **Parallel QG sweep:** When asked to run quality gates across many repos, use **max 20 concurrent** to avoid CPU
  thrash and timeouts. Split into 2 batches of 20: run batch 1, report results, then batch 2, report. Or use 4–5
  parallel sub-agents with 4–5 repos each per batch. Exclude `-api` and `-ui` if user says "excluding frontend."
  Command: `cd <repo> && bash scripts/quality-gates.sh 2>&1 | tail -5`. Return PASS/FAIL per repo. Fewer concurrent runs
  reduce timeouts from CPU contention.
- **Config:** `UnifiedCloudConfig` / `config.key_name` — never `os.getenv('KEY', '')`
- **Storage:** `get_storage_client()` — never `from google.cloud import storage`
- **Logging:** `logger.info()` — never `print()`
- **Datetime:** `datetime.now(timezone.utc)` — never `datetime.now()`
- **Imports:** at top of file — never inside functions

---

## 2. Git & Commits

- **Conventional commits required:** `feat:`, `fix:`, `chore:`, `feat!:` (breaking)
- **Never** `git reset --hard`, `git clean -fd`, `git restore` that discards uncommitted work — unless user explicitly
  requests
- **Dependency conflict:** If a dep repo has uncommitted changes, commit them first on the `active_feature_branch` (read
  from `workspace-manifest.json`), then re-run quickmerge. NEVER use `--dep-branch` — that flag is HUMAN-ONLY and will
  cause quickmerge to exit with an error in `--agent` mode.
- **Never bump versions manually** — CI bumps on merge to main
- **Untrack ignored files** — if tracked files match `.gitignore`: detect with
  `git ls-files --ignored --exclude-standard`, then `git rm --cached <files>`. Never bare `git rm` (deletes files)
- **Revert MUST be file-scoped:** If you need to undo your changes, ONLY restore the specific files you touched in this
  session. NEVER `git checkout <branch>` (switches whole branch) or `git reset --hard` (destroys all uncommitted work
  including other agents' changes). Correct pattern:
  ```bash
  # Revert only YOUR files using the backup branch as source
  git restore --source=$BACKUP_BRANCH -- path/to/file1.py path/to/file2.py
  ```
  Keep a list of every file you modify at task start — this is your revert scope.

---

## 3. Code Quality & Refactoring

- **Delete deprecated code** — no parallel code paths, no `# deprecated` comments, no `_old.py` copies
- **Search unified libraries first** — unified-market-interface, unified-trade-execution-interface,
  unified-config-interface, unified-cloud-interface, unified-events-interface, unified-domain-client,
  unified-api-contracts — USE if exists, FIX library if wrong, ADD to library if missing
- **No backward compat shims** — fail fast, no try/except import fallbacks
- **Strict quality gates** — no E722 global ignore, no empty fallbacks, no hardcoded project IDs, use specific
  exceptions

---

## 3b. UAC Citadel Architecture

### Import Rules

- **Facade imports only:** `from unified_api_contracts import X` or `from unified_api_contracts.{domain} import X`
- **NEVER import from internals:** `unified_api_contracts.canonical.*`, `.normalize_utils.*`, `.config.*`, `.shared.*`,
  `.schemas.*` — these are implementation details
- **External source modules:** Only interface adapters (UMI, UTEI, URDI) may import from
  `unified_api_contracts.external.{source}` — services NEVER import external modules directly

### Schema Placement

- External API response/request schemas → UAC `external/{source}/schemas.py`
- Internal service domain schemas → UIC `domain/{service}/`
- **NEVER define schemas inline in services or interface adapters** — they belong in contract repos (UAC or UIC)

### Normalization Placement

- Raw→canonical normalizers → UAC `external/{source}/normalize.py`
- **NEVER put normalizers in interface adapters or services** — normalization lives in UAC, co-located with the external
  source it normalizes

**Reference:** `unified-trading-codex/02-data/contracts-scope-and-layout.md`

---

## 4. Documentation

- **Never create** `*_SUMMARY.md`, `*_STATUS.md`, `READY_TO_*`, `COMPLETION_*` — unless user explicitly asks
- **Plans only in** `unified-trading-pm/plans/ai/` or `unified-trading-pm/plans/active/`
- **After task:** update code, run tests, commit — respond with text summary, NOT a file

---

## 5. Verification & Anti-Patterns

- **Never claim "done"** without running code, waiting 8–10s, checking terminal for errors
- **basedpyright:** `timeout 120 basedpyright <source_dir>/` — never from workspace root
- **Quality gates:** `bash scripts/quality-gates.sh` per repo — never standalone basedpyright for audits
- **Rule amnesia:** if you use pip, os.getenv, git push, or suggest skipping tests — stop and remind rules

---

## 6. Workspace Context

- **Multi-repo workspace** — each subdir is independent git repo; only commit to target repo
- **Tests/quality gates:** `cd <repo> && bash scripts/quality-gates.sh` — uses per-repo `.venv` (script activates it).
  NEVER use `.venv-workspace` for pytest — it has stale wheels; per-repo `.venv` matches CI.
- **Targeted pytest (debug only):** `cd <repo> && .venv/bin/pytest tests/unit/test_foo.py` — per-repo venv, not
  workspace.
- **General Python (non-test):** `.venv-workspace` for IDE; `uv sync && source .venv/bin/activate` for per-repo isolated
  runs (no extras — flat deps only).

---

## 7. Agent-Specific (Quickmerge)

- Use `--agent` in agent sessions: `bash scripts/quickmerge.sh "feat: ..." --agent`
- **NEVER use `--dep-branch`** — it is HUMAN-ONLY. Quickmerge will exit(1) if you pass it with `--agent`.
  - Branch is read automatically from `active_feature_branch` in `workspace-manifest.json` (currently:
    `live-defi-rollout`)
  - If a dep repo has uncommitted changes: commit them first (same feature branch), then re-run here
- Breaking changes: `--to-staging`

---

## 8. Testing & Mock Infrastructure

- **Credential-free requirement**: All CI tests must pass with `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true` — no live
  cloud calls
- **GCP tests**: Use `PUBSUB_EMULATOR_HOST`, `STORAGE_EMULATOR_HOST`, `BIGQUERY_EMULATOR_HOST` env vars in conftest
  fixtures — NOT live GCP APIs
- **AWS tests**: Use `@mock_aws` (moto) decorator — NOT `unittest.mock.patch` on boto3 internals unless unavoidable
- **WS tests**: Use `MockWebSocketFeed` from `unified-market-interface/tests/fixtures/mock_ws_server.py`
- **DeFi/Hyperliquid tests**: Use `responses` library with `passthrough=False` — proven zero live HTTP calls
- **Network blocking**: When writing new integration tests, add `@pytest.mark.allow_network` ONLY for tests that connect
  to local emulators (not live APIs) — emit a comment explaining why
- **Cassette tests**: VCR cassettes live in `unified-api-contracts/unified_api_contracts/external/*/mocks/`; parity
  tested on every commit via `test_cassette_schema_parity.py`
- **Fault injection**: Use `FaultInjectionTransport` from `unified-trading-pm/scripts/dev/fixtures/fault_injection.py`
  for circuit breaker tests
- **Tick replay**: Use `TickReplayEngine` from `unified-trading-pm/scripts/dev/fixtures/tick_replay.py` for
  deterministic tick streams
- **Full infra reference**: `unified-trading-pm/plans/archive/cicd_mock_hardening_2026_03_11.plan.md`

---

## 9. Plan Format Rules

- **New plans go to `plans/ai/` first** — NEVER directly to `plans/active/` unless the user has explicitly approved the
  plan
- **Promotion requires:** conflict check in INDEX.md, then user confirmation, then move to `plans/active/` with full
  YAML
- **Every `.plan.md` in `plans/active/` MUST have** `completion_gates` and `repo_gates` in YAML frontmatter (see format
  below)
- **Cursor-friendly checkboxes (MANDATORY):** Every todo's first content line MUST start with `- [x]` (done) or `- [ ]`
  (pending) so Cursor Plan Mode shows filled vs hollow circles. Format: `- [x] [SCRIPT] P0. Description...` or
  `- [ ] [AGENT] P0. Fix...`. See `plans/PLAN_FORMAT.md` § Cursor-Friendly Todo Checkboxes.
- **NEVER mark a plan done/archived** unless ALL repos in `repo_gates` have reached the level declared in
  `completion_gates`
- **Gate levels by plan type:**
  - `code`: needs C5 (quickmerge) for all repos to archive
  - `infra` / `deployment`: needs D3 (staging SIT — real service calls) for all repos — even during code-completion epic
  - `business`: needs B6 (user approved) + B3 domain KPIs
  - `mixed`: highest required gate across declared types
- **blocked_by** goes on the todo item, not on completion_gates — gates represent what THIS plan owns
- **Format SSOT:** `unified-trading-pm/plans/PLAN_FORMAT.md`

```yaml
# Required YAML frontmatter for every active plan
---
name: plan-slug
overview: One-line description
type: code | infra | deployment | business | mixed
epic: epic-code-completion | epic-deployment | epic-business | epic-infra | none
completion_gates:
  code: C5 # C0-C5 or "none"
  deployment: none
  business: none
repo_gates:
  - repo: repo-name
    code: C2 # highest gate currently reached
    deployment: none
    business: none
depends_on: []
todos: []
isProject: false
---
```

---

## §9a Plan Safety Rules

- **Locked plans:** Plans with `locked_by` in frontmatter MUST NOT be archived, deleted, or moved. Only a human with
  `[unlock-plan]` in the commit message can remove a locked plan.
- **Agent unlock protocol:** If all todos in a locked plan are complete, agents MAY ask the human: "Plan X is locked but
  all todos are done. Should I unlock it?" If approved, remove `locked_by`/`locked_since` and include `[unlock-plan]` in
  the commit message. If denied, leave it locked. NEVER unlock autonomously.
- **Plan dependencies:** If plan A has `depends_on: [plan-B-name]`, plan B cannot be archived while plan A is active.
- **Plan structure:** ALL todos must appear in the frontmatter YAML block (before closing `---`). Notes, context,
  architecture, Mermaid diagrams go AFTER frontmatter. Why: conflict-resolution-agent reads head -250 per plan; todos
  after line 250 are invisible.

## §9b Workflow Template Rules

- **Never edit per-repo workflow copies directly.** All per-repo GHA workflows (semver-agent, request-major-bump,
  staging-lock-check, update-dependency-version, major-bump-issue-handler) are managed as canonical templates in
  `unified-trading-pm/scripts/workflow-templates/`.
- **To modify a workflow:** Edit the PM template → run the rollout script → force-sync to remote.
  - Generic workflows: `bash unified-trading-pm/scripts/propagation/rollout-workflow-templates.sh`
  - Semver agent: `bash unified-trading-pm/scripts/propagation/rollout-semver-agent.sh`
- **Semver agent** uses `__REPO_NAME__` and `__SOURCE_DIR__` placeholders — the rollout script substitutes them.
- **Hardcoded org names are banned.** Use `${{ github.repository_owner }}` instead of `IggyIkenna`.
- **GHA workflows must fail hard.** No `|| true` or `|| echo ""` on critical operations (issue creation, Telegram
  alerts, version bumps). Use `exit 1` with `::error::` annotations.
- **`--skip-version-alignment` is HUMAN-ONLY.** Agents MUST NOT pass this flag to quality-gates.sh. If QG blocks on
  version drift, the agent must fix the drift (pull latest), not skip the check.
- **`--force-version-override` is HUMAN-ONLY.** Agents MUST NOT pass this flag to admin-force-sync.

---

## §9b Citadel-Grade Planning Standards

Every plan MUST follow these standards. Agents creating plans that don't meet these standards MUST be corrected.

### 1. Pre-Audit Before Execution

Before writing any code, audit the blast radius:

- Search the entire workspace for every import/reference to symbols being moved, deleted, or renamed
- Build a **pre-audit manifest**: repo, file, line number, import statement, action needed
- Embed the manifest in the plan so executing agents don't need to re-scan
- If working with a subset of repos (background agent), document what you CAN'T verify

### 2. Phased Execution DAG

Plans MUST define execution phases with clear dependencies:

- **Phase N** items run in parallel within the phase
- **QG gates** between phases — next phase cannot start until prior phase QG passes
- Mark items as PARALLEL or SEQUENTIAL explicitly
- Draw the dependency graph (ASCII or Mermaid) in the plan context section

### 3. No Technical Debt

- No backwards compatibility shims, re-exports of old paths, or deprecation wrappers
- Clean breaks: old implementation deleted, new implementation in place, consumers updated
- **Exception**: When working on a single repo without all downstream siblings available, backwards compatibility IS
  allowed temporarily. Document it as a follow-up todo.
- When all 60+ repos are available (full workspace): zero technical debt, update everything

### 4. Parallelization

- Maximize parallel execution. If items have no dependency, they MUST be marked PARALLEL
- Group independent items into parallel batches
- Use separate agents for parallel work where possible
- Document the parallelization strategy in the plan

### 5. Success Criteria

Every plan MUST declare explicit success criteria per phase:

- **Code gates**: quality-gates.sh pass, basedpyright clean, ruff clean
- **Test gates**: unit tests pass, integration tests pass (specify which)
- **Deployment gates**: D1-D5 (if applicable)
- **Business gates**: B1-B6 (if applicable)
- The final phase MUST include workspace-wide QG validation of all affected repos

### 6. Downstream Consumer Updates

When modifying shared libraries (UAC, UIC, UTL, UCI, UEI, UDC):

- Pre-audit identifies EVERY downstream consumer
- Plan includes explicit fix items for each affected repo
- No "fix later" — all consumers updated in the same plan
- Quality gates run on each affected downstream repo

### 7. Single Source of Truth

- Types/schemas belong in ONE place. UAC for external data normalization, UIC for internal.
- No service should self-declare types that exist in contracts libraries
- No re-definition of enums, dataclasses, or Pydantic models that already exist upstream
- Pre-audit should catch self-declared duplicates and include them in the fix manifest

---

## §10 Local Dev & Zombie Process Prevention

- **Vitest config:** Always use `pool: "forks"` in `vitest.config.ts`. The default `threads` pool leaves orphan node
  processes when tests crash. All UI repos must include `pool: "forks"` and `teardownTimeout: 5000`.
- **Non-interactive test runs:** Use `CI=true npm test -- --run` for headless/CI test execution. The `--run` flag
  prevents watch mode. `CI=true` ensures non-interactive behavior.
- **Zombie detection:** If node/python processes are stuck after tests:
  ```bash
  ps aux | grep "node.*vitest" | grep -v grep
  ps aux | grep "python.*-m.*_api" | grep -v grep
  ```
- **Mock mode for APIs:** `CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local DISABLE_AUTH=true` — every API returns realistic
  mock data, no cloud credentials needed.
- **MockStateStore:** In mock mode, use `get_store().list/create/update/delete` from `unified-trading-library` — NOT
  static dicts. Mutations persist across API restarts in `.local-dev-cache/`.
- **MOCK_STATE_MODE:**
  - `deterministic` — CI mode. Pure seed data, no persistence, no `.local-dev-cache/` writes.
  - `interactive` — UAT/dev mode. Mutations persist to `.local-dev-cache/{service}/{collection}.jsonl`.
- **Cache cleanup:** `dev-stop.sh --clean` (stop + wipe cache) or `dev-start.sh --reset` (wipe cache + start fresh).
- **Local dev stack:** `bash unified-trading-pm/scripts/dev/dev-start.sh --stack <name> --mode mock` — never start
  UIs/APIs manually with ad-hoc commands.
- **Port registry SSOT:** `unified-trading-pm/scripts/dev/ui-api-mapping.json` — UIs on 5173-5183, APIs on 8004-8016.
  All UIs use `strictPort: true`.
- **Test command reference:**

  | What                   | Command                                                              | Notes                                 |
  | ---------------------- | -------------------------------------------------------------------- | ------------------------------------- |
  | Python quality gates   | `cd <repo> && bash scripts/quality-gates.sh`                         | Per-repo .venv, never pytest directly |
  | UI tests (headless)    | `cd <ui-repo> && CI=true npm test -- --run`                          | `--run` prevents watch mode           |
  | UI smoke build         | `cd <ui-repo> && VITE_MOCK_API=true npx vite build`                  | Catches TS/import errors              |
  | Start local stack      | `bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock` | No credentials needed                 |
  | Stop + clean cache     | `bash unified-trading-pm/scripts/dev/dev-stop.sh --clean`            | Wipes `.local-dev-cache/`             |
  | Check running services | `bash unified-trading-pm/scripts/dev/dev-status.sh`                  | Shows all 5 mode axes                 |

- **Full docs:** `unified-trading-codex/08-workflows/local-dev.md`

---

## §11 Readiness Checklist & Semver Rules

### MANDATORY RULE: Check Readiness Before Claiming Stage Complete

NEVER declare a repo has reached a readiness stage (CR1, CR2, DR3, BR3, etc.) unless ALL criteria for that stage are
fully met. The criteria are defined in:

- Template: `unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml`
- Per-repo: `cat {repo}/.readiness-ref` → gives path to `codex/10-audit/repos/{repo-name}.yaml`

To check current declared state for a repo:

```bash
cat $(cat {repo}/.readiness-ref 2>/dev/null || echo "unified-trading-codex/10-audit/repos/{repo}.yaml")
```

### MANDATORY RULE: Three Axes — All Required

Every repo has CR (Code), DR (Deployment), BR (Business) readiness. A repo is NEVER "done" by checking only one axis.
Libraries satisfy DR and BR N/A for many items — but must declare N/A with reasons explicitly in their checklist file.

Stage summary (full criteria in codex YAML):

- CR1-CR5: functionality → unit tests → integration tests → QG → quickmerge
- DR1-DR6: infra → CI smoke → feature env → SIT → load/perf → prod-ready (per batch/live mode)
- BR1-BR8: acceptance criteria → circuit breaker → events → PnL targets → optimization → batch/live parity → USER
  APPROVED

### MANDATORY RULE: v1.0.0 Requires User Approval (BR8)

NEVER set version = "1.0.0" in pyproject.toml or package.json autonomously. NEVER trigger a version dispatch that would
result in a 1.0.0 tag. NEVER mark BR8 as complete without explicit user statement in the current session.

If gates are met, present the checklist summary to the user and WAIT for explicit approval.

### MANDATORY RULE: Pre-1.0.0 MAJOR → MINOR

On 0.x.x repos: feat!: bumps MINOR (0.x.y → 0.x+1.0), never MAJOR (0.x.y → 1.0.0).

### MANDATORY RULE: Per-Repo Semver Rules Lookup

Before proposing ANY commit message prefix (feat!:, feat:, fix:):

1. Read `semver_rules_ref` from `workspace-manifest.json` for this repo
2. Read `unified-trading-pm/docs/per-repo-semver-rules.yaml` for this repo type
3. Classify the actual change and verify the prefix matches
4. If post-1.0.0 and change is MAJOR: STOP, report to user, do NOT quickmerge

### MANDATORY RULE: Post-1.0.0 Major Bump Blocked

On repos at version >=1.0.0, quickmerge.sh Stage 0.3 will BLOCK feat!: commits. The --user-approved flag is required.
Agents MUST NOT pass --user-approved automatically.

### ABSOLUTE PROHIBITION: MAJOR Version Bumps (No Self-Approval)

You are a sub-agent. You are PROHIBITED from:

- Editing any `pyproject.toml` to increase the `MAJOR` version component
- Dispatching any `version-bump` event where the proposed version is a MAJOR increase
- Writing any commit that bumps a repo's MAJOR version (including 0.x.x → 1.0.0)
- Commenting `/approve` on any GitHub issue — you cannot self-approve MAJOR bumps

**If your task would logically require a MAJOR bump:**

1. Complete the code changes (normal commit/quickmerge flow)
2. Do NOT touch the version
3. Report back to the orchestrator/user:
   ```
   MAJOR bump required for {repo}: current={X.Y.Z} → proposed={X+1}.0.0
   Initiate with: bash scripts/approve-major-bump.sh {repo} {X+1}.0.0 --reason "..." --admin-pat $GH_PAT
   ```

This rule has NO exceptions — not for infra repos, not for 0.x.x → 1.0.0, not for "obviously needed" cases. The human
must always be in the loop for MAJOR version promotions.

---

**Venv vs testing:** `.venv-workspace` = IDE only. Tests use per-repo `.venv` via quality-gates.sh. See
`.cursor/rules/testing/no-manual-pytest.mdc`.

**CODEX:** unified-trading-codex/06-coding-standards/README.md

---

## §13 Downstream Cascade (Planned)

When a breaking change cascades via dependency-update, QG runs on direct dependents in topological order (fail-fast). If
a dependent fails, an autonomous fix agent attempts code repair and creates a PR for human approval. Agents MUST NOT
self-merge fix PRs — always require human /approve. See: cicd_code_rollout_master_2026_03_13.plan.md § Downstream
Cascade Intelligence.

Schema changes in T0 libraries (UAC, UIC, UEI) trigger reverse-dependency sync to update PM cursor-rules and codex docs
automatically.

---

## §12 Autonomous Agent Prompt Injection (MANDATORY for agent orchestrators)

If you are an orchestrator, script, or workflow that LAUNCHES other agents (Claude Code `--print`, Cursor agent, etc.):

1. **Agents in `--print` mode CANNOT read files from disk.** Telling them "read .cursorrules" is useless — they never
   see it. The rules MUST be pasted directly into the prompt text.
2. **Use `inject-mandatory-rules.sh`** for local scripts:
   ```bash
   RULES_PREAMBLE=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")
   FULL_PROMPT="${RULES_PREAMBLE}\n\n${TASK_PROMPT}"
   ```
3. **For GHA workflows:** Load rules via `GITHUB_ENV` heredoc in a prior step:
   ```yaml
   - name: Load mandatory rules
     run: |
       { echo "MANDATORY_RULES<<RULES_EOF"; cat cursor-configs/SUB_AGENT_MANDATORY_RULES.md; echo "RULES_EOF"; } >> "$GITHUB_ENV"
   ```
   Then prepend `${MANDATORY_RULES}` at the TOP of the agent prompt.
4. **If rules injection fails, the agent MUST NOT proceed.** Exit with error. Never launch an agent without rules — it
   will silently produce work that violates workspace standards.
5. **SSOT:** `unified-trading-pm/scripts/agents/inject-mandatory-rules.sh`
