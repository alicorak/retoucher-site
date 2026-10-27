#!/bin/sh
# Run once Figma approves the Community listing: merges the community-link
# branches into main in both repos and pushes (the site redeploys on GitHub Pages),
# then publishes the npm package with a one-off token.
set -e
cd "$(dirname "$0")/.."
git checkout -q main && git pull -q && git fetch -q origin && git merge -q --no-edit origin/community-link
git push -q origin main
cd "../retoucher"
git checkout -q main && git fetch -q public && git merge -q --no-edit public/community-link
git push -q public main
echo "Done: site and README now link to the Community page."
echo
echo "npm: paste a one-off token from npmjs.com and press Enter (it isn't shown; Enter alone skips):"
stty -echo; read -r T; stty echo; echo
if [ -n "$T" ]; then
  (cd npm && npm publish --access public "--//registry.npmjs.org/:_authToken=$T")
  unset T
  echo "Published. Delete the token on npmjs.com > Access Tokens."
else
  echo "Skipped npm."
fi
