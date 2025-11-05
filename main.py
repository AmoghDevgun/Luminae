#!/usr/bin/env python3
"""
Main script to orchestrate all Instagram scrapers.
Takes a username as input and runs all scrapers in sequence.
"""

import sys
import os
import json
import shutil
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import re
from profile import scrape_profile
from getMediaId import scrape_media_ids
from comments import scrape_comments
from likes import scrape_likes
from followers import scrape_followers
import subprocess

def main():
    """Main function to run all scrapers"""
    # Get username input
    username = input("Enter Instagram username: ").strip()
    
    if not username:
        print("❌ Please enter a valid username.")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Starting scraping process for @{username}")
    print(f"{'='*60}\n")
    
    # Ensure output directory
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Scrape profile posts (with pre-seed and skip support)
    print("\n[1/5] Scraping profile posts...")
    print("-" * 60)

    def has_lines(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        return True
        except Exception:
            return False
        return False

    postid_out = os.path.join(output_dir, f"{username}_postid.txt")

    # 1) If pre-seeded via env POST_IDS (comma/space/newline separated), write and skip scraping
    seed_env = os.environ.get("POST_IDS", "").strip()
    if seed_env and not has_lines(postid_out):
        items = [x.strip() for x in re.split(r"[\s,]+", seed_env) if x.strip()]
        if items:
            with open(postid_out, "w", encoding="utf-8") as f:
                f.write("\n".join(items))
            print(f"✅ Seeded {len(items)} post IDs from POST_IDS → {postid_out}")

    # 2) If seed file exists under seed/, copy it
    seed_dir = os.path.join(os.getcwd(), "seed")
    seed_file = os.path.join(seed_dir, f"{username}_postid.txt")
    if os.path.exists(seed_file) and not has_lines(postid_out):
        try:
            shutil.copyfile(seed_file, postid_out)
            print(f"✅ Seeded post IDs from {seed_file} → {postid_out}")
        except Exception as e:
            print(f"⚠️ Failed to use seed file: {e}")

    # 3) If output already has content, skip scraping
    if has_lines(postid_out):
        print(f"✅ Profile posts saved to: {postid_out}\n")
    else:
        # Prefer user's working script integration (no logic changes)
        def run_external_profile_scraper(user):
            """Try both fixed and original scripts, with proper error handling"""
            scripts_to_try = [
                ("netflix_posts_2025_fixed.py", f"{user}_posts.txt"),  # Fixed script uses _posts.txt
                ("netflix_posts_2025.py", f"{user}_postid.txt")  # Original uses _postid.txt
            ]
            
            for script_name, expected_output in scripts_to_try:
                try:
                    script_path = os.path.join(os.getcwd(), script_name)
                    if not os.path.exists(script_path):
                        continue
                    
                    # Run the script directly with username as argument (for fixed script)
                    # For original script, we still need temp file approach
                    if script_name == "netflix_posts_2025_fixed.py":
                        # Fixed script accepts username as command-line argument
                        proc = subprocess.run(
                            [sys.executable, script_path, user],
                            cwd=os.getcwd(),
                            capture_output=True,
                            text=True,
                            timeout=600
                        )
                        
                        # Check for output file (script creates {user}_posts.txt)
                        output_file = f"{user}_posts.txt"
                        if os.path.exists(output_file) and has_lines(output_file):
                            try:
                                shutil.copyfile(output_file, postid_out)
                                print(f"✅ Successfully scraped using {script_name}")
                                # Clean up the temporary output file in cwd
                                try:
                                    os.remove(output_file)
                                except Exception:
                                    pass
                                return True
                            except Exception as e:
                                print(f"⚠️ Failed to copy output from {script_name}: {e}")
                        
                        # If script ran but no output, log stderr if available
                        if proc.stderr:
                            print(f"⚠️ {script_name} ran but produced no output. Error: {proc.stderr[:200]}")
                    else:
                        # Original script: use temp file approach with string replacement
                        with tempfile.TemporaryDirectory() as tdir:
                            tscript = os.path.join(tdir, "scrape.py")
                            with open(script_path, "r", encoding="utf-8") as sf:
                                src = sf.read()
                            
                            # Replace USERNAME variable
                            src = re.sub(r'^(USERNAME\s*=\s*")[^"]+("\s*)$', f'USERNAME = "{user}"', src, flags=re.M)
                            
                            # Update Referer header if it exists
                            src = re.sub(
                                r'(\'Referer\':\s*\'https://www\.instagram\.com/)[^\']+(\'[,\s]*$)',
                                f"'Referer': 'https://www.instagram.com/{user}/'",
                                src,
                                flags=re.M
                            )
                            
                            # Original script: change "netflix_posts.txt" to "{user}_postid.txt"
                            src = src.replace('with open("netflix_posts.txt", "w") as f:', f'with open("{user}_postid.txt", "w") as f:')
                            
                            with open(tscript, "w", encoding="utf-8") as tf:
                                tf.write(src)
                            
                            # Run the script with timeout and error handling
                            proc = subprocess.run(
                                [sys.executable, tscript],
                                cwd=tdir,
                                capture_output=True,
                                text=True,
                                timeout=600
                            )
                            
                            # Check for output file
                            ofile = os.path.join(tdir, f"{user}_postid.txt")
                            if os.path.exists(ofile) and has_lines(ofile):
                                try:
                                    shutil.copyfile(ofile, postid_out)
                                    print(f"✅ Successfully scraped using {script_name}")
                                    return True
                                except Exception as e:
                                    print(f"⚠️ Failed to copy output from {script_name}: {e}")
                            
                            # If script ran but no output, log stderr if available
                            if proc.stderr:
                                print(f"⚠️ {script_name} ran but produced no output. Error: {proc.stderr[:200]}")
                            
                except subprocess.TimeoutExpired as e:
                    print(f"⚠️ {script_name} timed out after 600 seconds")
                    continue
                except Exception as e:
                    print(f"⚠️ {script_name} failed: {e}")
                    continue
            
            return False

        ok = False
        try:
            ok = run_external_profile_scraper(username)
        except Exception as e:
            print(f"⚠️ External profile scraper error: {e}")
        
        if not ok:
            # Fallback to live scrape, but don't abort pipeline if it fails
            try:
                postid_file = scrape_profile(username)
                if postid_file:
                    try:
                        shutil.move(postid_file, postid_out)
                    except Exception:
                        try:
                            shutil.copyfile(postid_file, postid_out)
                        except Exception:
                            pass
            except Exception as e:
                print(f"⚠️ Profile scrape failed, continuing with seeds if any: {e}")
        
        if has_lines(postid_out):
            print(f"✅ Profile posts saved to: {postid_out}\n")
        else:
            # Ensure an empty file exists to make subsequent steps predictable
            try:
                with open(postid_out, "w", encoding="utf-8") as _f:
                    pass
            except Exception:
                pass
            print(f"⚠️ No post IDs available; proceeding with next steps.\n")
    
    # Step 2: Get media IDs
    print("\n[2/5] Extracting media IDs...")
    print("-" * 60)
    media_ids_target = os.path.join(output_dir, f"{username}_media_ids.txt")
    media_ids_file = None
    try:
        media_ids_file = scrape_media_ids(postid_out, media_ids_target)
    except Exception as e:
        print(f"⚠️ Media ID extraction failed: {e}")

    if not media_ids_file:
        # Try seeds for media IDs
        seeded = False
        env_media = os.environ.get("MEDIA_IDS", "").strip()
        if env_media:
            items = [x.strip() for x in re.split(r"[\s,]+", env_media) if x.strip()]
            if items:
                try:
                    with open(media_ids_target, "w", encoding="utf-8") as f:
                        f.write("\n".join(items))
                    media_ids_file = media_ids_target
                    seeded = True
                    print(f"✅ Seeded {len(items)} media IDs from MEDIA_IDS → {media_ids_target}")
                except Exception as e:
                    print(f"⚠️ Failed writing seeded media IDs: {e}")
        if not seeded:
            seed_dir = os.path.join(os.getcwd(), "seed")
            seed_media = os.path.join(seed_dir, f"{username}_media_ids.txt")
            if os.path.exists(seed_media):
                try:
                    shutil.copyfile(seed_media, media_ids_target)
                    media_ids_file = media_ids_target
                    seeded = True
                    print(f"✅ Seeded media IDs from {seed_media} → {media_ids_target}")
                except Exception as e:
                    print(f"⚠️ Failed to copy seeded media IDs: {e}")
    if media_ids_file:
        print(f"✅ Media IDs saved to: {media_ids_file}\n")
    else:
        print("⚠️ No media IDs available; skipping comments and likes steps.\n")
    
    # Steps 3-5: Run comments, likes, followers in parallel
    print("\n[3-5] Running comments, likes, and followers in parallel...")
    print("-" * 60)
    comments_target = os.path.join(output_dir, f"{username}_comments.json")
    likes_target = os.path.join(output_dir, f"{username}_likers.txt")

    comments_file = None
    likes_file = None
    followers_file = None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        if media_ids_file and os.path.exists(media_ids_file):
            futures[executor.submit(scrape_comments, media_ids_file, comments_target)] = "comments"
            futures[executor.submit(scrape_likes, media_ids_file, likes_target)] = "likes"
        futures[executor.submit(scrape_followers, username)] = "followers"
        for future in as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
                if task == "comments":
                    comments_file = result
                    if comments_file:
                        print(f"✅ Comments saved to: {comments_file}")
                    else:
                        print("⚠️ Failed to scrape comments.")
                elif task == "likes":
                    likes_file = result
                    if likes_file:
                        print(f"✅ Likes saved to: {likes_file}")
                    else:
                        print("⚠️ Failed to scrape likes.")
                elif task == "followers":
                    followers_file = result
                    if followers_file:
                        followers_out = os.path.join(output_dir, f"{username}_followers.txt")
                        try:
                            shutil.move(followers_file, followers_out)
                            followers_file = followers_out
                        except Exception:
                            try:
                                shutil.copyfile(followers_file, followers_out)
                                followers_file = followers_out
                            except Exception:
                                pass
                        print(f"✅ Followers saved to: {followers_file}")
                    else:
                        print("⚠️ Failed to scrape followers.")
            except Exception as e:
                print(f"⚠️ {task} task failed: {e}")
    print()

    # Followers seed fallback if scraping failed
    if not followers_file:
        followers_out = os.path.join(output_dir, f"{username}_followers.txt")
        env_followers = os.environ.get("FOLLOWERS", "").strip()
        if env_followers:
            items = [x.strip() for x in re.split(r"[\s,]+", env_followers) if x.strip()]
            if items:
                try:
                    with open(followers_out, "w", encoding="utf-8") as f:
                        f.write("\n".join(items))
                    followers_file = followers_out
                    print(f"✅ Seeded {len(items)} followers from FOLLOWERS → {followers_out}")
                except Exception as e:
                    print(f"⚠️ Failed writing seeded followers: {e}")
        if not followers_file:
            seed_dir = os.path.join(os.getcwd(), "seed")
            seed_followers = os.path.join(seed_dir, f"{username}_followers.txt")
            if os.path.exists(seed_followers):
                try:
                    shutil.copyfile(seed_followers, followers_out)
                    followers_file = followers_out
                    print(f"✅ Seeded followers from {seed_followers} → {followers_out}")
                except Exception as e:
                    print(f"⚠️ Failed to copy seeded followers: {e}")

    # Aggregate leads (usernames) from followers, likers, comments
    print("\n[6/6] Aggregating leads...")
    leads = set()
    try:
        if likes_file and os.path.exists(likes_file):
            with open(likes_file, "r", encoding="utf-8") as f:
                for line in f:
                    uname = line.strip()
                    if uname:
                        leads.add(uname)
    except Exception:
        pass

    try:
        if followers_file and os.path.exists(followers_file):
            with open(followers_file, "r", encoding="utf-8") as f:
                for line in f:
                    uname = line.strip()
                    if uname:
                        leads.add(uname)
    except Exception:
        pass

    try:
        if comments_file and os.path.exists(comments_file):
            with open(comments_file, "r", encoding="utf-8") as f:
                comments = json.load(f)
                for c in comments:
                    uname = (c or {}).get("username")
                    if uname:
                        leads.add(uname)
    except Exception:
        pass

    leads_file = os.path.join(output_dir, f"{username}_leads.txt")
    # Limit to 500 accounts for MVP
    MAX_LEADS = 500
    sorted_leads = sorted(leads)
    limited_leads = sorted_leads[:MAX_LEADS]
    
    with open(leads_file, "w", encoding="utf-8") as f:
        for uname in limited_leads:
            f.write(uname + "\n")
    
    if len(sorted_leads) > MAX_LEADS:
        print(f"✅ Leads saved to: {leads_file} (Limited to {MAX_LEADS} of {len(sorted_leads)} total leads)")
    else:
        print(f"✅ Leads saved to: {leads_file}")

    # Enrich leads by invoking multiple leads_data.py subprocesses in parallel
    leads_data_out = os.path.join(output_dir, f"{username}_leads_data.json")
    try:
        with open(leads_file, "r", encoding="utf-8") as f:
            all_leads = [line.strip() for line in f if line.strip()]
    except Exception:
        all_leads = []

    if all_leads:
        # Chunk leads and run parallel workers based on CPU and lead volume
        def chunks(seq, n):
            for i in range(0, len(seq), n):
                yield seq[i:i+n]

        def run_worker(batch):
            with tempfile.TemporaryDirectory() as tmpdir:
                ufile = os.path.join(tmpdir, "usernames.txt")
                ofile = os.path.join(tmpdir, "output.json")
                with open(ufile, "w", encoding="utf-8") as uf:
                    uf.write("\n".join(batch))
                subprocess.run([sys.executable, os.path.join(os.getcwd(), "leads_data.py")], cwd=tmpdir, check=False)
                if os.path.exists(ofile):
                    try:
                        with open(ofile, "r", encoding="utf-8") as jf:
                            return json.load(jf)
                    except Exception:
                        return []
                return []

        cpu = os.cpu_count() or 4
        max_workers = min(16, max(4, cpu * 2))
        # Aim for ~2-3 batches per worker to keep them busy
        target_batches = max_workers * 3
        batch_size = max(10, (len(all_leads) + target_batches - 1) // target_batches)

        try:
            first_item = True
            with open(leads_data_out, "w", encoding="utf-8") as f:
                f.write("[\n")
                
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    futures = [pool.submit(run_worker, batch) for batch in chunks(all_leads, batch_size)]
                    for fut in as_completed(futures):
                        try:
                            worker_results = fut.result() or []
                            for item in worker_results:
                                if not first_item:
                                    f.write(",\n")
                                json.dump(item, f, ensure_ascii=False, indent=2)
                                f.flush()  # Ensure data is written immediately
                                first_item = False
                        except Exception:
                            pass
                
                f.write("\n]")
            print(f"✅ Leads data saved to: {leads_data_out}\n")
        except Exception as e:
            print(f"⚠️ Failed writing leads data: {e}")
    else:
        print("⚠️ No leads to enrich.")

    # Rank leads for the niche
    try:
        if os.path.exists(leads_data_out):
            with open(leads_data_out, "r", encoding="utf-8") as f:
                enriched_data = json.load(f)
        else:
            enriched_data = []

        # Clean and dedupe
        seen = set()
        cleaned = []
        for item in enriched_data or []:
            uname = (item.get("username") or "").strip().lower()
            if not uname or uname in seen:
                continue
            seen.add(uname)
            cleaned.append({
                "username": uname,
                "full_name": (item.get("full_name") or "").strip(),
                "followers": int(item.get("follower_count") or 0),
                "following": int(item.get("following_count") or 0),
                "bio": (item.get("biography") or "").strip().lower(),
            })

        ranked_json = os.path.join(output_dir, f"{username}_leads_ranked.json")
        ranked_csv = os.path.join(output_dir, f"{username}_leads_ranked.csv")

        if cleaned:
            # Signals and scoring per updated rules
            keywords = ["fitness", "gym", "training", "health", "workout"]
            for row in cleaned:
                # Lowercase everything per cleaning rule
                row["full_name"] = (row["full_name"] or "").lower()
                bio = row["bio"]
                # Bio relevance count and tiered score
                matches = sum(1 for kw in keywords if kw in bio)
                if matches >= 2:
                    bio_score = 1.0
                elif matches == 1:
                    bio_score = 0.6
                else:
                    bio_score = 0.0

                # Authenticity: real name has >1 words
                authenticity = 1 if len((row["full_name"] or "").strip().split()) > 1 else 0

                # Follow ratio balance (best near 1)
                followers = max(0, int(row["followers"]))
                following = max(0, int(row["following"]))
                if followers > 0 and following > 0:
                    ratio = following / followers
                    # Score 1 at ratio==1, declines towards 0 as deviates
                    follow_score = min(ratio, 1/ratio)
                    if follow_score > 1:
                        follow_score = 1.0
                    if follow_score < 0:
                        follow_score = 0.0
                else:
                    follow_score = 0.0

                # Weighted total: 70% bio, 20% authenticity, 10% ratio
                lead_score = 0.7 * bio_score + 0.2 * authenticity + 0.1 * follow_score
                # Ensure within [0,1]
                if lead_score < 0:
                    lead_score = 0.0
                if lead_score > 1:
                    lead_score = 1.0

                # Classification; enforce niche mention requirement for Medium/High
                if lead_score > 0.7 and bio_score > 0:
                    category = "High potential"
                elif lead_score >= 0.4 and bio_score > 0:
                    category = "Medium potential"
                else:
                    category = "Low potential"

                row["lead_score"] = round(lead_score, 4)
                row["category"] = category

            # Sort descending by score
            ranked = sorted(cleaned, key=lambda x: x["lead_score"], reverse=True)

            with open(ranked_json, "w", encoding="utf-8") as f:
                f.write("[\n")
                first_item = True
                for r in ranked:
                    if not first_item:
                        f.write(",\n")
                    json.dump({
                        "username": r["username"],
                        "full_name": r["full_name"],
                        "followers": r["followers"],
                        "following": r["following"],
                        "bio": r["bio"],
                        "lead_score": round(r["lead_score"], 4),
                        "category": r["category"],
                    }, f, ensure_ascii=False, indent=2)
                    f.flush()  # Ensure data is written immediately
                    first_item = False
                f.write("\n]")

            with open(ranked_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["username", "full_name", "followers", "following", "bio", "lead_score", "category"])
                for r in ranked:
                    writer.writerow([
                        r["username"],
                        r["full_name"],
                        r["followers"],
                        r["following"],
                        r["bio"],
                        f"{r['lead_score']:.4f}",
                        r["category"],
                    ])
                    f.flush()  # Ensure data is written immediately

            print(f"✅ Ranked leads saved to: {ranked_json} and {ranked_csv}")
        else:
            # Always materialize output files to satisfy callers
            ranked = []
            try:
                with open(ranked_json, "w", encoding="utf-8") as f:
                    json.dump(ranked, f, ensure_ascii=False, indent=2)
                with open(ranked_csv, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["username", "full_name", "followers", "following", "bio", "lead_score", "category"])
                print(f"⚠️ No enriched leads to rank. Wrote empty results to: {ranked_json}")
            except Exception as e:
                print(f"⚠️ Failed writing empty ranked outputs: {e}")
    except Exception as e:
        print(f"⚠️ Ranking failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("✅ Scraping process completed!")
    print(f"{'='*60}")
    print("\nGenerated files:")
    print(f"  - {postid_out}")
    if media_ids_file:
        print(f"  - {media_ids_file}")
    if comments_file:
        print(f"  - {comments_file}")
    if likes_file:
        print(f"  - {likes_file}")
    if followers_file:
        print(f"  - {followers_file}")
    print(f"  - {leads_file}")
    print(f"  - {leads_data_out}")
    print()

if __name__ == "__main__":
    main()

