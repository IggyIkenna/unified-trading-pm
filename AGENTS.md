# AGENTS.md — Unified Trading System

Shared instructions for all autonomous agents (Claude Code, Codex, Cursor) in any repo of this workspace. Symlinked into
every repo: AGENTS.md is ephemeral (copied from PM during setup, removed after use)

---

## Token Optimization — Read First

- No chain-of-thought, no planning prose, no restating context
- Prefer bullets, tables, or JSON over prose
- Launch parallel sub-agents (up to 10/turn) for independent cross-repo tasks
- Sub-agents: ONE narrowly scoped task each; return ONLY final result (≤400 tokens)
- NEVER pass `model=` in sub-agent Task calls — omitting it = auto mode = free
- Sub-agents do NOT inherit session context; always pass `WORKSPACE_ROOT` + venv path explicitly
- Full guidance: `unified-trading-pm/cursor-rules/core/token-optimization.mdc`

---

## Environment

```bash
# Activate workspace venv (Python 3.13, ruff, basedpyright, all libs editable-installed)
source <WORKSPACE_ROOT>/.venv-workspace/bin/activate

# Per-repo venv for isolated test/typecheck runs
uv sync --extra dev && source .venv/bin/activate
```

Verify: `which python` → `.venv-workspace/bin/python` (or `.venv/bin/python` for isolated runs).

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
├── market-tick-data-service/    # T3 service (merge_level 8)
├── strategy-ui/                 # UI repo (merge_level 11)
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
  "merge_level": 8,
  "dependencies": [{ "name": "unified-trading-library", "version": ">=0.1.0,<1.0.0", "required": true }]
}
```

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
For any shell command using Python, pytest, or quality gates:
  cd <WORKSPACE_ROOT> && source .venv-workspace/bin/activate first.
```

---

## Plans & Tracking

- Active plans: `unified-trading-pm/plans/active/` (`.plan.md` files)
- Registry: `unified-trading-pm/plans/active/INDEX.md` — register all new plans here
- SSOT index: `unified-trading-codex/00-SSOT-INDEX.md`
- Naming: `<topic>_<YYYY_MM_DD>.plan.md`
