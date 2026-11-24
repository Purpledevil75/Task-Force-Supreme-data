#!/bin/bash
# Render public PING documentation pages (single-page app) in headless Chrome; print links and text.
dump() { google-chrome --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --dump-dom "$1" 2>/dev/null; }
dump https://portail.ping-info-nautique.fr/static/data-services > /tmp/ds.html
python3 - <<'PY'
import re
s=open('/tmp/ds.html',encoding='utf8',errors='replace').read()
for m in re.finditer(r'<a\b[^>]*>.*?</a>',s,re.S):
    a=m.group(0)
    if 'Support' in a or 'href' in a and ('static' in a or 'api' in a or 'pdf' in a.lower() or 'cgu' in a.lower() or 'TOS' in a): print(re.sub(r'\s+',' ',a)[:300])
PY
for p in static/cgu static/tos static/legal-notice static/mentions-legales; do echo "== $p"; dump https://portail.ping-info-nautique.fr/$p | python3 -c "
import sys,re,html
s=sys.stdin.read(); s=re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S)
t=re.sub(r'<br\s*/?>|</(p|div|li|h\d|tr)>','\n',s); t=html.unescape(re.sub(r'<[^>]+>','',t))
t='\n'.join(l.strip() for l in t.split('\n') if l.strip()); i=t.find('Home\n'); print(t[:6000])"; done
