#!/bin/bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
B=https://portail.ping-info-nautique.fr
mkdir -p /tmp/p; cd /tmp/p
curl -sL -A "$UA" $B/ -o index.html
for s in $(grep -oE '(src|href)="[^"]+\.js"' index.html | cut -d'"' -f2); do curl -sL -A "$UA" "$B/${s#/}" -o "$(basename $s)"; done
for k in 1 2 3; do for f in *.js; do grep -oE '"\./[A-Za-z0-9_-]+\.js"' $f | tr -d '"' | sed 's#^\./##'; done | sort -u | while read c; do [ -f "$c" ] || curl -sL -A "$UA" "$B/$c" -o "$c"; done; done
echo "== env"
cat *.js | grep -oE '.{0,300}rootUrl:"[^"]*".{0,600}' | head -5
echo "== baseApiUrl"
cat *.js | grep -oE '.{0,200}baseApiUrl.{0,300}' | head -5
echo "== public warning api"
cat *.js | grep -oE '[A-Za-z]+:"/(api|public)[^"]*"' | sort -u | head -120
cat *.js | grep -oE '"/(api|public-api)/[^"]*"' | sort -u | head -80
