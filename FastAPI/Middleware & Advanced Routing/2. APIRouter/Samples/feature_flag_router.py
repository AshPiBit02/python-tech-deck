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
from fastapi import FastAPI,APIRouter

app=FastAPI(title="Feature-Flagged Router Demo")

FEATURE_BETA_ANALYTICS=os.getenv("FEATURE_BETA_ANALYTICS","false").lower()=="true"

analytics_routes=APIRouter(prefix="/analytics",tags=["analytics"])

@analytics_routes.get("/summary")
def stable_summary():
    return {"page_views":10596,"unique_visitors":935}

if FEATURE_BETA_ANALYTICS:
    @analytics_routes.get("/beta-summary")
    def beta_summary():
        return {"cohort_retention":0.45,"experimental":True}

app.include_router(analytics_routes)