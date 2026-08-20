#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Plan hygiene sweep — run by Ikenna and Harsh on the planning VM as a morning step.
# Runs all checks in sequence; prints a PASS/FAIL table.
# Hard (ratchet-baselined) checks: todo regression, frontmatter, line caps, terminal-status-
# archived, archive candidates, NA corpus size, reference paths. Soft/advisory checks: estimate
# sanity, superseded-in-active, codex refs, parent-epic alignment, CLAUDE/sub-agent parity,
# delete/VM-launch tagging, priority-vs-tier policy, model-tier coverage.
# Usage: bash scripts/plan-hygiene/run_hygiene_sweep.sh [--ci] [--no-regen] [--precommit]
#   --ci:        exit 1 on any hard failure (for cron/CI); default is interactive (always exits 0)
#   --no-regen:  skip the active-plan inventory regeneration step. Use when the sweep is called
#                from a READ-ONLY context (e.g. plan-reconciler STEP 1 input gather) where dirtying
#                master_to_live_defi_2026_05_23.md is undesirable. Flags may be combined: --ci --no-regen.
#   --precommit: lean, fast, LOCAL-only gate for the prek hook (fires on staged plans/**) —
#                runs the staged-files-only hard checks (frontmatter / todo-format / runbook-fields /
#                todo-regression / ...), NO soft/advisory checks, NO inventory regen, so a
#                plan-touching commit is gated in <1s. The corpus-wide advisory checks stay at
#                the daily cron / CI sweep, never pre-commit. Exit 1 on any hard failure.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

CI_MODE=""
NO_REGEN=""
for _arg in "$@"; do
  case "$_arg" in
    --ci)        CI_MODE="--ci" ;;
    --no-regen)  NO_REGEN="1" ;;
    --precommit) CI_MODE="--precommit" ;;
  esac
done

# ── --precommit: lean STAGED-FILES-ONLY local gate (prek hook) — bypass the heavy sweep body ──
# Validates ONLY the files THIS commit stages, so a pre-existing violation in an unrelated
# plan (e.g. another agent's WIP) never blocks your commit (RULE-11 blast-radius safety). Portable
# for macOS bash 3.2 (no mapfile). Gates the staged-capable HARD checks: frontmatter + todo-format
# on staged plans/**, frontmatter-schema on ALL staged codex/** (parity with CI's lint-codex slice,
# which schema-checks the whole corpus), runbook-fields on staged codex/15-runbooks/incidents/**.
if [ "$CI_MODE" = "--precommit" ]; then
  # --precommit never regenerates inventory (read-only by design)
  STAGED_PLANS=()
  STAGED_RUNBOOKS=()
  STAGED_CODEX=()
  while IFS= read -r line; do
    case "$line" in
      plans/*.md) STAGED_PLANS+=("$PM_DIR/$line") ;;
      codex/*.md)
        # EVERY staged codex doc gets the frontmatter-schema gate (below); runbook incidents
        # ALSO get the runbook-fields gate. Order-independent — a doc can be in both lists.
        STAGED_CODEX+=("$PM_DIR/$line")
        case "$line" in codex/15-runbooks/incidents/*.md) STAGED_RUNBOOKS+=("$PM_DIR/$line") ;; esac
        ;;
    esac
  done < <(git -C "$PM_DIR" diff --cached --name-only --diff-filter=ACM -- plans/ codex/ 2>/dev/null)
  # Separate, filter-unrestricted detection of "did this commit touch plans/ at all" — deliberately
  # NOT the --diff-filter=ACM loop above, because a plan ARCHIVAL is a `git mv` and git's default
  # rename detection reports that as status R, which --diff-filter=ACM excludes. A pure archival
  # commit (git mv plans/active/X.md -> plans/archive/.../X.md, no other plan file touched) would
  # leave STAGED_PLANS empty and skip the whole precommit gate below — exactly the commit shape that
  # needs the broken-link check (see the corpus-wide link check below).
  PLANS_TOUCHED=""
  if git -C "$PM_DIR" diff --cached --name-only -- plans/ 2>/dev/null | grep -q .; then
    PLANS_TOUCHED=1
  fi
  if [ "${#STAGED_PLANS[@]}" -eq 0 ] && [ "${#STAGED_RUNBOOKS[@]}" -eq 0 ] && [ "${#STAGED_CODEX[@]}" -eq 0 ] && [ -z "$PLANS_TOUCHED" ]; then
    echo "plan-hygiene pre-commit: no staged plan/runbook/codex files — skip."
    exit 0
  fi
  PF=0
  if [ -n "$PLANS_TOUCHED" ]; then
    # Corpus-wide broken-link check (not staged-files-only — a link's target can be ANY plan under
    # plans/active/ or plans/archive/, not just the files this commit stages). Fires on every commit
    # that adds/edits/renames anything under plans/, which is exactly what makes this the fast local
    # failure for the archiving agent instead of a fleet-wide QG-red discovered days later by an
    # unrelated worker (unified-trading-pm/plans/active/issues/
    # consolidated_closeout_plans_stale_archive_referrer_links_fleetwide_qg_block_2026_07_25.md).
    python3 "$SCRIPT_DIR/../validators/validate_plan_links.py" --quiet --workspace-root "$(dirname "$PM_DIR")" \
      && echo "  ✅ No broken links (plans/active/*.md, corpus-wide)" \
      || { echo "  ❌ Broken relative link(s) in plans/active/*.md — a referenced doc likely moved/archived without its referrers' paths being updated (CLAUDE.md § 'Plans' archival ritual step 5: 'update every referrer's path corpus-wide')"; PF=$(( PF + 1 )); }
  fi
  if [ "${#STAGED_PLANS[@]}" -gt 0 ]; then
    "$SCRIPT_DIR/check_frontmatter.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Frontmatter validity (staged plans)" || { echo "  ❌ Frontmatter validity (staged plans)"; PF=$(( PF + 1 )); }
    # Value-level schema gate (required NON-EMPTY fields + epic resolution) on the SAME staged
    # plans. check_frontmatter.sh above is presence-only ('---' + deprecated-field), so without this
    # a docs(plans): commit (which takes prek only, NOT full QG) can land a plan/issue doc missing
    # required status/priority on the integration branch — where it then blocks EVERY full QG run
    # fleet-wide. Running the schema check here closes that bypass at commit time. SSOT: check_frontmatter_schema.py.
    python3 "$SCRIPT_DIR/check_frontmatter_schema.py" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Frontmatter schema (staged plans)" || { echo "  ❌ Frontmatter schema — missing/empty required field (staged plans)"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_todo_format.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Todo format (staged plans)" || { echo "  ❌ Todo format (staged plans)"; PF=$(( PF + 1 )); }
    # Conflict-marker gate — catches committed git markers incl. mid-line + prettier-mangled
    # (`> > > > > > >`) forms the other checks miss (see check_conflict_markers.sh, 2026-06-21).
    "$SCRIPT_DIR/check_conflict_markers.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ No conflict markers (staged plans)" || { echo "  ❌ Conflict marker(s) in staged plans — resolve before commit"; PF=$(( PF + 1 )); }
    # Prettier emphasis-mangling gate — blocks landing underscore-identifiers rewritten as
    # asterisks by prettier <3.9.5 (data*type, asset*group, ...). Backstop to the >=3.9.5
    # version guard in scripts/hooks/prettier-autostage.sh. SSOT + repair recipe:
    # plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md
    "$SCRIPT_DIR/check_prettier_mangling.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ No prettier mangling (staged plans)" || { echo "  ❌ Prettier emphasis-mangling in staged plans — run: bash scripts/plan-hygiene/check_prettier_mangling.sh <file> for lines + see the corruption issue doc for the repair recipe"; PF=$(( PF + 1 )); }
    # Line-cap gate on staged plans ONLY — absolute bar (same model as frontmatter/todo-format
    # above, not a baseline delta): if a plan you're touching is over cap, split/trim it before
    # this commit lands, regardless of whether YOUR edit made it worse. No origin fetch, so it
    # stays in the <1s precommit budget. The corpus-wide ratchet (line_caps_baseline.yaml) is a
    # separate, full-sweep-only check for debt in files nobody is actively editing.
    "$SCRIPT_DIR/check_line_caps.sh" --quiet "${STAGED_PLANS[@]}" && echo "  ✅ Line caps (staged plans)" || { echo "  ❌ Line cap exceeded in a staged plan — split it (bash scripts/plan-hygiene/check_line_caps.sh <file> for detail)"; PF=$(( PF + 1 )); }
    # Finalize-plan coverage on staged plans ONLY (--only, ao_kpi_done_vs_detail_mismatch_2026_08_05
    # follow-up) — a brand-new assigned_vm:planning plan authored in a "pure doc/plan-flip -> prek
    # only" commit (CLAUDE.md's own carve-out) used to skip this check entirely, since it previously
    # lived ONLY in the full quality-gates.sh (repeat of the 2026-07-27
    # finalize_plan_coverage_regression incident, which blocked quickmerge fleet-wide until someone
    # noticed and authored the missing companions). --only still scans the whole corpus to resolve
    # gating but only fails on violations among these staged paths, so a pre-existing violation in an
    # unrelated plan never blocks this commit (RULE-11 blast-radius safety, same as frontmatter-schema
    # above).
    # Also enforces creation-time duplicate-gate idempotency (todo 1,
    # duplicate_finalize_plans_created_for_one_parent_2026_08_06.md): refuses a
    # staged finalize plan whose depends_on parent is already gated by a DIFFERENT
    # existing finalize plan, keyed on depends_on rather than filename shape.
    python3 "$SCRIPT_DIR/../quality_gates/check_finalize_plan_coverage.py" --workspace-root "$(dirname "$PM_DIR")" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Finalize-plan coverage (staged plans)" \
      || { echo "  ❌ Finalize-plan coverage — a staged assigned_vm:planning plan has no gated finalize companion, OR duplicates an existing finalize plan's parent (task_template.md §4, duplicate_finalize_plans_created_for_one_parent_2026_08_06.md)"; PF=$(( PF + 1 )); }

    # Evidence gates, --only-scoped (2026-08-09). These lived ONLY in the full quality-gates.sh,
    # so the CLAUDE.md-sanctioned pure-doc fast path (safe-doc-push.sh -> prek only) could land an
    # unsourced operator-ruling citation or an unresolvable <repo>@<sha> with nothing objecting.
    # The debt then surfaced for whichever OTHER agent next ran quickmerge, which re-gates the whole
    # tree — measured 2026-08-08/09: the ruling baseline went 58 -> 76 in a day, with the cost
    # landing on bystanders and one baseline RAISE absorbing 18 real violations rather than fixing
    # them. Author-pays, same blast-radius-safe --only shape as finalize-plan-coverage above.
    python3 "$SCRIPT_DIR/../quality_gates/check_plan_operator_ruling_evidence.py" --workspace-root "$(dirname "$PM_DIR")" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Operator-ruling evidence (staged plans)" \
      || { echo "  ❌ Operator-ruling evidence — a staged todo claims an 'operator ruling' with no traceable source doc"; PF=$(( PF + 1 )); }
    python3 "$SCRIPT_DIR/../quality_gates/check_plan_commit_sha_evidence.py" --workspace-root "$(dirname "$PM_DIR")" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Commit-SHA evidence (staged plans)" \
      || { echo "  ❌ Commit-SHA evidence — a staged todo cites <repo>@<sha> that does not resolve to a real commit"; PF=$(( PF + 1 )); }
    # Terminal-status-archived, --only-scoped (2026-08-07): a staged doc that's
    # status:resolved/complete/etc with all todos done but still physically under
    # plans/active/[issues/] is unconditionally wrong regardless of the corpus-wide
    # ratchet baseline below — no need to wait for the full sweep to catch a doc
    # THIS commit is creating/leaving unarchived. Same blast-radius-safe pattern as
    # finalize-plan-coverage above (--only, no baseline math, a pre-existing
    # unrelated violation elsewhere in the fleet never blocks this commit).
    python3 "$SCRIPT_DIR/check_terminal_status_archived.py" --quiet --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Terminal-status-archived (staged plans)" \
      || { echo "  ❌ A staged plan/issue doc is terminal-status but not archived — git mv it to plans/archive/[issues/] (see plan-completion-and-archival-discipline.md)"; PF=$(( PF + 1 )); }
    # Archive-candidates, --only-scoped (2026-08-09): same shape as operator-ruling-evidence above —
    # this check previously had NO precommit-time presence at all (only --ci mode's --diff-base and
    # the full corpus-wide baseline mode), so a docs(plans) commit flipping a doc's last open todo to
    # done had zero enforcement at commit time. Root-caused after the corpus-wide count reached 9
    # (baseline 0) entirely via commits that never ran this check — the LDR-red Tier-A synthetic
    # re-scan (baseline mode, not diff-scoped) is what eventually caught it, hours later, attributed
    # to whoever's unrelated commit happened to trigger the next full quality-gates.sh run. A staged
    # doc that's now 0-open/some-done/unlocked/not-exempt is unconditionally wrong regardless of the
    # corpus's pre-existing backlog — no baseline needed for a single-file check.
    bash "$SCRIPT_DIR/check_archive_candidates.sh" --quiet --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Archive candidates (staged plans)" \
      || { echo "  ❌ A staged plan/issue doc now has 0 open todos + some done, unlocked — archive it: flip status to a terminal value, add the archive banner, git mv to plans/archive/[issues/], fix corpus referrers (or set archive_exempt: true with a Progress Log reason if its 0-open-todos state is intentional/durable)"; PF=$(( PF + 1 )); }
    # Reference-path convention, --only-scoped (2026-08-09): same shape as the checks above — this
    # ratchet previously had NO precommit-time presence, only the full corpus-wide baseline mode, so
    # a docs(plans) commit introducing a badly-formatted or dangling /plans/…/codex/… reference had
    # zero enforcement at commit time. Root-caused after the existence-violation baseline grew 86->95
    # in one evening via commits that never ran this check. A staged file whose own content has a
    # bad-format or dangling reference is unconditionally wrong regardless of the rest of the
    # corpus's pre-existing debt.
    python3 "$SCRIPT_DIR/check_reference_paths.py" --quiet --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Reference-path convention (staged plans)" \
      || { echo "  ❌ A staged file has a badly-formatted or dangling /plans/…/codex/… reference — fix it (see codex/11-project-management/cross-reference-path-convention.md)"; PF=$(( PF + 1 )); }
    # Silent-default-effort, --only-scoped (2026-08-09): same shape as the checks above — this
    # ratchet previously had NO precommit-time presence, only the full corpus-wide baseline mode, so
    # a docs(plans) commit authoring a new living plan with assigned_role but no effort/
    # thinking_tier had zero enforcement at commit time. Root-caused after the baseline grew
    # 217->228 in under a day via commits that never ran this check. A newly-staged living plan with
    # assigned_role and no effort/thinking_tier signal is unconditionally flagged regardless of the
    # rest of the corpus's pre-existing population.
    python3 "$SCRIPT_DIR/check_effort_signal_ratchet.py" --quiet --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Silent-default-effort (staged plans)" \
      || { echo "  ❌ A newly-staged living plan declares assigned_role but no effort:/thinking_tier: — declare it explicitly, or confirm the role's default effort is genuinely right for this plan's complexity"; PF=$(( PF + 1 )); }
    # Todo regression, --only-scoped (2026-08-09): the module docstring's own precommit-exclusion
    # rationale ("NO origin fetch") describes a network call this check never actually makes — it
    # only reads the LOCAL origin/live-defi-rollout ref via `git show`, which is cheap and available
    # offline. Root-caused after a promote-PR full-QG run caught a plan that lost a todo hours after
    # it landed via safe-doc-push.sh, which never ran this check at all (unified-trading-pm PR #2670,
    # 2026-08-09) — same fast-path-blind-to-full-gate pattern as the checks above.
    bash "$SCRIPT_DIR/check_todo_regression.sh" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Todo regression (staged plans)" \
      || { echo "  ❌ A staged plan lost todos (total open+done shrank) vs origin/live-defi-rollout — restore the missing line(s), a checkbox flip never shrinks the total"; PF=$(( PF + 1 )); }
    # Stale base (2026-08-15): the check ABOVE counts todos, so it is blind to the
    # case measured that day — a staged edit that ADDED two todos while silently
    # dropping a peer's corrected prose blockquote. The count grew, so todo-regression
    # passed clean. Divergence-from-origin catches what counting cannot: if the file
    # changed upstream since your HEAD, your full-file edit cannot contain that change
    # and staging it overwrites with no conflict signal.
    bash "$SCRIPT_DIR/check_plan_stale_base.sh" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Stale base (staged plans)" \
      || { echo "  ❌ A staged plan was edited against a stale base — 'git pull --rebase --autostash', then verify BOTH your edit and the peer's survived"; PF=$(( PF + 1 )); }
    # Evidence-backed-completion, --only-scoped (2026-08-09): sub-rule B (a `- [x]` runtime-green
    # claim with no `Evidence: cloudbuild=<id>`) previously had NO precommit-time presence, only
    # the full corpus-wide baseline mode. Root-caused after a push to live-defi-rollout (sha
    # 42c50b4b3) blocked on this exact ratchet — a claim added via safe-doc-push.sh sailed through
    # clean and only surfaced on the next unrelated full CI run. Sub-rule A (Cloud Build API
    # verification) stays CI-only — needs gcloud/network/auth, incompatible with a <1s local hook.
    python3 "$SCRIPT_DIR/../quality_gates/check_evidence_backed_completion.py" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ Evidence-backed-completion (staged plans)" \
      || { echo "  ❌ A staged plan's '- [x]' runtime-green claim (build/deploy/promote) has no Evidence: cloudbuild=<id> — add the citation, or confirm this genuinely isn't a runtime claim"; PF=$(( PF + 1 )); }
    # Prosewrap-padding, --only-scoped (2026-08-09): this shrinking ratchet (baseline: corpus-wide
    # violation_count, 4472 lines at time of writing) previously had NO precommit-time presence,
    # only the full corpus-wide baseline mode — so a docs(plans) commit landing a NEW prettier
    # proseWrap corruption instance had zero enforcement at commit time and only surfaced hours/
    # days later on the next unrelated full quality-gates.sh run, misattributed to whichever
    # commit happened to trigger it. --only does NOT compare a staged file's total against the
    # corpus-wide baseline (a handful of staged-file violations would never approach 4472,
    # defeating the point) — it compares, per staged file, the SET of violation signatures
    # (detector-type + content, not line number) at current content vs `git show HEAD:<path>`,
    # flagging only what THIS commit introduces. Same HEAD-vs-current growth-ratchet shape as
    # check_effort_signal_ratchet.py --only above.
    # Accidental (undeclared) dispatch-exclusion gate, staged-files-only (2026-08-10). The
    # corpus-wide `check_ao_dispatch_visibility_gate.py` runs only in the FULL gate, so a plan
    # whose open todo is held by a marker buried mid-sentence lands via a docs(plans) push
    # unchallenged and fails later on an unrelated agent's QG run. Verdict comes from AO's own
    # module — no second copy of the marker rule — and a grep pre-filter keeps it free for the
    # ~3-in-4 plans that carry no marker at all. See the script header for the full rationale.
    bash "$SCRIPT_DIR/check_accidental_exclusions_only.sh" "${STAGED_PLANS[@]}" \
      && echo "  ✅ No new accidental dispatch-exclusions (staged plans)" \
      || PF=$(( PF + 1 ))

    # Unresolved evidence placeholder guard (2026-08-10). `<repo>@PENDING` is filled in by the
    # push that creates the commit (resolve_pending_citations in reconcile-sha-citations.sh), so
    # one surviving into a staged plan means the flip is being committed before, or without, the
    # ship it claims — exactly the false-progress the Commit+Push+Flip rule exists to prevent.
    # Cheap literal grep; no effect on any plan that does not use the convention.
    # Matching a bare `@PENDING` was the obvious implementation and it was WRONG: the first doc
    # it blocked was the issue doc DESCRIBING the convention, because prose necessarily writes
    # the literal `<repo>@PENDING` and the word PENDING. So match the CITATION GRAMMAR instead —
    # a real repo-name token immediately before `@PENDING`, which `<repo>@PENDING` cannot satisfy
    # (the `>` breaks the token) — and strip backtick spans first, so a documented example stays
    # documentable. Same backtick-stripping technique check_prosewrap_padding.sh's detectors use.
    # The array-length test is belt-and-braces: this block already sits inside a `-gt 0` guard,
    # but an awk/grep that word-splits to ZERO file arguments reads STDIN instead, which would
    # hang the pre-commit hook fleet-wide with no timeout to save it.
    if [ "${#STAGED_PLANS[@]}" -gt 0 ]; then
      _pending_hits="$(awk '
        { s = $0; gsub(/`[^`]*`/, "", s)
          if (s ~ /[a-z][a-z0-9-][a-z0-9-]+@PENDING/) print FILENAME ":" FNR ": " $0 }
      ' "${STAGED_PLANS[@]}" 2>/dev/null || true)"
      if [ -n "$_pending_hits" ]; then
        echo "  ❌ A staged plan still carries an unresolved '<repo>@PENDING' evidence placeholder:"
        printf '%s\n' "$_pending_hits" | sed 's/^/       /' | head -5
        echo "       PENDING is resolved by the quickmerge push that creates the commit. Ship the work first, then commit the flip — or replace it with the real sha."
        PF=$(( PF + 1 ))
      fi
    fi

    # AUTO-REPAIR, then re-verify (2026-08-10). Agents were hand-repairing this corruption on
    # every occurrence — a peer did so today — even though fix_prosewrap_padding.py already knew
    # the repair, because the fixer was whole-file scoped and unsafe to run unattended. Now that
    # `--only --emit-lines` can name exactly the lines THIS commit introduced, the repair is
    # scoped to those lines and can run here. The re-check is the gate: nothing passes because we
    # ran a fixer, only because the check agrees afterwards. Files are re-staged individually and
    # only if they were flagged, mirroring prettier-autostage.sh's contract.
    if bash "$SCRIPT_DIR/check_prosewrap_padding.sh" --only "${STAGED_PLANS[@]}"; then
      echo "  ✅ Prosewrap-padding (staged plans)"
    else
      _psw_scope="$(bash "$SCRIPT_DIR/check_prosewrap_padding.sh" --only --emit-lines "${STAGED_PLANS[@]}" 2>/dev/null || true)"
      if [ -n "$_psw_scope" ]; then
        printf '%s\n' "$_psw_scope" | python3 "$SCRIPT_DIR/fix_prosewrap_padding.py" --scoped || true
        if bash "$SCRIPT_DIR/check_prosewrap_padding.sh" --only "${STAGED_PLANS[@]}"; then
          _psw_n=0
          while IFS= read -r _psw_f; do
            [ -n "$_psw_f" ] || continue
            git -C "$PM_DIR" add -- "$_psw_f" 2>/dev/null && _psw_n=$(( _psw_n + 1 ))
          done < <(printf '%s\n' "$_psw_scope" | sed 's/:[0-9]*$//' | sort -u)
          echo "  ✅ Prosewrap-padding (staged plans) — auto-repaired and re-staged ${_psw_n} file(s); no hand-repair needed"
        else
          echo "  ❌ A staged plan has a NEW prettier proseWrap continuation-padding instance that the scoped auto-repair could not resolve — see plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the repair recipe"; PF=$(( PF + 1 ))
        fi
      else
        echo "  ❌ A staged plan has a NEW prettier proseWrap continuation-padding instance — see plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the repair recipe"; PF=$(( PF + 1 ))
      fi
    fi
    # depends_on DAG, --only-scoped (2026-08-09): the full-sweep cycle/self-dep check (below,
    # corpus-wide) previously had NO precommit-time presence, so a docs(plans) commit introducing
    # a cycle (depends_on gates archival — neither plan can ever close) had zero enforcement at
    # commit time. Unlike a single-file check, a cycle can SPAN two files (A depends_on B, B
    # depends_on A) where only one is staged — --only still builds the FULL corpus graph (cheap,
    # local reads only, ~750 docs) exactly like the full-sweep mode below, but reports a violation
    # only if it involves an edge ORIGINATING from a staged file (a self-dep, or a cycle with at
    # least one staged node) — catches "my edit introduced/is part of a cycle" without blocking on
    # a pre-existing cycle entirely among files this commit doesn't touch.
    python3 "$SCRIPT_DIR/check_depends_on_graph.py" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ depends_on DAG (staged plans)" \
      || { echo "  ❌ A staged plan's depends_on introduces a cycle or self-dependency — depends_on gates archival, so this would permanently stasis the plan(s) involved. Break the cycle: drop the weaker depends_on edge, or merge the plans."; PF=$(( PF + 1 )); }
    # AG-closeout linkage, --only-scoped (2026-08-09): this shrinking ratchet (baseline: 49
    # corpus-wide orphans at time of writing) previously had NO precommit-time presence, only the
    # full corpus-wide baseline mode. Cross-file like the depends_on check above (a doc's orphan
    # status depends on the related: graph, which can path through OTHER docs, and on the
    # closeout family's own body text — a DIFFERENT file) — --only builds the FULL corpus
    # graph/closeout-family/body-blob (cheap, local reads only), never a staged-only subgraph
    # (which could miss a real path through an unstaged intermediate doc). Per staged file: if it
    # is currently an orphan, was it ALSO an orphan when evaluated with its OWN `git show
    # HEAD:<path>` content (rest of today's corpus held fixed)? If yes, pre-existing debt in a
    # file this commit merely touches — skip. If this file's OWN content change (a dropped
    # related: link, a changed asset_group) newly created the orphan status, flag it.
    python3 "$SCRIPT_DIR/check_ag_closeout_linkage.py" --only "${STAGED_PLANS[@]}" \
      && echo "  ✅ AG-closeout linkage (staged plans)" \
      || { echo "  ❌ A staged single-asset-group plan/issue doc has no path (related: graph or closeout-doc mention) to its AG's consolidated closeout plan — add a related: link, or a mention in the closeout doc"; PF=$(( PF + 1 )); }
  fi
  if [ "${#STAGED_RUNBOOKS[@]}" -gt 0 ]; then
    python3 "$SCRIPT_DIR/check_runbook_fields.py" --quiet "${STAGED_RUNBOOKS[@]}" && echo "  ✅ Runbook fields (staged runbooks)" || { echo "  ❌ Runbook governance fields (staged runbooks)"; PF=$(( PF + 1 )); }
  fi
  if [ "${#STAGED_CODEX[@]}" -gt 0 ]; then
    # The SAME value-level schema gate CI's lint-codex slice runs over the WHOLE codex corpus,
    # scoped here to THIS commit's staged codex docs. Closes the prek bypass for codex/** (not just
    # plans/**): a docs commit (prek-only, NOT full QG) that adds/edits a codex doc with a
    # missing/empty required field (e.g. a codex-ssot lacking a present-but-empty `referenced_by`)
    # used to land on the integration branch and then fail EVERY full QG fleet-wide. SSOT:
    # check_frontmatter_schema.py (the exact checker the lint-codex slice invokes).
    python3 "$SCRIPT_DIR/check_frontmatter_schema.py" --quiet "${STAGED_CODEX[@]}" && echo "  ✅ Frontmatter schema (staged codex)" || { echo "  ❌ Frontmatter schema — missing/empty required field (staged codex)"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_conflict_markers.sh" --quiet "${STAGED_CODEX[@]}" && echo "  ✅ No conflict markers (staged codex)" || { echo "  ❌ Conflict marker(s) in staged codex — resolve before commit"; PF=$(( PF + 1 )); }
    "$SCRIPT_DIR/check_prettier_mangling.sh" --quiet "${STAGED_CODEX[@]}" && echo "  ✅ No prettier mangling (staged codex)" || { echo "  ❌ Prettier emphasis-mangling in staged codex — see plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md for the repair recipe"; PF=$(( PF + 1 )); }
    # Reference-path convention (staged codex) — check_reference_paths.py scans codex/** as well as
    # plans/**; same --only rationale as the plans-side call above.
    python3 "$SCRIPT_DIR/check_reference_paths.py" --quiet --only "${STAGED_CODEX[@]}" \
      && echo "  ✅ Reference-path convention (staged codex)" \
      || { echo "  ❌ A staged codex doc has a badly-formatted or dangling /plans/…/codex/… reference — fix it (see codex/11-project-management/cross-reference-path-convention.md)"; PF=$(( PF + 1 )); }
  fi
  if [ "$PF" -gt 0 ]; then
    echo "❌ plan-hygiene pre-commit: $PF hard failure(s) in STAGED files — fix before commit (fixable frontmatter: python3 scripts/plan-hygiene/fix_frontmatter.py; todo format: bash scripts/plan-hygiene/fix_todo_format.sh)."
    exit 1
  fi
  echo "✅ plan-hygiene pre-commit: staged files clean."
  exit 0
fi

HARD_FAIL=0
SOFT_WARN=0
RESULTS=()

# ── Diff-scoped ratchet base (2026-08-09, plan_hygiene_ratchet_regressions_outpace_serial_
# ci_fix_velocity_2026_08_09.md) ──
# Corpus-wide ambient ratchet checks (archive-candidates, reference-paths) attribute ANY
# concurrent agent's new violation — landing anywhere in the corpus between a worker's
# fix-push and the next CI re-run — to whoever happens to be re-triggering. On a
# high-churn branch this makes the checks un-convergeable serially (the issue doc above
# measured 4+ consecutive distinct-check regressions chasing one CI wall). Diff-scoped
# mode (`--diff-base <ref>`) fixes the shape: only a violation NEW at HEAD vs <ref> fails
# the gate; pre-existing corpus debt at <ref> is tolerated exactly like baseline mode.
# ONLY set DIFF_BASE_REF when the ref is actually resolvable locally — both checkers'
# diff-base mode is fail-UNSAFE on an unresolvable ref (git ls-tree/show against a
# missing ref returns nothing, so EVERY current violation reads as "new"), and
# `cron_hygiene_sweep_entrypoint.sh`'s shallow single-branch clone never fetches
# origin/main, so this guard is what keeps that periodic path on baseline mode instead of
# silently hard-failing on the corpus's entire pre-existing debt.
# PROMOTION PRs GET NO DIFF BASE AT ALL (2026-08-10). A promote PR's diff IS the entire
# LDR→main accumulation, so `--diff-base origin/main` there measures the whole unpromoted
# backlog rather than the change under test — and the further behind main falls, the more
# it measures, so the gate blocks the promote, main falls further behind, and the reported
# violation count GROWS. Measured on the NA-corpus check the same day: 51→53→55 new docs
# and 116→151→181 new todos across three runs on distinct HEADs while main went 1180→1440
# commits behind. A count that climbs across distinct HEADs is definitionally not a fixable
# regression, and no amount of retrying converges it.
#
# 4c964f8447 established this rule and the promote/ detection, scoped to the NA-corpus
# check. It is set HERE instead so the SAME rule covers every DIFF_BASE_REF consumer —
# reference-paths, archive-candidates and effort-ratchet carry the identical latent bug and
# were already tripping it (`check_reference_paths (--diff-base origin/main): 2 NEW
# violation(s)` hard-failed the 11:25Z promote-path run). Setting it once also avoids four
# copies of one rule, which is precisely the shape that rotted the tranche lists (see
# scripts/scheduled_job_already_ran.py's header). Falling back to baseline+buffer on the
# promote path is safe: every commit in that batch already passed these same checks
# diff-scoped on its way onto LDR, so re-gating the aggregate is double jeopardy.
#
# A WHOLE-BRANCH RUN AGAINST THE INTEGRATION BRANCH GETS NO DIFF BASE EITHER (2026-08-10).
# `cascade-qg-ordering.yml` (and `ldr-to-staging-promote.yml`) `workflow_dispatch` this gate
# directly at `live-defi-rollout` to answer "is LDR healthy?" — LDR has no push-triggered CI of
# its own. On a dispatch `GITHUB_HEAD_REF` is EMPTY (it is a PR-only variable), so the promote
# rule above cannot fire, and the diff once again spans the entire unpromoted backlog. Measured
# 2026-08-10: EIGHT such runs failed in one day (07:33/08:33/09:01/09:33/10:29/11:25/12:18/13:31Z),
# each paging #ci-failures CRITICAL, each reporting the same backlog-scale number
# (`61 new NA-population doc(s); 198 new open todo(s)`) that no commit under test caused.
# The cost is not just noise — it is MASKING. The 13:31Z run also carried a REAL hard failure
# (`No conflict markers (mid-line + mangled)` — genuine, transient corpus corruption, since
# resolved), and it was buried under a permanent false failure that fires every hour. An alert
# that always fires trains everyone to ignore the one time it means something.
# "Is this whole branch healthy?" is an ABSOLUTE question, so baseline+buffer is its correct
# shape; a diff base only makes sense when there is a specific change under test.
#
# NOT a blanket disable — a normal PR into main still gets full diff-scoping, which is where
# these checks actually catch a specific change's new violations.
DIFF_BASE_REF=""
if [ -n "$CI_MODE" ] \
  && [[ ! "${GITHUB_HEAD_REF-}" =~ ^promote/ ]] \
  && [ "${GITHUB_REF_NAME-}" != "live-defi-rollout" ] \
  && git -C "$PM_DIR" rev-parse --verify -q origin/main >/dev/null 2>&1; then
  DIFF_BASE_REF="origin/main"
fi

run_check() {
  local label="$1"
  local kind="$2"   # hard | soft
  shift 2
  local cmd=("$@")

  if "${cmd[@]}" --quiet 2>/dev/null; then
    RESULTS+=("  ✅ PASS  [$kind]  $label")
  else
    if [ "$kind" = "hard" ]; then
      RESULTS+=("  ❌ FAIL  [$kind]  $label")
      HARD_FAIL=$(( HARD_FAIL + 1 ))
    else
      RESULTS+=("  ⚠️  WARN  [$kind]  $label")
      SOFT_WARN=$(( SOFT_WARN + 1 ))
    fi
  fi
}

echo "========================================"
echo " Plan Hygiene Sweep — $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "========================================"
echo ""

run_check "Todo regression vs origin"       hard "$SCRIPT_DIR/check_todo_regression.sh"
run_check "Frontmatter validity"             hard "$SCRIPT_DIR/check_frontmatter.sh"
run_check "Todo format (priority + canonical)" hard "$SCRIPT_DIR/check_todo_format.sh"
run_check "Runbook governance fields"        hard python3 "$SCRIPT_DIR/check_runbook_fields.py"
run_check "No conflict markers (mid-line + mangled)" hard "$SCRIPT_DIR/check_conflict_markers.sh"
run_check "No prettier emphasis-mangling"    hard "$SCRIPT_DIR/check_prettier_mangling.sh"
# last_updated is a maintenance signal derived from the newest git commit. Keep this
# advisory in the full sweep: a staged edit cannot know its eventual commit date, so making
# it a pre-commit hard gate would create a false failure before the commit exists.
run_check "Fresh live-doc last_updated dates" soft python3 "$SCRIPT_DIR/check_last_updated.py"
# Prettier proseWrap continuation-padding gate — a DISTINCT prettier corruption class from the
# emphasis-mangling check above (non-idempotent reflow of a 2nd+ paragraph nested inside a list
# item; each reformat pass ADDS leading-space padding instead of converging). Corpus already
# carries real debt (found while root-causing 2026-08-03), so this is a shrinking ratchet like
# check_archive_candidates.sh below. Precommit protection is separate (the `--only` staged-file
# mode wired into the STAGED_PLANS block above); this is the full-corpus baseline/audit leg. SSOT
# + repro: plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md
#
# --diff-base wiring (2026-08-15): this checker gained a `--diff-base <ref>` mode on 2026-08-11
# (same signature-set-comparison shape as reference-paths/archive-candidates/effort-ratchet/
# na-corpus/ag-closeout below — see check_prosewrap_padding.sh's own header) but was never
# actually passed the shared DIFF_BASE_REF here, unlike its 5 siblings — found live while
# root-causing a 2026-08-15 promote-PR failure streak. Wiring it in only changes behavior on a
# "normal PR into main" CI run (DIFF_BASE_REF stays empty on promote/* heads and the
# live-defi-rollout dispatch by the same guard above, so promote-path behavior — and the
# 2026-08-15 failure streak specifically — is UNCHANGED by this: that streak was live, correctly-
# measured growing corpus debt at the time (2217->2324 violating lines against baseline 2011,
# confirmed against actual origin/live-defi-rollout tip, not a stale local snapshot), not a
# diff-scoping bug. See prosewrap_padding_corpus_wide_1290_space_2026_08_03.md's Progress Log.
PROSEWRAP_DIFF_ARGS=()
if [ -n "$DIFF_BASE_REF" ]; then
  PROSEWRAP_DIFF_ARGS=(--diff-base "$DIFF_BASE_REF")
fi
run_check "No prettier proseWrap continuation-padding (ratchet)" hard "$SCRIPT_DIR/check_prosewrap_padding.sh" "${PROSEWRAP_DIFF_ARGS[@]}"
# Broken relative links (plans/active/*.md -> a doc that moved to plans/archive/... without the
# referrer's path being updated) — the same check the --precommit fast path runs on any staged
# plans/ change, run here too so the operator's daily sweep catches drift from commits that landed
# before this gate existed. SSOT: validate_plan_links.py (also invoked fleet-wide by every repo's
# quality-gates.sh via run_validators.py — this is the LOCAL, fast-failure counterpart).
run_check "No broken links (plans/active/*.md, corpus-wide)" hard python3 "$SCRIPT_DIR/../validators/validate_plan_links.py"
# depends_on was SEEDED by fix_frontmatter.py but never VALIDATED — nothing checked the graph
# itself. A cycle (A->B->A) gates archival forever (CLAUDE.md: depends_on gates archival), so
# neither plan can ever close: silent permanent stasis, no error. Whole-graph check, so it lives
# in the full sweep, not the staged-files-only --precommit path. Corpus proven clean (0 cycles,
# 0 self-deps) before this was made hard. SSOT: check_depends_on_graph.py.
run_check "depends_on DAG (cycles + self-deps)" hard python3 "$SCRIPT_DIR/check_depends_on_graph.py" --quiet
# Reference path convention (/plans/... + /codex/... leading-slash, operator ruling
# 2026-07-23) — a shrinking-ratchet baseline (reference_paths_baseline.yaml), same shape
# as the fallback-import/DTZ ratchets: hard-fails only on a NEW violation above the
# pre-existing count, never on the corpus's existing debt. Supersedes check_codex_refs.sh's
# narrower existence-only scope (kept below for its standalone fast path).
# In CI-gate mode with a resolvable diff base (DIFF_BASE_REF above), run diff-scoped
# instead of baseline-scoped — closes the concurrent-commit race this check was one of the
# confirmed repeat offenders for. Baseline mode remains the fallback (periodic cron sweep,
# interactive/local runs) — no behavior change there.
REFPATH_DIFF_ARGS=()
if [ -n "$DIFF_BASE_REF" ]; then
  REFPATH_DIFF_ARGS=(--diff-base "$DIFF_BASE_REF")
fi
run_check "Reference path convention (/plans, /codex — ratchet)" hard python3 "$SCRIPT_DIR/check_reference_paths.py" "${REFPATH_DIFF_ARGS[@]}"
# AG-closeout linkage (operator request 2026-07-25) — every single-asset-group plan/issue
# doc must have a findable path (related: graph, either direction, or a body-text mention)
# to its AG's consolidated closeout plan, so a finding can never silently become an
# orphan nothing will ever pick up. Same shrinking-ratchet shape as the two checks above
# (ag_closeout_linkage_baseline.yaml): hard-fails only on a NEW orphan, never on debt.
# Uses the same DIFF_BASE_REF guard as reference-paths/na-corpus/effort-ratchet above
# (2026-08-14, extending the proven pattern per na_corpus_ratchet_diff_base_vs_lagging_main_
# deadlocks_promotion_2026_08_10.md's own todo — this check independently hit the identical
# lag-deadlock: a frozen-head "1 orphan (baseline 0)" that read as 0 orphans at LDR tip a
# minute later, transient corpus state no commit under test actually owned).
AGCLOSEOUT_DIFF_ARGS=()
if [ -n "$DIFF_BASE_REF" ]; then
  AGCLOSEOUT_DIFF_ARGS=(--diff-base "$DIFF_BASE_REF")
fi
run_check "AG-closeout linkage (single-AG docs -> consolidated closeout, ratchet)" hard python3 "$SCRIPT_DIR/check_ag_closeout_linkage.py" "${AGCLOSEOUT_DIFF_ARGS[@]}"
# Artefact disclosure + enum-drift (client_artefact_remediation_2026_08_18.md § E,
# operator ruling 2026-08-18) -- the six client-facing presentation artefacts under
# codex/14-customer-journeys/commercial-model/*.html were never checked by anything:
# the banned-client-name stop-ship in strategy-service-deep-dive.html was found only
# because an audit was commissioned, and the two P0 enum drifts (StrategyFamily,
# StrategyInstructionEnvelope) were hand-transcribed wrong independently of the SSOT.
# Disclosure's HARD class (banned name / maturity-label leak / internal route leak) has
# no baseline -- any hit fails, always; its WARN class (performance-figure patterns) and
# the enum-drift check are both shrinking ratchets, same shape as reference-paths above.
# NOTE: disclosure's hard class is currently RED (6 pre-existing ClearLoop hits in
# strategy-service-deep-dive.html) -- tracked and owned by
# client_artefact_remediation_siblings_2026_08_18.md, not a regression from this wiring.
run_check "Artefact disclosure (banned terms, ratchet)" hard python3 "$SCRIPT_DIR/check_artefact_disclosure.py"
run_check "Artefact enum drift (vs UAC, ratchet)" hard python3 "$SCRIPT_DIR/check_artefact_enum_drift.py"
# Claim ownership + marker counts — the acceptance test for the five-agent code-readiness
# effort (code_readiness_five_agent_coordinator_2026_08_19.md). Two shrinking ratchets
# (untagged claim-bearing sections; open st-part/st-plan/ev-check/ev-assumed markers) plus
# a HARD, un-baselined owner-resolution check. Seeded 2026-08-20 at the measured state
# (37 untagged / 189 open markers) — those numbers only ever go DOWN, and only by changing
# real state, never by editing an artefact's markup.
run_check "Artefact claim ownership + marker counts (ratchet)" hard python3 "$SCRIPT_DIR/check_artefact_claim_ownership.py"
# Terminal-status-archived (operator finding 2026-07-25) — no plan/issue doc with a TERMINAL
# status (issue: resolved/false-positive/superseded; plan: complete/superseded/cancelled) may
# sit in plans/active/ or plans/active/issues/ instead of plans/archive/ — this is
# codex/11-project-management/issue-doc-lifecycle.md's archive-on-resolve rule, now
# machine-enforced after its manual audit recipe was found to be silently dead (grepped a
# frontmatter field the schema no longer has). Same shrinking-ratchet shape as the two checks
# above (terminal_status_archived_baseline.yaml): hard-fails only on a NEW unarchived
# terminal-status doc, never on the pre-existing backlog being cleared by
# terminal_status_archival_backlog_sweep_2026_07_25.md.
run_check "Terminal-status-archived (plan/issue docs -> plans/archive/, ratchet)" hard python3 "$SCRIPT_DIR/check_terminal_status_archived.py" --quiet
# Create-only archival-commit guard (issue 2026-08-06) — `git commit --only -- <new-path>` after a
# `git mv` commits the ADD side of a rename but silently EXCLUDES the DELETE side, leaving a live
# plans/active/issues/<stem>.md twin next to the archive copy that then diverges. This ABSOLUTE check
# hard-fails on ANY plans/archive/issues/*.md whose active twin also exists in the same tree (the 5
# known live pairs + any new create-only residue). Distinct from the terminal-status ratchet above
# (that only catches unarchived terminal docs; this catches the twin that the create-only commit
# leaves behind). The 5 current pairs are reconciled by the issue doc's P2 todo; never lower this to
# advisory to make the sweep pass.
run_check "Create-only archival guard (archive/active duplicate pairs)" hard python3 "$SCRIPT_DIR/check_create_only_archive_commits.py" --quiet
# Duplicate-gated finalize plans (todo 2, duplicate_finalize_plans_created_for_one_parent_2026_08_06.md) —
# a corpus-wide sweep of the SAME `depends_on`-keyed collision todo 1's creation-time precommit guard
# already catches for a newly-staged finalize plan (check_finalize_plan_coverage.py's --only mode). This
# is the standing at-rest detector: any parent slug named in the depends_on of MORE THAN ONE
# gate_on_depends: true plan, regardless of when either was created. SHRINKING-RATCHET baseline (not
# absolute): a live 2026-08-15 scan found 6 pre-existing duplicates todo 3 has not yet de-raced, so
# hard-failing unconditionally would red the fleet on debt this check did not create — same
# "the gate must be one the whole fleet already passes" shape as the archival guard directly above.
run_check "Duplicate-gated finalize plans (parent gated by >1 finalize plan)" hard python3 "$SCRIPT_DIR/check_duplicate_gated_finalize_plans.py" --quiet
# assigned_vm:NA corpus size ratchet (operator directive 2026-07-27) — the NA backlog (doc count +
# open-todo count over assigned_vm:NA + status in {active,open}) must not grow unattended. Most NA
# content is genuinely operator-gated/judgment work and correctly stays NA — the point is not to
# drive it to zero, it's that new NA content must be offset by /na-eligibility-audit (or manual
# triage) reclassifying/archiving existing NA content, not just piling up forever unreviewed. Same
# shrinking-ratchet shape as the three checks above (na_corpus_baseline.yaml): hard-fails only when
# the CURRENT count exceeds the baseline on either axis. SSOT:
# codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 4.
# Uses the same DIFF_BASE_REF guard as the reference-path/archive-candidates checks above
# (2026-08-09, plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md) —
# diff-scoped in CI-gate mode with a resolvable base, baseline+buffer mode otherwise (periodic
# cron sweep, interactive/local runs unchanged).
NACORPUS_DIFF_ARGS=()
# Promotion PRs (LDR→main) carry the entire LDR accumulation as their diff, which
# will always include legitimate new NA docs/todos from normal work.  `--diff-base
# origin/main` on a promotion PR is therefore structually fail-unsafe: it catches
# ALL growth, not just unattended growth, and the check becomes un-convergeable on
# the promote path.  Use baseline+buffer mode instead (the same mode the periodic
# cron sweep and interactive/local runs already use), which tolerates routine
# accumulation within the buffer while still catching a genuine spike.
# Detect promotion PRs via GITHUB_HEAD_REF (e.g. "promote/unified-trading-pm/4840cdac0125").
if [ -n "$DIFF_BASE_REF" ] && [[ ! "${GITHUB_HEAD_REF-}" =~ ^promote/ ]]; then
  NACORPUS_DIFF_ARGS=(--diff-base "$DIFF_BASE_REF")
fi
run_check "assigned_vm:NA corpus size (docs + open todos, ratchet)" hard python3 "$SCRIPT_DIR/check_na_corpus_ratchet.py" "${NACORPUS_DIFF_ARGS[@]}"
# Line caps (plans 500 soft/1000 hard; epics 2000 hard flat, NO umbrella-exemption escape hatch —
# operator ruling 2026-07-24) — flipped from advisory to a real hard gate 2026-07-24 via the SAME
# shrinking-ratchet shape as the reference-path check above (line_caps_baseline.yaml): hard-fails
# only on a NEW over-cap plan/epic (or an existing one getting worse) above the pre-existing count,
# never on the debt plan_line_cap_remediation_2026_07_23.md didn't finish cleaning up. Lower the
# baseline as each remaining flagged plan/epic is split/trimmed; it should reach 0.
run_check "Line caps (plans 500/1000, epics 2000 — no exemption, ratchet)" hard "$SCRIPT_DIR/check_line_caps.sh" --quiet
run_check "Estimate sanity (±20% drift)"     soft "$SCRIPT_DIR/check_estimate_sanity.sh"
# Silent-default-effort ratchet (2026-08-05 follow-up to the AO dashboard effort/
# affinity/blocked-reason visibility work) — a living plan that sets assigned_role but
# declares neither effort: nor thinking_tier: resolves its reasoning-effort tier to
# whatever the role's generic default is (often model_tier.py's hardcoded "medium")
# with nobody having deliberately chosen that for THIS plan. Same shrinking-ratchet
# shape as the hard ratchets above (effort_signal_baseline.yaml): hard-fails only when
# the CURRENT count exceeds the baseline, never on the pre-existing 211-plan debt.
# Uses the same DIFF_BASE_REF guard as the checks above (2026-08-09,
# plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md) — diff-scoped
# in CI-gate mode with a resolvable base, baseline mode otherwise.
EFFORT_DIFF_ARGS=()
if [ -n "$DIFF_BASE_REF" ]; then
  EFFORT_DIFF_ARGS=(--diff-base "$DIFF_BASE_REF")
fi
run_check "Silent-default-effort plans (ratchet)" hard python3 "$SCRIPT_DIR/check_effort_signal_ratchet.py" "${EFFORT_DIFF_ARGS[@]}"
run_check "Superseded plans in active/"      soft "$SCRIPT_DIR/check_superseded_in_active.sh"
run_check "Codex path refs resolve (legacy, subset of the ratchet check above)" soft "$SCRIPT_DIR/check_codex_refs.sh"
run_check "Parent-epic alignment (keyword)"  soft python3 "$SCRIPT_DIR/check_parent_epic_alignment.py"
run_check "CLAUDE↔SUB_AGENT topic parity"    soft "$SCRIPT_DIR/check_claude_subagent_parity.sh"
# Delete/VM-launch todo tagging (task_template.md §3 finding O, 2026-07-25) — mechanical candidate
# signal only, feeds /plan-reconcile's AO-dispatch-readiness hunter for real judgment; soft because
# a regex cannot decide whether a self-justification is actually sound.
run_check "Delete/VM-launch todo tagging (AO plans, candidate signal)" soft "$SCRIPT_DIR/check_delete_vm_launch_gating.sh"
# Uncited-symbol todo candidate signal (tool_call_batching_authoring_gap_2026_08_14) — a todo
# citing no backtick-quoted symbol/file/table likely forces an exploratory Read/Grep before any
# edit is possible; feeds /plan-reconcile hunter 5's specificity sub-check. Soft/advisory: a
# backtick-presence regex cannot judge whether a todo genuinely has nothing to cite yet.
run_check "Uncited-symbol todo (candidate signal)" soft "$SCRIPT_DIR/check_todo_specificity.sh"
# Priority vs. tier policy (operator ruling 2026-07-28, plan_priority_policy_qg_validation_2026_07_28.md) —
# flags a bare sports/tradfi-tagged doc sitting at P0/P1 with no title/frontmatter signal of
# backfill-completion-critical work, per plan-priority-tier-and-dispatch-ordering.md. Soft/advisory:
# a keyword heuristic can only surface a re-triage candidate, never decide the judgment call itself.
run_check "Priority vs. asset-group tier policy (candidate signal)" soft python3 "$SCRIPT_DIR/check_priority_tier_policy.py"

# Archive candidates (operator finding 2026-07-29) — a done-but-unarchived plan/issue doc (0 open
# todos, unlocked, status never flipped to terminal) is DISTINCT from check_terminal_status_
# archived.py above (which only catches a doc whose status ALREADY says resolved/complete). This
# was purely informational (`|| true`) until now — the recurring gap CLAUDE.md's archival rule
# calls out ("MUST be archived immediately (HARD RULE, recurring gap)") had nothing actually
# enforcing it. Same shrinking-ratchet shape as the checks above (archive_candidates_baseline.yaml).
#
# In CI mode (promote path), pass --diff-base origin/main so the check is DIFF-SCOPED: only a
# candidate NEW since origin/main (i.e. introduced by this promote PR's diff) fails the gate;
# pre-existing corpus debt at origin/main is tolerated. Operator ruling 2026-08-06 —
# /plans/active/issues/archive_candidates_content_verification_backlog_2026_08_06.md.
# Uses the same DIFF_BASE_REF guard as the reference-path check above (2026-08-09 fix) —
# was previously gated on bare `[ -n "$CI_MODE" ]`, which also fires for
# cron_hygiene_sweep_entrypoint.sh's periodic sweep. That entrypoint does a shallow
# single-branch clone with no origin/main fetch, so --diff-base origin/main against an
# unresolvable ref degraded to "every current candidate is new" (fail-unsafe, not the
# intended baseline-tolerant behavior) — this was a live latent bug in the 2026-08-06 fix,
# just never triggered because the periodic sweep already tolerates hard failures
# (exit 0 always, Slack-only).
ARCHIVE_DIFF_ARGS=()
if [ -n "$DIFF_BASE_REF" ]; then
  ARCHIVE_DIFF_ARGS=(--diff-base "$DIFF_BASE_REF")
fi
run_check "Archive candidates (0 open todos, unlocked -> plans/archive/, ratchet)" hard "$SCRIPT_DIR/check_archive_candidates.sh" "${ARCHIVE_DIFF_ARGS[@]}"

# Model-tier coverage is informational — surfaces opus-candidates + plans on the
# silent Sonnet default for human review (SSOT: codex/06-coding-standards/model-tier-selection.md).
echo ""
echo "--- Model-tier coverage (advisory) ---"
cd "$PM_DIR" && python3 scripts/plans/audit_model_tier.py 2>&1 \
  | grep -E "active plans:|declare model_tier:|opus-candidates:|mismatch:|⬅ OPUS" || true

echo ""
echo "--- Results ---"
for r in "${RESULTS[@]}"; do
  echo "$r"
done

echo ""
echo "--- Inventory regenerator ---"
if [ -n "$NO_REGEN" ]; then
  echo "  ⏭  skipped (--no-regen)"
else
  cd "$PM_DIR" && python3 scripts/plans/regenerate_active_plan_inventory.py 2>&1 | tail -5 || echo "⚠️ regenerator failed"
fi

echo ""
echo "--- Domain index regenerator (plans/active/INDEX.md) ---"
if [ -n "$NO_REGEN" ]; then
  echo "  ⏭  skipped (--no-regen)"
else
  cd "$PM_DIR" && python3 scripts/plans/regenerate_active_plan_index.py 2>&1 | tail -5 || echo "⚠️ regenerator failed"
fi

echo ""
echo "========================================"
echo " Hard failures: $HARD_FAIL  |  Soft warnings: $SOFT_WARN"
echo "========================================"

if [ "$CI_MODE" = "--ci" ] && [ "$HARD_FAIL" -gt 0 ]; then
  echo ""
  echo "❌ Sweep FAILED — fix hard failures before proceeding."
  exit 1
fi

if [ "$HARD_FAIL" -gt 0 ]; then
  echo ""
  echo "⚠️  Fix hard failures before picking up new work."
fi

exit 0
