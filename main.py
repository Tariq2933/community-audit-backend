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


@app.post("/run")
def run_audit(req: RunRequest):

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
        thread_url = req.board
        page.goto(thread_url, timeout=60000)

        page.wait_for_selector("h1", timeout=30000)
        title = page.locator("h1").first.text_content().strip()

        post_blocks = page.locator(
            "article.topic-wrapper, div.threaded-reply-item[role='article']"
        )

        posts = []

        for i in range(post_blocks.count()):
            post = post_blocks.nth(i)
            position = "OP" if i == 0 else "Reply"

            # Author name
            name_locator = post.locator("a.qa-username")
            author_name = (
                name_locator.first.text_content().strip()
                if name_locator.count() > 0 else "UNKNOWN"
            )

            # Author role
            role_locator = post.locator("span.rank-title")
            author_role = (
                role_locator.first.text_content().strip()
                if role_locator.count() > 0 else "UNKNOWN"
            )

            # Date parsing
            posted_ago = "UNKNOWN"
            posted_date = "UNKNOWN"

            info_locator = post.locator("div.author-info.dot-seperated")
            if info_locator.count() > 0:
                info_text = info_locator.first.text_content().strip()
                info_text = info_text.replace(author_role, "").replace("·", "").strip()

                ago_match = re.search(r"\b\d+\s+\w+\s+ago\b", info_text)
                date_match = re.search(r"\b[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\b", info_text)

                if ago_match:
                    posted_ago = ago_match.group(0)
                if date_match:
                    posted_date = date_match.group(0)

            # Message text
            message_text = ""
            new_editor = post.locator("div.post__content.post__content--new-editor")
            if new_editor.count() > 0:
                message_text = "\n".join(
                    p.strip()
                    for p in new_editor.first.locator("p").all_inner_texts()
                    if p.strip()
                )
            else:
                legacy = post.locator("div.post.qa-topic-post-box")
                if legacy.count() > 0:
                    message_text = legacy.first.text_content().strip()

            posts.append({
                "position": position,
                "author_name": author_name,
                "author_role_label": author_role,
                "posted_ago": posted_ago,
                "posted_date": posted_date,
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
