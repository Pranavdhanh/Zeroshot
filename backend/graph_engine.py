"""
UPI Shield AI — Graph Intelligence & Mule Account Detection
Track 4: FinTech & GovTech Intelligence

Uses NetworkX to model directed UPI transaction flows, detecting:
- Fan-In Hubs (Mule Aggregators)
- Fan-Out Dispersers (Layering Smurfs)
- Multi-Hop Transfer Chains (Rapid Pass-Through Layering)
- Node Network Risk for real-time transaction scoring
"""

from typing import List, Dict, Any, Tuple, Optional, Set
import networkx as nx
from datetime import datetime


class GraphIntelligenceEngine:
    def __init__(self):
        self.G = nx.DiGraph()
        self.analyzed_nodes: Dict[str, Dict[str, Any]] = {}
        self.analyzed_edges: List[Dict[str, Any]] = []

    def build_graph_from_transactions(self, transactions: List[Dict[str, Any]]) -> nx.DiGraph:
        """
        Builds a directed NetworkX graph from a list of transaction records.
        Aggregates multiple transfers between the same sender and recipient.
        """
        G = nx.DiGraph()

        for tx in transactions:
            u = tx["sender_id"]
            v = tx["recipient_id"]
            amt = float(tx["amount"])
            ts = tx.get("timestamp", datetime.utcnow().isoformat())
            risk = float(tx.get("risk_score", 0.0))

            # Initialize nodes if new
            if not G.has_node(u):
                G.add_node(u, total_in=0.0, total_out=0.0, tx_count=0)
            if not G.has_node(v):
                G.add_node(v, total_in=0.0, total_out=0.0, tx_count=0)

            G.nodes[u]["total_out"] += amt
            G.nodes[u]["tx_count"] += 1
            G.nodes[v]["total_in"] += amt
            G.nodes[v]["tx_count"] += 1

            if G.has_edge(u, v):
                G[u][v]["amount"] += amt
                G[u][v]["count"] += 1
                if ts > G[u][v]["last_timestamp"]:
                    G[u][v]["last_timestamp"] = ts
                G[u][v]["max_risk"] = max(G[u][v]["max_risk"], risk)
            else:
                G.add_edge(
                    u, v,
                    amount=amt,
                    count=1,
                    last_timestamp=ts,
                    max_risk=risk
                )

        self.G = G
        return G

    def detect_mule_patterns(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyzes the directed graph to identify explainable suspicious mule patterns.
        Carefully avoids false positives (not every high-degree node is a mule).
        """
        G = self.G
        nodes_result: List[Dict[str, Any]] = []
        edges_result: List[Dict[str, Any]] = []

        if len(G) == 0:
            return [], []

        # Find simple paths of length >= 3 for multi-hop layering detection
        mule_chain_nodes: Set[str] = set()
        for source in G.nodes():
            if G.in_degree(source) == 0 or G.out_degree(source) >= 1:
                # Find descendants up to depth 4
                for target in G.nodes():
                    if source != target and nx.has_path(G, source, target):
                        try:
                            for path in nx.all_shortest_paths(G, source, target):
                                if len(path) >= 4:  # At least 3 hops: A -> B -> C -> D
                                    # Intermediate nodes are potential pass-through mules
                                    intermediates = path[1:-1]
                                    for node in intermediates:
                                        t_in = G.nodes[node].get("total_in", 0.0)
                                        t_out = G.nodes[node].get("total_out", 0.0)
                                        # Pass-through characteristic: money in roughly equals money out
                                        if t_in > 0 and t_out > 0:
                                            retention_ratio = abs(t_in - t_out) / max(t_in, t_out)
                                            if retention_ratio < 0.25:  # Retains less than 25% of flow
                                                mule_chain_nodes.add(node)
                        except nx.NetworkXNoPath:
                            pass

        for node in G.nodes():
            in_deg = G.in_degree(node)
            out_deg = G.out_degree(node)
            t_in = round(float(G.nodes[node].get("total_in", 0.0)), 2)
            t_out = round(float(G.nodes[node].get("total_out", 0.0)), 2)

            role = "NORMAL"
            is_mule = False
            reasons: List[str] = []
            risk_score = 15.0  # Baseline normal risk

            # Rule 1: FAN-IN AGGREGATOR
            # Many distinct senders pooling funds into one account with minimal onward distribution
            if in_deg >= 4 and (out_deg == 0 or (in_deg / max(1, out_deg) >= 3.0)):
                role = "FAN_IN_AGGREGATOR"
                is_mule = True
                risk_score = min(95.0, 70.0 + (in_deg * 3.5))
                reasons.append(
                    f"Fan-In Aggregator: Receives funds from {in_deg} distinct senders with low onward dispersal"
                )

            # Rule 2: FAN-OUT DISPERSER
            # One account suddenly dispersing funds to many new recipients (smurfing / cashout)
            elif out_deg >= 4 and (in_deg <= 2 or (out_deg / max(1, in_deg) >= 3.0)):
                role = "FAN_OUT_DISPERSER"
                is_mule = True
                risk_score = min(92.0, 68.0 + (out_deg * 3.5))
                reasons.append(
                    f"Fan-Out Disperser: Rapidly dispersing funds to {out_deg} separate recipient accounts"
                )

            # Rule 3: MULTI-HOP CHAIN MULE
            elif node in mule_chain_nodes:
                role = "CHAIN_MULE"
                is_mule = True
                risk_score = 88.0
                reasons.append(
                    f"Multi-Hop Mule: Part of rapid {t_in:.0f} INR -> {t_out:.0f} INR transfer chain with <25% retention"
                )

            # Rule 4: High volume pass-through with few connections
            elif in_deg >= 1 and out_deg >= 1 and (t_in > 40000 or t_out > 40000):
                retention = abs(t_in - t_out) / max(t_in, t_out)
                if retention < 0.15:
                    role = "HIGH_RISK"
                    is_mule = True
                    risk_score = 78.0
                    reasons.append(
                        f"Suspicious Pass-Through: Rapid high-volume turnover (INR {t_in:,.0f} in, INR {t_out:,.0f} out)"
                    )
            else:
                reasons.append("Normal transaction activity within standard peer behavior limits")

            node_data = {
                "id": str(node),
                "label": str(node),
                "role": role,
                "risk_score": round(risk_score, 1),
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_in": t_in,
                "total_out": t_out,
                "is_mule": is_mule,
                "reasons": reasons
            }
            nodes_result.append(node_data)
            self.analyzed_nodes[str(node)] = node_data

        # Serialize directed edges
        for u, v, data in G.edges(data=True):
            edges_result.append({
                "source": str(u),
                "target": str(v),
                "amount": round(float(data.get("amount", 0.0)), 2),
                "count": int(data.get("count", 1)),
                "last_timestamp": str(data.get("last_timestamp", datetime.utcnow().isoformat()))
            })

        self.analyzed_edges = edges_result
        return nodes_result, edges_result

    def get_node_network_risk(self, account_id: str) -> float:
        """
        Returns estimated network risk feature (0.0 to 1.0) for real-time scoring.
        """
        if account_id in self.analyzed_nodes:
            node = self.analyzed_nodes[account_id]
            if node["is_mule"]:
                return min(1.0, node["risk_score"] / 100.0)
            return round(node["risk_score"] / 100.0, 2)
        return 0.10  # Default low baseline risk for previously unseen node


# Global singleton instance
graph_engine = GraphIntelligenceEngine()
