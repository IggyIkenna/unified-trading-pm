# SUB-AGENT MANDATORY RULES — Lean Essentials

> You are a sub-agent / autonomous agent in the **Unified Trading System** workspace. Your context is FRESH — you
> inherited nothing. **Read this file in full before your first tool call.** The rules below are the non-negotiable
> floor; for anything domain-specific, **read `cursor-configs/CLAUDE.md` and only the codex SSOT your task actually
> touches** (conditional-load — don't read data/UI/DeFi/infra rules for a task that doesn't involve them).

## Identity + workspace

- **Multi-repo workspace** (NOT a monorepo); edit only the target repo your task names. Active branch
  `live-defi-rollout`.
- **Per-slot worktrees (Path-B)**: each slot is a `git clone --reference` with its OWN `.git`, checked out on
  `live-defi-rollout` (the `tab/<op>/N` tab-branch model is RETIRED — no tab branch/mirror; any such instruction is
  STALE). Stay current `git pull --ff-only origin live-defi-rollout`; the one invariant = HEAD ancestor-or-equal of
  `origin/live-defi-rollout`. SSOT: `codex/05-infrastructure/per-tab-worktrees.md`.

## Quality gates / tests — the ONLY way to run them

```bash
cd <repo> && bash scripts/quality-gates.sh           # ship mode (autofix + check) — only when you own a tree-wide reformat
cd <repo> && bash scripts/quality-gates.sh --no-fix   # diagnostic / committing only your own named files (NO tree reformat)
```

**Never** run `pytest` directly (wrong venv); **never** `pip install` (use `uv pip install`); **never** re-lock
internal-dep drift in `uv.lock` (editable range-pins absorb minor/patch by design — only a MAJOR bump acts). A
`quality-gates.sh`-green tree is the per-repo quality boundary — **the gate ENFORCES the banned patterns, so a green
tree is the contract.** SSOT: `codex/06-coding-standards/quality-gates.md`.

## Ship CODE: two-pass, never a raw `git push`

1. **Pass 1 — full quality gate** writes `.qg_last_passed_sha` (== HEAD). Skipping it means the change never ran tests;
   Pass 2 refuses on the missing sentinel. **The commit is the per-repo quality boundary** — this binds EVERY code
   commit toward the integration branch, not just the quickmerge ship. Gate ONCE over a batch (QG-sweep) → per-unit
   commits.
2. **Pass 2 — `bash scripts/quickmerge.sh "feat: …" --agent --files '<path1> <path2>'`** — ALWAYS `--agent`, ALWAYS
   scope `--files` by name (never the whole tree). It verifies sentinel == HEAD, stages only your `--files` (re-asserts
   scope on the prek retry — never `git add -A`), commits, lands on LDR; the Tier-C drain promotes LDR→staging→main with
   the server `quality-gates-v2` gate. **A raw `git push` of code is BANNED** (it dodges the dep gates + early-exits on
   a clean tree so commits pile up behind main with no PR). Closed carve-out direct pushes: dirty-deps; the FF-pull-in +
   cross-repo PM `docs(plans):` flip. **Never `[skip ci]`** a commit destined for a v2-gated promotion PR (required
   check goes MISSING → PR BLOCKED). **NEVER force-push a shared branch.**
   - **Pre-`--files` hygiene (MANDATORY)**: `git status && git diff --cached --stat` (NO path arg — see the WHOLE index)
     so you pass only YOUR paths. `--no-verify` only on prek auto-restore symptoms; verify `git show --stat HEAD` that
     your file landed.
3. **Commit + Push + Flip in the SAME turn (HARD RULE)**: after the code push, flip the plan checkbox `- [ ]` →
   `- [x] — <repo>@<sha> + evidence`, commit with the MANDATORY `docs(plans):` prefix (`plan(...)` is hook-rejected). An
   unflipped item is invisible to the orchestrator → it re-dispatches → wasted work. SSOT:
   `codex/08-workflows/ci-cd-flow.md`.

**Conditional push (multi-agent)**: `git fetch` first; 0 incoming → push freely; behind-remote at quickmerge → STAGE 0.4
auto-reconciles (ff → rebase-autostash), genuine same-file conflict → `rebase --abort` + structured `QUICKMERGE_BLOCKED`
exit (recover per the autostash recipe, never blind-overwrite).

## Foot-guns (each has burned the workspace)

- **Foreign work in your commit**: stage by NAME, never `git add .`/`-A`; after any hook reformat re-stage by name.
- **`git diff --cached --stat <path>` masks other staged hunks** — never pass a path arg there.
- **Never** `git checkout origin/<b> -- .` / `git checkout HEAD -- <file>` on a dirty file you don't own, or
  `git stash drop` a foreign WIP, or `git reset --hard`/`clean -fd`/`restore` uncommitted work — all UNRECOVERABLE.
- **Verify against the stable remote ref** (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`), never
  `FETCH_HEAD`.
- **Inherited dirty WIP is LIVENESS-gated**: dead/expired `.agent-claim` → inherit + commit; live claim / mtime <120s →
  PROTECT.
- **Generated artifacts + QG sentinels are gitignored** — a dirty `*_DAG.svg`/`coverage.xml`/`.qg_*` after a QG run is
  regen churn; NEVER `git add` it.

## Banned patterns (workspace-wide, zero exceptions — QG enforces)

❌ `os.getenv()` (use `UnifiedCloudConfig`) · `try/except ImportError` · `# type: ignore` · `Any` · `pip install` ·
`pytest` directly · hardcoded `"/tmp"` (use `tempfile.gettempdir()`) · inline `gs://`/`s3://` (use
`resolve_bucket_name(...)`) · direct `google.cloud`/`boto3` (use `get_storage_client()`/`get_secret_client()`) · non-UTC
datetimes (use `datetime.now(timezone.utc)`) · **service→service dependency** (a T4 service depends only on shared libs
UTL/UAC/`unified-*-interface`; integrate by API contract + mocks) · fire-and-forget VM launches · empty placeholder rows
that look populated (`record_failed`/`record_empty`, never fake `record_captured`). SSOT: `codex/06-coding-standards/` +
`codex/04-architecture/tier-and-import-architecture.md`.

## Findings triage (HARD RULE)

In your file → fix in same commit. Adjacent to your plan → fix in YOUR plan. Outside-plan small+clear → ≤30 min.
Outside-plan ambiguous → diagnose both sides. Fits another plan → annotate it, don't fix (collision risk). Outside every
plan → `plans/active/issues/<slug>_<YYYY_MM_DD>.md`. **Big finding** (data-correctness / May-23 critical path /
cross-repo / SSOT contradiction / kill-switch / batch≠live) → **NOTIFY THE OPERATOR** in chat AND file an issue doc.
"Pre-existing" is NOT a triage criterion.

## Plans + completion discipline

- **Plans run to actual completion, not smoke-test green** — code-shipped ≠ operationally-shipped (the VM actually
  launched + emitted STARTED/progress/STOPPED, the backfill filled the manifest with verified-non-NaN parquets). You
  have admin perms on both clouds. Hard-stops (human-only): wallet keys / kill-switch arming / force-push main /
  destructive ops beyond local.
- **A plan REFERENCES codex (the SSOT), never duplicates it; when you touch a plan, check it against the codex docs it
  cites** (plan↔codex drift is review-blocking). **Capture every side-discovery as a plan todo immediately** (P0-P3 +
  provenance — never auto-memory/chat-summary). **Citadel planning**: pre-audit the blast radius (grep every
  removed/renamed symbol; **grep-then-READ** — 0 hits ≠ missing, features are runtime-resolved); phased DAG + QG gates;
  no shims; SSOT types in UAC.

## Async-wait / background work

Never report a backgrounded task done before its real exit; rely on the tracked-task auto-re-invoke (don't poll harness
tasks); poll only external work on a **progress metric** (flat = STALL → diagnose); monitors read terminal `exit_code` +
log-mtime + reach a TERMINAL **measured** verdict (liveness `kill -0 <PID>`, no self-match). `ScheduleWakeup` / a
dispatched sub-agent are NOT reliable wakes — arm your OWN `run_in_background` heartbeat watchdog (≤30-min). SSOT:
`codex/12-agent-workflow/async-wait-and-poll-discipline.md`.

## When YOU spawn sub-agents

Paste THIS file at the TOP of every Task spawn (sub-agents do NOT inherit context); if paste impractical, prepend "read
`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` in full and follow ALL rules." If injection fails, the
agent MUST NOT proceed. Send all `Task` calls in ONE message; set `model=` explicitly. Finish-to-DONE → also paste
`cursor-configs/AUTONOMOUS_AGENT_RULES.md`.

## When escalating a question to the operator (HARD RULE)

**Always present options — never ask an open-ended question.** Every escalation must be structured as:

```
<question text>

A: <option — include your recommendation here if you have one>
B: <option>
C: <option>
Other: operator can type a custom answer
```

- Minimum 2 options; include your recommended option and mark it explicitly (e.g. "A: … [WORKER REC]").
- If genuinely only one path exists, say so and confirm rather than framing it as a choice.
- The orchestrator dashboard exposes an "Other" input for free-text — structure your options so the operator can pick
  one or override with custom text. Never block on a yes/no without framing both sides.

## When in doubt

Read `cursor-configs/CLAUDE.md` (the workspace index) + the ONE codex doc your task's domain points to —
`codex/02-data/` (manifest/data), `codex/04-architecture/` (services/DeFi/funds), `codex/05-infrastructure/` (VM/infra),
`codex/06-coding-standards/` (code/QG/UI). Or ask the operator a focused question (spend ≤1 min on read-only
investigation first so it's specific).
