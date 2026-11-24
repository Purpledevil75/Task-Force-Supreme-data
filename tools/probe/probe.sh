#!/bin/bash
# Ad-hoc source probe: prints responses to the workflow log.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
B=https://portail.ping-info-nautique.fr
echo "== index"; curl -sL -A "$UA" $B/ | head -c 4000; echo
for s in $(curl -sL -A "$UA" $B/ | grep -oE '(src|href)="[^"]+\.(js|json)"' | cut -d'"' -f2); do
  u=$s; [[ $u == http* ]] || u=$B/${s#/}
  echo "== $u"; f=$(mktemp); curl -sL -A "$UA" "$u" -o $f; wc -c < $f
  grep -oE '"https?://[^"]{4,120}"|/api/[A-Za-z0-9_/.-]{2,80}|rootUrl[^,]{0,120}|baseURL[^,]{0,120}|apiUrl[^,]{0,120}|realm[^,]{0,80}|clientId[^,]{0,80}' $f | sort -u | head -80
done
for p in config.json env.json assets/config.json config/config.json app-config.json; do echo "== $p"; curl -s -A "$UA" -o /dev/stdout -w " [%{http_code}]" $B/$p | head -c 1500; echo; done
