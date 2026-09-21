import asyncio
import time
from datetime import datetime,timezone

import httpx
from fastapi import FastAPI,BackgroundTasks,Query

app=FastAPI(title="Multi-Source Dashboard Aggregator")

REQUEST_LOGS:list[dict]=[]

def log_dashboard_request(sources_succeeded:list[str],sources_failed:list[str],total_time:float):
    REQUEST_LOGS.append({
        "succeeded":sources_succeeded,
        "failed":sources_failed,
        "total_time_seconds":round(total_time,3),
        "timestamp":datetime.now(timezone.utc).isoformat(),
    })