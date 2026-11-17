import json, math, os, re, collections
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
        for dx in range(-5, 6):
            for dz in range(-5, 6): near.add((int(x // CELL) + dx, int(z // CELL) + dz))
inn = lambda p: (int(p[0] // CELL), int(p[1] // CELL)) in near
def dline(p):
    best = 1e9
    for i in range(len(line) - 1):
        a, b = line[i], line[i + 1]; dx, dz = b[0] - a[0], b[1] - a[1]; l2 = dx * dx + dz * dz
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / l2)) if l2 else 0
        best = min(best, math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dz * t))
    return best
def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1e-9; k, dm = 0, 0
    for i in range(1, len(pts) - 1):
        dd = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / l
        if dd > dm: k, dm = i, dd
    return [a, b] if dm <= eps else rdp(pts[:k + 1], eps)[:-1] + rdp(pts[k:], eps)
ways = []; names = collections.Counter(); marks = []
PAT = re.compile(r'Menara Kuala Lumpur|KL Tower|Merdeka 118|Exchange 106|Petronas Twin|Menara Berkembar', re.I)
class H(osmium.SimpleHandler):
    def node(self, n):
        nm = n.tags.get('name', '') + ' ' + n.tags.get('name:en', '')
        if PAT.search(nm) and 101.6 < n.location.lon < 101.78: marks.append(('node', nm.strip(), n.location.lon, n.location.lat, dict(n.tags).get('tourism', '') + dict(n.tags).get('building', '')))
    def way(self, w):
        t = w.tags
        nm = t.get('name', '') + ' ' + t.get('name:en', '')
        if PAT.search(nm) and ('building' in t or 'man_made' in t):
            try: marks.append(('way', nm.strip(), sum(n.location.lon for n in w.nodes) / len(w.nodes), sum(n.location.lat for n in w.nodes) / len(w.nodes), t.get('building', '') + t.get('man_made', '') + ' h=' + t.get('height', '')))
            except Exception: pass
        rw = t.get('railway')
        if rw not in ('light_rail', 'subway', 'monorail', 'rail') or t.get('service') in ('yard', 'siding', 'spur'): return
        try:
            n0 = w.nodes[0].location
            if not (101.53 < n0.lon < 101.78 and 2.96 < n0.lat < 3.27): return
            pts = [((n.location.lon - lon0) * KX, -(n.location.lat - lat0) * KZ) for n in w.nodes]
        except Exception: return
        pts = [p for p in pts if inn(p)]
        if len(pts) < 2: return
        if rw == 'light_rail' and sum(dline(p) < 22 for p in pts) / len(pts) > .6: return      # the Kelana Jaya Line itself
        lvl = 'u' if t.get('tunnel') == 'yes' else 'e' if t.get('bridge') in ('yes', 'viaduct') else 'g'
        key = (rw, t.get('name', ''), t.get('operator', '')); names[key] += 1
        ways.append({'rw': rw, 'name': t.get('name', ''), 'lvl': lvl, 'pts': rdp(pts, 2)})
H().apply_file(S + '/bld/my.osm.pbf', locations=True, idx='flex_mem')
for k, v in names.most_common(40): print(v, k)
print('MARKS'); [print(m) for m in marks[:30]]
json.dump({'ways': ways, 'marks': marks}, open(S + '/bld/rail.json', 'w'))
