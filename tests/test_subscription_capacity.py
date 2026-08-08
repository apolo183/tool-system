from __future__ import annotations

import pytest

from tool_system.release_governance import SemanticVersion
from tool_system.subscription_capacity import (
    CapacityPolicy, CapacitySnapshot, CapacityStatus, RenewalStatus,
    SubscriptionChannel, choose_subscription_channel,
    evaluate_subscription,
)

POLICY = CapacityPolicy(700_000, 900_000, 100)

def _snapshot(channel=SubscriptionChannel.CHATGPT_WEB, used=100, **kw):
    values = dict(
        channel=channel, product_version=SemanticVersion(1, 0, 0),
        window_capacity_units=1000, used_units=used,
        observed_at_utc=1000, window_resets_at_utc=1100,
        subscription_renews_at_utc=2000, explicitly_enabled=True,
    )
    values.update(kw)
    return CapacitySnapshot(**values)

def test_capacity_ppm_and_thresholds_are_deterministic() -> None:
    healthy = evaluate_subscription(snapshot=_snapshot(), policy=POLICY)
    assert healthy.capacity_status is CapacityStatus.HEALTHY
    assert healthy.used_ppm == 100_000
    conserve = evaluate_subscription(
        snapshot=_snapshot(used=700), policy=POLICY
    )
    assert conserve.capacity_status is CapacityStatus.CONSERVE
    blocked = evaluate_subscription(
        snapshot=_snapshot(used=900), policy=POLICY
    )
    assert blocked.capacity_status is CapacityStatus.BLOCK_NEW_WORK
    assert blocked.external_action_authorized is False

def test_disabled_and_renewal_review_remain_non_authorizing() -> None:
    result = evaluate_subscription(
        snapshot=_snapshot(
            explicitly_enabled=False, subscription_renews_at_utc=1050
        ),
        policy=POLICY,
    )
    assert result.capacity_status is CapacityStatus.DISABLED
    assert result.renewal_status is RenewalStatus.REVIEW_REQUIRED
    assert result.purchase_authorized is False
    assert result.renewal_authorized is False

def test_channel_choice_is_deterministic_and_owner_gated() -> None:
    web = evaluate_subscription(snapshot=_snapshot(used=800), policy=POLICY)
    cli = evaluate_subscription(
        snapshot=_snapshot(
            channel=SubscriptionChannel.CODEX_CLI, used=100
        ),
        policy=POLICY,
    )
    choice = choose_subscription_channel((
        (SubscriptionChannel.CHATGPT_WEB, web),
        (SubscriptionChannel.CODEX_CLI, cli),
    ))
    assert choice.preferred_channel is SubscriptionChannel.CODEX_CLI
    assert choice.external_action_authorized is False

def test_invalid_snapshot_and_duplicate_channels_fail_closed() -> None:
    with pytest.raises(ValueError):
        _snapshot(used=1001)
    decision = evaluate_subscription(snapshot=_snapshot(), policy=POLICY)
    with pytest.raises(ValueError):
        choose_subscription_channel((
            (SubscriptionChannel.CHATGPT_WEB, decision),
            (SubscriptionChannel.CHATGPT_WEB, decision),
        ))
