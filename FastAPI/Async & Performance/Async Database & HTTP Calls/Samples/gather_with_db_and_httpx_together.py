import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

async def get_user_by_id(db:AsyncSession,user_id:int): # dummy
    pass

async def get_enriched_user(db:AsyncSession,user_id:int):
    user_task=get_user_by_id(db,user_id) # async DB call
    async with httpx.AsyncClient() as client:
        avatar_task=client.get(f"https://api.example.com/avatar/{user_id}")
        user,avatar_response=await asyncio.gather(user_task,avatar_task)
    return {"user":user,"avatar_url":avatar_response.json().get("url")}