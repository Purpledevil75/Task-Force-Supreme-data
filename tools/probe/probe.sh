#!/bin/bash
# Survey of candidate NAVAREA sources (public pages / files). Prints format, structure and samples.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
mkdir -p /tmp/s; cd /tmp/s
g() { curl -sL --max-time 60 -A "$UA" -w "\n[%{http_code} %{content_type} %{size_download}B %{time_total}s]\n" "$1" -o "$2"; tail -c 120 "$2" | tail -1; }
echo "==== V Brazil page"; g 'https://www.marinha.mil.br/chm/dados-do-segnav-aviso-radio-nautico-tela/avisos-radio-nauticos-e-sar' br.html
grep -oE '[^"'"'"' ]*avradio[^"'"'"' ]*' br.html | sort -u | head
echo "==== V Brazil JSON"; g 'https://www.marinha.mil.br/chm/sites/www.marinha.mil.br.chm/files/2026-11-%5BDEV%5D/avradio_65.json' br.json
python3 - <<'PY'
import json
s=open('/tmp/s/br.json','rb').read()
print('bytes',len(s), s[:300])
try:
    d=json.loads(s.decode('utf-8-sig'))
except Exception as e:
    print('JSON ERR',e); raise SystemExit
def show(x,depth=0,key='root'):
    if depth>3: return
    if isinstance(x,dict):
        print('  '*depth+key,'dict',list(x.keys())[:30])
        for k,v in list(x.items())[:30]: show(v,depth+1,k)
    elif isinstance(x,list):
        print('  '*depth+key,'list',len(x))
        if x: show(x[0],depth+1,key+'[0]')
show(d)
items=d if isinstance(d,list) else next((v for v in d.values() if isinstance(v,list)),[])
from collections import Counter
for k in (items[0].keys() if items and isinstance(items[0],dict) else []):
    vals=Counter(str(i.get(k))[:40] for i in items)
    if len(vals)<15: print('FIELD',k,dict(vals))
print(json.dumps(items[:2],ensure_ascii=False,indent=1)[:5000])
PY
echo "==== VII South Africa"; g 'https://www.sanho.co.za/notices_mariners/navarea_v11_messages.htm' za.html
python3 -c "
import re,html
s=open('/tmp/s/za.html',encoding='utf8',errors='replace').read()
t=re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S|re.I); t=re.sub(r'<br\s*/?>|</(p|div|tr|li|h\d|pre)>','\n',t,flags=re.I); t=html.unescape(re.sub(r'<[^>]+>','',t))
t='\n'.join(l.strip() for l in t.split('\n') if l.strip()); print(len(t)); print(t[:5000]); print('.....'); print(t[-2500:])"
echo "==== VIII India hi"; g 'https://hydrobharat.gov.in/hi/navarea-warnings' in.html
grep -oiE '(src|href|action|url)[=:] *["'"'"'][^"'"'"']*(ajax|api|json|views|navarea)[^"'"'"']*' in.html | sort -u | head -30
python3 -c "
import re,html
s=open('/tmp/s/in.html',encoding='utf8',errors='replace').read()
i=s.find('<table'); print('table at',i); print(s[i:i+4000])
m=re.search(r'drupal-settings-json[^>]*>(.*?)</script>',s,re.S); print('settings',(m.group(1)[:3000] if m else None))"
echo "==== VIII India en"; g 'https://hydrobharat.gov.in/navarea-warnings' in_en.html
echo "==== XV Chile"; g 'https://www.shoa.mil.cl/php/radioavisos.php?idioma=es' cl.html; head -c 1500 cl.html
