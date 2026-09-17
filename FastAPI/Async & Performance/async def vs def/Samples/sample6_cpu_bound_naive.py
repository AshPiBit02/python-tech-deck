from fastapi import FastAPI

app=FastAPI()

@app.get("/bad-cpu")
async def bad_cpu_task(n:int):
    total=0
    for i in range(n*10_000_000):
        total+=i
    return {"total":total}

@app.get("/ok-cpu-sync")
def ok_cpu_task(n:int):
    total=0
    for i in range(n*10_000_000):
        total+=i
    return {"total":total}
