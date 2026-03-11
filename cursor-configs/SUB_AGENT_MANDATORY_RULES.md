# Sub-Agent Mandatory Rules — Full Workspace Standards

**You are a sub-agent. You MUST follow ALL rules below. Read this entire document before any action.**

Sub-agents start with FRESH context and do NOT inherit the parent's rules. This file is the SSOT for workspace
standards.

---

## 1. Environment & Tooling

- **uv not pip** — always `uv pip install`
- **basedpyright not pyright** — run as `timeout 120 basedpyright <source_dir>/` — NEVER `basedpyright .` or
  `basedpyright` (no args)
- **quickmerge not git push** — `bash scripts/quickmerge.sh "message"` — never `git push`, never standalone
  `scripts/quality-gates.sh`
- **Tests:** `bash scripts/quality-gates.sh` — never `pytest` or `python -m pytest` directly (uses wrong venv)
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
- **Dependency conflict:** ALWAYS use `--dep-branch` — never suggest `git reset --hard` on deps
- **Never bump versions manually** — CI bumps on merge to main
- **Untrack ignored files** — if tracked files match `.gitignore`: detect with
  `git ls-files --ignored --exclude-standard`, then `git rm --cached <files>`. Never bare `git rm` (deletes files)

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
- **General Python (non-test):** `.venv-workspace` for IDE; `uv sync --extra dev && source .venv/bin/activate` for
  per-repo isolated runs.

---

## 7. Agent-Specific (Quickmerge)

- Use `--agent` in agent sessions: `bash scripts/quickmerge.sh "feat: ..." --agent`
- Use `--dep-branch` when dependencies differ from main
- Breaking changes: `--to-staging`

---

**Venv vs testing:** `.venv-workspace` = IDE only. Tests use per-repo `.venv` via quality-gates.sh. See
`.cursor/rules/testing/no-manual-pytest.mdc`.

**CODEX:** unified-trading-codex/06-coding-standards/README.md
