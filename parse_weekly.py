"""Refresh the dashboard data.

Downloads the SBC Weekly Report of Registration PDF and the council-district
boundary GeoJSON, then writes data/d1_stats.json. Self-contained; runs on any
OS as long as `pdftotext` is on PATH (apt: poppler-utils; brew: poppler;
choco: xpdf-utils / poppler).

Usage:
    python parse_weekly.py
"""
from __future__ import annotations
import json, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

# NOTE: the older www.sbcounty.gov/uploads/rov/DistrictSummary.pdf is a
# snapshot frozen in Jan 2025. The current weekly file lives on uploads.rov.*
PDF_URL  = "https://uploads.rov.sbcounty.gov/ROV/DistrictSummary.pdf"
GEO_URL  = (
    "https://services.arcgis.com/aA3snZwJfFkVyDuP/arcgis/rest/services/"
    "City_of_Yucaipa_City_Council_Districts/FeatureServer/0/query"
    "?where=1%3D1&outFields=*&f=geojson&outSR=4326"
)
PDF_FILE = DATA / "DistrictSummary.pdf"
GEO_FILE = DATA / "yucaipa_districts.geojson"
OUT_FILE = DATA / "d1_stats.json"

PARTIES = [
    "American Independent", "Democratic", "Green", "Libertarian",
    "No Party Preference", "Other", "Peace and Freedom", "Republican",
]
# Verified against yucaipa.gov/city-council, 2026-06.
MEMBERS = {
    1: {"councilMember": "Bob Miller",    "title": "Councilmember",
        "email": "bmiller@yucaipa.gov",  "phone": "909-797-2489 ext. 501"},
    2: {"councilMember": "Chris Venable", "title": "Mayor",
        "email": "cvenable@yucaipa.gov", "phone": "909-797-2489 ext. 502"},
    3: {"councilMember": "Judy Woolsey",  "title": "Councilmember",
        "email": "jwoolsey@yucaipa.gov", "phone": "909-797-2489 ext. 503"},
    4: {"councilMember": "Justin Beaver", "title": "Deputy Mayor",
        "email": "jbeaver@yucaipa.gov",  "phone": "909-797-2489 ext. 504"},
    5: {"councilMember": "Jon Thorp",     "title": "Councilmember",
        "email": "jthorp@yucaipa.gov",   "phone": "909-797-2489 ext. 505"},
}


def fetch(url: str, dest: Path) -> None:
    print(f"  GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "yucaipa-d1-refresh"})
    with urllib.request.urlopen(req, timeout=60) as resp, dest.open("wb") as f:
        shutil.copyfileobj(resp, f)
    print(f"  wrote {dest} ({dest.stat().st_size:,} bytes)")


def pdf_text(pdf: Path) -> str:
    return subprocess.check_output(
        ["pdftotext", str(pdf), "-"], stderr=subprocess.DEVNULL, text=True
    )


def grab_counts(after: str, n: int = 9) -> list[int]:
    nums = re.findall(r"\b\d{1,3}(?:,\d{3})*\b", after)
    return [int(x.replace(",", "")) for x in nums[:n]]


def extract_district_block(text: str, idx: int) -> dict:
    pat = re.compile(
        rf"City of Yucaipa, City Council, District\s+{idx}\s+Count.*?District Total",
        re.S,
    )
    m = pat.search(text)
    if not m:
        raise RuntimeError(f"District {idx} block not found")
    counts = grab_counts(text[m.end():], 9)
    parties = dict(zip(PARTIES, counts[:8]))
    total = counts[8]
    if sum(parties.values()) != total:
        print(f"  warn: D{idx} party sum {sum(parties.values())} != total {total}")
    return {"registered": total, "parties": parties}


def extract_county(text: str) -> dict:
    # The block we want is the county-wide summary that begins with
    # "San Bernardino County" and ends at the first "TOTAL Registered Voters"
    # header. After that header, the next 9 comma-formatted numbers are the
    # party totals + district total, in PARTIES order.
    #
    # We require commas because (a) all county totals are >1,000, and
    # (b) anchoring after the header alone still leaves "Board of Supervisors,
    # District 1" in the way — its "1" was a false positive before.
    m = re.search(r"San Bernardino County[\s\S]+?TOTAL Registered Voters", text)
    if not m:
        raise RuntimeError("County section not found")
    block = text[m.end(): m.end() + 2000]
    nums = re.findall(r"\b\d{1,3}(?:,\d{3})+\b", block)
    if len(nums) < 9:
        raise RuntimeError(f"County block parsed only {len(nums)} numbers, expected ≥9")
    counts = [int(n.replace(",", "")) for n in nums[:9]]
    parties = dict(zip(PARTIES, counts[:8]))
    total = counts[8]
    if sum(parties.values()) != total:
        print(f"  warn: county party sum {sum(parties.values()):,} != total {total:,}")
    return {"registered": total, "parties": parties}


def extract_report_date(text: str) -> str:
    m = re.search(r"As of (\d+)/(\d+)/(\d{4})", text)
    if not m:
        return ""
    mo, d, y = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def main() -> int:
    print("[1/3] Council district boundaries...")
    fetch(GEO_URL, GEO_FILE)

    print("[2/3] Weekly Report of Registration PDF...")
    fetch(PDF_URL, PDF_FILE)

    if not shutil.which("pdftotext"):
        print("pdftotext not found on PATH — install poppler-utils.", file=sys.stderr)
        return 2

    print("[3/3] Parsing PDF...")
    text = pdf_text(PDF_FILE)

    districts = {}
    for i in range(1, 6):
        d = extract_district_block(text, i)
        d.update(MEMBERS[i])
        districts[str(i)] = d

    county = extract_county(text)
    city_total = sum(d["registered"] for d in districts.values())
    city_parties = {p: sum(districts[str(i)]["parties"][p] for i in range(1, 6)) for p in PARTIES}

    out = {
        "reportDate": extract_report_date(text),
        "source": "San Bernardino County Weekly Report of Registration",
        "sourceUrl": PDF_URL,
        "precinctExportSource": "https://uploads.rov.sbcounty.gov/ROV/PrecinctDistrictExport.zip",
        "partyOrder": [
            "Republican", "Democratic", "No Party Preference",
            "American Independent", "Libertarian", "Other",
            "Peace and Freedom", "Green",
        ],
        "districts": districts,
        "cityTotal": {"registered": city_total, "parties": city_parties},
        "county": county,
    }
    OUT_FILE.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT_FILE} (report date {out['reportDate']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
