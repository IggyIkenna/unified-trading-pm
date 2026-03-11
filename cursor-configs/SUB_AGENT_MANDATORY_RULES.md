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
- **Cassette tests**: VCR cassettes live in `unified-api-contracts/unified_api_contracts_external/*/mocks/`; parity
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

**Venv vs testing:** `.venv-workspace` = IDE only. Tests use per-repo `.venv` via quality-gates.sh. See
`.cursor/rules/testing/no-manual-pytest.mdc`.

**CODEX:** unified-trading-codex/06-coding-standards/README.md
