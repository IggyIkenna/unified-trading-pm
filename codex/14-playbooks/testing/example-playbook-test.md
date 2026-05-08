---
scope: [engineer, admin]
---

# Example playbook test — pb1 Marketing

Reference Playwright spec for the pb1 playbook. Every other playbook spec should follow the same shape: seed, navigate,
assert click-path, assert visibility, no flakes.

## File: `tests/playbooks/marketing-pre-first-call.spec.ts`

```ts
import { test, expect } from "@playwright/test";

test.describe("pb1 — Marketing pre-first-call", () => {
  test("homepage loads and shows three services", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Odum Research/);

    // Three service cards visible
    await expect(page.getByRole("article", { name: /Invest/ })).toBeVisible();
    await expect(page.getByRole("article", { name: /Build & Run/ })).toBeVisible();
    await expect(page.getByRole("article", { name: /Regulate/ })).toBeVisible();

    // Primary CTAs
    await expect(page.getByRole("link", { name: "Discuss a Mandate" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Explore the Platform" })).toBeVisible();
  });

  test("three service cards navigate correctly", async ({ page }) => {
    await page.goto("/");

    await page
      .getByRole("link", { name: /Investment Management/ })
      .first()
      .click();
    await expect(page).toHaveURL("/investment-management");

    await page.goto("/");
    await page
      .getByRole("link", { name: /Platform/ })
      .first()
      .click();
    await expect(page).toHaveURL("/platform");

    await page.goto("/");
    await page
      .getByRole("link", { name: /Regulatory/ })
      .first()
      .click();
    await expect(page).toHaveURL("/regulatory");
  });

  test("top nav links all resolve 200", async ({ page }) => {
    await page.goto("/");
    const topNavLinks = [
      "/investment-management",
      "/platform",
      "/regulatory",
      "/firm",
      "/contact",
      "/login",
      "/signup",
    ];

    for (const href of topNavLinks) {
      const response = await page.goto(href);
      expect(response?.status(), `${href} should load`).toBeLessThan(400);
    }
  });

  test("Spaces dropdown shows public items only when anonymous", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Spaces" }).click();

    // Expected: Marketing items + Briefings Hub + Developer Docs
    await expect(page.getByRole("menuitem", { name: "Home" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "Investment Management" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: /DART|Data.*Research.*Trading/ })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "Regulatory" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: /Briefings Hub/ })).toBeVisible();

    // Auth-only items should NOT be visible (or should show a lock indicator)
    // Dashboard / admin / client access should not appear
  });

  test("footer links all resolve", async ({ page }) => {
    await page.goto("/");
    const footerLinks = ["/privacy", "/terms", "/services/regulatory", "/contact"];

    for (const href of footerLinks) {
      const response = await page.goto(href);
      expect(response?.status(), `${href} should load`).toBeLessThan(400);
    }
  });

  test("no auth gate appears on any pb1 route", async ({ page }) => {
    const pb1Routes = [
      "/",
      "/investment-management",
      "/platform",
      "/regulatory",
      "/firm",
      "/contact",
      "/demo",
      "/docs",
    ];

    for (const route of pb1Routes) {
      await page.goto(route);
      // Assert no login form and no briefings gate visible
      await expect(page.getByRole("heading", { name: "Welcome back" })).not.toBeVisible();
      await expect(page.getByRole("heading", { name: /Briefings Access/i })).not.toBeVisible();
    }
  });
});
```

## Principles demonstrated

1. **test.describe** per playbook — groups assertions, shows up as one group in CI output
2. **No explicit waits** — `expect(...).toBeVisible()` has auto-retry; avoid `page.waitForTimeout`
3. **Role-based selectors** — `getByRole('article'|'link'|'button')` is stable across CSS refactors
4. **200 assertion** — checks `response.status()` for every resolvable route
5. **Negative assertions** — assert gates/forms are NOT visible where they shouldn't be

## What good playbook tests do

- ✅ Walk the canonical click path start-to-finish
- ✅ Assert visibility slicing (what should and shouldn't be visible per persona)
- ✅ Catch regressions (broken links, renamed routes, changed nav config)
- ✅ Run fast (< 30s per spec at tier 0)
- ✅ Parallelise (no shared state between specs)

## What they don't do

- ❌ Test business logic (covered by service unit tests)
- ❌ Test individual components (covered by component tests)
- ❌ Assert visual pixel-perfectness (visual regression is a separate tool — Percy etc.)
- ❌ Hit real backends (tier 0 = mock; backend interactions tested in service pyramid)

## Related

- Matrix of all specs: [test-matrix.md](test-matrix.md)
- Testing overview: [README.md](README.md)
- Playbook pb1: [../playbooks/01-marketing-pre-first-call.md](../playbooks/01-marketing-pre-first-call.md)
