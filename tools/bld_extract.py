import json, math, os, re, sys
import osmium
S = os.path.dirname(os.path.abspath(__file__))
st = json.load(open(S + '/data/stations.json')); r = json.load(open(S + '/data/route.json'))
KX = math.cos(math.radians(3.15)) * 111320; KZ = 110574; lon0, lat0 = st[0][2], st[0][3]
line = []
for i, s in enumerate(st):
    line.append(((s[2] - lon0) * KX, -(s[3] - lat0) * KZ))
    if i < len(st) - 1:
        line += [tuple(v) for v in r['vias'][i]]
# coarse grid of the corridor for a fast distance test
CELL = 300; near = set()
for i in range(len(line) - 1):
    a, b = line[i], line[i + 1]; n = int(math.dist(a, b) / 100) + 1
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n; z = a[1] + (b[1] - a[1]) * k / n
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1): near.add((int(x // CELL) + dx, int(z // CELL) + dz))
def dline(p):
    best = 1e9
    for i in range(len(line) - 1):
        a, b = line[i], line[i + 1]; dx, dz = b[0] - a[0], b[1] - a[1]; l2 = dx * dx + dz * dz
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / l2)) if l2 else 0
        d = math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dz * t)
        if d < best: best = d
    return best
def num(s):
    m = re.match(r'\s*([\d.]+)', s or ''); return float(m.group(1)) if m else None
out = []; stats = {'h': 0, 'lv': 0, 'none': 0}
class H(osmium.SimpleHandler):
    def way(self, w):
        if 'building' not in w.tags or len(w.nodes) < 4: return
        try:
            n0 = w.nodes[0].location
            if not (101.54 < n0.lon < 101.77 and 2.97 < n0.lat < 3.26): return
            pts = [((n.location.lon - lon0) * KX, -(n.location.lat - lat0) * KZ) for n in w.nodes]
        except Exception: return
        cx = sum(p[0] for p in pts[:-1]) / (len(pts) - 1); cz = sum(p[1] for p in pts[:-1]) / (len(pts) - 1)
        if (int(cx // CELL), int(cz // CELL)) not in near: return
        d = dline((cx, cz))
        if d > 270: return
        best = None
        for i in range(len(pts) - 1):
            ex, ez = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]; l = math.hypot(ex, ez)
            if l < .5: continue
            ux, uz = ex / l, ez / l
            us = [p[0] * ux + p[1] * uz for p in pts]; vs = [-p[0] * uz + p[1] * ux for p in pts]
            W, Dp = max(us) - min(us), max(vs) - min(vs)
            if best is None or W * Dp < best[0]:
                mu, mv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
                best = (W * Dp, mu * ux - mv * uz, mu * uz + mv * ux, W, Dp, math.atan2(uz, ux))
        if not best: return
        area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2
        h = num(w.tags.get('height')); lv = num(w.tags.get('building:levels'))
        if h: stats['h'] += 1
        elif lv: h = lv * 3.6 + 2; stats['lv'] += 1
        else: h = 0; stats['none'] += 1
        out.append({'x': best[1], 'z': best[2], 'w': best[3], 'd': best[4], 'a': best[5], 'h': h, 'area': area, 'fill': area / max(best[0], 1), 'dist': d,
                    'name': w.tags.get('name', ''), 'type': w.tags.get('building')})
H().apply_file(S + '/bld/my.osm.pbf', locations=True, idx='flex_mem')
json.dump(out, open(S + '/bld/near.json', 'w'))
print('buildings near line', len(out), stats)
tall = sorted([o for o in out if o['h']], key=lambda o: -o['h'])[:25]
for o in tall: print(round(o['h']), round(o['area']), o['name'][:40], round(o['dist']))
