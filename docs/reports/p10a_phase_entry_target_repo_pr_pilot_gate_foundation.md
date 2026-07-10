# P10A Phase Entry: Target-Repo PR Pilot Gate Foundation

repo_rel_path: docs/reports/p10a_phase_entry_target_repo_pr_pilot_gate_foundation.md  
role: P10 phase-entry and gate-foundation record  
purpose: establish the first bounded P10 control stage for a controlled target-repository pull-request pilot  
status: P10_PHASE_ENTRY_GATE_FOUNDATION_READY  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-10 UTC+08:00

## 1. Disposition

P10A starts the approved P10 boundary after P9 acceptance and P10 boundary approval.

This record does not select a target repository, mutate any downstream repository, open a downstream pull request, execute rollback, deploy to production, implement business-domain logic, call a real external worker, or claim Codex replacement.

P10A only establishes the control surface for later P10 pilot work.

## 2. Parent and global alignment

Parent document:

```text
docs/reports/p9u_p9_acceptance_p10_boundary.md
```

Parent alignment: P9U accepted P9 and approved the P10 boundary named `P10_CONTROLLED_TARGET_REPO_PR_PILOT`, while preserving the requirement that real target-repository writes need separate named execution approval.

Global blueprint alignment:

```text
blueprint/tool_system_v0.yaml :: milestones.P10_CONTROLLED_TARGET_REPO_PR_PILOT
```

Global alignment: P10A remains inside the P10 milestone by establishing phase-entry controls, target-repo selection gates, execution-approval packet requirements, and no-production PR pilot boundaries.

## 3. P10A objective

P10A creates the first P10 gate foundation:

```text
P10A_PHASE_ENTRY_TARGET_REPO_PR_PILOT_GATE_FOUNDATION
```

Objective:

```text
Define the control requirements for selecting a target repository, preparing a target-repo execution approval packet, previewing downstream branch/PR commands, and recording rollback/audit evidence before any real downstream write is allowed.
```

## 4. Target-repo selection gate

A later P10 target-repo candidate selection record must be read-only and must identify:

- candidate repository full name;
- current default branch;
- current head SHA;
- relevant governance files or manifests in that repository;
- why the repository is inside the approved P10 pilot boundary;
- explicit no-production boundary;
- explicit business-domain non-ownership boundary;
- stop condition if the repository is ambiguous, dirty, protected, or outside the pilot boundary.

Selection evidence alone does not approve writes.

## 5. Execution approval packet requirements

Before any real target-repository branch or PR mutation, a separate execution approval packet must name at minimum:

- target repository;
- target branch;
- base branch and base SHA;
- exact allowed file paths or globs;
- explicit forbidden file paths or globs;
- intended diff summary;
- validation commands;
- rollback command or reference;
- post-action verification;
- stop condition;
- proof that the action remains inside P10 and outside production deployment.

If any field is missing or ambiguous, work stops before downstream mutation.

## 6. Command preview boundary

P10A allows dry-run or preview commands for future target-repo work. Preview commands may show intended `git`, `gh`, or connector actions, but they do not authorize execution.

Allowed preview outcomes:

- command packet text;
- file allowlist and forbidden-list review;
- target-state inspection checklist;
- rollback and post-check checklist.

Disallowed P10A outcomes:

- actual downstream branch creation;
- downstream file write;
- downstream PR creation;
- production deployment;
- business-domain implementation.

## 7. Required future stage sequence

Recommended next stages:

| Stage | Purpose | Mutation boundary |
|---|---|---|
| P10B target-repo candidate selection | Read-only target repo selection and state evidence | No downstream mutation |
| P10C target-repo execution approval packet | Prepare named execution approval packet | No downstream mutation by packet alone |
| P10D controlled PR pilot execution evidence | Record approved execution if separately authorized | Only after explicit execution approval |

## 8. P10A outputs

P10A adds:

- this phase-entry gate-foundation record;
- P10A task manifest;
- P10A change plan;
- active-gates registration.

No source behavior changes are part of P10A.

## 9. Boundary

P10A grants no downstream target-repository mutation, production deployment, real external worker call, rollback execution, cleanup execution, business-domain implementation, or Codex replacement claim. It only establishes the gate foundation for later controlled P10 pilot stages.
