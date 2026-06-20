# refresh.ps1 - Re-pull the public SBC voter aggregates and rebuild data/d1_stats.json.
# Run from the project root:  pwsh ./refresh.ps1

$ErrorActionPreference = "Stop"
$root  = Split-Path -Parent $MyInvocation.MyCommand.Path
$data  = Join-Path $root "data"
New-Item -ItemType Directory -Force -Path $data | Out-Null

$weeklyUrl   = "https://www.sbcounty.gov/uploads/rov/DistrictSummary.pdf"
$precinctUrl = "https://uploads.rov.sbcounty.gov/ROV/PrecinctDistrictExport.zip"
$boundUrl    = "https://services.arcgis.com/aA3snZwJfFkVyDuP/arcgis/rest/services/City_of_Yucaipa_City_Council_Districts/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&outSR=4326"

Write-Host "[1/3] Boundary GeoJSON..."
Invoke-WebRequest -Uri $boundUrl -OutFile (Join-Path $data "yucaipa_districts.geojson")

Write-Host "[2/3] Weekly Report PDF..."
Invoke-WebRequest -Uri $weeklyUrl -OutFile (Join-Path $data "DistrictSummary.pdf")

Write-Host "[3/3] Precinct & District Export..."
Invoke-WebRequest -Uri $precinctUrl -OutFile (Join-Path $data "PrecinctDistrictExport.zip")
Expand-Archive -Force -Path (Join-Path $data "PrecinctDistrictExport.zip") -DestinationPath $data

Write-Host ""
Write-Host "Files refreshed in $data."
Write-Host "Re-parse the PDF with parse_weekly.py to rebuild d1_stats.json, then reload index.html."
