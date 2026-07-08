---
doc_type: issue
title:
  Shared-host /tmp is a 2GB tmpfs — concurrent slot pytest runs exhaust it, causing spurious ENOSPC test failures and
  blocked quickmerge shipping
summary:
  "/tmp on the orchestrator VM is mounted as a 2.0G tmpfs shared by every slot. A single full unified-trading-library
  quality-gates.sh run (pytest -n 4, tmp_path-heavy cloud_interface/config_interface/ usage_meter suites) can leave
  900MB+ of pytest-of-ubuntu scratch behind, and with several slots' QG runs overlapping the tmpfs fills to 0 bytes free
  within minutes — causing 60+ spurious OSError ENOSPC test failures (files that have nothing to do with the change
  under review) and, once, blocking even the harness's own Bash-tool output capture (which also lives under /tmp) until
  manually cleared. Hit twice in one session while shipping manifest_record_expected_empty_blank_source-007 (slot 8)."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library]
scope: [engineer, admin]
tags: [infra, disk-space, tmp, pytest, quality-gates, shared-host, ci]
related: [plans/active/issues/manifest_record_expected_empty_blank_source_2026_07_08.md]
created: 2026-07-08
parent_epic: infrastructure_master
priority: P2
source: [manifest_record_expected_empty_blank_source-007]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
---

## What I found

Shipping the `_record_status` root-cause fix (`manifest_record_expected_empty_blank_source_2026_07_08.md`) required two
full `quality-gates.sh` runs for `unified-trading-library`. Both hit `/tmp` disk exhaustion:

1. **First hit**: `df -h /tmp` showed `tmpfs 2.0G 2.0G 0 100%`. 62 tests failed with
   `OSError: [Errno 28] No space left on device` — all from `tmp_path`-based fixtures in
   `cloud_interface`/`config_interface`/`usage_meter` test suites, none touching the files I changed.
   `/tmp/pytest-of-ubuntu` alone held 945M across 3 numbered session dirs from my own just-completed run (pytest-xdist
   appears to allocate a top-level `pytest-of-ubuntu/pytest-NNN` dir per worker under some configurations, not one per
   session).
2. Cleared the stale dirs (verified no live pytest process / open fd first), re-ran — green.
3. **Second hit**, ~10 minutes later, mid-quickmerge: `/tmp` fully exhausted again (0 bytes free), this time ALSO
   breaking the Claude Code harness's own Bash-tool output capture (its per-session temp dir at
   `/tmp/claude-1000/.../tasks` lives on the same tmpfs) — every Bash call failed with `ENOSPC` until I redirected
   output to `/home` and diagnosed via `Read`. Root cause: multiple slots' concurrent QG runs on this shared host, each
   pytest invocation using hundreds of MB of `/tmp` scratch.
4. **Workaround that fixed it**: set `TMPDIR=/home/ubuntu/<scratch-dir>` (root partition has 95G free vs 2G tmpfs)
   before invoking `quality-gates.sh` / `quickmerge.sh`. pytest's `tmp_path` fixture honors `TMPDIR`, so this fully
   sidesteps the tmpfs contention. Full run was green with zero ENOSPC failures once redirected.

## Why it matters

- **Every slot on this host shares the same 2GB tmpfs.** With N concurrent slots each running a full `pytest -n 4` UTL
  suite, the budget is easily blown — this is not specific to my change, any slot's QG run can be collaterally failed by
  another slot's concurrent test run filling `/tmp`.
- **False-negative QG failures waste slot time and risk misdiagnosis** — 62 unrelated `ENOSPC` failures look like a real
  regression at a glance; a less-careful pass could misattribute them to the change under test instead of recognizing
  the environmental signature (`OSError: [Errno 28] No space left on device` on `tmp_path`-backed writes).
- **It can also break the harness itself** — Bash-tool output capture for THIS slot's own session shares the same tmpfs,
  so a bad enough exhaustion event stops the WORKING slot's Bash tool entirely (not just its target repo's tests), until
  diagnosed via redirect-to-`/home` + `Read`.

## Recommended decision

- [x] ✅ [INFRA] P2. Set `TMPDIR` (or pytest's `--basetemp`) to a root-partition path (e.g. `/var/tmp/pytest-<slot>` or
      a per-slot dir under `/home`) by default in `unified-trading-pm/scripts/quality-gates-base/base-library.sh`'s
      pytest invocation, instead of relying on the default `/tmp` tmpfs — the root partition has ~95G free vs `/tmp`'s
      2G, and this is a one-line env-var change with no other side effects (verified working via manual `TMPDIR=`
      override this session) (repo: unified-trading-pm). — unified-trading-pm@0e29e6d81
- [ ] [INFRA] P3. Consider whether `/tmp` should be resized (a host/VM-image change, e.g. `mount -o remount,size=` or
      the underlying cloud instance's tmpfs config) given N-way concurrent slot QG runs are an expected steady state,
      not an edge case — lower priority than the TMPDIR redirect since that alone resolves the contention without
      needing a host-level change (repo: unified-trading-pm, infra decision — needs operator input on the VM's tmpfs
      sizing options).
- [ ] [INFRA] P3. Consider a periodic `find /tmp/pytest-of-ubuntu -maxdepth 1 -mmin +60 -exec rm -rf {} +` cron (or
      equivalent) as a belt-and-suspenders cleanup for whichever stale scratch dirs the TMPDIR redirect above doesn't
      eliminate (e.g. from tools other than pytest that still default to `/tmp`) (repo: unified-trading-pm).

## Progress Log

- **2026-07-08** — Implemented by slot-2 (infra craft). Root-caused the recommended target: `/` (and `/var/tmp` under
  it) is actually mounted **read-only** on this host (`ro`, `errors=remount-ro`) — the doc's original `/var/tmp`
  suggestion would have silently no-op'd (`mkdir -p ... || true` swallowing the failure), so the fix targets
  `$HOME/.cache/qg-tmp` (the separate `rw` `/home` mount, ~95G free) instead, matching the manual workaround already
  recorded above and the existing `QG_CACHE_ROOT` convention. Landed in `qg-common.sh` (the shared foundation sourced by
  ALL of base-service.sh/base-library.sh/base-ui.sh/base-codex.sh, not just base-library.sh as originally scoped — same
  one-line pattern, same root cause, single control point) rather than duplicating the export per base script. Verified
  end-to-end: unclean-tmpdir sourcing test confirms the new default + mkdir; a full `unified-trading-library` pytest run
  (via `base-library.sh`) populated `$HOME/.cache/qg-tmp` instead of `/tmp`; `unified-trading-pm`'s own
  `quality-gates.sh` passes (warn-only pre-existing drift unrelated to this change). A caller-exported `TMPDIR` still
  wins (verified). P3 items (tmpfs resize, stale-dir cron) left open — operator-input / belt-and-suspenders, lower
  priority per the doc's own ordering.
