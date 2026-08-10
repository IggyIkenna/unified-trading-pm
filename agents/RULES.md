# Agent worker-lifecycle rules

> **You are reading this from the canonical root PM clone (`unified-trading-pm/agents/`). Root-repo reads are
> READ-ONLY.** ALL your work happens inside your assigned slot directory `.tabs/<your-slot>/` — never edit, commit, or
> run work in root clones.
>
> **What this is**: the worker-lifecycle layer for orchestrator-spawned agents (worker, main, review, monitor) — the
> things NOT already in the auto-loaded workspace `CLAUDE.md`: your worktree contract, the ship→plan-flip→`/done` loop
> the **server verifies**, sub-agent spawning, and the backlog / HTTP surface you drive.
>
> **CLAUDE.md auto-loads.** Every repo has a `.claude/CLAUDE.md → cursor-configs/CLAUDE.md` symlink, so the full
> workspace rules (uv·quickmerge·basedpyright·findings-triage·the 8 code rules·honest-absence·…) are ALREADY in your
> context. This file does **not** restate them — it points to them (§6) and adds the worker-lifecycle specifics on top.
>
> **Every role's boot message opens with**: read this file before any other action.
>
> **Doc retrieval — retrieve less but right**: grep `unified-trading-pm/DOC_INDEX.generated.md` (L0; per-clone
> gitignored; regen `bash scripts/docs/refresh-doc-index.sh`; never read whole) →
> `rg -l '^authoritative_for:.*<topic>' codex/` → confirm `summary:` → open only the confirmed doc → `code_refs` for the
> doc→code jump. Full rule: workspace CLAUDE.md § "Doc retrieval".

---

## 0. STEP 0 — read your plan/issue's `context_scope` before starting any todo (HARD RULE)

Once `/boot` hands you a task, before touching any todo: open `task.plan_ref` and check its frontmatter for a
`context_scope` field. It's an ELECTIVE `free_list` (corpus backfill still in progress — most docs don't have one yet;
absent/empty is a no-op, fall back to the normal doc-retrieval flow, CLAUDE.md § "Doc retrieval") of the codex SSOTs (+
occasional script paths) the `/context-scout` skill has already curated as the MINIMAL reading list that doc's remaining
work depends on. When present, READ every listed path before starting work — it's cheaper than a cold grep of the wider
corpus and is maintained specifically so you don't have to re-derive it. SSOTs:
`/codex/11-project-management/doc-frontmatter-schema.md`, `/cursor-configs/skills/context-scout/SKILL.md`.

---

## 1. Your worktree — read from root, operate only in your slot

The dynamic values below — your slot id, workspace root, server URL, account, model — all arrive in your **boot
message**. This file is the static playbook; your boot message carries the per-session specifics.

You do your work inside a per-slot git clone at `${WORKSPACE_ROOT}/.tabs/<your-slot>/`, which holds sibling clones of
every repo: `unified-api-contracts/`, `market-tick-data-service/`, `agent-orchestrator/`, etc.

**Topology — Path-B reference-clones (the `tab/<operator>/<slot>` tab-branch model is RETIRED).** Each slot repo
`.tabs/<N>/<repo>` is its OWN `git clone --reference` with its **own `.git`**, checked out **directly on
`live-defi-rollout`** — there is NO tab branch, no `tab-mirror`, no upstream re-pointing. You commit ON
`live-defi-rollout` and ship via `quickmerge --agent --files '<paths>'`. The one invariant to police: your HEAD is
ancestor-or-equal of `origin/live-defi-rollout`. If you ever encounter `tab/<op>/N` branches, `tab-mirror`,
`--force-with-lease`-to-a-tab-branch, or `extensions.worktreeConfig` per-worktree identity in any doc or script, it is
STALE — report or fix it, do not act on it. SSOT: `codex/05-infrastructure/per-tab-worktrees.md`.

- **Reading the canonical role/RULES files means reading OUTSIDE your slot** (they live in the root PM clone at
  `unified-trading-pm/agents/`). Those reads are **READ-ONLY**. You WRITE, commit, and run work ONLY inside your
  assigned `.tabs/<your-slot>/` slot clone.
- **Stay in YOUR slot.** Other slots have their own `.tabs/<N>/` parallel. Editing files outside your
  `.tabs/<your-slot>/` tree (other than reading the canonical root docs) is a scope violation.
- **Don't touch dirty files in other workspace areas.** Two operators + many parallel slots work in parallel — untracked
  files / mid-edit dirty state in another agent's tree IS in-flight work. Leave it alone. (Full foreign-WIP /
  shared-worktree recovery recipes are in CLAUDE.md § "Multi-agent safety".)
- **Process kills — exact PID only, never a name-based pattern (HARD RULE, incident 2026-07-28).** To kill a background
  process YOU started this session (e.g. a stale `quality-gates.sh` run), kill only the exact PID/PGID you captured at
  launch time (`$!`, or the child PID) — **never** `pkill -f <script-basename>` / `pkill -f "quality-gates.sh --no-fix"`
  / any pattern lacking a slot-specific discriminator (full absolute cwd, or PID/PGID). Every slot invokes shared
  scripts with identical argv, so a name-based pattern is host-wide, not slot-scoped, and will kill a DIFFERENT slot's
  live QG run — confirmed incident (now resolved + archived, two recurrences):
  `plans/archive/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md`. **Mechanically enforced** on any host
  where `scripts/dev/install-pkill-guard-shell-env.sh` has run: a `pkill`/`pgrep` shell function REFUSES a bare
  name-only pattern instead of executing it host-wide — see `/codex/05-infrastructure/per-tab-worktrees.md` §
  "pkill/pgrep cross-slot-kill guard".
- **Bound memory BEFORE running any heavy script directly on this shared host (HARD RULE, RECURRING incident class — 3
  same-shape outages: 2026-07-27 `candle_coverage_gap.py` 15.8GB degraded AO's poll loop; 2026-07-31
  `expand_defi_pool_catalogue_from_manifest.py` 43.6GB caused a full AO outage; 2026-08-01
  `features_service.cross_instrument` 38.8GB caused a SECOND full AO outage the same day — the SSOT rule below already
  existed after incident 1 and still didn't stop 2 or 3).** The SSOT's own wording ("ad-hoc scratchpad script") is
  misleadingly narrow — incidents 2 and 3 were REAL, tracked service/CLI code (`instruments-service/scripts/...`,
  `features_service.cross_instrument`), not throwaway files, run directly as part of ordinary task work. Read it as:
  **any subprocess you invoke directly on this VM that could plausibly load a nontrivial dataset into memory** (a
  manifest, a multi-day/multi-instrument batch compute, a corpus scan) — scratchpad or production code, doesn't matter.
  Before running one: (1) confirm it already reads via a streamed/chunked/column-pruned path rather than materializing
  the whole working set, (2) if unsure or it can't be bounded easily, wrap it —
  `bash scripts/dev/run-bounded-analysis.sh <cmd>` (cgroup-enforced memory cap, exit 137 on breach) — or (3) if it's
  genuinely corpus-scale, dispatch it to a dedicated VM instead of running it here. **Do not trust `timeout <n>` alone
  as a substitute for a memory bound** — a process that ignores/delays `SIGTERM` runs past its stated wall-clock bound
  regardless (confirmed 2026-08-01: a `timeout 150`-wrapped process ran ~100x past its bound, then also ignored a direct
  `SIGTERM` for 12+ seconds, needing `SIGKILL`); use `timeout --kill-after=<n>` if you need a hard wall-clock cutoff,
  and bound memory separately regardless. Full SSOT: `/codex/05-infrastructure/vm-launcher-runbook.md` § "Heavy
  COMPUTE/MEMORY on the shared planning-vm".
- **Re-Read immediately before Edit/Write — never reuse an earlier turn's Read (pattern identified from a DeepSeek
  flash-vs-pro transcript comparison, 2026-08-05).** A file can change between your Read and a LATER Edit/Write of the
  same file within one task — a pre-commit hook reformatted it, an earlier Edit/Write this same turn already touched it,
  or a sibling process wrote to it. Reusing memorized content from a stale Read is the direct cause of two of the most
  common wasted-turn errors: `File has been modified since read` (Write refused) and
  `String to replace not found in file` (Edit's `old_string` no longer matches the live content). Re-Read the exact file
  immediately before any Edit/Write that isn't its first touch this turn — one cheap tool call beats a retry cycle.
- **Never delete another agent's already-landed content in a shared plan/issue doc — append, don't replace (confirmed
  root cause, 2026-08-08 incident, `quickmerge_concurrent_same_file_edit_blind_overwrite_2026_08_08.md`).**
  Investigation + direct reproduction (3 scratch-repo scenarios run through quickmerge's exact STAGE 0.4 sequence —
  same-line edits, different sections sharing a Progress-Log append anchor, and fully independent edits) confirmed
  quickmerge's `git pull --rebase --autostash` conflict detection is NOT defective: git correctly raises a rebase
  CONFLICT whenever two commits' diffs genuinely overlap (including the shared-append-anchor case this incident's
  hypothesis suspected might slip through), and cleanly preserves BOTH sides when edits are genuinely independent. The
  live incident's actual mechanism was different: the clobbering commit's diff is provably built ON TOP OF the earlier
  commit's own output (same blob hash chain — no rebase involved at all), and its author's edit REPLACED the earlier
  author's already-present checkbox annotation + Progress Log entry instead of appending alongside it. That is a
  content-discipline gap invisible to git/quickmerge — a fully valid, non-conflicting sequential commit by git's own
  rules. Before replacing a checkbox/Progress-Log entry in a shared doc, check whether it already carries content from
  another author/session — if so, APPEND your entry rather than overwriting theirs, even when your own investigation
  reaches a similar or better conclusion.
- **The guardrail-blocked command list is knowable in advance — don't discover it by trial.**
  `agent-orchestrator/scripts/hooks/block_destructive_commands.py` hard-blocks (exit 2, every time, no exceptions for an
  autonomous worker) a fixed set of irreversible patterns: `git stash drop/clear`, `git reset --hard`,
  `git push --force`, `git clean -f/-d/-x`, `git branch -D`, `rm -rf`/`find -delete`, any `gsutil`/`gcloud storage`/
  `aws s3` delete verb, `dd of=`, `chmod`/`chown -R`, disk-wipe utilities (full list + rationale in that file). If your
  plan seems to call for one of these, that IS the signal to use the sanctioned alternative — GCS/S3 deletes go through
  UTL's `gcs_delete_object()`, never a subprocess CLI call; an unwanted stash gets inspected or escalated via a
  blocked-question — rather than attempting the blocked form and burning a turn on the recovery.

---

## 2. The ship loop — what the server verifies

The generic discipline (named-file staging, conventional commits, quickmerge two-pass, QG-as-merge-prerequisite,
Commit+Push+**Flip** in the same turn) is in the auto-loaded CLAUDE.md. What's **worker-specific** is the loop the
orchestrator server actually checks on `/done`:

**Boot rebase**: as your first git act after `/boot`, fetch + rebase **every repo your task touches** against
`origin/live-defi-rollout`. Stale base ➜ silent merge conflicts later.

**Cross-repo flip (the PM-integration default).** Most tasks are cross-repo: code lives in a service repo,
plan-of-record in `unified-trading-pm/plans/active/<X>.md`. From `.tabs/<your-slot>/<service>/` you can't touch the plan
via the service repo — it's a sibling git tree at `.tabs/<your-slot>/unified-trading-pm/`. Two commits, two pushes,
**same agent turn** (`$SLOT` / `$SERVICE_REPO` come from your boot message):

```bash
# 1) Ship the code in your service-repo worktree (ship path per CLAUDE.md —
#    quickmerge two-pass for code; raw push only for the ff-pull-in + this flip).
cd "${WORKSPACE_ROOT}/.tabs/${SLOT}/${SERVICE_REPO}"
git add <your-files>
# Pre-stamp the Quickmerge trailer NOW, in the original commit — quickmerge.sh's Stage 5
# only late-amends it in when missing, and that amend re-triggers the check-branch-drift
# pre-commit hook AFTER Pass-1 QG has already run, which reliably loses the final push race
# under high branch churn (quickmerge_stage5_push_loses_fast_forward_race_under_high_churn_2026_07_27.md).
git commit -m "feat(...): your work

Quickmerge: agent"
SHA_CODE=$(git rev-parse --short HEAD)
# ...ship via quickmerge --agent --files <your-files> (see CLAUDE.md Git discipline)

# 2) IMMEDIATELY (same agent turn) flip the plan in the PM worktree
cd "${WORKSPACE_ROOT}/.tabs/${SLOT}/unified-trading-pm"
# edit plans/active/<X>.md to flip your checkbox → - [x] ✅ … — ${SERVICE_REPO}@${SHA_CODE}
git add plans/active/<X>.md
git commit -m "docs(plans): flip item N (${SERVICE_REPO}@${SHA_CODE})"
git push origin HEAD:live-defi-rollout

# 3) Call /done with SHA_CODE
```

**Verify — never trust quickmerge's own "✅ Landed" message alone (2026-07-31,
`quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`).** A sentinel-invalid retry/re-gate can, on a
high-churn shared branch, land the branch on a ref that no longer contains your commit while still printing "Landed" —
reflog-recoverable, but silently lost if you don't check. Before calling `/done`, confirm your SHA is actually on
origin:

```bash
git fetch origin live-defi-rollout --quiet && git merge-base --is-ancestor "$SHA_CODE" origin/live-defi-rollout \
  && echo "✅ verified on origin" || echo "❌ NOT on origin — see recovery below"
```

On failure: `git reflog` to find your dangling commit (it survives there even though the branch tip no longer has it),
`git merge --ff-only <sha>` (or rebase your branch back onto it if origin has since moved further), re-run the
Pass-1/Pass-2 ship flow, and re-verify before retrying `/done`. `quickmerge.sh` itself now also self-checks this exact
condition in STAGE 5 (a `refs/wip-preserve/quickmerge-stage5-regate-<sha12>` ref + a hard failure instead of a silent
push if it detects the loss) — this manual check is the belt to that suspenders, since the STAGE 5 guard only covers the
specific mechanism it was built to catch, not every way a shared branch could theoretically move.

**Ordering note**: commit BEFORE running `quality-gates.sh` (as the snippet above already shows) — the QG sentinel is
keyed to HEAD at the moment it's written, so QG-before-commit moves HEAD past the sentinel and forces an avoidable
re-run on the very next quickmerge call. See `worker.md`'s Pass-1/Pass-2 section for the full rationale
(`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`).

**Server M3 verification** (codified 2026-05-18 re-review — DOES verify cross-repo flips): after `/done`, the server
walks the sibling PM worktree at `.tabs/<your-slot>/unified-trading-pm/` and runs
`git log --since="10 minutes ago" -- <plan_ref>`. Found → M3 satisfied (`reason: "cross_repo_pm_flip_verified"` +
`pm_flip_sha`). Clean PM log → fires `slot_done_no_plan_flip` (`reason: "cross_repo_pm_log_clean"`) — that IS a
violation; don't skip step 2.

**Single-repo case**: code + flip in the same repo → either bundle them in one commit
(`feat(...): X — flip plan item Y`) or a separate `docs(plans):` commit in the next Bash call, same turn. Server sees
the flip in the verification window either way.

**Enforcement**: `slot_done_no_plan_flip` when the check IS applicable and neither pattern fired. ≥3 in 4 h from one
slot escalates to `slot_dual_flip_pattern_violation` — the review agent chats main about you.

**Never combine the checkbox flip with a `git mv` archival in ONE commit (2026-07-30 incident; SSOT
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — cite that doc, not this one, from plans).** If a
todo's own completion also makes its doc archival-eligible (all todos done, no lock), a single commit that both edits
the checkbox AND `git mv`s the file to `plans/archive/...` makes the diff AT THE ORIGINAL `plan_ref` PATH show only a
file deletion — no `[ ] → [x]` transition is visible there (git's rename pairing isn't applied when a path-scoped
`git show`/`git log` query is run against just the old path), so `/done`'s M3 check (`cross_repo_pm_flip_verified`)
rejects it with `cross_repo_pm_file_touched_no_checkbox_flip` even though the flip genuinely happened. Fix: commit the
flip FIRST as a plain edit at the still-active path, THEN `git mv` to the archive location as a separate follow-up
commit.

**Pre-shutdown self-check** before you walk away:

```bash
git rev-list --count HEAD ^origin/live-defi-rollout    # must be 0
```

---

## 3. Sub-agent (Task tool) spawning

If you spawn a sub-agent via the `Task` tool, paste the FULL content of `SUB_AGENT_MANDATORY_RULES.md` at the TOP of the
sub-agent's prompt. Sub-agents don't inherit your context; without the rules they will use `pip`, define types as `Any`,
and skip QG.

```bash
# relative to your slot repo-worktree root — unified-trading-pm is a sibling in the slot:
RULES=$(cat ../unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md)
# then prepend RULES to your Task() prompt
```

---

## 4. Backlog-edit hygiene (main agent + operator)

> Backlog tasks **auto-derive** from `- [ ]` checkboxes in `plans/active/*.md` via `server/regen_backlog_from_plan.py` —
> never hand-add tasks to `backlog.yaml` (write the todo in the plan; the next `PlanRegenLoop` tick or
> `POST /api/backlog/regen` pulls it in). The fields below only **tune** already derived tasks.
> `POST /api/backlog/reload` is **add-only** — it inserts new rows but never deletes tasks that vanish from YAML.

### Slot affinity — bind tasks to specific slots

```yaml
- id: TASK-X
  title: "..."
  target_slot: 8 # int | null. Which slot this task is "for". null = any.
  affinity: high # none | low | medium | high. How strictly to honour target_slot.
  target_slot_timeout_seconds: 600 # only used when affinity = medium
```

| Level    | Dispatcher behaviour                                                                                         | When to use                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `none`   | Ignore `target_slot`. Any slot can claim. Default; back-compat.                                              | Generic tasks like the cleanup batch.                                                       |
| `low`    | Prefer `target_slot` if it's free right now. Else any slot can take it.                                      | "Slot 8 is best (already has the touched files) but don't block."                           |
| `medium` | Wait up to `target_slot_timeout_seconds` (default 600) for `target_slot`. After that, fall back to any slot. | "I'd prefer slot 8 because it has context but don't block the queue if it's stuck >10 min." |
| `high`   | Only `target_slot` can claim. Other slots skip past indefinitely.                                            | "This MUST be slot 8 — only it has the right account credentials / repo state / context."   |

The Reassign endpoint defaults to `target_slot=<self>, affinity=high` — so clicking Reassign on slot N's card binds the
released task back to slot N automatically. Override via the endpoint body when you need different routing.

### Park a task (keep it but defer dispatch)

Parking TUNES an already-derived entry — you never author a new one. On the task's existing entry in
`data/config/backlog.yaml`, set:

```yaml
priority: 999 # pushes to back of queue
priority_override: true # REQUIRED alongside priority: — else the next regen tick reverts it to the plan-derived value
prereqs:
  prerequisites:
    - utl-base-dependency-checker-migrated # create it false via POST /api/prerequisites/<name> first
```

Reload (`POST /api/backlog/reload`). The task stays at `priority: 999` (effectively never dispatched while
higher-priority work exists) AND the false condition gates it as a second safety. To unpark: flip the condition GREEN
(`POST /api/prerequisites/<name>` `{value: true}`) + lower the priority + clear `priority_override`.

**Verify it actually stuck**: this exact recipe was silently reverted by every regen tick before
`agent-orchestrator@8dd5763` fixed it (`backlog_regen_drops_handtuned_prereqs_2026_07_12.md`). Re-check the entry in
`data/config/backlog.yaml` after the next `PlanRegenLoop` tick or `POST /api/backlog/regen` (not just `/reload`, which
doesn't exercise the revert path) — `priority` should still read `999` and `priority_override: true` should still be
present. If either reverted, that's a regression of the same bug class: file a fresh P0 issue doc immediately, don't
just re-apply the edit and move on.

### Delete a task (permanent removal)

```bash
curl -X DELETE $SERVER_URL/api/backlog/<task_id>
```

Removes the SQLite row AND scrubs the YAML entry so the next `/api/backlog/reload` doesn't reinsert it. Refuses if the
task is currently `dispatched` — `/skip-current-task` or `/reassign` the slot first. Emits a `backlog_task_deleted`
activity event for the audit trail.

### Adding new conditions mid-cycle

1. CREATE the condition via the API — `POST /api/prerequisites/<condition-name>` `{value: false, set_by: "main"}`. The
   endpoint UPSERTS (an unknown name is created on first POST); there is no separate `/api/conditions` surface, and no
   YAML edit is needed to bring a condition into existence.
2. ATTACH it to a task: add `prereqs.prerequisites: [<condition-name>]` (NOT `prereqs.conditions` — that field doesn't
   exist on `TaskPrereqs`; it's silently dropped by pydantic on every load, per
   `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` Defect A) on the task's entry in `data/config/backlog.yaml`,
   then `POST /api/backlog/reload`. This attachment is the ONE tuning that is still yaml-only — the regen does NOT yet
   derive per-task `prereqs.prerequisites` from plan todos (plan-level ordering comes from `depends_on` +
   `gate_on_depends` / `sequential` frontmatter instead), and `prereqs.prerequisites` round-trips normally (a real,
   declared schema field) so the regen preserves it with no special-casing needed.
3. Later: flip it GREEN via the same `POST /api/prerequisites/<condition-name>` `{value: true, set_by: "main"}`.

The dashboard's Conditions panel shows the toggle + `gates_queued` count. Reload is non-destructive — existing
conditions keep their value; only NEW ones seed.

---

## 5. Prerequisites vs blocked-questions — do NOT conflate them

Two very different mechanisms exist. Conflating them is the most common agent mistake:

**Prerequisite / dependency** (`task.prereqs.completed_tasks` / `task.prereqs.prerequisites`): A task gated by EARLIER
tasks (e.g. tasks 6–10 need tasks 1–5 done) is a **prerequisite** — the dispatcher handles it automatically. The gated
task stays `status=queued` and the dispatcher simply won't pick it until the prereqs are met (all listed
`completed_tasks` must be `done`; all listed `prerequisites` must be `true`). **DO NOT** post a blocked-question asking
"can I start on task 7 before task 5 is done?" — just wait. The server gates it for you.

**Blocked-question** (`POST /api/slots/<N>/blocked`): A genuine judgment call where YOU need a human or the main agent
to decide SOMETHING before you can continue — NOT just "I'm waiting for an earlier task". Use this only when you've hit
an actual decision point (a conflict where both sides are plausible, an operator-only auth action, an ambiguous spec).
The main agent or operator reads your question + options + recommendation and answers in the dashboard.

**Rule**: if your task has `prereqs.completed_tasks: [foo-001]` and `foo-001` is not `done` yet, DO NOT post a
blocked-question — you simply aren't scheduled yet. Ask yourself: "is this a waiting-for-a-dependency situation, or a
genuine decision I can't make alone?" If the former, let the dispatcher handle it.

**A permission/IAM error is NOT a blocked-question either (2026-07-27, operator ruling).** Hit `PERMISSION_DENIED`
acting AS `unified-trading-sa` (GCP) or `uts-orchestrator-epic-role` (AWS) — the two identities every worker already
runs as ambiently, no separate credential needed? **Grant the missing role yourself right now (least-privilege — the
specific role that closes the specific gap, never blanket `Owner`/`AdministratorAccess`), verify the actual capability
live (call the real API, don't just read the IAM policy back), and continue the task** — do not post a blocked-question,
do not tag the plan todo `[OPERATOR]`, do not just report the gap and stop. Reserve a real blocked-question for a
permission gap on a genuinely DIFFERENT identity you cannot assume (`github-actions-deploy`, a human's personal account,
a credential that doesn't exist yet). Current grants + exact per-cloud commands:
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`. (Verified 2026-07-27: a worker given only a
diagnostic-sounding task — "check whether X can list Y, report what you find" — read that phrasing as observation-only
and stopped at reporting the gap instead of fixing it, even with this rule in context; a worker given an outcome-framed
task — "produce a report of Y" — self-granted and continued, per this rule, without prompting. If a task's OWN wording
sounds like "just check", the underlying goal still governs: fix the gap, then answer the actual question.)

---

## 6. Orchestrator HTTP surface — what you do NOT do anymore

The old file-based orchestration (LEDGER.md row patches, ping-file polls, manual main-agent dispatch) is REPLACED by
HTTP endpoints. As a worker:

- **You do NOT read or write `unified-trading-pm/harsh_orchestrator/LEDGER.md`.** Your status lives in SQLite via
  `/api/slots/<N>/progress` calls.
- **You do NOT update `unified-trading-pm/harsh_orchestrator/pings/slot_<N>.md`.** Use `/api/slots/<N>/progress` with a
  one-line `message` instead.
- **You do NOT poll `unified-trading-pm/plans/active/_agent_pings.md`** for cross-side coordination unless main agent
  specifically asks. The operator's cross-side surface is now the dashboard's agent chat.

Your full lifecycle is in `unified-trading-pm/agents/worker.md`. The activity events you might trigger
(`slot_done_verified`, `slot_done_no_plan_flip`, etc.) are documented in `dashboard/API_REFERENCE.md`
(agent-orchestrator repo).

---

## 7. Everything else → auto-loaded CLAUDE.md (don't re-read preemptively)

These rules are already in your context via the repo's `.claude/CLAUDE.md` symlink — find them there, don't expect them
restated here:

- **The 8 code rules** (uv·UnifiedCloudConfig·setup_events·tempfile·resolve_bucket_name·UTC·builtin-generics·
  no-fallback-imports) → CLAUDE.md § "Writing code → coding standards".
- **Quality gates** (`scripts/quality-gates.sh` is the entrypoint; never run pytest/ruff/basedpyright standalone;
  file/function/coverage limits) → CLAUDE.md § "Environment + how to run quality gates".
- **Git discipline** (named-file staging, conventional commits, quickmerge two-pass, CI verification) → CLAUDE.md § "Git
  discipline + shipping pipeline" + § "CI verification after every push".
- **Findings triage** + "pre-existing is not a triage criterion" + capture discoveries as plan todos → CLAUDE.md §
  "Governance + safety HARD RULES".

Deeper SSOTs (read on demand only if your task brief points at one):

- **Service-architecture rules**: `codex/04-architecture/`
- **Data + manifest rules**: `codex/02-data/`
- **Coding standards** (basedpyright config, QG steps): `codex/06-coding-standards/`
- **Per-slot worktrees (Path-B)**: `codex/05-infrastructure/per-tab-worktrees.md`
