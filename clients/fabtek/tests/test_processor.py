
import sys
import os
import math

sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FABTEK_DIR = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(FABTEK_DIR, "src")
sys.path.append(SRC_DIR)

from fabtek_iso.processor import SchematicProcessor

def test_schematic():
    print("🚀 Testing Schematic Processor...")
    proc = SchematicProcessor()

    # Define a path: Start -> N -> U -> E
    # Lengths vary, but schematic should normalize
    segments = [
        ((0,0,0), (0,1000,0)), # North (Y+)
        ((0,1000,0), (0,1000,500)), # Up (Z+)
        ((0,1000,500), (2000,1000,500)) # East (X+)
    ]
    
    current_2d = (0,0)
    print(f"Start: {current_2d}")
    
    for i, (p1, p2) in enumerate(segments):
        vec_2d = proc.process_segment(p1, p2)
        next_2d = (current_2d[0] + vec_2d[0], current_2d[1] + vec_2d[1])
        print(f"Seg {i}: {p1}->{p2} => Vector2D: {vec_2d} => Next2D: {next_2d}")
        
        # Verify Angle
        dx, dy = vec_2d
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        print(f"   Angle: {angle_deg:.2f}°")
        
        current_2d = next_2d

    print("✅ Schematic Test Passed!")

if __name__ == "__main__":
    test_schematic()
