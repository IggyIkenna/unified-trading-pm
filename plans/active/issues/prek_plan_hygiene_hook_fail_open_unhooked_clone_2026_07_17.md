---
doc_type: issue
title: >-
  The prek plan-hygiene gate is fail-open — a clone without hooks (or with an unresolvable sweep path) ships broken
  frontmatter straight to LDR, where it reds EVERY PM PR until someone repairs it
summary: |
  2026-07-17 13:38Z: commit `4a7816269` (`ikennaigboaka [slot-3·laptop]`, "docs(issues): file 2 issues…") direct-pushed
  two issue docs with broken frontmatter (a wrapped `title:` continuation starting with `"` — invalid YAML block
  mapping — plus `stage: [infra]` off-enum and missing `source`/`resolved_by`) to `live-defi-rollout`. From ~13:40Z the
  lint-codex slice failed on EVERY PR into PM main (incl. the LDR→main promote #1121) until the repair commit
  `663ecb850` landed via PR #1123 (~14:09Z). **The commit-time defense exists and works**: the prek `plan-hygiene` hook
  runs `check_frontmatter_schema.py --quiet <staged files>` — VERIFIED by restoring the broken content at its real
  paths and running the hook's exact invocation: exit 1, both files caught, including the YAML error. So the hook did
  not run on that machine. Three candidate causes, undistinguishable from here: hooks never installed on the laptop
  clone; `--no-verify`; or the verified-latent fail-open in the hook entry itself — `[ -f "$SWEEP" ] || exit 0`
  silently PASSES when the workspace layout doesn't match the sweep-path derivation. Docs are quickmerge-carve-out
  (direct push legal) and LDR runs no server QG by design, so commit time is the ONLY line of defense for docs — it
  must not be fail-open.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prek, pre-commit, frontmatter, fail-open, quality-gates, slot-safety, docs-carve-out, lint-codex]
related:
  [
    "codex/11-project-management/doc-frontmatter-schema.md",
    "codex/08-workflows/ci-cd-flow.md",
    "plans/active/issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md",
    "plans/active/issues/slot_branch_realign_discards_uncommitted_worktree_2026_07_17.md",
  ]
created: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: none
depends_on: []
source: >-
  slot main·harsh_pc 2026-07-17 — root-caused live while the breakage was blocking #1121/#1123; operator asked "who
  shipped this and why wasn't it caught"; every claim below re-verified by running the actual hook invocation against
  the actual broken content
resolved_by:
locked_by:
locked_since:
---

# The only gate that guards docs pushes is fail-open

## Verified facts (2026-07-17)

1. `4a7816269` (`slot-3·laptop`) created both broken docs; direct push, no `Quickmerge:` trailer — **legal**:
   `plans/**`/`*.md` are in `check_strict_quickmerge.py`'s `CARVE_PREFIX`/`CARVE_EXT`.
2. The prek hook's exact invocation (`check_frontmatter_schema.py --quiet <staged paths>`) **catches both files**
   (exit 1) when run against the broken content at real repo paths — reproduced from `4a7816269`'s blobs. The hook did
   not run (or was bypassed) on the authoring machine.
3. The hook entry in `.pre-commit-config.yaml` is fail-open: `[ -f "$SWEEP" ] || exit 0` — sweep script not found ⟹
   silent PASS. A laptop clone whose PM checkout is named or nested differently than the
   `$(git toplevel)/../unified-trading-pm` derivation silently loses the whole gate.
4. LDR runs no server QG (by design; promote PR carries the gate) ⟹ first detection = lint-codex on the NEXT PR into
   main ⟹ blast radius is every PM PR, not the offending commit.
5. Checker footguns confirmed while testing: (a) without `--quiet` it prints violations but **exits 0** (interactive
   mode); (b) paths outside the repo are silently skipped (exit 0) — do not "test" the hook with copies in /tmp.

## Fixes shipped 2026-07-17 (operator directive: "fix the root cause so that alerts eventually drop")

- **Fix 1 SHIPPED** (`unified-trading-pm@0383b5df7`): the hook entry now FAILS LOUD when the sweep script is
  unresolvable (config + `scripts/pre-commit-templates/docs.pre-commit-config.yaml` so a rollout cannot revert it).
- **Fix 2 SHIPPED** (same commit): `.github/workflows/ldr-docs-gate.yml` — corpus frontmatter check on every
  doc-touching LDR push, self-hosted glue ($0), pages ONCE (dedup `ldr-docs-gate-red`, 60m) with the offending commit +
  author + remedy. Detection gap closed: a bypassed hook now surfaces in minutes on the offending push, not as
  fleet-wide red gates an hour later.
- **Fix 4 RESOLVED 2026-07-17** — live repro on slot-3·laptop (the exact machine that authored `4a7816269`); see "##
  Root cause CONFIRMED on slot-3·laptop" below. The bypass was `git commit --no-verify` (or `-n`) — NOT a missing/broken
  hook and NOT the path fail-open. `main·planning`'s hook-install state is a separate hygiene check (still worth doing),
  not this commit's cause.
- **Fix 3 is a NON-BUG** in the current checker (re-verified 2026-07-17): `check_frontmatter_schema.py` returns exit 1
  on real violations in BOTH `--quiet` and non-quiet mode. The "prints ❌ but exits 0" reading in footgun 5a was
  actually footgun 5b — an out-of-scope / `_`-prefixed / out-of-repo path is silently skipped
  (`doc_type_for_path → None` or `is_exempt`), which prints "✅ 0 docs" and exits 0. That skip is by design and does NOT
  weaken the real gate (the pre-commit hook feeds it real in-repo staged paths); it only misleads ad-hoc CLI testing. No
  code fix required.

## Root cause CONFIRMED on slot-3·laptop (2026-07-17, live repro)

Re-run on `Mac.mynet` = `ikennaigboaka [slot-3·laptop]` (git `user.name`), the exact identity that authored `4a7816269`.
Every link in the commit-time defense is present and working here:

1. **prek pre-commit hook installed** — `.git/hooks/pre-commit` is the prek-generated shim, mtime 2026-07-08 — present a
   full 9 days BEFORE the 2026-07-17 incident. `core.hooksPath` unset.
2. **FF-cron hook-heal alive on this laptop** — `crontab` runs `slot-cron-ff-pull.sh --all-slots` every 5 min;
   `/tmp/slot-cron-ff-pull.log` fresh. Its "install prek on every clone missing the marker" block (2026-07-06) keeps the
   hook installed; the unchanged 07-08 mtime confirms it hasn't needed to re-install since.
3. **The sweep path resolves** — with `WORKSPACE_ROOT` unset the hook falls to the
   `$(git toplevel)/../unified-trading-pm/…` derivation, which resolves to an existing `run_hygiene_sweep.sh` on this
   `.tabs/3` layout. So even the _incident-time_ fail-open (`[ -f "$SWEEP" ] || exit 0`, config at `4a7816269^`) would
   NOT have short-circuited here.
4. **No persistent bypass env** — `SKIP` / `PREK_SKIP` unset; no `git` commit alias injecting `--no-verify`; nothing in
   the shell rc / `.envrc`.
5. **The gate CATCHES the exact broken content** — restoring `4a7816269`'s broken blob to a realistically-named in-repo
   path and running BOTH the raw checker AND the full `prek run plan-hygiene` returns exit 1 with the YAML parser error
   (`expected <block end>, but found '<scalar>'`). (A first repro falsely "passed" only because the temp file was named
   `__hooktest…` → `_`-prefixed → `is_exempt` → skipped; renamed without the underscore it fails loudly — footgun 5b in
   the flesh.)

**Conclusion:** hooks were installed and functional on slot-3·laptop; the sweep resolved; the checker catches the
content. The only remaining path by which `4a7816269` reached LDR is an explicit commit-time bypass —
`git commit --no-verify` / `-n`. No install-checker (FF-cron heal, `check-slot-commit-identity.sh`,
`verify-slot-host-symmetry.sh`) can catch `--no-verify`; the correct and sufficient defense for that class is the
post-push corpus gate (Fix 2, `ldr-docs-gate.yml`), which is shipped. Fix-direction 2's clone-setup half is also now in
place — `setup-tab-worktrees.sh` (≈L388) installs the prek pre-commit hook per clone (not just the pre-push guard).

**Recommendation:** all four fix-directions are addressed (Fix 1 fail-closed + Fix 2 post-push gate shipped; fix 3 a
non-bug; fix 4 diagnosed). Recommend CLOSE. Residual independent follow-up: verify `main·planning`'s hook-install state
for the 3rd doc — a hygiene check, not a blocker on this issue.

## Fix directions (operator to rank)

1. **[INFRA] P1 — close the fail-open.**
   `[ -f "$SWEEP" ] || { echo "plan-hygiene sweep NOT FOUND at $SWEEP — refusing to commit plans/codex without the gate"; exit 1; }`
   — a missing sweep must block plan/codex commits, not wave them through. Same treatment for any other `|| exit 0`
   guard in local prek hooks.
2. **[INFRA] P1 — make un-hooked clones impossible or visible.** `prek install` belongs in the clone-setup path
   (`setup-tab-worktrees.sh` + whatever provisioned the laptop clone), and/or a cheap detector: a scheduled glue-runner
   job that runs `check_frontmatter_schema.py` (corpus mode) on LDR HEAD and alerts `#ci-failures` on violations —
   catches ANY bypass (missing hooks, --no-verify) minutes after push instead of at the next promote. $0 on self-hosted.
3. **[DEVOPS] P2 — checker exit-code honesty.** Non-quiet mode printing ❌ but exiting 0 invites scripted misuse; make
   exit codes uniform and add `--interactive` for the always-0 behavior if the morning sweep needs it.
4. **[VERIFY] P2 — confirm which bypass actually happened on slot-3·laptop** (hooks missing vs --no-verify) once that
   machine is reachable; the answer decides how much weight fix 2's detector carries vs fix 1 alone.
