"""
Analizza la DXF di ez-iso per capire:
1. Quali angoli usa per i segmenti pipe
2. La relazione tra quota reale (mm) e lunghezza disegnata
3. Il bounding box totale del disegno
"""
import ezdxf
import math

EZ_DXF = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\clients\fabtek\references\3-DRDS-SS01-W60001-1.dxf"

doc = ezdxf.readfile(EZ_DXF)
msp = doc.modelspace()

# --- 1. Raccolta testi (quote in mm) ---
texts = []
for t in msp.query('MTEXT TEXT'):
    try:
        val = t.plain_text() if hasattr(t, 'plain_text') else t.dxf.text
        digits = ''.join(c for c in val if c.isdigit() or c == '.')
        if digits:
            fval = float(digits)
            if 10 <= fval <= 100000:
                texts.append({'pos': t.dxf.insert, 'val': fval, 'raw': val})
    except:
        pass

# --- 2. Raccolta linee ---
lines = []
for line in msp.query('LINE'):
    s = line.dxf.start
    e = line.dxf.end
    dx = e.x - s.x
    dy = e.y - s.y
    L = math.hypot(dx, dy)
    if L < 0.5:
        continue
    ang = math.degrees(math.atan2(dy, dx)) % 360
    # Normalizza a 0-180
    ang_norm = ang % 180
    
    # Arrotonda a multipli di 30
    ang_round = round(ang_norm / 30) * 30
    
    mx = (s.x + e.x) / 2
    my = (s.y + e.y) / 2
    
    lines.append({
        'start': (s.x, s.y), 'end': (e.x, e.y),
        'len': L, 'ang': ang_norm, 'ang_r': ang_round,
        'mid': (mx, my)
    })

# --- 3. Distribuzione angoli ---
print("=== DISTRIBUZIONE ANGOLI (ez-iso) ===")
from collections import Counter
ang_counts = Counter(l['ang_r'] for l in lines)
for a, c in sorted(ang_counts.items()):
    print(f"  {a:5.0f}°  ->  {c} segmenti")

# --- 4. Abbina linee a quote ---
print("\n=== QUOTE -> LUNGHEZZA DISEGNATA ===")
pairs = []
for line in lines:
    mx, my = line['mid']
    best = None
    b_d = 9999
    for t in texts:
        d = math.hypot(t['pos'].x - mx, t['pos'].y - my)
        if d < b_d and d < 200:
            b_d = d
            best = t
    if best and line['len'] > 5:
        pairs.append({
            'quote_mm': best['val'],
            'drawn_len': line['len'],
            'ang': line['ang_r'],
            'raw': best['raw']
        })

pairs.sort(key=lambda x: x['quote_mm'])

# Dedup per quota
seen = {}
for p in pairs:
    k = round(p['quote_mm'])
    if k not in seen:
        seen[k] = p

print(f"{'Quote(mm)':>10} | {'Drawn_len':>10} | {'Ratio':>8} | Ang")
print("-" * 50)
for q in sorted(seen.keys()):
    p = seen[q]
    ratio = p['drawn_len'] / q if q > 0 else 0
    print(f"{q:10.0f} | {p['drawn_len']:10.2f} | {ratio:8.4f} | {p['ang']:.0f}°")

# --- 5. Bounding Box ---
print("\n=== BOUNDING BOX TOTALE ===")
all_x = [l['start'][0] for l in lines] + [l['end'][0] for l in lines]
all_y = [l['start'][1] for l in lines] + [l['end'][1] for l in lines]
if all_x:
    W = max(all_x) - min(all_x)
    H = max(all_y) - min(all_y)
    print(f"  W = {W:.2f}")
    print(f"  H = {H:.2f}")

# --- 6. Segmenti a 30/150 (iso) vs 0/90 ---
print("\n=== SEGMENTI ISO vs ORTOGONALI ===")
iso_segs = [l for l in lines if l['ang_r'] in (30, 60, 120, 150)]
ort_segs = [l for l in lines if l['ang_r'] in (0, 90, 180)]
other_segs = [l for l in lines if l not in iso_segs and l not in ort_segs]

print(f"  Ortogonali (0°/90°): {len(ort_segs)}")
print(f"  Isometrici (30°/150°): {len(iso_segs)}")
print(f"  Altri: {len(other_segs)}")

if iso_segs:
    print("\n  Dettaglio segmenti isometrici:")
    for s in sorted(iso_segs, key=lambda x: -x['len'])[:20]:
        print(f"    L={s['len']:7.2f}  ang={s['ang']:5.1f}°  raw_ang={s['ang']:.2f}")

print("\n  Dettaglio segmenti ortogonali (top 15 per lunghezza):")
for s in sorted(ort_segs, key=lambda x: -x['len'])[:15]:
    print(f"    L={s['len']:7.2f}  ang={s['ang']:5.1f}°")
