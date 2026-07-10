# P10C Finance-US US-Equity Contract Realignment Execution Packet

repo_rel_path: docs/reports/p10c_finance_us_us_equity_contract_realignment_execution_packet.md  
role: named downstream execution-approval packet  
purpose: define a bounded contract-only pull-request pilot that realigns finance-us from residual A-share semantics to a US-equity contract before ranking-code implementation  
status: EXECUTION_APPROVAL_REQUIRED  
phase: P10_CONTROLLED_TARGET_REPO_PR_PILOT  
created_at: 2026-07-10 UTC+08:00

## 1. Disposition

P10C prepares a named execution packet for the first real P10 downstream pull-request pilot.

This packet does not itself create a target branch, change a target file, open a target pull request, merge a target pull request, execute rollback, deploy to production, download data, train or evaluate models, run a backtest, call a real external worker, or claim Codex replacement.

A later explicit execution approval is required before any mutation in the target repository.

## 2. Parent and global alignment

Parent document:

```text
docs/reports/p10b2_finance_us_pilot_target_objective.md
```

Parent alignment: P10B2 selected canonical project `finance-us`, GitHub remote `apolo183/finance-os`, as the controlled P10 pilot target. The user then identified that the current target blueprint still contains A-share semantics. P10C therefore places contract realignment before ranking-code implementation.

Global blueprint alignment:

```text
blueprint/tool_system_v0.yaml :: milestones.P10_CONTROLLED_TARGET_REPO_PR_PILOT
```

Global alignment: P10C defines a named, file-scoped, no-production target pull-request packet with tests, rollback, post-action verification, and stop conditions. It grants no downstream write authority by itself.

## 3. Target identity and preflight state

```text
canonical_project_name: finance-us
github_repository_full_name: apolo183/finance-os
remote_slug_is_legacy_name: true
base_branch: main
observed_base_sha: b801326bea5e80ef585be0977e9e493cbfa0c34e
observed_base_commit: chore: add finance-os evaluation contract
proposed_target_branch: p1a-us-equity-contract-realignment
proposed_pr_base: main
proposed_pr_merge_authority: not granted
```

The canonical project name and GitHub remote slug must remain separate in all execution and audit records.

## 4. Drift evidence requiring correction

Read-only target evidence shows:

- `README.md` and `AGENTS.md` still identify the business system as `finance-os`;
- `blueprint/finance_os_phase_1_v0.yaml` uses the old system identity and includes A-share-oriented optional fields such as `board`, `is_st`, and `listed_days`;
- `contracts/data_input_contract.yaml` includes `amount`, `board`, `is_st`, `listed_days`, `suspended`, `limit_up_down_status`, `st_filter_policy`, and suspension-oriented filtering;
- `contracts/cutoff_contract.yaml` fixes the market timezone to `Asia/Shanghai` and uses the old system identity;
- ranking and evaluation contracts still use the old system identity;
- the target remains observation-only and already prohibits live trading, broker integration, investment recommendations, and unsupported performance claims.

The correction is a contract and identity realignment. It is not authorization to design alpha, select a model, download market data, run a backtest, or make an investment claim.

## 5. Approved objective if separately executed

Proposed target milestone:

```text
P1A_US_EQUITY_CONTRACT_REALIGNMENT
```

Objective:

```text
Replace residual A-share identity, field, calendar, and cutoff semantics with an explicit US-equity observation-only contract, while preserving Phase 1 shadow-top10 safety boundaries and deferring all ranking-code implementation.
```

This objective supersedes P1B ranking-code implementation as the first P10 pilot action. P1B remains a later milestone after contract realignment is reviewed and accepted.

## 6. Exact target file disposition

| Target path | Disposition | Required result |
|---|---|---|
| `README.md` | MODIFY | Canonical identity becomes `finance-us`; Phase 1 is explicitly US equities; pointer uses the new blueprint path; no live-trading or investment claims |
| `AGENTS.md` | MODIFY | Canonical identity becomes `finance-us`; current phase remains observation-only US-equity shadow ranking; tool-system separation remains explicit |
| `blueprint/finance_us_phase_1_v0.yaml` | ADD | New canonical US-equity blueprint with system `finance-us`, USD/exchange/security-type semantics, US market-calendar boundary, and observation-only safety rules |
| `blueprint/finance_os_phase_1_v0.yaml` | DELETE | Old-name blueprint removed only after all active references are migrated to the new path |
| `contracts/data_input_contract.yaml` | MODIFY | System identity becomes `finance-us`; remove A-share-only fields and filters; add explicit US-equity exchange, currency, security type, listing status, IPO date/age, volume and dollar-volume semantics |
| `contracts/cutoff_contract.yaml` | MODIFY | System identity becomes `finance-us`; timezone becomes `America/New_York`; calendar/session rules become US-exchange and DST aware; remove A-share cutoff semantics |
| `contracts/ranking_output_contract.yaml` | MODIFY | System identity becomes `finance-us`; output identity includes exchange and currency where needed; deterministic observation-only rules remain |
| `contracts/evaluation_contract.yaml` | MODIFY | System identity becomes `finance-us`; structural evaluation includes market-calendar identity; forbidden performance and production claims remain unchanged or stricter |

No other target file is allowed to change.

## 7. Required US-equity contract semantics

The target change must establish at minimum:

- canonical project identity `finance-us`;
- business domain `quantitative_finance_us_equities` or equivalent explicit US-equity identity;
- USD currency declaration;
- US-listed common-equity universe boundary, with exchange and security-type policies explicitly declared;
- exchange or venue identifier for each instrument;
- `America/New_York` market timezone;
- US exchange calendar identifier and daylight-saving-time-aware session rules;
- adjusted-price policy that accounts for splits and distributions without future information;
- listing-status and IPO-age policies instead of `is_st` and A-share listing-day semantics;
- volume and optional dollar-volume semantics instead of ambiguous A-share `amount` semantics;
- fail-closed behavior for unknown exchange, currency, security type, calendar, snapshot, or availability time;
- observation-only output with no buy/sell language, live execution instruction, expected-return claim, alpha claim, Sharpe claim, best-model claim, or production-readiness claim.

## 8. Explicitly forbidden target changes

The target PR must not change or add:

```text
src/**
tests/**
data/**
raw/**
lake/**
artifacts/**
reports/**
.github/**
Makefile
pyproject.toml
requirements*.txt
```

It must not:

- implement a ranking function;
- add a scheduler or pipeline runner;
- download or ingest market data;
- write databases, lakes, raw stores, or artifacts;
- train, evaluate, score, rank, select, or backtest stocks;
- add broker or order-execution code;
- merge the target pull request;
- delete any target branch;
- claim investment performance or production readiness.

## 9. Required validation commands

Run on the target branch after the proposed contract changes:

```bash
git diff --check

python - <<'PY'
from pathlib import Path

required_files = [
    Path("README.md"),
    Path("AGENTS.md"),
    Path("blueprint/finance_us_phase_1_v0.yaml"),
    Path("contracts/data_input_contract.yaml"),
    Path("contracts/cutoff_contract.yaml"),
    Path("contracts/ranking_output_contract.yaml"),
    Path("contracts/evaluation_contract.yaml"),
]
for path in required_files:
    if not path.is_file():
        raise SystemExit(f"BLOCK: missing required file {path}")

if Path("blueprint/finance_os_phase_1_v0.yaml").exists():
    raise SystemExit("BLOCK: legacy blueprint path still exists")

combined = "\n".join(path.read_text(encoding="utf-8") for path in required_files)
required_terms = [
    "finance-us",
    "America/New_York",
    "USD",
    "exchange",
    "security_type",
    "observation_only",
]
for term in required_terms:
    if term not in combined:
        raise SystemExit(f"BLOCK: required US-equity term missing: {term}")

forbidden_terms = [
    "Asia/Shanghai",
    "is_st",
    "limit_up_down_status",
    "st_filter_policy",
]
for term in forbidden_terms:
    if term in combined:
        raise SystemExit(f"BLOCK: residual A-share term present: {term}")

print("PASS: finance-us US-equity contract realignment checks passed")
PY

git status -sb --untracked-files=all
git diff --stat origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Pass conditions:

- all commands exit zero;
- changed target paths exactly match the allowlist in Section 6;
- no forbidden term remains in the active identity, blueprint, or contract files;
- no source, test, data, CI, dependency, runtime, or artifact file changes;
- target `main` is not modified.

## 10. Target mutation sequence if explicitly approved later

A later executor may perform only this sequence:

1. refresh `apolo183/finance-os` metadata and verify `main` still points to the approved base SHA or stop for packet refresh;
2. verify no branch named `p1a-us-equity-contract-realignment` exists;
3. create that branch once from the approved `main` SHA;
4. apply only the file dispositions in Section 6;
5. run every command in Section 9;
6. inspect exact changed filenames and diff statistics;
7. open one draft pull request to `main`;
8. collect target CI/review evidence;
9. stop without merging the target pull request.

## 11. Stop conditions

Stop before mutation or before PR creation if:

- target `main` SHA differs from the packet-approved SHA;
- target identity, README, AGENTS, blueprint, or active contracts changed after packet creation;
- the proposed target branch already exists;
- an open pull request already represents the same objective;
- any proposed change falls outside the exact allowlist;
- any source, test, CI, dependency, data, runtime, or artifact change is required;
- validation fails;
- US-equity semantics remain ambiguous;
- execution approval has not been explicitly granted.

## 12. Rollback and recovery

Before target PR merge, normal rollback is:

```text
close the unmerged target PR
retain its commit SHA as evidence
remove the target branch only through a separately approved cleanup gate
```

If a target commit must be reversed while retaining the branch, use a Git revert of the exact target commit after a separate rollback-execution approval.

No target-main rollback is authorized because target PR merge is outside this packet.

## 13. Post-action verification

After a separately approved execution, record:

- refreshed target base SHA;
- target branch name and head SHA;
- exact changed filenames;
- validation command outputs;
- draft target PR number and state;
- target CI jobs and steps;
- confirmation that target `main` remains unchanged;
- confirmation that no data/model/runtime operation occurred;
- rollback reference;
- cleanup disposition.

## 14. Approval boundary

This P10C packet is ready for human execution approval only after it is merged into tool-system with green CI.

Approval of P10C must explicitly name this packet and authorize only the target branch/file/PR mutations described above. It does not authorize target PR merge, production deployment, data operations, model execution, business-performance claims, real external worker calls, rollback execution, branch deletion, or Codex replacement claims.
