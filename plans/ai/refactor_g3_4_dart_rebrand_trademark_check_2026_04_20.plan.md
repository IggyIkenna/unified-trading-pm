---
title: Refactor G3.4 — DART marketing-copy rebrand + trademark check
status: active
priority: P1
owner: marketing + ops + agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §3.4
# Wave G3-α — independent, parallel with G3.2/3.3/3.5/3.6.
---

# Refactor G3.4 — DART marketing-copy rebrand + trademark check

## Context

Stage 3E §3.4 completes the DART rebrand. Nav label already replaced "Platform" → "DART" in UI
(`components/shell/nav-copy.ts` — shipped Phase 3). Marketing static pages + website + briefings still use "Platform" in
places. A trademark search under UKIPO / USPTO is needed (per 2026-04-19 memory: HSBC DART is non-competing on web
check; file formal search as an institutional record). Optional domain registration at `dart.odum.com`.

Target: complete marketing copy sweep across all external surfaces; formal trademark search filed; domain
`dart.odum.com` registered + redirect configured.

## Decisions locked with user (2026-04-20)

| Decision                                                         | Chosen                                                                                    | Source                     |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------- |
| "DART" = Data Analytics, Research & Trading                      | Canonical expansion; used in rebrand copy                                                 | Playbook SSOT (Stage 1)    |
| Trademark check at UKIPO + USPTO                                 | Both jurisdictions; HSBC DART appears non-competing on informal check                     | 2026-04-19 memory          |
| Domain `dart.odum.com`                                           | 301 redirect to canonical `/platform` or `/dart` landing (operator decides final landing) | Stage 3E §3.4 domain note  |
| Copy sweep scope: marketing-static + briefings + SEO metadata    | Full public-surface sweep; briefings come post-G3.3 migration                             | Stage 3E §3.4 blast radius |
| Agent-side: copy sweep + redirects; operator: trademark + domain | Split organisational vs engineering work                                                  | Stage 3E §3.4 ownership    |

## Cross-references

- **Upstream:** G1.12 public-site IA + briefings polish (cleanup target)
- **Wave G3-α peers (parallel):** G3.2, G3.3, G3.5, G3.6
- **Codex:** `/codex/14-playbooks/experience/marketing-journey.md`
- **Memory:** 2026-04-19 DART naming + HSBC non-competing note

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §3.4
2. `/codex/14-playbooks/experience/marketing-journey.md`
3. `unified-trading-system-ui/components/shell/nav-copy.ts` — already uses "DART"
4. `unified-trading-system-ui/app/(marketing)/` or `marketing-static/` directories — all external pages
5. `unified-trading-system-ui/next.config.mjs` — redirect config
6. `unified-trading-system-ui/app/api/` — SEO metadata sources

## Out of scope

- Logo / branding visual assets (separate marketing initiative)
- Press release or PR campaign (marketing ops)
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — Copy audit

- [ ] [AGENT] P0. Grep-inventory every "Platform", "platform", "the platform" in `app/(marketing)/`,
      `marketing-static/`, `components/marketing/`, briefings content (G3.3 YAML), SEO metadata.
- [ ] [AGENT] P0. Produce audit report: file × line × current text × proposed DART-branded replacement.

### Phase B — Copy sweep

- [ ] [AGENT] P0. Update all marketing-static + briefings content + SEO metadata per audit report.
- [ ] [AGENT] P0. `<meta name="description">`, OpenGraph titles, canonical URLs all reflect "DART" framing.
- [ ] [AGENT] P0. Internal-only codex docs: update `marketing-journey.md` to describe the DART-framed journey.

### Phase C — Trademark check (operator-led)

- [ ] [OPERATOR] P0. File formal trademark search at UKIPO (`https://trademarks.ipo.gov.uk/`).
- [ ] [OPERATOR] P0. File formal trademark search at USPTO (`https://tmsearch.uspto.gov/`).
- [ ] [OPERATOR] P0. Document results in `/codex/14-playbooks/_internal/dart-trademark-check.md` (internal-only).

### Phase D — Domain setup (operator + agent)

- [ ] [OPERATOR] P0. Register `dart.odum.com` via Odum's DNS provider.
- [ ] [AGENT] P0. Configure 301 redirect from `dart.odum.com` → canonical landing (choose `/platform` or `/dart` per
      operator).
- [ ] [AGENT] P0. Add redirect to Cloud Run / deployment-service config.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g3-4-dart-rebrand.spec.ts` — public-site sweep asserts no stale "Platform"
      references.
- [ ] [AGENT] P0. Domain smoke: `curl -I https://dart.odum.com` returns 301.

## Critical files to be modified

- `unified-trading-system-ui/app/(marketing)/**` — MODIFY (copy sweep)
- `unified-trading-system-ui/marketing-static/**` — MODIFY (copy sweep)
- `unified-trading-system-ui/components/marketing/**` — MODIFY (copy sweep)
- `unified-trading-system-ui/lib/seo/metadata.ts` (or equivalent) — MODIFY
- `unified-trading-system-ui/next.config.mjs` — MODIFY (domain redirect)
- `deployment-service/config/cloud-run-routes.yaml` (or equivalent) — MODIFY
- `/codex/14-playbooks/experience/marketing-journey.md` — MODIFY (DART framing)
- `/codex/14-playbooks/_internal/dart-trademark-check.md` — NEW (operator)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-4-dart-rebrand.spec.ts` — NEW

## Execution DAG

```
A (audit) → B (copy sweep) + C (trademark — operator) + D (domain — operator + agent) [parallel]
              ↓
            E (QG + Playwright + domain smoke)
```

## Verification

1. Grep: zero stale "Platform" (as trading-platform product label) references in external surfaces.
2. SEO meta tags reflect DART framing.
3. Trademark search filed + results archived in `_internal/`.
4. `dart.odum.com` 301 redirects to canonical landing.
5. Playwright spec green.
6. UI QG green.

## Handoff

Unblocks:

- **pb1 `marketing-journey.md`** — DART-framed top-of-funnel.
- **Future DART Signals-Out expansion** — brand consistency established.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools; crawl every marketing-static page +
briefings hub; assert no "Platform" product-label occurrences in rendered DOM text (whitelisted exceptions: "trading
platform" as a generic noun in specific contexts — document exclusions).

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-4-dart-rebrand.spec.ts`:

1. Crawl marketing-static + briefings hub + per-briefing pages.
2. Assert no stale "Platform" product references (honour whitelist).
3. Assert SEO meta tags contain "DART".
4. Visit `dart.odum.com` (when live) — assert 301.
5. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G3.4 (Wave G3-α, operator +
agent).**

---

You are executing **Refactor G3.4 — DART marketing-copy rebrand + trademark check** for the Unified Trading System at
Odum Research. Wave G3-α. Phases A, B, D (partial), E are agent-led. Phases C (trademark) + D (domain registration) are
operator-led.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
grep -rn "Platform" unified-trading-system-ui/app/\(marketing\)/ unified-trading-system-ui/marketing-static/ 2>/dev/null | head -20
ls unified-trading-system-ui/components/shell/nav-copy.ts
```

All must exist. STOP if missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute Phases A, B, D (redirects only), E of this plan. Phases C + D (domain registration) are operator-led.

### Read-set (mandatory)

All 6 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — spans UI repo + codex + deployment-service.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools; crawl every marketing-static + briefings page; assert no stale
"Platform" occurrences in rendered DOM. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-4-dart-rebrand.spec.ts` — crawl + DOM-text
assertion + SEO metadata check + optional domain smoke, wired into `scripts/quality-gates.sh`.

### Commit strategy

Two repos → two commits (codex + UI; deployment-service if domain redirect lands).

```
cd unified-trading-pm && bash scripts/quickmerge.sh "docs(codex/marketing): G3.4 — DART framing updates + trademark-check doc stub" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(marketing): G3.4 — DART rebrand copy sweep + Playwright coverage" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Zero stale "Platform" product-label references after sweep (whitelist documented).
2. ✅ SEO meta tags contain "DART".
3. ✅ Playwright spec green.
4. ✅ UI QG green.
5. ✅ 2 commit SHAs pushed.
6. ✅ Trademark-check doc stub committed (operator populates post-filing).
7. ✅ Domain redirect config committed if operator has registered.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT change logo / branding visuals (separate marketing initiative).
- Do NOT ship copy changes without the audit report as traceability.
- Do NOT delete trademark-check doc — operator populates post-filing.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Audit report: total "Platform" matches + whitelist exclusions.
- Copy sweep diff stats.
- Trademark-check doc committed.
- Domain redirect smoke (if domain registered).
- Playwright spec pass status.
- UI QG results.
- 2 commit SHAs pushed to live-defi-rollout.
