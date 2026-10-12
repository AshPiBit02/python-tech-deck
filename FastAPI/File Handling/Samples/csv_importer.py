import io
import pandas as pd
from fastapi import FastAPI,File,HTTPException,UploadFile

app=FastAPI(title="CSV import")

async def read_csv(file:UploadFile)->pd.DataFrame:
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400,"Only .csv files allowed")
    try:
        return pd.read_csv(io.BytesIO(await file.read()))
    except Exception:
        raise HTTPException(400,"Could not parse CSV")

@app.post("/upload/csv")
async def summary(file:UploadFile=File(...)):
    df=await read_csv(file)
    return {"rows":len(df),"columns":list(df.columns),"nulls":df.isnull().sum().to_dict()}
