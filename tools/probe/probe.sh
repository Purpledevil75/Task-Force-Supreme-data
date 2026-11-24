#!/bin/bash
# India NAVAREA VIII public page: locate the data the page's own custom element loads.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
B=https://hydrobharat.gov.in
mkdir -p /tmp/s; cd /tmp/s
curl -sL --max-time 60 -A "$UA" "$B/hi/navarea-warnings" -o in.html
echo "== custom element / client extension refs"
grep -oE 'india[_-]wins[^"'"'"' <>]{0,120}' in.html | sort -u | head -20
grep -oE '"[^"]*/o/[^"]*\.(js|css)[^"]*"' in.html | grep -iv 'frontend-js\|frontend-theme\|clay\|lexicon' | sort -u | head -20
grep -oE '<[a-z-]*wins[a-z-]*[^>]*>' in.html | head
for u in $(grep -oE '/o/[A-Za-z0-9_.-]*wins[^"'"'"' ]*\.js' in.html | sort -u); do
  echo "== JS $u"; curl -sL --max-time 60 -A "$UA" "$B$u" -o el.js; wc -c el.js
  grep -oE '"[^"]{0,40}(/o/|/api/|headless|navarea|warnings|fetch)[^"]{0,120}"|`[^`]{0,40}(/o/|/api/|navarea|warnings)[^`]{0,160}`' el.js | sort -u | head -40
done
echo "== in-force document"; curl -sIL --max-time 60 -A "$UA" "$B/documents/d/guest/in-force-navarea-viii-warnings-2" | grep -iE '^(HTTP|content-type|content-length|last-modified)'
