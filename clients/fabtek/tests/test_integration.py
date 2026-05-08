import sys
import os

# Add src to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# SCRIPT_DIR is .../clients/fabtek/tests
# Parent is .../clients/fabtek
FABTEK_DIR = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(FABTEK_DIR, "src")
sys.path.append(SRC_DIR)

from fabtek_iso.mapper import SymbolMapper
from fabtek_iso.boq_generator import BoQGenerator
from fabtek_iso.dxf_writer import IsoDxfWriter
from fabtek_iso.processor import SchematicBuilder

def test_integration():
    print("🚀 Starting Integration Test...")
    
    # 1. Mock Data (Simulating Extractor Output)
    # A simple line: Start --(Pipe1)--> Valve --(Pipe2)--> Elbow --(Pipe3)--> End
    # Coordinates in millimeters
    
    # IDs
    id_start_pipe = 100
    id_valve = 200
    id_mid_pipe = 300
    id_elbow = 400
    id_end_pipe = 500
    
    data_list = [
        {
            "Id": id_start_pipe, "Category": "Pipes", "FamilyName": "", "TypeName": "Pipe 6inch",
            "Points": [(0,0,0), (1000,0,0)],
            "ConnectedIds": [id_valve] 
        },
        {
            "Id": id_valve, "Category": "Pipe Accessories", "FamilyName": "Revit_Ball_Valve_Standard", "TypeName": "Ball Valve",
            "Points": [(1000,0,0)],
            "ConnectedIds": [id_start_pipe, id_mid_pipe]
        },
        {
            "Id": id_mid_pipe, "Category": "Pipes", "FamilyName": "", "TypeName": "Pipe 6inch",
            "Points": [(1000,0,0), (2000,0,0)],
            "ConnectedIds": [id_valve, id_elbow]
        },
        {
            "Id": id_elbow, "Category": "Pipe Fittings", "FamilyName": "Elbow Generic", "TypeName": "Elbow 90",
            "Points": [(2000,0,0)], # In reality fittings have origin
            "ConnectedIds": [id_mid_pipe, id_end_pipe]
        },
        {
            "Id": id_end_pipe, "Category": "Pipes", "FamilyName": "", "TypeName": "Pipe 6inch",
            "Points": [(2000,0,0), (2000,1000,0)], # Going North (Y+)
            "ConnectedIds": [id_elbow]
        }
    ]
    
    print(f"   Created {len(data_list)} mock elements.")

    # 2. Schematic Processing
    print("   Running Schematic Builder...")
    builder = SchematicBuilder(data_list)
    layout = builder.layout()
    print(f"   Layout generated for {len(layout)} nodes.")
    
    # 3. DXF Generation
    output_path = os.path.join(SCRIPT_DIR, "test_output_schematic.dxf")
    writer = IsoDxfWriter(output_path)
    mapper = SymbolMapper()
    
    print("   Generating DXF...")
    for eid, pos in layout.items():
        data = builder.elements[eid]
        
        # Place Symbols (skip pipes)
        if data["Category"] != "Pipes":
             symbol_key = data.get("FamilyName", "")
             dxf_file = mapper.get_symbol_file(symbol_key)
             
             if not dxf_file:
                 dxf_file = mapper.get_symbol_file("default")
                 block_name = "Generic"
             else:
                 block_name = os.path.basename(dxf_file).replace(".dxf", "")
                 
             if dxf_file:
                 writer.import_symbol(block_name, dxf_file)
                 writer.place_block(block_name, (pos[0], pos[1], 0))
        
        # Draw Connections
        if eid in builder.adj:
             for nid in builder.adj[eid]:
                 if nid in layout and nid > eid:
                     npos = layout[nid]
                     writer.draw_line((pos[0], pos[1], 0), (npos[0], npos[1], 0))

    writer.save()
    assert os.path.exists(output_path)
    print("✅ Integration Test Passed! DXF created at:", output_path)

if __name__ == "__main__":
    test_integration()
