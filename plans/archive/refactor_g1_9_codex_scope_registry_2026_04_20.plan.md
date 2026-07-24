---
doc_type: plan
title: Refactor G1.9 — Codex scope registry (per-audience documentation surface)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  [
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.9,
    codex/14-playbooks/_ssot-rules/ (all 10 rules),
    codex/00-SSOT-INDEX.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.9 — Codex scope registry (per-audience documentation surface)

## Context

Stage 3E §1.9 codifies a per-audience documentation surface: the codex contains material whose audience is mixed — some
sections are public (sales / prospect), some engineer-only, some admin-only, some investor. Today every codex doc is
readable by anyone with repo access, and docs with mixed audiences interleave commercial, technical, and
commercial-sensitive content without a machine-readable scope tag. The codex-scope-registry establishes a declarative
`scope:` frontmatter field on every codex doc (audience enumerated) plus a build-step gate that filters doc content by
audience when codex material is surfaced to downstream consumers (the playbook tooling, sales collateral generators, the
customer-facing help surfaces in unified-trading-system-ui).

## Decisions locked with user (2026-04-20)

| Decision                                                                                           | Chosen                                                             | Source                        |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------- |
| Scope enum                                                                                         | `scope ∈ {sales, engineer, admin, prospect, investor}`             | Kickoff §1.9                  |
| Applied as frontmatter `scope: [a, b, c]` on every codex doc                                       | Machine-readable; default = `[engineer, admin]` if absent          | Kickoff §1.9                  |
| Build-step gate lives in `codex/14-playbooks/_ssot-rules/` + surfaced via `codex/00-SSOT-INDEX.md` | Tool walks frontmatter, emits per-audience manifest                | Kickoff §1.9                  |
| Codex stays in-repo; audience filter runs at consumption time, not storage time                    | No forking of the codex per audience — same source, filtered views | Rule 03 same-system-principle |

## Cross-references

- **Sibling Wave A plans:** refactor*g1*{1,3,5,12,14}\_2026_04_20.md
- **Rules cited:** `_ssot-rules/02-tone-and-posture.md`, `_ssot-rules/06-show-dont-show-discipline.md`,
  `_ssot-rules/07-data-licensing-boundaries.md`, `_ssot-rules/09-internal-commercial-oneliners.md`
- **SSOT index:** `codex/00-SSOT-INDEX.md`
- **Parent stage plan:** `plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.md` §3E

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.9
2. `codex/00-SSOT-INDEX.md`
3. All 10 files in `codex/14-playbooks/_ssot-rules/` (01–10 + README)
4. `/codex/14-playbooks/README.md`
5. `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md`

## Out of scope

- Encrypting codex material by audience — filtering, not gating. Engineers with repo access can see everything
  regardless.
- Building a codex CMS / web frontend — registry + manifest tool only.
- Adjusting existing codex content tone — refactor_g1_12 handles public-site tone polish.
- Migrating codex out of the monorepo / repo — stays where it is.

## Phase breakdown

### Phase 9A — Define the scope frontmatter schema

- [x] [AGENT] P0. Write `/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md` documenting the scope enum +
      frontmatter shape + default behaviour.
- [x] [AGENT] P0. Schema: `scope: [sales, engineer, admin, prospect, investor]` (array subset of enum; defaults to
      `[engineer, admin]` if omitted).
- [x] [AGENT] P0. Add a 30-line example-per-audience block to rule 11.

### Phase 9B — Build the manifest-emitter tool

- [x] [AGENT] P0. Script at `codex/14-playbooks/_tools/build-scope-manifest.sh` (or Python equivalent at
      `_tools/build_scope_manifest.py`) — walks `codex/**/*.md`, reads frontmatter, emits
      `codex/14-playbooks/_generated/scope-manifest.json`.
- [x] [AGENT] P0. Manifest shape: `{[audience]: string[]}` — each audience maps to the paths of codex docs visible to
      it.
- [x] [AGENT] P0. Tool fails loud on invalid frontmatter (unknown scope value, malformed YAML).

### Phase 9C — Backfill scope frontmatter on existing codex

- [x] [AGENT] P0. Enumerate every `codex/**/*.md` without `scope:` frontmatter → list in `/tmp/g1_9_backfill.md`.
- [x] [AGENT] P0. Batch classify: `codex/14-playbooks/experience/*` → `[sales, prospect]`;
      `codex/14-playbooks/demo-ops/*` → `[sales, engineer, admin]`; `codex/09-strategy/**` → `[engineer, admin]`; etc.
      Full mapping in rule 11.
- [x] [AGENT] P0. Apply frontmatter patches — one commit per logical batch (do not one-line 500 files).

### Phase 9D — Wire into SSOT index + CI gate

- [x] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` to register rule 11 + the manifest tool + the generated manifest path.
- [x] [AGENT] P0. Add a `codex/14-playbooks/_tools/check-scope-coverage.sh` script that fails CI if any codex doc lacks
      `scope:` frontmatter.
- [x] [SCRIPT] P0. Hook check-scope-coverage.sh into `unified-trading-pm/scripts/quality-gates.sh`.

### Phase 9E — Verify

- [x] [SCRIPT] P0. Run `bash codex/14-playbooks/_tools/build-scope-manifest.sh` — produces valid JSON manifest.
- [x] [SCRIPT] P0. Run `bash codex/14-playbooks/_tools/check-scope-coverage.sh` — zero failures.
- [x] [SCRIPT] P0. Run PM QG — `cd unified-trading-pm && bash scripts/quality-gates.sh`.

## Critical files to be modified

- `/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md` — NEW
- `codex/14-playbooks/_tools/build-scope-manifest.sh` (or `.py`) — NEW
- `codex/14-playbooks/_tools/check-scope-coverage.sh` — NEW
- `codex/14-playbooks/_generated/scope-manifest.json` — GENERATED (committed)
- `codex/00-SSOT-INDEX.md` — MODIFY
- `unified-trading-pm/scripts/quality-gates.sh` — MODIFY (hook the check)
- Every `codex/**/*.md` lacking `scope:` frontmatter — MODIFY (backfill)

## Execution DAG

```
9A (schema)  →  9B (tool)  →  9C (backfill)  →  9D (SSOT + CI gate)  →  9E (verify)
```

Phases are strictly sequential — the tool depends on the schema being stable, the backfill depends on the tool, and the
CI gate depends on the backfill being complete (else gate fails).

## Verification

1. `/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md` exists and passes markdown lint.
2. `bash codex/14-playbooks/_tools/build-scope-manifest.sh` produces valid JSON — pipe through `jq .` to confirm.
3. `bash codex/14-playbooks/_tools/check-scope-coverage.sh` exits 0 (no uncovered docs).
4. `codex/00-SSOT-INDEX.md` has a new entry for rule 11 + tool + manifest.
5. PM QG green.

## Handoff

Unblocks:

- **G2.x** — sales-collateral generator (consumes manifest to filter codex by prospect audience).
- **G2.x** — customer-facing help surface in `unified-trading-system-ui` (consumes manifest to filter codex by prospect
  / investor audience).
- **Future rules:** downstream rules can reference rule 11 when they need to gate content by audience.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** Not applicable in the traditional sense — this is a codex tooling refactor, no UI
surface. However, if the UI help surface consumes the generated manifest in a follow-up, the Playwright spec covers that
consumer. For THIS plan, Playwright covers the CI-gate integration end: spin up a minimal fixture where a codex doc
lacks frontmatter, assert `check-scope-coverage.sh` exits non-zero, and the QG step fails correctly.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-9-codex-scope-registry.spec.ts` — must:

1. Seed an `admin` persona via `tests/e2e/playbooks/seed-persona.ts` (manifest is admin-scope).
2. (If the UI surface consumes the manifest) navigate to the help / briefings surface and assert sales-scope docs are
   visible to a `prospect-im` seed, admin-scope docs are NOT visible.
3. (If not yet consumed in UI) spec includes a shell-out to `bash codex/14-playbooks/_tools/check-scope-coverage.sh`
   that asserts exit 0 after backfill.
4. Assert visibility-slicing vs G1.6 `access_control` formula once G1.6 lands; until then, stub.
5. Include an orphan-reachability assertion on any new pages referenced via the manifest.
6. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.9 (Wave A, standalone — no
dependencies on other G1 items).**

---

You are executing **Refactor G1.9 — Codex scope registry** for the Unified Trading System at Odum Research. Wave A;
parallelisable with 1.1, 1.3, 1.5, 1.12, 1.14-markdown.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git checkout live-defi-rollout && git pull
ls codex/14-playbooks/_ssot-rules/ | wc -l  # expect 11 (10 rules + README)
ls codex/00-SSOT-INDEX.md
ls scripts/quality-gates.sh
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 9A through 9E of this plan:
`plans/active/refactor_g1_9_codex_scope_registry_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 5 + every doc under `codex/**/*.md` lacking `scope:` frontmatter (for the
backfill pass).

### Deliverables

- New: `/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md`
- New: `codex/14-playbooks/_tools/build-scope-manifest.sh` (or `.py`)
- New: `codex/14-playbooks/_tools/check-scope-coverage.sh`
- Generated + committed: `codex/14-playbooks/_generated/scope-manifest.json`
- Modified: `codex/00-SSOT-INDEX.md`, `scripts/quality-gates.sh`, every codex doc needing backfill
- New test: `tests/e2e/playbooks/refactor/refactor-g1-9-codex-scope-registry.spec.ts`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools if the UI help surface consumes the manifest in this scope; otherwise the spec covers the CI-gate
integration (a fixture codex doc lacking frontmatter fails `check-scope-coverage.sh`). Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-9-codex-scope-registry.spec.ts` — seed relevant
personas via `tests/e2e/playbooks/seed-persona.ts`, walk canonical click-path (if UI consumer exists), assert
visibility-slicing vs G1.6 `access_control` formula (stub until G1.6 lands), include orphan-reachability assertion, wire
into `scripts/quality-gates.sh`.

### Commit strategy

Logical batches — one commit per batch to keep diffs reviewable.

```
cd unified-trading-pm
# batch 1: rule 11 + tool
bash scripts/quickmerge.sh "docs(codex/playbooks): G1.9 — rule 11 codex scope registry + manifest tool" --agent --files "/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md codex/14-playbooks/_tools/ codex/14-playbooks/_generated/"

# batch 2: backfill by domain (one commit per major domain dir)
bash scripts/quickmerge.sh "docs(codex): G1.9 backfill scope frontmatter — 09-strategy/" --agent --files "codex/09-strategy/"
bash scripts/quickmerge.sh "docs(codex): G1.9 backfill scope frontmatter — 14-playbooks/experience/" --agent --files "codex/14-playbooks/experience/"
# ...etc. per domain

# batch 3: SSOT index + QG hook
bash scripts/quickmerge.sh "docs(codex): G1.9 — register rule 11 in SSOT-INDEX + hook CI gate" --agent --files "codex/00-SSOT-INDEX.md scripts/quality-gates.sh"
```

Fallback if quickmerge blocked: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`.
Never `--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ Rule 11 file exists + passes markdown lint.
2. ✅ `bash _tools/build-scope-manifest.sh` produces valid JSON (`jq .` clean).
3. ✅ `bash _tools/check-scope-coverage.sh` exits 0.
4. ✅ SSOT index has new entry for rule 11.
5. ✅ PM QG green.
6. ✅ Commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT fork the codex per audience — single source, filtered views.
- Do NOT encrypt or auth-gate codex content — filter only.
- Do NOT adjust existing codex tone/content in this refactor — refactor_g1_12 owns public-site tone polish.
- Do NOT one-line 500-file backfill commits — one commit per domain.

### Report back

- Rule 11 file path + line count.
- Manifest tool path + manifest JSON excerpt (5 lines).
- Backfill count per domain.
- Playwright spec path + pass status.
- Commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.
