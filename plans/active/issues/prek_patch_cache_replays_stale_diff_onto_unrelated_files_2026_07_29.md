---
doc_type: issue
title:
  prek's "stash unstaged changes / restore working tree" cycle reapplies a STALE, already-resolved patch onto unrelated
  files every quickmerge run on this slot — reproduced twice in one session, corrupting 2 plan docs both times with
  byte-identical garbage
summary: >-
  While shipping an unrelated fix via `quickmerge.sh` in `unified-trading-pm`, two `plans/active/*.md` files I never
  touched (`defi_consolidated_closeout_2026_07_18.md`,
  `issues/cefi_instruments_store_blank_data_type_residual_2026_07_29.md`) appeared dirty after the commit-hook chain
  ran, with a real content-corruption diff: a `last_updated:` YAML field mangled into a garbled multi-repeated-date
  runaway string, and a genuine `author: slot-4 (data_engineering)` line silently deleted. `git restore`'d both back to
  clean HEAD. Immediately re-ran the SAME `quickmerge.sh` command a second time (different files, same repo) — the
  IDENTICAL two files reappeared dirty with the BYTE-IDENTICAL corrupted diff. Traced to
  `/home/ubuntu/.cache/prek/patches/<timestamp>-<pid>.patch`: the patch FILE ITSELF already contains this exact
  corruption baked in (not something prettier/a hook mangled live during that run) — prek's "Unstaged changes detected,
  stashing... / Restored working tree changes from patch" step is replaying an ALREADY known, already-resolved stale
  diff, not a fresh snapshot of what was actually dirty at stash time. `~/.cache/prek/` is a HOME-level (not per-slot,
  not per-repo) cache directory — every slot/session on this host shares it, so this could plausibly also
  cross-contaminate a DIFFERENT repo's working tree if prek's patch-selection isn't scoped to the invoking repo path
  (not confirmed this session — flagged as the most severe possible blast radius, not proven).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prek, quickmerge, git, corruption, tooling-bug, ci-cd]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/quickmerge_help_flag_misparsed_as_commit_message_2026_07_30.md,
  ]
created: 2026-07-29
last_updated: "2026-07-30" # 6th confirmed reproduction, 2nd landed-on-origin occurrence, plus the concrete 9-patch-file forensic evidence (see Progress Log)
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: cicd
priority: P1
estimate_class: research
source: [cicd/general-worker session, ci_satellite_ao_dispatch_batch1-012, 2026-07-29 21:48-21:57 UTC]
drift_direction: worsening-slowly
depends_on: []
locked_by:
resolved_by:
---

# prek's stash/restore cycle replays a stale, already-resolved patch onto unrelated files

## What I found

Shipping a comment-only fix to `.github/workflows/ldr-to-main-promote-fleet.yml` via
`bash scripts/quickmerge.sh "..." --agent --files '.github/workflows/ldr-to-main-promote-fleet.yml'`:

1. **First run** hit branch-drift (1 commit behind), which failed the commit. The prek hook chain's own log showed:
   `Unstaged changes detected, stashing unstaged changes to /home/ubuntu/.cache/prek/patches/1785361735374-2412589.patch`
   then `Restored working tree changes from /home/ubuntu/.cache/prek/patches/1785361735374-2412589.patch`. After this,
   `git status --short` showed 2 files dirty that this commit never touched:
   - `plans/active/defi_consolidated_closeout_2026_07_18.md`: `last_updated:` (was empty) became
     `last_updated: 2026-06-27\n  2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27 2026-06-27\n  2026-06-27 "2026-07-25" # AO-readiness pass...`
     — a garbled, repeated-date runaway string appended into a YAML scalar, clearly invalid/corrupted content, not
     anything a human or agent would write.
   - `issues/cefi_instruments_store_blank_data_type_residual_2026_07_29.md`: the line
     `author: slot-4 (data_engineering)` was silently deleted from frontmatter.
2. `git restore`'d both files to clean HEAD (verified `git status --short` empty).
3. **Second run**, same command, after successfully rebasing past the branch drift: the prek chain again logged
   `Unstaged changes detected, stashing... /home/ubuntu/.cache/prek/patches/1785362239335-2507555.patch` /
   `Restored working tree changes from ...2507555.patch` — and the SAME 2 files reappeared dirty with the
   **byte-identical** corrupted diff (confirmed via `diff` against the first occurrence).
4. Read the patch file itself (`1785362239335-2507555.patch`) directly: **the corruption is already baked into the patch
   file's own diff content** — this is not prettier or another hook mangling the file live during THIS run; it is a
   stale, previously-captured diff being blindly re-applied.

## Why it matters

- This is silent, unattended corruption of plan-doc content that an agent could easily commit without noticing if they
  run a broad `git add .`/`-A` (banned by workspace rules, but a real risk for anyone who slips) or simply doesn't
  diff-check post-quickmerge output carefully.
- `/home/ubuntu/.cache/prek/patches/` is a **home-level** cache directory, not scoped per-slot or per-repo. Every
  slot/session sharing this host's `ubuntu` user shares this cache. I did NOT confirm cross-repo/cross-slot
  contamination this session (both reproductions were within the same `unified-trading-pm` clone) — but if prek's
  patch-selection logic isn't strictly scoped to `(repo, invocation)` and instead grabs "the newest" or otherwise
  under-scoped patch, the same mechanism could replay one repo's stale stash onto a DIFFERENT repo's working tree.
  Flagging this as the plausible worst case, not a confirmed one.
- Reproduced twice, back-to-back, in the same session — this reads like a standing condition on this slot's prek cache
  right now, not a one-off race.

## Recommended next step (not done here — needs prek/tooling-level investigation, not a doc fix)

**Start from the evidence already gathered** — the 2026-07-30 (slot-1) Progress Log entry below names the exact 9
candidate patch files in `~/.cache/prek/patches/` (2 confirmed-unrelated, 7 confirmed-culprit by content match), with
timestamps, so root-causing doesn't need to re-derive the candidate set from a 160-file directory.

1. Identify why prek's stash-patch mechanism is replaying a stale patch instead of a fresh working-tree snapshot —
   likely a patch-file lookup/cleanup bug (e.g. picking the most-recent-by-mtime file in a shared directory rather than
   the one it just wrote, or never invalidating/deleting consumed patches so a later run's glob still matches an old
   one). Also check the self-perpetuating hypothesis in the same Progress Log entry: do failed/corrupted runs themselves
   seed NEW stale patches with the same bad content, making this a growing cycle rather than fixed debris?
2. Confirm the actual blast radius: is `~/.cache/prek/patches/` scoped by repo path anywhere in its lookup, or genuinely
   global? If global, this needs to move to a per-repo-clone-scoped cache path.
3. Once root-caused, purge `~/.cache/prek/patches/` of stale entries as part of the fix (do NOT do this blind before
   root-causing — a patch file mid-legitimate-use could be live work).

## Todos

- [x] [SCRIPT] P1. **fix_frontmatter.py's stale-continuation-line bug — ROOT-CAUSED + FIXED (slot 16,
      `unified-trading-pm@e37b7ab47`).** `is_field_empty()` only inspected a date field's own line; a pre-existing
      YAML-folded continuation (left over from an earlier corruption event) never got stripped, so each fixer run reset
      the first line while the stale fold kept accumulating underneath it — across enough runs this produces exactly the
      observed multi-repeated-date runaway string. Fixed by adding `_clear_field_continuations()`, called
      unconditionally before setting `last_updated`/`execution_scope`. Confirmed via LIVE reproduction, not just
      source-reading (slot 16's own `quality-gates.sh` Pass-1 run independently corrupted
      `defi_consolidated_closeout_2026_07_18.md` through this exact path; the patched fixer cleaned it). This is a real,
      confirmed bug and a real fix — but see the new P1 below: it is demonstrably not sufficient on its own.
- [x] [SCRIPT] P2. **Out-of-scope collateral-corruption safety net — SHIPPED (slot 16,
      `unified-trading-pm@8132dba77`).** `quickmerge.sh` now snapshots unstaged paths before the commit-hook chain runs
      and auto-`git restore`s any path that is newly dirty AND outside the commit's own `--files` scope. A real, working
      mitigation for the ORIGINAL symptom (collateral damage to a file the commit never touched) — but see the explicit
      gap in the new P1 below.
- [ ] [SCRIPT] P1. **NEW (2026-07-30, slot-1) — the corruption still recurs on IN-SCOPE files; root cause unknown.**
      Confirmed via direct reproduction: this exact field corrupted TWICE MORE on
      `defi_consolidated_closeout_2026_07_18.md`, hours after `e37b7ab47` (the real fix_frontmatter.py fix above) was
      already live in this slot's checkout — so that fix, while genuine, does not explain or prevent this recurrence.
      Both times the file WAS explicitly named in the shipping commit's own `--files` argument (verified against the
      actual invocations, `unified-trading-pm@33fcd528d` and `@36fe18966`), which `8132dba77`'s safety net structurally
      cannot catch — it only reverts paths OUTSIDE `--files` scope, by design. Two live hypotheses, neither confirmed:
      (a) prek's stash/restore has a concurrency blind spot slot 16's single-invocation source read didn't consider —
      many slots run `prek` concurrently against the same shared `~/.cache/prek/patches/`, so even a
      per-invocation-correct mechanism could still race; or (b) a second, still-unidentified mechanism produces the same
      symptom independently of fix_frontmatter.py. Needs a worker to actually stress-test concurrent `prek` invocations
      against this file, not just read source serially — see the 9-patch forensic list + self-perpetuation hypothesis in
      the Progress Log below as a starting evidence base. **UPDATE 2026-07-30 (slot-1) — see the new P1 immediately
      below: the actually-running prek binary on this host turned out to be 5+ months stale and confirmed to predate a
      real, matching upstream bugfix in this exact code path. Hypothesis (b) now has a concrete, named candidate.**
- [ ] [SCRIPT] P1. **NEW (2026-07-30, slot-1) — the actually-invoked `prek` binary is `0.3.1` (2026-01-31), 5+ months
      and ~15 releases stale, and upstream has since fixed a confirmed corruption bug in the exact stash/restore code
      path this issue is about.** `which prek` → `/home/hk/.local/bin/prek` → `prek --version` reports `0.3.1`; its
      mtime (`2026-01-31 18:52:26`) matches 0.3.1's release day exactly, i.e. it was installed once and never touched
      since — no deliberate pin anywhere in the workspace (grepped `.pre-commit-config.yaml`/`*.toml`/codex, zero hits).
      Note `pip show prek` separately reports `0.4.10` — a SEPARATE pip-managed install that is NOT the one on `PATH`;
      the two install channels have drifted and the stale one is the one every hook actually runs through. **Confirmed
      via `gh` against `j178/prek` upstream (the real repo, verified via `gh api repos/j178/prek`):** -
      [j178/prek#2142](https://github.com/j178/prek/issues/2142) / [#2143](https://github.com/j178/prek/pull/2143) ("Fix
      intent-to-add stash restore", merged 2026-06-03, shipped in **v0.4.4**) — a **CONFIRMED, reproducible, fixed**
      bug: when the stash-restore patch fails to apply cleanly, the OLD code (identical in structure to what our 0.3.1
      binary still runs) restored files in the wrong order, corrupting file content on rollback. The PR touches
      `crates/prek/src/cli/run/keeper.rs` — the exact file/mechanism this whole issue is about. Our binary predates this
      fix by 2 major bugfix releases. - [j178/prek#1889](https://github.com/j178/prek/issues/1889) /
      [#1890](https://github.com/j178/prek/pull/1890) ("Stash conflict rollback corrupts git index, causing newly added
      files to be committed empty") — describes a **near-exact match** to our symptom class: an auto-fixing hook (their
      repro used `end-of-file-fixer` / `trailing-whitespace`; ours is `fix_frontmatter.py` — same role) modifies staged
      files while unstaged changes exist elsewhere, prek detects a stash conflict, rolls back via
      `checkout_working_tree(root)` — which checks out from the **current index**, not a saved pre-hook tree snapshot —
      and the rollback can leave a mix of old/new content instead of cleanly one or the other. **This PR was CLOSED
      WITHOUT MERGING** (2026-05-03) after the maintainer said they could not reproduce the general (non-intent-to-add)
      case with a minimal repro; verified directly by fetching current upstream master's `keeper.rs`
      (`gh api repos/j178/prek/contents/...`) — as of today it is STILL the single-arg `checkout_working_tree(root)` (no
      tree-ish parameter), i.e. this fix was never applied upstream in any version, including current `0.4.11`.
      Calibration: treat this as a **plausible, not confirmed** contributing mechanism — the maintainer's inability to
      reproduce it generally (vs. the narrower, confirmed, FIXED intent-to-add case above) means it should not be cited
      as proven. - v0.4.6 ([#2130](https://github.com/j178/prek/pull/2130)) added `--no-stash` / `PREK_NO_STASH=1` / a
      `no_stash` config key — an explicit opt-out for the entire stash/restore mechanism, also unavailable on our stale
      0.3.1 binary. **Recommendation (not executed — host-wide shared binary used by every concurrent slot, needs an
      explicit call, not a unilateral change mid-session):** upgrade `~/.local/bin/prek` to current (`0.4.11` at time of
      writing). This is a strict improvement regardless of which exact mechanism (confirmed #2142 class, or unconfirmed
      #1889 class, or something else) is producing our specific corruption — it cannot make things worse, and it closes
      at least one CONFIRMED bug in the exact code path. If corruption recurs even after upgrading,
      `--no-stash`/`PREK_NO_STASH=1` is available as a stronger fallback that bypasses the risky mechanism entirely (at
      the cost of prek erroring instead of auto-stashing when unstaged changes are present).
- [x] [SCRIPT] P1. **DONE 2026-07-30 (slot-1) — defensive backstop shipped regardless of root cause.** Whatever the
      remaining mechanism turns out to be, this corruption can no longer silently land: `scripts/docs/docspec.py`'s
      `date`-kind field validator (`_validate_value`) was a PREFIX-only check (`len(s)>=10` + dash-position check) that
      a garbled value like `2026-06-27 "2026-07-30"` — this exact signature — sails straight through, since it merely
      STARTS with something date-shaped. Tightened to a full-string `re.fullmatch(r"\d{4}-\d{2}-\d{2}", s)`. Verified:
      zero new violations across the full 1829-doc live corpus (no false positives on legitimately-dated docs), and a
      direct reproduction test using the exact corrupted value hard-fails with a clear message. Gap noted, not fixed
      here (kept this change minimal/low-risk): `last_updated` is only a validated field for `doc_type: plan` in the
      current schema, not `issue` — the same corruption on an issue doc's `last_updated` field would still sail through
      undetected.

## Progress Log

- 2026-07-29 (cicd/general-worker, slot 2): filed after reproducing twice in one session while shipping an unrelated
  workflow-comment fix. Both corruption occurrences safely caught + reverted via `git restore` before commit; nothing
  corrupted landed on `origin/live-defi-rollout`. Not investigated further this session — root cause is a prek-internal
  mechanism, out of scope for a docs/workflow-comment task.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — reproduced twice in one session with the offending
  patch file read directly; root-causing the patch-selection/cleanup logic and scoping the cache path are both
  determinable by a worker. Phase-2 conflict-check: ZERO citations anywhere in the active planning corpus.
- 2026-07-30 (satellite corpus-hygiene pass, slot-4): reproduced 2 MORE times, same exact file + same exact garbled
  `last_updated:` signature (`plans/active/defi_consolidated_closeout_2026_07_18.md`), same host, ~15 min apart in this
  session — brings the confirmed total to 4 occurrences across 2 separate sessions, always the same target file so far
  (not yet confirmed whether that's because this file is disproportionately likely to be mid-edit by a concurrent
  session at corruption time, or a deeper pattern in prek's patch-selection). Both caught + reverted via `git restore`
  before commit; nothing corrupted landed. `~/.cache/prek/patches/` inspected this session: dozens of `.patch` files
  with mtimes spanning this exact session's runtime, confirming the mechanism is actively firing on this host right now,
  not a one-off. Still not root-caused (third-party Rust binary, `prek 0.4.5` — reading its internal source is outside a
  bounded doc-hygiene task's scope); this entry exists purely to strengthen the evidence base for whoever picks up the
  actual root-cause investigation next.

- **2026-07-30 (slot-1, harsh_pc)**: first confirmed occurrence where the corruption actually **landed on
  `origin/live-defi-rollout`** rather than being caught pre-commit — a materially worse instance than the 4 above. While
  repairing this exact same target file's already-garbled `last_updated:` field (a separate task, unrelated to this
  issue), the intended clean single-line fix was verified correct locally (schema check passed, no conflict markers) and
  staged, but the SHIPPED commit (`unified-trading-pm@33fcd528d`) contains a different, still-garbled value
  (`last_updated: '2026-06-27 "2026-07-30"'` — parses as valid YAML, so `check_frontmatter_schema.py` did not catch it;
  caught instead by directly diffing `git show origin/<branch>:<path>` against the intended content). Confirms the
  replay can happen **during the quickmerge/prek run itself** (between `git add` and the final commit), not only as a
  leftover unstaged diff a careless `git add -A` might sweep in — post-ship verification for any file this bug might
  touch needs a real content diff against origin, not just "no conflict markers" / schema-pass. A second quickmerge run
  moments later (unrelated file) re-corrupted the same field a THIRD time locally (reverted to a stale pre-fix value,
  `last_updated: 2026-06-27`, caught before staging). Re-fixed properly this time; re-verified byte-for-byte against
  `git show origin/<branch>:<path>` after shipping, not just schema/conflict-marker checks.

- **2026-07-30 (slot-1, harsh_pc) — CORRECTION to the entry directly above, plus new forensic evidence.** The "re-fixed
  properly, re-verified byte-for-byte" claim in the prior entry was **premature** — the byte-for-byte diff WAS clean at
  the moment it was taken, but the very next `quickmerge.sh` run on this same slot (shipping a completely unrelated
  file) corrupted this field **a second time on origin** — the shipped commit (`unified-trading-pm@36fe18966`) again
  carried the garbled value. This is the **6th confirmed reproduction overall** and the **2nd to actually land on
  `origin/live-defi-rollout`** (not just caught pre-commit), both landed occurrences from consecutive commits by the
  same slot within ~20 minutes of each other, both on the exact same field of the exact same file. A third party's
  follow-up commit (`unified-trading-pm@16ff874e8`) has since cleaned it to a valid (if stale) plain value — current
  state is clean, but this was NOT this session's own fix holding; it was luck of a later, unrelated commit's own prek
  run landing a clean copy.

  **New forensic evidence — the actual stale patch files identified, not just the mechanism described abstractly.** Of
  160 total files in `~/.cache/prek/patches/` (home-level, shared across every slot on this host), filtering for ones
  containing an actual diff hunk header `+++ b/plans/active/defi_consolidated_closeout_2026_07_18.md` narrows to exactly
  9:
  - `1784558226594-3097283.patch`, `1784558229375-3099512.patch` (both 2026-07-20 ~20:07 IST) — **not culprits**:
    legitimate, already-landed historical diffs (`last_updated: 2026-07-18` → `2026-07-20`), unrelated content.
  - `1785396516865-2725083.patch`, `1785396524946-2725720.patch`, `1785396528024-2725977.patch`,
    `1785396539486-2726325.patch`, `1785396547491-2726768.patch` (all today, 12:58:36–12:59:07 IST) — **confirmed
    culprits**: each contains the same garbled `last_updated:` block (the multi-repeated-`2026-06-27`-date runaway
    string) as either context or diff content, timestamps matching exactly when this session's own quickmerge runs were
    executing.
  - `1785399735300-3150463.patch`, `1785399743321-3155622.patch` (today, 13:52:15–13:52:23 IST) — **confirmed
    culprits**: same signature, captured during the second failed-fix run.

  **Mechanistic implication worth flagging for whoever root-causes this**: the culprit patches are not one single piece
  of old debris that will eventually age out — they cluster in tight bursts that line up with THIS session's own
  repeated fix attempts, i.e. each failed fix appears to leave behind a fresh stale patch carrying the same bad content,
  which then becomes available for the _next_ run to wrongly replay. If confirmed, this makes the condition
  self-perpetuating rather than a fixed, shrinking population of old junk — purging today's known-bad patches would stop
  the CURRENT cycle but a future corruption event would seed new ones the same way, until the actual patch-selection bug
  in `prek` itself is fixed.

  **Decision NOT made this session, flagged for the operator/next investigator**: did not delete the 7 identified stale
  patches. Reasoning: `~/.cache/prek/patches/` is genuinely shared host-wide infrastructure (every slot's sessions write
  into it), and while this session's forensic evidence strongly indicates these 7 specific files are stale/superseded
  garbage (their content matches an already-known-corrupted, already-superseded state — not anyone's live legitimate
  work), deleting from a shared cache used by other concurrently-running sessions is a step beyond this task's own scope
  and was left for an explicit operator call rather than done unilaterally.

- **2026-07-30 (slot-1, harsh_pc) — synthesizing the full multi-round history + shipping a defense-in-depth fix.** This
  doc has now been resolved and reopened twice: slot 16 root-caused a REAL bug in
  `scripts/plan-hygiene/fix_frontmatter.py` (stale YAML-folded continuation lines never stripped by `is_field_empty()`,
  accumulating across repeated auto-fixer runs) and shipped a genuine fix (`unified-trading-pm@e37b7ab47`), plus a real,
  working `quickmerge.sh` safety net for collateral damage to out-of-scope files (`unified-trading-pm@8132dba77`) — then
  marked this doc resolved with both todos checked. Slot 4 (satellite corpus-hygiene pass) reopened it after reproducing
  the exact same symptom 2 more times. **This session's own two reproductions (recorded above) happened AFTER
  `e37b7ab47` was already live** — direct evidence that fix_frontmatter.py's bug, while real and fixed, is not the (or
  not the only) cause of the recurring corruption. The critical new distinction found this session: every occurrence
  THIS slot hit had the file explicitly named in the commit's own `--files` argument — the exact case `8132dba77`'s
  out-of-scope safety net was never designed to catch (it only reverts paths OUTSIDE `--files` scope). So the remaining
  open question isn't "does the old mitigation work" (it does, for its own scope) — it's "what still corrupts an
  IN-SCOPE file's content mid-pipeline," and that remains unidentified. Rather than chase that further this session,
  shipped a root-cause-agnostic backstop instead: `scripts/docs/docspec.py`'s date-field validator now requires a full
  `YYYY-MM-DD` match instead of a prefix match, so this exact corruption signature (or any future variant with the same
  shape) hard-fails the commit instead of silently landing, regardless of which upstream mechanism produces it. Verified
  against the full 1829-doc live corpus (zero new violations) and a direct reproduction test. `status` left `open` — the
  underlying recurring-corruption mechanism is still not identified; only the silent-landing consequence is now closed
  off.

- **2026-07-30 (slot-1, harsh_pc) — the stale-binary finding.** Prompted to go back and investigate what was left
  unresolved after the docspec.py backstop shipped. Checked the actual prek binary in use rather than continuing to
  treat it as an opaque black box: `which prek` resolves to `/home/hk/.local/bin/prek`, and `prek --version` reports
  `0.3.1` — released 2026-01-31, with the binary's own mtime matching that exact date, meaning it was installed once
  (the day 0.3.1 shipped) and never upgraded since. Separately, `pip show prek` reports `0.4.10` — a second, unused
  install channel that drifted independently; the one on `PATH`, the one every hook actually runs through, is the
  ~6-month-stale one. No deliberate version pin exists anywhere in the workspace (checked `.pre-commit-config.yaml`,
  `*.toml`, codex — zero hits), so this is simple staleness, not an intentional choice.

  Used `gh api`/`gh pr`/`gh issue` against the real upstream repo (`j178/prek`, confirmed via `gh api repos/j178/prek`,
  8.1k stars, MIT) to read every release's changelog between 0.3.1 and 0.4.11 and grep the commit history of
  `crates/prek/src/cli/run/keeper.rs` (the exact file this whole issue is about) for anything touching stash/restore.
  Found two directly relevant upstream items, cited with full detail in the two new P1 todos above:
  1. **j178/prek#2142/#2143** — a CONFIRMED, reproducible bug ("Content of 'intent to add' files lost after stashed
     changes conflicted with changes made by hook") in this exact code path, fixed in v0.4.4 (2026-06-04). Our binary
     predates the fix.
  2. **j178/prek#1889/#1890** — a proposed fix for a near-exact match to our symptom class (auto-fixing hook modifies
     staged files + unstaged changes elsewhere + stash conflict → rollback checks out from the current, possibly
     already-drifted index instead of a saved pre-hook tree snapshot, mixing old/new content). Confirmed via a direct
     fetch of current upstream master's `keeper.rs` that this fix was **never merged** — `checkout_working_tree()` is
     still single-arg (no tree-ish) in `0.4.11` today, so if this is a real general-case bug (the maintainer said they
     personally could not reproduce it outside the narrower, since-fixed intent-to-add case), it remains open in the
     latest available version too, not just our stale 0.3.1.

  **What this changes about the open P1 above**: hypothesis (b) — "a second, still-unidentified mechanism" — now has a
  concrete, named, evidence-backed candidate instead of being a total unknown. It is not a slam-dunk confirmed root
  cause (the #1889 half is explicitly maintainer-unreproduced), but the #2142 half alone is enough to justify upgrading
  regardless: our binary is definitively missing a fix for a real, confirmed corruption bug in the exact mechanism this
  issue is chasing. **Did not perform the upgrade this session** — `~/.local/bin/prek` is shared, host-wide, non-git-
  tracked infrastructure that every concurrently-running slot depends on; swapping it mid-session without the operator's
  awareness is a materially different kind of action than shipping a scoped code fix inside one repo, so it was left as
  an explicit recommendation (see the todo above) rather than done unilaterally. `status` stays `open`.
