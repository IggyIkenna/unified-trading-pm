#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the Phase-4 Slack-alerting helpers in qg-host-governor.sh — closes
# plans/active/qg_host_adaptive_resource_governor_2026_07_14.md's open Phase-4 todo
# ("Slack alerting via the reusable notify-slack.yml/carrier ... three triggers: per-run
# RSS over its 1.2x cap; ... host RAM > 80% abort").
#
# curl is mocked (a fake `curl` shimmed onto PATH that just logs its own invocation) so
# no network call ever happens and the suite is fast + deterministic. Covers:
#   (A) no webhook set               -> no post
#   (B) non-https webhook            -> no post (guards against an unset/masked secret)
#   (C) valid https webhook          -> posts, dedup marker written
#   (D) repeat within cooldown       -> suppressed (same dedup_key)
#   (E) repeat after cooldown elapses -> posts again (marker backdated)
#   (F) _qg_governor_check_overrun: token mode + exit 137     -> no post (cap is the flat
#       legacy default there, not a baseline signal)
#   (G) _qg_governor_check_overrun: reservation mode + exit 0 -> no post (not an overrun)
#   (H) _qg_governor_check_overrun: reservation mode + exit 137 -> posts
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-slack-alert.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
FAILFILE="$TMP/fails.log"
: > "$FAILFILE"
eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; echo "$1" >> "$FAILFILE"; fi; }

export QG_LEDGER_DIR="$TMP/ledger"

# Fake curl: records one line per invocation to CURL_LOG, never touches the network.
CURL_LOG="$TMP/curl_calls.log"
: > "$CURL_LOG"
FAKEBIN="$TMP/fakebin"
mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/curl" <<EOF
#!/usr/bin/env bash
echo "curl \$*" >> "$CURL_LOG"
exit 0
EOF
chmod +x "$FAKEBIN/curl"
export PATH="$FAKEBIN:$PATH"

# shellcheck source=/dev/null
source "$GOV"

reset_calls() { : > "$CURL_LOG"; }
call_count() { wc -l < "$CURL_LOG" | tr -d ' '; }

# ── (A) no webhook set — no post ──────────────────────────────────────────────
(
    unset SLACK_CI_WEBHOOK_URL SLACK_WEBHOOK_URL
    reset_calls
    _qg_governor_slack_alert "CRITICAL" "test-a" 30 "message a"
    eq "(A) no webhook: curl not invoked" "0" "$(call_count)"
)

# ── (B) non-https webhook — no post ───────────────────────────────────────────
(
    export SLACK_CI_WEBHOOK_URL="not-a-url"
    reset_calls
    _qg_governor_slack_alert "CRITICAL" "test-b" 30 "message b"
    eq "(B) non-https webhook: curl not invoked" "0" "$(call_count)"
)

# ── (C) valid https webhook — posts, dedup marker written ────────────────────
(
    export SLACK_CI_WEBHOOK_URL="https://hooks.example.test/services/T/B/X"
    reset_calls
    _qg_governor_slack_alert "CRITICAL" "test-c" 30 "message c"
    eq "(C) https webhook: curl invoked once" "1" "$(call_count)"
    marker_exists=false
    [[ -f "$(_qg_slack_alert_dir)/test-c.ts" ]] && marker_exists=true
    eq "(C) dedup marker written" "true" "$marker_exists"
)

# ── (D) repeat within cooldown — suppressed ───────────────────────────────────
(
    export SLACK_CI_WEBHOOK_URL="https://hooks.example.test/services/T/B/X"
    reset_calls
    _qg_governor_slack_alert "CRITICAL" "test-d" 30 "first"
    first_calls="$(call_count)"
    _qg_governor_slack_alert "CRITICAL" "test-d" 30 "second (should suppress)"
    eq "(D) first call posts" "1" "$first_calls"
    eq "(D) repeat within cooldown suppressed (no new curl call)" "1" "$(call_count)"
)

# ── (E) repeat after cooldown elapses — posts again ───────────────────────────
(
    export SLACK_CI_WEBHOOK_URL="https://hooks.example.test/services/T/B/X"
    reset_calls
    _qg_governor_slack_alert "CRITICAL" "test-e" 1 "first"
    # Backdate the marker well past the 1-minute cooldown instead of sleeping.
    marker="$(_qg_slack_alert_dir)/test-e.ts"
    echo "$(( $(date +%s) - 120 ))" > "$marker"
    _qg_governor_slack_alert "CRITICAL" "test-e" 1 "second (cooldown elapsed)"
    eq "(E) repeat after cooldown elapsed posts again" "2" "$(call_count)"
)

# ── (F) overrun check: token mode + exit 137 — no post ────────────────────────
(
    export SLACK_CI_WEBHOOK_URL="https://hooks.example.test/services/T/B/X"
    unset QG_GOVERNOR_MODE
    reset_calls
    _qg_governor_check_overrun "testrepo" "TESTS" 137
    eq "(F) token mode + exit 137: no post" "0" "$(call_count)"
)

# ── (G) overrun check: reservation mode + exit 0 — no post ────────────────────
(
    export SLACK_CI_WEBHOOK_URL="https://hooks.example.test/services/T/B/X"
    export QG_GOVERNOR_MODE=reservation
    reset_calls
    _qg_governor_check_overrun "testrepo" "TESTS" 0
    eq "(G) reservation mode + exit 0: no post" "0" "$(call_count)"
)

# ── (H) overrun check: reservation mode + exit 137 — posts ────────────────────
(
    export SLACK_CI_WEBHOOK_URL="https://hooks.example.test/services/T/B/X"
    export QG_GOVERNOR_MODE=reservation
    reset_calls
    _qg_governor_check_overrun "testrepo" "TYPE CHECK" 137
    eq "(H) reservation mode + exit 137: posts" "1" "$(call_count)"
)

echo "────────────────────────────────────────"
FAILS=$(wc -l < "$FAILFILE" | tr -d ' ')
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
