# Finance-US P1B Minimal Ranking Implementation Packet

status: EXECUTION_APPROVAL_REQUIRED
parent: docs/reports/finance_us_p1b_phase_entry_record.md
created_at: 2026-07-11 UTC+08:00

## Locked target

```text
repository: apolo183/finance-us
base_branch: main
base_sha: 7101847826e6701a4d8cc7f0a6208fb9aee2cc4e
proposed_branch: p1b-minimal-ranking-code
milestone: P1B_MINIMAL_RANKING_CODE
write_mode: draft_pull_request
```

This packet grants no target write or PR-lifecycle authority by itself.

## Objective

Implement one deterministic, standard-library-only, in-memory ranking function over rows that have already passed the active finance-us US-equity contracts, plus focused smoke tests.

## Exact future target allowlist

Only these target paths may change under a separate execution approval:

```text
README.md
AGENTS.md
blueprint/finance_us_phase_1_v0.yaml
finance_us/__init__.py
finance_us/ranking.py
tests/test_ranking.py
```

No contract YAML, dependency file, CI file, data file, adapter, scheduler, database, notebook, model, backtest, report artifact, portfolio, broker, or trading path may change.

## Governance synchronization

The three existing governance files may only be updated to:

- mark P1A accepted, merged, strictly validated, and closed;
- identify P1B as the current bounded milestone;
- describe the minimal ranking function and smoke-test scope;
- preserve all observation-only, fail-closed, no-data-adapter, no-backtest, no-live-trading, and no-investment-claim boundaries;
- keep P1C and later milestones unauthorized.

No market, exchange, calendar, currency, security-type, cutoff, or output-contract semantics may be changed.

## Required API

`finance_us/ranking.py` must expose:

```python
rank_top_k(rows, *, top_k=10)
```

The function must return a new list and must not mutate the input rows or input sequence.

## Ranking-relevant input fields

Each row must provide:

```text
symbol
exchange
currency
security_type
score
score_version
feature_version
```

The caller remains responsible for upstream validation against the full P1A data and cutoff contracts. The ranking function must independently fail closed on missing or invalid ranking-relevant fields.

## Validation and failure rules

- `symbol` must be a non-empty string.
- `exchange` must be `NYSE` or `NASDAQ`.
- `currency` must be `USD`.
- `security_type` must be `common_stock`.
- `score_version` and `feature_version` must be non-empty strings.
- `score` must be a finite real number; booleans, NaN, infinity, strings, nulls, and missing values are invalid.
- duplicate `(exchange, symbol)` identities must raise an error.
- `top_k` must be an integer from 1 through 10; booleans and values outside the range are invalid.
- empty valid input returns an empty list.
- fewer than `top_k` valid rows returns all rows.
- invalid input must raise a deterministic `ValueError`; invalid rows must never be silently dropped or coerced.

## Deterministic ordering

Sort with exactly this key:

```text
1. score descending
2. exchange ascending
3. symbol ascending
```

Input order must not affect output order. Random ordering and unstable ties are forbidden.

## Output row contract

Each returned row must contain exactly:

```text
rank
symbol
exchange
currency
security_type
score
score_version
feature_version
tie_breaker_value
```

Rules:

- ranks are contiguous integers starting at 1;
- no more than `top_k` rows are returned;
- `tie_breaker_value` is exactly `<exchange>:<symbol>`;
- visible input values are preserved without normalization or coercion;
- no run metadata, file output, recommendation language, order instruction, expected-return field, label, or future-return field is produced.

## Required smoke tests

`tests/test_ranking.py` must use the Python standard library and cover at minimum:

1. descending score ordering;
2. exchange then symbol tie-break ordering;
3. identical output after input permutation;
4. `top_k` truncation and fewer-than-`top_k` behavior;
5. empty input;
6. missing, non-numeric, boolean, NaN, and infinite score rejection;
7. invalid exchange, currency, security type, and blank version rejection;
8. duplicate `(exchange, symbol)` rejection;
9. invalid `top_k` rejection;
10. contiguous ranks, exact output keys, and exact tie-breaker values;
11. input sequence and row immutability.

## Verification commands

```bash
git diff --check
python -m compileall finance_us tests
python -m unittest discover -s tests -p 'test_ranking.py' -v
```

Additional pass conditions:

```text
changed_paths: exact_six_file_allowlist
external_dependencies_added: false
network_or_database_calls: false
filesystem_output: false
randomness: false
contract_semantics_changed: false
PR_state: open_draft_unmerged
```

## Authorized sequence after separate approval

1. verify finance-us `main` is exactly the locked base SHA;
2. confirm the proposed branch and duplicate open PR do not exist;
3. create `p1b-minimal-ranking-code` from the locked base;
4. modify only the six allowlisted paths;
5. run the verification commands and inspect the exact diff;
6. open one draft PR against `main`;
7. collect remote and target-local evidence;
8. stop without marking ready, merging, entering P1C, or deleting branches.

## Forbidden actions

- no direct write to target `main`;
- no target mutation without a new explicit execution approval;
- no PR ready transition or merge without separate approval;
- no market-data ingestion or adapter work;
- no feature research, model training, model selection, backtesting, or performance claims;
- no labels or future-return fields;
- no scheduler, persistence, production deployment, broker, portfolio, order, or trading logic;
- no rollback, cleanup, or branch deletion;
- no real external worker calls or Codex-replacement claims.

## Rollback

Before merge, close the draft PR and retain its head SHA as evidence. Branch deletion requires separate cleanup approval. After a future merge, rollback requires a separately approved revert packet and revert PR; never reset or force-push target main.
