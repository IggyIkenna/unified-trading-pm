---
name: context-scout
description: >-
  Maintain the `context_scope` frontmatter field (an elective free_list on `plan` and `issue` docs,
  `scripts/docs/docspec.py`) — a minimal reading-list of codex SSOTs, related plan/issue docs, and key source paths a
  worker should read before touching that doc, computed per-doc rather than left for every worker to re-derive via a
  fresh cold grep. Follows the MVI (Minimal Viable Information) principle — a short, curated list a worker can read in
  full, not an exhaustive index. Runs incrementally (skip docs already scouted and unchanged since) via
  `scripts/plan-hygiene/generate_context_scope_inventory.py`, so a daily re-run is cheap once the corpus is caught up.
  Trigger on `/context-scout`, "backfill context_scope", "populate the reading list for this plan", "what should I read
  before working on `<doc>`", "is context_scope stale".
---

# /context-scout — context_scope frontmatter maintenance

Maintains a DIFFERENT axis of every plan/issue doc than the other daily plan-health skills: not
status/orphan-coverage/NA-eligibility, but **what should a worker read first**. `/plan-reconcile`, `/ag-closeout-audit`,
and `/na-eligibility-audit` all judge a doc's own correctness; this skill never touches a doc's `status`, todos, or body
content beyond adding a dated marker — it only reads a doc and writes back a `context_scope:` list.

**Out of scope**: judging whether a doc's status/todos are still correct (that's
`/plan-reconcile`/`/na-eligibility-audit`), orphan detection (`/ag-closeout-audit`), or codex-doc health
(`/docs-reconcile`). A doc this skill scouts may separately need one of those audits — this skill doesn't run them and
doesn't defer to them; it's a disjoint concern.

## Why a minimal list, not an exhaustive one

The point is to cut a worker's cold-start context burn, not maximize recall. A `context_scope` with 15 entries is no
better than none — nobody reads 15 files before starting. Target **2-6 entries per doc**: the codex SSOT(s) the doc's
own subject matter depends on, any plan/issue this doc supersedes or is gated on (when not already obvious from
`depends_on`/`supersedes`), and source paths (directories or well-known filenames, never line numbers, same citation
discipline as `task_template.md` §3).

**A codex doc explains the RULE; a source path is where a worker actually goes to BUILD the fix — a doc that names one
without the other leaves a worker who has to re-derive the second half via a fresh cold grep, which is the exact cost
this skill exists to cut.** Measured on the first corpus-wide backfill (2026-07-30): a spot-check of 342 already-scouted
docs found only 51% carried a real source path at all, and roughly a third of the corpus were non-coordination docs that
ended up codex/plan-only when their own body text already named the exact file. The failure mode isn't "couldn't find
one" — it's settling for whatever's easiest to cite (a codex doc) over doing the extra step of surfacing a file the doc
_already names in its own prose_. **Default assumption: if a doc's body names a specific filename, script, module, or
class by name anywhere in its text, that path is a near-automatic include** (verify it exists, then add it) — treat NOT
including it as the exception requiring justification, not the other way around. The only docs that legitimately end up
with zero source paths are ones with no code target at all: a dispatch-batch coordinator
(`*_satellite_ao_dispatch_batchN_*`) or a `*_finalize` gate whose entire job is pointing at OTHER docs, a pure
design/proposal doc not yet executed, or a process/audit-of-docs doc. For everything else, a codex-only `context_scope`
should be treated as an unfinished Phase-1 pass, not an acceptable minimal result.

## Phase 0 — inventory (cheap, no agents)

Run `python3 scripts/plan-hygiene/generate_context_scope_inventory.py --json`. Reuses `scripts/docs/docspec.py`'s PyYAML
frontmatter parser — do not re-derive frontmatter parsing with a line-grep (that bug class — a multi-line YAML value or
a non-standard checkbox bullet silently missed — has recurred twice already in this repo's other inventory scripts). Per
doc, the script verdicts:

- **NEVER_SCOUTED** — no `context_scope` field, or present but empty.
- **STALE** — has `context_scope`, but no dated `context-scout YYYY-MM-DD` Progress Log marker at or after the doc's
  last-touched date (frontmatter `last_updated`, falling back to the file's git last-commit date).
- **UP_TO_DATE** — marker date already covers the doc's last-touched date. Skip.

Report the split up front (total in-scope docs, never-scouted, stale, up-to-date-skipped). **The first-ever run will
show hundreds of NEVER_SCOUTED docs — expect it to look like a real backfill (many sub-agent batches), not a quick daily
pass.** Every subsequent run should be small (only docs created or edited since yesterday), which is the entire point of
the incremental design — if a run ever looks like a full re-scan again, something is wrong with the marker/date logic;
report that plainly rather than silently paying the full cost every day.

## Phase 1 — per-doc scouting (the real work)

**Backfill mode** (a large NEVER_SCOUTED+STALE population — dozens to hundreds of docs, e.g. the first corpus-wide run
or a fix that re-flags a large slice): batch the in-scope docs into groups of ~10-15 and fan out read-only sub-agents
via a `Workflow` `pipeline()` (max 10 concurrent per this workspace's sub-agent cap; paste
`cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of every spawn; set `model=` explicitly — sonnet is enough for
this, no architecture/trading judgment involved).

**Daily-incremental mode** (the expected steady state once the corpus is caught up — a small residual, roughly under ~15
docs, from that hour's/day's edits): a `Workflow`'s fan-out ceremony is overkill for a handful of docs — dispatch 2-4
direct `Agent` tool calls instead (same sub-agent-rules pasting + explicit `model=`), splitting the small doc list
evenly across them. Reserve `Workflow` for genuine backfills.

Each hunter, per doc (per `/codex/12-agent-workflow/context-economy.md`'s scoped-read discipline — grep the doc for
`related:`/`depends_on:`/`Codex SSOTs:`/named filenames first; for a doc over ~300 lines, read only the sections that
matter — Why/root-cause, todos, the most recent Progress Log entries — rather than top-to-bottom; fall back to a full
read only once grep shows most of the doc is actually relevant):

1. Reads the doc's frontmatter (`related`, `depends_on`, `supersedes`, `parent_epic`) and body (Why section, todos, any
   `Codex SSOTs:` list already present).
2. Extracts every codex/plan/issue path the doc's OWN text already cites — these are free, no judgment required, just
   collection.
3. Judges whether the doc's substance implies an unstated codex SSOT it should but doesn't cite (e.g. a doc doing a GCS
   delete that never mentions the delete-safety protocol). **Never guess a plausible-sounding codex path** —
   grep-then-READ the candidate (per this workspace's grep-then-conclude ban) and confirm the doc actually exists and
   actually covers the claim before adding it. An unconfirmed guess becomes a Phase 5 suggestion, not a written
   `context_scope` entry.
4. **Resolve any hedged "candidate" pointer already sitting in the doc's own prose/todos** — phrases like "candidates
   found by grep", "likely owned by", "probably tracked in", "TBD which doc covers this". These read like citations but
   are unverified guesses the doc's own author never confirmed; treat them exactly like step 3's unstated-SSOT case:
   grep-then-READ every named candidate and confirm whether it actually owns/tracks the claim (real incident: a plan's
   own todo named 3 grep candidates for 4 follow-up items — only 1 of the 3 was a real owner, and 2 of the 4 items were
   actually owned by an entirely different, unlisted doc found only by a fresh corpus-wide grep, per
   `data_status_page_ux_and_canonicalisation_2026_07_16.md` todo P3, 2026-08-03). Any CONFIRMED owner goes straight into
   `context_scope` — even though the doc's own hedge was never resolved, a future worker should get the verified doc,
   not redo the grep. Any candidate that turns out NOT to own the claim, or a hedge that resolves to "no doc found," is
   surfaced in the Phase 3 report as a stale-candidate-pointer finding — **do not rewrite the doc's own todo/body prose
   to fix it**; that correction is `/plan-reconcile`'s job (this skill only ever writes `context_scope` + the dated
   marker, per its scope boundary above). 4a. **Cross-reference by evidence fingerprint, not just topic** — for a doc
   whose "Evidence"/findings section quotes a distinctive literal (an exact error code, an HTTP header value, a
   secret/resource name, a VM name, a byte-identical log line), grep the rest of `plans/active/` (and `.../issues/`) for
   that EXACT string before finalizing `context_scope`. Two docs independently recording the same distinctive
   fingerprint is strong evidence they're investigating the SAME underlying incident, even when their titles/topics look
   unrelated (real incident: `odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md`'s original scout
   pass — 4 entries, all topically about the live connector — never surfaced
   `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, which had independently recorded the identical
   `x-requests-remaining: -772`/`x-requests-used: 5000772` evidence a day earlier and already contained the full
   root-cause forensic trail; a worker who later got only the shallow scope had to redo ~215k tokens of fleet-wide
   grepping and gcloud attempts to re-find what was already written down, 2026-08-03). A CONFIRMED fingerprint match
   goes straight into `context_scope` on BOTH docs (this is one of the few cases where scouting one doc legitimately
   touches another's frontmatter — see Phase 2); a topical-only match without a literal string overlap does not qualify,
   don't over-fire on it.
5. **Actively hunts for the doc's real source-code target — this is not optional padding, it's the half of the job a
   codex citation alone doesn't cover.** Re-read the doc's body specifically looking for filenames, script names, class
   names, or module paths already named in prose (root-cause sections, "Plan"/"What shipped" todos, and error messages
   are the highest-yield spots) — every one of those is a near-automatic include once verified to exist. If the body
   doesn't name one explicitly but the doc is clearly about fixing/building something in a specific repo (not a
   coordination/dispatch-batch doc — see below), grep that repo for the obvious entry point before concluding there's
   nothing to cite. Add 1-3 source paths (directories or well-known filenames, never line numbers — a plan outlives the
   code it points at; see `task_template.md` §3's identical rule for todos). **Skip source paths only for a genuinely
   code-free doc**: a dispatch-batch coordinator (`*_satellite_ao_dispatch_batchN_*`), a `*_finalize` gate, a pure
   design/proposal not yet executed, or a process/meta-audit-of-docs doc — for these, codex+plan-only is the correct,
   complete answer, not a shortcut.
6. Verifies every proposed entry actually resolves — `/codex/...` and `/plans/...` paths must exist on disk, source
   paths must exist in the named repo — before returning. A dead pointer in a reading-list field is worse than an absent
   field; drop anything that doesn't resolve and note it was dropped.
7. Returns a **minimal** ordered list (2-6 entries) — resist padding; if a doc genuinely only needs one codex doc, write
   one.

## Phase 2 — apply

- **Line-cap pre-check (HARD RULE, before writing)**: if the doc is within ~15 lines of the workspace's 1000-line hard
  cap (already flagged `SOFT` by Phase 0, or a quick `wc -l` shows >985), verify with
  `bash scripts/plan-hygiene/check_line_caps.sh <path>` before shipping — a doc newly crossing 1000L in this commit is a
  real, unexempted violation (SCOPED mode has zero baseline tolerance for that; see `check_line_caps.sh`'s own policy
  comment). Two `.prettierrc` behaviors make this non-obvious: (1) a `context_scope:` flow-list stays on ONE line only
  if the full `context_scope: [...]` line fits under `printWidth: 120` — count it before choosing entry count, or it
  silently expands to one-entry-per-line (7-8+ lines for a 5-entry list); (2) `proseWrap: always` means a marker
  appended right after existing prose (no blank line) gets merged into that paragraph and reflowed, which costs a full
  extra wrapped line REGARDLESS of how short the marker text is — a blank-line separator doesn't avoid this either, it
  just costs the same +1 a different way. If `context_scope` + marker together would push a doc over cap: try the most
  compact single-line `context_scope` first (2-3 entries, dropping to the highest-value pair if needed); if still over,
  ship `context_scope` alone and skip the marker (the doc shows `STALE` not `NEVER_SCOUTED` next run — a real
  improvement, not a failure) rather than force the cap or skip the doc's `context_scope` entirely. Note the doc + why
  in Phase 3's report; check for an existing line-cap remediation tracking issue (e.g.
  `plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`) before filing a new one.
- Write `context_scope: [...]` into the doc's frontmatter (YAML flow-list, matching the existing style already used in
  the corpus, e.g. `ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md`). This is the ONLY frontmatter field this
  skill ever writes. **Exception**: a Phase-1 step-4a confirmed fingerprint match writes `context_scope` on BOTH docs in
  the pair (the doc currently being scouted, AND the other doc whose evidence it matched) — even if the second doc is
  already UP_TO_DATE and wouldn't otherwise be touched this run. Still only ever writes `context_scope` + the dated
  marker on that second doc, nothing else.
- Append a dated Progress Log marker: `**context-scout YYYY-MM-DD**: populated/refreshed context_scope (<n> entries)` —
  this is Phase 0's incremental-skip anchor for every future run. Never skip writing this, even when the computed list
  is short.
- Stage by name, mandatory pre-commit `git status && git diff --cached --stat` (no path arg), commit prefix
  `docs(plans):`, ship per CLAUDE.md's git-discipline section (`quickmerge.sh --agent --files`). Batch by cohort (e.g.
  one commit per ~50 docs), not one mega-commit and not one commit per doc.
- A Phase-1 "unstated SSOT" suggestion that could NOT be confirmed does not get written anywhere in the doc — carry it
  into the Phase 3 report only, so a human can judge it without the doc itself making an unverified claim. Same rule for
  a Phase-1 step 4 stale-candidate-pointer finding: the confirmed owner (if any) goes into `context_scope`, but the
  doc's own hedge-prose is never rewritten by this skill — that goes to the report for `/plan-reconcile` to fix.

## Phase 3 — report

Finish with text: total docs scouted this run (never-scouted vs stale), total skipped (up-to-date), entries written (avg
per doc), any doc where Phase 1 found ZERO confirmable entries (report these — a doc with genuinely no reading-list is
fine, but worth surfacing so a human can sanity-check it isn't a scouting failure), every unconfirmed "unstated SSOT"
suggestion surfaced in Phase 1 step 3, every stale-candidate-pointer finding surfaced in Phase 1 step 4 (which
candidate(s) named in the doc's own prose/todos turned out wrong, and what the confirmed owner actually is, so
`/plan-reconcile` can correct the prose itself), and every step-4a fingerprint-match pair found (both doc paths + the
matched literal) — these are the strongest signal of genuinely duplicated investigation effort in the corpus and are
worth a human glance even though this skill already links them. Like
`docs_reconciler`/`ag_closeout_auditor`/`na_eligibility_auditor`, this is chat-text only — there is no separate
structured-findings endpoint. NEVER write agent memory; NEVER create a `*_SUMMARY.md` file.

**Post-hoc source-hunting lint (advisory, not a blocker)**: run
`python3 scripts/plan-hygiene/generate_context_scope_source_lint.py` and fold its output into the report. This is a
cheap deterministic regex-only second pass — not a re-run of Phase 1's judgment — over every already-scouted doc whose
`context_scope` has zero source-path entries: it checks whether the doc body still names a plausible source-code token
(a `*_service` identifier, a `.py` filename, or a `repos:` frontmatter name followed by a path-like token) that isn't
covered anywhere in the written `context_scope`, and skips the doc shapes SKILL.md already exempts (dispatch-batch
coordinators, `*_finalize` gates). A hit is a candidate for human spot-check, not a fact — the token could be a false
positive (a generic phrase, a renamed/deleted file, a doc discussing a service in the abstract). This exists because
Phase 1's hunting is pure agent judgment with no other check that it actually ran as specified (confirmed miss:
`/plans/archive/issues/context_scout_source_hunting_gap_2026_08_03.md`).

## Modes

**Interactive** (operator present, or invoked directly against one doc — `/context-scout <path>`): scout that one doc
synchronously, no Workflow fan-out needed for a single doc. **Autonomous (scheduled)**: the `all` default — Phase 0
across the whole corpus, Phase 1 fan-out, Phase 2 apply, Phase 3 report, never pausing; a doc whose Phase-1 judgment is
genuinely ambiguous (step 3's unconfirmed-SSOT case) is reported, never guessed.

## Scheduled cadence

Fires hourly via `context-scout.timer` on the central orchestrator VM
(`agent-orchestrator/scripts/install-context-scout-timer.sh`, staggered to :52 past the hour, after `plan-reconciler`
(:00), `docs-reconciler` (:15), `ag-closeout-auditor` (:30), and `na-eligibility-auditor` (:45) — so this run's Phase 0
sees that hour's other corpus fixes/retags first); the dispatch wrapper itself gates to at-most-once-per-day and only
retries the remaining hours in the day if an earlier attempt 503'd on capacity — same retry-until-capacity design as the
sibling timers. Still directly invocable interactively any time, against the whole corpus or a single doc path.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — `context_scope` field definition (elective, `plan`/`issue`
  doc types)
- `plans/active/task_template.md` §3 — symbol-not-line-number citation discipline (same rule this skill's Phase 1 step 4
  follows)
- `cursor-configs/skills/na-eligibility-audit/SKILL.md`, `cursor-configs/skills/docs-reconcile/SKILL.md` — sibling
  scheduled plan-health skills (disjoint concerns, same dispatch/report shape)
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract
- `/codex/12-agent-workflow/context-economy.md` — scoped-read + terse-response discipline this skill's own scouting work
  follows (Phase 1's per-doc read); that doc also names this skill as its complementary mechanism (pre-computing what a
  FUTURE worker reads, vs. how the CURRENT worker reads)
- `scripts/plan-hygiene/check_line_caps.sh` — the 1000L hard-cap gate Phase 2 must clear before writing
