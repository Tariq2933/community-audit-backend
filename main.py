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
    try:
        with sync_playwright() as p:
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

            # ✅ Open ONE known thread directly (fast + deterministic)
            thread_url = "https://community.adobe.com/questions-9/how-to-turn-off-grey-popups-when-hovering-over-images-1301933"
            page.goto(thread_url, timeout=60000)

            # ✅ Title (this always exists)
            page.wait_for_selector("h1", timeout=30000)
            title = page.locator("h1").first.text_content().strip()

            # ✅ Get first message container ONLY
            page.wait_for_selector(".lia-message-body", timeout=30000)
            first_post = page.locator(".lia-message-body").first

            # ✅ OP name — NON BLOCKING
            name_locator = first_post.locator(
                ".lia-user-name, .lia-user-name-link, .lia-message-author"
            )
            op_name = (
                name_locator.first.text_content().strip()
                if name_locator.count() > 0
                else "UNKNOWN"
            )

            # ✅ OP role — NON BLOCKING
            role_locator = first_post.locator(
                ".lia-user-rank, .lia-user-role, .lia-user-label"
            )
            op_role = (
                role_locator.first.text_content().strip()
                if role_locator.count() > 0
                else "UNKNOWN"
            )

            # ✅ Reply count — SAFE
            reply_count = page.locator(".lia-message-reply").count()

            browser.close()

        return {
            "status": "ok",
            "message": "Thread parsed without blocking",
            "thread": {
                "thread_url": thread_url,
                "title": title,
                "op_name": op_name,
                "op_role_label": op_role,
                "reply_count": reply_count
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Backend exception caught",
            "error": str(e)
        }

