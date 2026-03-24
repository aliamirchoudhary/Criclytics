"""
debug_rapidapi.py  —  run this ONCE to dump the raw API response
so we can see the exact field names and structure.
"""
import requests, json, os

KEY  = "d73929627bmshbccf96f2e8a1d98p1c4855jsn68729b8d2460"
HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE = "https://cricbuzz-cricket.p.rapidapi.com"
HDR  = {"x-rapidapi-key": KEY, "x-rapidapi-host": HOST}

for endpoint in ["/matches/v1/recent", "/matches/v1/upcoming", "/matches/v1/live"]:
    print(f"\n{'='*60}")
    print(f"ENDPOINT: {endpoint}")
    print('='*60)
    try:
        r = requests.get(BASE + endpoint, headers=HDR, timeout=15)
        print(f"HTTP {r.status_code}")
        data = r.json()
        
        # Save full raw response
        fname = endpoint.replace("/","_").strip("_") + ".json"
        with open(fname, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Raw saved to: {fname}")
        
        # Print top-level keys
        print(f"Top keys: {list(data.keys())}")
        
        # Walk and print every match
        count = 0
        for typeMatch in data.get("typeMatches", []):
            type_name = typeMatch.get("matchType","?")
            print(f"  matchType block: {type_name!r}")
            for seriesMatch in typeMatch.get("seriesMatches", []):
                # Try both wrapper styles
                wrapper = (seriesMatch.get("seriesAdWrapper") 
                          or seriesMatch.get("series") 
                          or seriesMatch)
                sname = (wrapper.get("seriesName") 
                        or wrapper.get("name") 
                        or "?")
                matches = wrapper.get("matches", [])
                if not matches:
                    # Maybe matches are directly in seriesMatch
                    matches = seriesMatch.get("matches", [])
                for m in matches:
                    mi = m.get("matchInfo", {})
                    t1 = mi.get("team1",{}).get("teamName","?")
                    t2 = mi.get("team2",{}).get("teamName","?")
                    fmt = mi.get("matchFormat","?")
                    mid = mi.get("matchId","?")
                    sn  = mi.get("seriesName","?")
                    print(f"    [{fmt}] id={mid} | {t1} vs {t2}")
                    print(f"           seriesName={sn!r}")
                    count += 1
        print(f"  Total: {count} matches")
        
    except Exception as e:
        print(f"Error: {e}")

print("\nDone. Paste the output here so the match filter can be fixed.")
