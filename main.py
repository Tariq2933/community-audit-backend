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

# ----------------------------
# Run audit – full thread traversal
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

            # ✅ Load ONE known thread (safe + deterministic)
            thread_url = "https://community.adobe.com/questions-9/how-to-turn-off-grey-popups-when-hovering-over-images-1301933"
            page.goto(thread_url, timeout=60000)

            # ✅ Thread title
            page.wait_for_selector("h1", timeout=30000)
            title = page.locator("h1").first.text_content().strip()

            # ✅ Get ALL posts (OP + replies)
            post_blocks = page.locator("article")
            post_count = post_blocks.count()

            posts = []

            for i in range(post_count):
                post = post_blocks.nth(i)

                # ---------- Author name ----------
                name_locator = post.locator("a.qa-username")
                author_name = (
                    name_locator.first.text_content().strip()
                    if name_locator.count() > 0
                    else "UNKNOWN"
                )

                # ---------- Author role ----------
                role_locator = post.locator("span.rank-title")
                author_role = (
                    role_locator.first.text_content().strip()
                    if role_locator.count() > 0
                    else "UNKNOWN"
                )

                # ---------- Posted time ----------
                info_locator = post.locator("div.author-info")
                posted_ago = "UNKNOWN"

                if info_locator.count() > 0:
                    info_text = info_locator.first.text_content().strip()
                    if author_role != "UNKNOWN":
                        info_text = info_text.replace(author_role, "").replace("·", "").strip()
                    posted_ago = info_text

                # ---------- Message text ----------
                body_locator = post.locator(
                    ".lia-message-body, .lia-message-content"
                )

                message_text = (
                    body_locator.first.text_content().strip()
                    if body_locator.count() > 0
                    else ""
                )

                posts.append({
                    "position": "OP" if i == 0 else "Reply",
                    "author_name": author_name,
                    "author_role_label": author_role,
                    "posted_ago": posted_ago,
                    "message_text": message_text
                })

            browser.close()

        return {
            "status": "ok",
            "message": "Full thread parsed successfully",
            "thread": {
                "thread_url": thread_url,
                "title": title,
                "total_posts": len(posts),
                "posts": posts
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Backend exception caught",
            "error": str(e)
        }
