"""
PROBLEM: Verifying a webhook signature (Stripe, GitHub, Shopify-style) requires
HMAC-hashing the EXACT raw bytes the sender signed. If we declare a Pydantic model 
as our parameter, FastAPI parses JSON first and we lose access to the original raw
bytes - re-serializing the parsed dict rarely produces byte-identical output, so 
signature fail.

SOLUTION: Take the Request object directly and call 'await request.body()' to get
the raw bytes BEORE any parsing happens. Verify the signature against those exact
bytes, then parse JSON only after verification succeeds.
"""

import hashlib
import hmac
import json

from fastapi import FastAPI,HTTPException,Request,status

app=FastAPI(title="Webhook Signature Verification Demo")

WEBHOOK_SECRET=b"whsec_test_secret"

@app.post("/webhooks/payment")
async def handle_payment_webhook(request:Request):
    raw_body=await request.body()
    signature=request.headers.get("x-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature",
        )

    expected_signature=hmac.new(WEBHOOK_SECRET,raw_body,hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature,expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    payload=json.loads(raw_body)
    return {"received":True,"event":payload.get("event")}