from datetime import datetime
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name:str
    price:float

class Product(ProductCreate):
    id:int

class StockAdjust(BaseModel):
    quantity:int

class StockLevel(BaseModel):
    product_id:int
    available:int

class OrderItem(BaseModel):
    product_id:int
    quantity:int

class CreateOrder(BaseModel):
    items:list[OrderItem]
    coupon_code:str|None=None

class Order(BaseModel):
    id:int
    items:list[OrderItem]
    coupon_code:str|None
    total:float
    created_at:datetime