# Context Bloat Remediation Plan

## Problem

Context fills quickly even on the first prompt when running agents. Investigation shows rules and duplicated content are
the main cause.

---

## Root Causes

### 1. 46 Always-Applied Rules (~16K–20K tokens)

- **Location:** `unified-trading-pm/cursor-rules/` (108 `.mdc` files, ~4,118 lines)
- **46 rules** have `alwaysApply: true` and are injected on every prompt
- **Estimate:** ~4,118 lines × 4 tokens/line ≈ **16,500–20,500 tokens** from rules alone

### 2. 8 Repos With Full Rule Copies (Not Symlinks)

These repos have **real** `.cursor/rules` directories (not symlinks to PM):

| Repo                       | Lines |
| -------------------------- | ----- |
| batch-audit-ui             | 3,273 |
| unified-api-contracts      | 3,275 |
| unified-internal-contracts | 3,272 |
| features-sports-service    | 3,272 |
| unified-trading-ui-auth    | 3,272 |
| deployment-api             | 3,272 |
| deployment-service         | 3,272 |
| system-integration-tests   | 3,272 |

**Total:** ~26,000 lines of duplicated rules. If Cursor loads rules per workspace folder, the same rules can be loaded
multiple times → **~100K+ tokens** from rules alone.

### 3. 38 Per-Repo `.cursorrules` Files

- Many are 100–200+ lines
- Repeated content: External Import Standards, SSOT Alignment Validation, etc.
- Adds more duplication in multi-root workspace

### 4. Other Context Sources

- 50+ workspace paths (repos)
- Large git status for many repos
- Token-optimization rule (alwaysApply) adds more instructions

---

## Remediation (Priority Order)

### P0: Replace Repo Rule Copies With Symlinks

**Goal:** Single source of rules; no duplication across repos.

**Action:** For each repo with a real `.cursor/rules` dir, replace with symlink:

```bash
# Example for batch-audit-ui
cd batch-audit-ui
rm -rf .cursor/rules   # backup first if needed
ln -s ../../unified-trading-pm/cursor-rules .cursor/rules
```

**Script:** Extend `unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh` to:

1. Detect repos with real `.cursor/rules` (not symlinks)
2. Replace with symlink to PM

**Repos to fix:** batch-audit-ui, unified-api-contracts, unified-internal-contracts, features-sports-service,
unified-trading-ui-auth, deployment-api, deployment-service, system-integration-tests

---

### P1: Reduce Always-Applied Rules

**Goal:** Fewer rules injected on every prompt; more on-demand.

**Candidates to move from `alwaysApply: true` to on-demand (globs / description only):**

- `breaking-change-major-version-protocol.mdc` — only when editing version/commit
- `gcp-auth-in-tests.mdc` — only in tests/
- `no-backward-compat-shims.mdc` — only when refactoring
- `concurrency-max-workers.mdc` — only in service code
- `async-http-aiohttp.mdc` — only in async code
- `batch-live-symmetry.mdc` — only in services

**Process:** Change `alwaysApply: true` → `alwaysApply: false`, add specific `globs` so they apply only when relevant.

---

### P2: Shorten Long Rules

**Goal:** Keep rules under ~50 lines where possible; link to Codex for full detail.

**Examples:**

- `anti-patterns-quick-reference.mdc` — keep table, trim prose
- `always-use-quickmerge.mdc` — keep DO/NEVER, link to codex for flags
- `event-logging.mdc` — keep import pattern, link to lifecycle-events.md

---

### P3: Trim Per-Repo `.cursorrules`

**Goal:** Remove duplicated sections; reference shared docs.

- Replace long "External Import Standards" blocks with: `See: .cursor/rules/imports/external-import-standards.mdc`
- Replace long "SSOT Alignment Validation" blocks with a one-line reference
- Keep only repo-specific patterns (service type, deps, testing)

---

## Expected Impact

| Change                                   | Token Savings (est.) |
| ---------------------------------------- | -------------------- |
| P0: Symlinks (no duplicate rule loading) | 80K–100K             |
| P1: 10–15 rules off alwaysApply          | 3K–5K                |
| P2: Shorten 5–10 long rules              | 2K–4K                |
| P3: Trim .cursorrules                    | 2K–4K                |
| **Total**                                | **~90K–115K tokens** |

---

## Verification

After changes:

1. Open a fresh Cursor session
2. Run a simple agent (e.g. "list files in instruments-service")
3. Check token usage in Cursor dashboard — should be noticeably lower on first prompt

---

## References

- `cursor-folder-boundary.mdc` — rules should be symlinks to PM
- `unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh` — existing symlink setup
