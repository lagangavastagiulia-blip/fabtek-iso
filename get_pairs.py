import math, ezdxf

filepath = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\clients\fabtek\references\3-DRDS-SS01-W60001-1.dxf"
try:
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    
    texts_data = []
    for text in msp.query('MTEXT TEXT'):
        val = text.plain_text() if hasattr(text, 'plain_text') else text.dxf.text
        val = ''.join(c for c in val if c.isdigit())
        if val:
            texts_data.append({'pos': text.dxf.insert, 'val': float(val)})
            
    pairs = []
    for line in msp.query('LINE'):
        start = line.dxf.start
        end = line.dxf.end
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2
        
        geom_length = math.hypot(end.x - start.x, end.y - start.y)
        if geom_length < 1.0: continue
            
        best_text = None
        best_dist = 99999
        for t in texts_data:
            dist = math.hypot(t['pos'].x - mid_x, t['pos'].y - mid_y)
            if dist < best_dist and dist < 150:
                best_dist = dist
                best_text = t['val']
                
        if best_text is not None and int(best_text) > 50:
            pairs.append((best_text, geom_length))
            
    print("PAIRS:")
    dedup = {}
    for q, g in pairs:
        if q not in dedup: dedup[q] = g
    for q in sorted(dedup.keys()):
        print(f"{q:.0f} mm -> {dedup[q]:.2f} units")
        
except Exception as e:
    print(e)
