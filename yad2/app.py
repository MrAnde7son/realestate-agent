from fastapi import FastAPI, Request, HTTPException
import os

app = FastAPI()
TOKEN = os.environ.get("DOWNSTREAM_API_KEY", "")

@app.middleware("http")
async def require_token(request: Request, call_next):
    if TOKEN:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)

@app.get("/")
def health():
    return {"ok": True}
