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

import traceback

@app.post("/run")
def run_audit(req: RunRequest):
    print("=== /run called ===")
    print("Input payload:", req.model_dump())

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process"
                ]
            )
            page = browser.new_page()

            thread_url = "https://community.adobe.com/questions-9/how-to-turn-off-grey-popups-when-hovering-over-images-1301933"
            print("Navigating to thread:", thread_url)

            page.goto(thread_url, timeout=60000)
            print("Page loaded")

            page.wait_for_selector("h1", timeout=30000)
            title = page.locator("h1").first.text_content().strip()
            print("Title:", title)

            name_locator = first_post.locator(
                ".lia-user-name, .lia-user-name-link, .lia-message-author"
            )
            op_name = (
                name_locator.first.text_content().strip()
                if name_locator.count() > 0
                else "UNKNOWN"
            )
            print("OP name:", op_name)

            role_locator = first_post.locator(
                ".lia-user-rank, .lia-user-role, .lia-user-label"
            )
            op_role = (
                role_locator.first.text_content().strip()
                if role_locator.count() > 0
                else "UNKNOWN"
            )
            print("OP role:", op_role)

            reply_count = page.locator(".lia-message-reply").count()
            print("Reply count:", reply_count)

            browser.close()
            print("Browser closed")

        return {
            "status": "ok",
            "message": "Thread parsed",
            "thread": {
                "thread_url": thread_url,
                "title": title,
                "op_name": op_name,
                "op_role_label": op_role,
                "reply_count": reply_count
            }
        }

    except Exception as e:
        print("=== EXCEPTION ===")
        traceback.print_exc()

        return {
            "status": "error",
            "message": "Backend exception caught",
            "error": str(e)
        }
