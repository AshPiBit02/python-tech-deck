"""
The 'responses' paramter at the route level lets explicitly define the 
possible HTTP responses that endpoint can return, along with their status
codes, description, and example payloads.(Mainly for doucmentation and
OpenAPI schema generation.)
"""

from fastapi import FastAPI,HTTPException

FAKE_PRODUCTS={"1":"MacBook Pro","2":"Electric Bike"}

app=FastAPI(title="Responses Route Demo")

@app.get("/products/{product_id}",
         responses={
             404:{"description":"Product not found",
                  "content":{"application/json":
             {"example":{"detail":"Product not found"}
             }}},
         },)
def get_product(product_id:str):
    if product_id not in FAKE_PRODUCTS:
        raise HTTPException(status_code=404,detail="Prouduct not found")
    return {"product_id":product_id,"name":FAKE_PRODUCTS[product_id]}


