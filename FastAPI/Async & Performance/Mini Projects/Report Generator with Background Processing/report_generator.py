import time
import uuid
from datetime import datetime,timezone
from fastapi import FastAPI,BackgroundTasks,HTTPException

APP=FastAPI(title="Report Generator")

FAKE_TRANSACTIONS=[
    {"user_id":i%50,"amount":round((i*37.5)%500,2),"category":["flood","travel","bills"][i%3]}
    for i in range(200_000)
]

REPORTS:dict[str,dict]={}

def generate_report(report_id:str,category_filter:str|None):
    start=time.perf_counter()

    relevant=[t for t in FAKE_TRANSACTIONS if category_filter is None or t["category"]==category_filter]
    total=sum(t["amount"] for t in relevant)
    by_user:dict[int,float]={}
    for t in relevant:
        by_user[t["user_id"]]=by_user.get(t["user_id"],0)+t["amount"]

    top_spenders=sorted(by_user.items(),key=lambda x: x[1],reverse=True)[:5]
    elapsed=time.perf_counter()-start

    REPORTS[report_id].update({
        "status":"ready",
        "completed_at":datetime.now(timezone.utc).isoformat(),
        "computation_seconds":round(elapsed,3),
        "result":{
            "transaction_count":len(relevant),
            "total_amount":round(total,2),
            "top_5_spenders":[{"user_id":uid,"total":round(amt,2)} for uid,amt in top_spenders],
        },
    })