import sys, wave
import numpy as np
U = '/root/.claude/uploads/5d779c4b-5220-572b-b253-d4a6a6c8c14d/'
for name in ['741d3675-lrt_open_candidate.wav', '106fc738-lrt_close_candidate.wav', 'd28ee3c0-lrt_announcement_candidate.wav']:
    w = wave.open(U + name)
    sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
    x = np.frombuffer(w.readframes(n), dtype={1: np.uint8, 2: np.int16, 4: np.int32}[sw]).astype(float)
    if sw == 1:
        x -= 128
    x = x.reshape(-1, ch).mean(1)
    x /= (np.abs(x).max() or 1)
    print('==', name.split('-', 1)[1], 'sr', sr, 'dur', round(n / sr, 2))
    N, H = 4096, 512
    win = np.hanning(N)
    fr = np.fft.rfftfreq(N, 1 / sr)
    band = (fr > 300) & (fr < 5000)
    rows = []
    for i in range(0, len(x) - N, H):
        s = np.abs(np.fft.rfft(x[i:i + N] * win))
        sb = s[band]
        k = sb.argmax()
        rows.append((i / sr, fr[band][k], sb[k], sb[k] / (np.median(sb) + 1e-9)))
    rows = np.array(rows)
    thr = max(rows[:, 2].max() * .25, 1e-6)
    seg = []
    for t, f, m, ton in rows:
        if m > thr and ton > 25:
            if seg and t - seg[-1][1] < .06 and abs(f - seg[-1][2]) < 25:
                seg[-1][1] = t; seg[-1][3].append(f); seg[-1][4] = max(seg[-1][4], m)
            else:
                seg.append([t, t, f, [f], m])
    for s in seg:
        if s[1] - s[0] >= .03:
            print('  tone %.2f-%.2f s  len %.2f  freq %.0f Hz  level %.0f' % (s[0], s[1] + N / sr / 2, s[1] - s[0] + .05, np.median(s[3]), s[4]))
    # strongest overall peaks
    S = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f2 = np.fft.rfftfreq(len(x), 1 / sr)
    b2 = (f2 > 300) & (f2 < 6000)
    idx = np.argsort(S[b2])[::-1]
    pk = []
    for k in idx:
        f = f2[b2][k]
        if all(abs(f - p) > 40 for p in pk):
            pk.append(f)
        if len(pk) == 6:
            break
    print('  top peaks Hz:', [round(p) for p in pk])
