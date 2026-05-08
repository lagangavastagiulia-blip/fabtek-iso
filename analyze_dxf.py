import sys
import ezdxf
import math

filepath = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\clients\fabtek\references\1^2-HeUHP-SU83C-K3-0AE-SPOOL1.dxf"

try:
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    
    # Extract line entities and their lengths
    lines = []
    # Look for dimensions explicitly
    pairs = []
    
    # Simple heuristic: find text that is near the middle of a line
    texts_data = []
    for text in msp.query('MTEXT TEXT'):
        # Just grab the number if it is one
        val = text.plain_text() if hasattr(text, 'plain_text') else text.dxf.text
        # Strip brackets or spaces
        val = ''.join(c for c in val if c.isdigit())
        if val:
            texts_data.append({'pos': text.dxf.insert, 'val': float(val)})
            
    # For every line, try to find a text near its midpoint
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
            if dist < best_dist and dist < 100: # must be reasonably close
                best_dist = dist
                best_text = t['val']
                
        if best_text is not None and int(best_text) > 100:
            pairs.append((best_text, geom_length))
            
    pairs.sort(key=lambda x: x[0])
    print("Pairs (Quoted Physical Length vs Geometric CAD Length):")
    for q, g in pairs[:30]:
        print(f"Quote {q:.0f} mm -> Geometric {g:.2f} units")

except Exception as e:
    print(f"Error parsing DXF: {e}")
