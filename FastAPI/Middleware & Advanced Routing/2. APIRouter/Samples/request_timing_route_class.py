"""
PROBLEM: You need every response from a given router to carry a request ID and 
response-time header (for tracking/debugging in production), without pasting 
timing/logging code into every single endpoint function.

SOLUTION: Subclass APIRoute and set it as the router's route_class. The wrapping
logic runs for every route automatically.
"""

import time
import uuid
from typing import Callable
from fastapi import FastAPI,Header,APIRouter,Request,Response
from fastapi.routing import APIRoute

app=FastAPI(title="Custom APIRoute Timing Demo")

class TimedRoute(APIRoute):
    def get_route_handler(self)->Callable:
        original_handler=super().get_route_handler()

        async def timed_handler(request:Request)->Response:
            request_id=str(uuid.uuid4())
            start=time.perf_counter()
            response=await original_handler(request)
            duration_ms=(time.perf_counter()-start)*1000

            response.headers["X-Request_ID"]=request_id
            response.headers["X-Response-Time-ms"]=f"{duration_ms:.2f}"
            print(f"[{request_id}] {request.method} {request.url.path} -> {duration_ms:.2f}ms")
            return response
        
        return timed_handler

orders_router=APIRouter(prefix="/orders",tags=["orders"],route_class=TimedRoute)

@orders_router.get("/{order_id}")
def get_order(order_id:int):
    return {"order_id":order_id,"status":"shipped"}

app.include_router(orders_router)