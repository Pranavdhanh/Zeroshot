"""
Reproducible Latency Benchmark Script.

Measures end-to-end scoring path latency under load:
  - 100 TPS benchmark (500 transactions)
  - 500 TPS benchmark (1,000 transactions)
Reports:
  - p50, p95, p99, mean, and max latency in milliseconds.
Verifies prototype gate constraint: all p99 latency < 200 ms (target < 50 ms).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import numpy as np
import pandas as pd
from tabulate import tabulate

from service.scorer import RealTimeScorer


def run_latency_benchmark():
    """Run end-to-end latency benchmark."""
    print("=" * 60)
    print("PHASE 5: SCORING LATENCY BENCHMARK (100 & 500 TPS)")
    print("=" * 60)

    print("\n[1/3] Initializing Real-Time Scorer...")
    scorer = RealTimeScorer()

    # Load real test stream samples from parquet
    df = pd.read_parquet("data/transactions.parquet")
    sample_records = df.tail(2000).to_dict("records")
    print(f"  Loaded {len(sample_records)} transaction payloads for benchmarking")

    # Warmup
    print("  Warming up inference engine & JIT compiler...")
    for i in range(50):
        scorer.score_transaction(sample_records[i])
    scorer.latency_history.clear()

    benchmarks = [
        {"name": "100 TPS Stream Benchmark", "target_tps": 100, "count": 500},
        {"name": "500 TPS High-Load Benchmark", "target_tps": 500, "count": 1000},
    ]

    results_table = []
    saved_data = {}

    for b in benchmarks:
        name = b["name"]
        target_tps = b["target_tps"]
        count = b["count"]

        print(f"\n[Running {name}] ({count} transactions at {target_tps} TPS pace)...")
        latencies = []
        interval = 1.0 / float(target_tps)

        t_bench_start = time.perf_counter()
        for idx in range(count):
            txn = sample_records[idx % len(sample_records)]

            t0 = time.perf_counter()
            scorer.score_transaction(txn)
            t1 = time.perf_counter()
            lat_ms = (t1 - t0) * 1000.0
            latencies.append(lat_ms)

            # Pace regulation to simulate streaming arrival
            elapsed = time.perf_counter() - t0
            if elapsed < interval:
                time.sleep(interval - elapsed)

        total_wall_time = time.perf_counter() - t_bench_start
        achieved_tps = count / total_wall_time

        lat_arr = np.array(latencies)
        p50 = float(np.percentile(lat_arr, 50))
        p95 = float(np.percentile(lat_arr, 95))
        p99 = float(np.percentile(lat_arr, 99))
        mean_lat = float(np.mean(lat_arr))
        max_lat = float(np.max(lat_arr))

        gate_passed = p99 < 200.0
        target_passed = p99 < 50.0

        status = "PASS (<50ms)" if target_passed else ("PASS (<200ms)" if gate_passed else "FAIL")

        results_table.append([
            name,
            f"{achieved_tps:.1f}",
            f"{mean_lat:.2f} ms",
            f"{p50:.2f} ms",
            f"{p95:.2f} ms",
            f"{p99:.2f} ms",
            f"{max_lat:.2f} ms",
            status,
        ])

        saved_data[str(target_tps)] = {
            "name": name,
            "target_tps": target_tps,
            "achieved_tps": achieved_tps,
            "count": count,
            "mean_ms": mean_lat,
            "p50_ms": p50,
            "p95_ms": p95,
            "p99_ms": p99,
            "max_ms": max_lat,
            "status": status,
        }

    print("\n" + "=" * 60)
    print("LATENCY BENCHMARK RESULTS")
    print("=" * 60)
    headers = ["Benchmark", "Actual TPS", "Mean", "p50", "p95", "p99", "Max", "Gate Check"]
    print(tabulate(results_table, headers=headers, tablefmt="grid"))

    # Save benchmark artifacts
    os.makedirs("eval", exist_ok=True)
    with open("eval/latency_results.json", "w") as f:
        json.dump(saved_data, f, indent=2)
    print("\n  Saved benchmark metrics to eval/latency_results.json")

    print("\n" + "=" * 60)
    print("PHASE 5 GATE CHECK: COMPLETE")
    print("=" * 60)
    return saved_data


if __name__ == "__main__":
    run_latency_benchmark()
