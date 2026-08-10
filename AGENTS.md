# AGENTS.md — Unified Trading System

Shared instructions for all agents (Claude Code, Codex, Cursor) across this workspace.

---

## Core Rules

- Follow all workspace cursor rules in `.cursorrules` and `.cursor/rules`
- No summary files — never create `*_SUMMARY.md`, `*_STATUS.md`, `READY_TO_*`, `COMPLETION_*`
- Delete deprecated code; no parallel code paths
- Search existing repos/libraries before implementing anything new
- Never `git reset --hard` or discard uncommitted work without explicit user request
- Conventional commits: `feat:`, `fix:`, `chore:`, `feat!:` (breaking)
- **Agent memory writes are BANNED (HARD RULE)**: never write to `memory/` or `MEMORY.md` — it's per-cwd, local-only,
  NOT inherited by sub-agents, and causes drift. Session findings go to the plan's Progress Log; the only exception is
  operator-written personal/secrets state.

---

## Workspace Structure

Multi-repo workspace (~62 independent git repos). Key locations:

- `unified-trading-pm/` — plans, scripts, cursor rules, workspace manifest (SSOT)
- `unified-trading-pm/workspace-manifest.json` — all repos, deps, versions, merge order
- `unified-trading-pm/plans/active/INDEX.md` — canonical plan registry
- **Venue axis (trading / asset group)** — SSOT and waves:
  [venue_axis_asset_group_vocabulary_2026_04_25.plan.md](plans/active/venue_axis_asset_group_vocabulary_2026_04_25.plan.md);
  quick rules in `unified-trading-pm/cursor-configs/CLAUDE.md` (“Venue axis (trading) SSOT”). Applies across UAC, UTL,
  MDPS, MTDS, and downstream consumers; touch UAC first for registry changes.

---

## Doc Retrieval — grep the L0 index first (L0→L4, grep-native)

Finding any doc/rule/SSOT: **grep the L0 index FIRST** — `unified-trading-pm/DOC_INDEX.generated.md` (per-clone,
gitignored; absent/stale → `bash scripts/docs/refresh-doc-index.sh`; NEVER read it whole — grep it). Narrow with L1
frontmatter facets: `rg -l '^authoritative_for:.*<topic>' codex/` lands THE one SSOT; compose axes for broader cuts
(`doc_type` / `asset_group` / `stage` / `repos` / `status` / `nature` / `tags`, e.g.
`rg -l '^doc_type: codex-ssot' codex/ | xargs rg -l '^asset_group:.*defi'`). Confirm relevance via `summary:` (L2)
before opening; open ONLY the confirmed doc (L3); jump doc→code via its `code_refs` (L4, module-dir granularity). This
applies to every agent reading this file (Claude Code, Codex, Cursor) — not just Claude Code's own retrieval habits.
SSOT: `codex/11-project-management/doc-frontmatter-schema.md` §1 + epic `agent_operating_framework_master` § "Target
architecture (L0–L4)".

---

## Sub-Agent Rules

Sub-agents start with FRESH context — they do NOT inherit rules.

Every sub-agent prompt MUST include:

- "Before any action, read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` and follow ALL rules
  strictly."
- `WORKSPACE_ROOT: <absolute path>`
- MUST set `model=` explicitly (stale "NEVER pass model=" convention retired — CLAUDE.md § "Model tier" is current)

---

## Quality Gates & Pushing

```bash
# Pass 1 — full (lint, tests, typecheck, codex, security)
bash scripts/quality-gates.sh

# Pass 2 — push (lint + format + typecheck + codex; no tests)
bash scripts/quickmerge.sh "your message" --agent   # ALWAYS --agent in Claude Code / CI
```

- `--to-staging` flag for breaking changes (`feat!:` commits) → staging → SIT → main
- `--agent --skip-typecheck` for max speed (lint + format + codex only)
- Staging lock: `staging_status.locked=true` in manifest = SIT running, do not merge to main

**Push before quickmerge (agents and humans)** — `quickmerge` stashes **uncommitted** work, then may align your branch
to `origin/<branch>`. That does **not** protect **commits** that exist only locally: the branch pointer can move to
match the remote and leave earlier local-only commits off the branch (recoverable via `git reflog`, but avoid the
surprise). **Rule:** If you already ran `git commit` on `feat/your-branch` and those commits are **not** on `origin`
yet, run `git push -u origin feat/your-branch` **before** `quickmerge` (or rely on quickmerge alone to create the commit
so there are no orphan local commits). Prefer the two-pass model: Pass 1 QG → Pass 2 `quickmerge --agent` with
**either** a clean working tree of uncommitted changes **or** a pushed branch tip.

**Untrack ignored files** — If tracked files match `.gitignore`, untrack them so history is clean and clones don't get
bad files. Safe workflow: (1) detect: `git ls-files --ignored --exclude-standard`; (2) untrack:
`git rm --cached <files>` (or `git rm -r --cached <dir>` for dirs). Never bare `git rm` — that deletes files from disk.

---

## Coding Rules (Quick Reference)

- `uv pip install` not `pip install`
- `basedpyright` not `pyright`; run as `run_timeout 120 basedpyright <src_dir>/` — never from workspace root
- No `os.getenv()` — use `UnifiedCloudConfig`
- No `try/except ImportError` — fail loud on missing deps
- No `# type: ignore` to hide architectural violations — fix root cause
- No `Any` types — use specific types
- No backwards-compat shims — delete deprecated code
- `from unified_trading_library.events import setup_events, log_event` — no fallbacks
- Search unified libraries before implementing anything new

Full standards: `/codex/06-coding-standards/README.md`

**No summary files** — never create `*_SUMMARY.md`, `*_STATUS.md`, `READY_TO_*`, `COMPLETION_*` files. Report results as
text in the chat, not as committed documents. Rule (ARCHIVED 2026-08-02, no longer live):
`plans/archive/cursor-rules_2026_08_02/core/no-summary-docs.mdc`

---

## Reporting — Telegram

Every agent job must send a Telegram notification on completion (success or failure). Secrets are pre-set on every repo:
`TELEGRAM_BOT_TOKEN` (secret) + `TELEGRAM_CHAT_ID` (variable).

**GHA step template** (copy into any workflow's `steps`, after your main job step):

```yaml
- name: Notify Telegram
  if: always()
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ vars.TELEGRAM_CHAT_ID }}
    STATUS: ${{ job.status }}
    RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
  run: |
    ICON=$([ "$STATUS" = "success" ] && echo "✅" || echo "❌")
    CHANGES=$(git log --oneline origin/main..HEAD 2>/dev/null | head -5 || echo "no commits")
    TEXT="${ICON} *${{ github.workflow }}* | ${STATUS} | repo: \`${{ github.repository }}\`"
    TEXT="${TEXT}"$'\n'"Changes: \`${CHANGES}\`"
    TEXT="${TEXT}"$'\n'"[view run](${RUN_URL})"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TELEGRAM_CHAT_ID}" \
      -d text="${TEXT}" \
      -d parse_mode="Markdown" || true
```

To propagate secrets to all repos (or new repos added to manifest):

```bash
bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh
# or for a single repo:
bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --repo <name>
```

---

## Commits & Versions

- Conventional commits: `feat:`, `fix:`, `chore:`, `feat!:` (breaking)
- `feat/*` → QG only, no PR | breaking → `--to-staging` | `main` → always stable
- **Never bump versions manually** — GitHub Action bumps on merge to main only
- All repos pre-stable: `0.x.x` until first successful CI merge to main

---

## Sub-Agent Prompting Template

Include at the top of every sub-agent prompt:

```
Follow all workspace cursor rules in .cursorrules.
WORKSPACE_ROOT: <absolute path>
For tests/quality gates: cd <repo> && bash scripts/quality-gates.sh (uses per-repo .venv; never .venv-workspace for pytest).
For other Python: cd <WORKSPACE_ROOT> && source .venv-workspace/bin/activate as needed.
```

## 10. Repo Readiness Checklist & Semver Rules

**Readiness SSOT:** `/codex/10-audit/REPO_READINESS_CHECKLIST.yaml` (template) +
`/codex/10-audit/repos/{repo-name}.yaml` (per-repo status)

Every repo progresses through three independent axes:

**Code Readiness (CR)**

- CR1: Functionality 100% — zero NotImplementedError/stubs/TODO in prod paths; audit §2 passes
- CR2: Unit tests 100% passing — QG unit stage green; coverage ≥ floor; cov-report=xml written
- CR3: Integration tests 100% passing — every direct manifest dep has tests/integration/ coverage
- CR4: Quality gate locally green — `bash scripts/quality-gates.sh` Pass 1 fully green
- CR5: Quickmerge to feature branch — CI passes on feat/code-readiness-{repo}

**Deployment Readiness (DR)** — tracked per mode (batch | live | both per repo's deployment_modes)

- DR1: Deployable (Docker builds, infra provisioned, setup-workspace.sh succeeds)
- DR2: CI smoke tests pass (emulators only, zero live calls)
- DR3: Feature environment deployed (GET /health 200, GET /readiness 200)
- DR4: Staging SIT pass (system-integration-tests full suite green)
- DR5: Load/performance pass (P99 ≤ SLA, no memory leaks)
- DR6: Production-ready (zero CRITICAL CVEs, auth verified, runbook exists, 24hr health)

**Business Readiness (BR)** — tracked per mode (batch | live | both per repo's business_modes)

- BR1: Acceptance criteria defined in owning plan
- BR2: Circuit breaker validated (N/A for libraries and UIs)
- BR3: UEI event handling validated (all events fire with correct schema + correlation_id)
- BR4: PnL/performance targets declared AND measured (not estimated)
- BR5: PnL optimization validated via backtest (revenue-path repos only)
- BR6: Batch vs live validation (t+1 check within tolerance)
- BR7: Staging vs live parity (N-minute replay within tolerance)
- BR8: User approved — human sign-off. **NO AGENT MAY SET BR8 AUTONOMOUSLY.**

### v1.0.0 Gate

**NEVER promote a repo to v1.0.0 autonomously.** v1.0.0 requires ALL of:

- CR5 (merged to main via cascade) + DR3 + DR4 + BR2 (services) + BR3 + BR4 + BR8 (no exceptions)

Pre-1.0.0 rule: `feat!:` on `0.x.x` bumps MINOR only. CI never auto-crosses to 1.0.0.

### Per-Repo Semver Rules

Before proposing any commit message with `feat!:`, `feat:`, or `fix:`:

1. Look up `semver_rules_ref` for this repo in `unified-trading-pm/workspace-manifest.json`
2. Read the matching rule set from `unified-trading-pm/docs/per-repo-semver-rules.yaml`
3. Verify the change matches the declared bump level
4. Post-1.0.0: if change is MAJOR — stop and request user approval before proceeding

Check a repo's current readiness state: `cat {repo}/.readiness-ref` to get path to its codex YAML.

Cursor rules (ARCHIVED 2026-08-02, no longer live — kept here as the historical rationale record):
`plans/archive/cursor-rules_2026_08_02/core/repo-readiness-checklist.mdc`,
`plans/archive/cursor-rules_2026_08_02/core/semver-v1-hardening.mdc`,
`plans/archive/cursor-rules_2026_08_02/core/per-repo-semver-rules.mdc`

### MAJOR Bump Approval Gate (ABSOLUTE — all repos, no exceptions)

No agent may bump MAJOR version autonomously. The **only** approved path:

1. `semver-agent.yml` detects MAJOR needed → creates GitHub Issue (label: `major-bump-pending`) → sends Telegram alert
2. Human comments `/approve` on the issue (or `/reject` to cancel)
3. `major-bump-issue-handler.yml` fires → bumps `pyproject.toml` on `staging` branch ONLY → dispatches version-bump to
   PM manifest

To **request** a MAJOR bump from CLI:

```bash
bash unified-trading-pm/scripts/approve-major-bump.sh {repo} {X.0.0} \
  --reason "Breaking change description" \
  --admin-pat $GH_PAT
```

**Agents MUST NOT:**

- Edit `pyproject.toml` to increase MAJOR version
- Dispatch `version-bump` events with a MAJOR version increase
- Comment `/approve` on issues (agents cannot self-approve — humans only)
- Set `staging_versions` in `workspace-manifest.json` to a MAJOR increase autonomously

**Applies to:** all repos including infra (PM, codex, deployment-service). **Applies to:** the initial 0.x.x → 1.0.0
promotion — requires the same issue flow.

---

## Plan Locking (Agent Safety)

Plans with `locked_by` in frontmatter are actively being implemented. Agents MUST NOT:

- Archive locked plans (even if all todos show as done)
- Delete or move locked plans
- Remove the `locked_by` field programmatically

The plan-hygiene tooling checks this automatically (the daily `plan-reconciler` agent's HARD LIMITS forbid touching a
locked plan; see `/codex/11-project-management/plan-hygiene.md`). If you encounter a locked plan during conflict
resolution, treat its contents as authoritative for the locked branch's changes.

**Agent unlock protocol:** If all todos in a locked plan are genuinely complete, agents MAY ask the human: "Plan X is
locked but all todos are done. Should I unlock it?" If the human approves, remove `locked_by`/`locked_since` from
frontmatter and include `[unlock-plan]` in the commit message. If denied, leave it locked. Agents MUST NEVER unlock
autonomously.

## PM/Codex Routing

PM and codex have a doc-only fast-path in quickmerge:

- plans/, docs/, cursor-configs// changes → direct to main (agents fire immediately)
- scripts/, .github/workflows/ changes → staging (SIT validates before main)

This means plan changes are available to agents (plan-health, rules-alignment, codex-sync, conflict-resolution) within
minutes, not hours.

## Workflow Templates (SSOT in PM)

Per-repo GHA workflows are canonical templates in PM — never edit the per-repo copies directly.

- **Templates:** `unified-trading-pm/scripts/workflow-templates/`
- **Rollout (generic):** `bash unified-trading-pm/scripts/propagation/rollout-workflow-templates.sh`
- **Rollout (semver-agent):** `bash unified-trading-pm/scripts/propagation/rollout-semver-agent.sh`
- **Semver agent** uses `__REPO_NAME__`/`__SOURCE_DIR__` placeholders — rollout script substitutes per repo.
- **Hardcoded org names banned** — use `${{ github.repository_owner }}`.
- **Workflows must fail hard** — no silent `|| true` on critical ops (issue creation, Telegram, version bumps).

---

## Downstream Cascade (Planned)

When a breaking change cascades via dependency-update, QG runs on direct dependents in topological order (fail-fast). If
a dependent fails, an autonomous fix agent attempts code repair and creates a PR for human approval. Agents MUST NOT
self-merge fix PRs — always require human /approve. See: cicd_code_rollout_master_2026_03_13.plan.md § Downstream
Cascade Intelligence.

Schema changes in T0 libraries (UAC, UIC, UEI) trigger reverse-dependency sync to update codex docs (PM cursor-rules/
archived 2026-08-02) automatically.

---

## Plans & Tracking

- Active plans: `unified-trading-pm/plans/active/` (`.plan.md` files)
- New AI-generated plans: `unified-trading-pm/plans/ai/` only — never directly to `active/`
- Plan naming: `<topic>_<YYYY_MM_DD>.plan.md`
- Locked plans (`locked_by` in frontmatter): do NOT archive, delete, or unlock autonomously
