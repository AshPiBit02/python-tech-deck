import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI,Request

class FakeDBEngine:
    def __init__(self):
        self.connected=False
        self.data:dict[str,list]={}

    async def connect(self):
        await asyncio.sleep(0)
        self.connected=True
        print("[DB] engine connected")

    async def disconnect(self):
        await asyncio.sleep(0)
        self.connected=False
        print("[DB] engine disconnected")

