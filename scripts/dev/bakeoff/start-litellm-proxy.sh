#!/usr/bin/env bash
# Epic: orchestrator_master (multi_provider_model_capability_bakeoff_2026_08_19)
# Lifecycle: TEMPORARY — delete when that plan archives.
#
# WHY THIS EXISTS: (re)starts the local litellm proxy with the bake-off's provider
# keys actually visible to it. `~/.claude-accounts/litellm-proxy.env` uses plain
# `VAR=value` (no `export`) — a bare `source ...` in the same shell as a
# backgrounded `nohup` command does NOT propagate those vars to the child
# process, so litellm sees no key and fails with "Missing Gemini API key" even
# though the file genuinely has the right value (hit this exactly, 2026-08-19,
# twice, before tracing it to this). `set -a; source; set +a` fixes it.
set -a
source ~/.claude-accounts/litellm-proxy.env
set +a
cd /active/unified-trading-system-repos/.tabs/1/agent-orchestrator
exec ~/.venvs/litellm-proxy/bin/litellm --config config/litellm/grok_gemini_proxy.yaml --host 127.0.0.1 --port 8768
