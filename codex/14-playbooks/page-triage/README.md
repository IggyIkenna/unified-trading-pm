---
scope: [engineer, admin]
---

# Page triage

Classification of every `.tsx` page in unified-trading-system-ui and user-management-ui against the playbook spec. The
**reuse-first** discipline: most orphans are promote/refactor candidates, not delete candidates.

## Sibling docs

- [triage-matrix.md](triage-matrix.md) — master table (177 routes × classification × action)
- [broken-links.md](broken-links.md) — 4 confirmed + 5 probable broken outbound hrefs
- [duplicate-clusters.md](duplicate-clusters.md) — 10 overlap clusters with merge decisions
- [partial-archive.md](partial-archive.md) — pages where only some tabs promote forward

## Classification legend

Static analysis categorises every route as:

- **HUB** — 10+ inbound refs OR driven by nav/menu config. The page is a structural anchor.
- **LINKED** — 1-9 inbound refs. Normal internal page, reachable via at least one explicit link.
- **ORPHAN** — 0 inbound refs. The page exists but is not reachable by clicking anywhere in the current UI. Can only be
  accessed by typing the URL.
- **DYNAMIC** — `[param]` route rendered by parent's list map. Reachable when parent shows the list.
- **BROKEN_LINK_TARGET** — referenced by hrefs elsewhere but page.tsx doesn't exist. Must be fixed by either building
  the page or pruning the reference.

## Action legend (reuse-first)

Every row in the triage matrix gets one action:

- `promote` — page is good as-is; wire it into playbook nav
- `refactor` — page has reusable content but needs restructure to fit playbook spec
- `merge-into:X` — fold content into another route X; deprecate this route
- `partial-archive` — keep some tabs/components forward, deprecate others; detailed in partial-archive.md
- `deprecate` — redirect to a successor for 1 release, then delete
- `defer` — decide in a follow-up plan (e.g. awaiting strategy-service read API, awaiting demo Firebase, awaiting
  visibility-slicing implementation)

## Rule

**An `archive`/`deprecate` decision is the BIG one.** Requires explicit confirmation that:

1. No referenced code or doc still depends on it
2. No reusable content/tabs/components would be lost
3. It has no role in any of the three playbook families

When in doubt → `defer`.

## Reuse hints

Every row also carries a `reuse_hint` indicating which playbook family the page could serve:

- `pb1:marketing` — marketing pre-first-call surface
- `pb2:im-deep` / `pb2:dart-deep` / `pb2:reg-deep` — post-first-call briefing content
- `pb3:demo-im` / `pb3:demo-dart` / `pb3:demo-reg` — warm prospect demo surface
- `pb3:admin-org` — org/fund/client provisioning (admin-only for pb3)
- `cross:catalogue-data` / `cross:catalogue-strategy` / `cross:catalogue-ml` / `cross:catalogue-exec` — one of the four
  catalogues
- `cross:client-reporting` — the shared reporting surface
- `cross:ir` — investor relations (not client-facing)
- `ops:internal` — Odum-internal ops; not in any playbook
- `merge:X` — likely duplicate of X, candidate for merge
- `archive` — truly no purpose in new playbook spec

## Related

- Information architecture: [../information-architecture.md](../information-architecture.md)
- Audiences: [../audiences-and-journeys.md](../audiences-and-journeys.md)
- Static audit methodology: see Phase 0 of the parent plan
