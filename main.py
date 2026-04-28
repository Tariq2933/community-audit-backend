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

        # ✅ Directly open a known thread (fast, no board crawl)
        thread_url = "https://community.adobe.com/questions-9/how-to-turn-off-grey-popups-when-hovering-over-images-1301933"

        page.goto(thread_url, timeout=60000)

        page.wait_for_selector("h1", timeout=30000)
        title = page.locator("h1").inner_text()

        op_name = page.locator(
            "[data-testid='author-name'], .lia-user-name"
        ).first.inner_text()

        role_locator = page.locator(
            ".lia-user-rank, .lia-user-role, .lia-user-label"
        ).first

        op_role = role_locator.inner_text() if role_locator.count() > 0 else "UNKNOWN"

        reply_count = page.locator(".lia-message-reply").count()

        browser.close()

    return {
        "status": "ok",
        "message": "Thread page loaded (safe mode)",
        "thread": {
            "thread_url": thread_url,
            "title": title,
            "op_name": op_name,
            "op_role_label": op_role,
            "reply_count": reply_count
        }
    }

