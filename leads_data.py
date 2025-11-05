#!/usr/bin/env python3
import requests
import re
import json
import sys
import time
from cookies_headers import COOKIES, HEADERS  # same format as before

# --- Configuration ---



def get_user_id(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    resp = requests.get(url, headers=HEADERS, cookies=COOKIES, allow_redirects=False)

    if resp.status_code == 302:
        print("❌ Redirected to login — cookies expired or invalid.")
        return None
    elif resp.status_code != 200:
        print(f"❌ Failed to load {username}: HTTP {resp.status_code}")
        return None

    try:
        js = resp.json()
        return js["data"]["user"]["id"]
    except Exception as e:
        print(f"⚠️ Could not parse user_id for {username}: {e}")
        return None



def get_profile_info(username, user_id):
    url = "https://www.instagram.com/graphql/query"
    doc_id = "24963806849976236"

    variables = {
        "enable_integrity_filters": True,
        "id": user_id,
        "render_surface": "PROFILE",
        "__relay_internal__pv__PolarisProjectCannesEnabledrelayprovider": True,
        "__relay_internal__pv__PolarisProjectCannesLoggedInEnabledrelayprovider": True,
        "__relay_internal__pv__PolarisCannesGuardianExperienceEnabledrelayprovider": True,
        "__relay_internal__pv__PolarisCASB976ProfileEnabledrelayprovider": False,
        "__relay_internal__pv__PolarisRepostsConsumptionEnabledrelayprovider": False
    }

    data = {
        "av": "17841446085823069",
        "__d": "www",
        "__user": "0",
        "__a": "1",
        "__req": "2",
        "__hs": "20396.HYP:instagram_web_pkg.2.1...0",
        "dpr": "1",
        "__ccg": "GOOD",
        "__rev": "1029384238",
        "__s": "nxa7io:f9zpir:ahz0jz",
        "__hsi": "7568992210495101128",
        "fb_api_req_friendly_name": "PolarisProfilePageContentQuery",
        "server_timestamps": "true",
        "doc_id": doc_id,
        "variables": json.dumps(variables)
    }

    headers = HEADERS.copy()
    headers["referer"] = f"https://www.instagram.com/{username}/"
    headers["x-csrftoken"] = COOKIES["csrftoken"]

    resp = requests.post(url, headers=headers, cookies=COOKIES, data=data)
    if resp.status_code != 200:
        print(f"❌ GraphQL failed for {username}: HTTP {resp.status_code}")
        return None

    try:
        js = resp.json()
        user = js["data"]["user"]
        return {
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "is_private": user.get("is_private"),
            "biography": user.get("biography"),
            "follower_count": user.get("follower_count"),
            "following_count": user.get("following_count")
        }
    except Exception as e:
        print(f"⚠️ Parse error for {username}: {e}")
        return None


if __name__ == "__main__":
    input_file = "usernames.txt"
    output_file = "output.json"

    try:
        usernames = [u.strip().lower() for u in open(input_file) if u.strip()]
    except FileNotFoundError:
        print(f"❌ Input file '{input_file}' not found.")
        sys.exit(1)

    count = 0
    first_item = True

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("[\n")
        
        for username in usernames:
            print(f"\n🔍 Processing @{username}...")
            user_id = get_user_id(username)
            if not user_id:
                continue

            info = get_profile_info(username, user_id)
            if info:
                if not first_item:
                    f.write(",\n")
                json.dump(info, f, indent=4, ensure_ascii=False)
                f.flush()  # Ensure data is written immediately
                first_item = False
                count += 1
                print(f"✅ Done: {info['username']} — Followers: {info['follower_count']}")
            else:
                print(f"⚠️ Skipped {username}")

            time.sleep(2)
        
        f.write("\n]")

    print(f"\n📁 Saved {count} profiles to '{output_file}' successfully!")

