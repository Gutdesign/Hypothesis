# Rebuild the market map and publish ONLY site files to the gh-pages branch of origin.
# main is not pushed, so the rest of the repo (hypotheses, retrospectives) stays local.
# Usage: powershell -File scripts/publish_map.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
python scripts/registry.py build
python scripts/build_map.py
$origin = git remote get-url origin
$tmp = Join-Path $env:TEMP "gh-pages-publish"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Path $tmp | Out-Null
Copy-Item -Path "site/index.html", "site/registry.csv", "site/.nojekyll" -Destination $tmp -Force
if (Test-Path "site/charts") { Copy-Item -Path "site/charts" -Destination $tmp -Recurse -Force }
Push-Location $tmp
git init -q -b gh-pages
git add -A
git commit -q -m "publish market map"
git remote add origin $origin
git push --force origin gh-pages
Pop-Location
