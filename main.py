from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RunRequest(BaseModel):
    board: str
    start_date: str
    end_date: str
    filter: str = "all"

@app.get("/")
def health_check():
    return {"status": "Backend is running"}

@app.post("/run")
def run_audit(req: RunRequest):
    return {
        "status": "ok",
        "message": "Request received",
        "input": req.model_dump()
    }
