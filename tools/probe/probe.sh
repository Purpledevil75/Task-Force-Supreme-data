#!/bin/bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
B=https://portail.ping-info-nautique.fr
mkdir -p /tmp/p; cd /tmp/p
curl -sL -A "$UA" $B/ -o index.html
for s in $(grep -oE '(src|href)="[^"]+\.js"' index.html | cut -d'"' -f2); do curl -sL -A "$UA" "$B/${s#/}" -o "$(basename $s)"; done
for k in 1 2 3; do for f in *.js; do grep -oE '"\./[A-Za-z0-9_-]+\.js"' $f | tr -d '"' | sed 's#^\./##'; done | sort -u | while read c; do [ -f "$c" ] || curl -sL -A "$UA" "$B/$c" -o "$c"; done; done
cat *.js > all.txt
echo "== api object"
python3 - <<'PY'
s=open('/tmp/p/all.txt',encoding='utf8',errors='replace').read()
i=s.find('staticSection:{findByKey')
print(s[max(0,i-3000):i+3000] if i>=0 else 'nf')
for k in ['warning','Warning']:
    import re
    for m in sorted(set(re.findall(r'[A-Za-z]{2,40}:"[^"]{0,80}'+k+r'[^"]{0,80}"',s)))[:80]: print(m)
PY
