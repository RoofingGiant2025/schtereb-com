#!/bin/sh
# Rebuild and publish schtereb.com to the Hostinger host (SSH alias "roofinggiant").
set -e
cd "$(dirname "$0")"
python3 tools/build_content.py
python3 tools/build_site.py
rsync -az --delete --exclude '*.sha' -e ssh docs/ roofinggiant:~/domains/schtereb.com/public_html/
echo "deployed $(find docs -type f | wc -l | tr -d ' ') files to schtereb.com"
