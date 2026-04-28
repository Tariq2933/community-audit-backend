from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(req.board, timeout=60000)
        title = page.title()
        browser.close()

    return {
        "status": "ok",
        "message": "Playwright page loaded successfully",
        "page_title": title,
        "input": req.model_dump()
    }

