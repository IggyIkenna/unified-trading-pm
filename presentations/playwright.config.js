const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 30000,
  retries: 0,
  use: {
    headless: true,
    viewport: { width: 1920, height: 1080 },
    // Allow local file:// access
    launchOptions: {
      args: ["--allow-file-access-from-files", "--disable-web-security"],
    },
  },
  reporter: [["list"], ["html", { open: "never", outputFolder: "tests/playwright-report" }]],
});
