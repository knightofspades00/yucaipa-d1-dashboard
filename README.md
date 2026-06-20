# Yucaipa City Council District 1 — Map & Data Dashboard

Single-file ArcGIS dashboard for Yucaipa Council District 1.

- Custom **ArcGIS map** of all five districts (D1 highlighted), with address search and click-to-focus
- **Aggregated voter registration** by party for each district, with a chart comparing to county-wide baseline
- **Precinct boundary overlay** (toggle)
- **Census ACS demographic overlay** (toggle) — income, age, ethnicity, education, poverty (US Census ACS via Esri Living Atlas)
- **Live SBC Registrar dashboard** embedded for always-current numbers
- City's official **"Find My District" address lookup** embedded for definitive checks
- **Download PDF** button — exports the current district's snapshot as a one-page handout

> **Privacy / law.** Individual voter registration and party affiliation are **not public** — they're held by the SBC Registrar of Voters under California Elections Code §2194 and released only to qualifying campaigns, parties, scholars, and journalists. This dashboard sticks to public aggregates by design. The smallest geography with public party splits is the city council district itself, which this dashboard already shows.

## Live site

GitHub Pages: https://knightofspades00.github.io/yucaipa-d1-dashboard/

## Run locally

```powershell
# anywhere on the box with Python:
python -m http.server 8000
# then open http://localhost:8000/
```

The page reads `data/d1_stats.json` over `fetch`, so it must be served over HTTP (not `file://`).

## Refresh the data

```bash
python parse_weekly.py
```

The script downloads the latest Weekly Report of Registration PDF + the council district FeatureService GeoJSON, then parses the PDF into `data/d1_stats.json`. Requires `pdftotext` on PATH:

- Windows (Git Bash): already included in mingw64
- Linux: `sudo apt-get install poppler-utils`
- macOS: `brew install poppler`

GitHub Actions runs this automatically every Monday at 07:00 PT (the SBC report drops Sunday) — see `.github/workflows/refresh-weekly.yml`. No manual refresh needed once the site is deployed.

## Data sources

| File | Source | Cadence |
|---|---|---|
| `data/yucaipa_districts.geojson` | [SBC Open Data — Yucaipa CC Districts FeatureServer](https://services.arcgis.com/aA3snZwJfFkVyDuP/arcgis/rest/services/City_of_Yucaipa_City_Council_Districts/FeatureServer/0) | Rare (redistricting only) |
| `data/d1_stats.json` | Parsed from [Weekly Report of Registration](https://www.sbcounty.gov/uploads/rov/DistrictSummary.pdf) | Weekly |
| Precinct overlay | [SBC Registrar of Voters Precincts](https://services.arcgis.com/aA3snZwJfFkVyDuP/arcgis/rest/services/Registrar_of_Voters_Precincts/FeatureServer/0) (loaded live, no cached copy) | Updated by SBC ROV |
| ACS demographic overlays | Esri Living Atlas — [Population](https://www.arcgis.com/home/item.html?id=f430d25bf03744edbb1579e18c4bf6b8), [Income](https://www.arcgis.com/home/item.html?id=45ede6d6ff7e4cbbbffa60d34227e462), [Race](https://www.arcgis.com/home/item.html?id=23ab8028f1784de4b0810104cd5d1c8f), [Education](https://www.arcgis.com/home/item.html?id=84e3022a376e41feb4dd8addf25835a3), [Age](https://www.arcgis.com/home/item.html?id=d227d6a4ee3e4d2d87eb9843ee14dd87), [Poverty](https://www.arcgis.com/home/item.html?id=0e468b75bca545ee8dc4b039cbb5aff6) | US Census ACS 5-year |

## Other useful links

- City of Yucaipa Redistricting: <https://yucaipa.gov/yucaipa-redistricting/>
- Official 2016 District Boundary Map (PDF): <https://yucaipa.gov/wp-content/uploads/redistricting/2016_councilselectedmap.pdf>
- City's interactive "Find My District" lookup: <https://yucaipa.maps.arcgis.com/apps/instant/lookup/index.html?appid=e9ee0957ad4c4a39aed74fafd35051d5>
- SBC Voter Registration Dashboard (live): <https://elections.sbcounty.gov/voterregistration/dashboard/>
- District 1 Councilmember Bob Miller: <bmiller@yucaipa.gov> · 909-797-2489 ext. 501

## What's *not* possible

- "What party do the people at 123 Main St belong to?" — not public; only the Registrar (and qualifying recipients) sees that.
- Sub-precinct party splits — the smallest unit with publicly published party totals is the city council district itself.
