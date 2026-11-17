import json, math, os, re, html
S = os.path.dirname(os.path.abspath(__file__))
D = S + '/data'
st = json.load(open(D + '/stations.json'))          # [n, name, lon, lat]
g = json.load(open(D + '/geoline.json'))
segs = g['features'][0]['geometry']['coordinates'] if 'features' in g else g['geometry']['coordinates']
KX = math.cos(math.radians(3.15)) * 111320
KZ = 110574


def xy(p):
    return ((p[0] - st[0][2]) * KX, -(p[1] - st[0][3]) * KZ)


# first direction: chain segments from Gombak until we reach Putra Heights
gom, ph = xy((st[0][2], st[0][3])), xy((st[-1][2], st[-1][3]))
line = []
for s in segs:
    pts = [xy(p) for p in s]
    if line:
        if math.dist(pts[-1], line[-1]) < math.dist(pts[0], line[-1]):
            pts.reverse()
        if math.dist(pts[0], line[-1]) > 400:
            break
    else:
        if math.dist(pts[-1], gom) < math.dist(pts[0], gom):
            pts.reverse()
    for p in pts:
        if not line or math.dist(p, line[-1]) > 1:
            line.append(p)
    if math.dist(line[-1], ph) < 150:
        break
cum = [0]
for i in range(1, len(line)):
    cum.append(cum[-1] + math.dist(line[i], line[i - 1]))
print('points', len(line), 'length km', round(cum[-1] / 1000, 2))


def project(p):
    best = (1e18, 0, 0)
    for i in range(len(line) - 1):
        a, b = line[i], line[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2)) if l2 else 0
        q = (a[0] + dx * t, a[1] + dy * t)
        d = math.dist(p, q)
        if d < best[0]:
            best = (d, cum[i] + t * math.sqrt(l2), i)
    return best


def at(s):
    s = max(0, min(cum[-1], s))
    for i in range(len(line) - 1):
        if cum[i + 1] >= s:
            t = (s - cum[i]) / max(1e-9, cum[i + 1] - cum[i])
            return (line[i][0] + (line[i + 1][0] - line[i][0]) * t, line[i][1] + (line[i + 1][1] - line[i][1]) * t)
    return line[-1]


out = []
prevS = -1
for n, name, lon, lat in st:
    p = xy((lon, lat))
    d, s, i = project(p)
    a, b = at(s - 120), at(s + 120)
    hd = math.atan2(b[1] - a[1], b[0] - a[0])
    out.append({'n': n, 'name': name, 'off': round(d), 's': s, 'h': round(hd, 4), 'ok': s > prevS})
    prevS = s
vias = []
for k in range(len(out) - 1):
    s0, s1 = out[k]['s'], out[k + 1]['s']
    v = []
    for i, p in enumerate(line):
        if s0 + 230 < cum[i] < s1 - 230 and (not v or math.dist(p, v[-1]) > 110):
            v.append(p)
    vias.append([[round(p[0]), round(p[1])] for p in v])
for o, v in zip(out, vias + [[]]):
    print(o['n'], o['name'], 'offset m', o['off'], 'order ok', o['ok'], 'vias', len(v))
json.dump({'h': [o['h'] for o in out], 'vias': vias}, open(D + '/route.json', 'w'))

# rest of the depot report
s = open(D + '/blog.html', encoding='utf-8', errors='ignore').read()
i = s.find('Ampang Line', s.find('Prepared By'))
t = s[i:i + 30000]
t = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
t = re.sub(r'<br\s*/?>|</p>|</div>|</li>', '\n', t)
t = html.unescape(re.sub(r'<[^>]+>', '', t))
t = re.sub(r'[ \t\xa0]+', ' ', t)
t = re.sub(r'\n\s*\n+', '\n', t)
j = t.find('Posted by')
t = t[:j if j > 0 else 9000]
for para in t.split('\n'):
    if re.search(r'depot|Depot|workshop|stabl|wash|maintenance|track', para):
        print('>>', para.strip()[:900])
