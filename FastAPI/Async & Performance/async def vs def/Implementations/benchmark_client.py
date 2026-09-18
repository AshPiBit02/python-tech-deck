import httpx
import time

BASE_URL="http://127.0.0.1:8000"
CONCURRENT_REQUESTS=3

def benchmark_route(path:str,label:str):
    print(f"\n---- {label} ----")
    start=time.perf_counter()

    with httpx.Client(timeout=30) as client:
        responses=[]
        for _ in range(CONCURRENT_REQUESTS):
            responses.append(client.get(f"{BASE_URL}{path}"))

    elapsed=time.perf_counter()-start
    print(f"{CONCURRENT_REQUESTS} sequentiall client-side calls took {elapsed:.2f}s total")
    return elapsed

def benchmark_route_truly_concurrent(path:str,label:str):
    import asyncio
    async def _run():
        async with httpx.AsyncClient(timeout=30) as client:
            start=time.perf_counter()
            tasks=[client.get(f"{BASE_URL}{path}") for _ in range(CONCURRENT_REQUESTS)]
            await asyncio.gather(*tasks)
            elapsed = time.perf_counter() - start
            print(f"\n--- {label} ({path}) — {CONCURRENT_REQUESTS} TRUE concurrent requests ---")
            print(f"Total time: {elapsed:.2f}s")
            return elapsed
 
    return asyncio.run(_run())
 
 
if __name__ == "__main__":
    print("=" * 60)
    print("Sending 3 CONCURRENT requests to each route, measuring total time")
    print("If the server handles them concurrently, total time stays ~2s.")
    print("If the server blocks, total time grows to ~6s (2s x 3, serialized).")
    print("=" * 60)
 
    benchmark_route_truly_concurrent("/bad-async", "BAD async (time.sleep inside async def)")
    benchmark_route_truly_concurrent("/good-async", "GOOD async (asyncio.sleep inside async def)")
    benchmark_route_truly_concurrent("/sync-blocking", "SYNC route (auto thread-pooled)")
 
    print("\n" + "=" * 60)
    print("Expected results:")
    print("  bad-async       -> ~6s  (blocks the event loop, requests serialize)")
    print("  good-async      -> ~2s  (event loop free, requests run concurrently)")
    print("  sync-blocking   -> ~2s  (thread pool isolates each blocking call)")
    print("=" * 60)
 