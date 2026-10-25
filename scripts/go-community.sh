#!/bin/sh
# Run once Figma approves the Community listing: merges the community-link
# branches into main in both repos and pushes (the site redeploys on GitHub Pages).
set -e
cd "$(dirname "$0")/.."
git checkout -q main && git pull -q && git merge -q --ff-only origin/community-link 2>/dev/null || git merge -q origin/community-link
git push -q origin main
cd "../retoucher"
git checkout -q main && git merge -q public/community-link
git push -q public main
echo "Done: site and README now link to the Community page."
