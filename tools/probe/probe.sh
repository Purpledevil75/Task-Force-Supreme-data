#!/bin/bash
# Check PING's documented public REST API (portail.ping-info-nautique.fr/static/an-api-rest-v2) and the TOS data-services section.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
U='https://services.ping-info-nautique.fr/nw/v2/Get_NW_Messages?nameOfSeries=NAVAREA%20II&lang=en'
curl -s -A "$UA" -w "\n[%{http_code} %{content_type} %{size_download}]\n" "$U" -o /tmp/n2.xml; tail -c 200 /tmp/n2.xml; echo
head -c 6000 /tmp/n2.xml; echo; echo ...
grep -o '<[A-Za-z:_]*' /tmp/n2.xml | sort | uniq -c | sort -rn | head -60
google-chrome --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --dump-dom https://portail.ping-info-nautique.fr/static/cgu 2>/dev/null | python3 -c "
import sys,re,html
s=sys.stdin.read(); s=re.sub(r'<(script|style)\b.*?</\1>','',s,flags=re.S)
t=re.sub(r'<br\s*/?>|</(p|div|li|h\d|tr|pre)>','\n',s); t=html.unescape(re.sub(r'<[^>]+>','',t))
t='\n'.join(l.strip() for l in t.split('\n') if l.strip())
i=t.find('DATA SERVICES',t.find('Glossary')); print(t[i-20:i+3500])"
