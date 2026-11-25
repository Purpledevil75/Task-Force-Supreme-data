#!/bin/bash
# NAVAREA VIII (India, NHO): what the "In-Force Navarea VIII Warnings" download is
cd /tmp
for u in "https://hydrobharat.gov.in/documents/d/guest/in-force-navarea-viii-warnings-2" "https://hydrobharat.gov.in/navarea-warnings"; do
  echo "== $u"; curl -sSL -A "TaskForceSupreme-data/1.0 (+https://github.com/Purpledevil75/Task-Force-Supreme-data)" -D h.txt -o f.bin -w "%{http_code} %{content_type} %{size_download}\n" "$u"; grep -iE "^(content-type|content-disposition|last-modified|etag)" h.txt
  file f.bin; head -c 300 f.bin | tr -c '[:print:]\n' '.'; echo
  if file f.bin | grep -q PDF; then sudo apt-get install -y -qq poppler-utils >/dev/null 2>&1; pdfinfo f.bin | head -8; pdftotext -layout f.bin - | head -80; pdftotext f.bin - | grep -cE "NAVAREA VIII ?[0-9]+"; fi
  if file f.bin | grep -qi html; then grep -oiE 'href="[^"]*(documents|navarea)[^"]*"' f.bin | sort -u | head -20; fi
done
