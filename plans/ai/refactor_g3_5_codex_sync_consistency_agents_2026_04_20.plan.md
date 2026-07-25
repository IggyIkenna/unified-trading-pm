---
title: Refactor G3.5 — Codex-sync + playbook consistency agents
status: active
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §3.5
# Wave G3-α — independent, parallel with G3.2/3.3/3.4/3.6. Addresses stale-plan-vs-shipped-code institutional failure mode.
---

# Refactor G3.5 — Codex-sync + playbook consistency agents

## Context

Stage 3E §3.5 ships automated agents that verify codex + playbook consistency. G1 surfaced the "stale-plan-vs-shipped-
code" failure mode as the dominant institutional defect: plan files claiming fake SHAs, orphaned staged files, commit
messages that don't match codex changes, rule citations pointing at stale sections after rule renumbering.

Target: a `playbook-consistency-agent` (part of the `plan-health-agent` family) that runs on merges to
`codex/14-playbooks/` and verifies:

1. Rule citations still point to live rule sections (no rule-11 citation if rule 12 is the current slot).
2. Experience playbook structural grammar (9 sections per rule 01).
3. Demo-restriction-profile references are valid.
4. SHAs cited in plan prose resolve via `git cat-file -t`.
5. Orphan staged files flagged (files touched by multiple agents with no owning plan).
6. Cross-codex internal links resolve.
7. Plan checkbox state matches shipped code (best-effort heuristic — e.g., declaring a file exists).

## Decisions locked with user (2026-04-20)

| Decision                                                           | Chosen                                                                      | Source                     |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------- | -------------------------- |
| Lives in `plan-health-agent` family (existing agent infra)         | Reuse GHA infra; no new repo                                                | Stage 3E §3.5 "part of..." |
| Runs on merges to `codex/14-playbooks/`                            | Catches drift immediately after merge; blocks PR if critical                | Stage 3E §3.5              |
| Failures: warn by default, block on critical (broken cites / SHAs) | Graduated enforcement; don't stop merges on noise                           | Operator deferral          |
| Audit checks codified in a rules file                              | `codex/14-playbooks/_ssot-rules/_consistency-checks.yaml` lists every check | SSOT pattern               |
| Addresses G1 stale-plan-vs-shipped-code failure                    | Primary motivation — never let a plan claim a SHA that isn't real           | G1 Wave C+D audit memory   |

## Cross-references

- **Wave G3-α peers (parallel):** G3.2, G3.3, G3.4, G3.6
- **G3.3 dep:** codex ↔ YAML briefings parity (consumed by this agent)
- **Existing infra:** `unified-trading-pm/scripts/agents/` + `plan-health-agent` GHA workflow
- **Memory sources:** `project_g1_refactor_wave_c_d_audit_2026_04_20.md`, `project_g1_wave_e_closure_2026_04_20.md`

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §3.5
2. `unified-trading-pm/scripts/agents/` — existing agent infrastructure
3. `codex/14-playbooks/_ssot-rules/` — all 12 rules (consistency targets)
4. `codex/14-playbooks/experience/` — playbooks (structural grammar targets)
5. `/codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md`
6. `/codex/14-playbooks/_ssot-rules/01-briefing-structure-grammar.md` — 9-section grammar

## Out of scope

- Autonomous plan-mutation (agent flags, humans fix)
- Real-time (sub-minute) drift detection
- Integration with external monitoring (Datadog, PagerDuty)
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Check specification

- [ ] [AGENT] P0. `codex/14-playbooks/_ssot-rules/_consistency-checks.yaml` — declarative list of checks:
      `{id, description, severity, target_glob, rule_file, impl_function}`.
- [ ] [AGENT] P0. Minimum 7 checks from Context list above.

### Phase B — Agent implementation

- [ ] [AGENT] P0. `unified-trading-pm/scripts/agents/playbook_consistency_agent.py` — reads the YAML, runs each check,
      emits markdown report.
- [ ] [AGENT] P0. Per-check impls in `unified-trading-pm/scripts/agents/checks/`: rule-citations.py, section-grammar.py,
      sha-validity.py, orphan-files.py, cross-links.py, restriction-profile-refs.py, plan-checkbox-reality.py.
- [ ] [AGENT] P0. CLI: `python playbook_consistency_agent.py --fail-on critical|warn` for CI integration.

### Phase C — GHA workflow

- [ ] [AGENT] P0. `.github/workflows/playbook-consistency-agent.yml` in unified-trading-pm — triggers on push to
      `codex/14-playbooks/**` or `plans/active/**`. Runs agent; posts markdown report as PR comment.
- [ ] [AGENT] P0. Critical-severity failures block PR; warnings informational.

### Phase D — Initial sweep

- [ ] [AGENT] P0. Run agent on current `live-defi-rollout` state. Produce baseline report.
- [ ] [AGENT] P0. Fix any critical-severity findings before landing the agent (bootstrap: agent must pass on its own
      landing commit).

### Phase E — QG + documentation

- [ ] [AGENT] P0. Codex doc `/codex/14-playbooks/_ssot-rules/_consistency-agent-guide.md` — describes the agent, how to
      add a check, how to interpret reports.
- [ ] [SCRIPT] P0. `cd unified-trading-pm && bash scripts/quality-gates.sh`

## Critical files to be modified

- `unified-trading-pm/scripts/agents/playbook_consistency_agent.py` — NEW
- `unified-trading-pm/scripts/agents/checks/` — 7 check modules, NEW
- `unified-trading-pm/scripts/agents/tests/test_playbook_consistency_agent.py` — NEW
- `unified-trading-pm/.github/workflows/playbook-consistency-agent.yml` — NEW
- `codex/14-playbooks/_ssot-rules/_consistency-checks.yaml` — NEW
- `/codex/14-playbooks/_ssot-rules/_consistency-agent-guide.md` — NEW

## Execution DAG

```
A (check spec) → B (agent + per-check impls) → C (GHA workflow)
                                                  ↓
                                                D (initial sweep + fix findings)
                                                  ↓
                                                E (docs + QG)
```

## Verification

1. ≥7 consistency checks declared + implemented.
2. Agent passes on its own landing commit (bootstrap check).
3. GHA workflow runs on push to codex/14-playbooks/ or plans/active/.
4. Baseline report archived.
5. PM QG green.

## Handoff

Unblocks:

- **Long-term playbook maintenance** — drift detected within minutes of landing.
- **G1 stale-plan-vs-shipped-code failure mode** — formally guarded.
- **Future waves** — new rules + plans get structural validation automatically.

## Playwright test coverage (mandatory)

**MCP Playwright:** not primarily a UI-facing change. The "test" is the agent's own test suite + GHA validation.

**Durable spec for CI:** `unified-trading-pm/scripts/agents/tests/test_playbook_consistency_agent.py` +
`.github/workflows/playbook-consistency-agent.yml`:

1. Unit tests: each check module has ≥3 cases (pass + fail + edge).
2. Integration: agent runs against fixture codex snapshot with known defects; asserts correct findings.
3. GHA smoke: CI job runs on PR; report rendered as comment.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G3.5 (Wave G3-α).**

---

You are executing **Refactor G3.5 — Codex-sync + playbook consistency agents** for the Unified Trading System at Odum
Research. Wave G3-α; independent.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
ls unified-trading-pm/scripts/agents/  # existing agent infra
ls unified-trading-pm/.github/workflows/  # existing GHA
ls codex/14-playbooks/_ssot-rules/
```

All must exist. STOP if missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g3_5_codex_sync_consistency_agents_2026_04_20.md`

### Read-set (mandatory)

All 6 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 7+ files in PM repo.

### MCP Playwright clause (verbatim — REQUIRED)

Not primarily a UI surface. Use MCP Playwright only if any UI dashboard surfaces consistency-agent reports; otherwise
the agent's unit + integration tests + GHA workflow smoke serve as the verification surface.

### Commit strategy

One commit in PM repo.

```
cd unified-trading-pm && bash scripts/quickmerge.sh "feat(agents): G3.5 — playbook-consistency-agent + 7 checks + GHA workflow" --agent
```

Manual-git fallback. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ ≥7 checks declared + implemented.
2. ✅ Agent bootstrap: passes on its own landing commit.
3. ✅ GHA workflow runs on codex/plans pushes.
4. ✅ Baseline report archived.
5. ✅ PM QG green.
6. ✅ 1 commit SHA pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT have agent mutate plan files — flag only; humans fix.
- Do NOT block PRs on warn-level findings — only critical.
- Do NOT hard-code check thresholds — use the YAML spec.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Check count + severity breakdown.
- Baseline report summary.
- GHA workflow job ID.
- Bootstrap-pass verification.
- PM QG results.
- 1 commit SHA pushed to live-defi-rollout.
