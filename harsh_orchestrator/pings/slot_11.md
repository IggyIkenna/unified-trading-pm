[2026-05-19 15:00 UTC] slot-1-main → slot 11 (Harsh side) — 🔴 OPERATOR BROADCAST: commit + push your dirty work to slot
branch + FF to LDR. See
[`plans/active/_operator_broadcast_2026_05_19_commit_dirty_work.md`](../../plans/active/_operator_broadcast_2026_05_19_commit_dirty_work.md).
Ack here once your tab is clean.

---

# Slot 11 ping log

---

[2026-05-19 12:15 UTC] main → slot 11 — 🔄 RULES REFRESH + NEW WORK ASSIGNMENT (2026-05-19)

**Action required (in order)**:

1. Pull LDR in ALL your repos:
   `cd ${WORKSPACE_ROOT}/.tabs/11/<repo> && git fetch origin --quiet && git rebase origin/live-defi-rollout`
2. Re-read `harsh_orchestrator/AGENT_ONBOARDING.md` (updated boot context)
3. Read `plans/active/agent_orchestrator_slack_notifications_2026_05_19.md + work_split_2026_05_19_harsh.md § Slot 11` —
   this is your slot's work for today

**Key rule change now in force** (QG STEP 5.83 — landed PM@429b64b2b):

- `base-service.sh` now runs `check_uac_hard_required_fields.py` as STEP 5.83
- Validates UAC `validate_instrument_records()` still present + bundled shard-key kwargs correct
- Any service that runs `bash scripts/quality-gates.sh` will hit this gate on next run
- If your QG fails at STEP 5.83 on a file you don't own: log it, skip, continue

**Today's assignment — Slot 11**: agent_orchestrator_slack_notifications: P1 first (server/notifications/slack.py + unit
tests — no Cloud Run needed). Then P2 (event hook wiring). P0 (--update-secrets) waits for Slot 10 P1. Then P3 staging
smoke (real message to #agent-orchestrator-alerts). No human gates. (~2 cal)

Ack this ping by appending `[2026-05-19 12:15 UTC] slot 11 — STARTED <first item>` below.
