"""
PROBLEM: A checkout flow needs to reject out-of-stock items, but that check lives inside a shared
dependency (validate_cart) used by multiple routes. Without a central exception handler, each route
need to repeat the same try/except + error-formatting logic.

SOLUTION: Raise a custom exception type inside the shared dependency, and register ONE handler for
it -- every route using that dependency gets consistent error handling for free, regardless of how 
deep the exception was actually raised.
"""

from fastapi import FastAPI,Depends,Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app=FastAPI(title="Custom Exception Deep in Dependency Chain")

FAKE_STOCK={
    "in-stock-item":5,
    "sold-out-item":0,
}

class OutOfStockError(Exception):
    def __init__(self,product_id:str):
        self.product_id=product_id

class CheckOutResponse(BaseModel):
    product_id:str

class OrderResponse(BaseModel):
    product_id:str
    updated_stock:int

def validate_cart(order:CheckOutResponse)->CheckOutResponse:
    stock=FAKE_STOCK.get(order.product_id,0)
    if stock==0:
        raise OutOfStockError(order.product_id)
    FAKE_STOCK[order.product_id]=stock-1
    return order


@app.exception_handler(OutOfStockError)
async def handle_out_of_stock(request:Request,exc:OutOfStockError):
    return JSONResponse(
        status_code=409,
        content={"detail":f"Product '{exc.product_id}' is out of stock"},
    )

@app.post("/checkout")
def checkout(order:CheckOutResponse=Depends(validate_cart))->OrderResponse:
    return_order={
        "product_id":order.product_id,
        "updated_stock":FAKE_STOCK[order.product_id]
    }
    return OrderResponse(**return_order)