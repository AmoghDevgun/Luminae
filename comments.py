#!/usr/bin/env python3
import requests
import json
import time
from cookies_headers import COOKIES, HEADERS  # same format as before

# --- Constants ---
URL = "https://www.instagram.com/graphql/query"
DOC_ID = "25060748103519434"  # Current Polaris Post Comments Query ID

# --- Prepare Headers ---
HEADERS = HEADERS.copy()
HEADERS["x-fb-friendly-name"] = "PolarisPostCommentsPaginationQuery"
HEADERS["x-ig-app-id"] = "936619743392459"
HEADERS["content-type"] = "application/x-www-form-urlencoded"

# --- GraphQL Query Variables ---
def make_variables(media_id, after_cursor=None):
    variables = {
        "after": after_cursor,
        "before": None,
        "first": 20,
        "last": None,
        "media_id": media_id,
        "sort_order": "popular",
        "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True
    }
    return json.dumps(variables)

# --- Fetch a single page of comments ---
def fetch_comments(media_id, after=None):
    payload = {
        "fb_api_req_friendly_name": "PolarisPostCommentsPaginationQuery",
        "variables": make_variables(media_id, after),
        "doc_id": DOC_ID,
    }

    try:
        res = requests.post(URL, headers=HEADERS, cookies=COOKIES, data=payload, timeout=15)
        if res.status_code != 200:
            print("HTTP Error:", res.status_code)
            return None
        return res.json()
    except Exception as e:
        print(f"[!] Request failed for media {media_id}: {e}")
        return None

# --- Collect all comments for one media ---
def collect_comments_for_media(media_id, file_handle, first_item_ref, global_count, max_total=500):
    after = None
    page = 1
    total_comments = 0

    while True:
        # Stop if global limit reached
        if global_count[0] >= max_total:
            print(f"[!] Reached global limit of {max_total} comments across all media")
            break
            
        print(f"\n[*] Fetching comments (page {page}) for media ID {media_id}...")
        data = fetch_comments(media_id, after)
        if not data:
            break

        try:
            comments_data = data["data"]["xdt_api__v1__media__media_id__comments__connection"]
            edges = comments_data.get("edges", [])
        except Exception as e:
            print(f"[!] Parse error for media {media_id}: {e}")
            break

        remaining = max_total - global_count[0]
        for edge in edges[:remaining]:
            node = edge["node"]
            user = node.get("user", {})
            comment = {
                "media_id": media_id,
                "username": user.get("username", ""),
                "text": node.get("text", ""),
                "likes": node.get("comment_like_count", 0),
                "created_at": node.get("created_at", 0)
            }
            # Stream comment to file
            if not first_item_ref[0]:
                file_handle.write(",\n")
            json.dump(comment, file_handle, ensure_ascii=False)
            first_item_ref[0] = False
            total_comments += 1
            global_count[0] += 1
            
            if global_count[0] >= max_total:
                break

        page_info = comments_data.get("page_info", {})
        has_next = page_info.get("has_next_page", False)
        after = page_info.get("end_cursor")

        print(f"    → Collected {len(edges[:remaining])} new comments, total {total_comments} for this media (Global: {global_count[0]}/{max_total})...")

        if global_count[0] >= max_total:
            print(f"[+] Reached global limit of {max_total} comments\n")
            break

        if not has_next or not after:
            print(f"[+] Done fetching comments for media {media_id}.\n")
            break

        page += 1
        time.sleep(2)

    return total_comments

def scrape_comments(filename, output_file="comments.json"):
    """Scrape comments from media IDs file"""
    # --- Load Media IDs File ---
    try:
        with open(filename, "r") as f:
            media_entries = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None

    if not media_entries:
        print("File is empty or invalid.")
        return None

    # --- Main Execution ---
    print(f"[*] Processing {len(media_entries)} media IDs...\n")
    MAX_COMMENTS = 500  # Limit for MVP
    total_comments = 0
    first_item = [True]  # Use list to allow modification in nested function
    global_count = [0]  # Use list to allow modification in nested function

    # Open file and write opening bracket
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[\n")
        
        for entry in media_entries:
            if global_count[0] >= MAX_COMMENTS:
                print(f"[!] Reached global limit of {MAX_COMMENTS} comments, stopping")
                break
                
            parts = entry.split(":")
            if len(parts) != 2:
                print(f"[!] Invalid line format: {entry}")
                continue

            shortcode, media_id = parts
            count = collect_comments_for_media(media_id, f, first_item, global_count, MAX_COMMENTS)
            total_comments += count
            time.sleep(2)
        
        # Close JSON array
        f.write("\n]")

    if global_count[0] >= MAX_COMMENTS:
        print(f"\n✅ Done! Saved {total_comments} comments → {output_file} (Limited to {MAX_COMMENTS} total)")
    else:
        print(f"\n✅ Done! Saved {total_comments} comments → {output_file}")
    return output_file

if __name__ == "__main__":
    filename = input("Enter filename containing media IDs: ").strip()
    scrape_comments(filename)

