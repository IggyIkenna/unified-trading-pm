---
doc_type: issue
title: >-
  alerting-service: missing PagerDuty secret crashed every CONSOLIDATOR_DOWN fire (10+h of false ALERT_DISPATCH_FAILED
  paging), no email fallback existed, and CONSOLIDATOR_DOWN bypassed the recurring-alert dedup cooldown entirely
summary: >-
  Operator-directed investigation of a repeating `ALERT_DISPATCH_FAILED` page (observed every ~1-60 min for 10+ hours
  straight). Root-caused to three compounding bugs in `alerting-service`: (1) `notifiers/pagerduty.py`'s routing-key
  Secret Manager lookup raised an unguarded `RuntimeError` when the secret was absent (PagerDuty was never provisioned)
  — every `send_event()` call crashed, caught only generically by `alert_subscriber.py`'s `_page_own_dispatch_failure`;
  (2) `AlertingSystemConfig` declared `email_smtp_host`/`email_smtp_port`/`email_to` fields with ZERO consumers anywhere
  in the repo — no fallback channel existed for a CRITICAL event when PagerDuty was down; (3) `CONSOLIDATOR_DOWN` (and,
  once found, `MANIFEST_CONSOLIDATION_FAILED`/`FEED_REFETCH_FAILED`) dispatch via `route_event_with_explicit_channels`,
  which used the deduplicator's bare 60s default and never consulted `router._dedup_window_for`'s
  `_RECURRING_ALERT_COOLDOWNS` map at all — so a still-down consolidator re-paged (and re-crashed on bug 1) roughly
  every minute instead of firing once and re-reminding hourly. All three fixed and shipped same session.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service]
scope: [engineer]
tags: [alerting, pagerduty, email-fallback, dedup, consolidator, observability, secret-manager, capability-probe]
related:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    plans/archive/2026_05/manifest_reader_fail_fast_on_stale_fallback_2026_05_28.md,
  ]
created: 2026-08-06
author: unknown
priority: P1
parent_epic: observability_master
source:
  [
    "Operator-directed investigation, 2026-08-06 — observed ALERT_DISPATCH_FAILED repeating every ~1-60 min for 10+
    hours straight in production alerting-service logs",
    alerting-service/alerting_service/notifiers/pagerduty.py,
    alerting-service/alerting_service/notifiers/router.py,
    alerting-service/alerting_service/subscribers/alert_subscriber.py,
  ]
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
  "alerting-service@4e252b4 (all three fixes + CONSOLIDATOR_RECOVERED wiring + regression tests), same session"
---

# alerting-service: missing PagerDuty secret crash, no email fallback, CONSOLIDATOR_DOWN dedup bypass

## What I found (verified against live code, 2026-08-06)

1. **PagerDuty secret-lookup crash, zero fallback.** `notifiers/pagerduty.py`'s `_get_routing_key()` raised
   `RuntimeError(f"Secret '{_SECRET_NAME}' not found in Secret Manager")` when `alerting-pagerduty-routing-key` was
   absent — it genuinely does not exist in Secret Manager (PagerDuty was never provisioned). Called unguarded inside
   `send_event()`; that function's `try/except` wraps only the `httpx.post` call, not the secret lookup. The call site
   in `router._deliver_to_channels` (`pd_send_event(...)`) has no surrounding try/except either. Only caught generically
   in `subscribers/alert_subscriber.py::_route_one`, which then pages `ALERT_DISPATCH_FAILED` via
   `_page_own_dispatch_failure()` — this is the exact message the operator was seeing repeatedly.

2. **No email notifier existed.** `config.py` declared `email_smtp_host`/`email_smtp_port`/`email_to` fields with **zero
   consumers** anywhere in the repo — no notifier module, no `smtplib`/`sendgrid`/SES usage. `email_to` was further
   broken as a plain dead `ClassVar[list[str]] = []` (a shared mutable class attribute, not a real per-instance config
   field — could never be configured via env/SM even if a consumer existed). Checked `unified-trading-library` first
   (the only shared dep this T4 service may import) for a reusable email utility — none exists there either.

3. **Dedup is a TTL cooldown keyed per-event, not real fire-once/stay-quiet/resolve — and CONSOLIDATOR_DOWN was
   bypassing even that.** `router.route_event()` consults `_dedup_window_for()` → `_RECURRING_ALERT_COOLDOWNS` (a real,
   working, already-shipped mechanism for e.g. `DP_RUN_MOSTLY_EMPTY`). But `CONSOLIDATOR_DOWN` is dispatched via
   `rules/consolidator_rules.py::handle_consolidator_down_payload` → `route_event_with_explicit_channels` **directly**,
   bypassing `route_event()` (and its cooldown-aware dedup check) entirely. Separately,
   `route_event_with_explicit_channels`'s OWN dedup check called `_deduplicator.is_duplicate(event_name, details)` with
   **no `ttl_override`** — always the bare 60s default, regardless of what `_RECURRING_ALERT_COOLDOWNS` said. Net
   effect: the cooldown map had **zero effect** on CONSOLIDATOR_DOWN, which re-fired (and re-crashed on bug 1) roughly
   every 60s for 10+ hours. The same bypass pattern affects `MANIFEST_CONSOLIDATION_FAILED` (once its breaker escalates
   to CRITICAL) and `FEED_REFETCH_FAILED` (once ITS breaker opens) — both dispatch via the same
   `route_event_with_explicit_channels` direct path.

4. **Bonus finding, in scope of the same fix:** `CONSOLIDATOR_RECOVERED` (the RESOLVED half of the same UTL liveness
   watchdog) was **completely unwired** — no typed handler, not in `_TYPED_HANDLERS`, not in any UAC alert registry — so
   it silently no-opped through the router's no-match Slack fallback (`_is_runtime_alert` returns False for an
   unregistered event name → `_deliver_to_uts_live_alerts_slack` treats it as a non-runtime no-op). This meant that even
   with dedup fixed, the operator would still never see a "consolidator is back" notification — only the dwindling
   hourly re-reminds while it stayed down, then silence.

## Fix shipped (alerting-service@4e252b4)

- **`notifiers/pagerduty.py`**: `_probe_routing_key()` — an `lru_cache`-wrapped, process-lifetime capability probe
  (mirrors the `_ACTUATORS_AVAILABLE = importlib.util.find_spec(...)` pattern used elsewhere in this workspace, e.g.
  deployment-service's `escalation.py`). Probes Secret Manager ONCE, catches every exception (missing secret AND any
  SM-call failure), logs a single WARNING, returns `None`. `send_event()` now returns `False` on an unavailable routing
  key instead of raising. Added `is_available()` for health-checks/tests.
- **`notifiers/email.py` (new)**: CRITICAL-severity email fallback, implemented directly with the Python stdlib
  `smtplib` + `email.message` (no reusable UTL utility existed, confirmed by grep; no new third-party dependency). SMTP
  host/port stay plain `AlertingSystemConfig` fields (non-secret); username/password/from-address are SM-hot-reloaded
  via `config_reloaders.py`'s existing `_PagingCredentialsReloader` (new SM keys `alerting-email-smtp-username` /
  `-password` / `alerting-email-from-address`, same precedence as every other paging credential — SM first, config-field
  env fallback second). `config.py`'s `email_to` fixed from the dead `ClassVar` to a real `Field(default_factory=list)`.
  Wired into `router._deliver_to_channels`: fires only when `pd_send_event()` returns `False` for a CRITICAL-severity
  event; own `log_event("EMAIL_FALLBACK_SENT"/"_FAILED", …)` observability (kept the router.py diff to a ~3-line hook,
  not a full GCS delivery record, to stay under this file's 1100-line QG cap — `router.py` was already at 1093/1100
  before this change).
- **`notifiers/router.py`**: `route_event_with_explicit_channels` now calls
  `_deduplicator.is_duplicate(event_name, details, ttl_override=_dedup_window_for(event_name, details))` — the SAME
  cooldown-aware check `route_event()` already used. Added `CONSOLIDATOR_DOWN` / `MANIFEST_CONSOLIDATION_FAILED` /
  `FEED_REFETCH_FAILED` to `_RECURRING_ALERT_COOLDOWNS` at 3600s (hourly) each — fire once, hourly re-remind while still
  down, matching the operator's explicit ask ("when things are down they don't need to refire if still down, they can
  just fire once and fire again when resolved"). Did NOT touch the existing `DP_RUN_MOSTLY_EMPTY` entry.
- **`rules/consolidator_rules.py` + `subscribers/alert_subscriber.py`**: added `handle_consolidator_recovered_payload`
  (INFO, Telegram/Slack-only, no page) and wired `CONSOLIDATOR_RECOVERED` into both `route_consolidator_event` and the
  subscriber's `_TYPED_HANDLERS` — the RESOLVED half of the state transition. A different `event_name` always hashes to
  a different dedup key, so it is never suppressed by `CONSOLIDATOR_DOWN`'s new hourly cooldown.
- **Regression tests**: `tests/unit/notifiers/test_pagerduty.py` (capability-probe: missing secret / SM exception /
  never-raises / probed-once-not-per-call / `is_available()`), `tests/unit/notifiers/test_email.py` (new — SMTP send
  success/failure/missing-config, SM-vs-config-field credential precedence), `tests/unit/notifiers/test_router.py` (new
  cooldown-map entries, `route_event_with_explicit_channels` now honouring the cooldown, email-fallback wiring in
  `_deliver_to_channels`), `tests/unit/rules/test_consolidator_rules.py` (CONSOLIDATOR_RECOVERED handler + dispatch).
  Also fixed a pre-existing test (`tests/unit/test_paging_credentials_reloader.py`'s `_ALL_PAGING_KEYS` hardcoded
  key-set) that broke because it didn't know about the 3 new SM-hot-reload keys — caught by the first `quality-gates.sh`
  run before shipping, not a follow-up.

**Verified before shipping**: `quality-gates.sh` green (ruff, basedpyright, workflow-yaml, 945 tests passed, 80.28%
coverage vs 76% floor), sentinel `.qg_last_passed_sha` matched `HEAD` at commit time, shipped via
`quickmerge.sh --agent --files '<12 files>'`, landed on `live-defi-rollout` as `4e252b4` (`git show --stat` confirms all
12 files: `config.py`, `config_reloaders.py`, `notifiers/email.py` (new), `notifiers/pagerduty.py`,
`notifiers/router.py`, `rules/consolidator_rules.py`, `subscribers/alert_subscriber.py`, and the 5 test files — 848
insertions, 40 deletions).

## Todos

- [x] ✅ [SCRIPT] P1. Fix PagerDuty secret-lookup crash — capability-probe pattern, degrade gracefully instead of
      raising. `alerting-service@4e252b4`.
- [x] ✅ [SCRIPT] P1. Implement CRITICAL-severity email fallback notifier, SM-hot-reloaded SMTP creds, wired into the
      router's PagerDuty-failure path. `alerting-service@4e252b4`.
- [x] ✅ [SCRIPT] P1. Give CONSOLIDATOR_DOWN (+ MANIFEST_CONSOLIDATION_FAILED + FEED_REFETCH_FAILED) real
      state-transition dedup via the existing cooldown-map mechanism, fixing the `route_event_with_explicit_channels`
      bypass; wire the previously-unhandled CONSOLIDATOR_RECOVERED resolved-notification. `alerting-service@4e252b4`.
- [x] ✅ [SCRIPT] P2. Add regression tests for all three fixes + the CONSOLIDATOR_RECOVERED wiring.
      `alerting-service@4e252b4`.
- [ ] [OPERATOR] P3. Provision the `alerting-pagerduty-routing-key` Secret Manager secret (and, if email fallback is
      wanted as a standing channel rather than pure last-resort, the `alerting-email-smtp-username` /
      `alerting-email-smtp-password` / `alerting-email-from-address` secrets + `email_smtp_host`/`email_to` config) —
      PagerDuty and the email fallback both degrade gracefully today (logged, no crash, no page lost silently via the
      Slack primary channel) but genuinely have NO delivery channel until these are provisioned. Not blocking; the
      crash/refire-storm this doc tracks is fully fixed regardless of whether PagerDuty is ever provisioned.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-alerting.md` — standing-condition dedup-by-state-transition precedent this
  fix follows (fire on change / RESOLVED / re-remind, never every tick).
