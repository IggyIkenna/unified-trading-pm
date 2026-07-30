## Summary

When the stash restore conflicts, the rollback restores from the **current index** rather than the pre-hook state. If a
hook has re-staged its own output, the index has already moved, so the saved patch gets applied on top of the hook's
content and the user's unstaged changes are silently lost.

This is the general case behind #1889. That issue was closed because the reported scenario couldn't be reproduced from
the description — this PR includes a minimal deterministic reproduction as a test.

## The mechanism

`UnstagedChangesRestorer::restore` falls back to `checkout_working_tree` when `git apply` fails, intending to discard
the hook's changes and retry:

```rust
// Discard any changes made by hooks, and try applying the patch again.
Self::checkout_working_tree(&self.root)?;
Self::git_apply(patch)?;
```

`checkout_working_tree` runs `git checkout -- <root>` with no tree-ish, so it restores from the index. That's correct
only while the index still holds the pre-hook state.

Auto-fixing hooks commonly break that assumption: they run a formatter and then `git add` the result, so the commit
completes in one step instead of aborting for a manual re-stage. Once such a hook runs, the index holds the hook's
content. The rollback then reinstates _that_ as the baseline, and the patch — computed against the original content — is
applied on top of it. It either fails outright or lands on the wrong lines. Either way the unstaged work is gone, and
`git status` is clean afterwards, so nothing signals it.

## The fix

`clean` already computes the pre-hook tree with `git write-tree` and then discards it. This keeps it and passes it to
the rollback checkout, so `git checkout <tree> -- <root>` restores both the index entries and the working tree to their
true pre-hook state before the patch is re-applied.

The happy path is unchanged — the initial `clean` checkout still passes `None`, since the tree was just written from the
index and the two are identical at that point. Only the conflict path differs, and it gains one argv element on a
command that runs only after a conflict has already occurred.

## Reproduction

`restaging_hook_does_not_discard_unstaged_changes` in `crates/prek/tests/run.rs`. A hook rewrites a file and `git add`s
it; the same file has both a staged edit and a further unstaged edit.

On master:

```
  left: "NORMALISED\nbody\nstaged edit\n"
 right: "ORIGINAL\nbody\nstaged edit\nUNSTAGED TAIL\n"
```

The unstaged tail is gone and the hook's content has replaced the user's. With the fix, the working tree comes back
exactly as the user left it and the file is still reported dirty.

## Checks

- New test fails on master, passes with the change.
- `staged_files_only`, `intent_to_add_file_survives_conflicted_stash_restore`, `restore_on_interrupt`, and
  `all_files_with_existing_unstaged_changes_uses_snapshot_baseline` all still pass.
- Remaining failures in a full local `cargo test` run are language-toolchain tests (conda, dart, haskell, julia, lua,
  perl, php, r, ruby) that need toolchains not installed on this machine; they fail identically on an unmodified
  checkout.

Happy to adjust the approach if you'd prefer the index restored a different way.
