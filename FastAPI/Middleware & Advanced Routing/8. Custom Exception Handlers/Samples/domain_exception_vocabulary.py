"""
PROBLEM: A banking-syly service function need to signal "insufficient funds" -- but
service/business logic shouldn't need to know about HTTP status codes or JSONResponse,
that's a web-layer concern, not a domain one.

SOLUTION: Raise a plain, custom Python exception carrying structured data. The service
function stays HTTP-agnostic, ONE registered handler does the translation to an actual
HTTP response, in exactly one place.
"""

from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app=FastAPI(title="Domain Exception Vocabulary DEMO")

FAKE_BALANCES={
    "acc1":10.25,
    "acc2":106.00,
    "acc3":99.5,
}

class InsufficientFundsError(Exception):
    def __init__(self,accound_id:str,shortfall:float):
        self.account_id=accound_id
        self.shortfall=shortfall

def withdraw_from_account(account_id:str,amount:float):
    balance=FAKE_BALANCES.get(account_id,0)
    if amount>balance:
        raise InsufficientFundsError(account_id,amount-balance)
    FAKE_BALANCES[account_id]-=amount
    return FAKE_BALANCES[account_id]


