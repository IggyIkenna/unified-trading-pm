# AGENTS.md — Unified Trading System

Shared instructions for all autonomous agents (Claude Code, Codex, Cursor) in any repo of this workspace. Symlinked into
every repo: `AGENTS.md → ../unified-trading-pm/AGENTS.md`

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
