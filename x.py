import json
import taichi.aot.sr.gfxruntime140 as sr
import taichi.aot.dr.gfxruntime140 as dr
import taichi as ti

with open('tmp/x/modulef/metadata.json') as f:
    j = json.load(f)
    d = dr.Metadata(j)
    s = sr.from_dr_metadata(d)
    dd = sr.to_dr_metadata(s)
    jj = dr.to_json(dd)

with open('tmp/x/modulef/metadata.edited.json', 'w') as f:
    json.dump(jj, f, indent=4)
