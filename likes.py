#!/usr/bin/env python3
import requests, time, sys, json
from cookies_headers import COOKIES, HEADERS  # same format as before

# --- Headers & Cookies ---
HEADERS = HEADERS.copy()
HEADERS["X-IG-App-ID"] = "936619743392459"
HEADERS["User-Agent"] = "Mozilla/5.0"

# --- Function to fetch likers ---
def get_likers(media_id, file_handle, global_count, max_total=50):
    next_max_id = ""
    page = 1
    total = 0

    while True:
        # Stop if global limit reached
        if global_count[0] >= max_total:
            print(f"[!] Reached global limit of {max_total} likers across all media")
            break
            
        print(f"[*] Fetching page {page} for media {media_id}...")

        url = f"https://www.instagram.com/api/v1/media/{media_id}/likers/?count=50"
        if next_max_id:
            url += f"&max_id={next_max_id}"

        try:
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
            data = r.json()
        except Exception as e:
            print(f"[!] Error fetching media {media_id}: {e}")
            break

        users = data.get("users", [])
        if not users:
            print(f"[!] No users found or session expired for {media_id}.")
            break

        remaining = max_total - global_count[0]
        for user in users[:remaining]:
            username = user.get("username")
            if username:
                file_handle.write(username + "\n")
                total += 1
                global_count[0] += 1
                if global_count[0] >= max_total:
                    break

        print(f"    → Saved {total} usernames for this media (Global: {global_count[0]}/{max_total})...")

        if global_count[0] >= max_total:
            print(f"[+] Reached global limit of {max_total} likers\n")
            break

        has_more = data.get("has_more")
        next_max_id = data.get("next_max_id")

        if not has_more or not next_max_id:
            print(f"[+] Done fetching likers for media {media_id}. Total: {total}\n")
            break

        page += 1
        time.sleep(2)
    
    return total

def scrape_likes(filename, output_file="likers.txt"):
    """Scrape likers from media IDs file"""
    # --- Input ---
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
    MAX_LIKERS = 50  # Limit for MVP
    global_count = [0]  # Use list to allow modification in nested function

    with open(output_file, "w") as f:
        for entry in media_entries:
            if global_count[0] >= MAX_LIKERS:
                print(f"[!] Reached global limit of {MAX_LIKERS} likers, stopping")
                break
                
            parts = entry.split(":")
            if len(parts) != 2:
                print(f"[!] Invalid line format: {entry}")
                continue

            shortcode, media_id = parts
            get_likers(media_id, f, global_count, MAX_LIKERS)
            time.sleep(2)

    if global_count[0] >= MAX_LIKERS:
        print(f"\n✅ All likers saved to {output_file} (Limited to {MAX_LIKERS} total)")
    else:
        print(f"\n✅ All likers saved to {output_file}")
    return output_file

if __name__ == "__main__":
    filename = input("Enter filename containing media IDs: ").strip()
    scrape_likes(filename)

