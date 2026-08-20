---
scope: [engineer, admin]
---

# Testing — every playbook is tested

Every playbook in this SSOT ships with a Playwright end-to-end test. The test walks the canonical click path from start
to end-state, asserts visibility slicing behaves correctly, and catches regressions (broken links, renamed routes,
changed nav config) automatically.

> User quote: "of course the runbooks/playbooks need to all be tested"

## Sibling docs

- [test-matrix.md](test-matrix.md) — playbook × persona × environment → test file path
- [example-playbook-test.md](example-playbook-test.md) — reference test (pb1 marketing)

## Rule

**When a playbook doc changes, the matching Playwright spec MUST be updated in the same PR.** CI enforces this via
grep-coverage: every playbook doc has a test file; every test file references back to its playbook doc.

## Where tests live

All specs under `unified-trading-system-ui/tests/e2e/playbooks/`:

```
tests/e2e/playbooks/
├── marketing-pre-first-call.spec.ts       # pb1
├── research-and-documentation.spec.ts     # pb2 hub
├── 02a-research-im.spec.ts                # pb2a (sub-spec)
├── 02b-research-dart.spec.ts              # pb2b
├── 02c-research-regulatory.spec.ts        # pb2c
├── warm-prospect-demo.spec.ts             # pb3 hub
├── 03a-reg-umbrella.spec.ts               # pb3a
├── 03b-im.spec.ts                         # pb3b (shares helper with pb3a)
├── 03c-dart.spec.ts                       # pb3c
├── visibility-slicing.spec.ts             # cross-cutting, parametrised over all personas
└── helpers/
    ├── seed-persona.ts                    # localStorage seed helper
    ├── expect-service-tile-locked.ts      # visibility assertion helper
    └── expect-click-path.ts               # walk a canonical path
```

> **Not independently re-verified this pass (2026-08-15, plan_reconciler,
> `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md` Doc-drift #3):** only the directory-prefix rename
> (`tests/playbooks/` → `tests/e2e/playbooks/`) was confirmed via `ls`. The finer structure above — the per-playbook
> spec filenames (`02a-*`, `03a-*`, etc.) and the `helpers/` subdirectory — was NOT re-verified this pass; a live
> `ls tests/e2e/playbooks/` shows several of these spec names absent and `seed-persona.ts` sitting flat in the directory
> rather than under `helpers/`. Needs its own dedicated closer-read/scoping pass — out of this mechanical path-fix's
> scope. **Verified 2026-08-20 (docs-reconcile):** the tree above is substantially stale, not just the one file —
> `expect-service-tile-locked.ts` and `expect-click-path.ts` (cited in the Scaffolding code blocks below) do not exist
> anywhere in the repo either (confirmed via `find`), no `helpers/` subdirectory currently exists at all, and the real
> `tests/e2e/playbooks/` directory holds ~30 spec files not shown here (`dart-cockpit/`, `refactor/`,
> `signal-broadcast-*`, `strategy-evaluation-allocator.spec.ts`, etc.) — the `seed-persona.ts` code comment below is
> corrected to match verified reality; the rest of this section's tree/scaffolding still needs the full rewrite this
> caveat already calls for.

Tests run against:

- **Local tier 0** — every run (CI + dev)
- **Local tier 1** — when testing backend-dependent features
- **Staging** — manual smoke post-deploy (until staging Firebase is live)
- **Production** — no automated tests (admin-only smoke)

## Scaffolding

### Persona seeding helper

```ts
// tests/e2e/playbooks/seed-persona.ts (verified flat, not under helpers/ — see caveat above)
export async function seedPersona(page, personaId: string) {
  const personas = {
    admin: {
      id: "admin",
      email: "admin@odum.internal",
      role: "admin",
      org: { id: "odum-internal", name: "Odum Internal" },
      entitlements: ["*"],
    },
    "prospect-im": {/* ... */},
    "prospect-dart": {/* ... */},
    "prospect-reg": {/* ... */},
    // etc
  };
  await page.addInitScript(
    ({ user, token }) => {
      localStorage.setItem("portal_user", JSON.stringify(user));
      localStorage.setItem("portal_token", token);
    },
    { user: personas[personaId], token: `demo-token-${personaId}` }
  );
}
```

### Visibility assertion helper

```ts
// tests/e2e/playbooks/helpers/expect-service-tile-locked.ts
export async function expectServiceTileLocked(page, tileName: string) {
  const tile = page.getByRole("article", { name: tileName });
  await expect(tile.locator('[data-testid="lock-icon"]')).toBeVisible();
  await expect(tile.getByRole("link")).not.toBeVisible();
}
```

### Click-path walker

```ts
// tests/e2e/playbooks/helpers/expect-click-path.ts
export async function expectClickPath(page, steps: Array<{ click: string; expectUrl: string }>) {
  for (const step of steps) {
    await page.getByRole("link", { name: step.click }).click();
    await page.waitForURL(step.expectUrl);
  }
}
```

## CI integration

- `scripts/quality-gates.sh` includes a Playwright step for `tests/e2e/playbooks/`
- Build fails if any playbook spec fails
- Flaky tests are NOT tolerated — isolate with `test.fixme` and file an issue

## Coverage gates

| Coverage requirement                                                   | Where enforced                                                   |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Every playbook doc has matching spec                                   | Grep check in pre-commit: doc name → expected spec file          |
| Every nav-config change is covered by a spec                           | Spec reads nav config fixtures; if nav changes, spec must update |
| Every broken-link entry in triage gets a spec that verifies it's fixed | New tests added in Phase 3 alongside href fixes                  |

## Visibility-slicing cross-test

`visibility-slicing.spec.ts` is parametrised over all personas. It asserts:

For each persona, navigating to `/dashboard` shows exactly the expected service tiles (unlocked vs padlocked vs hidden)
per the entitlement × role × lock_state × maturity matrix in
[../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md).

If a new persona or entitlement is added, this test must be updated.

## Related

- Playbooks: [../playbooks/](../playbooks/)
- Visibility slicing: [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md)
- Demo personas: [../authentication/README.md](../authentication/README.md)
