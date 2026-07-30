---
doc_type: issue
title:
  "base-service.sh had ~35 hardcoded /tmp/*_qg.log capture paths that made a full /tmp tmpfs produce FALSE quality-gates
  failures (checker itself passes standalone) — fixed for base-service.sh, base-library.sh + this host's missing cleanup
  crons remain"
summary: >-
  Discovered while shipping the slot-git-status-report.sh loopback fix (ao_satellite_ao_dispatch_batch1_2026_07_26.md
  item 3): `quality-gates.sh` on host ip-172-31-5-118 failed STEP 5.100 (architectural ratchets) with "Architectural
  ratchet violation", but re-running the exact same checker command standalone (`check_architectural_ratchets.py
  --workspace-root ...`) printed "0 violation(s)". Root cause: STEP 5.100's shell redirect (`>/tmp/arch_ratchets_qg.log
  2>&1`) was hardcoded to literal `/tmp`, and this host's `/tmp` (a 2GB tmpfs) was at 100% full — the redirect itself
  failed with ENOSPC, so the `if` construct's exit status reflected the failed write, not the checker's real (clean)
  result. This is the SAME already-tracked recurring class as `shared_host_tmp_tmpfs_exhaustion_2026_07_08.md` /
  `..._2026_07_26.md`, but a NEW failure mode neither of those docs caught: those fixed pytest/basedpyright's cache dirs
  and the Claude-session scratch sweep, but never audited `base-service.sh`'s OWN internal checker-output capture files,
  which turned out to have ~35 more hardcoded `/tmp/` sites (STEP 5.19 cloudbuild, 5.65 removed-symbols,
  5.67/5.69/5.70/5.86/5.89/5.90/5.91/5.92/5.93/5.94/5.95/5.96/5.97/ 5.98/5.99/5.100/5.101/5.102/5.103 ratchet checkers,
  the AST import-order checker, pip-audit's JSON output, and the `act` simulation log) — any one of which could produce
  the identical false-failure the moment `/tmp` fills, on ANY repo across the fleet, not just PM. Fixed all ~35 sites in
  `base-service.sh` (this repo's SSOT, sourced by every service repo) as part of shipping the loopback todo, since it
  was directly, reproducibly blocking that ship (confirmed fixed: full `quality-gates.sh --no-fix` run went from 2 hard
  failures — STEP 4 TYPE CHECK + STEP 5.100 — to a clean pass after redirecting these captures through `${TMPDIR:-/tmp}`
  instead of a bare `/tmp` literal, matching the pattern `BASEDPYRIGHT_CACHE_DIR` already used). Two things remain, both
  genuinely out of scope for the todo that surfaced this: (1) `scripts/quality-gates-base/base-library.sh` (used by
  library-tier repos, e.g. unified-api-contracts / unified-trading-library) has the IDENTICAL hardcoded-`/tmp` pattern
  across a similar number of sites — NOT audited or fixed here; (2) this host (ip-172-31-5-118) has NEITHER of the two
  sanctioned cleanup crons (`cleanup-stale-qg-tmp.sh` / `cleanup-stale-claude-session-tmp.sh`) installed at all —
  confirmed via `crontab -l` — even though they were registered on the human-planning VM per the 2026-07-26 doc;
  attempting to install them here failed with `/var/spool/cron/: mkstemp: Permission denied` (this host's cron appears
  locked down for this account), so an operator with the right privileges needs to register them (or fix the permission)
  directly on this host.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, tmpfs, disk-space, false-failure, base-service, base-library, shared-host, cron]
related:
  [
    /plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md,
    /plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_26.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/shared_host_tmp_tmpfs_full_2026_07_26.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
source:
  "slot-11 (infra), discovered + partially fixed while executing ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3"
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# base-service.sh's own checker-output capture paths bypassed TMPDIR — false QG failures on a full /tmp

## What I found

- `quality-gates.sh` (PM, host ip-172-31-5-118) failed twice in a row at STEP 5.100 (architectural ratchets) with
  `Architectural ratchet violation in unified-trading-pm`, while running the EXACT recheck command it printed
  (`.venv/bin/python unified-trading-pm/scripts/quality_gates/check_architectural_ratchets.py --workspace-root /home/ubuntu/unified-trading-system-repos/.tabs/11`)
  standalone printed `Ran 3 ratchet(s) across 10 target file(s); 0 violation(s)` — i.e. the checker itself was clean;
  the GATE was lying.
- Root cause: `base-service.sh`'s STEP 5.100 block redirects the checker's stdout+stderr to
  `>/tmp/arch_ratchets_qg.log 2>&1`, a LITERAL `/tmp` path (not `${TMPDIR:-/tmp}`, the pattern already used 3 lines
  above it for `BASEDPYRIGHT_CACHE_DIR`). `df -h /tmp` showed the host's 2GB tmpfs at 100% full
  (`tmpfs 2.0G 2.0G 4.0K 100%`). The redirect's own `open()`/`write()` failed with ENOSPC, so the `if $PYTHON_CMD ...
  > /tmp/arch_ratchets_qg.log 2>&1;
  > then`construct's exit status reflected the FAILED REDIRECT, not the checker's real (passing) exit code —`base-service.sh`then reported it as a content violation with an empty/truncated log to`cat`.
- Confirmed the SAME bug independently at STEP [4] TYPE CHECK: `_bp_out="/tmp/bp_out.$$"` (basedpyright's own stdout
  capture) is ALSO a hardcoded `/tmp` literal, producing `❌ Type check FAILED/timeout (exit=N)` with
  `ERROR_COUNT=0`/`WARN_COUNT=0` extracted from an empty capture file — indistinguishable from a genuine crash/timeout
  until you notice the counts are both zero.
- Grepped the rest of `base-service.sh` for the same literal-`/tmp/` pattern used for a checker's output capture and
  found ~35 more sites across nearly every STEP 5.x ratchet gate (5.19, 5.65, 5.67, 5.69, 5.70, 5.86, 5.89-5.104), the
  AST import-order checker (`_inside_imports_qg.err`), pip-audit's JSON output (`pip-audit-output.json`, read by 4
  separate call sites plus `sbom-store.py`), and the `act` simulation log (`mktemp /tmp/act-output.XXXXXX`) — every one
  of them vulnerable to the identical false-failure mode the moment this host's (or ANY host's) `/tmp` fills, for ANY
  repo in the fleet (this file is the shared SSOT sourced by every service repo's `quality-gates.sh`), not just PM.
- Also checked whether the two sanctioned cleanup crons from the archived 2026-07-26 fix
  (`shared_host_tmp_tmpfs_exhaustion_2026_07_26.md`) were installed on THIS host — they were not (`crontab -l` showed
  neither `cleanup-stale-qg-tmp` nor `cleanup-stale-claude-session-tmp` marker lines). That fix's registration only ever
  happened on the human-planning VM (52.194.240.144); ip-172-31-5-118 was never covered. Attempted to install both here
  myself (idempotent, already-shipped, already-vetted scripts — same action the archived doc's own Progress Log
  describes an agent performing) but both installers failed identically: `/var/spool/cron/: mkstemp: Permission denied`
  — this account cannot write its own crontab on this host. Also could not `mkdir /var/tmp/claude-agent-scratch` (the
  other doc's TMPDIR workaround target) — `Read-only file system`. Both point to this host having tighter
  filesystem/cron permissions for this account than the human-planning VM did.

## Why it matters

- A false QG failure is worse than a flaky test: it looks exactly like a real architectural regression (the same
  `❌ STEP 5.100: Architectural ratchet violation` banner as a genuine violation), so an agent hitting this would
  reasonably start debugging the WRONG THING (their own diff) instead of recognizing a shared-host resource issue —
  exactly the failure mode this issue's own investigation had to rule out by hand (re-running the checker standalone).
- This can strike ANY of the ~35+ gate steps, on ANY repo, non-deterministically, purely based on how full `/tmp`
  happens to be on whatever shared host the agent is running on at that moment — a wide, silent flakiness surface, not a
  one-off.
- The specific host this was found on (ip-172-31-5-118) has NEITHER cleanup cron installed, so the tmpfs-exhaustion
  recurrence rate on THIS host is un-mitigated relative to the human-planning VM — and this agent lacks the permissions
  to fix that host-level gap itself.

## Fixed (this session)

- `scripts/quality-gates-base/base-service.sh`: all ~35 `/tmp/*_qg.log` / `_inside_imports_qg.err` /
  `pip-audit-output.json` / `act-output.XXXXXX` capture paths now route through `${TMPDIR:-/tmp}` (mechanical
  substitution, verified via `git diff` — no check LOGIC changed, only where its stdout/stderr capture file lives).
  `bash -n` clean; full `quality-gates.sh --no-fix` re-run (with `TMPDIR=${HOME}/.cache/qg-tmp` set, since this
  session's OWN shell had no TMPDIR exported) went from 2 hard failures to a clean pass on the identical tree.

## Relationship to `shared_host_tmp_tmpfs_full_2026_07_26.md` (slot-14, same session, independent discovery)

Slot-14 hit the identical symptom (STEP 5.93 failing in-pipeline while the same checker passes standalone) within a
minute of this doc being filed and correctly diagnosed a SECOND, DISTINCT root cause on the same ~35 lines: a
**cross-slot filename COLLISION**, not disk-space exhaustion — two slots' concurrent `quality-gates.sh` runs on this
shared host can both target the identical fixed `/tmp/<name>_qg.log` name at the same instant, so one's write races the
other's read. My `${TMPDIR:-/tmp}` fix (this doc) does NOT resolve that collision on its own — if two slots share the
same `TMPDIR` value (e.g. both left unset, defaulting to plain `/tmp`), the identical race remains. Slot-14's own P2
SCRIPT todo (PID-or-mktemp-unique paths + updating every paired read-back site) is the correct fix for THAT root cause
and is still needed — **but it must now rebase against this doc's already-landed rewrite of the same ~35 lines**
(`unified-trading-pm@f7e913e98`) rather than the pre-fix version, or it will conflict. Both fixes are complementary and
both real: ENOSPC-on-full-disk (this doc) and same-name-collision-under-concurrency (slot-14's doc) are two different
ways the same hardcoded-shared-filename design fails.

## Todos

- [x] ✅ [INFRA] P2. **DONE — already shipped, unified-trading-pm@f2f227ff9** ("fix(qg): make base-library.sh
      TMPDIR-aware, mirrors base-service.sh fix"). Verified live 2026-07-30: every checker-capture site in
      `scripts/quality-gates-base/base-library.sh` (all sites named in this todo, plus the AST import-order checker and
      pip-audit's JSON output) routes through `${TMPDIR:-/tmp}` — zero bare `/tmp/` literals remain. `bash -n` clean.
- [x] ✅ [OPS] P2. **DONE 2026-07-28 — operator personally registered both crons on ip-172-31-5-118.** RULED 2026-07-28
      (operator direct answer: "Yes, happy to do this now"), retagged from `[OPERATOR]` to `[OPS]`, and executed the
      same day — the operator ran both install commands themselves (the only path available, since this account has no
      crontab-write permission on this host and no cloud identity can self-serve an OS-level account permission):
      `bash     bash unified-trading-pm/scripts/dev/install-cleanup-stale-qg-tmp-cron.sh     bash unified-trading-pm/scripts/dev/install-cleanup-stale-claude-session-tmp-cron.sh     `
      Auditing/remediating other fleet hosts the same way (if any are similarly missing these crons) is tracked
      separately — not re-verified as part of this todo's closure, since the specific host that triggered this doc is
      now confirmed fixed.

## Update 2026-07-27 (slot-4, ag_closeout_auditor) — THIRD failure mode, this time on the ROOT filesystem, not just /tmp

While shipping `defi_satellite_ao_dispatch_batch5_2026_07_27.md`, a `quickmerge.sh --agent` attempt failed with the
plan-hygiene pre-commit hook reporting `missing required field: parent_epic/title/priority/status/estimate_class/...` on
THREE files that visibly and unambiguously carry every one of those fields (confirmed by direct `grep` immediately after
— `parent_epic:`/`title:` both present, count=1 each). The same run's stderr showed the real cause:
`awk: ... warning: error writing standard output: No space left on device` for all three files, at the exact FNR
line-numbers the frontmatter parser would be reading. `df -h /` at that moment showed `/dev/root 290G 288G 2.4G 100% /`
— i.e. this is NOT the 2GB `/tmp` tmpfs this doc's Fixed section already addressed; it's the 290GB ROOT filesystem
itself (which `/home` shares — same device), independently near-exhausted. By the time a later retry succeeded (~10
minutes later), `df -h /` read `290G 289G 1.2G 100% /` — i.e. the condition is ACTIVELY WORSENING in real time, not a
one-off blip. Two sibling slots independently hit and documented the same root-disk-exhaustion class in the same window:
`issues/host_root_disk_full_transient_2026_07_13.md` (earlier occurrence) and
`issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` (concurrent RAM-pressure symptom, same host, same
session).

**New failure mode for this doc's tracking purposes**: the plan-hygiene pre-commit's own frontmatter-schema check (an
`awk`-based parser, NOT one of the ~35 `base-service.sh` `/tmp/*_qg.log` sites already fixed) silently mis-reports
"missing required field" — a CONTENT-shaped error message — when its stdout write hits ENOSPC mid-file, on a filesystem
it doesn't control the fullness of. This is the same failure SHAPE as this doc's original finding (a disk-write failure
surfacing as a false content/logic error, sending whoever hits it down the wrong debugging path) but a DIFFERENT script
(plan-hygiene, not base-service.sh) and a DIFFERENT filesystem (root disk, not the 2GB tmp tmpfs) — so the existing
"Fixed" section's `${TMPDIR:-/tmp}` remediation does not cover this instance; there is no `/tmp` redirect to fix here,
the disk itself is the constrained resource. Retrying (fetch + `git merge --ff-only` + re-run) worked once transient
headroom returned, so this is not a hard block, but it burned ~6 unnecessary retry cycles before the true (external,
unfixable-by-me) cause was clear each time. Not filing a new todo — the existing P2 operator ask (register the cleanup
crons on this host) is the correct remedy already tracked above; flagging here only because it's evidence the condition
is both broader (root disk, not just tmp) and actively worsening, which raises the urgency of that existing todo. No
content of this doc's existing Todos changes.

## Update 2026-07-27 (slot-7) — SAME root-disk ENOSPC on the identical `awk` frontmatter parser, 7 consecutive hits

Hit the identical failure shape (plan-hygiene pre-commit awk parser at the same FNR-line-numbered
`No space left on device` warning, on a routine `docs(plans):` checkpoint commit — no code, no VM launches) 7 times
across ~15 minutes on this same host class. `df -h /` fluctuated `3.1G`→`3.5G`→`3.1G` available across retries (never
meaningfully recovering), matching slot-4's "actively worsening, not a one-off blip" observation above rather than a
quick transient blip. Retrying (with a short gap + a `git pull --rebase --autostash` in between, since branch drift was
also firing concurrently on this busy branch) eventually succeeded each time disk momentarily had enough headroom. No
new remedy found beyond what's already tracked — corroborating that the P2 operator cron-registration ask above is still
the correct, still-unactioned fix; the workaround (retry with brief spacing, verify `df -h /` isn't the real story
before assuming a genuine content/logic bug) remains the only in-session mitigation available to a worker.
