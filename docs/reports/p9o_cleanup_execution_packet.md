# P9O Cleanup Execution Packet

repo_rel_path: docs/reports/p9o_cleanup_execution_packet.md  
role: cleanup execution packet and review gate  
purpose: define exact local cleanup commands for verified accidental remote branch residue without executing deletion in this PR  
status: READY_FOR_LOCAL_EXECUTION_AFTER_FINAL_READONLY_CHECK  
phase: P9_WORKER_ADAPTER_ORCHESTRATION  
created_at: 2026-07-10 UTC+08:00

## 1. Disposition

P9O prepares a cleanup execution packet after the user explicitly chose not to accept P9 and requested continued review/cleanup.

This record does not itself delete branches, accept P9, close P9, approve P10, approve downstream target-repository mutation, approve production deployment, execute rollback, or claim Codex replacement.

## 2. Parent and global alignment

Parent document:

```text
docs/reports/p9k_cleanup_readonly_verification.md
```

Parent alignment: P9K verified accidental cleanup candidates using read-only comparisons and found `ahead_by = 0` for the listed residue candidates.

Global blueprint alignment:

```text
blueprint/tool_system_v0.yaml :: milestones.P9_WORKER_ADAPTER_ORCHESTRATION
```

Global alignment: P9O remains within P9 governance, review, rollback, cleanup planning, and no-mutation boundaries. It does not authorize downstream target-repository mutation or production deployment.

## 3. Cleanup candidates from verified residue

Primary cleanup candidates from P9K:

```text
p9f-dgx-local-evidence2
p9f-dgx-local-evidence3
p9f-dgx-local-evidence4
p9f-dgx-local-evidence5
p9f-dgx-local-evidence6
p9f-dgx-local-evidence7
p9f-dgx-local-evidence8
p9g-rollback-rehearsal-evidence
p9g-rollback-rehearsal-evidence2
p9g-rollback-rehearsal-evidence3
p9g-rollback-rehearsal-evidence4
p9g-rollback-rehearsal-evidence5
p9g-rollback-rehearsal-evidence6
```

Additional superseded residue observed in the DGX fetch output after P9M:

```text
p9m-blueprint-alignment-gate
```

This branch was a stopped duplicate implementation path after P9M alignment gate enforcement was already merged. It must be rechecked before deletion because it was not part of the P9K compare table.

## 4. Final read-only check before deletion

Run from the local tool-system checkout:

```bash
cd /home/rich/projects/tool-system
git fetch origin
for branch in \
  p9f-dgx-local-evidence2 \
  p9f-dgx-local-evidence3 \
  p9f-dgx-local-evidence4 \
  p9f-dgx-local-evidence5 \
  p9f-dgx-local-evidence6 \
  p9f-dgx-local-evidence7 \
  p9f-dgx-local-evidence8 \
  p9g-rollback-rehearsal-evidence \
  p9g-rollback-rehearsal-evidence2 \
  p9g-rollback-rehearsal-evidence3 \
  p9g-rollback-rehearsal-evidence4 \
  p9g-rollback-rehearsal-evidence5 \
  p9g-rollback-rehearsal-evidence6 \
  p9m-blueprint-alignment-gate
  do
    echo "== $branch =="
    git ls-remote --heads origin "$branch"
    git log --oneline "origin/main..origin/$branch" || true
  done
```

Eligible deletion condition:

- branch exists on origin;
- `git log --oneline origin/main..origin/<branch>` prints no commits;
- branch is not `main`;
- branch is not the active working branch;
- branch is not referenced by an open PR;
- branch is not protected.

## 5. Local cleanup command

Only after the final read-only check passes for a branch, delete that branch from origin:

```bash
cd /home/rich/projects/tool-system
git push origin --delete \
  p9f-dgx-local-evidence2 \
  p9f-dgx-local-evidence3 \
  p9f-dgx-local-evidence4 \
  p9f-dgx-local-evidence5 \
  p9f-dgx-local-evidence6 \
  p9f-dgx-local-evidence7 \
  p9f-dgx-local-evidence8 \
  p9g-rollback-rehearsal-evidence \
  p9g-rollback-rehearsal-evidence2 \
  p9g-rollback-rehearsal-evidence3 \
  p9g-rollback-rehearsal-evidence4 \
  p9g-rollback-rehearsal-evidence5 \
  p9g-rollback-rehearsal-evidence6 \
  p9m-blueprint-alignment-gate
```

If any branch no longer exists, omit it from the command and record that it was already absent.

## 6. Post-cleanup verification

After deletion, verify:

```bash
cd /home/rich/projects/tool-system
git fetch origin --prune
for branch in \
  p9f-dgx-local-evidence2 \
  p9f-dgx-local-evidence3 \
  p9f-dgx-local-evidence4 \
  p9f-dgx-local-evidence5 \
  p9f-dgx-local-evidence6 \
  p9f-dgx-local-evidence7 \
  p9f-dgx-local-evidence8 \
  p9g-rollback-rehearsal-evidence \
  p9g-rollback-rehearsal-evidence2 \
  p9g-rollback-rehearsal-evidence3 \
  p9g-rollback-rehearsal-evidence4 \
  p9g-rollback-rehearsal-evidence5 \
  p9g-rollback-rehearsal-evidence6 \
  p9m-blueprint-alignment-gate
  do
    git ls-remote --heads origin "$branch"
  done
git status -sb --untracked-files=all
```

Expected outcome:

- deleted branches no longer appear in `git ls-remote --heads` output;
- `main` remains clean;
- no file changes are made by cleanup.

## 7. Rollback note

Remote branch deletion is not a normal file rollback. If a branch was deleted by mistake and its SHA is known, recreate it with:

```bash
git push origin <sha>:refs/heads/<branch>
```

Therefore the final read-only check must record each branch SHA before deletion.

## 8. Boundary

P9O grants no P9 acceptance, P10 entry, downstream target-repository mutation, production deployment, real external worker call, or business-domain implementation authority.
