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

    # ----------------------------
    # Playwright browser lifecycle
    # ----------------------------
    # We use Playwright in synchronous mode.
    # Chromium is launched headless with extra flags
    # required for Render / Linux containers.
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

        # Create a new browser tab (page)
        page = browser.new_page()

        # ----------------------------
        # Navigate to thread URL
        # ----------------------------
        # IMPORTANT:
        # req.board MUST be a FULL THREAD URL, e.g.
        # https://community.adobe.com/questions-9/how-to-turn-off-grey-popups-...-1301933
        thread_url = req.board
        page.goto(thread_url, timeout=60000)

        # ----------------------------
        # Extract thread title
        # ----------------------------
        # Every Adobe Community thread has an <h1>.
        # Board pages also have <h1> ("Questions"),
        # which is why board URLs produce 0 posts.
        page.wait_for_selector("h1", timeout=30000)
        title = page.locator("h1").first.text_content().strip()

        # ----------------------------
        # Locate all posts in the thread
        # ----------------------------
        # This selector intentionally covers:
        #   - Original post (OP)
        #   - All replies
        #
        # If this list is empty, it usually means
        # a board URL was passed instead of a thread URL.
        post_blocks = page.locator(
            "article.topic-wrapper, div.threaded-reply-item[role='article']"
        )

        posts = []

        # --------------------------------------------------
        # Iterate through OP + replies
        # --------------------------------------------------
        for i in range(post_blocks.count()):
            post = post_blocks.nth(i)

            # First post is OP, rest are replies
            position = "OP" if i == 0 else "Reply"

            # ----------------------------
            # Extract author name
            # ----------------------------
            # qa-username is consistent across OP and replies
            name_locator = post.locator("a.qa-username")
            author_name = (
                name_locator.first.text_content().strip()
                if name_locator.count() > 0 else "UNKNOWN"
            )

            # ----------------------------
            # Extract author role
            # ----------------------------
            # rank-title tells us:
            # Participant / Community Manager / Legend / etc.
            role_locator = post.locator("span.rank-title")
            author_role = (
                role_locator.first.text_content().strip()
                if role_locator.count() > 0 else "UNKNOWN"
            )

            # ----------------------------
            # Extract and split date info
            # ----------------------------
            # Adobe combines relative + absolute dates in one block.
            # Example text:
            #   "Participant · 1 year agoApril 24, 2025"
            #
            # We:
            #   - Remove role text
            #   - Use regex to extract:
            #       posted_ago  -> "1 year ago"
            #       posted_date -> "April 24, 2025"
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

            # ----------------------------
            # Extract message text
            # ----------------------------
            # New editor posts use:
            #   div.post__content.post__content--new-editor
            #
            # Legacy posts (older threads) use:
            #   div.post.qa-topic-post-box
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

            # ----------------------------
            # Append post to results
            # ----------------------------
            posts.append({
                "position": position,
                "author_name": author_name,
                "author_role_label": author_role,
                "posted_ago": posted_ago,
                "posted_date": posted_date,
                "message_text": message_text
            })

        # Close browser cleanly
        browser.close()

    # --------------------------------------------------
    # Final response
    # --------------------------------------------------
    # Returned JSON is consumed by the UI and audit logic.
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
