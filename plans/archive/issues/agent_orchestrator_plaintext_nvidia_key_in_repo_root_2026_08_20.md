---
doc_type: issue
title: Plaintext NVIDIA API key sitting in agent-orchestrator repo root (untracked keys.env)
summary: >-
  Found live 2026-08-20 while investigating an unrelated AO dispatch-reclaim bug (interactive
  session, slot 3): an untracked file `agent-orchestrator/keys.env` (82 bytes, one line,
  `nvidia_key=nvapi-...`) sitting in the repo root, not gitignored, not staged. Never committed
  by this session — pre-existing debris, most likely left over from the NVIDIA/Gemma wiring work
  (`agent-orchestrator@86cd2066`, "feat(nvidia): wire NVIDIA/Gemma into the shared
  dispatch-headroom gate"). Confirmed not currently at risk of a git leak (untracked, `git
  check-ignore` found no match but nothing has ever `git add`ed it), but a live API key sitting
  in plaintext in a shared multi-operator checkout is bad hygiene regardless — any slot/operator
  on this VM can read it, and a future broad `git add -A`/`-.` by anyone would commit it.
status: resolved
resolved_by: operator (moved keys.env off the shared checkout; GSM migration explicitly deferred)
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, secrets-hygiene, nvidia, credentials]
related: [/plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
locked_by:
locked_since:
context_scope: [agent-orchestrator/keys.env, agent-orchestrator/server/nvidia_headroom.py]
supersedes:
superseded_by:
depends_on: []
source: >-
  Surfaced incidentally during idle_lingering_session_reclaim_not_firing_2026_08_19.md's
  2026-08-20 fix session (interactive, slot 3) while checking `git status` before shipping —
  unrelated to that session's actual work, split into its own doc rather than bundled in.
assigned_role: infra
drift_direction: none
---

# Plaintext NVIDIA API key in agent-orchestrator repo root

> **🟢 RESOLVED 2026-08-20** — operator relocated `keys.env` off the shared `agent-orchestrator`
> checkout directly; GSM migration explicitly declined for now. Sole todo `[x]`, 0 remaining,
> `locked_by:` empty. Archived per the 6-step ritual.

## What was found

`ls -la agent-orchestrator/keys.env`: 82 bytes, created 2026-08-20 08:39 UTC, owner `hk`, mode
`rw-rw-r--`. Contents: a single line, `nvidia_key=nvapi-<redacted>`. `git check-ignore -v keys.env`
returns no match (exit 1) — it is genuinely untracked, not gitignored. `git status --short` shows
it as `??` and it has never appeared in any commit this session touched.

Not an active leak: it was never staged or pushed. The risk is (a) any operator/slot on this
shared VM can read a live API key in plaintext right now, and (b) it is one careless `git add -A`
away from landing in history permanently (git history is effectively forever — a later `git rm`
would not undo the exposure).

## Why this probably isn't a fresh mistake

`git log --oneline -- server/` shows `86cd2066 feat(nvidia): wire NVIDIA/Gemma into the shared
dispatch-headroom gate` as recent history in this same area — plausible source of manual local
testing that left this file behind. Not confirmed against that commit's author/session directly;
flagging the correlation, not asserting it.

## Follow-up

- [x] [OPERATOR] P3. **Decide correct storage for the NVIDIA key and remove the plaintext file.**
      Resolved 2026-08-20 by the operator directly: the key is being moved off the shared
      `agent-orchestrator` repo-root checkout to a location of the operator's choosing. GSM
      migration was explicitly declined for now ("we dont have to push the key to GSM for now") —
      so this is a relocation, not a GSM-backed credential wiring change; `nvidia_headroom.py`'s
      actual credential-loading path was not re-examined as part of this resolution.

## Resolution

Operator moved `keys.env` out of the shared checkout on 2026-08-20. No GSM/`UnifiedCloudConfig`
migration was done or requested at this time — if `nvidia_headroom.py` still expects a local
`.env`-style credential file, that convention question remains genuinely open should someone
revisit secrets hygiene for this provider later, but it is not blocking and not tracked as a
separate open todo here.
