from fastapi import FastAPI
import httpx

app=FastAPI()

# I/O-bound -> async def is correct here
@app.get("/external-data")
async def get_external_data():
    async with httpx.AsyncClient() as client:
        response=await client.get("https://jsonplaceholder.typicode.com/posts/1")
        return response.json()

# CPU-bound -> plain def is correct here (thread-pooled automatically)
@app.get("/compute-primes")
def compute_primes(limit:int=100_000):
    primes=[n for n in range(2,limit) if all(n % i !=0 for i in range(2,int(n**0.5)+1))]
    return {"count":len(primes)}