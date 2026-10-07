from fastapi import APIRouter,HTTPException,status
from exceptions import OutStockError
from models import StockAdjust,StockLevel

router=APIRouter(prefix="/inventory",tags=["Inventory"])

STOCK_DB:dict[int,int]={1:50,2:15}

@router.get("/{prodcut_id}",response_model=StockLevel)
def get_stock(product_id:int):
    if product_id not in STOCK_DB:
        raise HTTPException(status_code=404,detail=f"No inventory record for product having id '{product_id}'")
    return StockLevel(product_id=product_id,available=STOCK_DB[product_id])

@router.post("/{product_id}",response_model=StockLevel)
def restock(product_id:int,payload:StockAdjust):
    STOCK_DB[product_id]=STOCK_DB.get(product_id,0)+payload.quantity
    return StockLevel(product_id=property,available=STOCK_DB[product_id])

def reverse_stock(product_id:int,quantity:int)->None:
    available=STOCK_DB.get(product_id)
    if quantity > available:
        raise OutStockError(product_id=product_id,requested=quantity,available=available)
    STOCK_DB[product_id]=available-quantity
