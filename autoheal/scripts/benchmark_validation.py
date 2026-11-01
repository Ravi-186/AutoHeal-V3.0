import os
import sys
import time
import json
import sqlite3
import numpy as np
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from server import app
from src.appsec.models import (
    record_security_event, upsert_security_incident, get_security_events,
    is_client_blocked, block_client_ip, unblock_client_ip
)
from src.appsec.detector import AppSecDetector, DetectionResult
from src.appsec.responder import AppSecResponder
from src.appsec.verifier import AppSecVerifier
from shopsphere.services import ProductService, CartService, OrderService, UserService
from shopsphere.database import get_db_connection

client = TestClient(app)

def calc_stats(latencies_ms):
    arr = np.array(latencies_ms)
    return {
        "count": len(arr),
        "min_ms": round(float(np.min(arr)), 3),
        "median_ms": round(float(np.median(arr)), 3),
        "p95_ms": round(float(np.percentile(arr, 95)), 3),
        "p99_ms": round(float(np.percentile(arr, 99)), 3),
        "max_ms": round(float(np.max(arr)), 3),
        "avg_ms": round(float(np.mean(arr)), 3),
        "std_ms": round(float(np.std(arr)), 3)
    }

def benchmark_all():
    results = {}
    print("--- Starting AutoHeal v2.5.0 Production Performance Benchmarking ---")

    from src.appsec.middleware import AppSecProtectionMiddleware
    AppSecProtectionMiddleware._rate_tracker.clear()

    # 1. API Response Latency (GET /api/shop/products)
    print("Benchmarking GET /api/shop/products...")
    api_latencies = []
    for i in range(100):
        t0 = time.perf_counter()
        resp = client.get("/api/shop/products", headers={"X-Forwarded-For": f"192.168.{i // 10}.{i % 10 + 1}"})
        t1 = time.perf_counter()
        if resp.status_code == 200:
            api_latencies.append((t1 - t0) * 1000)
    results["api_products_list"] = calc_stats(api_latencies)

    # 2. API Response Latency (GET /api/shop/products/1)
    print("Benchmarking GET /api/shop/products/1...")
    api_single_latencies = []
    for i in range(100):
        t0 = time.perf_counter()
        resp = client.get("/api/shop/products/1", headers={"X-Forwarded-For": f"192.168.{i // 10}.{i % 10 + 1}"})
        t1 = time.perf_counter()
        if resp.status_code == 200:
            api_single_latencies.append((t1 - t0) * 1000)
    results["api_product_detail"] = calc_stats(api_single_latencies)

    # 3. Security Event Ingestion Latency
    print("Benchmarking Telemetry Event Ingestion...")
    ingest_latencies = []
    for i in range(100):
        t0 = time.perf_counter()
        record_security_event(
            client_ip="192.168.1.100",
            method="GET",
            path="/api/shop/benchmark",
            status_code=200,
            event_type="BENCHMARK_PROBE",
            severity="INFO",
            correlation_id=f"bench-{i}"
        )
        t1 = time.perf_counter()
        ingest_latencies.append((t1 - t0) * 1000)
    results["event_ingestion"] = calc_stats(ingest_latencies)

    # 4. Detection Processing Latency (AppSecDetector.analyze_live_request)
    print("Benchmarking Detection Processing Latency...")
    det_latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        AppSecDetector.analyze_live_request(
            client_ip="198.51.100.55",
            method="GET",
            path="/api/shop/products",
            query_string="q=laptop%27%20OR%20%271%27=%271"
        )
        t1 = time.perf_counter()
        det_latencies.append((t1 - t0) * 1000)
    results["detection_processing"] = calc_stats(det_latencies)

    # 5. Incident Creation Latency
    print("Benchmarking Incident Creation Latency...")
    incident_latencies = []
    dummy_det = DetectionResult(
        triggered=True,
        rule_id="INJ-001",
        category="Injection",
        severity="HIGH",
        confidence=0.98,
        summary="Benchmark SQLi incident creation",
        evidence={"target": "/api/shop/products", "client_ip": "198.51.100.55"}
    )
    last_inc_id = None
    for i in range(100):
        t0 = time.perf_counter()
        inc_id = upsert_security_incident(
            rule_id="INJ-001",
            title=f"Benchmark Incident {i}",
            category="Injection",
            severity="HIGH",
            summary="Benchmark SQLi incident creation",
            source_ip=f"198.51.100.{i % 250}",
            evidence={"target": "/api/shop/products", "payload": "1' OR '1'='1"},
            affected_endpoints=["/api/shop/products"],
            impact_actual="Attempted SQLi",
            impact_potential="Data exfiltration",
            mitigation_actions=[{"action": "BLOCK_IP", "target": f"198.51.100.{i % 250}"}],
            confidence=0.98
        )
        t1 = time.perf_counter()
        last_inc_id = inc_id
        incident_latencies.append((t1 - t0) * 1000)
    results["incident_creation"] = calc_stats(incident_latencies)

    # 6. Remediation Execution Latency
    print("Benchmarking Remediation Execution Latency...")
    remed_latencies = []
    for i in range(50):
        t0 = time.perf_counter()
        AppSecResponder.execute_defensive_mitigation(dummy_det)
        t1 = time.perf_counter()
        remed_latencies.append((t1 - t0) * 1000)
    results["remediation_execution"] = calc_stats(remed_latencies)

    # 7. Verification Latency
    print("Benchmarking Verification Latency...")
    verif_latencies = []
    # Ensure client IP is quarantined for incident
    block_client_ip("198.51.100.55", reason="Benchmark", rule_id="INJ-001")
    for i in range(30):
        t0 = time.perf_counter()
        AppSecVerifier.verify_incident_containment(
            incident_id=last_inc_id,
            test_client=client
        )
        t1 = time.perf_counter()
        verif_latencies.append((t1 - t0) * 1000)
    unblock_client_ip("198.51.100.55")
    results["verification_execution"] = calc_stats(verif_latencies)

    # 8. Database Query Latency (Indexed Product Lookup)
    print("Benchmarking Database Indexed Query...")
    db_latencies = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for _ in range(100):
            t0 = time.perf_counter()
            cursor.execute("SELECT * FROM products WHERE id = 1;")
            _ = cursor.fetchone()
            t1 = time.perf_counter()
            db_latencies.append((t1 - t0) * 1000)
    results["db_indexed_query"] = calc_stats(db_latencies)

    # 9. Multi-Threaded Concurrency Throughput
    print("Benchmarking Multi-Threaded Throughput (10 concurrent workers, 200 requests)...")
    t0_c = time.perf_counter()
    def fetch_job(idx):
        return client.get(f"/api/shop/products?q=item{idx%5}", headers={"X-Forwarded-For": f"10.50.{idx//10}.{idx%10 + 1}"}).status_code
    with ThreadPoolExecutor(max_workers=10) as executor:
        statuses = list(executor.map(fetch_job, range(200)))
    t1_c = time.perf_counter()
    duration = t1_c - t0_c
    throughput_rps = round(200 / duration, 2)
    results["concurrency"] = {
        "total_requests": 200,
        "concurrency_level": 10,
        "duration_seconds": round(duration, 3),
        "throughput_rps": throughput_rps,
        "success_rate": round(sum(1 for s in statuses if s == 200) / 200 * 100, 2)
    }

    # Print summary JSON
    print("\n================ BENCHMARK RESULTS (JSON) ================")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    benchmark_all()
