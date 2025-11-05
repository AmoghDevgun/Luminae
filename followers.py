#!/usr/bin/env python3
import requests, json, time, random, sys
from cookies_headers import COOKIES, HEADERS

# --- Step 1: Get USER_ID using new endpoint ---
def get_user_id(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    try:
        r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
        r.raise_for_status()
        data = r.json()
        return str(data["data"]["user"]["id"])
    except Exception as e:
        print(f"[!] Error fetching user ID: {e}")
        if "message" in r.text:
            print("Response:", r.text)
        return None

def scrape_followers(username):
    """Scrape followers for a username"""
    username = username.strip().lower()
    if not username:
        print("❌ Please enter a valid username.")
        return None

    USER_ID = get_user_id(username)
    if not USER_ID:
        print("❌ Failed to get user ID.")
        return None

    print(f"[*] Got user ID for @{username}: {USER_ID}")

    # --- Step 2: Setup ---
    QUERY_HASH = "37479f2b8209594dde7facb0d904896a"  # followers query
    OUT_FILE = f"{username}_followers.txt"

    session = requests.Session()
    session.headers.update({
        **HEADERS,
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{username}/followers/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    })
    session.cookies.update(COOKIES)

    print(f"[*] Starting followers dump for @{username} (User ID: {USER_ID})...\n")

    after = ""
    count = 0
    page = 1

    # --- Step 3: Fetch followers ---
    MAX_FOLLOWERS = 500  # Limit for MVP
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        while True:
            # Stop if we've reached the limit
            if count >= MAX_FOLLOWERS:
                print(f"\n✅ Reached limit of {MAX_FOLLOWERS} followers (stopping early)")
                break
            
            variables = {
                "id": USER_ID,
                "first": 50,
                "after": after or None
            }

            params = {
                "query_hash": QUERY_HASH,
                "variables": json.dumps(variables)
            }

            try:
                r = session.get("https://www.instagram.com/graphql/query/", params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[!] Request error: {e}")
                break

            try:
                edges = data["data"]["user"]["edge_followed_by"]["edges"]
                page_info = data["data"]["user"]["edge_followed_by"]["page_info"]
            except KeyError:
                print("[!] Unexpected response:")
                print(json.dumps(data, indent=2)[:300])
                break

            new_usernames = [u["node"]["username"] for u in edges]
            remaining = MAX_FOLLOWERS - count
            usernames_to_write = new_usernames[:remaining]
            
            for uname in usernames_to_write:
                f.write(uname + "\n")

            count += len(usernames_to_write)
            print(f"Page {page}: +{len(usernames_to_write)} usernames (Total: {count})")

            if not page_info.get("has_next_page") or count >= MAX_FOLLOWERS:
                if count >= MAX_FOLLOWERS:
                    print(f"\n✅ Reached limit of {MAX_FOLLOWERS} followers")
                else:
                    print("\n✅ Finished! No more pages.")
                break

            after = page_info.get("end_cursor", "")
            if not after:
                break

            page += 1
            sleep_time = random.randint(2, 5)
            print(f"→ Waiting {sleep_time}s before next page...\n")
            time.sleep(sleep_time)

    print(f"\n✅ DONE! {count} followers saved to {OUT_FILE}")
    print("Preview:")
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.strip())
    
    return OUT_FILE

if __name__ == "__main__":
    USERNAME = input("Enter Instagram username: ").strip().lower()
    if not USERNAME:
        print("❌ Please enter a valid username.")
        sys.exit(1)
    scrape_followers(USERNAME)

