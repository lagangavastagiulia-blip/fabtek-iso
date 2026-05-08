
import ezdxf
import os

TEMPLATE_DIR = "clients/fabtek/templates/symbols"
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

def create_simple_dxf(name, drawing_func):
    doc = ezdxf.new('R2000')
    
    # Create Block Definition
    # iso_builder expects a block with the same name as the file (minus extension)
    blk = doc.blocks.new(name=name)
    drawing_func(blk)
    
    # Add reference to ModelSpace for direct viewing
    msp = doc.modelspace()
    msp.add_blockref(name, (0, 0))
    
    filename = os.path.join(TEMPLATE_DIR, name + ".dxf")
    doc.saveas(filename)
    print("Created: " + filename)

def draw_elbow(msp):
    # L-Shape
    msp.add_line((0, 0), (5, 0))
    msp.add_line((5, 0), (5, 5))

def draw_tee(msp):
    # T-Shape
    msp.add_line((0, 0), (10, 0))
    msp.add_line((5, 0), (5, 5))

def draw_reducer(msp):
    # Triangle
    msp.add_line((0, 0), (10, 0))
    msp.add_line((10, 0), (5, 5))
    msp.add_line((5, 5), (0, 0))

def draw_cap(msp):
    # C-Shape
    msp.add_line((0, 0), (0, 5))
    msp.add_line((0, 5), (2, 5))
    msp.add_line((0, 0), (2, 0))

def draw_flange(msp):
    # Two vertical lines
    msp.add_line((0, -2), (0, 2))
    msp.add_line((2, -2), (2, 2))

def draw_gate_valve(msp):
    # Bowtie
    msp.add_line((0, 0), (10, 5))
    msp.add_line((0, 5), (10, 0))
    
def draw_check_valve(msp):
    # Arrow-ish
    msp.add_line((0, 0), (10, 5))
    msp.add_line((10, 5), (10, 0))
    msp.add_line((10, 0), (0, 0))

def draw_guide(msp):
    # Guide Symbol: U-shape bracket + Line
    # Center line at (5,0)? 
    # Let's make it a simple bracket around a point
    # Bracket Left
    msp.add_line((3, 2), (3, -2))
    # Bracket Right
    msp.add_line((7, 2), (7, -2))
    # Base
    msp.add_line((0, -2), (10, -2))

if __name__ == "__main__":
    create_simple_dxf("Elbow_90", draw_elbow)
    create_simple_dxf("Tee", draw_tee)
    create_simple_dxf("Reducer_Conc", draw_reducer)
    create_simple_dxf("Cap", draw_cap)
    create_simple_dxf("Flange", draw_flange)
    create_simple_dxf("Valve_Gate", draw_gate_valve)
    create_simple_dxf("Valve_Check", draw_check_valve)
    create_simple_dxf("Guide", draw_guide)
