# SUB-AGENT MANDATORY RULES — Lean Essentials

> Sub-agent in the **Unified Trading System** workspace — context is FRESH, nothing inherited. **Read this file in full
> before your first tool call.** Non-negotiable floor; for domain rules read `cursor-configs/CLAUDE.md` + only the codex
> SSOT your task touches (conditional-load — skip what doesn't apply).

## Identity + workspace

- **Multi-repo workspace** (NOT a monorepo) on `live-defi-rollout`; edit only your task's named repo. **Per-slot
  worktrees (Path-B)**: each slot is a `git clone --reference` with its OWN `.git` (`tab/<op>/N` RETIRED). Stay current
  `git pull --ff-only origin live-defi-rollout`; invariant = HEAD ancestor-or-equal of `origin/live-defi-rollout`. SSOT:
  `/codex/05-infrastructure/per-tab-worktrees.md`.
- **Agent memory is BANNED (HARD RULE)**: never write to `memory/` or `MEMORY.md` — it's per-cwd, not inherited, and
  causes drift. Session findings go to the plan's Progress Log only.
- **Before any task (HARD RULE)**: grep `plans/active/`+`issues/` for conflicts first (0 hits ≠ clear). **CLAIM ≤
  MEASUREMENT**: 0 hits ≠ missing (runtime-resolved) — read the consumer; a PROXY (line count, exit 0, green test) ≠ the
  property — measure or say you didn't; uncertain → ASK. SSOT:
  `/codex/12-agent-workflow/measurement-claims-discipline.md`. Never `python3 <<EOF` for file analysis — use `rg`.
- **Batch independent tool calls — the trigger is PRE-call**: before any Bash/Read/Grep ask _what else will I want
  regardless of this answer_ and fold it into the SAME call (compound `&&`/`;`, several `tool_use` blocks, `replace_all`
  over serial Edits); only result-dependent calls stay sequential. 57.3% collapsible. SSOT:
  `/codex/06-coding-standards/tool-call-batching.md`.

## Quality gates / tests — the ONLY way to run them

```bash
cd <repo> && bash scripts/quality-gates.sh           # ship mode — only when you own a tree-wide reformat
cd <repo> && bash scripts/quality-gates.sh --no-fix   # no reformat — committing only your own named files
```

**Never** run `pytest` directly (wrong venv); **never** `pip install` (use `uv pip install`); **never** re-lock
internal-dep drift in `uv.lock`. A green `quality-gates.sh` tree is the per-repo quality boundary — the gate enforces
the bans, so green tree = contract. **QG admission is RESOURCE-based — just invoke it, it queues; never quote a fixed
concurrency cap (legacy), never bulk-kill another slot's `pytest`/QG.** SSOT:
`/codex/06-coding-standards/quality-gates.md`.

## Ship CODE: two-pass, never a raw `git push`

1. **Pass 1 — full quality gate** writes `.qg_last_passed_sha` (== HEAD); skip it and Pass 2 refuses. The commit is the
   quality boundary for EVERY code commit, not just the ship. Gate ONCE per batch (QG-sweep) → per-unit commits.
2. **Pass 2 — `bash scripts/quickmerge.sh "feat: …" --agent --files '<p1> <p2>'`** — ALWAYS `--agent`, scope `--files`
   by name (never the whole tree, never `git add -A` even on prek retry). Verifies sentinel == HEAD, stages, commits,
   lands on LDR; a standing job promotes LDR→main DIRECT behind `quality-gates-v2` (staging is DORMANT). **A raw
   `git push` of code is BANNED** (dodges dep gates). Carve-outs: dirty-deps; PM `docs(plans):` flip via
   `scripts/dev/safe-doc-push.sh`. **Never `[skip ci]`** on a v2-gated promotion-PR commit (required check goes MISSING
   → PR BLOCKED). **NEVER force-push a shared branch.**
3. **Commit + Push + Flip, SAME turn (HARD RULE)**: flip `- [ ]` → `- [x] — <repo>@<sha> + evidence`, commit with the
   MANDATORY `docs(plans):` prefix (`plan(...)` is hook-rejected) — unflipped is invisible to the orchestrator, causing
   a wasted re-dispatch. An all-done unlocked plan archives immediately (`locked_by` needs `[unlock-plan]` ask). SSOT:
   `/codex/08-workflows/ci-cd-flow.md`.

**Behind remote**: quickmerge STAGE 0.4 auto-reconciles (ff → rebase-autostash); same-file conflict → `rebase --abort`,
then `QUICKMERGE_BLOCKED` recovery per the autostash recipe — never blind-overwrite.

## Foot-guns (each has burned the workspace)

- **Foreign work in your commit**: stage by NAME, never `git add .`/`-A`; re-stage by name after any hook reformat.
- **`git diff --cached --stat <path>` masks other staged hunks** — never pass a path arg.
- **Never** `git checkout origin/<b> -- .` / `... HEAD -- <file>` on a dirty file you don't own, `git stash drop`
  foreign WIP, or `git reset --hard`/`clean -fd`/`restore` uncommitted work — all UNRECOVERABLE.
- **Verify against the stable remote ref** (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`, never
  `FETCH_HEAD`); **inherited dirty WIP is LIVENESS-gated** — dead `.agent-claim` → inherit + commit, live/mtime <120s →
  PROTECT.
- **Generated artifacts + QG sentinels are gitignored** (`*_DAG.svg`/`coverage.xml`/`.qg_*`) — post-QG dirt is regen
  churn; NEVER `git add` it.

## Banned patterns (workspace-wide, zero exceptions — QG enforces)

Suggesting one of these is a rule-amnesia signal — STOP.

❌ `os.getenv()` (use `UnifiedCloudConfig`) · `try/except ImportError` · `# type: ignore` · `Any` · `pip install` ·
`pytest` directly · hardcoded `"/tmp"` (use `tempfile.gettempdir()`) · inline `gs://`/`s3://` (use
`resolve_bucket_name(...)`) · direct `google.cloud`/`boto3` (use `get_storage_client()`/`get_secret_client()`) · non-UTC
datetimes (use `datetime.now(timezone.utc)`) · **service→service dependency** (a T4 service depends only on shared libs
UTL/UAC/`unified-*-interface`; integrate by API contract + mocks) · fire-and-forget VM launches · empty placeholder rows
that look populated (`record_failed`/`record_empty`, never fake `record_captured`) · hand-raising a QG ratchet baseline
(never raise, only lower) · `*_SUMMARY.md` docs · bare `npx prettier` (use `prettier-autostage.sh`). SSOT:
`codex/06-coding-standards/` + `/codex/04-architecture/tier-and-import-architecture.md`.

## Findings triage (HARD RULE)

In your file → fix in same commit. Adjacent to your plan → fix in YOUR plan. Outside-plan small+clear → ≤30 min.
Outside-plan ambiguous → diagnose both sides. Fits another plan → annotate it, don't fix (collision risk). Outside every
plan → `plans/active/issues/<slug>_<YYYY_MM_DD>.md`. **Big finding** (data-correctness / May-23 critical path /
cross-repo / SSOT contradiction / kill-switch / batch≠live) → **NOTIFY THE OPERATOR** in chat AND file an issue doc.
"Pre-existing" is NOT a triage criterion.

## Plans + completion discipline

- **New plan? ASK first** — AO-dispatched (`planning`) or human (`NA`, default); read `plans/active/task_template.md`. A
  plan REFERENCES codex, never duplicates it — check it against the docs it cites (drift is review-blocking).
- **Plans run to actual completion, not smoke-test green** — code-shipped ≠ operationally-shipped (VM emitted
  STARTED/progress/STOPPED; backfill manifest verified-non-NaN). A `- [x]` deploy claim needs
  `Evidence: cloudbuild=<id>` resolving SUCCESS. Hard-stops (human-only): wallet keys / kill-switch arming / force-push
  main. Otherwise you have admin perms — `PERMISSION_DENIED` as a service account? GRANT the role yourself, verify,
  continue (not `[OPERATOR]`). SSOTs: `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a,
  `…/orchestrator-cloud-identity-self-service.md`.
- **Capture every side-discovery as a plan todo immediately** (P0-P3 + provenance, never auto-memory/chat-summary).
  **Citadel planning**: pre-audit the blast radius (grep removed/renamed symbols first); phased DAG + QG gates; no
  shims; SSOT types in UAC.

## Async-wait / background work

Never report a backgrounded task done before its real exit; rely on the tracked-task auto-re-invoke (don't poll harness
tasks); poll external work only on a **progress metric** (flat = STALL → diagnose); reach a TERMINAL **measured**
verdict (liveness `kill -0 <PID>`, no self-match) — `ScheduleWakeup`/a dispatched sub-agent are NOT reliable wakes, arm
your OWN `run_in_background` heartbeat watchdog (≤30-min). **Never `gh workflow run ldr-to-main-promote-fleet.yml` to
check if your repo promoted** — starves its one shared slot (measured 2+ hr livelock); read `promotion_lag_monitor.py`
or `gh pr list --search "chore(promote)"`. SSOT: `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`.

## When YOU spawn sub-agents

**Max 5 parallel** (different repos ok, same file never) — the host is SHARED by ~4 slots (operator ruling 2026-08-10).
Paste THIS file at the TOP of every Task spawn (no inherited context); if impractical, prepend "read
`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` in full and follow ALL rules" — injection failure means
the agent MUST NOT proceed. Send all `Task` calls in ONE message; set `model=` explicitly. Finish-to-DONE → also paste
`cursor-configs/AUTONOMOUS_AGENT_RULES.md`.

## When escalating a question to the operator (HARD RULE)

**Always present options, never open-ended** — min 2, your recommendation marked (e.g. "A: … [WORKER REC]"); the
dashboard has an "Other" free-text input. Only one path genuinely exists → say so. Never a bare yes/no unframed.

## When in doubt — retrieve less but right

**Grep the L0 doc index first**: `unified-trading-pm/DOC_INDEX.generated.md` (gitignored; regen
`scripts/docs/refresh-doc-index.sh`; grep, NEVER read whole). Narrow by facet —
`rg -l '^authoritative_for:.*<topic>' codex/` lands THE one SSOT; confirm its `summary:`, open ONLY that doc;
`code_refs` jumps doc→code. Fallback: `cursor-configs/CLAUDE.md`'s domain index — or ask the operator a focused question
(≤1 min read-only investigation first).

- **Ship via `safe-doc-push.sh`/`quickmerge.sh` — they COMMIT FROM AN ISOLATED WORKTREE** so a peer session sharing your
  checkout can't revert your edits; never re-improvise reconcile-retry. **quickmerge 10 / safe-doc-push 12·13 = your
  change is NOT on origin — RECOVER from the printed ref, never plain re-run**; verify with a marker only YOUR change
  could have produced. SSOT: `/codex/12-agent-workflow/ship-tooling-silent-success.md`.
