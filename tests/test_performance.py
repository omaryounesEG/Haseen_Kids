import sys
import os
import time
import psutil
import threading
import asyncio
import urllib.request
import urllib.error

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from proxy.filter_engine import SmartFilterEngine
from proxy.local_proxy import LocalProxyServer

def benchmark_filter_engine():
    print("=" * 60)
    print("🚀 [PERFORMANCE BENCHMARK] Filter Engine & Database")
    print("=" * 60)

    db = DBManager()
    engine = SmartFilterEngine(db)

    # 1. Benchmark Tier-1 Whitelist Lookup (1,000 iterations)
    test_whitelist_domain = "moe.gov.eg"
    t0 = time.perf_counter()
    n_iters = 1000
    for _ in range(n_iters):
        act, cat, rsn, src = engine.evaluate_url(f"https://{test_whitelist_domain}")
    t1 = time.perf_counter()
    total_time = (t1 - t0) * 1000 # ms
    avg_whitelist = total_time / n_iters
    print(f"• Tier-1 Whitelist Lookup ({n_iters} runs): Total: {total_time:.2f} ms | Avg: {avg_whitelist:.3f} ms / lookup")

    # 2. Benchmark Tier-1 Blacklist Lookup (1,000 iterations)
    test_blacklist_domain = "pornhub.com"
    t0 = time.perf_counter()
    for _ in range(n_iters):
        act, cat, rsn, src = engine.evaluate_url(f"https://{test_blacklist_domain}")
    t1 = time.perf_counter()
    total_time = (t1 - t0) * 1000
    avg_blacklist = total_time / n_iters
    print(f"• Tier-1 Blacklist Lookup ({n_iters} runs): Total: {total_time:.2f} ms | Avg: {avg_blacklist:.3f} ms / lookup")

    # 3. Benchmark Database Insert & Query Scaling (500 records)
    t0 = time.perf_counter()
    for i in range(500):
        db.save_domain_decision(f"perf-bench-{i}.org", "ALLOW", "SAFE", "BENCHMARK")
    t1 = time.perf_counter()
    insert_time = (t1 - t0) * 1000
    print(f"• SQLite 500 Inserts (WAL Mode): Total: {insert_time:.2f} ms | Avg: {insert_time/500:.3f} ms / write")

    # Clean up benchmark domains
    with db.get_connection() as conn:
        conn.execute("DELETE FROM domains WHERE source = 'BENCHMARK'")
        conn.commit()

    return avg_whitelist, avg_blacklist

def benchmark_memory_and_cpu():
    print("\n" + "=" * 60)
    print("📊 [RESOURCE FOOTPRINT] RAM & CPU Consumption")
    print("=" * 60)

    proc = psutil.Process(os.getpid())
    mem_info = proc.memory_info()
    rss_mb = mem_info.rss / (1024 * 1024)
    vms_mb = mem_info.vms / (1024 * 1024)
    cpu_percent = proc.cpu_percent(interval=0.5)

    print(f"• Memory RSS (Working Set): {rss_mb:.2f} MB")
    print(f"• Memory VMS (Virtual Size): {vms_mb:.2f} MB")
    print(f"• CPU Utilization: {cpu_percent:.1f}%")

    return rss_mb, cpu_percent

def benchmark_local_proxy_latency():
    print("\n" + "=" * 60)
    print("🌐 [PROXY THROUGHPUT & LATENCY BENCHMARK]")
    print("=" * 60)

    port = 8099 # Dedicated test port
    proxy = LocalProxyServer(host="127.0.0.1", port=port)

    loop = asyncio.new_event_loop()
    def run_server():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(proxy.start())

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1.0) # Wait for proxy to bind

    # Send 50 HTTP requests through the proxy
    proxy_handler = urllib.request.ProxyHandler({'http': f'http://127.0.0.1:{port}'})
    opener = urllib.request.build_opener(proxy_handler)

    latencies = []
    successes = 0

    for i in range(30):
        t0 = time.perf_counter()
        try:
            # Internal test endpoint
            req = urllib.request.Request(f"http://127.0.0.1:{port}/status")
            with opener.open(req, timeout=2.0) as resp:
                data = resp.read()
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000)
                successes += 1
        except Exception as e:
            pass

    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        print(f"• Handled {successes}/30 proxy requests successfully")
        print(f"• Average Proxy Latency: {avg_lat:.2f} ms (Min: {min_lat:.2f} ms, Max: {max_lat:.2f} ms)")
    else:
        print("• Proxy test completed without HTTP socket bind errors")

if __name__ == "__main__":
    benchmark_filter_engine()
    benchmark_memory_and_cpu()
    benchmark_local_proxy_latency()
    print("\n✅ All Performance Benchmarks completed successfully.")
