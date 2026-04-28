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
    result = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Load board
        page.goto(req.board, timeout=60000)

        page.wait_for_selector(
            "a[href*='/questions-'], a[href*='/bugs-'], a[href*='/feature-requests-']",
            timeout=30000
        )

        # 2️⃣ Pick the FIRST thread only
        thread_link = page.locator(
            "a[href*='/questions-'], a[href*='/bugs-'], a[href*='/feature-requests-']"
        ).first

        thread_url = thread_link.get_attribute("href")
        if thread_url.startswith("/"):
            thread_url = "https://community.adobe.com" + thread_url

        # 3️⃣ Open thread
        page.goto(thread_url, timeout=60000)

        # 4️⃣ Extract title
        page.wait_for_selector("h1", timeout=30000)
        title = page.locator("h1").inner_text()

        # 5️⃣ Extract OP name
        op_name = page.locator(
            "[data-testid='author-name'], .lia-user-name"
        ).first.inner_text()

        # 6️⃣ Extract OP role label (Participant / Expert / Legend / Manager)
        role_locator = page.locator(
            ".lia-user-rank, .lia-user-role, .lia-user-label"
        ).first

        op_role = role_locator.inner_text() if role_locator.count() > 0 else "UNKNOWN"

        # 7️⃣ Count replies
        reply_count = page.locator(".lia-message-reply").count()

        browser.close()

        result = {
            "thread_url": thread_url,
            "title": title,
            "op_name": op_name,
            "op_role_label": op_role,
            "reply_count": reply_count
        }

    return {
        "status": "ok",
        "message": "Single thread extracted",
        "thread": result
    }

