import httpx
import pandas as pd
import io

async def process_upload_csv(url:str):
    # I/O-bound: downloading the file
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        csv_bytes=response.content

    # CPU-bound: parsing and computing statistics
    df = pd.read_csv(io.BytesIO(csv_bytes))
    summary={
        "rows":len(df),
        "columns":list(df.columns),
        "mean_values":df.select_dtypes("number").mean().to_dict(),
    }
    return summary