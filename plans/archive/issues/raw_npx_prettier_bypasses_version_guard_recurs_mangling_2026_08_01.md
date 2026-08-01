---
doc_type: issue
title:
  A raw `npx prettier --write` call bypasses the `>=3.9.5` version guard and resolves an unpinned 3.6.2, re-triggering
  the already-"fixed" 2026-07-14 emphasis-mangling corruption class — CLAUDE.md never says NOT to call it directly
summary: >-
  While reconciling a large context_scope frontmatter backfill (2026-08-01), I ran `npx prettier --write <files>`
  directly, several times, across dozens of plan docs — not realizing this workspace has a dedicated, version-guarded
  wrapper (`scripts/hooks/prettier-autostage.sh`, pinning `>=3.9.5` after a proven 2026-07-14 incident where prettier
  `<3.9.5` deterministically rewrites underscore identifiers as asterisks in prose:
  `asset_group`→`asset*group`/`data_type`→`data*type`/etc.). Bare `npx prettier` in this environment resolves **3.6.2**
  — no local `node_modules/.bin/prettier` exists in this checkout, no pinned version, so npx falls through to whatever
  its cache/registry gives it. This silently corrupted ~15-17 docs across `plans/active/`. Caught before any of it
  reached the shared branch (verified `HEAD` clean, scanned all upstream commits with zero hits) — the corrupted local
  working-tree copies were discarded (`git checkout HEAD --`), not shipped. `check_prettier_mangling.sh` (the backstop
  gate) is only wired into the prek pre-commit hook path, not into an ad-hoc interactive `npx prettier --write` call —
  so an agent (or human) who reaches for prettier directly, rather than via the hook or `quality-gates.sh`, gets zero
  warning until the pre-commit gate (if reached at all — this incident's corruption was all in the pre-stage working
  tree, one step before that gate would even run).
status: resolved
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prettier, corruption, mangling, version-guard, tooling-gap, process, big-finding, commit-hygiene]
related:
  [
    /plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md,
    /scripts/hooks/prettier-autostage.sh,
    /scripts/plan-hygiene/check_prettier_mangling.sh,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
priority: P2
parent_epic: agent_operating_framework_master
source: >-
  Self-caught 2026-08-01 while reconciling a context_scope backfill — noticed an unusually large diff on one file,
  traced a mangled span (`asset*group`) back to my own `npx prettier --write` calls earlier in the same session, then
  confirmed via `npx prettier --version` = 3.6.2 (below the documented 3.9.5 floor) and a corpus-wide
  `check_prettier_mangling.sh` + a broader heuristic grep.
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
drift_direction: advance-code
resolved_by: "2026-08-01"
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md,
    /scripts/hooks/prettier-autostage.sh,
  ]
---

# Raw `npx prettier --write` resolves an unpinned, corrupting version — the guard only lives in one call path

## What happened

1. This session ran `npx prettier --write <file>` directly (not through `scripts/hooks/prettier-autostage.sh` or
   `quality-gates.sh`) on dozens of plan docs while reconciling a large context_scope backfill.
2. `npx prettier --version` in this checkout resolves **3.6.2** — no local `node_modules/.bin/prettier`, no version pin
   on the bare invocation. Per the 2026-07-14 incident doc, any prettier `<3.9.5` with this workspace's
   `proseWrap: always` deterministically rewrites underscore identifiers as asterisks in prose (and can collapse
   paragraphs) — proven repro: 3.8.4 mangles, 3.9.5 is clean.
3. Result: ~15-17 docs picked up real corruption (`asset_group`→`asset*group`, `paper_run_handler`→`paper*run_handler`,
   `rebuild_defi_manifest`→`rebuild*defi_manifest`, etc.) in the local working tree.
4. Caught via `scripts/plan-hygiene/check_prettier_mangling.sh` (run manually, not automatically) plus a broader ad-hoc
   heuristic grep for the same signature (the curated checker's pattern list is deliberately narrow — it missed at least
   one instance, e.g. `defi*delta_one_funding_oi_...`, that the broader heuristic caught).
5. **Verified NOT shipped**: `HEAD` was clean for every sampled file, and all upstream commits from this session's work
   were scanned with zero hits. The corrupted local copies were discarded (`git checkout HEAD --`) rather than
   committed.

## Why it's a gap, not just an operator mistake

- `scripts/hooks/prettier-autostage.sh` already has the correct logic (prefer a pinned local binary, else
  `npx -y prettier@3.9.5`, else skip with a warning) — but nothing stops a direct `npx prettier --write` call from
  bypassing it entirely. The workspace's own CLAUDE.md says "**Prettier** `.md/.json/.yaml/.ts*` before commit" with no
  pointer to the guarded wrapper or a warning against the bare command.
- `check_prettier_mangling.sh` is a real backstop, but it is only exercised via the prek pre-commit hook — there is no
  standing reminder to run it after an ad-hoc format pass, and this incident's corruption never even reached a commit
  attempt (caught by a manual, self-initiated re-check, not by any automated gate).

## Recommended fix

- [x] [DOCS] P2. Add an explicit line to CLAUDE.md's git-discipline section (and/or
      `/codex/06-coding-standards/quality-gates.md`): **never run a bare `npx prettier`/`prettier` command on this
      corpus** — always go through `scripts/hooks/prettier-autostage.sh` (or accept the pre-commit hook's own pass), or
      if a manual format pass is genuinely needed, pin explicitly (`npx -y prettier@3.9.5`) and immediately follow it
      with `bash scripts/plan-hygiene/check_prettier_mangling.sh <files>` before staging. Cite this doc + the 2026-07-14
      incident doc as the reason.
- [x] [SCRIPT] P3. Consider whether `check_prettier_mangling.sh`'s curated pattern list should be widened (or a second,
      broader-but-noisier mode added) — this incident's manual broader heuristic (`[a-zA-Z0-9]\*[a-zA-Z_]+`) caught real
      corruption the curated list missed (`defi*delta_one_funding_oi_...`). Weigh against the script's own stated design
      goal (low false-positive rate); a wider mode could be opt-in (`--strict`) rather than replacing the default.

## Progress Log

- **2026-08-01**: Filed after self-catching and remediating (discarded 15-17 corrupted docs locally, never shipped; 90
  clean docs from the same backfill effort landed as `unified-trading-pm@9bf4fd50a`). Not fixed here — the doc-only
  hardening (todo 1) and the checker-widening question (todo 2) are both quick but distinct follow-ups, left as open
  todos rather than actioned inline.
- **2026-08-01 (both todos closed)**: Todo 1 — added the warning to `cursor-configs/CLAUDE.md`'s git-discipline bullet
  (condensed an unrelated historical sentence elsewhere in the same file to stay under the 40KB hard cap — was
  40,958/40,960 B, 2 B of headroom, before this edit) and fixed THREE bare `npx prettier --write` call sites inside
  `/codex/06-coding-standards/quality-gates.md` itself (lines ~1244/1257/1901 — the codex SSOT was recommending the
  exact dangerous pattern this doc is about) to use `scripts/hooks/prettier-autostage.sh`, plus a explicit callout
  citing both incident docs. Todo 2 — added an opt-in `--strict` flag to `check_prettier_mangling.sh`
  (`STRICT_PAT='[a-zA-Z0-9]\*[a-zA-Z_]+'`), never wired into the default precommit gate. Verified: (a) full-corpus
  default-mode run stays clean (`✅ no prettier emphasis-mangling in 1783 file(s)`, no regression), (b) a synthetic test
  file containing a `defi*delta_one_funding_oi_something`-shaped span plus deliberate legit constructs (bold `**text**`,
  a backtick-wrapped glob, `8*3600` arithmetic, a backtick-wrapped wildcard filename) — default mode stays clean (as
  expected, matches this incident's real miss), `--strict` catches exactly the mangled span and flags none of the legit
  constructs. All three edited files (`CLAUDE.md`, `quality-gates.md`, this doc) formatted with the PINNED
  `npx -y prettier@3.9.5` and re-verified clean via the checker itself.
