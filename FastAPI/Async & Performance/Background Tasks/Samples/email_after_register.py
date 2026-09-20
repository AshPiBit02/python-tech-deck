from fastapi import BackgroundTasks,FastAPI

app=FastAPI()

def log_to_file(message:str):
    with open("events.log","a") as f:
        f.write(message+"\n")

@app.post("/register")
def register(email:str,backgound_tasks:BackgroundTasks):
    backgound_tasks.add_task(log_to_file,f"New registration: {email}")
    return {"message":"Registered"}