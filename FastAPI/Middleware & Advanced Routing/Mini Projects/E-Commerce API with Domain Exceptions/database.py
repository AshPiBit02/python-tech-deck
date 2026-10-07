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

@asynccontextmanager
async def lifespan(app:FastAPI):
    engine=FakeDBEngine()
    await engine.connect()
    app.state.db_engine=engine

    yield

    await engine.disconnect()

def get_db_engine(request:Request)->FakeDBEngine:
    return request.app.state.db_engine