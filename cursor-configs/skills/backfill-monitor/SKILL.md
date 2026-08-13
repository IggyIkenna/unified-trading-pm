---
name: backfill-monitor
description:
  End-to-end pre-flight → launch → post-launch monitoring wrapper for any backfill wave (new data source, resumed gap,
  or MVP-scope catch-up). Composes 3 existing skills rather than reimplementing them —
  `/data-pipeline-alerts-reconcile` (nothing already broken before adding load), `/vm-resource-rightsizing-check`
  (right machine type, checked pre- AND post-launch, not just assumed), `/vm-preemption-billing-waste-audit`
  (during-run silent-waste sweep) — and adds what none of them cover: a pre-launch sizing ESTIMATE (not just a
  post-launch check), an explicit one-data-source-per-VM isolation rule, and a mandatory small-range smoke test before
  the real-scope launch. Built 2026-08-12 from the TradFi MVP backfill relaunch (VIX preemption/schema/manifest
  incidents, the tradfi 6-7%-CPU-on-16-vCPU rightsizing finding) — this is the skill that should have run BEFORE those
  launches, not the audit that found the waste after. Trigger on `/backfill-monitor`, "monitor this backfill", "check
  before launching a backfill", "backfill pre-flight check", "smoke-test then launch this backfill".
---

# /backfill-monitor — pre-flight, launch, and post-launch monitoring for a backfill wave

Run this **before, during, and after** launching any backfill VM(s) — a brand-new data source, a resumed gap, or an
MVP-scope catch-up. It is a **checklist + composition wrapper**, not a reimplementation: every sub-check below already
has its own skill or codex SSOT; this skill's job is sequencing them correctly and adding the pre-launch estimate and
isolation/smoke-test steps that no existing skill covers. **This is a living document — update it as gaps are found in
real use, per the operator's own instruction; don't let a finding stay a one-off chat note.**

## 0. Pre-flight — is anything already broken?

Run `/data-pipeline-alerts-reconcile` (or at minimum its § 0 ground-truth sweep: live Slack channel read + the Cloud Run
Jobs/Services + GCE fleet health cross-check) before adding new load. Launching a backfill wave on top of an
already-degraded pipeline (a stuck consolidator, a crash-looping alerting subscriber, a zombie scheduler) means the new
wave's own failures get lost in existing noise, and a shared-resource issue (GCS 429 storm, IAM quota) can misattribute
to the new launch when it was already live. **A dirty pre-flight is itself a blocker** — fix or at least clearly log
what's pre-existing before proceeding, so a post-launch investigation can tell "caused by this wave" from "was already
broken."

## 1. Pre-flight — estimate the right machine type BEFORE launch, don't default-and-hope

`/vm-resource-rightsizing-check` is a **post-launch** check by design (it needs real telemetry). This step is its
missing pre-launch counterpart:

1. **Find the closest prior precedent** for this exact launcher family (same `scripts/vm/launch-*.sh`, same
   asset_group/venue/data_type shape) — check `vm-launcher-runbook.md`'s duration table, any prior
   `vm_resource_utilization_*` finding doc, or the launcher script's own header comments for a previously-measured
   CPU/RAM profile. A prior finding for the SAME family (e.g. the tradfi OHLCV fleet's 6-7%-CPU-on-16-vCPU downsize to
   `e2-highmem-8`) is a real estimate, not a guess — cite it and use it.
2. **No precedent exists** (a genuinely new data source/launcher): start from the SMALLEST machine type the launcher's
   own memory-floor comments/known OOM history justify, not the largest available "to be safe" — over-provisioning is
   the default failure mode this skill exists to catch, and Step 5 below (smoke test) is exactly where a too-small guess
   gets corrected cheaply, before the real-scope launch commits to it.
3. **State the estimate and its confidence** in your pre-launch note (precedent-based / smoke-test-pending /
   genuinely-uncertain) — this is what Step 6 checks against.

## 2. Isolation rule — one data source per VM, sized to the actual job

**Different data sources never share a VM**, even if bundling looks efficient on paper — a slow/stuck source (a rate
limit, a schema bug, a preemption) on a shared VM stalls or corrupts the OTHER source's progress on the same box, and
post-hoc log/resource attribution becomes ambiguous (which source caused the CPU spike, the OOM, the hung request). This
applies to genuinely distinct **sources** (Databento vs. Yahoo vs. FRED), not to multiple **shards of the same source**
(e.g. bundling several Databento venues on one VM via `--venues "A B C"` is the existing, correct pattern from
`/data-pipeline-check-mtds` § 3 — that's concurrency within a source, not source-sharing).

**Don't under-size a VM to make it "thin enough" for a small job either** — a VM sized for a genuinely small, isolated
job (e.g. one Yahoo Finance daily-series backfill) should be sized to THAT job's real resource need, not padded up to
match a bigger family's default just for consistency. The exception that justifies running a small job on its OWN small
isolated VM even when a bigger shared VM COULD technically absorb it cheaply: **a fast, cheap source where isolation
itself is the win** (Yahoo Finance daily series, FRED series — minutes-long jobs where a dedicated tiny VM's boot
overhead is trivial next to the correctness/attribution benefit of never mixing sources). State explicitly, per launch,
which case you're in: "sized to precedent," "sized to smoke-test measurement," or "isolated-small, boot overhead
accepted for correctness."

## 3. Mandatory smoke test — small date range, before the real-scope launch

Before committing to the full backfill window, run a small-range smoke test **per data source** (never bundled) — this
is the same shape as `/data-pipeline-check-mtds`'s force/skip leg pattern, scaled down to a pre-flight check rather than
a full MVP-matrix sweep:

1. Pick a **narrow, real date range** (a single day, or the smallest range the launcher's own chunking allows) that the
   source is known to have data for — never synthesize a date; if unsure which day has real data, use
   `--auto-day`-equivalent logic (prefer a source-verified-captured day) rather than guessing.
2. Launch via the SAME launcher script and machine-type estimate from Step 1 — a smoke test on a different
   launcher/config than the real run proves nothing about the real run.
3. Verify: the VM reaches `STARTED`, writes real (non-phantom, `row_count>0`) rows, the manifest records them correctly
   (per this workspace's own recent finding class: a manifest write can silently fail non-blocking even when the
   underlying download succeeded — check `run.log` for `Manifest write failed`/`MalformedRowKeyError` patterns, not just
   that the VM reached a terminal state), and the schema is canonical (no stray `ts_event`-instead- of-`timestamp` class
   of regression).
4. **A smoke-test failure is a hard stop** — fix the root cause (schema mapping, row_key construction, credential,
   whatever it is) and re-smoke before launching the real-scope backfill. Launching the real range on top of a known
   broken smoke test just multiplies the same bug across the whole window (exactly what happened to the VIX relaunch
   this workspace already hit once — 2 code bugs found only after a 7-VM real-scope launch had already burned SPOT
   preemptions and partial runs on the broken path).
5. **The smoke test's own resource sample is real, usable data for Step 1's estimate** — if it ran hot/cold relative to
   the precedent, adjust the real-scope launch's machine type BEFORE committing, not after.

## 4. Launch the real backfill — via deployment-service, no fire-and-forget

Standard `vm-launcher-runbook.md` discipline applies unchanged: reuse an existing `launch-*.sh` (never hand-roll a VM
name), backfill VMs default SPOT with a documented preemption-resume story, verify `STARTED` + ongoing progress + a
terminal state (never fire-and-forget). **The VMs launched from `deployment-service` are the monitoring's system of
record** — its resource-logging (`HostMetricsSampler` → `host_metrics_window` / BigQuery
`deployment_operational_data.resource_samples`) is what Step 6 reads, so launching outside that path (a hand-rolled
`gcloud compute instances create`) loses monitoring coverage entirely, not just naming-registry coverage.

## 5. During the run — watch on the right cadence, right signal

- **Progress metric**: the TARGET artifact count (real captured rows for this exact source/window), never activity (log
  lines, heartbeat) — per `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` § "Backfill progress = the TARGET
  ARTIFACT, entity-scoped."
- **Preemption/billing-waste**: run `/vm-preemption-billing-waste-audit` if the wave is expected to run long enough to
  matter (>30 min) or crosses a SPOT-eligible window — catches a silently-un-relaunched preemption or a re-attempted
  structurally-dead shard before it becomes a multi-hour surprise.
- **Watchdog sizing**: per the hardened `async-wait-and-poll-discipline.md` rule — size any watchdog to THIS launch
  family's own documented/estimated duration (Step 1), never a flat short cap; a multi-hour backfill needs one long
  event-driven monitor, not a chain of short re-arms.

## 6. Post-launch — recalibrate against the pre-flight estimate

Run `/vm-resource-rightsizing-check` for real (representative sample, not immediately after boot). Compare against Step
1's estimate:

- **Matched the estimate**: note it as confirmed precedent for the next wave of this same family — this is how the
  precedent library in Step 1 grows instead of every wave re-guessing from scratch.
- **Over-provisioned** (Step 1 guessed too big): downsize per `/vm-resource-rightsizing-check`'s own Step 4
  verdict/action guidance, and update Step 1's precedent note for this family so the NEXT wave starts from the corrected
  estimate, not the original guess.
- **Under-provisioned / rising memory trend**: do not let this wave OOM-crash to find out — if the trend is visible
  early enough (Step 1's own "check no earlier than ~15-20 min in" guidance), upsize or split the remaining window
  before it fails, rather than waiting for a crash-and-relaunch cycle.

## Report

For each backfill wave covered by this skill: the source/window/launcher, Step 0's pre-flight verdict (clean /
pre-existing issues found + handled), Step 1's sizing estimate + basis (precedent cited / smoke-test-derived /
genuinely-uncertain), Step 3's smoke-test result (pass / fail+fixed / fail+blocked), the real launch's VM name(s) +
isolation posture (one-source-per-VM confirmed), Step 5's during-run findings (preemption/billing-waste, if any), and
Step 6's final rightsizing verdict + whether the family's precedent note was updated. No findings at any step is a
valid, expected outcome — say so plainly.

## What this skill does NOT do

Does not replace `/data-pipeline-alerts-reconcile`, `/vm-resource-rightsizing-check`, or
`/vm-preemption-billing-waste-audit` — it sequences them, they do the actual work. Does not skip the smoke test for a
"probably fine" launcher just because a precedent exists for a DIFFERENT family — precedent only substitutes for the
sizing guess (Step 1), never for the correctness smoke test (Step 3), since a schema/manifest-write bug is
per-launcher-code, not per-machine-type. Does not resize or kill a currently-running VM itself (same carve-out as
`/vm-resource-rightsizing-check`). Does not bundle multiple data sources onto one VM to save boot overhead — that
tradeoff is explicitly rejected by the isolation rule (§ 2) regardless of apparent efficiency gains.

## Composes with

`/data-pipeline-alerts-reconcile` (§ 0), `/vm-resource-rightsizing-check` (§ 1, § 6),
`/vm-preemption-billing-waste-audit` (§ 5), `/data-pipeline-check-mtds` (§ 3's smoke-test shape is the same
force/skip-leg pattern, scaled down), `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (§ 5's watch/watchdog
discipline), `/codex/05-infrastructure/vm-launcher-runbook.md` (§ 4's launch discipline).

## Provenance

Built 2026-08-12 from the TradFi MVP-of-the-MVP backfill relaunch
(`tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`, `tradfi_vix_backfill_launch_failed_2026_08_10.md`) — a
real-scope 7-VM VIX launch hit 2 code bugs (schema regression, manifest row_key bug) and a SPOT-preemption near-total
loss (5/7 VMs preempted within minutes) that a small smoke test would have caught cheaply before the real-scope
commitment, plus the same session's separately-discovered tradfi fleet rightsizing finding (245 VMs averaging 6-7% CPU
on 16-vCPU machines, undetected for weeks). This skill is explicitly a living document — extend it with new gaps found
in real backfill-monitor use, per the operator's own instruction, rather than treating it as a finished checklist.
