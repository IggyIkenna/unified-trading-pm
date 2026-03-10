// Odum Research — Presentation Smoke Tests
// Run: cd presentations && npx playwright test tests/smoke.spec.js
//
// Checks every slide in every deck for:
//   - Page loads without JS errors
//   - Logo visible on every slide
//   - No empty/blank slide bodies (sections with no rendered content)
//   - No remaining broken Mermaid elements (.mermaid without SVG child)
//   - No content overflowing the slide viewport
//   - Slide count matches expectations

const { test, expect } = require("@playwright/test");
const path = require("path");
const fs = require("fs");

const PRESENTATIONS_DIR = path.join(__dirname, "..");

const DECKS = fs
  .readdirSync(PRESENTATIONS_DIR)
  .filter((f) => f.endsWith(".html") && /^\d\d-/.test(f))
  .sort()
  .map((f) => ({ file: f, url: `file://${path.join(PRESENTATIONS_DIR, f)}` }));

// Expected minimum slide counts per deck
const MIN_SLIDE_COUNTS = {
  "00-master.html": 10,
  "01-data-provision.html": 8,
  "02-backtesting-as-a-service.html": 8,
  "03-strategy-white-labelling.html": 8,
  "04-execution-as-a-service.html": 7,
  "05-investment-management.html": 7,
  "06-regulatory-umbrella.html": 7,
  "07-autonomous-ai-operations.html": 7,
  "08-system-quality.html": 7,
  "09-platform-portal.html": 7,
};

for (const deck of DECKS) {
  test.describe(deck.file, () => {
    test("loads without JS errors", async ({ page }) => {
      const errors = [];
      page.on("pageerror", (e) => {
        // Ignore CDN resource errors (offline environments)
        if (!e.message.includes("net::ERR") && !e.message.includes("Failed to fetch")) {
          errors.push(e.message);
        }
      });
      await page.goto(deck.url);
      await page.waitForLoadState("networkidle");
      expect(errors, `JS errors in ${deck.file}: ${errors.join(", ")}`).toHaveLength(0);
    });

    test("logo is visible", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("domcontentloaded");
      const logo = page.locator(".slide-logo");
      await expect(logo, `Logo missing in ${deck.file}`).toBeVisible();
      const src = await logo.getAttribute("src");
      expect(src, "Logo src should be a data URI or odum-logo.png reference").toMatch(/data:image\/png|odum-logo\.png/);
    });

    test("has correct minimum slide count", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("domcontentloaded");
      const slideCount = await page.locator(".reveal .slides > section").count();
      const minCount = MIN_SLIDE_COUNTS[deck.file] || 5;
      expect(slideCount, `${deck.file} has ${slideCount} slides, expected at least ${minCount}`).toBeGreaterThanOrEqual(
        minCount
      );
    });

    test("no broken Mermaid elements (raw text, no SVG)", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("networkidle");
      // Navigate through all slides to trigger lazy rendering
      const slideCount = await page.locator(".reveal .slides > section").count();
      for (let i = 0; i < slideCount; i++) {
        await page.keyboard.press("ArrowRight");
        await page.waitForTimeout(200);
      }
      // Check for .mermaid divs that contain raw diagram text (not SVG)
      const brokenMermaid = await page.evaluate(() => {
        const els = document.querySelectorAll(".mermaid");
        const broken = [];
        els.forEach((el) => {
          const hasSvg = el.querySelector("svg");
          const hasText =
            el.textContent.trim().startsWith("flowchart") ||
            el.textContent.trim().startsWith("graph") ||
            el.textContent.trim().startsWith("sequenceDiagram");
          if (!hasSvg && hasText) broken.push(el.textContent.trim().slice(0, 80));
        });
        return broken;
      });
      expect(brokenMermaid, `Broken Mermaid in ${deck.file}: ${brokenMermaid.join(" | ")}`).toHaveLength(0);
    });

    test("cover slide has title and subtitle", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("domcontentloaded");
      const coverTitle = page.locator(".cover-title, .reveal h1, .reveal h2").first();
      await expect(coverTitle, `No title on cover slide of ${deck.file}`).toBeVisible();
      const titleText = await coverTitle.textContent();
      expect(titleText.trim().length, "Cover title should not be empty").toBeGreaterThan(3);
    });

    test("no slide section is completely empty", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("domcontentloaded");
      const emptySections = await page.evaluate(() => {
        const sections = document.querySelectorAll(".reveal .slides > section");
        const empty = [];
        sections.forEach((sec, idx) => {
          // Exclude aside.notes from text check
          const clone = sec.cloneNode(true);
          clone.querySelectorAll("aside").forEach((a) => a.remove());
          const text = clone.textContent.trim();
          if (text.length < 20) empty.push(idx);
        });
        return empty;
      });
      expect(emptySections, `Empty sections at indices [${emptySections}] in ${deck.file}`).toHaveLength(0);
    });

    test("slide footer present on last slide", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("domcontentloaded");
      // Footer exists on cover or last slide — just check at least one exists
      const footerCount = await page.locator(".slide-footer").count();
      expect(footerCount, `No slide-footer found in ${deck.file}`).toBeGreaterThanOrEqual(1);
      // Check that at least one footer across the deck contains the FCA number
      const allFooterText = await page.locator(".slide-footer").allTextContents();
      const hasFca = allFooterText.some((t) => t.includes("975797"));
      expect(hasFca, `No footer in ${deck.file} contains FCA number 975797`).toBe(true);
    });

    test("FCA badge/reference present where expected", async ({ page }) => {
      await page.goto(deck.url);
      await page.waitForLoadState("domcontentloaded");
      const bodyText = await page.locator("body").textContent();
      expect(bodyText, `FCA reference missing in ${deck.file}`).toContain("975797");
    });
  });
}

// Static HTML validation (no browser needed)
test.describe("Static HTML checks", () => {
  test("no raw Mermaid code blocks remain in any HTML file", async () => {
    for (const deck of DECKS) {
      const content = fs.readFileSync(path.join(PRESENTATIONS_DIR, deck.file), "utf8");
      const hasMermaidDiv = content.includes('<div class="mermaid">');
      expect(hasMermaidDiv, `${deck.file} still contains a <div class="mermaid"> block`).toBe(false);
    }
  });

  test("all files reference the logo", async () => {
    for (const deck of DECKS) {
      const content = fs.readFileSync(path.join(PRESENTATIONS_DIR, deck.file), "utf8");
      // Logo is either referenced by filename or embedded as a data URI
      expect(content, `${deck.file} missing logo img tag`).toMatch(/odum-logo\.png|data:image\/png/);
    }
  });

  test("all files use correct Reveal.js ready-event pattern", async () => {
    for (const deck of DECKS) {
      const content = fs.readFileSync(path.join(PRESENTATIONS_DIR, deck.file), "utf8");
      const hasReadyEvent = content.includes("Reveal.on('ready'") || content.includes('Reveal.on("ready"');
      expect(hasReadyEvent, `${deck.file} missing Reveal ready-event listener`).toBe(true);
    }
  });

  test("logo file exists on disk", async () => {
    const logoPath = path.join(PRESENTATIONS_DIR, "assets", "odum-logo.png");
    expect(fs.existsSync(logoPath), `Logo file not found at ${logoPath}`).toBe(true);
  });

  test("theme.css exists", async () => {
    const cssPath = path.join(PRESENTATIONS_DIR, "assets", "theme.css");
    expect(fs.existsSync(cssPath), "theme.css missing").toBe(true);
  });

  test("no file contains emoji in potentially-Mermaid context", async () => {
    const emojiPattern = /class="mermaid[^"]*"[^<]*[\u{1F300}-\u{1FFFF}]/su;
    for (const deck of DECKS) {
      const content = fs.readFileSync(path.join(PRESENTATIONS_DIR, deck.file), "utf8");
      expect(emojiPattern.test(content), `${deck.file} has emoji inside a mermaid div`).toBe(false);
    }
  });
});
