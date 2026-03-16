# Emergency Exit Playbooks

## Overview

This directory contains the **editable source** templates for emergency exit playbooks and client risk tolerance
configuration. These are deployed to GCS for runtime use.

## Files

- `exit_playbooks.yaml` — Per-strategy exit procedures. Defines what "close all positions" means for each strategy type.
- `client_risk_tolerance_template.yaml` — Template for per-client risk thresholds.

## Deployment

Templates are synced to GCS by deployment-service:

- `exit_playbooks.yaml` → `gs://config/emergency/exit_playbooks.yaml`
- Per-client configs → `gs://config/clients/{client_id}/risk_tolerance.yaml`

## Schema

All schemas are defined in `unified-internal-contracts`:

- `EmergencyExitType`, `EmergencyExitStep`, `EmergencyExitPlaybook`
- `ClientRiskTolerance`
- `KillSwitchScope`, `ScopedKillSwitchState`

See `unified-internal-contracts/unified_internal_contracts/domain/risk_service/risk.py`
