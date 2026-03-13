# SIT (System Integration Tests) Runbook

## Force-Unlock Staging

If staging is locked and SIT is stuck/failed, force-unlock with:

```bash
gh api repos/IggyIkenna/unified-trading-pm/dispatches \
  -X POST \
  -f event_type="sit-unlock"
```

Or manually edit `workspace-manifest.json`:

```json
"staging_status": {
  "locked": false,
  "locked_since": null,
  "locked_reason": null,
  "lock_version": null
}
```

Then commit with `[skip ci]` to avoid re-triggering cascades.

## Manual SIT Trigger

```bash
gh workflow run system-integration-tests.yml \
  --repo IggyIkenna/system-integration-tests \
  --ref main
```

Or via dispatch:

```bash
gh api repos/IggyIkenna/system-integration-tests/dispatches \
  -X POST \
  -f event_type="staging-changed" \
  -f client_payload='{"reason": "manual-trigger"}'
```

## Starvation Detector

The starvation detector is a scheduled workflow that checks if staging has been locked for longer than a configured
threshold (default: 2 hours). It runs every 30 minutes and:

1. Reads `staging_status.locked_since` from `workspace-manifest.json`
2. Computes elapsed time since lock acquisition
3. If elapsed > threshold: sends Telegram alert and optionally dispatches `sit-unlock`

When it fires, it means SIT either failed silently, hung, or was never triggered after a staging lock.

## Common Failure Modes

| Failure Mode              | Symptoms                                        | Fix                                                                                                           |
| ------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **OOM**                   | SIT runner killed, exit code 137                | Increase runner memory or split test suite into shards                                                        |
| **Quota exceeded**        | GH API 403 / rate limit errors                  | Wait for quota reset (1h); reduce parallel dispatches                                                         |
| **Network timeout**       | Emulator connection refused / curl timeouts     | Check emulator health; restart docker-compose stack                                                           |
| **Staging lock stuck**    | `staging_status.locked = true` for >2h          | Force-unlock (see above); check SIT logs for root cause                                                       |
| **SHA pinning violation** | staging-to-main aborts with "untested commits"  | New commits landed in staging after SIT ran; SIT auto-re-triggers                                             |
| **Merge conflict**        | staging-to-main reports "dirty" mergeable_state | Resolve conflict on the repo's staging branch; re-run promotion                                               |
| **Manifest corruption**   | JSON parse errors on workspace-manifest.json    | `git log -1 workspace-manifest.json` to find last good state; `git checkout <sha> -- workspace-manifest.json` |

## Escalation Path

1. **Automated**: Telegram alert fires (starvation detector or dead man switch)
2. **L1 — Self-service**: Check this runbook; try force-unlock + manual SIT trigger
3. **L2 — Investigation**: Check GHA run logs at `github.com/IggyIkenna/system-integration-tests/actions`; check
   emulator logs
4. **L3 — Owner escalation**: If the problem is in the cascade logic (update-repo-version, staging-to-main), escalate to
   PM repo owner
5. **Emergency**: If staging is blocking a hotfix, use `staging-to-main` workflow_dispatch with `start_from_repo` to
   resume partial promotion, or manually merge the hotfix repo's staging->main PR
