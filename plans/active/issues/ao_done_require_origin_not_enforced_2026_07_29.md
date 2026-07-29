---
doc_type: issue
title: >-
  agent-orchestrator's /done accepts a task as complete even when its cited commit SHA never reached origin —
  done_require_origin exists and is wired, but defaults False and is unset everywhere in prod
summary: >-
  server/verify.py::verify_done() already computes on_origin (is the reported SHA reachable from any origin/* ref) and
  server/routes/slots_worker.py's /done handler already has a real enforcement branch that would reject the call with a
  409 (\"push failed... re-run quickmerge\") when on_origin is False -- but that branch is gated behind
  config.tuning.done_require_origin, which defaults to False (server/config.py:685) and is not set in the systemd unit
  template, any repo script, or the live orchestrator VM's actual .env.local (confirmed directly via SSM 2026-07-29).
  Today, a /done call whose cited SHA only exists locally (quickmerge never ran, or ran and failed silently, or the
  worker never pushed) is accepted -- the task is marked status='done', a DoneWarning (type=sha_not_on_origin) is
  returned to the caller and an on_origin:false field is logged to the slot_done_verified activity event, but nothing
  blocks it. Surfaced by the operator directly asking, while reviewing the ao_backlog_done_row_disappearance_2026_07_25
  fix, "as long as agents only mark tasks done once they have actually gone to LDR" -- that assumption does not
  currently hold as an enforced invariant, only as a warned-and-logged one.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, data-integrity, done-verification, quickmerge, unenforced-config, backend]
related:
  [
    /plans/archive/issues/ao_backlog_done_row_disappearance_2026_07_25.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Operator question during the 2026-07-28/29 done-row-disappearance fix session: "as long as agents only mark tasks done
  once they have actually gone to ldr and also assuming other agents/crons pull from ldr (that happens right?)". The
  pull side was verified true (ao-self-pull.sh + confirmed live this session: the fix commit reached the orchestrator
  VM's own checkout and reloaded within ~2 minutes of push). The done-side assumption was checked live against the
  actual code + the actual deployed config and found NOT to hold as an enforced guarantee.
resolved_by:
locked_by:
locked_since:
---

# /done accepts an unpushed SHA as complete — enforcement exists but is off

## What's confirmed

1. `server/verify.py::_sha_on_origin()` (line ~213) checks `git branch -r --contains <sha> --list origin/*` against the
   LOCAL remote-tracking refs (no network fetch — relies on a prior push having updated them). Returns `True`/`False`,
   or `None` on any git failure (timeout, not-a-repo, etc. — treated as "unknown", never as a block, by design).
2. `verify_done()` attaches this as `DoneVerification.on_origin`.
3. `server/routes/slots_worker.py`'s `/done` handler (~line 1322-1349) has a real, working enforcement branch:
   ```python
   if verification.verified and verification.on_origin is False:
       warnings.append(DoneWarning(type="sha_not_on_origin", ...))
       if get_config().tuning.done_require_origin:
           ...log slot_done_rejected_not_on_origin...
           raise HTTPException(status_code=409, detail={"msg": "... push failed. Re-run quickmerge ..."})
   ```
   This is a genuine, already-written, already-tested-shape gate — not a stub. It just never fires in prod because the
   flag it's conditioned on is off.
4. `config.py:685`: `done_require_origin: BoolEnvFalse = Field(default=False)`.
5. Confirmed absent from every place that could override it: `scripts/orchestrator.service` (the checked-in template),
   every `.sh` script in `scripts/`, and — via a live, read-only SSM check against the actual orchestrator VM
   (`i-0c9b283b31d6b5ca7`) on 2026-07-29 — `systemctl show orchestrator -p Environment` and the VM's actual
   `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/.env.local` both come back with **no**
   `DONE_REQUIRE_ORIGIN`/`ORCHESTRATOR_DONE_REQUIRE_ORIGIN` entry. The flag is at its `False` default in the real
   running system, not just in theory.
6. **Consequence, concretely**: right now, any `/done` call citing a SHA that exists only in a worker's local worktree
   (quickmerge silently failed, the worker forgot to push, `--files` scoping missed something, a network blip during
   push that the worker didn't notice) is accepted as genuinely done. The task is marked `status='done'` in `state.db`,
   the SAME durability guarantee this session's other fix
   (`/plans/archive/issues/ao_backlog_done_row_disappearance_2026_07_25.md`) now protects — but the underlying claim
   ("this work is safely on the shared branch") was never actually true for that row. Distinct bug class from that
   issue: that one was about a `done` row's _status_ getting silently corrupted after the fact; this one is about a
   `done` row's status being _wrong from the moment it was set_, because nothing checked the one fact that actually
   matters (is the code anywhere but this one worker's disk).
7. **`on_origin` checks "any origin branch", not specifically `origin/live-defi-rollout`.** In this workspace's actual
   ship discipline (quickmerge always lands on LDR) this is very unlikely to matter in practice, but it means the check
   is a slightly weaker proxy than "is this on LDR" — worth knowing, not necessarily worth tightening given how this
   repo actually ships code.

## What is NOT yet known — the actual next step

**Do NOT flip `done_require_origin=True` blind.** Turning this into a hard 409 in production is a real behavior change
with unknown blast radius until someone checks how often `on_origin=False` is _already_ firing today (it's already
computed and logged on every `/done` call regardless of the flag, via the `slot_done_verified` activity event's
`on_origin` field — no new instrumentation needed to answer this):

- If `on_origin=False` is rare (a handful of transient push failures) → flipping the flag on is very likely safe and
  should just be shipped, closing this gap outright.
- If it's common → there's a legitimate flow this check doesn't yet account for (a race between `/done` firing and
  quickmerge's push landing? a sentinel-SHA edge case not fully covered? something about how `_sha_on_origin`'s
  local-remote-tracking-refs-only check interacts with the per-slot worktree model?) that needs understanding BEFORE
  turning this into a hard block, or it will start rejecting legitimate completions.

## Todos

- [x] [BACKEND] P2. Query the `slot_done_verified` activity-log events over the last 14 days and compute the
      `on_origin=False` rate. — **Done 2026-07-29**: 1137 events, 1103 `true` / 26 `false` (2.29%) / 8 `none`. Sampled 3
      of the 26 false examples' actual cited SHAs and checked them directly against the real repos: `54850f6`
      (`ao_worker_context_lifecycle_gap-005`) was **already present on `origin/live-defi-rollout`** at check time — a
      confirmed false negative, not a failed push (the other 2 samples belong to repos this session didn't have cloned
      locally, inconclusive either way, not needed given the first result already answers the question).
- [x] [BACKEND] P2. Based on that rate: investigate before enabling. — **Done 2026-07-29, root-caused and fixed rather
      than just flipping the flag.** The false rate wasn't random noise — it's a real race: `verify_done` only reaches
      `_sha_on_origin` after `git show` already succeeded (the commit object is known locally), so a LOCAL-only
      `origin/*` miss is genuinely ambiguous between "never pushed" and "pushed, but this worktree's own remote-tracking
      ref cache hasn't caught up yet" (confirmed via the `54850f6` sample). Fixed by falling back to one
      `git fetch origin --quiet` + re-check, but ONLY on that rare (~2.3%) local-miss path, so the common (~98%) case
      stays exactly as fast as before (no fetch added to the hot path). Shipped: `agent-orchestrator@25d497f`
      (`server/verify.py::_sha_on_origin`), 2 new tests reproducing the exact stale-ref race deterministically + the
      genuinely-never-pushed case staying `False` (`tests/test_e2e_findings_remediation.py`). Full suite green (1917
      passed), `quality-gates.sh` green. **`done_require_origin` was deliberately NOT flipped to `true` in this same
      pass** — the false rate should be re-measured post-fix before deciding; flipping blind before this fix would have
      started rejecting real legitimate completions on exactly this race.
- [ ] [BACKEND] P2. Re-measure the `on_origin=False` rate over a window AFTER `25d497f` has been live for a few days
      (the fallback-fetch fix should collapse most/all of the 2.29% down to genuine failures only). **Tool now exists**:
      `bash agent-orchestrator/scripts/orchestrator/check-on-origin-rate.sh --days N` (promoted 2026-07-29 from the
      one-off script that produced the original 2.29% figure — same read-only SSM pattern as
      `check-ao-backlog-status.sh`). A `--days 1` spot-check on 2026-07-29 already shows an encouraging early signal
      (0/151 false in the last 24h) but that's too short a window to act on — wait for the "a few days" this todo asks
      for. If the rate is now at/near 0%, set `done_require_origin=true` in the orchestrator's `.env.local` (or the
      systemd unit template if it should apply fleet-wide) and ship. If a nonzero rate persists, sample those specific
      examples the same way this session did (check the cited SHA against the real repo) before deciding whether it's a
      genuine failure class or a different race this fix didn't cover.
- [ ] [BACKEND] P3. Consider whether `_sha_on_origin`'s "any origin/* branch" check should be tightened to specifically
      `origin/live-defi-rollout` (or configurable per repo's promotion model) — low priority given quickmerge's actual
      landing behavior, but worth a deliberate yes/no rather than leaving it implicit.

## Codex SSOTs

- None directly own `/done`'s verification internals. If `done_require_origin` gets enabled fleet-wide, add a reference
  here and to `/codex/12-agent-workflow/commit-push-flip-rule.md` (which currently documents the _intended_ discipline —
  commit+push+flip in the same turn — but not that the orchestrator can/does mechanically verify the push half of that).
