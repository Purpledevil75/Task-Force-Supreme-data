#!/bin/bash
# Render a public documentation page (single-page app) in headless Chrome and print its text.
U=https://portail.ping-info-nautique.fr/static/data-services
google-chrome --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --dump-dom "$U" > /tmp/page.html 2>/dev/null
python3 - <<'PY'
import re,html
s=open('/tmp/page.html',encoding='utf8',errors='replace').read()
s=re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S)
links=sorted(set(re.findall(r'href="(https?://[^"]+)"',s)))
t=re.sub(r'<br\s*/?>|</(p|div|li|h\d|tr)>','\n',s); t=html.unescape(re.sub(r'<[^>]+>','',t))
t='\n'.join(l.strip() for l in t.split('\n') if l.strip())
print(t[:8000]); print('== links'); print('\n'.join(links))
PY
