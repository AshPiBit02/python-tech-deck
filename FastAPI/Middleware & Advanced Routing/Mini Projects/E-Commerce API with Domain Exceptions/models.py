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