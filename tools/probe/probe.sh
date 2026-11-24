#!/bin/bash
# Fetch a public page and show its structure.
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
curl -sL -A "$UA" -w "\n[%{http_code} %{size_download}]\n" https://nha.gov.ng/navarea-ii-warnings/ -o /tmp/nha.html; tail -c 100 /tmp/nha.html
python3 - <<'PY'
s=open('/tmp/nha.html',encoding='utf8',errors='replace').read()
i=s.find('411/26'); j=s.find('298/26')
print('len',len(s),i,j)
print(s[max(0,i-3000):i+2500])
print('#######'); print(s[max(0,j-1500):j+800])
PY
