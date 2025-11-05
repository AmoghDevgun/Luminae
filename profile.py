# netflix_posts_2025.py
# Run: python3 netflix_posts_2025.py
# ΓåÆ Saves ALL post shortcodes to <username>_postid.txt

import requests, json, time, re, os
from cookies_headers import COOKIES, HEADERS  # <--- load from external file

DOC_ID = "25461702053427256"  # Current Polaris query ID (Nov 2025)

def scrape_profile(username):
    """Scrape all post shortcodes for a username"""
    # Fast path: if we already have a generated file, reuse it to avoid network flakiness
    existing_local = f"{username}_postid.txt"
    existing_out = os.path.join(os.getcwd(), "output", existing_local)

    def has_lines(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        return True
        except Exception:
            return False
        return False

    if os.path.exists(existing_out) and has_lines(existing_out):
        return existing_out
    if os.path.exists(existing_local) and has_lines(existing_local):
        return existing_local
    def get_posts(after=None):
        variables = {
            "username": username,
            "first": 50,
            "data": {
                "count": 50,
                "include_reel_media_seen_timestamp": True,
                "include_relationship_info": True,
                "latest_besties_reel_media": True,
                "latest_reel_media": True
            },
            "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True
        }
        if after:
            variables["after"] = after

        payload = {
            'variables': json.dumps(variables),
            'doc_id': DOC_ID,
            'fb_dtsg': 'NAfsdGpQ8B1C8aSW9ZBSQw7gpZMByeVd3CjWCQ8AUqxG51UlPCIlgwA:17843709688147332:1757617690',
            'lsd': 'YOvULOO686BEKESSLvSL9H',
            'jazoest': '26113',
        }

        # Be resilient to non-JSON (e.g., HTML challenges/rate limits)
        r = requests.post(
            "https://www.instagram.com/graphql/query/",
            headers=HEADERS,
            cookies=COOKIES,
            data=payload,
            timeout=20
        )
        ct = (r.headers.get("content-type") or "").lower()
        if "application/json" in ct:
            try:
                return r.json()
            except Exception:
                pass
        # Fallback: try decode as JSON anyway; else raise with snippet for diagnostics
        try:
            return json.loads(r.text)
        except Exception:
            snippet = (r.text or "").strip()[:300]
            raise RuntimeError(f"Instagram response not JSON (status {r.status_code}): {snippet}")

    print(f"Dumping ALL @{username} posts...")
    output_file = f"{username}_postid.txt"
    with open(output_file, "w") as f:
        cursor = None
        total = 0
        while True:
            # Basic retry loop to survive transient failures
            attempts = 0
            last_err = None
            while attempts < 3:
                try:
                    data = get_posts(cursor)
                    break
                except Exception as e:
                    last_err = e
                    attempts += 1
                    time.sleep(2 * attempts)
            else:
                # Exhausted retries
                raise last_err or RuntimeError("Failed to fetch posts")
            edges = data['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['edges']
            
            for edge in edges:
                shortcode = edge['node']['code']
                f.write(shortcode + "\n")
                total += 1

            print(f"Saved {total} posts...", end="\r")

            page_info = data['data']['xdt_api__v1__feed__user_timeline_graphql_connection']['page_info']
            if not page_info['has_next_page']:
                break
            cursor = page_info['end_cursor']
            time.sleep(2)

    print(f"\nDONE! {total} post IDs ΓåÆ {output_file}")
    return output_file

if __name__ == "__main__":
    USERNAME = input("Enter Instagram username: ").strip()
    scrape_profile(USERNAME)

