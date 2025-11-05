#!/usr/bin/env python3
import requests, re, time

def get_media_id(profile_id):
    url = f"https://www.instagram.com/p/{profile_id}/"
    try:
        r = requests.get(url, timeout=10)
        match = re.search(r'"page_id":\s*"postPage_([0-9]+)"', r.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"[!] Error fetching {profile_id}: {e}")
    return None

def scrape_media_ids(filename, output_file="media_ids.txt"):
    """Extract media IDs from profile IDs file"""
    try:
        with open(filename, "r") as f:
            profile_ids = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None

    if not profile_ids:
        print("File is empty or invalid.")
        return None

    print(f"Extracting media IDs for {len(profile_ids)} posts...\n")
    media_ids = []

    for pid in profile_ids:
        mid = get_media_id(pid)
        if mid:
            print(f"{pid} → {mid}")
            media_ids.append(f"{pid}:{mid}")
        else:
            print(f"{pid} → Not found / Private / Error")
        time.sleep(1)

    if media_ids:
        with open(output_file, "w") as f:
            f.write("\n".join(media_ids))
        print(f"\n✅ Saved {len(media_ids)} media IDs → {output_file}")
        return output_file
    else:
        print("\n⚠️ No media IDs found.")
        return None

if __name__ == "__main__":
    filename = input("Enter filename containing profile IDs: ").strip()
    scrape_media_ids(filename)

