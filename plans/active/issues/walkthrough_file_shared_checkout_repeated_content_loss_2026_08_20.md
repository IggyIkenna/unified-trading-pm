---
doc_type: issue
title: platform-external-api-walkthrough.html lost committed and uncommitted structure-pass content THREE times in one session on a shared slot-6 checkout
summary: >-
  Across 2026-08-20, `codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` lost work
  three separate times: (1) an already-verified, origin-pushed commit (c1585907e3) was reverted wholesale by a
  different slot (583358306a, "agt-5f1add", one-line unexplained message, no linked issue) across all five
  same-session artefacts, not just this one; (2) after restoring from the intact commit object and re-shipping, a
  freshly-dispatched content-rebuild agent's ~296K-token, 62-tool-call output (sections 28-30) was found completely
  absent from HEAD, origin AND the local working tree — confirmed by direct byte-for-byte comparison against the
  pre-work baseline; (3) the recovery for (2) itself required a python-script splice from a scratchpad backup because
  the agent's direct edits never survived to a commit. This is a structural risk on this specific file/checkout, not a
  one-off, and needs a real fix, not repeated manual recovery.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    multi-agent-collision,
    shared-checkout,
    data-loss,
    client-artefacts,
    safe-doc-push,
    per-tab-worktrees,
  ]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/state_fabric_artefacts_2026_08_20.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
context_scope:
  [
    scripts/dev/safe-doc-push.sh,
    codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Interactive session slot 6, discovered mid-flow while executing the state-fabric artefact structure pass — recorded
  in real time as each loss and recovery happened, not reconstructed after the fact.
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
---

# Three losses, one file, one session

## What happened, in order

1. **A verified commit was reverted with no explanation.** `c1585907e3` (structure pass on all five state-fabric
   client artefacts) was independently verified structurally sound and confirmed present at origin before being
   reported complete. It was then reverted by `583358306a`, authored from a DIFFERENT slot (`[slot-32·planning]`),
   message: `"revert unverified artefact structure pass (agt-5f1add)"` — one line, no body, no linked issue doc, and
   `agt-5f1add` does not match any agent ID this session dispatched. `git log --all` for the affected file in the
   relevant window shows no separate `agt-5f1add` commit — the thing reverted **was** `c1585907e3`. Recovered by
   extracting the intact commit object directly (`git show c1585907e3:<path>`) and re-shipping.
2. **A freshly-dispatched agent's work vanished before it could be committed.** A single-file, single-writer agent
   spent ~296K tokens / 62 tool calls building three new sections. Its own completion report described the work in
   detail and flagged mid-run file churn it did not cause ("an external concurrent process modified the file on disk
   ... I made zero git calls"). Post-completion, `git log`/`git show HEAD`/`git show origin/...` all showed **zero**
   trace of the new sections — the file matched the pre-work byte count exactly, at HEAD, at origin, and locally.
3. **The recovery for (2) came from a scratchpad backup, not from git.** A file in this session's scratchpad
   (`new_sections.html`, written independently of any explicit instruction to write there) turned out to contain the
   exact tail content the lost agent produced — byte count within 500 of the agent's own reported delta, section IDs
   matching, ending in a verbatim copy of the document's real footer. This was spliced back in via a direct
   read-modify-write script and shipped. **Without this scratchpad artifact, the ~296K-token work would have been
   unrecoverable and required a full re-run.**

## Why this is worth its own issue, not just three retries

- **The `safe-doc-push.sh` isolated-worktree mechanism, designed for exactly this kind of contention, was insufficient
  on its own.** It correctly detected drift mid-run at least once ("peer landed different content — abandoning
  isolated mode... falling back to shared-index reconcile") and merged safely rather than clobbering — that part
  worked. What it could not protect against was loss occurring **before** a push was ever attempted, i.e. the working
  tree itself being reset by something else between an agent finishing its edits and the orchestrating session running
  the push.
- **This happened to committed AND uncommitted content, on the same file, within about 90 minutes.** The stash pile
  grew from 75 to 80 entries in that same window (`pre-reconcile quarantine`, timestamps spanning the whole session) —
  consistent with very high concurrent write pressure on this specific slot's checkout, but the exact mechanism that
  caused the WORKING TREE (not just HEAD) to reset was never conclusively identified.
- **A scratchpad backup happening to exist was luck, not design.** Nothing in this session's workflow explicitly
  writes recovery snapshots for agent-authored content before a commit succeeds. The recovery worked this time; it is
  not a repeatable safety net.

## Todos

- [ ] [REVIEW] P1. **Determine the actual mechanism that reset the working tree**, not just the commit history. Check
      whether another slot/session's `git checkout`, `git reset`, or a scheduled reconcile job touched this exact
      path during the loss windows (`~19:00-19:32` local, 2026-08-20) — `ps aux` during the incident showed 16
      claude-matching processes with this slot's cwd; identify which, if any, ran a git write operation against this
      specific file.
- [ ] [BACKEND] P1. **Add a pre-write safety snapshot for agent-authored client-artefact edits** — before a
      single-file structure-pass agent begins editing a large, contested file, snapshot its current state
      (content-hashed, timestamped) to a location outside the shared working tree, so a repeat of loss (2)/(3) has a
      designed recovery path instead of a lucky scratchpad find.
- [ ] [REVIEW] P1. **Investigate whether `platform-external-api-walkthrough.html` specifically is unusually
      contended** — it is the largest of the five client artefacts (now ~839KB) and was the target of both losses (2)
      and (3); check whether size, edit frequency, or being the T7b reconciliation target made it a hotspot other
      files in the same commits were not.
- [ ] [DOC] P2. **Add this incident to `/codex/05-infrastructure/per-tab-worktrees.md`** as a concrete case study
      alongside the existing multi-agent-collision documentation, since the existing guidance did not anticipate
      working-tree loss occurring independently of a git operation this session performed.

## Progress Log

**2026-08-20 — filed.** All three losses were fully recovered within the same session — nothing is currently missing.
Filed because the pattern (not the individual incidents) needs a real fix; recovering by luck three times in one
session is not sustainable for the remaining artefact work still in flight.
