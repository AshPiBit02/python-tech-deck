import time
import uuid
from datetime import datetime,timezone
from fastapi import FastAPI,BackgroundTasks,HTTPException

app=FastAPI(title="Report Generator")

CATEGORIES=["food","travel","bills"]
FAKE_TRANSACTIONS=[
    {"user_id":i%50,"amount":round((i*37.5)%500,2),"category":CATEGORIES[i%3]}
    for i in range(200_000)
]

REPORTS:dict[str,dict]={}

def generate_report(report_id:str,category_filter:str|None):
    try:
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
    except Exception as e:
        REPORTS[report_id].update({
            "status":"error",
            "eror_message":str(e),
        })

@app.post("/reports")
def request_report(background_tasks:BackgroundTasks,category:str|None=None):
    if category not in CATEGORIES:
        raise HTTPException(status_code=400,detail="No such category exists!")
    report_id=str(uuid.uuid4())
    REPORTS[report_id]={
        "status":"processing",
        "requested_at":datetime.now(timezone.utc).isoformat(),
        "category_filter":category,
    }
    background_tasks.add_task(generate_report,report_id,category)
    return {"report_id":report_id,"status":"processing","check_status_at":f"/reports/{report_id}"}

@app.get("/reports/{report_id}")
def get_report_status(report_id:str):
    report=REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404,detail="Report not found")
    return report