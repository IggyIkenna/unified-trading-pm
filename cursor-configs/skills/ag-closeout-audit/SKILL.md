---
name: ag-closeout-audit
description: >-
  Audit one asset-group's plan/issue corpus in unified-trading-pm to answer "if the AG's consolidated-closeout plan's
  own todos AND every currently-active AO-dispatch-batch (+ finalize) plan for this AG all run to completion, how many
  plan/issue docs are left orphaned — real remaining open work nothing currently active/dispatched actually covers —
  excluding genuinely cross-cutting (multi-AG) docs?" Classifies every AG-primary doc via a per-doc read (not checkbox
  count — this corpus has confirmed traps: prose-only remaining work, dated RE-TRIAGE sections overriding earlier
  checkmarks). Then, for orphaned docs carrying genuine AO-eligible bounded-outcome work, drafts (status: draft, never
  auto-shipped) the next `<ag>_satellite_ao_dispatch_batchN_<date>.md` + gated `batchN_finalize` plan pair, mirroring
  the pattern built for sports (`sports_satellite_ao_dispatch_batch2_2026_07_24.md` +
  `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`). Parameterized by topic tranche — invoke as
  `/ag-closeout-audit <tranche>` across all 10: `cefi`, `defi`, `tradfi`, `prediction`, `sports`, `cross-cutting`, `ao`,
  `ci`, `infra`, `ui`. **`all` is a valid tranche and the DEFAULT when invoked with no argument** (e.g. a scheduled AO
  trigger) — runs every tranche's audit and aggregates one combined report, so a no-arg scheduled invocation never fails
  for lack of a tranche name. Trigger on `/ag-closeout-audit [<tranche>]`, "run the sports treatment for <tranche>",
  "audit <tranche> orphans", "how many <tranche> docs would be orphaned if we finished the consolidated plan",
  "<tranche> closeout completeness check", "audit everything"/"run the full closeout audit" (→ `all`).
---

# /ag-closeout-audit — per-AG closeout completeness projection + next-batch drafting

Generalizes the sports-corpus closeout arc built 2026-07-24/25 (triage → `sports_satellite_ao_dispatch_batch2` →
`sports_satellite_ao_dispatch_batch2_finalize` → the orphan-projection audit) into a repeatable, AG-parameterized
procedure. As of 2026-07-25 all 5 AGs (cefi/defi/tradfi/prediction/sports) have been through this treatment at least
once AND through a follow-on consolidated-plan line-cap split (parent trimmed to ~450-750L, forked into
Track/phase-named AO-dispatch children per `task_template.md` findings I/R) — this skill's Phase 0.2 (below) discovers
BOTH doc classes. As of 2026-07-25 a full 9-way topic partition existed: the 5 AGs, `cross-cutting` (data-pipeline
concerns spanning IS→features-service→data-status-UI→manifest/GCS-path→UAC→UTL that aren't specific to any one AG,
`cross_cutting_consolidated_closeout_2026_07_25.md`), `ao` (agent-orchestrator dispatch/worker-lifecycle,
`ao_consolidated_closeout_2026_07_25.md`), `ci` (CI/CD pipeline mechanics, `ci_consolidated_closeout_2026_07_25.md`),
and `infra` (generic repo/dependency/terraform/org hygiene, `infra_consolidated_closeout_2026_07_25.md`) — built the
same day from a corpus-wide classification pass so this AG↔topic partition covers the WHOLE plans/issues corpus with
zero unaccounted docs. **A 10th tranche, `ui`, was added 2026-07-30** (deployment-ui/deployment-api/
unified-trading-system-ui closeout — deploy/launch consoles, data-status UI, cost/VM/alerts observability surfaces,
`ui_consolidated_closeout_2026_07_30.md`) — operator finding: this UI-specific work had been sitting split across the
`deployment_and_user_management_master` EPIC (never audited by this skill — epics live in `plans/epics/`, outside Phase
0's `plans/active/<ag>_consolidated_closeout_*.md` discovery pattern, and epics aren't part of the asset_group partition
at all) and various `infrastructure`/`cross-cutting`-tagged plans, with no dedicated tranche of its own.

## The 10 tranches + `all` default — classification mechanism differs by tranche

**5 AGs (`cefi`/`defi`/`tradfi`/`prediction`/`sports`)**: membership is `asset_group` frontmatter — a doc's
`asset_group` list containing exactly that AG name is ground truth (subject to the Orthogonality HARD CHECK below).

**`cross-cutting`**: membership is `asset_group` containing `cross-cutting` AND `parent_epic` in one of the 5
data-relevant epics this doc was scoped from (`infrastructure_master`'s data-relevant subset, `instruments_master`,
`mtds_mdps_master`, `manifest_master`, `features_and_ml_master`) OR explicit membership in one of Tracks 16-24 (docs
epic-scoped elsewhere but reclassified in by content — see that doc's own Progress Log). **The two paths are a UNION,
not a fallback chain**: the epic filter alone misses docs that entered the closeout via the corpus-wide sweep (Tracks
16-24), so membership derivation MUST always union both sources — see the 2026-07-26 audit's Progress Log entry in the
closeout doc for the measured consequences of using epic-filter-only.

**`ao`/`ci`/`infra`**: **`ao`, `ci`, and `infrastructure` are now real dedicated `asset_group` enum values** (added
2026-07-27, `unified-trading-pm@a97bc7bed` — `docspec.py`/`PLAN_FORMAT.md`/`doc-frontmatter-schema.md` §5, now 10
values: `cefi · defi · tradfi · sports · prediction · cross-cutting · ao · ci · infrastructure · meta`). The
2026-07-25→27 workaround this section used to describe (no dedicated value, ground-truth only via each tranche's Sources
list) is RETIRED — a 2026-07-27 corpus-wide retag pass
(`/plans/archive/2026_07/asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`) mechanically re-derived membership
from all 4 non-AG tranches' closeout Sources lists and applied it to the frontmatter directly: 119 docs retagged
(`asset_group: [cross-cutting]` → `[ao]`/`[ci]`/`[infrastructure]` as appropriate), verified via
`check_ag_closeout_linkage.py` (0 orphans) and a re-run of the citation pre-filter (cross-cutting's never-cited rate
dropped 92.5% → 3%). **`asset_group` containing `ao`/`ci`/`infrastructure` is now the PRIMARY membership signal for
these 3 tranches** — use it exactly like the 5 real AGs (subject to the same Orthogonality HARD CHECK below).
`parent_epic` (`ao` ≈ `orchestrator_master` + `agent_operating_framework_master`; `ci`/`infra` split the
CI/CD-vs-generic content inside `infrastructure_master` + `deployment_and_user_management_master` + `strategy_master` +
`plan_hygiene_master`) is now only a secondary hint for docs the tag doesn't yet cover — still relevant because the
retag pass only covered docs that were bare-tagged `cross-cutting` at the time; a NEW doc authored after 2026-07-27 with
a habitually-typed `cross-cutting` tag (old muscle memory) or a blank/mistagged `asset_group` needs the same
content-judgment fallback the old workaround used: read that tranche's own consolidated-closeout doc's Track/Sources
lists, or read the doc itself, before concluding it's out of scope. **Still do not fully trust `asset_group` alone
without a linkage check** — `check_ag_closeout_linkage.py` is the safety net for any doc the tag and the Sources lists
disagree about. **Read that gate's real coverage before relying on it (corrected 2026-07-31)**: it used to enforce only
the 5 original AGs — a hand-listed `REAL_AGS` that never got the 2026-07-27 `ao`/`ci`/`infrastructure` expansion, plus a
filename-prefix bug that silently matched zero closeout docs for `cross-cutting` and `infrastructure` — so it reported a
comfortable "0 orphans" while checking nothing at all for 5 of 10 tranches. A 2026-07-30 attempt to fix this was
recorded as DONE in `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` but never actually shipped
(`git log --follow` on the script showed only its original 2026-07-25 commit); this line went stale for a day as a
result. It now genuinely derives its covered set from docspec's live `ASSET_GROUP` enum minus `meta`, searches BOTH
`plans/active` and `plans/archive` for each tranche's closeout family (closing the `ao`/`ci` gap for real — both are
archived-only and now resolve non-empty, 11/44 and 11/38 enforced respectively), and reports any tranche with no
discoverable closeout family LOUDLY instead of skipping it in silence. Baseline re-seeded 32 → 69 at the honest measured
count. Track: `/plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`,
`/plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md` (resolved, see below) — repointed
2026-08-06 (/plan-reconcile ao).

**`ui`**: **`ui` is a real dedicated `asset_group` enum value from the day it was added** (2026-07-30,
`unified-trading-pm@<sha-this-session>` — `docspec.py`/`PLAN_FORMAT.md`/`doc-frontmatter-schema.md` §5, now 11 values:
`cefi · defi · tradfi · sports · prediction · cross-cutting · ao · ci · infrastructure · ui · meta`) — there is no
pre-2026-07-30 "workaround" period to describe, unlike `ao`/`ci`/`infrastructure`'s 2026-07-25→27 transition. Scope:
`deployment-ui`, `deployment-api`, `unified-trading-system-ui` — deploy/launch consoles, data-status honest-coverage
surface, cost/VM/artifact/alerts observability, promote endpoints, auth flow (the same repo scope
`deployment_and_user_management_master.md`'s epic already declares). `parent_epic` is a secondary hint, same caveat as
`ao`/`ci`/`infra` — most `ui`-tagged docs carry `parent_epic: deployment_and_user_management_master` or
`observability_master`, but a doc's `asset_group` tag is the primary signal, not its epic. **A corpus-wide retag pass
(mirroring the 2026-07-27 `asset_group_ao_ci_infra_schema_expansion` migration) is still owed** — only the bounded set
of docs discovered + retagged when `ui_consolidated_closeout_2026_07_30.md` was authored are tagged so far; a doc
authored before 2026-07-30 that's genuinely UI-scoped but still reads `infrastructure`/`cross-cutting` needs the same
content-judgment fallback (read the doc, don't trust the tag alone) until that migration runs — see
`ui_consolidated_closeout_2026_07_30.md`'s own todos for the tracked follow-up.

**`all` (the default with no argument)**: run the audit for all 10 tranches (parallel Agent dispatch, one per tranche,
is the efficient path given the scale — see Phase 1) and aggregate one combined report: total orphan count per tranche,
any genuine new mistags found (feed back into the Orthogonality HARD CHECK below), and per-tranche next-batch
recommendations. **This is the mode a scheduled/cron AO invocation with no explicit tranche argument should resolve to —
never fail or block asking "which tranche?"**.

**Total-coverage gap, fixed 2026-07-26, partially superseded 2026-07-27**: this 9-tranche partition's stated value is
total coverage of the plans/issues corpus, but `plans/PLAN_FORMAT.md:88` also declares `infrastructure` and `meta` as
valid `asset_group` values — the 9 tranches above originally only ever swept `cross-cutting` (+ the 5 AGs), so docs
tagged `asset_group: infrastructure` or `asset_group: meta` were invisible to every tranche's membership rule regardless
of `all` mode (measured: ~48 unlisted docs at the time). **`asset_group: infrastructure` is now a NON-issue** —
`infrastructure` IS the `infra` tranche's real enum value as of 2026-07-27 (see the classification-mechanism section
above), so Phase 0.3's standard inventory step already sweeps it directly; no separate fold-in sweep needed anymore.
**`asset_group: meta` remains the one genuine gap** — `meta` has no dedicated tranche of its own (it was, and still is,
a deliberately generic "spans everything / process-level" marker) — `all` mode (and any single-tranche run) MUST still
sweep `asset_group: meta` and fold genuine hits into whichever of `ci`/`infra`/`ao`/`cross-cutting` its content actually
matches. `check_ag_closeout_linkage.py` does not catch this class either; **the original ~48-doc delta was NOT touched
by the 2026-07-27 retag** (that pass's population was bare-`[cross-cutting]` docs specifically — a doc already tagged
`infrastructure`/`meta` was never in scope for it) — re-measured 2026-07-27: 59 docs carry `asset_group: infrastructure`
and 65 carry `asset_group: meta` corpus-wide right now, still a real, still-open population. The corpus-wide triage was
tracked in `/plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md` — repointed + updated
2026-08-06 (/plan-reconcile ao): that doc is now `status: resolved`, 4/4 todos done, and archived (was stale here as
`active`/2/4-done).

**This skill answers a forward-looking completeness question — it is NOT `/plan-reconcile`.** `/plan-reconcile` fixes
what's already provably done (false-unchecked flips, contradiction resolution, archival) across the WHOLE corpus (or, as
of 2026-07-25, a single topic-scoped shard of it — see `/plan-reconcile`'s own SKILL.md). This skill projects forward
("if everything currently active/dispatched for this ONE tranche finishes, what's still stuck?") and, where warranted,
drafts the next AO-dispatch batch to close the gap. Run `/plan-reconcile` first if the corpus might have
stale/false-unchecked state — this skill's classification is only as good as the frontmatter `status` it reads.

**Also NOT `/na-eligibility-audit` — but an `assigned_vm: NA` doc is NOT categorically excluded from orphan-eligibility
here (RULED 2026-07-30, correcting this section's prior wording).** The two skills are disjoint by QUESTION, not by
population. This skill asks "does any currently-active covering plan actually claim this doc's remaining work?";
`/na-eligibility-audit` asks "is this doc's own `NA` self-classification still correct?". **An NA doc's
self-classification correctness is out of scope here** — never reclassify one from this skill, never verdict its
NA-ness, just report whether anything covers it.

The prior wording ("an `assigned_vm: NA` doc is by definition NOT orphaned — it has an owner: itself") was WRONG, and it
contradicted the shipped tooling. **Tooling wins — `generate_ag_closeout_audit_candidates.py` is the definition.** That
script treats a doc as covering itself only when it is SELF-DISPATCHED: `assigned_vm == "planning"` AND `status` ∈
`{active, open}` (its `self_dispatched` flag). `assigned_vm: NA` is precisely the case where the doc is NOT its own
dispatch vehicle — nothing will pick it up — which is exactly the orphan signal this skill exists to raise. Reading the
old prose literally excludes every NA doc from the candidate set; that swung one tranche's orphan count by 19 docs on
2026-07-30. An NA doc reported orphaned here is an accurate "no active plan covers this" finding: report it, and let
`/na-eligibility-audit` separately decide, on its own schedule, whether NA was the right classification to begin with.

## Why `batchN` exists as a SIBLING doc, not content folded into the consolidated closeout plan

Two independent reasons, both real, neither alone sufficient:

1. **The coverage gap (the actual root cause).** Every `<ag>_consolidated_closeout_*.md` carries a section (something
   like "Aggregated source docs — referenced, not duplicated") that just LISTS/links every satellite doc in the AG for
   discoverability. That section is explicitly a **digest, not real dispatch** — a satellite doc being linked there
   means nothing is actually working its specific open items. `batchN` extracts AO-eligible items DIRECTLY OUT OF the
   satellite docs themselves (never out of the consolidated doc's own content) to close that gap. This is why the
   conflict-check (Phase 3) matters: it's reconciling two independent claims on the same ground, not splitting one doc's
   content into two files.
2. **The line-cap constraint (a real, independent, reinforcing reason).** Even where a satellite doc's items COULD in
   principle be pasted into the consolidated doc's own todo list, the corpus scale makes that structurally impossible: a
   single AG's triage routinely finds 40-60 AO-eligible candidates (defi batch1 alone shipped 54), and consolidated
   closeout docs are already substantial. Inlining that volume would breach the workspace's 1000-line hard cap
   (`check_line_caps.sh`, no exceptions) on the FIRST batch, let alone across batch2/3/N. So even in a hypothetical
   world with no coverage-gap problem at all, extraction into sibling docs would still be the only viable shape.

## The `batchN` methodology — an iterative drain, not a one-shot

`batch1` is never expected to close an AG's orphan backlog in one pass — it extracts only what's conflict-clear TODAY.
Everything else lands in that batch's own `## Deferred` section, tagged by WHY it was held back (see taxonomy below).
Re-invoking this skill for the same AG (producing `batch2`, `batch3`, ...) is how the backlog drains over time:

1. **Before fresh Phase-1 triage, re-check the PRIOR batch's own Deferred section first.** Every conflict-gated item
   there names the specific competing claim it collided with (a consolidated-plan todo, another satellite doc's own
   item). Check whether that competing claim has since shipped, superseded, or otherwise resolved — if so, the conflict
   clears WITHOUT needing a fresh triage agent, and the item can move straight into the new batch's Todos. This is cheap
   (a few greps + reads) and should always run first; it's frequently how a doc that was 100%-blocked in batch1 becomes
   dispatchable in batch2 with zero new investigation.
2. **Only then run a fresh Phase-1/Phase-3 pass** over whatever's left — either the same still-unresolved conflicts (if
   nothing changed) or entirely new orphans that appeared since the last audit (new docs, new findings).
3. **Stop iterating on an AG once every remaining orphaned doc's open work is PURELY from the non-batchable taxonomy
   below** (no more conflict-gated items convertible by re-triage) — at that point, report the residual count to the
   operator as "needs direct human action, not another batch" rather than continuing to spin batches that can't possibly
   extract anything new.

## The non-batchable taxonomy — why some Deferred items will NEVER become a `batchN` todo

Not everything in a Deferred section is the same KIND of blocked. Distinguishing these matters because only one category
resolves through re-triage — the others need direct operator/human action, and re-running this skill against them wastes
a cycle:

- **Conflict-gated (re-triageable — the ONLY category batch2+ can convert).** A genuine but resolvable collision with
  another doc's own claim on the same ground. Clears when the competing side ships, is superseded, or a dated section
  proves one claim stale. This is what step 1 above re-checks every iteration.
- **Operator-gated.** An undecided design/judgment call, a two-option fork with no evidence-based tiebreaker, or an
  explicit sign-off requirement (prod-bucket deletes, a credential ask, a schema/canonical-set change with blast-radius
  the dispatch-scope rule excludes). No amount of re-triage resolves this — it needs the operator to actually rule, same
  as any entry in `autonomous_session_operator_decisions_<date>.md`. Once ruled, it becomes a normal batch candidate
  (see the Kamino/Solend precedent, 2026-07-25: queued, operator ruled, folded into `defi_satellite_ao_dispatch_batch1`
  directly rather than waiting for a batch2) — **but "operator-ruled" and "worker-determinable" are two separate tests,
  not one** (added 2026-08-10, from the `ui` tranche's 2026-08-08 Finding 4): a ruled item still has to pass the
  ordinary bounded-outcome check before it is drafted into a batch. A ruling that says "yes, do this eventually" on an
  otherwise open-ended design task does not make it dispatchable.
  - **Apply `task_template.md` finding U's POSITIVE test before parking anything here — do not inherit the source doc's
    own `[OPERATOR]` tag** (added 2026-08-10; finding U, operator ruling 2026-07-27, exists precisely because a 65-doc
    audit found dozens of reflexive `[OPERATOR]` tags on work that was clear-scope and read-only or
    reversibility-qualifiable). Park as operator-gated ONLY for: **(i)** a business/spend/value judgment with no
    data-derivable answer (activate a paid tier, accept a compliance risk) — a _standing_ ruling already on record is
    not a live gate; **(ii)** work structurally requiring a credential/access only a human holds (tag it a
    credential-ask; once the credential exists the todo is dispatchable); **(iii)** a whole-bucket destroy or a target
    failing a fresh reversibility check (finding T). Everything else is NOT gated. In particular: **a read-only
    audit/census/diagnostic todo can never be operator-gated** regardless of subject; **"relaunch/resume a named
    launcher or VM" is not operator-gated** by itself (findings Q/T/U narrowed the finding-O VM-launch clause to genuine
    prior-approval-and-validation gaps — AO workers already drive the `DP-VM-*` launchers routinely); and a **named-doc,
    named-field retag / stale-claim fix / checkbox reconciliation is never operator-gated** — that is mechanical corpus
    hygiene, see the in-run rule below.
- **Time-gated.** Work that depends on elapsed real time (an accrual/backfill window not yet reached, a pending external
  event, a cron cadence that hasn't fired enough cycles to have data yet). Re-triage will keep finding the same "not
  yet" until the clock actually passes — track it, don't keep re-surfacing it every batch cycle.
- **Too-large-or-risky-for-a-batch-todo.** A doc that's itself a live, fast-moving, multi-phase migration (dated DELTA
  sections superseding each other within the same file, an actively-draining VM-backed process) — folding even its
  cleanest-looking candidate into a batch risks colliding with its own in-flight state. Needs its own dedicated
  triage/design pass as a standalone plan, not another `batchN` slot.
- **Genuinely human-only, permanently.** Design-conversation-needed work the source doc itself says needs "a dedicated
  engineering session with judgment," unbuilt safety tooling, or anything the dispatch-scope eligibility rule excludes
  outright. These docs will keep reporting `orphaned_*` from Phase 1 forever unless a human directly does the work —
  that's an accurate signal, not a stuck audit.

## Modes

- **Interactive (default, operator present)**: report the audit results directly in chat; if Phase 3 drafts new
  batch/finalize plans, present them for review before shipping — **never quickmerge a newly-drafted AO batch plan
  without explicit operator confirmation** (CLAUDE.md § "Plan destination — ASK BEFORE CREATING" HARD RULE — this
  applies to a skill-drafted plan exactly as it applies to a hand-authored one).
- **Autonomous / AO-dispatched**: run Phases 0-2 (audit + report) freely — read-only, no ruling needed. Phase 3
  (drafting a new batch/finalize pair) is a `status: draft` doc creation, which is safe to do autonomously (drafts are
  not ingested/dispatched), but flipping it to `status: active` to actually dispatch it is an operator decision — park
  it as a normal `- [ ]` follow-up item, never auto-flip.

## Running as one of N concurrent sharded tranche workers — two HARD safety rules (added 2026-07-30)

The scheduled shape of this skill is NOT one worker sweeping 10 tranches — it is up to 9-10 workers, ONE PER TRANCHE,
dispatched concurrently onto separate slots by `ag-closeout-auditor.timer`
(`agent-orchestrator/scripts/install-ag-closeout-auditor-timer.sh`). Two failure classes exist only in that shape, and
both bit on 2026-07-30:

**1. A doc that legitimately spans multiple tranches has exactly ONE owning tranche — derive it from `parent_epic`.**
Stated once, not twice: `cursor-configs/skills/na-eligibility-audit/SKILL.md` § "Primary-owner rule for multi-tranche
docs" is the rule, and `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 2 (`parent_epic`,
not `asset_group`, is the clean grouping axis) is the SSOT both skills defer to. This skill and `/na-eligibility-audit`
partition the SAME corpus by the SAME 10-way split, so they hit the SAME collision — measured on the NA corpus
2026-07-30: one doc appeared in 6 of 9 tranches, and up to 47% of a single tranche's docs appeared in 2+. Applied here:
a NON-owning tranche still classifies a shared doc and still reports its orphan verdict (that verdict is real and
belongs in that tranche's report), but any **write** to the shared doc itself — a linkage/`related:` fix, a retag, a
verdict marker — belongs to the OWNING tranche alone, so N workers never race the same file.

**2. NEVER `git stash` while running as one of several concurrent sharded tranche workers on a shared clone.**
`refs/stash` is a SINGLE shared LIFO stack per `.git` directory — it is **not** worktree-scoped, so worktree isolation
does not protect it (`/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT cover"). A
`stash push` in worker A followed by a `stash pop` in worker B pops **A's** entry, not B's. That exact push/pop race on
2026-07-30 swapped two workers' unrelated changesets. **If you need a pristine-tree comparison, use a throwaway second
worktree at HEAD instead** — `git worktree add <scratch-path> HEAD`, read it, `git worktree remove <scratch-path>`. The
same hazard applies to the `--autostash` flavours (`git pull --rebase --autostash` drives the same stack), so prefer an
explicit `git pull --ff-only` from an already-clean tree.

## Phase 0 — discover the AG's covering-plan set (cheap, no agents)

For the target `<ag>`:

1. **Consolidated closeout doc(s)**: `plans/active/<ag>_consolidated_closeout_*.md` (the master plan), plus any
   `<ag>_consolidated_closeout_aggregated_sources_*.md` (discoverability index — like the sports one, treat as
   NON-covering: being listed there is not dispatch) and `<ag>_consolidated_audit_*.md` (an earlier audit that may have
   spawned the closeout). Confirm these exist — if there is no `<ag>_consolidated_closeout_*.md` yet, stop and tell the
   operator this AG hasn't been consolidated at all (a different, prior gap than this skill addresses). **Naming
   exception for `<ag>=cross-cutting`**: filenames are snake*case, so substitute the underscore form, not the literal
   asset_group value — the doc is `cross_cutting_consolidated_closeout*_.md`(underscore between "cross" and "cutting"),
   NOT`cross-cutting*consolidated_closeout*_.md` (hyphen). Every other AG name has no internal separator so this
   exception never comes up for them.
2. **Existing AO-dispatch-batch + finalize pairs for this AG** — TWO discovery paths, UNION the results (added
   2026-07-25 after the 5-AG consolidated-plan split found the filename-only path alone misses a real class of covering
   plan). **NEITHER path filters on `assigned_vm`/`status` (widened 2026-07-25)** — a covering plan sitting
   `status: draft` / `assigned_vm: NA` still counts as covering, it just hasn't been AO-dispatched YET; the whole point
   of `/ag-closeout-audit` running BEFORE the mass-flip-to-planning is to confirm the not-yet-flipped plans already
   cover everything, so filtering discovery to `assigned_vm: planning` would make the audit blind to its own pre-flip
   candidates and wrongly report them as orphans needing a fresh draft. Record each covering plan's
   `status`/`assigned_vm` in the report (covered-and-dispatched vs covered-but-still-draft are both "not orphaned", but
   the operator needs to know which): a. **Filename-pattern path**: grep `plans/active/*.md` for docs (any
   `status`/`assigned_vm`) whose `asset_group` includes `<ag>` and whose filename matches
   `<ag>_*(ao_dispatch|satellite)*batch*` or similar — read each to confirm it's a batch-extraction plan (cites
   `Source: <doc>` per todo) and check whether it has a paired `depends_on: [<slug>] + gate_on_depends: true` finalize
   plan. b. **Dependency-graph path**: read `<ag>_consolidated_closeout_*.md`'s frontmatter `depends_on:` + `related:`
   (and its `_history_*`/`_native_ao_extract_*` siblings' own `depends_on:`/`related:`) and follow every listed slug
   regardless of its `assigned_vm`/`status` — this catches plans FORKED OUT of the consolidated closeout itself during a
   line-cap split (e.g. `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`,
   `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`), whose filenames describe their CONTENT (a Track/phase
   name), not the `ao_dispatch`/`satellite`/`batch` pattern — path (a) alone silently misses these, which would
   misclassify an already-covering, already-AO-readiness-scrubbed plan as an orphan needing a fresh draft. For BOTH
   paths: check whether each has a paired `depends_on: [<slug>] + gate_on_depends: true` finalize plan (per
   `task_template.md` §4's finalize-plan-coverage rule — cross-check with
   `.venv/bin/python scripts/quality_gates/check_finalize_plan_coverage.py --workspace-root <root>` if convenient). Also
   check `plans/archive/2026_*/` for already-archived batches of this AG (their coverage is DONE, not a gap).
3. **AG-primary doc inventory**: for the 5 real AGs + `cross-cutting` + `ao`/`ci`/`infrastructure`/`ui` (all 10 now have
   a real dedicated `asset_group` value as of 2026-07-30 — see the classification-mechanism section above), enumerate
   every `plans/active/*.md` and `plans/active/issues/*.md` whose frontmatter `asset_group` list contains `<ag>`
   (`infra` reads as `infrastructure` here, matching the enum). **Discovery MUST be a frontmatter-block-aware parse that
   strips YAML comments before tokenising — a single-line `rg '^asset_group:.*<ag>'` is NOT sufficient** (added
   2026-07-26, `issues/ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26.md`): a multi-line
   `asset_group:\n  [<ag>] # corrected ... -- was [<old-ag>], a genuine mistag`-shaped block (the orthogonality-retag
   convention this same skill's HARD CHECK below prescribes) defeats single-line grep entirely (the value sits on a
   continuation line, past the line-anchored colon), and it ALSO defeats a naive block-aware tokenizer that doesn't
   strip `#` comments first (the quoted old value reads as a live second tag, wrongly excluding the doc as a peer-AG
   candidate) — either failure drops the doc from the candidate set, the exact invisible-orphan class this phase exists
   to catch. Collapse continuation lines, strip every `#`-prefixed comment token, THEN tokenise the `asset_group` list.
   Same requirement applies to the membership greps quoted inside the closeout docs themselves — don't cite a bare
   `rg -l '^asset_group:.*<ag>'` count as a membership total without the same caveat. Cross-check against that tranche's
   own `<ag>_consolidated_closeout_2026_07_25.md`'s Track/Sources lists — the two should now largely agree post-retag; a
   doc present in one but not the other is either a post-2026-07-27 addition never added to the Sources list (fix by
   adding it there, per the 3-doc example already tracked in
   `/plans/archive/2026_07/asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`'s own Phase 3), or a genuine new
   mistag worth fixing on sight. For the 5 AGs + cross-cutting, filter out docs whose `asset_group` also contains a
   genuinely DIFFERENT peer asset-group marker (any of `cefi`/`defi`/`tradfi`/`quant`/`options`/`cross-cutting`,
   EXCLUDING `<ag>` itself and the historically-confirmed same-work dual-tag `prediction` when auditing `sports` or vice
   versa — that pairing describes the same betting-market work tagged two ways, not two different scopes) — these are
   the deterministic cross-cutting candidates to exclude from the deep audit. This is a CANDIDATE filter only; the
   per-doc agent in Phase 1 re-checks scope from real content (step 5 below), since `asset_group` tagging is not
   perfectly reliable. Further exclude docs already `status: resolved`/`archived`/`superseded` — they're already closed,
   not orphans. **Orthogonality HARD CHECK (added 2026-07-25 — a real corpus-quality bug, not a hypothetical; peer set
   WIDENED 2026-08-08 after a live miss — see below)**: `cefi`/`defi`/`tradfi`/`prediction`/`sports` and `cross-cutting`
   are meant to be a MUTUALLY EXCLUSIVE partition — a doc belongs to exactly one specific tranche, or is genuinely
   cross-tranche, never both. **The peer set this check runs against is ALL 9 other real tranches, not just the original
   5 AGs**: `ao`/`ci`/`infrastructure`/`ui` became real dedicated `asset_group` enum values on 2026-07-27/30 (see the
   classification-mechanism section above) and are exactly as "specific" as `cefi`/`defi`/`tradfi`/`prediction`/
   `sports` for this check's purposes — a doc tagged `[ao, cross-cutting]` or `[ci, cross-cutting]` is the identical
   mistag shape as `[cefi, cross-cutting]`. **This was a real, live gap, not a hypothetical widening**: every daily run
   from 2026-07-25 through 2026-08-07 only ever grepped the 5-AG peer set (every prior parked-findings doc's
   Orthogonality section shows zero ao/ci/infra/ui dual-tag hits reported, not because none existed but because the
   check never looked) — the 2026-08-08 cross-cutting run reran the grep against the full 9-tranche peer set and found 5
   hits instantly: `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md` `[ao, cross-cutting]`,
   `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` `[ao, cross-cutting]`,
   `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` `[ao, cross-cutting]`,
   `glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md` `[ci, cross-cutting]`,
   `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` `[cross-cutting, ci]` — full evidence in
   `issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md`. A doc tagged with exactly ONE specific tranche PLUS
   `cross-cutting` (e.g. `[cefi, cross-cutting]` or `[ao, cross-cutting]`) is a MISTAG, not a valid third category — and
   it is actively dangerous: per the exclusion rule above, such a doc gets excluded from `<tranche>`'s own audit
   (cross-cutting reads as "a different peer marker") AND excluded from `cross-cutting`'s own audit (the specific
   tranche reads as "a different peer marker" there too) — it falls through BOTH audits and becomes an invisible orphan
   the discovery step itself creates, exactly the failure class this whole skill exists to catch. **Before running Phase
   1 for `<tranche>` OR for `cross-cutting`**, grep the corpus for `asset_group:.*cross-cutting` and check each hit's
   array for exactly one other specific-tranche marker from the FULL peer set (`cefi`/`defi`/`tradfi`/
   `prediction`/`sports`/`ao`/`ci`/`infrastructure`/`ui` — not just the 5 AGs; not the legitimate "spans multiple/all 5
   AGs + cross-cutting" pattern used by genuine cross-AG coordination docs, e.g.
   `ag_closeout_audit_rollout_2026_07_25.md`, which is fine as-is, if slightly redundant — cross-cutting alone would
   already imply multi-AG scope). Any single- tranche+cross-cutting hit found must be RETAGGED correctly (read the doc's
   real content/repos to decide which side is right — confirmed examples fixed 2026-07-25:
   `coinbase_bare_name_migration_execution_service_2026_07_10.md` was genuinely cefi-only, `cross-cutting` dropped;
   `issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` was genuinely cross-AG, `cefi` dropped), never
   silently left dual-tagged or silently excluded from both audits. **After every retag, re-run
   `scripts/plan-hygiene/check_ag_closeout_linkage.py` before moving on** — fixing the TAG is necessary but not
   sufficient: a doc just retagged onto its real AG can be newly orphaned WITHIN that AG if nothing in that AG's
   closeout family (its `related:` graph or its aggregated-sources digest body text) mentions it yet — the check went
   0→4→0 orphans, then 0→1→0, then 0→3→0 across 3 separate retag rounds this session, each time because the fix landed
   correctly but the linkage step was skipped first. The remedy is a one-line addition to the AG's
   `<ag>\_consolidated_closeout_aggregated_sources*\*.md`(or the main closeout doc if no aggregated-sources sibling
   exists) naming the retagged doc — use a proper`[text](path)` markdown link, not a bare backtick-quoted filename,
   since prettier can wrap a long bare filename across a line break and silently break the substring match the linkage
   check relies on.

   **A second, distinct sub-bug (found the same day, scoping the cross-cutting AG's own candidate corpus):** the
   dual-tag grep above only catches a doc carrying BOTH a specific AG and `cross-cutting`. It does NOT catch a doc
   tagged with ONLY `cross-cutting` whose actual content is single-AG-specific — there is no second tag to grep for, so
   this class is invisible to any tag-only check and only surfaces by reading the doc's real content (endpoints,
   registries, data types, `tags:`/`related:`). Confirmed example:
   `issues/understat_bulk_download_backfill_2026_06_29.md` was tagged bare `[cross-cutting]` but is an Understat
   (football/soccer xG provider)-specific backfill for 5 named leagues — every endpoint/registry/data type in it is
   sports-only, not a generic reusable pattern; retagged `[sports]`. **Before shipping any `cross_cutting_*` corpus
   scoping decision, spot-check a sample of candidate docs' actual content against their tag, not just their frontmatter
   shape** — a plausible-sounding generic title is not proof the content is actually cross-AG.

   **A third pattern, found scoping the same corpus, confirms this is SYSTEMIC not one-off: a fork inherits its parent's
   `cross-cutting` tag verbatim instead of being corrected to the child's real single-AG scope.** When a large cross-AG
   coordinator/harness plan (e.g. `master_data_canonicalisation_migration_catalogue_2026_06_07.md`,
   `migration_verification_orphan_safety_2026_06_10.md`) gets line-cap-split and forks a per-AG residual child (e.g.
   "the DeFi-specific bucket", "the sports pre-launch bucket"), the fork commonly copies the parent's
   `asset_group: [cross-cutting]` forward unchanged even though the forked child's content is now single-AG-specific by
   construction (that's WHY it was forked into its own bucket). Confirmed examples fixed 2026-07-25 (all 6 were bare
   `[cross-cutting]`, all forked from one of the 2 coordinators above): `defi_migration_audit_log_2026_07_24.md` →
   `[defi]`, `defi_venue_lst_rates_residual_2026_07_24.md` → `[defi]`,
   `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` → `[cefi]`, `issues/cefi_universe_capture_rule_2026_06_23.md` →
   `[cefi]`, `prediction_cqg_residual_2026_07_24.md` → `[prediction]`,
   `sports_prelaunch_cf5_verify_residual_2026_07_24.md` → `[sports]`. **When auditing a doc whose title or
   `related:`/`source:` names a per-AG fork of a cross-cutting coordinator, check the FORK's own content scope, not the
   parent's tag** — a title starting with an AG name (`cefi_`/`defi_`/`tradfi_`/`prediction_`/`sports_`) on a doc tagged
   bare `[cross-cutting]` is close to a guaranteed hit; grep `^plans/active/(cefi|defi|tradfi|prediction|sports)_.*\.md`
   / `issues/(cefi|defi|tradfi|prediction|sports)_.*\.md` against the cross-cutting-tagged file list as a fast first
   pass before the full corpus sweep.

   **`asset_group: [meta]` on a NEW doc is an authoring defect going forward (added 2026-07-30, after this session's
   one-time meta fold-in sweep).** `meta` is a legitimate value for genuinely process-level content that belongs to no
   tranche (the frontmatter schema itself, the plan-format spec, a corpus-wide convention doc). It is NOT a default, and
   it is NOT a place to park a doc whose content is really single-tranche or genuinely cross-AG — a bare `[meta]` doc is
   invisible to all 10 tranche membership rules, which is exactly the invisible-orphan class Phase 0.3 exists to catch
   (the one-time sweep that folded the standing `meta` population into its real tranches is done; the point of this note
   is that the population must not silently rebuild). **Authoring rule**: pick the correct tag at creation time — a real
   tranche value when the content is tranche-scoped, `cross-cutting` when it genuinely spans AGs, `meta` only when it
   spans everything or nothing. **Tooling follow-up**: `check_frontmatter_schema.py` (or a lighter dedicated QG check)
   should at minimum FLAG — not necessarily hard-block — a `meta`-tagged doc whose filename carries an AG-specific-
   sounding prefix (`cefi_`/`defi_`/`tradfi_`/`prediction_`/`sports_`/`ao_`/`ci_`/`infra_`/`ui_`), mirroring the
   existing cross-cutting-mistag heuristic two paragraphs above. Until that check exists, an `all`-mode run still sweeps
   `asset_group: meta` by hand per the "Total-coverage gap" note above.

## Phase 1 — per-doc classification (Workflow tool, one agent per doc)

**`all` mode**: run Phase 0-3 once PER TRANCHE, as 10 separate top-level `Workflow` invocations (never nest a
`workflow()` call inside another — the tool throws on >1 level of nesting) — either sequentially or fired in parallel
from the calling context, then aggregate the 10 reports into one combined summary at the end. Do not try to flatten all
10 tranches' docs into one giant Workflow pipeline; each tranche's Phase 0 discovery (its own consolidated closeout +
batch/finalize pairs) is genuinely distinct context per doc.

Given the AG-primary candidate list from Phase 0.3, launch a `Workflow` (`pipeline()` over the doc list — this corpus
runs 50-90+ AG-primary docs per AG, well past what's worth doing serially or by hand). Each agent:

1. Reads its target doc IN FULL, end to end — **never conclude from checkbox count alone** (confirmed trap: real
   remaining work expressed as numbered PROSE lists with zero checkboxes) and **always read to the doc's end**,
   including any dated `## Update` / `## RE-TRIAGE` / `## RESOLVED` section (confirmed trap: these override earlier
   `[x]` marks back to open, or vice versa — the latest dated section is authoritative).
2. Notes frontmatter `status` + `related:`.
3. Enumerates genuinely remaining open work (checkbox AND prose-form) as of now.
4. For each remaining item, greps the AG's consolidated-closeout doc AND every discovered batch/finalize plan (Phase
   0.1/0.2 — pass their paths into the agent's context) for this doc's filename/basename, reads any citing todo, and
   judges whether it fully closes the item or only partially covers it. **The coverage bar is a dispatched `## Todos`
   entry, nothing weaker** (added 2026-08-10, from the `ui` tranche's 2026-08-08 Finding 1): only an open `- [ ]` in a
   covering doc's own `## Todos` section, on a doc that is actually dispatchable (`assigned_vm: planning` +
   `status: active`), counts as coverage. A mention in a `## Deferred` section, a `related:` link, a narrative/analysis
   paragraph, or a citation inside a `status: draft` doc is NOT coverage — those are exactly the shapes that produce a
   false `archivable_after_planned_work` verdict on work nothing is actually going to do.
5. Sanity-checks real scope vs the asset_group tag (catches Phase 0.3's imperfect deterministic filter).
6. Returns a structured verdict: `archivable_now` / `archivable_after_planned_work` / `orphaned_partial_coverage` /
   `orphaned_never_touched` / `exclude_cross_cutting`, each with `reasoning` citing the specific evidence found.

Use the exact schema and covering-context prompt pattern from the sports run
(`plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`'s sibling audit, 2026-07-25) as the template
— swap in the discovered `<ag>` covering-plan paths.

## Phase 2 — synthesize + report

Count by verdict, excluding `exclude_cross_cutting`. Report to the operator: total AG-primary docs audited, counts per
verdict, and the full list of `orphaned_partial_coverage` + `orphaned_never_touched` paths with one-line reasoning each.
This alone answers "how many docs are left orphaned" — stop here if the operator only asked the audit question.

## Parked findings ALWAYS get a durable issue doc — including a Phase-0-2-only run (HARD, added 2026-07-30)

**The failure this closes**: on 2026-07-30, **30 of 41** parked ag-closeout decisions were never written anywhere
durable — they existed only in the ephemeral chat/return text of the agent that found them. The root cause is
structural, not carelessness: until now the ONLY parking location this skill designated was **Phase 3's** new-batch
`## Deferred` section, and a **Phase-0-2-only run never reaches Phase 3**. That is the NORMAL daily-cron shape (audit +
report, no drafting), so the standard scheduled run had nowhere sanctioned to put a parked finding and simply reported
them into the void.

**The rule**: every genuine parked / `BLOCKED-OPERATOR-DECISION` finding is written to a durable doc in the SAME run
that found it, whichever phase the run stops at. **Never leave one only in the agent's own return text** — chat is not a
durable surface, and an AO-dispatched run has no human reading its chat at all.

- **Phase 3 ran** → the new batch's own `## Deferred` section stays the durable home (unchanged; tag each entry with its
  non-batchable-taxonomy category, above).
- **Phase 0-2 only** — including EVERY scheduled/cron invocation → write
  `plans/active/issues/ag_closeout_audit_<tranche>_parked_<YYYY_MM_DD>.md`. This is the same pattern `/plan-reconcile`,
  `/docs-reconcile` and `/na-eligibility-audit` already use for their own parked findings; do not invent a new shape.
  One doc per tranche per run — APPEND to a same-day doc if one already exists rather than creating a second. Each entry
  carries: the doc/finding, which taxonomy category it is parked under, and an options block with a marked
  recommendation (`cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § escalation format). **ASK > PARK still applies** — if
  the operator is reachable, ask; the issue doc is for a genuinely absent operator, not a mode flag.

  **HARD — check `plans/archive/**` for the slug BEFORE writing it (added 2026-08-10).** "APPEND to a same-day doc if
  one already exists" only ever looked at `plans/active/issues/`. A doc archived EARLIER THE SAME DAY is not there, so
  the write re-creates it at the active path and the corpus ends up with two different documents sharing one slug —
  which breaks `[[wikilink]]` resolution, defeats the create-only duplicate guard's basename matching, and makes "which
  one is authoritative?" unanswerable. Measured 2026-08-10: this produced **3 of the 10 live duplicate pairs** on origin
  (`42247c0405`, `064019f77f`, `6b7ddb7944` each `A`-added a doc an earlier commit had archived that morning).

  ```bash
  # BEFORE writing plans/active/issues/ag_closeout_audit_<tranche>_parked_<DATE>.md:
  git ls-tree -r --name-only origin/live-defi-rollout plans/archive/ | grep -F "ag_closeout_audit_<tranche>_parked_<DATE>.md"
  ```

  A hit means today's report is a SECOND run of a tranche already closed out today. Do **not** re-create the active
  path. Either append your new findings to the archived doc (and un-archive it deliberately, with the 6-step ritual in
  reverse and a banner saying why), or — if the findings are genuinely new work rather than a re-report — write to a
  distinct slug that says so (`…_parked_<DATE>_run2.md`) and cite the archived doc. Never resurrect a slug silently.

- **`all` mode** → each tranche writes its OWN doc; the aggregated report cites every one by path.
- **Count it, don't eyeball it.** Mirror `/plan-reconcile`'s Phase 5.9(a) ledger: assert
  `parked_findings == entries_actually_written_to_the_issue_doc(s)` and print BOTH numbers in the final report. That
  reconciliation is the specific defence against the 30-of-41 class — a run whose two numbers do not balance is NOT
  done; go write the difference before reporting.

### Three things that must NOT reach a parked doc (HARD, added 2026-08-10)

**The failure this closes**: a 2026-08-10 operator review of all 28 live `ag_closeout_audit_*_parked_*.md` docs found 62
open todos of which only ~⅓ were real, uncovered, human-needing work. The rest were mechanical fixes the run could have
just done, informational tombstones that are not tasks at all, and the same unresolved finding re-parked into a new
dated doc every single day (one carried 7 days across 5 docs, self-labelling "carried, 7th day"). A parked doc whose
open count is mostly noise cannot be triaged by anyone, which is the same practical outcome as not writing it down.

1. **Mechanical corpus hygiene is FIXED IN-RUN, never parked.** If the finding is a named-doc, named-field edit whose
   correct value the run has already determined — an `asset_group` retag, a stale "0 open todos"/"STILL OPEN" claim in
   another doc, a checkbox whose resolving evidence you just cited, a `related:`/linkage edge — **do it, ship it, and
   record it under "Resolved this run" instead of `## Todos`**. Precedent already in this corpus: the `ao` tranche's
   2026-08-10 run fixed its own mistags in-run under the Orthogonality HARD CHECK and shipped them
   (`unified-trading-pm@60b2953cc5`); the same day, the `cross-cutting` and `ci` runs parked the identical class of work
   as `[DOCS] P3` todos, where they then sat for 3-9 days. Same work, two dispositions — the in-run one is correct. Only
   park a hygiene fix if it collides with another agent's live claim (`locked_by`, mtime <120s), and say so explicitly.
   **Retagging a doc OUT of your tranche is still your fix to make** — "leave it to the `<other>` tranche's own audit"
   is how a wrong tag survives 9 days without any tranche ever owning it.
2. **An informational finding is NOT a todo.** "No action needed on Finding N unless/until X", "re-check when Y next
   moves", "left unchecked for continuity/audit-trail only" — these have no done-when and no actor, so they can never be
   closed and they inflate the corpus open count (and the NA ratchet) forever. Write them as prose in the findings body.
   A `- [ ]` line requires a named actor and a checkable done-when, per `plans/PLAN_FORMAT.md`. If a finding's real
   content is "the NEXT worker to touch this file should also check Z", that belongs in the target doc, not as a
   standing todo here.
3. **A carried finding lives in ONE doc — re-date it, never re-park it.** The existing "APPEND to a same-day doc" rule
   dedupes WITHIN a day but says nothing across days, so an unresolved P3 got copied into a fresh dated doc on every
   run. **Before writing any entry, grep `plans/active/issues/ag_closeout_audit_<tranche>_parked_*.md` for the finding's
   subject.** If a prior doc already carries it and it is still unresolved: append a dated `> **<date> re-confirmed**`
   line to THAT doc's existing entry and leave today's doc silent on it. A finding may appear in exactly one parked doc
   at a time. If a finding survives 3 re-confirmations, stop re-confirming and escalate it — ASK the operator, or file
   it as its own issue doc with a real owner; a 4th "still true" is not new information.

## Phase 3 — draft the next batch (only if the operator wants this AG progressed, not just measured)

For every orphaned doc, apply the SAME dispatch-scope eligibility test `task_template.md` uses (operator ruling
2026-07-23): is the remaining work a bounded, checkable outcome a worker can execute alone, or does it require an
undecided design/judgment call?

**Conflict check — BEFORE drafting any candidate todo (HARD, added 2026-07-25 per operator instruction: a
naively-extracted batch todo can regress work the consolidated plan already has in flight for the SAME file/fix from a
different angle).** This is now the SHARED protocol documented in full at
`codex/11-project-management/ao-dispatch- batch-naming-and-conflict-check.md` § 3 — `/na-eligibility-audit` (the sibling
skill auditing the disjoint `assigned_vm: NA` population) runs the identical check before any `NA → planning` flip, so
the procedure lives in one place, not two. For each candidate item, grep the AG's consolidated-closeout plan's OWN todos
AND every existing batch plan for this AG (Phase 0.1/0.2) for overlap on the same target file(s)/same underlying fix —
not just "is this covered" (Phase 1's question) but "does something ELSE already claim this exact ground, possibly with
a different approach". **Also check the 4th surface**: any `status: draft` `{ag}_satellite_ao_dispatch_batch{N}_*.md`
for this tranche from a PRIOR `/ag-closeout-audit` or `/na-eligibility-audit` run, not just this one — grep its
`Source:`/`## Deferred`/`## Already covered` citations for the candidate doc's path before drafting a new extraction.
Three outcomes:

- **No overlap** — draft normally.
- **Clear duplicate or the other side is provably stale/superseded** (a newer dated section in either doc, a commit that
  already shipped one approach, an explicit supersession banner) — resolve by logic: do not draft a competing todo;
  instead cite the existing one and skip, or fold the residual delta into a note on the existing todo. Same auto-resolve
  bar as `/plan-reconcile`'s Phase 4: the evidence must make exactly one answer provably right, not just plausible.
- **Genuine conflict** (two todos would prescribe different fixes to the same file/mechanism, ordering is unclear, or
  it's not resolvable from evidence alone) — do NOT draft it silently. Surface it as a batched operator question (same
  format as `/plan-reconcile` Phase 4: both quotes + locations, why they conflict, options with a marked recommendation)
  before drafting/shipping that specific item. In autonomous mode, park it as `BLOCKED-OPERATOR-DECISION` in the new
  batch's own `## Deferred` section rather than guessing which side wins.

Only conflict-cleared bounded items become candidate todos for a new `<ag>_satellite_ao_dispatch_batch<N>_<date>.md` —
author it with the SAME discipline as `sports_satellite_ao_dispatch_batch2_2026_07_24.md`:

- Every todo ends with `Source: \`<doc>.md\`` and a **Done when** clause.
- Internally-sequential multi-step work in one source doc becomes ONE combined todo, not fanned-out steps that would
  race each other (confirmed pattern: `mdt_legacy_canonical_row_gap_2026_07_16.md`'s 5-step chain).
- Verify zero cross-todo file collisions before finalizing (same-priority todos in one plan run concurrently by default
  — CLAUDE.md's Plans rule).
- Anything still gated on a sibling todo landing or an unmade human/operator decision goes in an explicit `## Deferred`
  section, NOT dispatched speculatively.
- `assigned_vm: planning`, `execution_scope: orchestrator-agent`, `sequential:` unset unless the batch is genuinely a
  dependency chain.
- **`status: draft`** — this is the safety rail. A draft is not ingested/dispatched (`plans/PLAN_FORMAT.md`); flipping
  it to `active` is the operator's call, in interactive mode ask directly, in autonomous mode park it as a follow-up.

**IDEMPOTENCY GUARD — re-derive gated slugs BEFORE writing the finalize plan (2026-08-11,
`duplicate_finalize_plans_created_for_one_parent_2026_08_06.md`).** Before authoring the finalize plan, verify the batch
is not ALREADY gated by an existing finalize plan — key on the `depends_on` relationship, not on the expected filename
(the two colliding files that spawned this guard differed only by a redundant `_2026_07_31` suffix). Run:

```bash
.venv/bin/python scripts/quality_gates/check_finalize_plan_coverage.py --workspace-root <root> 2>&1 \
  | grep -Fw "<batchN-slug>" && echo "ALREADY GATED — skip finalize-plan creation" || echo "not gated — proceed"
```

Or programmatically: re-derive `check_finalize_plan_coverage.py::_gated_slugs()` over the current corpus and check
`<batchN-slug> in gated`. If already gated, SKIP finalize-plan creation entirely — a companion already exists and
creating a second one is the exact race this guard prevents. Report the skip + the existing plan's path so the operator
can verify.

Pair it with `<ag>_satellite_ao_dispatch_batch<N>_finalize_<date>.md` in the SAME turn (`depends_on: [<batchN-slug>]` +
`gate_on_depends: true` + `sequential: true`) — per `task_template.md` §4's finalize-plan-coverage rule. Author it
**`status: active`, NOT draft** (corrected 2026-07-30 — see finding below). Validate both with
`.venv/bin/python scripts/plan-hygiene/check_frontmatter_schema.py --files <paths>` and
`bash scripts/plan-hygiene/check_todo_format.sh <paths>` before presenting them.

**Why the finalize plan is `active`, not `draft` (2026-07-30 finding — no double gate)**: `gate_on_depends: true`
already machine-holds every one of the finalize plan's tasks until the batch's own todos are done —
`_wire_gate_on_depends_prereqs` (`regen_backlog_from_plan.py`) covers BOTH an already-active batch (holds via
`prereqs.completed_tasks` until its tasks are literally `done`) AND a still-draft batch (holds via a derived
`gate-upstream-open:<stem>` condition read straight off the batch file's own checkboxes, regardless of the batch's
`status`). A finalize plan carries no independent judgment call — its content (reconcile checkboxes + archive) is fully
decided at authoring time — so stacking the batch's `status: draft` safety rail on top of it is a redundant second gate
that requires a SEPARATE manual flip nobody reliably remembers: a 2026-07-30 corpus audit found 46 finalize plans stuck
in draft, most with their batch already done and archived weeks earlier. Only the BATCH itself (genuinely unreviewed,
judgment-call content) needs `status: draft` + explicit operator approval.

**Never quickmerge/ship the drafted BATCH without the operator explicitly approving it** (flip its `status: draft` →
`active` yourself only after that approval, then ship). The finalize plan needs no separate flip — it ships `active`
from the start and `gate_on_depends` holds it correctly either way.

## Codex SSOTs

- `plans/active/task_template.md` §4 — finalize-plan-coverage rule + dispatch-scope eligibility test this skill reuses
- `plans/PLAN_FORMAT.md` — `status: draft` semantics, frontmatter schema
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/` — findings triage, archival ritual
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  (§ 3) this skill's Phase 3 runs, also used by `/na-eligibility-audit`; § 2 (`parent_epic` as the grouping axis) is the
  SSOT behind the primary-owner rule for multi-tranche docs
- `/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT cover" — why `git stash` is banned
  for concurrent sharded tranche workers (`refs/stash` is one shared LIFO stack per clone)
- `cursor-configs/skills/na-eligibility-audit/SKILL.md` — sibling skill (already-owned `assigned_vm: NA` doc validity —
  a disjoint QUESTION over an OVERLAPPING population; see the "Also NOT `/na-eligibility-audit`" note above) + the
  statement of the primary-owner rule this skill references rather than duplicates
- Precedent: `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` +
  `plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`
