from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from database import lifespan
from exceptions import InvalidCouponError,OrderNotFoundError,OutStockError
from routers import inventory,orders,products

app=FastAPI(title="E-Commerce API",lifespan=lifespan)

@app.exception_handler(OutStockError)
async def out_of_stock_handler(reqest:Request,exc:OutStockError):
    return JSONResponse(
        status_code=409,
        content={
            "error":"out_of_stock",
            "product_id":exc.product_id,
            "requested":exc.requested,
            "available":exc.available,
            "detail":str(exc)
        },
    )

@app.exception_handler(InvalidCouponError)
async def invalid_coupon_handler(request:Request,exc:InvalidCouponError):
    return JSONResponse(
        status_code=400,
        content={
            "error":"invalid_coupon",
            "code":exc.code,
            "detail":str(exc)
        }
    )

@app.exception_handler(OrderNotFoundError)
async def order_not_found_handler(request:Request,exc:OrderNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error":"order_not_found",
            "order_id":exc.order_id,
            "detail":str(exc)
        }
    )

app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)

@app.get("/",tags=["meta"])
def roor():
    return {"message":"E-Commerce API running"}