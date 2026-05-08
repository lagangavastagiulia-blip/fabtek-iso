import ezdxf
import math

f_ez = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\clients\fabtek\references\3-DRDS-SS01-W60001-1.dxf"
f_my = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\clients\fabtek\references\Line_3-DRDS-SS01-W60001_Page_0.dxf"

def analyze(path, name):
    print(f"\n--- Analyzing {name} ---")
    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
    except Exception as e:
        print(f"Error reading DXF: {e}")
        return
    
    texts = []
    for t in msp.query('MTEXT TEXT'):
        val = t.plain_text() if hasattr(t, 'plain_text') else t.dxf.text
        # Clean text
        val = ''.join(c for c in val if c.isdigit())
        if val:
            texts.append({'pos': t.dxf.insert, 'val': float(val)})

    pairs = []
    for line in msp.query('LINE'):
        start = line.dxf.start
        end = line.dxf.end
        length = math.hypot(end.x - start.x, end.y - start.y)
        if length < 1.0: continue
        
        dx = end.x - start.x
        dy = end.y - start.y
        ang = math.degrees(math.atan2(dy, dx)) % 180
        
        mx = (start.x + end.x) / 2
        my = (start.y + end.y) / 2
        
        best = None
        b_d = 999
        for t in texts:
            d = math.hypot(t['pos'].x - mx, t['pos'].y - my)
            if d < b_d and d < 150:
                b_d = d
                best = t['val']

        if best and int(best) > 100:
            pairs.append({'q': best, 'len': length, 'ang': ang, 'mid': (mx, my)})
            
    pairs.sort(key=lambda x: x['q'])
    
    dedup = {}
    for p in pairs:
        if p['q'] not in dedup: dedup[p['q']] = p
        
    for q in sorted(dedup.keys())[:15]:
        print(f"Quote {q:8.0f} mm -> L: {dedup[q]['len']:6.1f} | Ang: {dedup[q]['ang']:5.1f}")
        
    minx=99999; maxx=-99999; miny=99999; maxy=-99999
    lcount = 0
    for line in msp.query('LINE'):
        start = line.dxf.start; end = line.dxf.end
        minx = min(minx, start.x, end.x); maxx = max(maxx, start.x, end.x)
        miny = min(miny, start.y, end.y); maxy = max(maxy, start.y, end.y)
        lcount += 1
    
    if lcount > 0:
        print(f"Bounding Box: W={maxx-minx:.1f}, H={maxy-miny:.1f}")

analyze(f_ez, "EZ-ISO")
analyze(f_my, "FABTEK-ISO")
