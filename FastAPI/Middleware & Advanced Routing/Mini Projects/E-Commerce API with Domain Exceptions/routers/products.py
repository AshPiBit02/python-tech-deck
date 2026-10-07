from fastapi import APIRouter,HTTPException
from models import Product,ProductCreate

router=APIRouter(prefix="/products",tags=["Products"])

PRODUCTS_DB:dict[int,Product]={
    1:Product(id=1,name="Wireless Mouse",price=29.36),
    2:Product(id=2,name="MacBook Pro M5",price=1699.00),
}
next_id=3

@router.get("/",response_model=list[Product])
def list_products():
    return list(PRODUCTS_DB.values())

@router.get("/{product_id}",response_model=Product)
def get_product(product_id:int):
    product=PRODUCTS_DB.get(product_id)
    if product is None:
        raise HTTPException(status_code=404,detail="Product not found")
    return product

@router.post("/",response_model=Product,status_code=201)
def create_product(payload:ProductCreate):
    global next_id
    product=Product(id=next_id,**payload.model_dump())
    PRODUCTS_DB[product.id]=product
    next_id+=1
    return product