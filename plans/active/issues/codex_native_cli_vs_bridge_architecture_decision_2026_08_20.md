---
doc_type: issue
title: >-
  New evidence the Codex/Luna translation bridge itself (not Luna, not the sandbox) is the source of
  ~3 distinct token/reliability costs — reopens, but does not by itself overturn, the 2026-08-14
  "stays Claude Code" ruling that created the bridge instead of running native Codex CLI
summary: >-
  Investigating the slot-31 heartbeat stuck-loop (codex_luna_heartbeat_sandbox_network_stuck_loop_
  2026_08_20.md) surfaced a broader pattern worth a standalone decision record: the bridge's OWN
  translation layer — not Luna as a model, not a misconfiguration — is the direct, documented source
  of at least 3 separate costs, each already noted individually in the two bridge plans but never
  before totaled as one case: (1) the sandbox/MCP-tool-routing ambiguity that caused slot 31's
  ~1.85M-token, ~70-minute stuck loop; (2) a per-tool-use-turn wasted streaming round trip
  (`codex_mcp_tool_use_bridge_2026_08_18.md`'s own validation note); (3) "no incremental thread
  reuse" — every tool_use/tool_result pair restarts a fresh Codex thread rather than continuing the
  live one (`codex_mcp_proxy.py`'s own docstring, flagged "still real, still deliberately
  unaddressed"). Running Luna through the REAL, native Codex CLI instead of this bridge would very
  likely eliminate all three, since none of them exist for any other AO-dispatched provider — they
  are specifically artifacts of translating Claude Code's two-call pause/resume tool-use protocol
  onto Codex's synchronous MCP thread model. This does NOT automatically mean switching: the bridge
  exists specifically because of a standing, twice-invoked 2026-08-14 operator requirement ("Claude
  Code's harness — CLAUDE.md, skills, hooks, slash commands — must not be reengineered for any new
  provider") that already ruled out an analogous native-harness path for Grok/OpenCode on that exact
  basis. This doc exists to hand the operator a concrete, evidence-backed decision with the real
  unknowns scoped, not to pre-decide it.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, codex, luna, architecture-decision, bridge, native-cli, token-efficiency]
related:
  [
    /plans/active/issues/codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/codex_mcp_tool_use_bridge_2026_08_18.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/server/codex_mcp_proxy.py,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/codex_mcp_tool_use_bridge_2026_08_18.md,
    /plans/active/issues/codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-20, following up on the slot-31 heartbeat investigation:
  "if we start using codex cli just like claude cli, can we avoid this and will that also solve the
  tool call issues and also make luna work more efficiently... write findings and remaining decision
  that are not already in the plan so that we can act on it tomorrow."
assigned_role: infra
drift_direction: none
---

# Native Codex CLI vs. the translation bridge — a decision to make, not yet made

## What's NEW here (not duplicated from the other 2 bridge plans)

Neither bridge plan states this as one combined finding — each of the 3 costs below is individually
documented in its own plan, but nothing before today connected them as "the cost of choosing the
bridge over native Codex CLI." That synthesis, plus the concrete question below, is the new content:

1. **Sandbox/MCP-tool-routing ambiguity** — `codex_mcp_proxy.py`'s own "KNOWN OPEN RISK" section:
   Codex may reach for its own native shell/file tools instead of the MCP-registered `claude_tools`
   server, and `Sandbox.read_only` only partially guards against it. **Real measured cost, this
   session**: slot 31 stuck retrying a heartbeat for ~70 minutes, ~1.85M input tokens, because the
   command intermittently ran through the sandboxed native path instead of the unrestricted MCP path.
   Full detail: `codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md`.
2. **Per-turn streaming-fallback tax** — `codex_mcp_tool_use_bridge_2026_08_18.md`'s own validation
   run: a real `?beta=true` streaming attempt got this bridge's honest `501`, and the CLI
   transparently fell back to non-streaming — "costs one wasted round trip per turn." Never
   quantified in tokens; likely small per-turn but compounds over a long session (see todo below).
3. **No incremental thread reuse** — `codex_mcp_proxy.py`'s own docstring: every tool_use/tool_result
   pair spins up a NEW Codex thread rather than continuing the live one, because Claude Code's
   two-separate-HTTP-calls tool-use model doesn't map onto Codex's synchronous in-thread MCP call.
   Flagged there as "still real, still deliberately unaddressed" — never estimated in token cost.

None of these 3 exist for any other AO-dispatched provider (DeepSeek/GLM/Gemini/Kimi/Gemma) — they
are specific to translating Claude Code's protocol onto Codex's structurally different one. Running
Luna through Codex's OWN native CLI (the way a human uses `codex` directly, no translation) would
very likely eliminate all 3 at once, not just the sandbox bug — because none of them would have a
reason to exist without the translation layer in between.

## The decision this doc exists to surface

**This is NOT a recommendation to switch.** The bridge exists because of a standing, explicitly
twice-invoked requirement (`codex_luna_flex_bridge_2026_08_14.md`, 2026-08-14 operator ruling):

> "Claude Code's harness — CLAUDE.md, skills, hooks, slash commands — must not be reengineered for
> any new provider; every provider must present as if it's just another Claude account."

...and the SAME session explicitly ruled out an analogous native-harness path for a different
provider on exactly this basis:

> "Ruled out this session: xAI's SuperGrok+OpenCode subscription integration (a DIFFERENT open-source
> coding harness, not an API facade — bridging into it would mean running a second, competing agent
> harness, which conflicts with the 'stays Claude Code' requirement)."

Native Codex CLI is the same category of thing for Codex/Luna that OpenCode was for Grok — a
different harness, not a REST facade. Switching would mean AO permanently maintains a SECOND,
bespoke worker-fleet integration (spawn, liveness, context/token tracking, task dispatch, role
instructions) alongside the uniform Claude-Code-CLI one every other provider shares — not a config
flag. Today's new token-cost evidence is real and worth weighing, but it does not by itself settle
whether that permanent maintenance cost is worth paying for one provider.

## What's genuinely unknown and needs research before the operator can decide

None of these are answered in either existing bridge plan — they were never asked, because the
"stays Claude Code" requirement made native CLI out of scope from the start:

- Does Codex CLI support an AO-equivalent of CLAUDE.md / per-repo standing instructions at all
  (OpenAI's own docs may name a specific convention — verify, don't assume it matches Claude's)?
- Does it support anything equivalent to skills/slash-commands (`/pre-compact`, the heartbeat
  convention, `/done`/`/blocked`), or would AO's whole worker-lifecycle protocol need a parallel
  reimplementation for this one provider?
- Does it emit a parseable session/transcript log AO could read for context-window tracking and
  token accounting (`context_probe.py`'s entire mechanism assumes Claude Code's JSONL shape) — or
  would that be built from scratch too?
- Does it support a genuinely headless/non-interactive dispatch mode compatible with AO's
  spawn-assign-work-signal-done tmux lifecycle, the same way `claude -p
  --dangerously-skip-permissions` does today?
- Under Codex CLI's OWN normal (non-bridged) sandbox/approval defaults for a real coding session, is
  network/heartbeat-shaped traffic actually reliable — or does native Codex CLI have the same
  approval-gate friction observed today, just without the bridge to blame?

## Todos

- [ ] [OPERATOR] P2. Decide: is this worth a dedicated research spike to answer the unknowns above
      before any build commitment, or does the "stays Claude Code" requirement stand as-is given the
      permanent-maintenance cost of a second harness? Done when: an explicit ruling is recorded here
      (mirroring the 2026-08-14 OpenCode ruling's own format), whichever way it goes.
- [ ] [REVIEW] P3. IF the operator wants the spike: scope it as a small, time-boxed research pass
      (not a build) against the 5 unknowns above, using OpenAI's own current Codex CLI docs — done
      when each unknown has a real, cited answer (or a confirmed "undocumented, would need a live
      probe"), not a guess.
- [ ] [REVIEW] P3. Quantify todo-2 and todo-3's per-turn token cost for real (currently qualitative
      only in both source plans) — a real multi-turn Codex/Luna session, comparing observed
      input-token deltas against what a non-bridged provider's equivalent turn costs, so the
      operator's decision has a real number for "how much is the bridge itself costing us today",
      not just "some, unquantified."

## Progress Log

- **2026-08-20**: filed following the operator's direct request to capture findings/decision not
  already in the two bridge plans, after the slot-31 heartbeat investigation. No code changed; no
  research spike started — that's explicitly gated on the `[OPERATOR]` todo above.
