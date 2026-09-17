from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI,Depends
import httpx

get_async_db="just for demonstaration"
User="dummy"

app=FastAPI()

@app.get("/user-profile/{user_id}")
async def get_enriched_profile(user_id:int,db:AsyncSession=Depends(get_async_db)):
    user= await db.get(User,user_id)

    async with httpx.AsyncClient() as client:
        avatar_response=await client.get(f"https://api.example.com/avatar/{user_id}")

    return {"user":user,"avatar":avatar_response.json()}