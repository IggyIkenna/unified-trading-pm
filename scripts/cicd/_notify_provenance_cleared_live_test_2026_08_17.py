#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: temporary
# Delete-when: immediately after this live test completes (same session, 2026-08-17)
"""Deliberate, operator-approved live test of the new provenance BLOCKED/CLEARED Slack
notifications added to ldr-to-main-promote.yml this session.

This file is committed DIRECTLY to live-defi-rollout (no Quickmerge trailer) on purpose, to
produce a real strict-quickmerge violation that exercises the notify-provenance-blocked job.
It is deleted via a normal quickmerge-shipped commit immediately after the test confirms both
the BLOCKED and CLEARED notifications fire correctly. Not meant to persist.
"""
