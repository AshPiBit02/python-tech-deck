import asyncio,time

async def fetch_a():
    await asyncio.sleep(1)
    return "A"

async def fetch_b():
    await asyncio.sleep(1)
    return "B"

async def fetch_c():
    await asyncio.sleep(1)
    return "C"

async def sequential():
    start=time.perf_counter()
    a=await fetch_a()
    b=await fetch_b()
    c=await fetch_c()
    print(f"Sequential: {time.perf_counter()-start:.2f}s")
    print(f"{a} {b} {c}")

async def concurrent():
    start=time.perf_counter()
    a,b,c=await asyncio.gather(fetch_a(),fetch_b(),fetch_c())
    print(f"Gather: {time.perf_counter()-start:.2f}s")
    print(f"{a} {b} {c}")

asyncio.run(sequential())
asyncio.run(concurrent())