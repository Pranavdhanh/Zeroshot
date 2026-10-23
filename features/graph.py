"""
Incremental graph feature computation for UPI fraud and mule network detection.

Maintains in-memory graph state:
  - Account in/out degrees
  - Fan-in and fan-out ratios
  - Windowed pass-through ratio (outflow / inflow within short window)
  - Funds dwell time (delay between receiving and moving funds)
  - Distinct senders in the last 1 hour
  - O(1) Hop distance to known flagged fraud / mule accounts
  - Community / cluster ID (computed periodically via NetworkX)

All operations are O(1) in memory per transaction.
Never rebuilds the entire graph per transaction.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx


class AccountGraphState:
    """Tracks graph-level counters and rolling transaction windows for an account."""

    def __init__(self, vpa: str):
        self.vpa: str = vpa
        self.in_degree: int = 0
        self.out_degree: int = 0
        self.total_in_amount: float = 0.0
        self.total_out_amount: float = 0.0

        self.first_seen: Optional[datetime] = None
        self.last_seen: Optional[datetime] = None

        self.is_flagged: bool = False
        self.flagged_timestamp: Optional[datetime] = None
        self.community_id: int = -1

        # Rolling inbound credits: list of (timestamp, amount, sender_vpa)
        self.recent_inbound: deque = deque(maxlen=50)
        # Rolling outbound debits: list of (timestamp, amount, receiver_vpa)
        self.recent_outbound: deque = deque(maxlen=50)

    def get_fan_in_ratio(self) -> float:
        """Return fan-in to fan-out ratio: in_degree / (out_degree + 1)."""
        denominator = float(self.out_degree + 1)
        return float(self.in_degree) / denominator

    def get_fan_out_ratio(self) -> float:
        """Return fan-out to fan-in ratio: out_degree / (in_degree + 1)."""
        denominator = float(self.in_degree + 1)
        return float(self.out_degree) / denominator

    def get_pass_through_ratio(self, current_time: datetime, window_seconds: int = 86400) -> float:
        """
        Compute pass-through ratio in sliding window:
        outflow_amount / (inflow_amount + 1.0)
        Mule accounts typically have high pass-through (>0.8) within short windows.
        """
        cutoff = current_time - timedelta(seconds=window_seconds)
        inflow = 0.0
        for ts, amt, _ in self.recent_inbound:
            if ts >= cutoff:
                inflow = inflow + amt

        if inflow <= 0.0:
            return 0.0

        outflow = 0.0
        for ts, amt, _ in self.recent_outbound:
            if ts >= cutoff:
                outflow = outflow + amt

        ratio = outflow / (inflow + 1.0)
        if ratio > 5.0:
            ratio = 5.0
        return ratio

    def get_dwell_time_seconds(self, current_time: datetime, window_seconds: int = 86400) -> float:
        """
        Estimate funds dwell time: time difference between recent inbound credit
        and the earliest subsequent outbound debit.
        """
        cutoff = current_time - timedelta(seconds=window_seconds)
        valid_in = [ts for ts, amt, _ in self.recent_inbound if ts >= cutoff]
        valid_out = [ts for ts, amt, _ in self.recent_outbound if ts >= cutoff]

        if len(valid_in) == 0 or len(valid_out) == 0:
            return float(window_seconds)

        total_dwell = 0.0
        paired_count = 0
        for in_ts in valid_in:
            subsequent_outs = [out_ts for out_ts in valid_out if out_ts >= in_ts]
            if len(subsequent_outs) > 0:
                earliest_out = min(subsequent_outs)
                dwell = (earliest_out - in_ts).total_seconds()
                total_dwell = total_dwell + dwell
                paired_count = paired_count + 1

        if paired_count > 0:
            return total_dwell / float(paired_count)
        else:
            return float(window_seconds)

    def get_distinct_senders_1hr(self, current_time: datetime) -> int:
        """Return count of distinct senders sending money in the last 1 hour."""
        cutoff = current_time - timedelta(seconds=3600)
        senders: Set[str] = set()
        for ts, _, sender in self.recent_inbound:
            if ts >= cutoff:
                senders.add(sender)
        return len(senders)


class GraphFeatureEngine:
    """
    Incremental graph feature engine with O(1) hop tracking and rolling window metrics.
    """

    def __init__(self):
        self.accounts: Dict[str, AccountGraphState] = {}
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)

        # O(1) Sets for hop distance lookups
        self.flagged_accounts: Set[str] = set()
        self.hop1_flagged: Set[str] = set()
        self.hop2_flagged: Set[str] = set()

        self.nx_graph: nx.Graph = nx.Graph()
        self.total_transactions_processed: int = 0

    def get_or_create_account(self, vpa: str) -> AccountGraphState:
        """Retrieve existing account state or create a new one."""
        if vpa not in self.accounts:
            self.accounts[vpa] = AccountGraphState(vpa)
        return self.accounts[vpa]

    def flag_account(self, vpa: str, timestamp: datetime) -> None:
        """
        Flag an account as fraudulent or confirmed mule, and update O(1) neighborhood sets.
        """
        account = self.get_or_create_account(vpa)
        account.is_flagged = True
        account.flagged_timestamp = timestamp
        self.flagged_accounts.add(vpa)

        # Update hop1 and hop2 sets
        neighbors = self.adjacency.get(vpa, set())
        for n1 in neighbors:
            if n1 not in self.flagged_accounts:
                self.hop1_flagged.add(n1)
                # Add n1's neighbors to hop2
                for n2 in self.adjacency.get(n1, set()):
                    if n2 not in self.flagged_accounts and n2 not in self.hop1_flagged:
                        self.hop2_flagged.add(n2)

    def get_hop_distance_to_flagged(self, vpa: str) -> int:
        """O(1) hop distance lookup using pre-indexed neighborhood sets."""
        if vpa in self.flagged_accounts:
            return 0
        elif vpa in self.hop1_flagged:
            return 1
        elif vpa in self.hop2_flagged:
            return 2
        else:
            return 999

    def compute(self, txn: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute graph features for a transaction BEFORE updating graph state.
        """
        sender_vpa = str(txn["sender_vpa"])
        receiver_vpa = str(txn["receiver_vpa"])

        timestamp = txn["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        sender_state = self.get_or_create_account(sender_vpa)
        receiver_state = self.get_or_create_account(receiver_vpa)

        features: Dict[str, float] = {}

        # Degrees
        features["sender_in_degree"] = float(sender_state.in_degree)
        features["sender_out_degree"] = float(sender_state.out_degree)
        features["receiver_in_degree"] = float(receiver_state.in_degree)
        features["receiver_out_degree"] = float(receiver_state.out_degree)

        # Fan-in / Fan-out
        features["receiver_fan_in_ratio"] = receiver_state.get_fan_in_ratio()
        features["sender_fan_out_ratio"] = sender_state.get_fan_out_ratio()

        # Pass-through & dwell time
        features["receiver_pass_through_ratio"] = receiver_state.get_pass_through_ratio(timestamp)
        features["sender_pass_through_ratio"] = sender_state.get_pass_through_ratio(timestamp)
        features["receiver_funds_dwell_time_seconds"] = receiver_state.get_dwell_time_seconds(timestamp)

        # Distinct senders in last 1 hour
        features["receiver_distinct_senders_1hr"] = float(receiver_state.get_distinct_senders_1hr(timestamp))

        # Network age
        if receiver_state.first_seen is not None:
            age_delta = timestamp - receiver_state.first_seen
            features["receiver_network_age_days"] = max(0.0, age_delta.total_seconds() / 86400.0)
        else:
            features["receiver_network_age_days"] = 0.0

        # O(1) Hop distance
        receiver_dist = self.get_hop_distance_to_flagged(receiver_vpa)
        sender_dist = self.get_hop_distance_to_flagged(sender_vpa)
        features["receiver_hop_to_flagged"] = float(receiver_dist)
        features["sender_hop_to_flagged"] = float(sender_dist)
        min_hop = min(receiver_dist, sender_dist)
        features["min_hop_to_flagged"] = float(min_hop)

        # Community matching
        if sender_state.community_id != -1 and receiver_state.community_id != -1:
            if sender_state.community_id == receiver_state.community_id:
                features["same_community"] = 1.0
            else:
                features["same_community"] = 0.0
        else:
            features["same_community"] = 0.0

        return features

    def update(self, txn: Dict[str, Any]) -> None:
        """
        Update graph state AFTER computing features for the transaction.
        """
        sender_vpa = str(txn["sender_vpa"])
        receiver_vpa = str(txn["receiver_vpa"])
        amount = float(txn["amount"])

        timestamp = txn["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        sender_state = self.get_or_create_account(sender_vpa)
        receiver_state = self.get_or_create_account(receiver_vpa)

        # Timestamps
        if sender_state.first_seen is None:
            sender_state.first_seen = timestamp
        sender_state.last_seen = timestamp

        if receiver_state.first_seen is None:
            receiver_state.first_seen = timestamp
        receiver_state.last_seen = timestamp

        # Degrees
        sender_state.out_degree = sender_state.out_degree + 1
        sender_state.total_out_amount = sender_state.total_out_amount + amount

        receiver_state.in_degree = receiver_state.in_degree + 1
        receiver_state.total_in_amount = receiver_state.total_in_amount + amount

        # Rolling deques (automatic bounded length)
        sender_state.recent_outbound.append((timestamp, amount, receiver_vpa))
        receiver_state.recent_inbound.append((timestamp, amount, sender_vpa))

        # Update adjacency
        self.adjacency[sender_vpa].add(receiver_vpa)
        self.adjacency[receiver_vpa].add(sender_vpa)

        # If either endpoint is flagged or near flagged, update hop sets
        if sender_vpa in self.flagged_accounts:
            self.hop1_flagged.add(receiver_vpa)
        elif sender_vpa in self.hop1_flagged:
            if receiver_vpa not in self.flagged_accounts and receiver_vpa not in self.hop1_flagged:
                self.hop2_flagged.add(receiver_vpa)

        if receiver_vpa in self.flagged_accounts:
            self.hop1_flagged.add(sender_vpa)
        elif receiver_vpa in self.hop1_flagged:
            if sender_vpa not in self.flagged_accounts and sender_vpa not in self.hop1_flagged:
                self.hop2_flagged.add(sender_vpa)

        # Add to NetworkX
        self.nx_graph.add_edge(sender_vpa, receiver_vpa)

    def run_community_detection(self) -> None:
        """
        Run fast connected components community detection.
        """
        if self.nx_graph.number_of_nodes() == 0:
            return

        try:
            components = nx.connected_components(self.nx_graph)
            for comp_idx, comp_nodes in enumerate(components):
                if len(comp_nodes) > 1:
                    for node_vpa in comp_nodes:
                        if node_vpa in self.accounts:
                            self.accounts[node_vpa].community_id = comp_idx
        except Exception:
            pass
