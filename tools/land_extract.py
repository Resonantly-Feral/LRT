import json, math, os, re
import osmium
S = os.path.dirname(os.path.abspath(__file__))
st = json.load(open(S + '/data/stations.json')); r = json.load(open(S + '/data/route.json'))
KX = math.cos(math.radians(3.15)) * 111320; KZ = 110574; lon0, lat0 = st[0][2], st[0][3]
line = []
for i, s in enumerate(st):
    line.append(((s[2] - lon0) * KX, -(s[3] - lat0) * KZ))
    if i < len(st) - 1: line += [tuple(v) for v in r['vias'][i]]
CELL = 150; near = set()
for i in range(len(line) - 1):
    a, b = line[i], line[i + 1]; n = int(math.dist(a, b) / 60) + 1
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n; z = a[1] + (b[1] - a[1]) * k / n
        for dx in range(-3, 4):
            for dz in range(-3, 4): near.add((int(x // CELL) + dx, int(z // CELL) + dz))
inn = lambda p: (int(p[0] // CELL), int(p[1] // CELL)) in near
def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1e-9; k, dm = 0, 0
    for i in range(1, len(pts) - 1):
        dd = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / l
        if dd > dm: k, dm = i, dd
    return [a, b] if dm <= eps else rdp(pts[:k + 1], eps)[:-1] + rdp(pts[k:], eps)
ROAD = {'motorway': 15, 'trunk': 15, 'primary': 12, 'secondary': 9, 'tertiary': 7, 'motorway_link': 6, 'trunk_link': 6, 'primary_link': 6, 'residential': 5, 'unclassified': 5}
out = {'road': {}, 'river': [], 'park': [], 'water': [], 'names': set()}
class H(osmium.SimpleHandler):
    def way(self, w):
        t = w.tags; hw = t.get('highway'); ww = t.get('waterway')
        park = t.get('leisure') in ('park', 'garden', 'golf_course', 'pitch') or t.get('landuse') in ('forest', 'grass', 'recreation_ground', 'cemetery') or t.get('natural') == 'wood'
        water = t.get('natural') == 'water'
        if not ((hw in ROAD) or ww in ('river', 'canal') or park or water): return
        try:
            n0 = w.nodes[0].location
            if not (101.53 < n0.lon < 101.78 and 2.96 < n0.lat < 3.27): return
            pts = [((n.location.lon - lon0) * KX, -(n.location.lat - lat0) * KZ) for n in w.nodes]
        except Exception: return
        if park or water:
            if len(pts) < 4 or pts[0] != pts[-1]: return
            c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2
            if not inn(c) or area < 1500: return
            out['water' if water else 'park'].append(rdp(pts[:-1], 6))
            if water and t.get('name'): out['names'].add(t.get('name'))
            return
        if t.get('tunnel') in ('yes', 'culvert'): return
        runs, cur = [], []
        for p in pts:
            if inn(p): cur.append(p)
            else:
                if len(cur) > 1: runs.append(cur)
                cur = []
        if len(cur) > 1: runs.append(cur)
        for run in runs:
            run = rdp(run, 2.5)
            if hw: out['road'].setdefault(ROAD[hw], []).append(run)
            else:
                out['river'].append(run)
                if t.get('name'): out['names'].add(t.get('name'))
H().apply_file(S + '/bld/my.osm.pbf', locations=True, idx='flex_mem')
SC = .35; q = lambda run: [round(v * SC * 10) for p in run for v in p]
res = {'road': {str(k): [q(x) for x in v] for k, v in out['road'].items()}, 'river': [q(x) for x in out['river']], 'park': [q(x) for x in out['park']], 'water': [q(x) for x in out['water']]}
for k, v in out['road'].items(): print('road width', k, 'ways', len(v), 'pts', sum(len(x) for x in v))
for k in ('river', 'park', 'water'): print(k, len(out[k]), 'pts', sum(len(x) for x in out[k]))
print('names', sorted(out['names'])[:30])
for k in list(res['road']):
    print(k, len(json.dumps(res['road'][k], separators=(',', ':'))))
json.dump(res, open(S + '/bld/land.json', 'w'), separators=(',', ':'))
print('total bytes', os.path.getsize(S + '/bld/land.json'))
