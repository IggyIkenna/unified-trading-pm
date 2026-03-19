// SSOT ESLint config for all UI repos — owned by unified-trading-pm
// Do NOT edit per-repo. Edit this file and propagate via:
//   python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --ui-only
// OR:
//   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first --ui-only
//
// Rule philosophy (matches Python zero-warning policy):
//   - no-explicit-any    → error  (was warn; agents must use specific types)
//   - no-unused-vars     → error  (was warn; dead code is noise)
//   - no-console         → error  (enforced by base-ui.sh [3.5] codex check too)
//   - react-refresh      → warn   (informational; never blocks a build)
//
// Per-repo overrides: add a rules{} block in eslint.config.js AFTER the spread,
// or use inline eslint-disable comments for documented exceptions.
// Document all exceptions in QUALITY_GATE_BYPASS_AUDIT.md.
//
// Format: ESLint 9 flat config (all UI repos migrated to ESLint 9 + typescript-eslint)

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";

export default tseslint.config(
  { ignores: ["dist/**", "coverage/**", "node_modules/**", "*.config.*"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,

      // Promoted from warn → error (parity with Python zero-warning policy)
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      "no-console": "error",

      // Keep as warn — informational, never blocks a build
      "react-refresh/only-export-components": "off",
    },
  }
);
