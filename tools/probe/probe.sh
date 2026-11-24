#!/bin/bash
# India NAVAREA VIII: read the page's own custom-element script to see where its table data comes from.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
B=https://hydrobharat.gov.in
cd /tmp
curl -sL --max-time 60 -A "$UA" "$B/o/india-wins-custom-element/js/main.89cfce1b.js?t=1794553193908" -o el.js; wc -c el.js; head -c 300 el.js; echo
grep -oE '"[^"]{0,60}(/o/|/api/|headless|navarea|NAVAREA|warning|Warning|\.json|webdav)[^"]{0,160}"|`[^`]{0,60}(/o/|/api/|navarea|warning|webdav)[^`]{0,200}`' el.js | sort -u | head -60
python3 - <<'PY'
import re
s=open('/tmp/el.js',encoding='utf8',errors='replace').read()
for k in ['fetch(','axios','XMLHttpRequest','webdav','api/jsonws','headless']:
    for m in list(re.finditer(re.escape(k),s))[:3]:
        print('##',k,':',s[max(0,m.start()-250):m.start()+350].replace('\n',' '))
PY
