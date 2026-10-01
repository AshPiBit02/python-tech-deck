"""
PROBLEM: A payment system has several distinct failure types that are all "payment-related" -- the
team wants a specific message for a couple of common cases, but doesn't want to write a handler for 
every possible payment failure that could ever exist.

SOLUTION: Befine a base exception type with a general handler, and more specific subclasses with
their own handlers. FastAPI matches the MOST SPECIFIC registered type first, falling back to the 
general one otherwise.
"""

from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse

app=FastAPI(title="Inheritance Matching DEMO")

class PaymentError(Exception):
    pass

class InsufficientFundsError(PaymentError):
    def __init__(self,account_id:str):
        self.account_id=account_id

class CardExpiredError(PaymentError):
    def __init__(self,card_last_four:str):
        self.card_last_four=card_last_four

@app.exception_handler(PaymentError)
def handle_generic_payment_error(request:Request,exc:PaymentError):
    return JSONResponse(
        status_code=402,
        content={"detail":"Payment failed!"}
    ) 

@app.exception_handler(InsufficientFundsError)
def handle_insufficient_funds(request:Request,exc:InsufficientFundsError):
    return JSONResponse(
        status_code=400,
        content={"detail":f"Account {exc.account_id} has insufficient funds!"},
    )

@app.exception_handler(CardExpiredError)
def handle_card_expired(request:Request,exc:CardExpiredError):
    return JSONResponse(
        status_code=402,
        content={"detail":"Card Expired!"}
    )

