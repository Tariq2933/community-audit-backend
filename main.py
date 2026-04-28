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
    threads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(req.board, timeout=60000)

        # Wait for thread list to load
        page.wait_for_selector("a[href*='/questions-']", timeout=30000)

        # Collect thread links
        links = page.locator("a[href*='/questions-']").all()
        seen = set()

        for link in links:
            href = link.get_attribute("href")
            if href and href not in seen:
                seen.add(href)
                if href.startswith("/"):
                    href = "https://community.adobe.com" + href
                threads.append(href)

        browser.close()

    return {
        "status": "ok",
        "message": "Thread URLs extracted",
        "thread_count": len(threads),
        "threads": threads[:20],  # limit for now
        "input": req.model_dump()
    }


