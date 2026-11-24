#!/bin/bash
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
B=https://portail.ping-info-nautique.fr
mkdir -p /tmp/p; cd /tmp/p
curl -sL -A "$UA" $B/ -o index.html
grep -oE '(src|href)="[^"]+"' index.html | grep -v fonts | cut -d'"' -f2 | sort -u
for s in $(grep -oE '(src|href)="[^"]+\.js"' index.html | cut -d'"' -f2); do curl -sL -A "$UA" "$B/${s#/}" -o "$(basename $s)"; done
# follow chunk imports
for k in 1 2; do for f in *.js; do grep -oE '"\./[A-Za-z0-9_-]+\.js"' $f | tr -d '"' | sed 's#^\./##'; done | sort -u | while read c; do [ -f "$c" ] || curl -sL -A "$UA" "$B/$c" -o "$c"; done; done
ls -la | wc -l
echo "== strings"
cat *.js | grep -oE '"[^"]{0,100}(api|API|navarea|NAVAREA|avurnav|config\.json|keycloak|realm|/auth|rootUrl|environment|\.json)[^"]{0,100}"' | sort -u | head -150
echo "== backtick"
cat *.js | grep -oE '`[^`]{0,100}(api|navarea|avurnav|/v[0-9])[^`]{0,100}`' | sort -u | head -60
for p in assets/config.json assets/env.json assets/environment.json config.json; do echo "== $p"; curl -s -A "$UA" -w " [%{http_code}]" $B/$p | head -c 1500; echo; done
