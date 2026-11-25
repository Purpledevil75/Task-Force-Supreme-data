#!/bin/bash
# rosatomport.ru NAVAREA XX/XXI and PRIP pages: format, count, freshness, stability.
export LC_ALL=C.UTF-8
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
mkdir -p /tmp/r; cd /tmp/r
for p in page149739436.html page148594096.html page148590696.html; do
  for k in 1 2; do curl -sL --max-time 60 -A "$UA" -o $p.$k -w "== $p try$k: %{http_code} %{content_type} %{size_download}B\n" "https://rosatomport.ru/$p"; sleep 5; done
  cmp -s $p.1 $p.2 && echo "   identical" || echo "   DIFFERENT between fetches"
  python3 - $p.1 <<'PY'
import sys,re,html
s=open(sys.argv[1],'rb').read().decode('utf-8','replace')
for h in sorted(set(re.findall(r'(?:href|src|data-[a-z-]*)="([^"]+\.(?:pdf|txt|json|xml|docx?|xlsx?)[^"]*)"',s))): print('  FILE',h)
t=html.unescape(re.sub(r'<br\s*/?>|</(p|div|li|tr|h\d)>','\n',re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S)))
t=re.sub(r'<[^>]+>','',t); t='\n'.join(' '.join(l.split()) for l in t.split('\n') if l.strip())
i=max(t.find('NAVAREA'),0)
print(t[i:i+3500] if 'NAVAREA' in t else t[:2500])
PY
done
