from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from database import FakeDBEngine,get_db_engine
from exceptions import InvalidCouponError,OrderNotFoundError
from models import Order,CreateOrder
from routers.inventory import reverse_stock
from routers.products import PRODUCTS_DB

router=APIRouter(prefix="/orders",tags=["Orders"])

ORDERS_DB:dict[int,Order]={}
next_id=1

VALID_COUPONS={"SAVE10":0.10,"SAVE20":0.20}

def Validate_coupon(code:str|None)->float:
    if code is None:
        return 0.0
    discount=VALID_COUPONS[code]
    if discount is None:
        raise InvalidCouponError(code=code)
    return discount

@router.post("/",response_model=Order,status_code=201)
def create_order(payload:CreateOrder,engine:FakeDBEngine=Depends(get_db_engine)):
    global next_id
    discount=Validate_coupon(payload.coupon_code)
    subtotal=0.0
    for item in payload.items:
        product=PRODUCTS_DB.get(item.product_id)
        if product is None:
            raise HTTPException(status_code=404,detail=f"Product {item.product_id} not found")
        
        reverse_stock(item.product_id,item.quantity)
        subtotal+=product.price*item.quantity
        total=round(subtotal*(1-discount),2)
        order=Order(
            id=next_id,
            items=payload.items,
            coupon_code=payload.coupon_code,
            total=total,
            created_at=datetime.now(timezone.utc),
        )
        ORDERS_DB[order.id]=order
        next_id+=1
        engine._data.setdefault("orders",[]).append(order.id)
        return order