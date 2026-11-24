#!/bin/bash
# Render public PING documentation pages (single-page app) in headless Chrome; print text.
dump() { google-chrome --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --dump-dom "$1" 2>/dev/null | python3 -c "
import sys,re,html
s=sys.stdin.read(); s=re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S)
s=re.sub(r'<a\b[^>]*href=\"([^\"]+)\"[^>]*>',r' [\1] ',s)
t=re.sub(r'<br\s*/?>|</(p|div|li|h\d|tr|pre)>','\n',s); t=html.unescape(re.sub(r'<[^>]+>','',t))
print('\n'.join(l.strip() for l in t.split('\n') if l.strip()))"; }
echo "== CGU section 9"; dump https://portail.ping-info-nautique.fr/static/cgu | sed -n '/^9 *DATA SERVICES/,/^10 /p' | head -60
for p in an-api-rest-v2 s124-2-0; do echo "== $p"; dump https://portail.ping-info-nautique.fr/static/$p | sed -n '/Data Services/,$p' | head -170; done
