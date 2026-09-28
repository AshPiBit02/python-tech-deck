"""
PROBLEM: After a deploy, EVERY route responds slower -- including routes
that share no dependencies with each other. Chasing this route-by-route 
wastes time, since the symptom's SCOPE already tells you where to look.

SOLUTION: A symptom affecting literally every route, regardless of which
dependencies each route uses, points at middleware -- since middleware is 
the only mechanism that runs for every single request unconditionally. This 
file deliberately includes a slow middleware and two unrealted routes,
to make that reasoning concrete rather than abstract.
"""

import time
from fastapi import FastAPI

app=FastAPI()

@app.middleware("http")
async def accidentally_slow_middleware(request,call_next):
    time.sleep(1) # simulatees an expensive, blocking setup step added by mistake
    response=await call_next(request)
    return response

@app.get("/cats")
def get_cats():
    return {"animals":["TOM","JERRY"]}

@app.get("/dogs")
def get_dogs():
    return {"animals":["Bob","Rocky"]}
