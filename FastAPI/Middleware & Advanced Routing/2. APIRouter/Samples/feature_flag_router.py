"""
PROBLEM: You're rolling out a new "beta analytics" feature to only some environment
(or gradually to prod). You don't want the routes to exist at all - not even return 
a 403 - when the flag is off, because you don't want them discoverable via OpenAPI/
docs.

SOLUTION: Build the router conditionally at import time. If the flag is off, the 
routes are never registered - they 404 like they don't exists, and never appear 
in /docs.
"""

import os
from fastapi import FastAPI,HTTPException,APIRouter

app=FastAPI(title="Feature-Flagged Router Demo")

FEATURE_BETA_ANALYTIC=os.getenv("FEATURE_BETA_ANALYSICS","false").lower()=="true"

analytics_routes=APIRouter(prefix="/anaytics",tags=["analytics"])

@analytics_routes.get("/summary")
def stable_summary():
    return {"page_views":10596,"unique_visitors":935}

