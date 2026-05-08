import ezdxf
import os

dxf_path = r"c:\Users\giuli\Desktop\FABTEK-ISO\Antigravity-main\clients\fabtek\tests\output_3d.dxf"
if not os.path.exists(dxf_path):
    print("DXF not found")
    exit()

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

print("--- DIMENSIONS ---")
for dim in msp.query('DIMENSION'):
    print(f"Type: {dim.dxftype()}")
    print(f"  DefPoint: {dim.dxf.defpoint}")
    print(f"  DefPoint2: {dim.dxf.defpoint2}")
    print(f"  DefPoint3: {dim.dxf.defpoint3}")
    print(f"  Text: {dim.dxf.text}")

print("--- BOX BOUNDS ---")
# Center: 205, 210. Size: 405.
# X: 2.5 to 407.5
# Y: 7.5 to 412.5
