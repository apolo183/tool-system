# P8 Milestone Review Evidence

repo_rel_path: docs/reports/p8_milestone_review_evidence.md  
role: milestone review evidence record  
purpose: summarize P8 evidence, rollback references, claim boundaries, and remaining review decisions  
status: P8_REVIEW_REQUIRED  
phase: P8_MULTI_AGENT_RUNTIME  
created_at: 2026-07-09 UTC+08:00

## 1. Review disposition

User disposition: P8 is not accepted yet. Before P9, supplement P8 closeout evidence, audit report, and rollback proof.

This document is evidence for milestone review. It does not close P8, approve P9, approve production deployment, approve target-repository mutation, or claim Codex replacement.

## 2. Current repository state

- Repository: apolo183/tool-system.
- Default branch: main.
- Current main evidence head: 0ad283cf9405efc944cc95a43f114e014e035654.
- Recent P8 commits:
  - 743ea1f775c1520b8ae0870e1cbc59f8c601c57d — P8A runtime phase entry (#46).
  - 3de1b7381ce4da5c97647e88c15affb9dedd021c — P8B role runtime foundation (#47).
  - f6aa4dadd2e3e915de8d0a9e2896feb8339a0d33 — P8C no-mutation agent worker interface (#49).
  - 5aaccfeea903e820347d325b2166ffff40da60e8 — P8D runtime audit bundle (#50).
  - 0ad283cf9405efc944cc95a43f114e014e035654 — P8E role transition gate (#51).

## 3. P8 output evidence map

| P8 output | Evidence artifact | Status |
|---|---|---|
| role step runtime contract | src/tool_system/runtime/role_runtime.py | Implemented |
| no-mutation role execution records | src/tool_system/runtime/role_runtime.py; src/tool_system/agent_worker/interface.py | Implemented |
| agent worker interface | src/tool_system/agent_worker/interface.py | Implemented |
| runtime audit bundle | src/tool_system/runtime/audit_bundle.py | Implemented |
| rollback reference bundle | src/tool_system/runtime/audit_bundle.py | Implemented |
| role transition gate | src/tool_system/runtime/transition_gate.py | Implemented |
| active gate registration | examples/active_gates.yaml | Implemented |
| focused tests | tests/test_role_runtime.py; tests/test_agent_worker_interface.py; tests/test_runtime_audit_bundle.py; tests/test_role_transition_gate.py | Implemented |

## 4. CI evidence

| PR | Head / merge evidence | Workflow evidence | Status |
|---|---|---|---|
| #49 P8C | f6aa4dadd2e3e915de8d0a9e2896feb8339a0d33 | tool-system-ci run 29015484755; verify job 86109313116 | PASS |
| #50 P8D | 5aaccfeea903e820347d325b2166ffff40da60e8 | tool-system-ci run 29017114441 | PASS |
| #51 P8E | 0ad283cf9405efc944cc95a43f114e014e035654 | tool-system-ci run 29017304117; verify job 86115373836 | PASS |

Unverified in this report:

- Local DGX `git status`, `git diff`, and local test run were not executed in this evidence record.
- P8A and P8B CI/job logs are not re-cited in this evidence record.

## 5. Boundary evidence

P8 remains a no-mutation runtime phase:

- No downstream target-repository mutation is approved by this record.
- No production deployment is approved by this record.
- No destructive cleanup is approved by this record.
- No Codex replacement claim is approved by this record.
- No milestone closure is approved by this record.

The role transition gate is expected to stop at `P8_MILESTONE_REVIEW` and returns no execution authority.

## 6. Rollback reference bundle

Rollback is not executed by this record. The rollback evidence is a concrete commit reference plan for reverting P8 changes if review rejects P8.

Rollback target commits, newest first:

```text
0ad283cf9405efc944cc95a43f114e014e035654  P8E role transition gate (#51)
5aaccfeea903e820347d325b2166ffff40da60e8  P8D runtime audit bundle (#50)
f6aa4dadd2e3e915de8d0a9e2896feb8339a0d33  P8C no-mutation agent worker interface (#49)
3de1b7381ce4da5c97647e88c15affb9dedd021c  P8B role runtime foundation (#47)
743ea1f775c1520b8ae0870e1cbc59f8c601c57d  P8A runtime phase entry (#46)
```

Read-only rollback planning command:

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout main
git status -sb --untracked-files=all
git log --oneline -8
```

Rollback rehearsal command, must use a throwaway branch and must not be pushed unless separately approved:

```bash
cd /home/rich/projects/tool-system
git fetch origin
git checkout -B p8-rollback-rehearsal origin/main
git revert --no-commit \
  0ad283cf9405efc944cc95a43f114e014e035654 \
  5aaccfeea903e820347d325b2166ffff40da60e8 \
  f6aa4dadd2e3e915de8d0a9e2896feb8339a0d33 \
  3de1b7381ce4da5c97647e88c15affb9dedd021c \
  743ea1f775c1520b8ae0870e1cbc59f8c601c57d
git diff --stat
git revert --abort
```

Rollback execution requires separate approval and should be done through a PR, not direct main mutation.

## 7. Review questions for process and direction

The reviewer does not need to inspect source code. The reviewer should decide:

1. Does P8 correctly remain a no-mutation multi-agent runtime layer?
2. Does tool-system still remain domain-agnostic infrastructure rather than finance/trading business logic?
3. Is the role transition gate acceptable as the stop point before P8 acceptance?
4. Is the rollback reference bundle sufficient, or must a DGX rollback rehearsal be executed before P8 acceptance?
5. If P8 is accepted later, what is P9: worker adapter, runtime orchestration, closeout hardening, or target-repo execution preparation?

## 8. Current recommendation

Process-conservative recommendation: keep P8 in `P8_REVIEW_REQUIRED` until DGX local status/diff and rollback rehearsal evidence are captured.

Fast-forward recommendation: accept P8 after this report and green CI are reviewed, but continue to prohibit downstream target-repository mutation and production deployment until separate explicit approval.
