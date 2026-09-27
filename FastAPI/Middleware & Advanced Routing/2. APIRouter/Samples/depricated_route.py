"""
When we change old feature and made new one better, we won't deleted the old one,
we mark the old as depricated so that old client can still use but mark the route
as depricated so that it will be visibly marked in view.
"""

from fastapi import FastAPI,APIRouter

app=FastAPI(title="Depricated Route demo")

v1=APIRouter(prefix="/v1",deprecated=True)

v2=APIRouter(prefix="/v2")

@v1.get("/sales-stats")
def get_sales_info():

    return {
        "total_sales":595265.36,
        "customer_traffic":9683,
        "average_sales_per_customer":569.3,
    }

@v2.get("/sales-stats")
def get_sales_info():
    return{
         "total_sales":595265.36,
         "customer_traffic":9683,
         "most_sold_category":"Electronics",
         "avg_reviews":4.6
    }

app.include_router(v1)
app.include_router(v2)