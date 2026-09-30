"""
PROBLEM: The same endpoint need to serve different formats to different
clients - a browser hitting the URL directly wants an HTML page, which'
your JS frontend or a third-party API consumer wants JSON. You don't want
two separate URLs for the same resources.

SOLUTION: Inspect the standard 'Accept' header on the Request object and 
branch the response format based on what the client asked for.
"""

from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse

app=FastAPI(title="Content Negotiation Demo")

STATUS={"service":"orders-api","healthy":True,"uptime_seconds":93211}

@app.get("/status")
def get_status(request:Request):
    accept=request.headers.get("accept","")
    if "text/html" in accept and "application/json" not in accept:
        rows="".join(f"<tr><td>{k}</td></tr>" for k,v in STATUS.items())
        html=f"<html><body><table>{rows}</table></body></html>"
        return HTMLResponse(content=html)
    return JSONResponse(content=STATUS)