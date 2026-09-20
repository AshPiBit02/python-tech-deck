from fastapi import FastAPI,BackgroundTasks

app=FastAPI()

def send_confirmation_email(order_id:int):
    pass

async def update_inventory_async(order_id:int):
    pass

def notify_warehouse(order_id:int):
    pass

@app.post("/order")
def place_order(order_id:str,background_taks:BackgroundTasks):
    background_taks.add_task(send_confirmation_email,order_id)
    background_taks.add_task(update_inventory_async,order_id)
    background_taks.add_task(notify_warehouse,order_id)
    return {"status":"order placed"}