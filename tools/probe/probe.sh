#!/bin/bash
python3 -c "
import importlib.util,json
spec=importlib.util.spec_from_file_location('f','tools/navwarn/fetch.py'); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
r,note=f.ping(); print(len(r),note)
for m in r: print(json.dumps(m,ensure_ascii=False))
"
# 2
