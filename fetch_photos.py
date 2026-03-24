"""
fetch_photos.py — Player Photo Fetcher
=======================================
Fetches player photos from multiple sources in priority order:
1. CricAPI h.cricapi.com (already in players_meta.json for 57 players)
2. Wikipedia REST API (no key, reliable, public domain)
3. ESPNcricinfo player photos (unofficial, may require VPN)

Run:  python fetch_photos.py
Updates: data/static/players_meta.json
"""

import json, os, sys, time, urllib.request, urllib.error, urllib.parse

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "data", "static")
META_FILE  = os.path.join(STATIC_DIR, "players_meta.json")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def http_get(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return None

# ── Wikipedia name mappings (Cricsheet name → Wikipedia article title) ────────
WIKI_NAMES = {
    "V Kohli":        "Virat_Kohli",
    "RG Sharma":      "Rohit_Sharma",
    "JJ Bumrah":      "Jasprit_Bumrah",
    "HH Pandya":      "Hardik_Pandya",
    "KL Rahul":       "KL_Rahul",
    "RA Jadeja":      "Ravindra_Jadeja",
    "JE Root":        "Joe_Root",
    "BA Stokes":      "Ben_Stokes",
    "PJ Cummins":     "Pat_Cummins",
    "SPD Smith":      "Steve_Smith_(cricketer)",
    "Babar Azam":     "Babar_Azam",
    "Shaheen Shah Afridi": "Shaheen_Shah_Afridi",
    "KS Williamson":  "Kane_Williamson",
    "K Rabada":       "Kagiso_Rabada",
    "Rashid Khan":    "Rashid_Khan_(cricketer)",
    "Shakib Al Hasan": "Shakib_Al_Hasan",
    # Additional players
    "DA Warner":      "David_Warner_(cricketer)",
    "SPD Smith":      "Steve_Smith_(cricketer)",
    "TM Head":        "Travis_Head",
    "MR Marsh":       "Mitchell_Marsh",
    "MA Starc":       "Mitchell_Starc",
    "JR Hazlewood":   "Josh_Hazlewood",
    "GJ Maxwell":     "Glenn_Maxwell",
    "AT Carey":       "Alex_Carey",
    "MP Stoinis":     "Marcus_Stoinis",
    "M Labuschagne":  "Marnus_Labuschagne",
    "SB Gill":        "Shubman_Gill",
    "YBK Jaiswal":    "Yashasvi_Jaiswal",
    "SS Iyer":        "Shreyas_Iyer",
    "Arshdeep Singh": "Arshdeep_Singh",
    "Mohammed Siraj": "Mohammed_Siraj",
    "AR Patel":       "Axar_Patel",
    "Kuldeep Yadav":  "Kuldeep_Yadav",
    "W Sundar":       "Washington_Sundar",
    "Mohammed Shami": "Mohammed_Shami",
    "R Ashwin":       "R._Ashwin",
    "EJG Morgan":     "Eoin_Morgan",
    "JC Buttler":     "Jos_Buttler",
    "BT Foakes":      "Ben_Foakes",
    "ZS Crawley":     "Zak_Crawley",
    "MJ Leach":       "Jack_Leach",
    "SCJ Broad":      "Stuart_Broad",
    "JM Anderson":    "James_Anderson_(cricketer)",
    "MSD":            "MS_Dhoni",
    "MS Dhoni":       "MS_Dhoni",
    "Babar Azam":     "Babar_Azam",
    "Imam-ul-Haq":    "Imam-ul-Haq",
    "Mohammad Rizwan":"Mohammad_Rizwan_(cricketer)",
    "Fakhar Zaman":   "Fakhar_Zaman",
    "Haris Rauf":     "Haris_Rauf",
    "F du Plessis":   "Faf_du_Plessis",
    "Q de Kock":      "Quinton_de_Kock",
    "AK Markram":     "Aiden_Markram",
    "HE van der Dussen": "Rassie_van_der_Dussen",
    "WD Parnell":     "Wayne_Parnell",
    "KA Maharaj":     "Keshav_Maharaj",
    "LRPL Taylor":    "Ross_Taylor",
    "TWM Latham":     "Tom_Latham",
    "DS Conway":      "Devon_Conway",
    "IS Sodhi":       "Ish_Sodhi",
    "TG Southee":     "Tim_Southee",
    "Shakib Al Hasan": "Shakib_Al_Hasan",
    "Mushfiqur Rahim": "Mushfiqur_Rahim",
    "Litton Das":     "Liton_Das",
    "Taskin Ahmed":   "Taskin_Ahmed",
    "Mustafizur Rahman": "Mustafizur_Rahman",
    "Mehidy Hasan Miraz": "Mehidy_Hasan_Miraz",
    "Mohammad Nabi":  "Mohammad_Nabi_(cricketer)",
    "Najibullah Zadran": "Najibullah_Zadran",
    "Hashmatullah Shahidi": "Hashmatullah_Shahidi",
    "PR Stirling":    "Paul_Stirling_(cricketer)",
    "AF Tector":      "Harry_Tector",
    "G Coetzee":      "Gerald_Coetzee",
    "M Jansen":       "Marco_Jansen",
}

def fetch_wikipedia_photo(wiki_name):
    """Fetch player photo URL from Wikipedia REST API."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wiki_name)}"
    data = http_get(url)
    if not data: return None
    # Try thumbnail first (good quality, right size)
    thumb = data.get('thumbnail', {}).get('source', '')
    if thumb:
        # Upgrade to 300px width for better quality
        thumb = thumb.replace('/220px-', '/300px-').replace('/150px-', '/300px-')
        return thumb
    # Try original image
    orig = data.get('originalimage', {}).get('source', '')
    return orig or None

def main():
    print("=" * 55)
    print("  Criclytics — Player Photo Fetcher")
    print("=" * 55)

    if not os.path.exists(META_FILE):
        print(f"  ERROR: {META_FILE} not found. Run create_static_files.py first.")
        sys.exit(1)

    with open(META_FILE, encoding='utf-8') as f:
        meta = json.load(f)

    total = len(meta)
    already = sum(1 for v in meta.values() if v.get('image_url'))
    print(f"  Players in meta: {total}")
    print(f"  Already have photos: {already}")
    print()

    fetched = 0
    failed  = 0
    skipped = 0

    for cs_name, player in meta.items():
        if player.get('image_url'):
            skipped += 1
            continue  # Already has photo (CricAPI URL)

        # Try Wikipedia - check meta wiki_name first, then WIKI_NAMES dict, then full_name
        wiki_name = player.get('wiki_name') or WIKI_NAMES.get(cs_name)
        if not wiki_name:
            full = player.get('full_name', '')
            if full and full != cs_name:
                wiki_name = full.replace(' ', '_')

        img_url = None
        if wiki_name:
            img_url = fetch_wikipedia_photo(wiki_name)
            time.sleep(0.3)  # Rate limiting

        if img_url:
            meta[cs_name]['image_url'] = img_url
            fetched += 1
            print(f"  ✓ {cs_name}: {img_url[:70]}")
        else:
            failed += 1
            if wiki_name:
                print(f"  ✗ {cs_name} (tried: {wiki_name})")

    # Save
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 55)
    print(f"  Already had: {skipped}")
    print(f"  Newly fetched: {fetched}")
    print(f"  Failed/not found: {failed}")
    print(f"  Saved to: {META_FILE}")
    print("=" * 55)

if __name__ == "__main__":
    main()
