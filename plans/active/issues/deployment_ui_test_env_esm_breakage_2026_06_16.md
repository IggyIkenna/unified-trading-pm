---
title: deployment-ui vitest needs Node ≥22 (jsdom@29 ESM deps) — NOT a fleet breakage; RESOLVED via Node-22 pin
created: 2026-06-16
status: RESOLVED 2026-06-16
priority: P1
source:
  - data-status UI fix wave 2026-06-16 — local UI gate failed ERR_REQUIRE_ESM on this host
  - root-caused to host Node 20.18.2 vs CI Node 22; verified CI quality-gates-v2 GREEN
locked_by: live-defi-rollout
---

# deployment-ui vitest requires Node ≥22 — RESOLVED (was a host Node-version mismatch, NOT a breakage)

> **⚠️ CORRECTION (2026-06-16):** my first cut of this doc claimed the deployment-ui jsdom suite was broken
> **fleet-wide**. **That was WRONG.** The suite is **GREEN in CI** (`quality-gates-v2` on `live-defi-rollout` =
> success). The failure was **local-only**: this host runs **Node 20.18.2** while the test stack requires **Node 22**.

## What I found

deployment-ui's vitest unit suite failed `ERR_REQUIRE_ESM` (then a Node-20 ESM-loader `Maximum call stack size exceeded`
under `--experimental-require-module`) on this host. Root cause: jsdom@29 (+ its `html-encoding-sniffer@6` /
`whatwg-url@16`) depends on the **ESM-only `@exodus/bytes`** (and `@csstools/css-calc`), which the vitest@4 **forks pool
(CJS)** can only `require()` where Node's `require(esm)` is stable — **Node 22+; Node 20.18 cannot** (the experimental
flag hits a loader stack-overflow). The big tooling bump (deployment-ui@`6b8e183`: jsdom@29 / vite@8 / vitest@4 /
react@19) is a **Node-22 stack**. CI runs Node 22 (`quality-gates-v2.yml: node-version: "22"`) → **green**. This host
simply lacked Node 22.

Downgrade attempts (html-encoding-sniffer@4, jsdom@27) were whack-a-mole — each just swapped one ESM transitive for
another (jsdom@29 itself depends on `@exodus/bytes`; jsdom@27 pulls `@csstools/css-calc`). The correct resolution is the
**Node version**, not dep surgery.

## Why it matters

- It is NOT a CI / fleet blocker (CI is green). It only blocks **a host running Node < 22** from running the UI gate /
  `quickmerge` locally — which silently produced a cryptic `ERR_REQUIRE_ESM` with no signal that Node was the cause.
- The repo had **no `.nvmrc` / `engines`** declaring the Node-22 requirement, so a Node-20 host fails confusingly.

## Resolution (DONE)

1. **Declared the requirement** — added `.nvmrc` (`22`) + `engines: { node: ">=22" }` to deployment-ui
   (deployment-ui@`80c547d`) so any host/tooling gets a clear Node-22 signal instead of `ERR_REQUIRE_ESM`.
2. **This host** — installed Node 22.12.0 (`~/.local/node22`); the full UI gate then passes
   (`✅ ALL UI QUALITY GATES PASSED`), and the data-status UI fixes shipped on it (deployment-ui@`80c547d`).
3. No dep downgrade — jsdom@29 / the Node-22 stack stays as the big bump intended.

**Follow-up (minor, not blocking):** ensure every UI-capable slot/host provisions Node ≥22 (the `.nvmrc` now documents
it); consider a `verify-slot-host-symmetry` check that the UI host's Node satisfies `engines`. Archive this issue once
that host-provisioning note lands in the slot-setup SSOT. </content> </invoke>
