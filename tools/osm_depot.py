import json, math, os, sys
import xml.etree.ElementTree as ET
S = os.path.dirname(os.path.abspath(__file__))
root = ET.parse(S + '/osm/depot.osm').getroot()
nodes = {n.get('id'): (float(n.get('lon')), float(n.get('lat'))) for n in root.iter('node')}
rail, bld, other = [], [], []
for w in root.iter('way'):
    tags = {t.get('k'): t.get('v') for t in w.findall('tag')}
    pts = [nodes[nd.get('ref')] for nd in w.findall('nd') if nd.get('ref') in nodes]
    if 'railway' in tags:
        rail.append((tags, pts))
    elif 'building' in tags or tags.get('landuse') == 'railway' or 'depot' in json.dumps(tags).lower():
        bld.append((tags, pts))
from collections import Counter
print('railway ways', len(rail))
print(Counter((t.get('railway'), t.get('service'), t.get('usage')) for t, _ in rail).most_common(20))
names = Counter(t.get('name') for t, _ in rail if t.get('name'))
print(names.most_common(15))
# anything named like a depot
for t, pts in bld:
    s = json.dumps(t)
    if 'depot' in s.lower() or 'depoh' in s.lower() or 'rapid' in s.lower() or 'lrt' in s.lower() or t.get('landuse') == 'railway':
        lon = sum(p[0] for p in pts) / len(pts); lat = sum(p[1] for p in pts) / len(pts)
        print('AREA', round(lon, 5), round(lat, 5), {k: t[k] for k in list(t)[:6]})
# service tracks: bounding box and count
sv = [(t, p) for t, p in rail if t.get('service') in ('yard', 'siding', 'spur', 'crossover') or t.get('railway') in ('light_rail', 'subway') and t.get('service')]
print('service ways', len(sv))
if sv:
    lons = [p[0] for _, ps in sv for p in ps]; lats = [p[1] for _, ps in sv for p in ps]
    print('service bbox', min(lons), min(lats), max(lons), max(lats))
json.dump({'rail': [[t, p] for t, p in rail], 'bld': [[t, p] for t, p in bld]}, open(S + '/osm/depot.json', 'w'))
