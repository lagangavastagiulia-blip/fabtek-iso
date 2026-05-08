import sys
import ezdxf
import math

filepath = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\clients\fabtek\references\3-DRDS-SS01-W60001-1.dxf"

try:
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    
    # Simple heuristic to extract text geometry pair
    texts_data = []
    for text in msp.query('MTEXT TEXT'):
        val = text.plain_text() if hasattr(text, 'plain_text') else text.dxf.text
        val = ''.join(c for c in val if c.isdigit())
        if val:
            texts_data.append({'pos': text.dxf.insert, 'val': float(val)})
            
    print("ANALYZING LINES IN DXF:")
    pairs = []
    angles = []
    for line in msp.query('LINE'):
        start = line.dxf.start
        end = line.dxf.end
        mid_x = (start.x + end.x) / 2
        mid_y = (start.y + end.y) / 2
        
        dx = end.x - start.x
        dy = end.y - start.y
        geom_length = math.hypot(dx, dy)
        if geom_length < 1.0: continue
        
        # Determine angle in degrees
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0: angle_deg += 360
        # Normalize to 0-180
        angle_norm = angle_deg % 180
        angles.append((angle_norm, geom_length))
            
        best_text = None
        best_dist = 99999
        for t in texts_data:
            dist = math.hypot(t['pos'].x - mid_x, t['pos'].y - mid_y)
            # Find the closest text
            if dist < best_dist and dist < 150:
                best_dist = dist
                best_text = t['val']
                
        if best_text is not None and int(best_text) > 100:
            pairs.append((best_text, geom_length, angle_norm))
            
    pairs.sort(key=lambda x: x[0])
    print("Pairs (Quoted Physical Length vs Geometric CAD Length vs Angle):")
    for q, g, a in pairs[:20]:
        print(f"Quote {q:8.0f} mm -> Geometric {g:6.2f} units, Angle: {a:.1f} deg")

    print("\nDOMINANT ANGLES (Sorted by total line length):")
    angle_sums = {}
    for a, l in angles:
        # rounding to nearest 5 degrees for accumulation
        bucket = round(a / 5) * 5
        angle_sums[bucket] = angle_sums.get(bucket, 0) + l
        
    for k in sorted(angle_sums, key=angle_sums.get, reverse=True)[:5]:
        print(f"Angle {k:3.0f} => Total Length: {angle_sums[k]:.1f}")
        
except Exception as e:
    print(f"Error parsing DXF: {e}")
