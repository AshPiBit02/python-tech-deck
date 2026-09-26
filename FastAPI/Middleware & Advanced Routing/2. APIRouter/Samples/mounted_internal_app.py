"""
PROBLEM: We have internal-only endpoints(health checks, DB pool stats, features-flag toggles
for ops) that should NEVER appear in the customer-facing API docs, and ideally should be 
reachable only from the internal network / a different auth mechanism entirely.

SOLUTION: inlclude_router() merges routes into the SAME OpenAPI schema as everything else -
not what we want here. Instead, we build a second, fully separate FastAPI() app and app.mount()
it at a path. It gets its own docs page and scheme, totally decoupled from the public API.
"""
from fastapi import FastAPI,APIRouter

app=FastAPI(title="Public Customer API")

@app.get("/products",tags=["public"])
def list_products():
    return [
        {"id":1,"item":"Laptop"},
        {"id":2,"item":"GPU"},
        {"id":3,"item":"Jacket"},
    ]

