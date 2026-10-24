#!/usr/bin/env bash
# Moves the site from alicorak.github.io/retoucher-site to retoucher.alicorak.com once the DNS record exists
# (CNAME retoucher -> alicorak.github.io.). Safe to run again: each step checks whether it is already done.
set -euo pipefail
DOMAIN=retoucher.alicorak.com
OLD=https://alicorak.github.io/retoucher-site/
NEW=https://$DOMAIN/
SITE="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_REPO="${PLUGIN_REPO:-$HOME/Figma Designs/figma-annotate}"

if [ "$(dig +short "$DOMAIN" CNAME)" != "alicorak.github.io." ]; then
  echo "waiting: $DOMAIN has no CNAME to alicorak.github.io yet"
  exit 0
fi

cd "$SITE"
if [ ! -f CNAME ]; then
  echo "$DOMAIN" > CNAME
  grep -rl "$OLD" --include='*.html' --include='*.txt' --include='*.xml' . | xargs perl -pi -e "s{\Q$OLD\E}{$NEW}g"
  git add -A
  git commit -qm "Serve from $DOMAIN" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
  git push -q
  echo "site files point at $DOMAIN"
fi

if [ "$(gh api repos/alicorak/retoucher-site/pages --jq .cname)" != "$DOMAIN" ]; then
  gh api -X PUT repos/alicorak/retoucher-site/pages -f cname="$DOMAIN" >/dev/null
  gh repo edit alicorak/retoucher-site --homepage "$NEW"
  gh repo edit alicorak/retoucher --homepage "$NEW"
  echo "pages domain set"
fi

if [ -d "$PLUGIN_REPO" ] && grep -q "$OLD" "$PLUGIN_REPO/README.md"; then
  perl -pi -e "s{\Q$OLD\E}{$NEW}g" "$PLUGIN_REPO/README.md"
  git -C "$PLUGIN_REPO" add README.md
  git -C "$PLUGIN_REPO" commit -qm "README: website at $DOMAIN" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
  git -C "$PLUGIN_REPO" push -q public main
  echo "plugin README links updated"
fi

# GitHub issues the certificate a while after the domain is set; enforcing HTTPS fails until then
if [ "$(gh api repos/alicorak/retoucher-site/pages --jq .https_enforced)" != "true" ]; then
  if gh api -X PUT repos/alicorak/retoucher-site/pages -F https_enforced=true >/dev/null 2>&1; then
    echo "https enforced"
  else
    echo "waiting: certificate for $DOMAIN not issued yet"
    exit 0
  fi
fi
echo "done: $NEW"
