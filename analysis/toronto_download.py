"""Download the City of Toronto open data used by build_toronto.py into data/toronto_raw/ (not committed: about 100 MB).
Sources: City of Toronto Open Data portal (https://open.toronto.ca). Run from the repo root:  python analysis/toronto_download.py
"""
import json, os, urllib.request

API = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id="
WANT = [  # (package id, resource name, local file)
    ("municipal-licensing-and-standards-business-licences-and-permits", "Business licences data.csv", "business_licences.csv"),
    ("dinesafe", "Dinesafe.csv", "dinesafe.csv"),
    ("neighbourhoods", "Neighbourhoods - 4326.geojson", "neighbourhoods.geojson"),
    ("neighbourhood-profiles", "neighbourhood-profiles-2021-158-model", "neighbourhood_profiles_2021.xlsx"),
    ("business-improvement-areas", "Business Improvement Areas Data - 4326.geojson", "bia.geojson"),
]

os.makedirs("data/toronto_raw", exist_ok=True)
for pkg, name, local in WANT:
    path = f"data/toronto_raw/{local}"
    if os.path.exists(path):
        print("have", local); continue
    res = json.load(urllib.request.urlopen(API + pkg, timeout=60))["result"]["resources"]
    url = next(r["url"] for r in res if r["name"] == name)
    print("downloading", local)
    urllib.request.urlretrieve(url, path)
