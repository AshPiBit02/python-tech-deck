import asyncio

async def works():
    await asyncio.sleep(1)
    return "OK"

async def fails():
    await asyncio.sleep(1)
    raise ValueError("Something broke")

async def result():
    result = await asyncio.gather(works(),fails(),return_exceptions=True)
    return result

print(asyncio.run(result()))