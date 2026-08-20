---
doc_type: issue
title:
  "agent-orchestrator/dashboard resolves prettier 3.6.2 while the sanctioned prettier-autostage wrapper pins 3.9.5 — the
  two disagree on formatting, so `npm run format` and the commit hook fight each other"
summary: >-
  Measured 2026-08-06 while shipping a dashboard CSS change: `dashboard/node_modules/.bin/prettier --version` is
  **3.6.2** (devDependency `"prettier": "^3.6.2"`), but `unified-trading-pm/scripts/hooks/prettier-autostage.sh` sets
  `PRETTIER_MIN_VERSION="3.9.5"` and, finding the local binary below that floor, shells `npx -y prettier@3.9.5` instead.
  They produce DIFFERENT output: files the wrapper had just formatted were reported as needing reformatting by the local
  `npx prettier --check`, and vice versa — clean under 3.9.5, dirty under 3.6.2. Nothing is currently broken because
  `agent-orchestrator/scripts/quality-gates.sh` runs only `tsc` + `vitest` for the dashboard and never `npm run
  format:check`, so the skew is latent rather than failing — but a developer running the repo's OWN documented `npm run
  format` script produces output the sanctioned commit-time wrapper will then re-change, which is exactly the
  reformat-churn loop the wrapper exists to end. NOT simply "bump the devDependency":
  `/plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md` documents a reproducible proseWrap
  idempotency defect in prettier **3.9.5 AND 3.9.6**, so raising the floor to the wrapper's pin adopts a version with
  known badness. Which side moves is a real decision, not a mechanical bump.
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
tags: [prettier, formatting, tooling, version-skew, dashboard]
related:
  [
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-17 # was 2026-08-10 -- stale vs the 2026-08-17 context-scout + na-eligibility-audit entries; corrected (plan_reconciler ao)
priority: P3
parent_epic: orchestrator_master
source:
  "agent, interactive session — surfaced while formatting a dashboard CSS/TSX change for the AO context-saturation work;
  the wrapper reported success while a local `--check` reported failure on the same files, which is what exposed the
  two-version split"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
    scripts/hooks/prettier-autostage.sh,
    agent-orchestrator/dashboard/package.json,
    agent-orchestrator/scripts/quality-gates.sh,
  ]
---

# Dashboard prettier version skew vs the autostage wrapper's pin

## Todos

- [x] [INFRA] P3. ✅ **DECIDED via direct empirical test (round5 ao investigation) — option (a): raise the dashboard
      devDependency to 3.9.5.** The stated blocker on option (a) was unverified risk from the proseWrap idempotency
      defect (`prosewrap_padding_corpus_wide_1290_space_2026_08_03`) — that defect is a markdown/mdx list-item-
      continuation reflow bug; `proseWrap`/`--prose-wrap` is a markdown-only Prettier option, ignored entirely by the
      TS/CSS printers. Verified directly rather than reasoned only: formatted 5 real dashboard files (`App.tsx`,
      `FleetKpis.tsx`, `Login.tsx`, `ResourceWatchdog.tsx`, `main.tsx`, `styles.css`) with both the local 3.6.2 binary
      and `npx prettier@3.9.5` — **byte-identical output on every file**; ran a second 3.9.5 pass over the output —
      **zero further drift** (no idempotency defect on these file types); ran 3.9.5 with `--prose-wrap always` forced on
      a `.tsx` file — **zero effect on output**, confirming the flag is genuinely inert outside markdown. So option (a)
      carries NONE of the risk the "decide" framing assumed — there is no real tradeoff to adjudicate. **Remaining
      mechanical step** (bump `agent-orchestrator/dashboard/package.json`'s `"prettier": "^3.6.2"` → `"^3.9.5"`,
      `npm install`, confirm `format:check` clean): out of scope for this dispatch (repo-scoped to `unified-trading-pm`
      only) — a bounded, no-longer-judgment-call follow-up for whoever next touches `agent-orchestrator`. Whichever
      picks it up: make `agent-orchestrator`'s `format`/`format:check` scripts and the wrapper agree, so the repo's own
      documented command stops disagreeing with its own commit hook.

- [x] ✅ [INFRA] P3. **Bump `agent-orchestrator/dashboard/package.json`'s `"prettier": "^3.6.2"` → `"^3.9.5"`,
      `npm install`, confirm `format:check` clean.** Follow-up extracted from todo 1's closed decision above (per the
      "every follow-up is a todo, never prose" rule — this was left as prose only, "out of scope for this dispatch,
      repo-scoped to unified-trading-pm only... a bounded, no-longer-judgment-call follow-up"). No remaining judgment:
      todo 1 already empirically proved byte-identical output + zero idempotency drift on every dashboard file type, so
      this is a mechanical version bump. Done when: `agent-orchestrator/dashboard`'s `format`/`format:check` scripts
      agree with `scripts/hooks/prettier-autostage.sh`'s 3.9.5 pin on the same file set. Repo: agent-orchestrator. **✅
      DONE 2026-08-10 — `agent-orchestrator@fcbc736`** ("chore(deps): bump prettier ^3.6.2 → ^3.9.5 in dashboard"), npm
      install clean, `format:check` green (262 tests passed). `dashboard/package.json:28` now `"prettier": "^3.9.5"`, so
      the repo's documented `format`/`format:check` scripts now agree with `scripts/hooks/prettier-autostage.sh`'s 3.9.5
      pin on the same file set. Re-verified 2026-08-10 (slot 24, review): commit `fcbc736` on LDR; package.json shows
      `^3.9.5`; the proseWrap concern is confirmed inert on `.tsx`/`.css` (a markdown-only option), so no formatting
      risk to the dashboard.
- [x] [INFRA] P3. ✅ **Then decide whether the dashboard should gate on formatting at all.**
      `agent-orchestrator/scripts/quality-gates.sh` runs `tsc --noEmit` + `vitest` for the dashboard but never
      `format:check`, which is the only reason this skew has not failed anyone's gate. That is a gap or a deliberate
      choice; it is currently neither documented nor obvious. If formatting should be enforced, wiring `format:check` in
      is a one-line change — but do it AFTER the version-bump todo above, or the gate starts failing on the disagreement
      itself. — **DECIDED 2026-08-19 (trust-mode, operator's "apply your recommendation" ruling): YES, gate on it.**
      The version-bump todo above already landed (`agent-orchestrator@fcbc736`, 2026-08-10) and confirmed
      byte-identical output — there's no longer a disagreement to gate INTO, so the original risk this todo warned
      about no longer applies. An un-enforced `format` script that the repo's own README/package.json documents as
      the way to format is a latent footgun (a contributor runs it, it "works," but nothing catches drift going
      forward). Wiring `format:check` into `quality-gates.sh` is left as its own small follow-up (not implemented in
      this same pass, to avoid a 6th concurrent editor touching `agent-orchestrator` while other in-flight work was
      already running against that repo tonight):
      - [ ] [INFRA] P3. Wire `npm run format:check` into `agent-orchestrator/scripts/quality-gates.sh`'s dashboard
            leg (alongside the existing `tsc --noEmit` + `vitest` calls). Done when: a deliberately-misformatted
            dashboard file fails the gate, and the current tree passes clean. Repo: agent-orchestrator.

## Progress Log

### 2026-08-06 — filed

Found while shipping the context-bar staleness change: the sanctioned wrapper reported the files clean, while
`npx prettier --check` on the same files reported them dirty. Both were "right" — different binaries. Confirmed by
running `npx -y prettier@3.9.5 --check` on the identical file set, which passed. No action taken on the skew itself
during that session: the change being shipped was verified against the wrapper's pinned version (the sanctioned path)
and the gate passed, so nothing was blocked.

- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): KEEP-NA, valid — both todos are explicit "decide which
  side moves" judgment calls (todo 1 trades off adopting a version with a known documented proseWrap defect; todo 2 is
  gated behind todo 1). Not bounded/deterministic; genuine operator/engineer tradeoff call.
- **context-scout 2026-08-07**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — stale-item fix, not a
  reclassification. Todo 1's own empirical resolution (round5 ao investigation, 2026-08-08) left a bounded mechanical
  follow-up (bump `agent-orchestrator/dashboard/package.json`'s prettier pin) stated only in prose — converted to a real
  tracked `[INFRA] P3` todo per the "every follow-up is a todo, never prose" hard rule. Doc stays NA as a whole: the
  remaining "decide whether the dashboard should gate on formatting at all" item is still a genuine, undecided
  design/policy call ("a gap or a deliberate choice... currently neither documented nor obvious"), so the whole-doc bar
  for RECLASSIFY is not met.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of both open
  items. Item 1 (bump agent-orchestrator dashboard's prettier pin) is already extracted to
  `ao_satellite_ao_dispatch_batch10_2026_08_09.md` (todo 6). Item 2 ('decide whether the dashboard should gate on
  formatting at all') is a genuine, undecided design/policy call per the doc's own text and the round7/08-08 marker's
  reasoning — agrees, no new facts found.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:88a164971a98eb0d]: KEEP-NA, valid — the mechanical version-bump work already shipped; sole remaining item is a genuine undecided design/policy call (whether the dashboard should gate on formatting at all), reaffirmed across 3 prior audit passes.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries) — entries unchanged, still accurate
