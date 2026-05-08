import math, ezdxf

filepath = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\clients\fabtek\references\3-DRDS-SS01-W60001-1.dxf"
try:
    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    angles = {}
    
    for line in msp.query('LINE'):
        start = line.dxf.start
        end = line.dxf.end
        dx = end.x - start.x
        dy = end.y - start.y
        l = math.hypot(dx, dy)
        if l < 1: continue
        
        a = math.degrees(math.atan2(dy, dx))
        if a < 0: a += 360
        a = a % 180
        
        b = round(a)
        angles[b] = angles.get(b, 0) + l
        
    with open(r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\angle_results.txt", "w") as f:
        f.write("TOP ANGLES:\n")
        # sorting by total length
        for k, v in sorted(angles.items(), key=lambda item: item[1], reverse=True)[:5]:
            f.write(f"{k} deg : {v:.1f}\n")
            
except Exception as e:
    with open(r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\Antigravity-main\angle_results.txt", "w") as f:
        f.write(str(e))
