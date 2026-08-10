#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: a NEW accidental (undeclared) dispatch-exclusion is caught at COMMIT time.
#
# THE FAILURE THIS PREVENTS (2026-08-10). `check_ao_dispatch_visibility_gate.py` is corpus-wide
# and full-gate-only. A `docs(plans):` push runs prek alone, so a plan whose open todo is held by
# a marker buried mid-sentence lands on origin unchallenged — and then fails on some unrelated
# agent's full quality-gates run, pointing at whichever commit happened to trigger it. This
# session lost a diagnosis to exactly that indirection: the gate was read as "content on origin is
# broken and blocks everyone", when the honest reading was "a plan authored hours ago carried an
# undeclared marker, and normal fleet activity later closed those todos".
#
# The negative cases carry the weight. A gate that flagged correctly-declared holds would push
# authors to delete the marker instead of declaring it, which loses the signal the marker exists
# to carry — strictly worse than not checking.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  CHECK="${REPO_ROOT}/scripts/plan-hygiene/check_accidental_exclusions_only.sh"
  AO_PY="$(dirname "$REPO_ROOT")/agent-orchestrator/.venv/bin/python3"
  # A real AO-dispatched plan with open todos and no pre-existing accidental exclusion.
  SRC="${REPO_ROOT}/plans/active/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07_finalize_2026_08_09.md"
  PROBE="${REPO_ROOT}/plans/active/.accex_bats_probe.md"
  [ -f "$SRC" ] || skip "source plan absent (corpus moved) — pick another assigned_vm: planning plan"
  [ -x "$AO_PY" ] || skip "sibling agent-orchestrator venv absent — the check is a no-op here by design"
}

teardown() {
  rm -f "${PROBE:-/nonexistent}"
}

@test "a mid-sentence marker in an open todo is caught" {
  cp "$SRC" "$PROBE"
  printf '\n- [ ] [INFRA] P3. **Probe** — cannot proceed until the vendor replies, so treat as BLOCKED-CREDENTIALS for now.\n' >> "$PROBE"
  run bash "$CHECK" "$PROBE"
  [ "$status" -eq 1 ]
  [[ "$output" == *"does not declare itself"* ]]
  # The remedy has to name the fix, not just the rule.
  [[ "$output" == *"head of the line"* ]]
}

@test "a marker declared inside the leading tag cluster is NOT flagged" {
  cp "$SRC" "$PROBE"
  printf '\n- [ ] [BLOCKED-CREDENTIALS][INFRA] P3. **Declared** — waiting on the vendor.\n' >> "$PROBE"
  run bash "$CHECK" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "a marker declared at the head of the description is NOT flagged" {
  cp "$SRC" "$PROBE"
  printf '\n- [ ] BLOCKED-CREDENTIALS [INFRA] P3. **Declared** — waiting on the vendor.\n' >> "$PROBE"
  run bash "$CHECK" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "an unmodified plan is clean" {
  cp "$SRC" "$PROBE"
  run bash "$CHECK" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "a plan with no marker token at all short-circuits without invoking the AO module" {
  # The pre-filter is what keeps this affordable on the hot path: the AO module costs ~8s to
  # import, and the repo's central problem is that the commit critical section already exceeds
  # the gap between commits. If this ever starts paying the import for marker-free plans, the
  # gate becomes a regression in the thing this whole workstream exists to fix.
  cp "$SRC" "$PROBE"
  # Strip every marker token so the pre-filter must short-circuit.
  sed -i.bak 's/BLOCKED-[A-Z][A-Z0-9-]*/HELD/g; s/DEFERRED-BY-DESIGN/HELD/g; s/STRETCH/HELD/g' "$PROBE"
  rm -f "${PROBE}.bak"
  start=$(date +%s)
  run bash "$CHECK" "$PROBE"
  elapsed=$(( $(date +%s) - start ))
  [ "$status" -eq 0 ]
  [ "$elapsed" -lt 3 ]
}

@test "the check is a silent no-op when handed no files" {
  run bash "$CHECK"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
