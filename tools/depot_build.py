import json, math, os
S = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(S + '/osm/depot.json'))
st = json.load(open(S + '/data/stations.json'))
KX = math.cos(math.radians(3.15)) * 111320
KZ = 110574
lonS, latS = st[24][2], st[24][3]          # Lembah Subang


def rel(p):
    return ((p[0] - lonS) * KX, -(p[1] - latS) * KZ)


def inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
    return c


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1e-9
    k, dm = 0, 0
    for i in range(1, len(pts) - 1):
        dd = abs((pts[i][0] - a[0]) * dy - (pts[i][1] - a[1]) * dx) / l
        if dd > dm:
            k, dm = i, dd
    if dm <= eps:
        return [a, b]
    return rdp(pts[:k + 1], eps)[:-1] + rdp(pts[k:], eps)


poly = None
for t, pts in d['bld']:
    if t.get('name') == 'Kompleks Rapid Rail Subang':
        poly = [rel(p) for p in pts]
assert poly
ways = []
for t, pts in d['rail']:
    if t.get('railway') != 'light_rail' or not t.get('service'):
        continue
    r = [rel(p) for p in pts]
    frac = sum(inside(p, poly) for p in r) / len(r)
    if frac >= .5:
        ways.append(rdp(r, .35))
print('yard ways kept', len(ways), 'points', sum(len(w) for w in ways), 'length m', round(sum(math.dist(w[i], w[i + 1]) for w in ways for i in range(len(w) - 1))))
blds = []
for t, pts in d['bld']:
    if 'building' not in t or len(pts) < 4:
        continue
    r = [rel(p) for p in pts]
    c = (sum(p[0] for p in r) / len(r), sum(p[1] for p in r) / len(r))
    if inside(c, poly):
        lv = t.get('building:levels')
        blds.append({'n': t.get('name', ''), 'h': (float(lv) * 4 if lv and lv.replace('.', '').isdigit() else 9), 'p': [[round(p[0], 1), round(p[1], 1)] for p in rdp(r[:-1], .5)]})
print('buildings', len(blds), [(b['n'], b['h']) for b in blds if b['n']])
# straight runs for parked trains
runs = []
for wi, w in enumerate(ways):
    i = 0
    while i < len(w) - 1:
        j = i + 1
        h0 = math.atan2(w[j][1] - w[i][1], w[j][0] - w[i][0])
        while j < len(w) - 1:
            h1 = math.atan2(w[j + 1][1] - w[j][1], w[j + 1][0] - w[j][0])
            if abs(math.atan2(math.sin(h1 - h0), math.cos(h1 - h0))) > .012:
                break
            j += 1
        L = math.dist(w[i], w[j])
        if L >= 80:
            runs.append((L, wi, w[i], w[j]))
        i = j
runs.sort(reverse=True)
print('straight runs >=80m:', len(runs), [round(r[0]) for r in runs[:25]])
park = []
for L, wi, a, b in runs:
    hd = math.atan2(b[1] - a[1], b[0] - a[0])
    for f in ([.5] if L < 170 else [.28, .72]):
        m = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        if all(math.dist(m, (p[0], p[1])) > 30 for p in park):
            park.append([round(m[0], 1), round(m[1], 1), round(hd, 4), round(L)])
park = park[:9]
print('parked', park)
cx = sum(p[0] for p in poly) / len(poly)
cz = sum(p[1] for p in poly) / len(poly)
far = max(poly, key=lambda p: math.dist(p, (cx, cz)))
ax = math.atan2(far[1] - cz, far[0] - cx)
ext = [max(abs((p[0] - cx) * math.cos(ax) + (p[1] - cz) * math.sin(ax)) for p in poly), max(abs(-(p[0] - cx) * math.sin(ax) + (p[1] - cz) * math.cos(ax)) for p in poly)]
print('centre', round(cx), round(cz), 'axis', round(ax, 3), 'half extents', [round(e) for e in ext])
out = {'ways': [[round(v, 1) for p in w for v in p] for w in ways], 'bld': blds, 'poly': [[round(p[0], 1), round(p[1], 1)] for p in rdp(poly[:-1], 1.5)],
       'park': park, 'c': [round(cx), round(cz)], 'ax': round(ax, 3), 'ext': [round(e) for e in ext]}
s = json.dumps(out, separators=(',', ':'))
open(S + '/osm/depot_data.json', 'w').write(s)
print('json bytes', len(s))
