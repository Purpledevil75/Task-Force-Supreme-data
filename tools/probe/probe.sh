#!/bin/bash
# NAVAREA VII adapter check: 3 fetches 2 min apart, compare, print parsed messages.
python3 - <<'PY'
import importlib.util,json,hashlib,time
spec=importlib.util.spec_from_file_location('f','tools/navwarn/fetch.py'); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
hs=[]
for k in range(3):
    r=f.sanho(); hs.append(hashlib.md5(json.dumps(r,sort_keys=True).encode()).hexdigest()); print('fetch',k+1,len(r),hs[-1], flush=True)
    if k<2: time.sleep(60)
print('stable', len(set(hs))==1)
for m in r: print(json.dumps(m,ensure_ascii=False))
PY
