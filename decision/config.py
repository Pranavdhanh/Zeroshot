"""
Configuration for the Cost-Based Decision Layer.

Instead of arbitrary static thresholds, the decision layer minimizes expected loss:
  - Cost of missed fraud = transaction amount (money transferred to mule/fraudster)
  - Cost of friction on genuine payment = configurable penalty:
      - Low friction for WARN (subtle prompt, user can proceed or cancel)
      - High friction for HOLD (payment delayed, support call)
"""

from dataclasses import dataclass


@dataclass
class DecisionConfig:
    """Master configuration for the cost-based decision layer."""

    # Friction cost assigned to genuine transactions facing an intervention
    cost_warn_friction: float = 50.0      # INR penalty for showing a warning
    cost_hold_friction: float = 600.0     # INR penalty for holding payment

    # Warning intervention effectiveness: fraction of victims who cancel payment upon warning
    warn_effectiveness: float = 0.70      # 70% of warned victims cancel

    # Absolute safety boundaries (guardrails)
    min_prob_warn: float = 0.03           # Minimum probability to ever consider WARN
    min_prob_hold: float = 0.25           # Minimum probability to ever consider HOLD

    # High amount guardrail: above this amount, suspicious payments escalate to HOLD
    high_value_escalation_amount: float = 50000.0

    # Senior citizen protection mode multiplier (amplifies protection, lowers friction barrier)
    senior_protection_multiplier: float = 1.50
