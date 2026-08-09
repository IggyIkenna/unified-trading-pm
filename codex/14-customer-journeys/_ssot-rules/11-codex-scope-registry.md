---
doc_type: codex-ssot
title: Rule 11 — Codex scope registry (per-audience documentation surface)
summary:
  "Rule 11 — the machine-readable per-audience scope frontmatter tag (scope ∈ {sales, engineer, admin, prospect,
  investor}) on every codex doc; default [engineer, admin], a per-directory default mapping, and build-manifest +
  CI-gate consumption. One source, filtered views at read time."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, codex, governance, docspec, sales]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md,
    /codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md,
  ]
created: 2026-04-20
authoritative_for: [codex per-audience scope registry (scope frontmatter tag + per-directory defaults)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
  ]
owner:
last_reviewed:
code_refs:
  [codex/14-customer-journeys/_tools/build-scope-manifest.sh, codex/14-customer-journeys/_tools/check-scope-coverage.sh]
---

# Rule 11 — Codex scope registry (per-audience documentation surface)

> **Status:** active — Stage 3E G1.9 landing commit. **Parent plan:**
> `plans/archive/refactor_g1_9_codex_scope_registry_2026_04_20.plan.md`. **Spec reference:**
> `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.9.

## Why this rule exists

The codex is a single source of truth but its readership is mixed — engineering, admin, sales, external prospects, and
investors all pull from the same tree. Today every doc is readable by anyone with repo access, and when a client-facing
surface (sales collateral generator, help drawer in `unified-trading-system-ui`, investor briefing PDF) tries to embed
codex content, it either copies the markdown verbatim (leaking internal cost commentary — see
[rule 07 (data licensing boundaries)](07-data-licensing-boundaries.md),
[rule 09 (internal commercial one-liners)](09-internal-commercial-oneliners.md),
[rule 06 (show / don't-show discipline)](06-show-dont-show-discipline.md)) or has to forego codex altogether.

Rule 11 fixes that by declaring a **machine-readable audience tag** on every codex doc. The codex stays where it is —
one source, filtered views at consumption time. See [rule 03 (same-system principle)](03-same-system-principle.md): one
system, partitioned views.

## The scope enum

```
scope ∈ { sales, engineer, admin, prospect, investor }
```

| Audience   | Who sees it                                                                             | Typical content                                                                                   |
| ---------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `sales`    | Internal sales + prospects via sales-collateral generator                               | DART commercial axes, building-block packaging, demo click paths                                  |
| `engineer` | Internal engineering                                                                    | Architecture, infra, coding standards, service setup, quality gates                               |
| `admin`    | Internal admin + ops                                                                    | Deployment runbooks, secret rotation, audit procedures, ops matrix                                |
| `prospect` | External anonymous / post-first-call prospects via public marketing + briefing surfaces | Public-facing platform claims, what Odum does, glossary, high-level catalogues                    |
| `investor` | External investors (board presentations, investor-relations surfaces)                   | Fund-level reporting, org/fund/client hierarchy, regulated umbrella framing, presentation content |

Scopes are an **array subset** of the enum. A doc may be visible to multiple audiences:

```yaml
---
scope: [engineer, admin]
---
```

Or sales + prospect:

```yaml
---
scope: [sales, prospect]
---
```

Engineers always see everything regardless of scope — repo access is the hard gate; scope is the consumption filter. The
registry never **hides** content from engineers; it filters what the sales-collateral generator / help-surface consumer
emits.

## Default behaviour

A doc with **no `scope:` frontmatter** defaults to `[engineer, admin]`. Rationale: codex content written before this
rule existed is overwhelmingly engineering-internal. Defaults make the rule backwards-compatible while the backfill pass
completes; after Phase 9C every doc has explicit scope, so the default only fires on brand-new docs that the author
forgot to tag (and the CI gate — see Phase 9D — catches that).

## Frontmatter shape

YAML frontmatter, array form, at the top of every codex `*.md`:

```yaml
---
scope: [engineer, admin]
---
# Doc title

...body...
```

Validator tolerates:

- Array form: `scope: [engineer, admin]`
- Flow-list form: `scope:\n - engineer\n - admin`
- Empty array: `scope: []` — explicit opt-out (no audience sees it; internal-only by repo access)

Validator rejects:

- Scalar: `scope: engineer` (must be array)
- Unknown values: `scope: [intern]` (not in the enum)
- Malformed YAML in the frontmatter block

## Default mapping per directory

When backfilling (Phase 9C), apply these defaults per top-level directory. Each is a rebuttable default — a specific doc
can override if it genuinely serves a different audience.

| Codex subdir                                       | Default scope                 | Rationale                                                                                   |
| -------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------- |
| `00-SSOT-INDEX.md`                                 | `[engineer, admin]`           | Navigation index for internal readers                                                       |
| `00-getting-started/`                              | `[engineer]`                  | New-engineer onboarding                                                                     |
| `01-domain/`                                       | `[engineer]`                  | Instrument schemas, domain types                                                            |
| `02-data/`                                         | `[engineer, admin]`           | Data catalogues, schema governance, availability manifests                                  |
| `02-venues/`                                       | `[engineer, admin]`           | Per-venue adapter notes                                                                     |
| `03-observability/`                                | `[engineer, admin]`           | Events, lifecycle, logging                                                                  |
| `03-services/`                                     | `[engineer]`                  | Service specs                                                                               |
| `04-architecture/`                                 | `[engineer, admin]`           | Tier architecture, topology, separation of concerns                                         |
| `05-infrastructure/`                               | `[engineer, admin]`           | Deployment, CI/CD, secrets, auth setup                                                      |
| `06-coding-standards/`                             | `[engineer]`                  | Code conventions                                                                            |
| `07-security/`                                     | `[engineer, admin]`           | Secrets, auth, compliance                                                                   |
| `08-workflows/`                                    | `[engineer, admin]`           | Local dev, quickmerge, quality gates                                                        |
| `09-strategy/`                                     | `[engineer, admin]`           | Strategy engine internals; catalogue-strategy.md specifically is `[engineer, admin, sales]` |
| `10-audit/`                                        | `[engineer, admin]`           | Audit reports, compliance checklists                                                        |
| `11-project-management/`                           | `[engineer, admin]`           | Plan registry, planning standards                                                           |
| `12-agent-workflow/`                               | `[engineer]`                  | Sub-agent rules                                                                             |
| `13-codex-governance/`                             | `[engineer, admin]`           | Codex rules                                                                                 |
| `14-customer-journeys/README.md`                   | `[engineer, admin, sales]`    | Playbook hub overview                                                                       |
| `14-customer-journeys/glossary.md`                 | `[sales, prospect, investor]` | Canonical DART / IM / Reg Umbrella definitions — prospect-safe                              |
| `14-customer-journeys/_ssot-rules/`                | `[engineer, admin, sales]`    | Rules govern experience layer — sales reads too                                             |
| `14-customer-journeys/experience/`                 | `[sales, prospect]`           | Narrative sales-owned docs                                                                  |
| `14-customer-journeys/shared-core/`                | `[engineer, admin, sales]`    | Shared product truths — impl + commercial                                                   |
| `14-customer-journeys/commercial-model/`           | `[sales, admin]`              | Pricing structure — internal commercial only (rule 08: internal cost codex-private)         |
| `14-customer-journeys/demo-ops/`                   | `[sales, engineer, admin]`    | Demo config + sales ops orchestration                                                       |
| `14-customer-journeys/implementation-mapping/`     | `[engineer, admin, sales]`    | Narrative → code bridge                                                                     |
| `14-customer-journeys/playbooks/`                  | `[engineer, admin, sales]`    | Impl-layer click paths                                                                      |
| `14-customer-journeys/authentication/`             | `[engineer, admin]`           | Auth runbooks                                                                               |
| `14-customer-journeys/environments/`               | `[engineer, admin]`           | Per-env config                                                                              |
| `14-customer-journeys/playbook-concepts/`          | `[engineer, admin, sales]`    | Concepts used across playbooks; visibility-slicing is the key cross-cutting doc             |
| `14-customer-journeys/page-triage/`                | `[engineer, admin]`           | 177-page classification — internal-only                                                     |
| `14-customer-journeys/testing/`                    | `[engineer, admin]`           | Playwright coverage                                                                         |
| `14-customer-journeys/roadmap/`                    | `[engineer, admin, sales]`    | Follow-up waves — visible to sales for commercial planning                                  |
| `16-strategy-playbooks/infra-spec/`                | `[engineer, admin]`           | Infra audit + refactor plan — engineering-owned                                             |
| `14-customer-journeys/presentations/`              | `[engineer, admin, investor]` | Target-state deck — investor-briefing-ready                                                 |
| `14-customer-journeys/information-architecture.md` | `[engineer, admin, sales]`    | IA hub — all internal                                                                       |
| `14-customer-journeys/audiences-and-journeys.md`   | `[engineer, admin, sales]`    | Matrix of audiences × journeys                                                              |
| `DEPRECATED_UIS_NOTICE.md`                         | `[engineer, admin]`           | Internal deprecation note                                                                   |
| `QUALITY_GATE_BYPASS_AUDIT.md`                     | `[engineer, admin]`           | Internal audit                                                                              |
| `GLOSSARY.md`                                      | `[engineer, admin]`           | Workspace glossary                                                                          |
| `README.md`                                        | `[engineer, admin]`           | Codex root README                                                                           |
| `validators/`                                      | `[engineer]`                  | Validator specs                                                                             |

Exceptions to the defaults must be documented inline (one-line comment above the frontmatter or in the doc's intro
paragraph) so future readers understand why a specific doc breaks the pattern.

## Example-per-audience block

### `sales`-only doc (demo-ops pricing lever)

```yaml
---
scope: [sales]
title: Demo upsell overlay — seven-day stall trigger
---
# Demo upsell overlay

When a demo account has been idle for seven days, the sales rep receives a reminder to send the follow-up email template
from /admin/demo-ops/post-demo. ...
```

### `engineer`-only doc (architecture internal)

```yaml
---
scope: [engineer]
title: Protocol injection contract
---
# Protocol injection

T0 libraries discover the runtime cloud protocol via SERVICE_MODE + CLOUD_PROVIDER env vars. ...
```

### `admin`-only doc (ops runbook)

```yaml
---
scope: [admin]
title: Secret rotation runbook
---
# Secret rotation

Run `bash scripts/rotate-secrets.sh --service <name>` quarterly. ...
```

### `prospect`-visible doc (public marketing claim)

```yaml
---
scope: [sales, prospect]
title: What Odum does — one paragraph
---
# What Odum does

Odum Research provides enriched data, research, and trading infrastructure to institutional desks ... (no internal
pricing, no internal tooling references, no cost leak)
```

### `investor`-visible doc (board presentation content)

```yaml
---
scope: [investor, admin]
title: Q2 fund-level returns — board pack
---
# Q2 fund-level returns

Net-of-fees NAV progression ... (no strategy IP leak, no technical detail below the board line)
```

### Multi-audience doc (glossary term shared across sales + prospect + investor)

```yaml
---
scope: [sales, prospect, investor]
title: DART — one-line definition
---
# DART

Data, Analytics, Research & Trading — Odum's DIY platform track ...
```

## How the registry is consumed

1. **Build step.** `codex/14-customer-journeys/_tools/build-scope-manifest.sh` walks every `codex/**/*.md`, parses the
   frontmatter, and emits `codex/14-customer-journeys/_generated/scope-manifest.json`. Shape:
   ```json
   {
     "sales":     ["/codex/14-customer-journeys/experience/im-decision-journey.md", ...],
     "engineer":  ["codex/00-SSOT-INDEX.md", ...],
     "admin":     ["/codex/07-security/secrets-management.md", ...],
     "prospect":  ["/codex/14-customer-journeys/glossary.md", ...],
     "investor":  ["/codex/14-customer-journeys/presentations/target-experience-post-refactor.md", ...]
   }
   ```
2. **Downstream consumers.** Sales-collateral generators, help-drawer surfaces in `unified-trading-system-ui`, and
   investor-briefing PDFs read the manifest and filter codex paths by the requested audience before embedding content.
3. **CI gate.** `codex/14-customer-journeys/_tools/check-scope-coverage.sh` fails loud if any codex doc is missing
   `scope:` frontmatter — wired into `unified-trading-pm/scripts/quality-gates.sh`.

## What this rule does NOT do

- **Does not encrypt.** Engineers with repo access see everything — this is a consumption filter, not an access gate.
- **Does not fork the codex.** One source tree; filtered views at read time.
- **Does not adjust doc content tone.** Tone is [rule 02](02-tone-and-posture.md); public-site polish is
  `refactor_g1_12`. Rule 11 only declares visibility; it does not rewrite bodies.
- **Does not cover non-codex docs.** Service READMEs, plans, cursor rules — out of scope. Apply frontmatter only under
  `codex/`.

## Cross-references

- [Rule 03 (same-system principle)](03-same-system-principle.md) — one source, partitioned views.
- [Rule 06 (show / don't-show discipline)](06-show-dont-show-discipline.md) — LOCKED-VISIBLE vs HIDDEN-ENTIRELY pairs.
- [Rule 07 (data licensing boundaries)](07-data-licensing-boundaries.md) — enriched services not raw resale; what leaks.
- [Rule 09 (internal commercial one-liners)](09-internal-commercial-oneliners.md) — internal shorthand; external
  expansion.
- [Stage 3E §1.9](../../16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md) — the infra spec entry this rule
  implements.
- [visibility-slicing.md](../playbook-concepts/visibility-slicing.md) — UI-level visibility rule for catalogue entries
  (separate from codex scope but conceptually sibling).
