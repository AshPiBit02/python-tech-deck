import httpx

async def featch_user_data(user_id:int):
    async with httpx.AsyncClient() as client:
        response=await client.get(f"https://jsonplaceholder.typicode.com/users/{user_id}")
        return response.json()
    