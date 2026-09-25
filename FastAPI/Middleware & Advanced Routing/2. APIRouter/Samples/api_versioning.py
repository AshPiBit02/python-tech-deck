"""
PROBLEM: You need to ship a breaking change to an endpoint without
breaking existing clients that are still calling the old version.

SOLUTION: Keep v1 and v2 as separate APIRouters with different prefixes,
mount both on the same app. Old clients keep working on /v1, new clients 
mirgrate to /v2 at their own pace. Retire /v1 later.
"""
from fastapi import FastAPI,APIRouter,HTTPException

app=FastAPI(title="Versoning Demo")

PRODUCTS={1:{"name":"Laptop","price":1699},
           2:{"name":"Phone","price":899},
           3:{"name":"SSD","price":499},}

v1=APIRouter(prefix="/v1/products",tags=["v1"])

@v1.get("/{product_id}")
def get_product_v1(product_id:int):
    p=PRODUCTS[product_id]
    if p is None:
        raise HTTPException(status_code=404,detail="Product not found!")
    return {"id":product_id,"name":p["name"],"price":p["price"]}

v2=APIRouter(prefix="/v2/products",tags=["v2"])

@v2.get("/{product_id}")
def get_product_v2(product_id:int):
    p=PRODUCTS.get(product_id)
    if p is None:
        raise HTTPException(status_code=404,detail="Product not found!")
    return {
        "id":product_id,
        "name":p["name"],
        "cost":{
            "amount":p["price"],
            "currency":"USD"
        },
    }

app.include_router(v1)
app.include_router(v2)