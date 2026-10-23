"""
Cost-based Decision Engine for real-time UPI transaction routing:
ALLOW / WARN / HOLD.

Principles:
  - Chooses action that minimizes expected loss given calibrated risk P and transaction amount.
  - A Rs. 50 payment to a new payee faces negligible risk (expected fraud loss is small),
    so friction cost dominates and ALLOW is chosen.
  - An Rs. 80,000 payment to a new payee has enormous potential loss,
    so even a modest 10% risk justifies a WARN or HOLD.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

from decision.config import DecisionConfig


class CostDecisionEngine:
    """Evaluates expected loss to determine optimal protective intervention."""

    def __init__(self, config: DecisionConfig = None):
        if config is None:
            self.config = DecisionConfig()
        else:
            self.config = config

    def decide_transaction(
        self,
        amount: float,
        calibrated_prob: float,
        is_senior: bool = False,
        is_collect_request: bool = False,
    ) -> Dict[str, Any]:
        """
        Choose ALLOW, WARN, or HOLD to minimize expected loss.

        Expected Loss:
          E[ALLOW] = P * amount
          E[WARN]  = P * amount * (1 - warn_effectiveness) + (1 - P) * cost_warn_friction
          E[HOLD]  = (1 - P) * cost_hold_friction
        """
        prob = float(np.clip(calibrated_prob, 0.0, 1.0))
        amt = float(max(0.0, amount))

        # Apply senior citizen protection scaling if applicable
        if is_senior:
            effective_prob = min(1.0, prob * self.config.senior_protection_multiplier)
            hold_friction = self.config.cost_hold_friction * 0.70
            warn_friction = self.config.cost_warn_friction * 0.70
        else:
            effective_prob = prob
            hold_friction = self.config.cost_hold_friction
            warn_friction = self.config.cost_warn_friction

        # Expected losses
        loss_allow = effective_prob * amt
        loss_warn = (
            effective_prob * amt * (1.0 - self.config.warn_effectiveness)
            + (1.0 - effective_prob) * warn_friction
        )
        loss_hold = (1.0 - effective_prob) * hold_friction

        # High value escalation guardrail
        if amt >= self.config.high_value_escalation_amount and effective_prob >= self.config.min_prob_hold:
            action = "HOLD"
        elif is_collect_request and effective_prob >= 0.15:
            # Fake collect requests deceive users into paying; warn aggressively
            action = "WARN"
        elif effective_prob < self.config.min_prob_warn:
            action = "ALLOW"
        else:
            # Pick minimum expected loss
            if loss_allow <= loss_warn and loss_allow <= loss_hold:
                action = "ALLOW"
            elif loss_warn <= loss_hold:
                if effective_prob >= self.config.min_prob_warn:
                    action = "WARN"
                else:
                    action = "ALLOW"
            else:
                if effective_prob >= self.config.min_prob_hold:
                    action = "HOLD"
                elif effective_prob >= self.config.min_prob_warn:
                    action = "WARN"
                else:
                    action = "ALLOW"

        # Chosen action expected loss
        if action == "ALLOW":
            chosen_loss = loss_allow
        elif action == "WARN":
            chosen_loss = loss_warn
        else:
            chosen_loss = loss_hold

        return {
            "action": action,
            "calibrated_prob": prob,
            "effective_prob": effective_prob,
            "amount": amt,
            "expected_loss": chosen_loss,
            "loss_allow": loss_allow,
            "loss_warn": loss_warn,
            "loss_hold": loss_hold,
            "is_senior": is_senior,
        }

    def evaluate_batch(
        self,
        amounts: np.ndarray,
        probs: np.ndarray,
        is_fraud: np.ndarray,
        is_senior: np.ndarray = None,
        is_collect: np.ndarray = None,
    ) -> Dict[str, Any]:
        """
        Evaluate performance across a test stream.
        Computes total fraud rupees prevented, friction count, and net savings.
        """
        n = len(amounts)
        actions: List[str] = []

        total_fraud_amt = 0.0
        prevented_fraud_amt = 0.0
        genuine_friction_count = 0
        genuine_hold_count = 0
        genuine_warn_count = 0
        fraud_caught_count = 0
        total_fraud_count = 0

        for i in range(n):
            amt = float(amounts[i])
            p = float(probs[i])
            fraud = bool(is_fraud[i])
            senior = bool(is_senior[i]) if is_senior is not None else False
            collect = bool(is_collect[i]) if is_collect is not None else False

            res = self.decide_transaction(amt, p, senior, collect)
            act = res["action"]
            actions.append(act)

            if fraud:
                total_fraud_count = total_fraud_count + 1
                total_fraud_amt = total_fraud_amt + amt
                if act == "HOLD":
                    prevented_fraud_amt = prevented_fraud_amt + amt
                    fraud_caught_count = fraud_caught_count + 1
                elif act == "WARN":
                    # Warn saves partial fraud via user cancellation
                    prevented_fraud_amt = prevented_fraud_amt + (amt * self.config.warn_effectiveness)
                    fraud_caught_count = fraud_caught_count + 1
            else:
                if act == "HOLD":
                    genuine_friction_count = genuine_friction_count + 1
                    genuine_hold_count = genuine_hold_count + 1
                elif act == "WARN":
                    genuine_friction_count = genuine_friction_count + 1
                    genuine_warn_count = genuine_warn_count + 1

        total_friction_cost = (
            float(genuine_warn_count) * self.config.cost_warn_friction
            + float(genuine_hold_count) * self.config.cost_hold_friction
        )
        net_value_saved = prevented_fraud_amt - total_friction_cost

        return {
            "total_transactions": n,
            "total_fraud_count": total_fraud_count,
            "fraud_caught_count": fraud_caught_count,
            "total_fraud_amount": total_fraud_amt,
            "prevented_fraud_amount": prevented_fraud_amt,
            "fraud_amount_prevented_pct": (prevented_fraud_amt / total_fraud_amt * 100.0) if total_fraud_amt > 0 else 0.0,
            "genuine_friction_count": genuine_friction_count,
            "genuine_warn_count": genuine_warn_count,
            "genuine_hold_count": genuine_hold_count,
            "total_friction_cost": total_friction_cost,
            "net_value_saved": net_value_saved,
            "actions": actions,
        }

    def generate_friction_curve(
        self,
        amounts: np.ndarray,
        probs: np.ndarray,
        is_fraud: np.ndarray,
        num_points: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Generate fraud caught vs customer friction curve by sweeping friction sensitivity.
        Used live by the dashboard widget and evaluation report.
        """
        curve_points: List[Dict[str, Any]] = []
        multipliers = np.logspace(-1.0, 1.0, num_points)  # 0.1x to 10x friction cost

        original_warn_cost = self.config.cost_warn_friction
        original_hold_cost = self.config.cost_hold_friction

        for mult in multipliers:
            self.config.cost_warn_friction = original_warn_cost * mult
            self.config.cost_hold_friction = original_hold_cost * mult

            stats = self.evaluate_batch(amounts, probs, is_fraud)
            curve_points.append({
                "friction_multiplier": round(float(mult), 3),
                "warn_friction_cost": round(self.config.cost_warn_friction, 1),
                "hold_friction_cost": round(self.config.cost_hold_friction, 1),
                "prevented_fraud_amount": round(stats["prevented_fraud_amount"], 0),
                "genuine_friction_count": stats["genuine_friction_count"],
                "net_value_saved": round(stats["net_value_saved"], 0),
                "fraud_recall_pct": round(stats["fraud_caught_count"] / max(1, stats["total_fraud_count"]) * 100.0, 1),
            })

        # Restore original config
        self.config.cost_warn_friction = original_warn_cost
        self.config.cost_hold_friction = original_hold_cost

        return curve_points
