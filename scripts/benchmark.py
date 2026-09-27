import asyncio
import aiohttp
import time
import argparse
import random
from rich.console import Console
from rich.table import Table

console = Console()

async def send_bid_request(session, url, publisher_id, slot_id, geo, category):
    payload = {
        "publisher_id": publisher_id,
        "slot_id": slot_id,
        "user_geo": geo,
        "page_category": category,
        "user_interests": [category]
    }
    start = time.time()
    try:
        async with session.post(url, json=payload) as response:
            res_json = await response.json()
            rt_time = (time.time() - start) * 1000
            return res_json, rt_time
    except Exception as e:
        return None, 0

async def run_benchmark(num_requests, concurrency, base_url, endpoint):
    url = f"{base_url}{endpoint}"
    console.print(f"[cyan]Running benchmark against {url}[/cyan]")
    
    geos = ['US', 'UK', 'IN', 'DE', 'CA']
    categories = ['tech', 'finance', 'gaming', 'health', 'news']
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bound_request():
            async with semaphore:
                pid = random.randint(1, 5)
                sid = (pid - 1) * 2 + random.randint(1, 2)
                geo = random.choice(geos)
                cat = random.choice(categories)
                return await send_bid_request(session, url, pid, sid, geo, cat)
                
        tasks = [bound_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
    return [r for r in results if r[0] is not None]

def calculate_stats(results):
    if not results:
        return {}
    latencies = [r[1] for r in results] # HTTP Round trip
    api_latencies = [r[0].get('latency_ms', 0) for r in results]
    hits = sum(1 for r in results if r[0].get('cache_hit', False))
    
    latencies.sort()
    
    def get_percentile(data, p):
        idx = int(len(data) * p)
        return data[idx]
        
    return {
        "min": min(latencies),
        "max": max(latencies),
        "mean": sum(latencies)/len(latencies),
        "median": get_percentile(latencies, 0.5),
        "p95": get_percentile(latencies, 0.95),
        "p99": get_percentile(latencies, 0.99),
        "hit_rate": (hits / len(results)) * 100
    }

async def main():
    parser = argparse.ArgumentParser(description="Benchmark Ad Bid Simulator")
    parser.add_argument("--requests", type=int, default=200, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency level")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL")
    args = parser.parse_args()

    console.print(f"[bold blue]Starting Benchmark[/bold blue]: {args.requests} requests, concurrency {args.concurrency}")
    
    # Run with cache
    cached_results = await run_benchmark(args.requests, args.concurrency, args.base_url, "/api/v1/bid")
    cached_stats = calculate_stats(cached_results)
    
    # Run without cache
    uncached_results = await run_benchmark(args.requests, args.concurrency, args.base_url, "/api/v1/bid/no-cache")
    uncached_stats = calculate_stats(uncached_results)
    
    table = Table(title="Benchmark Results (Latency in ms)")
    table.add_column("Metric", style="cyan")
    table.add_column("Cached", style="green")
    table.add_column("Uncached", style="red")
    
    metrics = ["min", "max", "mean", "median", "p95", "p99"]
    for m in metrics:
        table.add_row(m.upper(), f"{cached_stats.get(m, 0):.2f}", f"{uncached_stats.get(m, 0):.2f}")
        
    console.print(table)
    
    if cached_stats.get("mean", 0) > 0:
        speedup = uncached_stats.get("mean", 0) / cached_stats.get("mean", 1)
        console.print(f"[bold yellow]Speedup Factor:[/bold yellow] {speedup:.2f}x")
    console.print(f"[bold green]Cache Hit Rate:[/bold green] {cached_stats.get('hit_rate', 0):.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
