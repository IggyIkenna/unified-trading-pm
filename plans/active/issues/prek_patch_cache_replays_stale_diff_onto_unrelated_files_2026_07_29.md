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
last_updated: "2026-07-31" # own-patched-fork shipped + deployed to 2 hosts, upstream PR prepared (see Progress Log)
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
- [x] [SCRIPT] P1. **DONE 2026-07-30 (slot-8) — concurrency hypothesis (a) actually stress-tested against a live binary,
      not just read about; RULED OUT as the cause of the silent content corruption; a distinct, real, lower- severity
      bug found instead.** Full methodology + results in the Progress Log below. Summary: read
      `crates/prek/src/cli/run/keeper.rs` (`WorkTreeKeeper`/`UnstagedChangesRestorer`) directly from upstream source —
      the stash-patch a process restores is held as an in-memory `PathBuf` on the exact struct that wrote it, never
      re-selected from the shared directory by a rescan/mtime heuristic, so the "picks the wrong stale file" framing in
      hypothesis (a) is not how the mechanism actually works. Built a scratch git repo reproducing the real hook shape
      (a `local`/`system` auto-fixer hook that mutates + re-stages a target file, matching `fix_frontmatter.py`'s
      pattern) and fired genuinely concurrent `prek run` pairs (default/staged-files selection mode — the mode
      `git     commit` actually uses, confirmed via `FileSelection::requires_clean_worktree()`) against the SAME working
      directory, 115 rounds total. Result: **zero silent content corruptions.** The real race (confirmed to fire in 43%
      of tightly-concurrent rounds) is git's own `.git/index.lock` rejecting the second `checkout --`, which makes the
      losing `prek` invocation abort LOUDLY with a clear `fatal: Unable to create '.git/index.lock'` stderr message and
      nonzero exit — not a silent bad write. This is consistent with (does not contradict) the already-confirmed
      #1889-class single-invocation bug from the todo above being the real, sufficient mechanism for the silent
      corruption symptom this issue is chasing.
- [x] [SCRIPT] P1. **DONE 2026-07-30 (slot-1) — `~/.local/bin/prek` upgraded 0.3.1 → 0.4.11 on this host, and BOTH
      candidate upstream bugs directly tested against the new binary (not just read about).** Was `0.3.1` (2026-01-31,
      mtime matched the release day exactly — installed once, never touched since; `pip show prek` separately reported
      `0.4.10`, a second, unused install channel). Downloaded the official `prek-x86_64-unknown-linux-gnu.tar.gz`
      release asset for `v0.4.11` directly from `gh api repos/j178/prek/releases/latest`, verified its published sha256,
      and atomically swapped it into `~/.local/bin/prek` (old binary backed up to scratch first). This is a HOME-level
      path shared by every slot/tab on this host, so all 30 tabs picked up the upgrade in one action; confirmed via
      `prek --version` → `0.4.11`. **Test 1 — j178/prek#2142/#2143 (intent-to-add stash restore), fixed in v0.4.4:**
      reproduced the exact upstream repro (intent-to-add file + conflicting hook rewrite) in an isolated scratch git
      repo against the new binary. Result: **FIXED** — the intent-to-add file's content survived intact (`preserve me`),
      the unstaged patch reapplied correctly (`a=1` / `b = 2`), matching the fixed-version's expected behavior exactly.
      **Test 2 — j178/prek#1889/#1890 (stash-conflict-rollback index corruption), PR closed without merging:**
      reproduced the exact repro from the unmerged PR's own test (`corrupt-index.py`, which desyncs the git index from
      the working tree mid-hook via `git update-index --cacheinfo` + a working-tree write) in a separate scratch repo
      against the same 0.4.11 binary. Result: **STILL BROKEN — CONFIRMED, not just plausible.** `prek run` printed
      `Failed to restore unstaged changes: ... patch does not apply`, and afterward BOTH the working tree AND the index
      entry for `new-file.txt` were silently emptied (`git show :new-file.txt` → empty; `cat new-file.txt` → empty) —
      exactly the "newly added files end up empty" symptom the original issue reported, on the CURRENT latest release.
      **Correction to my own claim two Progress Log entries ago**: I said v0.4.6 added a `--no-stash`/`PREK_NO_STASH`
      opt-out ([#2130](https://github.com/j178/prek/pull/2130)) as an available fallback — checked its actual merge
      state and it is **also CLOSED WITHOUT MERGING**, same as #1890. Verified directly: `prek run --no-stash` on 0.4.11
      errors `unexpected argument '--no-stash' found`. **There is no built-in opt-out for this mechanism in any released
      prek version** — that fallback does not exist. Net effect of the upgrade: closes one confirmed bug (#2142-class),
      does NOT close the other (#1889-class, now confirmed rather than hypothesized), and removes an escape hatch I'd
      incorrectly believed existed. The docspec.py backstop (already shipped) remains the only concrete protection
      against this landing silently, regardless of prek version.
- [x] [SCRIPT] P1. **DONE 2026-07-30 (slot-8) — durable-prevention piece (2) SHIPPED (`agent-orchestrator@4898f88`); (1)
      other-host remediation and (3) upstream contribution deliberately DEFERRED as their own new todos below
      (operator-scope / separate-effort, not this todo's own determinable piece).** Originally filed as NEW (2026-07-30,
      slot-1) — workspace-wide prek version drift: other hosts run different, equally unpatched-for-#1889 versions, and
      nothing detects this.** Grepped every repo in this workspace for prek install/CI references: **CI is NOT
      applicable at all** — zero `.github/workflows/*.yml` files anywhere invoke the `prek` binary (confirmed by direct
      grep across all repos); CI's `quality-gates-v2` runs ruff/pytest/basedpyright/docspec directly against an
      already-committed SHA, where prek's stash/restore mechanism has nothing to do (no unstaged state exists in a CI
      checkout). `unified-trading-pm/.github/workflows/ldr-docs-gate.yml`'s only "prek" mention is a comment citing this
      as the MOTIVATION for why that independent CI-side doc check exists (a different, already resolved/archived issue,
      `prek_plan_hygiene_hook_fail_open_unhooked_clone_2026_07_17.md`, about the hook being _absent_ on a clone, not
      about version staleness). **Other hosts, checked live via read-only SSM (same sanctioned pattern as
      `check-ao-backlog-status.sh`):** - Orchestrator/planning VM (`i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`) — running
      **prek 0.4.8** (installed ~2026-07-07, per `bin -> .local/share/uv/tools/prek/bin/prek` symlink mtime), 3 releases
      behind current. Has the #2142 fix (anything ≥0.4.4 does) but is equally exposed to the confirmed-still-open
      #1889-class bug — version doesn't change that half. This is where most background AO agent commits actually
      happen. - Human-planning VM (`i-0dd9812a96cdda5dc`) — **prek not installed at all**, checked under both the
      default SSM execution context and the `ubuntu` user. A different, arguably more urgent gap for that host
      specifically (zero hook coverage — gitleaks/branch-drift/prettier-autostage all skipped on any commit from there),
      separate from the version-staleness question. - This laptop (`harsh_pc`) — fixed above. - The other operator's
      laptop (`…@gmail.com` identity, per the slot/host commit-attribution split) — not reachable via SSM (no agent on a
      personal machine); needs that operator to run the same check locally. **Root cause of the drift**:
      `agent-orchestrator/scripts/bootstrap_vm.sh` STEP 4.6 installs prek via `uv tool install 'prek>=0.3.0,<1.0.0'` —
      ONE TIME at VM bootstrap. The SemVer range is already wide enough to permit `0.4.11` (no manifest edit needed to
      "unlock" it), but `uv tool install` does not auto-upgrade an already-satisfying install, so every host silently
      freezes at whatever was current the day IT was bootstrapped. `worker-host-preflight.sh`'s existing prek check
      (added by the 2026-06 fix below) is presence-only (`command -v prek`) — it never compares the resolved version
      against anything, so a 5-month-stale binary passes cleanly. A near-identical-sounding but distinct problem was
      already found and fixed in `plans/archive/issues/hook_tooling_version_alignment_across_environments_2026_06_03.md`
      (2026-06-03, RESOLVED) — but that investigation was about prek being **absent** on worker VMs, never about
      installed-but-stale, so this exact dimension was never covered. **Not yet actioned — awaiting an operator decision
      on scope**: (1) one-time remediation — `uv tool install prek     --reinstall` (or `uv tool upgrade prek`) on the
      orchestrator VM + human-planning VM (if prek should be installed there at all) + the other operator's laptop; (2)
      durable prevention — extend `worker-host-preflight.sh`'s presence-only check to an actual version comparison
      against a floor in `workspace-constraints.toml` (currently `prek>=0.3.0,<1.0.0`, itself just a permissive range,
      not an enforced floor); (3) since neither (1) nor (2) closes the confirmed-still-open #1889-class bug, the durable
      protection layer stays the docspec.py backstop already shipped, plus a possible high-leverage option: we now have
      the exact minimal repro the upstream maintainer asked for on #1889 and never received — contributing it back
      (reviving #1890 or filing fresh) could get a REAL upstream fix merged rather than us re-deriving one internally.

      **What slot-8 actually shipped for piece (2), 2026-07-30**: `worker-host-preflight.sh`'s prek check (STEP 4c) now
                                              parses `prek --version` and FAILs (not just WARNs) below a `0.4.4` floor — the confirmed j178/prek#2142 fix
                                              version — with a remediation message (`uv tool install prek --reinstall` / `uv tool upgrade prek`); verified live
                                              on this host (`prek 0.4.12` → `OK: prek 0.4.12 >= floor 0.4.4`) and unit-tested the version-compare logic
                                              (`sort -V -C`) against `0.3.1`/`0.4.3`/`0.4.4`/`0.4.8`/`0.4.12`/`1.0.0` fakes — correctly rejects only the two
                                              below-floor cases, including the `0.4.12 vs 0.4.4` lexical trap a naive string compare would get wrong.
                                              `bootstrap_vm.sh` STEP 4.6's `uv tool install` pin raised `0.3.0` → `0.4.4` to match, so a freshly-bootstrapped VM
                                              lands compliant. **Deliberately scoped OUT of this change** (left as new todos below, not silently dropped):
                                              (a) did NOT touch `workspace-constraints.toml`'s `prek` entry or the ~6 repos' `pyproject.toml` `prek>=0.3.0,...`
                                              dev-dependency pins — that file is machine-generated from the TIGHTEST pin across repos
                                              (`resolve-canonical-versions.py`, header says "do not edit by hand") and governs a DIFFERENT thing (the `prek`
                                              PyPI package as an importable dev-dependency) than the `uv tool install`-managed hook-runner BINARY this todo is
                                              actually about; bumping it would mean editing 6 repos' pyproject.toml + regenerating + `uv lock` per repo, a much
                                              larger and only tangentially-related footprint than the floor-enforcement fix itself, so it was left alone rather
                                              than folded in speculatively. (b) did NOT run `uv tool install --reinstall`/`--upgrade` against the already-running
                                              orchestrator VM (`prek 0.4.8`, still passes the new `>=0.4.4` floor so it isn't urgent) or the human-planning VM
                                              (prek absent entirely — separate gap) — mutating an already-running shared host's tool-install state mid-session
                                              is a materially different, operator-aware action than a scoped repo code change, consistent with slot-1's same
                                              call earlier in this doc; filed as its own `[OPERATOR]`-tagged todo below instead. (c) did NOT pursue the upstream
                                              #1889 contribution — a separate, open-ended research effort, also filed as its own todo below.

- [x] [OPERATOR] P2. **RESOLVED 2026-07-31 (slot-1, harsh_pc) — this todo's premise (a stock version upgrade is
      sufficient) turned out to be WRONG, so what got shipped is a different and stronger fix than what was asked.**
      Rather than `uv tool upgrade prek` (which would land stock `0.4.11` — confirmed by direct reproduction to STILL
      carry the #1889-class index-corruption bug), root-caused the actual mechanism (see keeper.rs analysis in the P1
      above), wrote a 34-line fix against `crates/prek/src/cli/run/keeper.rs`, and proved it against a real regression
      test that fails on stock upstream master and passes with the fix
      (`restaging_hook_does_not_discard_unstaged_changes`, upstreamed — see below). Built a fully-static
      `x86_64-unknown-linux-musl` binary (glibc-independent — the naive `cargo build --release` needs `GLIBC_2.39` and
      would not run on an older distro) and macOS binaries via a fork's CI, published as
      [`IggyIkenna/prek` v0.4.12](https://github.com/IggyIkenna/prek/releases/tag/v0.4.12) (every binary checksum-
      verified against the harness — `clean=5 corrupt=0` — before publishing, not just version-bumped). **Installed +
      verified on the two hosts this todo named that are reachable from this session:** - **This laptop** (`harsh_pc`) —
      atomically swapped `~/.local/bin/prek` (0.3.1 → patched 0.4.12; covers all ~30 tabs sharing this one binary).
      Verified: `clean=5 corrupt=0`. - **Orchestrator/planning VM** (`i-0c9b283b31d6b5ca7`) — via
      read-only-becomes-write SSM `send-command` (download + sha256-verify + atomic install, stock `0.4.8` backed up
      alongside), same fresh binary. Verified LIVE ON THE VM ITSELF (not just claimed): fetched the harness and ran it
      there — `clean=5 corrupt=0`. **Genuinely still open, not resolved by this**: the human-planning VM decision below
      (split to its own line, unchanged), and the other operator's laptop (see below — dispatched to that operator
      directly, not resolved by a worker).
- [ ] [OPERATOR] P2. **SPLIT 2026-07-31 (slot-1) from the todo above — does prek belong on the human-planning VM at
      all?** `i-0dd9812a96cdda5dc` has no prek installed under any checked user account (default SSM context or
      `ubuntu`), confirmed via the same read-only SSM check used for the orchestrator VM. This is a decision, not a
      remediation: if that VM is meant to be interactive-only with no direct commits, absence may be correct and this
      todo should close as not-applicable; if commits do happen from there, it needs `IggyIkenna/prek` v0.4.12 installed
      the same way as the two hosts above (command ready, ~30s, blocked only on this decision).
- [ ] [OPERATOR] P3. **NEW 2026-07-31 (slot-1) — the other operator's laptop: instructions sent directly, action still
      pending confirmation.** Not reachable via SSM (personal machine, no agent), so this can't be verified from a
      worker session. The operator sent Ikenna a message directly (not routed through this doc) with: the harness to
      self-check (`clean=3 corrupt=2` on stock, `clean=5 corrupt=0` on a safe build), the `aarch64-apple-darwin` binary
      from the same `v0.4.12` release (no compiling needed), and an explicit warning not to `uv tool upgrade`/
      `brew upgrade` afterward (that would silently restore the broken stock build). Close this once confirmed.
- [x] [SCRIPT] P3. **DONE 2026-07-31 (slot-1) — the worker-bounded piece (build + prove a minimal repro, prepare the
      upstream contribution) is complete; contribute the j178/prek#1889 minimal repro upstream (item (3) from the todo
      above, split out).** Forked `j178/prek` (as `IggyIkenna/prek`), wrote a Rust regression test in upstream's own
      style (`restaging_hook_does_not_discard_unstaged_changes` in `crates/prek/tests/run.rs`) — confirmed it FAILS on
      current upstream `master` with the exact silent-loss content shown in the assertion diff, and PASSES with the
      34-line `keeper.rs` fix applied. This is precisely the deterministic reproduction the maintainer asked for on
      #1889 and never received. Pushed to `IggyIkenna/prek@fix/keeper-rollback-baseline-pr`. **Remaining, NOT a worker
      task**: opening the PR itself needs one click from an account with write access to `j178/prek` (a fine-grained PAT
      without cross-repo PR-creation scope can push a branch but not open the PR) —
      <https://github.com/j178/prek/compare/master...IggyIkenna:prek:fix/keeper-rollback-baseline-pr?expand=1> already
      has the branch + prefillable body ready. Already communicated directly to the operator; not re-filed as a separate
      todo since it's a 5-second human click, not open-ended work.
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
- [ ] [SCRIPT] P3. **NEW (2026-07-30, slot-8) — `~/.cache/prek/patches/` has no cleanup path at all, by design; not
      urgent (6.7MB / 520 files today) but worth a bounded retention decision.** Found while stress-testing concurrency
      (see Progress Log): `UnstagedChangesRestorer::restore()` in `keeper.rs` never deletes a patch file after
      successfully applying it — every stash a hook run needed is kept forever, on the happy path, not just on
      failure/race. Confirmed `prek cache gc` (the one cache-pruning command prek ships) does NOT touch `patches/` — ran
      it directly against a populated isolated `PREK_HOME`, output was `Nothing to clean` with the patches still present
      after. This fully explains the large, ever-growing patch population on this host WITHOUT needing the
      "self-perpetuating corruption" hypothesis from the todo above (that hypothesis isn't disproven, just not required
      — normal, correct runs also grow this directory unboundedly). Separately, confirmed the race in the todo above's
      losing side leaves behind a patch file that is structurally _guaranteed_ orphaned:
      `UnstagedChangesRestorer::clean()` returns `Err` (propagated via `?`) before constructing the
      `Self { patch: Some(patch_path), .. }` struct when `checkout_working_tree` fails, so that instance's `Drop`-based
      `restore()` never runs for it. Recommended next step (not done here — a scoped hygiene decision, not a code fix):
      decide a bounded retention policy for this HOME-level, multi-slot-shared directory (e.g. a low-priority cron
      deleting `*.patch` files older than N days) and wire it in, since prek itself provides no such mechanism today
      (repo: `unified-trading-pm`, likely alongside the other host-maintenance cron scripts).

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

- **2026-07-30 (slot-1, harsh_pc) — operator approved the upgrade; tested it directly instead of trusting the
  changelog.** Downloaded and sha256-verified the official `v0.4.11` release asset, atomically swapped
  `~/.local/bin/prek` (0.3.1 → 0.4.11, covers every tab on this host). Rather than assume the changelog-cited fixes
  actually apply here, built two isolated scratch-repo reproductions of the two candidate upstream bugs and ran them
  against the new binary directly: **#2142's intent-to-add case is genuinely fixed**; **#1889's index-corruption case is
  CONFIRMED still broken** on the very binary now installed (not merely plausible anymore — reproduced the emptied
  index + working-tree entry directly). Also caught and corrected my own error from the entry above: I'd claimed
  `--no-stash`/`PREK_NO_STASH` (v0.4.6, #2130) was an available fallback; checking its actual GitHub state shows that PR
  was **also closed without merging** — `prek run --no-stash` on 0.4.11 errors as an unrecognized flag. No opt-out for
  this mechanism exists in any released version.

  Followed the operator's next ask (blast radius before a workspace-wide rollout decision) by checking every other host
  this workspace runs on. **CI needs nothing** — confirmed via full-workspace grep that no `.github/workflows/*.yml`
  anywhere invokes the `prek` binary; CI validates an already-committed SHA where prek's unstaged-changes mechanism is
  structurally not in play. **Orchestrator VM** (`i-0c9b283b31d6b5ca7`, checked read-only via SSM, same pattern as
  `check-ao-backlog-status.sh`): `prek 0.4.8`, 3 releases behind, has the #2142 fix but not immune to #1889. **Human-
  planning VM** (`i-0dd9812a96cdda5dc`, same SSM check): prek is not installed there at all — a separate, more basic gap
  (zero hook coverage on any commit from that host), independent of version staleness. **Other operator's laptop**: not
  reachable via SSM, needs a local check by that operator. Root cause of the drift, confirmed by reading
  `agent-orchestrator/scripts/bootstrap_vm.sh` + `worker-host-preflight.sh`: prek installs once per host via
  `uv tool install 'prek>=0.3.0,<1.0.0'` at bootstrap and is never re-checked for freshness — the preflight assertion is
  presence-only (`command -v prek`), never a version comparison — so every host silently freezes at whatever was current
  the day it bootstrapped, with nothing detecting the drift. This is a new dimension of a problem already investigated
  once (`plans/archive/issues/hook_tooling_version_alignment_across_environments_2026_06_03.md`, 2026-06-03, RESOLVED) —
  but that pass was about prek being _absent_, never about installed-but-stale, so it never built a freshness check.
  Reported the full picture to the operator; awaiting their call on scope (remediate other hosts now vs. also build the
  durable version-check vs. pursue an upstream fix for #1889 using the repro we now have) before doing anything beyond
  this host.

- **2026-07-30 (slot-8, host `ip-172-31-5-118`) — the concurrency hypothesis, actually stress-tested.** Picked up the
  open P1 asking a worker to stress-test concurrent `prek` invocations rather than read source serially. Did both, in
  that order.

  **Source read first** (`crates/prek/src/cli/run/keeper.rs` + `run.rs`, fetched directly from `j178/prek` upstream via
  `gh api repos/j178/prek/contents/...?ref=v0.4.11` — this host's actual binary reports `prek 0.4.12`, one patch ahead
  of the latest tagged GitHub release at investigation time, but the structural pieces below are architectural, not
  release-note items, and were independently confirmed against the real running 0.4.12 binary in the stress test itself,
  not just the 0.4.11 source text): `WorkTreeKeeper::clean()` is only invoked when
  `FileSelection::requires_clean_worktree()` is true, which is `Default`/`Diff` selection (i.e. the mode `git commit`'s
  installed hook actually uses) — NOT `--all-files`/`--files` (this cost one wasted round of testing: an initial
  `prek run --all-files` stress pass never triggered the stash path at all, because that selection mode skips it by
  construction). Once corrected to default selection: the patch a process restores is a `PathBuf` held on the
  `UnstagedChangesRestorer` struct instance that wrote it — never re-derived from a directory scan/mtime-newest lookup —
  so the "prek picks up a DIFFERENT, stale patch file" framing in the open hypothesis is not how the code works; there's
  no file-selection step to race on. Also found (not previously documented): a `LockedFile::acquire()` cross-process
  lock DOES exist in `fs.rs`, but `store.rs` only takes it for the store's own `.lock` (hook-environment
  installs/downloads) — nothing locks the `WorkTreeKeeper` git working-tree clean/restore cycle itself, so if two `prek`
  processes DO run against the same working directory concurrently, nothing in prek serializes them.

  **Then built and ran the actual stress test**, since a race being structurally _possible_ doesn't mean it produces
  _this_ symptom. Scratch repo (`~/.claude-configs/.../scratchpad/prek-concurrency-test/repo`, deleted nothing from any
  shared path — all synthetic) with a `local`/`system` `.pre-commit-config.yaml` hook shaped like the real culprit class
  described in this doc (`fixer.sh`: mutates a `last_updated:`-style field on a target file and re-`git add`s it,
  mirroring `fix_frontmatter.py`'s auto-fix-and-restage pattern), plus a second file carrying a genuinely unstaged edit
  to force the stash path. Fired pairs of `prek run --hook-stage pre-commit` (default file-selection) truly concurrently
  (backgrounded, `wait`ed) against the SAME working directory, snapshotting file content every round: 30 rounds with
  only the target file's own unstaged diff, then 60 more (115 total incl. an earlier 25-round dry run) with the target
  file STAGED (matching "file explicitly named in `--files`" from the open todo) plus a second file carrying the
  unstaged diff, matching the doc's own "hook modifies staged files + unstaged changes elsewhere" phrasing most closely.

  **Result: zero silent content corruptions across all 115 rounds** (verified per-round: exact expected line count +
  exactly one `last_updated:` occurrence, no duplicated/garbled/truncated content). The race is real and reproducible —
  26/60 rounds (43%) in the final batch hit it — but it manifests as git's OWN `.git/index.lock` rejecting the second
  process's `checkout --` with
  `fatal: Unable to create '.../.git/index.lock': File exists. Another git process seems to be running...`, which
  propagates as a hard `Err` out of `UnstagedChangesRestorer::clean()` — the losing process aborts LOUDLY (nonzero exit,
  unmistakable stderr, no hooks even run) rather than silently landing bad content. This is a negative result for
  hypothesis (a) specifically as an explanation for the SILENT corruption symptom: it doesn't contradict or diminish the
  already-confirmed #1889-class single-invocation bug two entries above (reproduced independently, on an isolated
  non-concurrent repo, by slot-1) — if anything it makes that bug look more clearly sufficient on its own, since the
  concurrency angle doesn't add a silent-failure mode on top of it.

  **One genuine new finding fell out of building this test, unrelated to the corruption symptom itself** — filed as its
  own new P3 todo above rather than folded into this narrative per the "every follow-up is a todo" rule:
  `~/.cache/prek/patches/` has no cleanup path at all. `keeper.rs`'s `restore()` never deletes a patch after applying
  it, even on the fully-successful happy path, and `prek cache gc` (checked directly: ran it against a populated
  isolated `PREK_HOME`, got `Nothing to clean`, files still there afterward) doesn't touch `patches/` either. This alone
  explains this host's 520-file / 6.7MB `patches/` population without needing the "self-perpetuating" hypothesis from an
  earlier entry — though that hypothesis isn't disproven, it's just not required to explain the raw count. Not urgent
  (6.7MB), filed P3.

  **Cache hygiene note**: my first test pass accidentally pointed `PREK_HOME` at the real shared `~/.cache/prek` (the
  default) instead of an isolated scratch path, writing 52 synthetic patch files into the same directory every slot on
  this host shares. Caught it, verified all 52 by exact filename + content (none referenced any real workspace path, all
  referenced only the synthetic scratch repo), deleted exactly those 52 by explicit filename list (not a directory-tree
  delete), and re-ran all further rounds against an isolated `PREK_HOME` under scratch. Net effect on the shared cache:
  zero (back to the pre-test 520-file count before this todo, now 520 again after the P3 finding's own — separately
  isolated — testing).

- **2026-07-30 (slot-8, host `ip-172-31-5-118`) — durable-prevention piece (2) shipped from the workspace-wide-drift
  todo; scope split for the remaining two pieces.** Picked up the open P1 that was "not yet actioned — awaiting an
  operator decision on scope" (three sub-parts: remediate other hosts, add a durable version-floor check, pursue an
  upstream fix). Rather than block on the whole bundle, split it: shipped the one piece that is fully bounded and
  determinable by a worker alone (the preflight version-floor check), and split the other two into their own
  `[OPERATOR]`/research-tagged todos instead of leaving the parent todo open indefinitely or guessing at the
  operator-gated pieces.

  Shipped `agent-orchestrator@4898f88`: `worker-host-preflight.sh`'s prek check now parses `prek --version` and FAILs
  below a `0.4.4` floor (the confirmed j178/prek#2142 fix version) instead of only checking presence; `bootstrap_vm.sh`
  STEP 4.6's `uv tool install` pin raised to match. Verified live on this host (`prek 0.4.12` passes) and unit-tested
  the `sort -V -C` version-compare against 6 representative version strings (0.3.1 stale, 0.4.3 one-patch-below, 0.4.4
  exact floor, 0.4.8 orchestrator-VM's actual version, 0.4.12 this-host's actual version, 1.0.0 future-major) — all
  classified correctly, including the `0.4.12 vs 0.4.4` case a naive lexical string compare would get wrong
  (`"0.4.12" < "0.4.4"` lexically, but not under `-V`). Ran Pass-1 `quality-gates.sh` (harness-backgrounded, not `nohup`
  — the cicd role doc's own `nohup ... &` example is superseded by the newer orphan-reap HARD RULE in `worker.md`) and
  shipped via `quickmerge --agent --files 'scripts/bootstrap_vm.sh scripts/worker-host-preflight.sh'`.

  Explicitly did NOT: touch `workspace-constraints.toml`'s `prek` entry or the ~6 repos' `pyproject.toml` `prek`
  dev-dependency pins (that machinery governs a different thing — the importable PyPI package, not the
  `uv tool install`-managed binary — and bumping it means a much larger 6-repo footprint than this fix, so it's split
  out as a separate, lower-priority chore rather than folded in speculatively); did NOT upgrade the orchestrator VM
  (already passes the new floor) or touch the human-planning VM (prek absent — a distinct, more basic gap) — mutating an
  already-running shared host mid-session is the same category of action slot-1 already deferred earlier in this doc;
  did NOT pursue the upstream #1889 contribution. Filed both as new todos above (`[OPERATOR]` P2 for the other-host
  remediation since it touches live shared infra; plain `[SCRIPT]` P3 for the upstream contribution since it's bounded,
  non-operator-gated research work).

- **2026-07-31 (slot-1, harsh_pc) — the fix, built and deployed, with the operator's explicit go-ahead at each
  shared-infra step.** Picked up exactly the two things slot-8 split out and left open above: the host remediation
  (`[OPERATOR]` P2) and the upstream contribution (`[SCRIPT]` P3).

  **Root-caused the #1889-class bug precisely, from our OWN hook chain rather than upstream's abstract description.**
  Read `.pre-commit-config.yaml` + `scripts/hooks/prettier-autostage.sh` directly: the hook `git add`s the files it
  reformats, so the index moves mid-hook-run. Built a 4-scenario harness modeling that exact chain
  (`scripts/hooks/prek-keeper-fix/prek-corruption-harness.sh`) — confirmed via a controlled A/B (hook re-stages vs.
  doesn't) that `git add` inside the hook is the precise trigger, not merely "a hook exists" or "an unrelated file is
  dirty" (those alone are clean). In `keeper.rs`: `clean()` computes the pre-hook tree via `git write-tree` and discards
  it; the conflict-rollback path then checks out from the CURRENT index instead, which the hook has already moved. Wrote
  the fix (34 lines): keep the tree, roll back to `git checkout <tree> -- <root>`.

  **Verified with more rigor than "the harness passes"**: built the patched binary locally (Rust toolchain, ~90s),
  confirmed `clean=5 corrupt=0`; ran upstream's OWN full test suite against a pristine-vs-patched control (94/41 vs.
  93/42 — the single delta, `perl::additional_dependencies`, passes deterministically in isolation and is cpan
  flakiness, not the patch — every one of the 42 failures is an uninstalled language toolchain, none touch `keeper.rs`);
  confirmed `prettier-autostage`'s normal auto-stage path is byte-identical patched vs. unpatched.

  **Two portability findings that would have quietly broken this for other hosts/operators if skipped:**
  1. A default `cargo build --release` binary requires `GLIBC_2.39` — would not run on any older Ubuntu, while
     upstream's own official binary needs only `2.16`. Rebuilt `--target x86_64-unknown-linux-musl`: fully static, zero
     glibc dependency, verified `clean=5 corrupt=0`.
  2. Ikenna is on an M-series Mac — a Linux host cannot cross-compile `aarch64-apple-darwin`. The fork
     (`IggyIkenna/prek`) inherits upstream's `cargo-dist` `release.yml`, which builds all 12 targets including that one
     via GitHub Actions (free — the fork is public). The automated `host`/publish job itself is gated on a Docker-image
     job that fails on a fork (no registry credentials) and never completes, so the tag never auto-publishes; worked
     around it by downloading the already-built, already-checksum-passing artifacts from the run and publishing the
     GitHub Release manually. Version chosen was `0.4.12-uts.1` first — invalid, because prek ships as a maturin Python
     wheel and that suffix isn't valid PEP 440 (Rust SemVer accepted it and built fine; the wheel job didn't) —
     corrected to plain `0.4.12`, rebuilt, republished.

  **Deployed + verified on every host reachable this session** (see the resolved `[OPERATOR]` P2 above for detail): this
  laptop and the orchestrator VM, both atomic-swapped, both checksum-verified before install, both re-verified with the
  harness AFTER install (not just "the version string changed"). Split what remains into two honest, separate
  `[OPERATOR]` todos rather than one bundle: the human-planning VM (a decision, not a remediation — prek isn't installed
  there at all) and Ikenna's laptop (dispatched directly to him by the operator, outside this doc, not resolved by a
  worker).

  **Upstream contribution**: initially opened from a wrong account, closed and reopened correctly per the operator's
  explicit correction, now sitting as a ready branch + PR body one click away from being a real PR — see the resolved
  `[SCRIPT]` P3 above.

  **One coincidental naming note worth flagging, not a real collision**: slot-8's stress test (entry above) observed
  upstream's own unreleased `master`-branch `Cargo.toml` already reporting `0.4.12` at the time they checked — an
  upstream internal dev-version bump after cutting `v0.4.11`, unrelated to this session's own choice of `0.4.12` for the
  fork build. They're different repos/tags (`IggyIkenna/prek@v0.4.12` vs. any future real `j178/prek@v0.4.12`), so
  there's no actual binary collision — but if upstream tags a real `0.4.12` before this fork is retired, a bare
  `prek --version` string alone won't disambiguate which one a host is running; `prek --version` on the fork build also
  prints the commit hash, which does.

  **Net status**: the docspec.py backstop (P1 above) and this fix together close both the silent-landing consequence and
  (on every host running the patched build) the actual mechanism. `status` stays `open` — genuinely open pieces remain
  (human-planning VM decision, Ikenna's confirmation, the upstream PR click), each now its own precise, non-stale todo
  rather than folded into a compound one.

- **2026-08-02 (slot-15, data_engineering craft) — 2 more reproductions on this slot's host, both caught + restored
  before commit; nothing landed.** Shipping an unrelated plan-archival change via `quickmerge --agent --files`, two
  files never named in `--files`
  (`plans/archive/issues/instruments_backfill_launcher_missing_sports_provider_passthrough_2026_08_01.md`,
  `plans/active/issues/mtds_live_smoke_vm_name_exceeds_gcp_limit_2026_08_01.md`) appeared dirty twice — once after a run
  I killed via an over-short client-side timeout (expected: the run's own restore step never got to execute), and once
  again after a SECOND, uninterrupted run that completed and reported "✅ Landed". The diff itself is milder than the
  garbled-runaway-string signature above — a clean `fix_frontmatter.py`-shaped normalization (adds
  `execution_scope`/`drift_direction`/`depends_on`, drops a stray `author:` line) rather than corrupted YAML — but it is
  the same underlying symptom: stale unstaged state from elsewhere on this shared host being replayed onto files outside
  the commit's own scope. The second occurrence is the more informative data point: the run was NOT interrupted, so the
  collateral-corruption safety net (`unified-trading-pm@8132dba77`, todo 2 above) either isn't catching this particular
  flavor of collateral (a "clean" auto-fix diff, not a garbled one — possibly outside whatever content-shape the safety
  net's detection logic expects) or isn't installed/active on this host/session. Not investigated further (out of scope
  for an unrelated archival task) — both files `git restore`'d clean before commit, confirmed via
  `git status --porcelain` empty post-restore.
