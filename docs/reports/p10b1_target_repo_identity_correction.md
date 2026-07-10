# P10B1 Target-Repo Identity Correction

repo_rel_path: docs/reports/p10b1_target_repo_identity_correction.md  
role: P10 target-repository identity correction and candidate-selection record  
purpose: correct the canonical-name versus GitHub-slug error in P10B and select the finance-cn candidate for read-only P10C packet preparation  
status: CANDIDATE_SELECTED_READONLY_IDENTITY_CORRECTED  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-10 UTC+08:00

## 1. Disposition

P10B1 corrects the repository-identity inference recorded in:

```text
docs/reports/p10b_target_repo_candidate_selection.md
```

The original read-only calls were real, but the conclusion was wrong because the canonical project name was treated as the GitHub repository slug.

This correction does not create a downstream branch, modify a downstream file, open a downstream pull request, execute rollback, deploy to production, implement business-domain logic, call a real external worker, or claim Codex replacement.

## 2. User correction

The user supplied the authoritative rename mapping:

```text
finance-app -> finance-cn
finance-os  -> finance-us
```

The canonical project names and GitHub remote slugs must therefore be recorded separately.

## 3. Error analysis

P10B called:

```text
GitHub.get_repo(repository_full_name="apolo183/finance-cn")
```

and received `404 Not Found`.

That result proved only that `apolo183/finance-cn` is not the accessible GitHub slug. It did not prove that the canonical `finance-cn` project was inaccessible.

The incorrect P10B conclusion:

```text
CANDIDATE_NOT_SELECTED_ACCESS_BLOCKED
```

is superseded by this record.

## 4. Correct identity map

| Canonical project name | Current GitHub remote slug | Prior name | Selection status |
|---|---|---|---|
| `finance-cn` | `apolo183/finance-app` | `finance-app` | Selected for read-only P10C packet preparation |
| `finance-us` | `apolo183/finance-os` | `finance-os` | Identity recorded; not selected for this pilot |

Future P10 records must include both `canonical_project_name` and `github_repository_full_name` when they differ.

## 5. Connector-backed repository evidence

The authenticated GitHub repository list shows:

### finance-cn remote

```text
canonical_project_name: finance-cn
github_repository_full_name: apolo183/finance-app
visibility: private
default_branch: main
permissions: admin, maintain, pull, push, triage
```

Current visible main HEAD:

```text
9bda8d068545cd9bde2da7dbb6e3e2e35a164177
Require governance check before material changes (#582)
```

### finance-us remote

```text
canonical_project_name: finance-us
github_repository_full_name: apolo183/finance-os
visibility: private
default_branch: main
permissions: admin, maintain, pull, push, triage
```

Current visible main HEAD:

```text
b801326bea5e80ef585be0977e9e493cbfa0c34e
chore: add finance-os evaluation contract
```

## 6. finance-cn governance evidence

The selected `finance-cn` remote contains active governance controls:

- `AGENTS.md` requires reading `docs/project_global_development_principles_v1.md` before engineering work;
- `AGENTS.md` requires `make governance-check` before material modification;
- gate failure must stop with `DRIFT_BLOCKED`;
- gate success does not authorize runtime, training, evaluation, scoring, ranking, selection, backtest, production, deletion, commit, push, DB/lake/raw/model-artifact writes, deployment, or external-system writes;
- `REPO_MANIFEST.md` is the active repository manifest and formal-file registry;
- unregistered formal files are not active until registered or explicitly classified;
- `scripts/governance/check_milestone_gate.py` is registered as an active machine milestone gate.

Local evidence previously supplied by the user used:

```text
/home/rich/projects/finance-cn
```

This is consistent with the canonical-name mapping above.

## 7. Corrected candidate-selection decision

Selected P10 pilot candidate:

```text
canonical_project_name: finance-cn
github_repository_full_name: apolo183/finance-app
base_branch: main
observed_base_sha: 9bda8d068545cd9bde2da7dbb6e3e2e35a164177
selection_scope: read-only P10C execution-approval packet preparation only
```

Selection does not approve any downstream mutation.

Before P10C is finalized, the packet must refresh the base SHA and re-read the current target governance files. Any drift blocks packet approval.

## 8. P10C entry condition

P10C may now prepare a named execution-approval packet for `finance-cn`, using GitHub remote `apolo183/finance-app`.

The packet must explicitly distinguish:

```text
canonical_project_name: finance-cn
github_repository_full_name: apolo183/finance-app
```

It must also name the target branch, exact file allowlist, forbidden paths, intended diff, validation commands, rollback, post-action verification, and stop condition.

P10C packet creation alone grants no write authority. A later explicit execution approval remains required before any target branch, target file, or target PR mutation.

## 9. Boundary

P10B1 corrects repository identity and selects `finance-cn` for read-only P10C packet preparation. It grants no downstream target-repository mutation, production deployment, real external worker call, rollback execution, cleanup execution, business-domain implementation, or Codex replacement claim.
