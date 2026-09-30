"""
PROBLEM: You need to return an absolute URL to the client (e.g. a password-reset link
, or a "Location" header after creating a resource). request.base_url naively gives you 
the schema/host FastAPI itself sees - but behind a reverse proxy (nginx, an ALB) termin-
-ating TLS, the app often only sees plain "http://" internally even though the real 
public site is "https://", and the Host header may be the internal serivce name, not the
public domain. Links generated this way are broken.

SOLUTION: Respect the standard forwarded headers (X-Forwarded-Proto, X-Forwarded-Host) 
that reverse proxies set, and use them to build the correct public-fetching URL instead
of trusting request.base_url blindly.
"""

from fastapi import FastAPI,Request

app=FastAPI(title="Reverse Proxy URL Building Demo")

def get_public_base_url(request:Request)->str:
    proto=request.headers.get("x-forwarded-proto",request.url.scheme)
    host=request.headers.get("x-forwarded-host",request.headers.get("host",request.url.netloc))
    return f"{proto}://{host}"

@app.get("/reset-link")
def generate_reset_link(request:Request):
    base_url=get_public_base_url(request)
    token="abc569"
    return {"reset_url":f"{base_url}/reset-password?token={token}"}