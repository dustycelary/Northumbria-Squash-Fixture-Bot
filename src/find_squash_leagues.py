#!/usr/bin/env python3
"""
Find all squash leagues hosted on leaguemaster.co.uk by discovering subdomains.
Uses multiple techniques: DNS brute-force with a wordlist, Google/search scraping,
and certificate transparency logs (crt.sh).
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LeagueFinder/1.0)"}
TIMEOUT = 10

# ── 1. Certificate Transparency (crt.sh) ─────────────────────────────────────


def fetch_crtsh():
    """Query crt.sh for all subdomains of leaguemaster.co.uk."""
    print("[*] Querying crt.sh certificate transparency logs...")
    url = "https://crt.sh/?q=%.leaguemaster.co.uk&output=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        entries = r.json()
        subdomains = set()
        for entry in entries:
            name = entry.get("name_value", "")
            for line in name.splitlines():
                line = line.strip().lstrip("*.")
                if line.endswith("leaguemaster.co.uk") and line != "leaguemaster.co.uk":
                    subdomains.add(line)
        print(f"    Found {len(subdomains)} subdomains from crt.sh")
        return subdomains
    except Exception as e:
        print(f"    crt.sh error: {e}")
        return set()


# ── 2. Check if a subdomain is a squash league ───────────────────────────────


def is_squash_league(subdomain):
    """
    Return (subdomain, title_or_None) — title is set if the page looks like
    a squash league.
    """
    url = f"https://{subdomain}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        text = r.text.lower()
        # Must be on leaguemaster and mention squash
        if "leaguemaster" not in r.url.lower() and "leaguemaster" not in text:
            return subdomain, None
        if "squash" not in text and "squash" not in subdomain:
            return subdomain, None
        # Extract page title
        title_match = re.search(
            r"<title>(.*?)</title>", r.text, re.IGNORECASE | re.DOTALL
        )
        title = title_match.group(1).strip() if title_match else subdomain
        return subdomain, title
    except Exception:
        return subdomain, None


# ── 3. Wordlist brute-force ───────────────────────────────────────────────────

COUNTY_WORDS = [
    "bedfordshire",
    "berkshire",
    "bristol",
    "buckinghamshire",
    "cambridgeshire",
    "cheshire",
    "cleveland",
    "cornwall",
    "cumbria",
    "derbyshire",
    "devon",
    "dorset",
    "durham",
    "eastmidlands",
    "eastsussex",
    "essex",
    "gloucestershire",
    "hampshire",
    "hereford",
    "herts",
    "hertfordshire",
    "humberside",
    "isleofwight",
    "kent",
    "lancashire",
    "leicestershire",
    "lincolnshire",
    "london",
    "manchester",
    "merseyside",
    "middlesex",
    "norfolk",
    "northants",
    "northumberland",
    "northumbria",
    "nottinghamshire",
    "oxfordshire",
    "shropshire",
    "somerset",
    "staffordshire",
    "suffolk",
    "surrey",
    "tyneside",
    "warwickshire",
    "westsussex",
    "westmidlands",
    "wiltshire",
    "worcestershire",
    "yorkshire",
    "northyorkshire",
    "southyorkshire",
    "westyorkshire",
    "wales",
    "scotland",
    "nwcounties",
    "nwwomens",
    "nwwomenssquash",
    "nwsquash",
    "eastmidlandssquash",
    "westmidlandssquash",
    "leedsmetro",
    "leeds",
    "sheffield",
    "manchester",
    "ipswich",
    "ipswichsports",
    "norwich",
    "kentnw",
    "kenttournaments",
    "county",
]

SUFFIXES = ["squash", "squash1", ""]


def build_wordlist_subdomains():
    candidates = set()
    for word in COUNTY_WORDS:
        for suffix in SUFFIXES:
            sub = f"{word}{suffix}.leaguemaster.co.uk"
            candidates.add(sub)
    return candidates


# ── 4. Main ───────────────────────────────────────────────────────────────────


def main():
    # Gather candidates
    crtsh_subs = fetch_crtsh()
    wordlist_subs = build_wordlist_subdomains()
    all_candidates = crtsh_subs | wordlist_subs

    print(f"\n[*] Total candidates to check: {len(all_candidates)}")
    print("[*] Checking each for squash content...\n")

    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(is_squash_league, sub): sub for sub in all_candidates}
        for i, future in enumerate(as_completed(futures), 1):
            sub, title = future.result()
            if title:
                results.append(
                    {"subdomain": sub, "title": title, "url": f"https://{sub}/"}
                )
                print(f"  ✓ {sub}  →  {title}")
            if i % 50 == 0:
                print(f"    ... checked {i}/{len(all_candidates)}")

    results.sort(key=lambda x: x["subdomain"])

    print(f"\n{'=' * 60}")
    print(f"Found {len(results)} squash leagues on leaguemaster.co.uk")
    print(f"{'=' * 60}")
    for r in results:
        print(f"  {r['url']}")

    # Save JSON
    with open("data/squash_leagues.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n[*] Results saved to squash_leagues.json")


if __name__ == "__main__":
    main()
