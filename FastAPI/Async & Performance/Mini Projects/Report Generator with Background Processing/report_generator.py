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
