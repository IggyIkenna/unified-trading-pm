# AGENTS.md — Unified Trading System

Shared instructions for all autonomous agents (Claude Code, Codex, Cursor) in any repo of this workspace. Ephemeral:
copied from PM during setup-workspace-from-manifest.sh, removed by cleanup script before quickmerge/PR.

---

## Token Optimization — Read First

- No chain-of-thought, no planning prose, no restating context
- Prefer bullets, tables, or JSON over prose
- Launch parallel sub-agents (up to 10/turn) for independent cross-repo tasks
- Sub-agents: ONE narrowly scoped task each; return ONLY final result (≤400 tokens)
- NEVER pass `model=` in sub-agent Task calls — omitting it = auto mode = free
- Sub-agents do NOT inherit session context; always pass `WORKSPACE_ROOT` + venv path explicitly
- **Sub-agents MUST get full rules:** paste contents of `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
  at TOP of prompt, OR instruct: "Before any action, read SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly"
- Full guidance: `unified-trading-pm/cursor-rules/core/token-optimization.mdc`, `agents-follow-cursor-rules.mdc`

---

## Environment

| Use case                  | Venv                        | Command                                                      |
| ------------------------- | --------------------------- | ------------------------------------------------------------ |
| **Quality gates / tests** | Repo `.venv`                | `cd <repo> && bash scripts/quality-gates.sh` — no activation |
| **IDE / general Python**  | Workspace `.venv-workspace` | `source <WORKSPACE_ROOT>/.venv-workspace/bin/activate`       |

**Never** run `pytest` directly. Always use `quality-gates.sh` (uses per-repo `.venv`).

---

## Workspace Structure

**Multi-repo workspace (~62 independent git repos) — NOT a monorepo.** Each subdirectory is its own git repo with its
own pyproject.toml, venv, and QG script.

```
unified-trading-system-repos/
├── unified-trading-pm/          # Plans, scripts, cursor rules, workspace manifest (SSOT)
├── unified-trading-codex/       # Coding standards, architecture docs
├── unified-cloud-interface/     # T0 — cloud primitives
├── unified-config-interface/    # T0 — config
├── unified-events-interface/    # T0 — events
├── unified-trading-library/     # T1 — shared library
├── unified-domain-client/       # T2/T3 — domain client
├── market-tick-data-service/    # T3 service (level 8)
├── strategy-ui/                 # UI repo (level 11)
└── ...                          # ~55 more repos
```

**Key files (all in `unified-trading-pm/`):**

- `workspace-manifest.json` — SSOT: all repos, types, deps, versions, merge order
- `plans/active/INDEX.md` — canonical plan registry
- `cursor-rules/` — all cursor rules (workspace root `.cursor/rules` → here)
- `cursor-configs/CLAUDE.md` — Claude Code instructions (symlinked into every repo's `.claude/`)

---

## Manifest Structure

Every repo entry in `workspace-manifest.json`:

```json
{
  "type": "service | library | ui | infrastructure | api",
  "arch_tier": "0 | 1 | 2 | 3 | service | ui | api | infrastructure",
  "dependencies": [{ "name": "unified-trading-library", "version": ">=0.1.0,<1.0.0", "required": true }]
}
```

Tier/level order: `topologicalOrder.levels` (SSOT). Repo level = which level lists it.

**Tier invariant:** T0 → T1 → T2 → T3 — never import from a higher tier. T0 must be fully green before T1.

**Dependency checkout in GHA** — every repo's `scripts/setup-workspace.sh`:

```bash
bash scripts/setup-workspace.sh   # clones PM + all direct manifest deps as siblings; pre-flight checks
```

Pre-flight outcomes: required dep clone failure → `exit 1` | optional failure → warn | version mismatch → warn.

What `setup-workspace.sh` also sets up for you:

- **Cursor rules** — copied as real files (not symlinks) to `$WORKSPACE_ROOT/.cursor/rules/` from PM
- **`.cursorrules`** — copied to `$WORKSPACE_ROOT/.cursorrules` from PM
- **AGENTS.md** — copied as a real file to `$WORKSPACE_ROOT/AGENTS.md` from PM (ephemeral)
- **`.claude/CLAUDE.md`** — workspace-root symlink → PM `cursor-configs/CLAUDE.md`
- **Cleanup script** — `$WORKSPACE_ROOT/.cleanup-cursor-rules.sh` generated automatically

**Cursor rule cleanup is mandatory before quickmerge / PR creation:**

```bash
bash $WORKSPACE_ROOT/.cleanup-cursor-rules.sh   # removes ephemeral .cursor/rules + .cursorrules + AGENTS.md
```

The per-repo `.claude/CLAUDE.md` is a committed symlink. AGENTS.md is ephemeral (copied during setup, removed by
cleanup).

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
- `from unified_events_interface import setup_events, log_event` — no fallbacks
- Search unified libraries before implementing anything new

Full standards: `unified-trading-codex/06-coding-standards/README.md`

**No summary files** — never create `*_SUMMARY.md`, `*_STATUS.md`, `READY_TO_*`, `COMPLETION_*` files. Report results as
text in the chat, not as committed documents. Rule: `cursor-rules/core/no-summary-docs.mdc`

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

**Readiness SSOT:** `unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml` (template) +
`unified-trading-codex/10-audit/repos/{repo-name}.yaml` (per-repo status)

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

Cursor rules: `cursor-rules/core/repo-readiness-checklist.mdc`, `cursor-rules/core/semver-v1-hardening.mdc`,
`cursor-rules/core/per-repo-semver-rules.mdc`

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

## Plans & Tracking

- Active plans: `unified-trading-pm/plans/active/` (`.plan.md` files)
- Registry: `unified-trading-pm/plans/active/INDEX.md` — register all new plans here
- SSOT index: `unified-trading-codex/00-SSOT-INDEX.md`
- Naming: `<topic>_<YYYY_MM_DD>.plan.md`
