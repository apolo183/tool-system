"""Pure subscription-capacity and renewal-review decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tool_system.release_governance import SemanticVersion

class SubscriptionChannel(str, Enum):
    CHATGPT_WEB = "CHATGPT_WEB"
    CODEX_CLI = "CODEX_CLI"

@dataclass(frozen=True)
class CapacitySnapshot:
    channel: SubscriptionChannel
    product_version: SemanticVersion
    window_capacity_units: int
    used_units: int
    observed_at_utc: int
    window_resets_at_utc: int
    subscription_renews_at_utc: int
    explicitly_enabled: bool

    def __post_init__(self) -> None:
        if self.window_capacity_units <= 0:
            raise ValueError("window capacity must be positive")
        if not 0 <= self.used_units <= self.window_capacity_units:
            raise ValueError("used units must be within capacity")
        if self.observed_at_utc < 0:
            raise ValueError("observation time must be non-negative")
        if self.window_resets_at_utc < self.observed_at_utc:
            raise ValueError("window reset cannot precede observation")
        if self.subscription_renews_at_utc < self.observed_at_utc:
            raise ValueError("renewal cannot precede observation")

@dataclass(frozen=True)
class CapacityPolicy:
    conserve_at_ppm: int
    block_at_ppm: int
    renewal_review_lead_seconds: int

    def __post_init__(self) -> None:
        if not 0 <= self.conserve_at_ppm < self.block_at_ppm <= 1_000_000:
            raise ValueError("capacity thresholds must be ordered PPM values")
        if self.renewal_review_lead_seconds < 0:
            raise ValueError("renewal review lead must be non-negative")

class CapacityStatus(str, Enum):
    DISABLED = "DISABLED"
    HEALTHY = "HEALTHY"
    CONSERVE = "CONSERVE"
    BLOCK_NEW_WORK = "BLOCK_NEW_WORK"

class RenewalStatus(str, Enum):
    NOT_DUE = "NOT_DUE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

@dataclass(frozen=True)
class SubscriptionDecision:
    capacity_status: CapacityStatus
    renewal_status: RenewalStatus
    used_ppm: int
    reasons: tuple[str, ...]
    purchase_authorized: bool = False
    renewal_authorized: bool = False
    external_action_authorized: bool = False

def evaluate_subscription(
    *, snapshot: CapacitySnapshot, policy: CapacityPolicy
) -> SubscriptionDecision:
    used_ppm = (
        snapshot.used_units * 1_000_000 // snapshot.window_capacity_units
    )
    reasons: list[str] = []
    if not snapshot.explicitly_enabled:
        capacity = CapacityStatus.DISABLED
        reasons.append("SUBSCRIPTION_CHANNEL_DISABLED")
    elif used_ppm >= policy.block_at_ppm:
        capacity = CapacityStatus.BLOCK_NEW_WORK
        reasons.append("CAPACITY_BLOCK_THRESHOLD_REACHED")
    elif used_ppm >= policy.conserve_at_ppm:
        capacity = CapacityStatus.CONSERVE
        reasons.append("CAPACITY_CONSERVATION_REQUIRED")
    else:
        capacity = CapacityStatus.HEALTHY
    seconds_to_renewal = (
        snapshot.subscription_renews_at_utc - snapshot.observed_at_utc
    )
    if seconds_to_renewal <= policy.renewal_review_lead_seconds:
        renewal = RenewalStatus.REVIEW_REQUIRED
        reasons.append("RENEWAL_REVIEW_REQUIRED")
    else:
        renewal = RenewalStatus.NOT_DUE
    return SubscriptionDecision(
        capacity_status=capacity,
        renewal_status=renewal,
        used_ppm=used_ppm,
        reasons=tuple(reasons),
    )

@dataclass(frozen=True)
class PortfolioDecision:
    preferred_channel: SubscriptionChannel | None
    reasons: tuple[str, ...]
    external_action_authorized: bool = False

def choose_subscription_channel(
    decisions: tuple[tuple[SubscriptionChannel, SubscriptionDecision], ...],
) -> PortfolioDecision:
    if len({channel for channel, _ in decisions}) != len(decisions):
        raise ValueError("subscription channels must be unique")
    rank = {
        CapacityStatus.HEALTHY: 0,
        CapacityStatus.CONSERVE: 1,
        CapacityStatus.BLOCK_NEW_WORK: 2,
        CapacityStatus.DISABLED: 3,
    }
    eligible = [
        (rank[decision.capacity_status], channel.value, channel)
        for channel, decision in decisions
        if decision.capacity_status
        not in {CapacityStatus.BLOCK_NEW_WORK, CapacityStatus.DISABLED}
    ]
    if not eligible:
        return PortfolioDecision(None, ("NO_ELIGIBLE_SUBSCRIPTION_CHANNEL",))
    _, _, selected = min(eligible)
    return PortfolioDecision(
        selected, ("OWNER_REVIEW_BEFORE_CHANNEL_SWITCH_REQUIRED",)
    )
