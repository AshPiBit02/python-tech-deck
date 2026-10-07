class OutStockError(Exception):
    def __init__(self,product_id:int,requested:int,available:int):
        self.product_id=product_id
        self.requested=requested
        self.available=available
        super.__init__(f"Product {product_id} out of stock: requested {requested}, available {available}")

class InvalidCouponError(Exception):
    def __init__(self,code:str,reason:str="Coupon is invalid or expired"):
        self.code=code
        self.reason=reason
        super().__init__(f"Invalid coupon '{code}': {reason}")

class OrderNotFoundError(Exception):
    def __init__(self,order_id:int):
        self.order_id=order_id
        super().___init__(f"Order {order_id} not found")
