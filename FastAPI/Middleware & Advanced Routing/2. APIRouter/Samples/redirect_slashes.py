"""
A client may call a route with trailing slash. By default FastAPI redirects this automatically
so the request still succeeds -- but sometimes(e.g. two routes that must be treaded as genuinely
different path) we want that automatic redirect turned off instead.
"""
from fastapi import FastAPI,APIRouter

app=FastAPI(title="Redirect Slashes",redirect_slashes=False)

redirect_false=APIRouter(prefix="/redirect-false")

@redirect_false.get("/products")
def get_products():
    return {"result":["shoes","jackets","pants"],
            "info":"No trailing slash allowed here"}
app.include_router(redirect_false)