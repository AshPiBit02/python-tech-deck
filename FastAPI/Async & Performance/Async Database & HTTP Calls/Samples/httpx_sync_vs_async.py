import httpx

def sync_fetch(url:str):
    with httpx.Client() as client:
        return client.get(url).json()

async def async_fetch(url:str):
    async with httpx.AsyncClient() as client:
        response=client.get(url)
        return response.json()
