from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

app = FastAPI()



# ----------------------------
# Request model
# ----------------------------
class RunRequest(BaseModel):
    board: str
    start_date: str
    end_date: str
    filter: str = "all"

# ----------------------------
# Health check
# ----------------------------


@app.get("/")
def health_check():
    return {"status": "Backend is running"}

import traceback


# ----------------------------
# Main run endpoint
# ----------------------------

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

            # ✅ Load ONE known thread (safe + fast)
            thread_url = "https://community.adobe.com/questions-9/how-to-turn-off-grey-popups-when-hovering-over-images-1301933"
            page.goto(thread_url, timeout=60000)

            # ✅ Thread title (always exists)
            page.wait_for_selector("h1", timeout=30000)
            title = page.locator("h1").first.text_content().strip()

            # ✅ Fallback-safe first post container
            first_post = page
            possible_post_selectors = [
                "article",
                ".lia-message",
                ".lia-message-content",
                ".lia-message-body"
            ]

            for selector in possible_post_selectors:
                locator = page.locator(selector)
                if locator.count() > 0:
                    first_post = locator.first
                    break

            # ✅ AUTHOR NAME (from qa-username)
            name_locator = first_post.locator(
                "a.qa-username, a.username"
            )

            author_name = (
                name_locator.first.text_content().strip()
                if name_locator.count() > 0
                else "UNKNOWN"
            )

            # ✅ AUTHOR ROLE (from author-info)
            author_info_locator = first_post.locator(
                "div.author-info"
            )

            author_info_text = (
                author_info_locator.first.text_content().strip()
                if author_info_locator.count() > 0
                else ""
            )

            role = "UNKNOWN"
            posted_ago = "UNKNOWN"

            if "·" in author_info_text:
                role, posted_ago = [x.strip() for x in author_info_text.split("·", 1)]

            # ✅ Reply count
            reply_count = page.locator(".lia-message-reply").count()

            browser.close()

        return {
            "status": "ok",
            "message": "Thread parsed successfully",
            "thread": {
                "thread_url": thread_url,
                "title": title,
                "author_name": author_name,
                "author_role_label": role,
                "posted_ago": posted_ago,
                "reply_count": reply_count
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Backend exception caught",
            "error": str(e)
        }

