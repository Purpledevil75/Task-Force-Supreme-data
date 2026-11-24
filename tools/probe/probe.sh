#!/bin/bash
python3 - <<'PY'
import importlib.util,json
spec=importlib.util.spec_from_file_location('f','tools/navwarn/fetch.py'); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
r=f.sanho(); print(len(r), [m['ref'] for m in r])
for m in r:
    if m['num'] in (14,221,330): print(json.dumps(m,ensure_ascii=False))
PY
