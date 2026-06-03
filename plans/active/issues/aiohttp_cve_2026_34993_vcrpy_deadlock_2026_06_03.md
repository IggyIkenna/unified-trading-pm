---
title: Fleet dep-infra blockers — aiohttp CVE-2026-34993 vs vcrpy deadlock + deployment-service pyproject duplicate-key
created: 2026-06-03
author: ikennaigboaka [slot-6·laptop]
source:
  - features-service quality-gates.sh pip-audit (CVE-2026-34993)
  - unified-api-contracts quality-gates.sh (64 vcrpy AttributeError on aiohttp 3.14.0)
  - deployment-api uv lock --upgrade-package aiohttp (deployment-service pyproject TOML parse error)
locked_by: live-defi-rollout
---

## What I found

Two **pre-existing, fleet-wide** dependency-infra blockers surfaced while shipping tradfi-manifest-canonicalisation code
(they block EVERY repo's local QG / `uv lock`, not just tradfi). Both are now fixed at the SSOT; this doc records the
decision + the successor.

### 1. aiohttp CVE-2026-34993 (RCE) deadlocks every VCR-using repo

- **CVE-2026-34993** (newly published; in the OSV DB as of 2026-06-03): `aiohttp <= 3.13.5` — `CookieJar.load()` with
  untrusted input may allow arbitrary code execution. `fix_versions = [3.14.0]`.
- **CVE-2026-47265** (`GHSA-hg6j-4rv6-33pg`; surfaced in OSV minutes later, mid-session): `aiohttp <= 3.13.5` — cookies
  set via the `cookies=` param are re-sent after a cross-origin redirect. `fix_versions = [3.14.0]`. **aiohttp 3.13.5 is
  accumulating cookie CVEs, all fixed only in 3.14.0** — the ignore set will grow until the fleet can reach 3.14.0. Both
  ignored in the QG bases with the same justification (HTTP-client services using header auth, not untrusted cookie
  loads / cookie-auth-across-origins).
- aiohttp **3.13.5** is the locked version **fleet-wide** (confirmed on `origin/live-defi-rollout` uv.lock for every
  repo checked). So pip-audit (a BLOCKING codex gate, `base-service.sh`/`base-library.sh`) now fails on **every repo**,
  tipping each over its `CODEX_MAX_VIOLATIONS` ceiling (features V:0→1 FAIL; deployment-api V:23→24 FAIL).
- The fix version **aiohttp 3.14.0 is within the existing `>=3.13.4,<4.0.0` constraint** — BUT 3.14.0 **removed
  `aiohttp.streams.AsyncStreamReaderMixin`**, which **vcrpy 8.1.1 (the latest release)** references in
  `vcr/stubs/aiohttp_stubs.py` (`class MockStream(asyncio.StreamReader, streams.AsyncStreamReaderMixin)`). So bumping to
  3.14.0 breaks **64 VCR cassette tests** in unified-api-contracts with `AttributeError` (and any other repo with
  aiohttp-backed VCR tests). **No vcrpy release supports aiohttp 3.14 yet** (8.1.1 is newest).
- Net deadlock for VCR-using repos: aiohttp 3.13.5 → pip-audit CVE FAIL; aiohttp 3.14.0 → vcrpy tests FAIL.

### 2. deployment-service/pyproject.toml has a committed duplicate TOML key

- `[tool.uv.sources.unified-api-contracts]` was declared **twice** (identical blocks), committed on
  `origin/live-defi-rollout`. A stricter `uv` rejects it (`TOML parse error … duplicate key`), so **any
  `uv lock --upgrade`** against deployment-service's dep tree (deployment-api depends on it as an editable path-dep)
  fails fleet-wide. A plain `uv lock` survived via cache; `--upgrade-package` forced the rebuild that exposed it.

## Why it matters

- **(1)** blocks the LOCAL QG (commit/quickmerge prerequisite) AND the server `quality-gates-v2` PR gate on **every
  repo** — the entire staging→main promotion pipeline is jammed until resolved. It is a security CVE, so silently
  raising `CODEX_MAX_VIOLATIONS` would be wrong (masks the signal); the correct lever is the sanctioned `--ignore-vuln`
  list that already carries 4 reviewed CVEs.
- **(2)** silently breaks dependency resolution for the whole deployment-service consumer tree.

## Recommended decision (TAKEN — within established patterns)

1. **aiohttp CVE** — added `--ignore-vuln CVE-2026-34993` to BOTH `base-service.sh` and `base-library.sh` pip-audit
   blocks (the same mechanism already used for CVE-2026-4539/45409/3219/6357), with a full-justification comment.
   Rationale: these services use aiohttp as an HTTP **client** and never call `CookieJar.load()` on untrusted files →
   exploit surface is nil; the only patched version breaks vcrpy fleet-wide. Repos **without** vcrpy (features-service,
   deployment-api) run the genuinely-patched **aiohttp 3.14.0**; vcrpy repos stay on 3.13.5 + ignore.
2. **deployment-service** — removed the duplicate `[tool.uv.sources.unified-api-contracts]` block.

## Successor (close this issue when done)

- [ ] [DEPS] P2. **Remove the `CVE-2026-34993` ignore + bump `aiohttp>=3.14` fleet-wide** once **vcrpy** ships an
      aiohttp-3.14-compatible release (track vcrpy >8.1.1) OR an aiohttp 3.13.x backport of the CookieJar fix lands.
      Repos: ALL (edit `base-service.sh` + `base-library.sh` to drop the ignore, then
      `uv lock --upgrade-package aiohttp` + `uv lock --upgrade-package vcrpy` per repo, re-QG). Owner: cicd/dep-security
      epic. Verifier: `pip-audit` clean with NO `--ignore-vuln CVE-2026-34993` + all VCR cassette tests green.
      Cold-start: read this issue doc.
