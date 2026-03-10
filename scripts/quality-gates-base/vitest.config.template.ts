// Canonical vitest.config.ts template for UI repos — owned by unified-trading-pm
// Copy to repo root as vitest.config.ts and adjust setupFiles / include patterns as needed.
// DO NOT lower thresholds below 70 — workspace floor enforced by base-ui.sh MIN_UI_COVERAGE.
//
// Coverage enforcement chain:
//   base-ui.sh → npm test -- --coverage → vitest (thresholds fail build)
//                                       → base-ui.sh post-run JSON check (belt-and-suspenders)
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      reportsDirectory: "./coverage",
      exclude: ["src/main.tsx", "src/vite-env.d.ts", "src/**/*.d.ts", "src/setupTests.ts"],
      thresholds: {
        lines: 70,
        statements: 70,
        functions: 70,
        branches: 70,
      },
    },
  },
});
