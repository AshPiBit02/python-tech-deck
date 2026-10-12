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

@app.post("/upload/csv/preview")
async def preview(file:UploadFile=File(...)):
    df = await read_csv(file)
    return df.head(10).fillna("").to_dict(orient="records")

@app.post("/upload/csv/filter")
async def filter(col:str,gt:float,file:UploadFile=File(...)):
    df =await read_csv(file)
    if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
        raise HTTPException(400,f"'{col}' must be an existing numeric column")
    return df[df[col]>gt].fillna("").to_dict(orient="records")