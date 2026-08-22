#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# migrate-personal-settings-keys.sh — pull personal keys (model/effortLevel/theme) out of the
# gitignored team-shared cursor-configs/settings.json and into the REAL, personal
# ~/.claude/settings.json, without ever clobbering an already-set personal choice.
#
# WHY THIS EXISTS: cursor-configs/settings.json is meant to hold ONLY team policy (permissions,
# mcpServers, hooks) — see codex/05-infrastructure/claude-code-settings-symlink.md. In practice a
# stray `/model` or `/effort` switch (or an old symlinked ~/.claude/settings.json — the exact bug
# in /plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md) can leave
# personal keys sitting in the team file, where they don't belong and can silently drift onto
# other slots/machines that inherit it. This script is the one-shot self-heal for any machine that
# hits the same pattern:
#   1. If ~/.claude/settings.json is STILL a symlink INTO the team file (the root cause of the
#      2026-07-23 incident), convert it to a real file first, preserving current content.
#   2. For each personal key found in the team file: if your personal file doesn't already set it,
#      migrate the value over; if it already does, your choice wins — never overwritten.
#   3. Strip the personal keys from the team file either way (they never belong there).
#
# Idempotent, best-effort (never touches an unrelated symlink, never fails loudly). Safe to run
# repeatedly, and safe to wire into an automated linker (see link-claude-skills.sh).
#
# Usage: migrate-personal-settings-keys.sh [TEAM_SETTINGS_PATH]
#   TEAM_SETTINGS_PATH defaults to cursor-configs/settings.json relative to this script's PM repo.
set -u

PERSONAL_KEYS=(model effortLevel theme)

_self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${_self}/../.." && pwd)"
TEAM_SETTINGS="${1:-${PM_DIR}/cursor-configs/settings.json}"
PERSONAL_SETTINGS="${HOME}/.claude/settings.json"

command -v jq >/dev/null 2>&1 || { echo "[migrate-personal-settings-keys] jq not found — skipping (non-blocking)" >&2; exit 0; }

[ -f "$TEAM_SETTINGS" ] || { echo "[migrate-personal-settings-keys] no ${TEAM_SETTINGS} — nothing to migrate"; exit 0; }

# ── Step 1: ~/.claude/settings.json must be a REAL file, never a symlink to the team file ──
if [ -L "$PERSONAL_SETTINGS" ]; then
    _resolved="$(readlink -f "$PERSONAL_SETTINGS" 2>/dev/null)"
    _team_resolved="$(readlink -f "$TEAM_SETTINGS" 2>/dev/null)"
    if [ -n "$_resolved" ] && [ "$_resolved" = "$_team_resolved" ]; then
        echo "[migrate-personal-settings-keys] ${PERSONAL_SETTINGS} is a symlink INTO the team file (the exact bug from 2026-07-23) — converting to a real file"
        _content="$(cat "$PERSONAL_SETTINGS" 2>/dev/null || echo '{}')"
        rm -f "$PERSONAL_SETTINGS"
        printf '%s\n' "$_content" > "$PERSONAL_SETTINGS"
    else
        echo "[migrate-personal-settings-keys] ${PERSONAL_SETTINGS} is a symlink to something else — leaving it alone (non-blocking)" >&2
        exit 0
    fi
fi

[ -f "$PERSONAL_SETTINGS" ] || { mkdir -p "$(dirname "$PERSONAL_SETTINGS")" && echo '{}' > "$PERSONAL_SETTINGS"; }

jq empty "$TEAM_SETTINGS" 2>/dev/null || { echo "[migrate-personal-settings-keys] ${TEAM_SETTINGS} is not valid JSON — skipping (non-blocking)" >&2; exit 0; }
jq empty "$PERSONAL_SETTINGS" 2>/dev/null || { echo "[migrate-personal-settings-keys] ${PERSONAL_SETTINGS} is not valid JSON — refusing to touch it (non-blocking)" >&2; exit 0; }

# ── Step 2: find personal keys sitting in the team file, migrate any your personal file lacks ──
_found_any=0
for key in "${PERSONAL_KEYS[@]}"; do
    _team_val="$(jq -r --arg k "$key" '.[$k] // empty' "$TEAM_SETTINGS" 2>/dev/null)"
    [ -z "$_team_val" ] && continue
    _found_any=1

    _personal_has="$(jq -r --arg k "$key" 'has($k)' "$PERSONAL_SETTINGS" 2>/dev/null)"
    if [ "$_personal_has" = "true" ]; then
        echo "[migrate-personal-settings-keys] ${key}=${_team_val} found in team file but ${PERSONAL_SETTINGS} already sets ${key} — NOT overwriting your choice, just stripping the team-file copy"
    else
        echo "[migrate-personal-settings-keys] migrating ${key}=${_team_val} → ${PERSONAL_SETTINGS} (was absent there)"
        _tmp="$(mktemp)"
        jq --arg k "$key" --arg v "$_team_val" '.[$k] = $v' "$PERSONAL_SETTINGS" > "$_tmp" && mv "$_tmp" "$PERSONAL_SETTINGS"
    fi
done

if [ "$_found_any" -eq 0 ]; then
    echo "[migrate-personal-settings-keys] ${TEAM_SETTINGS} clean — no personal keys to migrate"
    exit 0
fi

# ── Step 3: strip personal keys from the team file (they never belong there) ──
_tmp="$(mktemp)"
_jq_prog="."
for key in "${PERSONAL_KEYS[@]}"; do
    _jq_prog="${_jq_prog} | del(.${key})"
done
jq "$_jq_prog" "$TEAM_SETTINGS" > "$_tmp" && mv "$_tmp" "$TEAM_SETTINGS"
echo "[migrate-personal-settings-keys] stripped personal keys from ${TEAM_SETTINGS}"
exit 0
