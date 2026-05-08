
import sys
import os
import json
import traceback
from typing import Dict, Tuple, List, Any

# Add src to path if needed (though PyInstaller handles this)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from fabtek_iso.processor import SchematicBuilder
    from fabtek_iso.dxf_writer import IsoDxfWriter
    from fabtek_iso.mapper import SymbolMapper
    from fabtek_iso.boq_generator import BoQGenerator
except ImportError as e:
    print("Error importing modules: {}".format(e))
    # In PyInstaller, we might need specific hidden imports or hook
    sys.exit(1)

def _get_element_origin(data):
    points = data.get("Points", [])
    if not points: return (0,0,0)
    if len(points) == 2:
        p1, p2 = points
        return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
    else:
        return points[0]

def main():
    if len(sys.argv) < 2:
        print("Usage: iso_builder.exe <json_data_path>")
        sys.exit(1)
        
    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print("JSON file not found: {}".format(json_path))
        sys.exit(1)
        
    try:
        with open(json_path, 'r') as f:
            data_bundle = json.load(f)
            
        # Data Bundle Structure:
        # {
        #    "line_number": "L-100",
        #    "iso_page": "1",
        #    "output_path": "C:/...",
        #    "elements": [ ... list of dicts ... ]
        # }
        
        line_num = data_bundle.get("line_number", "UNKNOWN")
        iso_page = data_bundle.get("iso_page", "0")
        out_path = data_bundle.get("output_path", "output.dxf")
        elements_data = data_bundle.get("elements", [])
        
        print("Processing Line: {}, Page: {}".format(line_num, iso_page))
        print("Elements count: {}".format(len(elements_data)))
        
        # 1. Layout
        builder = SchematicBuilder(elements_data)

        # Apply view orientation from Revit if provided
        view_right = data_bundle.get("view_right", None)
        view_up    = data_bundle.get("view_up",    None)
        if view_right and view_up:
            builder.set_view_orientation(view_right, view_up)

        layout: Dict[int, Tuple[float, float]] = builder.layout()
        
        if not layout:
            print("Layout failed or empty.")
            sys.exit(0)
            
        # 2. DXF Generation
        mapper = SymbolMapper()
        
        template_path = data_bundle.get("template_path", "")
        writer = IsoDxfWriter(out_path, template_path=template_path)
        boq = BoQGenerator()
        
        # --- SCALING LOGIC: Fit ISO drawing into the template's drawing area ---
        
        # 1. Calculate Bounding Box of Layout
        min_x: float = float('inf')
        max_x: float = float('-inf')
        min_y: float = float('inf')
        max_y: float = float('-inf')
        
        if not layout:
            print("Layout empty.")
            sys.exit(0)
            
        for pos in layout.values():
            x, y = pos
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            
        # ADD AGGRESSIVE PADDING FOR DIMENSIONS (50mm buffer)
        DIM_PADDING = 50.0 
        min_x -= DIM_PADDING
        max_x += DIM_PADDING
        min_y -= DIM_PADDING
        max_y += DIM_PADDING

        width: float = max_x - min_x
        height: float = max_y - min_y

        # Avoid degenerate layouts (all nodes collinear or on same axis)
        # Use at least 10% of the dominant dimension for the smaller one
        dominant = max(width, height, 1.0)
        if width  < dominant * 0.01: width  = dominant * 0.1
        if height < dominant * 0.01: height = dominant * 0.1

        # 2. Determine drawing area from template extents (auto-detected) or A2 defaults
        # Exact drawing square: 405x405 mm
        # INCREASING MARGIN TO 25% (total 50% buffer) to force a much smaller drawing
        DRAW_AREA_SIZE = 405.0
        MARGIN = 0.25 
        if writer.template_extents:
            xmin, ymin, xmax, ymax = writer.template_extents
            tpl_w = xmax - xmin
            tpl_h = ymax - ymin

            # We center the 405x405 box in the main drawing portion
            # On A2 (594 wide), the title column starts at ~420mm from left.
            # We target the center of the first 420mm of width.
            iso_x0 = xmin + (420.0 - DRAW_AREA_SIZE) / 2.0
            iso_y0 = ymin + (tpl_h - DRAW_AREA_SIZE) / 2.0 + 10.0 # Small vertical offset for title block room

            target_w = DRAW_AREA_SIZE * (1.0 - 2.0 * MARGIN)
            target_h = DRAW_AREA_SIZE * (1.0 - 2.0 * MARGIN)
            center_x = iso_x0 + DRAW_AREA_SIZE / 2.0
            center_y = iso_y0 + DRAW_AREA_SIZE / 2.0

            print("Template detected. Fit into 405x405mm square centered at ({:.1f}, {:.1f})".format(center_x, center_y))
        else:
            # Fallback A2 defaults: force a safer smaller box (300x300) centered in the viewport
            target_w = 300.0
            target_h = 300.0
            center_x = 210.0
            center_y = 210.0

        scale_x = target_w / width
        scale_y = target_h / height
        
        # Uniform scale — preserve ISO angles
        final_scale = min(scale_x, scale_y)
        
        # Layout center (in layout coordinate space)
        lay_cx = (min_x + max_x) / 2.0
        lay_cy = (min_y + max_y) / 2.0
        
        print("Layout Bounds: ({:.2f},{:.2f}) to ({:.2f},{:.2f})".format(min_x, min_y, max_x, max_y))
        print("Fitting to box {:.1f}x{:.1f} with Scale: {:.6f}".format(target_w, target_h, final_scale))
        
        # --- DEBUG LOGGING TO FILE ---
        try:
            temp_dir = os.environ.get("TEMP", "C:/Temp")
            debug_log = os.path.join(temp_dir, "fabtek_iso_debug.txt")
            with open(debug_log, "a") as f:
                import datetime
                f.write("\n--- ISO BUILD [{}] ---\n".format(datetime.datetime.now()))
                f.write("Line: {}, Page: {}\n".format(line_num, iso_page))
                f.write("Layout Bounds: ({:.2f}, {:.2f}) -> ({:.2f}, {:.2f})\n".format(min_x, min_y, max_x, max_y))
                if writer.template_extents:
                    f.write("Template Extents: ({:.1f}, {:.1f}) -> ({:.1f}, {:.1f})\n".format(*writer.template_extents))
                else:
                    f.write("Template Extents: NONE\n")
                f.write("Scale: {:.6f}, Center: ({:.1f}, {:.1f})\n".format(final_scale, center_x, center_y))
                f.write("Output: {}\n".format(out_path))
        except:
            pass

        # Prepare Preview Data
        preview_data: Dict[str, List[Dict[str, Any]]] = {
            "lines": [],
            "text": [],
            "dimensions": []
        }
        
        # Draw connections and items
        lines_drawn = 0
        
        # Pre-process layout into scaled_layout
        scaled_layout: Dict[int, Tuple[float, float]] = {}
        for eid_str, pos in layout.items():
            px = (pos[0] - lay_cx) * final_scale + center_x
            py = (pos[1] - lay_cy) * final_scale + center_y
            scaled_layout[int(eid_str)] = (px, py)
            
        for eid_str, pos_old in layout.items():
            eid = int(eid_str)
            if eid not in scaled_layout: continue
            
            pos = scaled_layout[eid]
            data = builder.elements[eid]
            
            # Place Symbol
            symbol_key = data.get("FamilyName", "")
            skey_data = mapper.get_skey_data(symbol_key)
            dxf_file = mapper.get_symbol_file(symbol_key)
            if not dxf_file:
                if "Valve" in data.get("Category", ""): symbol_key = "Revit_Ball_Valve_Standard"
                dxf_file = mapper.get_symbol_file(symbol_key)
                
            # Calculate Rotation
            rotation = 0.0
            if eid in builder.adj and builder.adj[eid]:
                # Find a neighbor to determine direction
                # Prefer a pipe neighbor
                target_nid = builder.adj[eid][0]
                for nid in builder.adj[eid]:
                     if builder.elements[nid]["Category"] == "Pipes":
                         target_nid = nid
                         break
                
                if target_nid in scaled_layout:
                    npos = scaled_layout[target_nid]
                    dx = npos[0] - pos[0]
                    dy = npos[1] - pos[1]
                    # Calculate angle in degrees
                    import math
                    angle_rad = math.atan2(dy, dx)
                    rotation = math.degrees(angle_rad)
            
            # Fixed symbol scale in mm — independent of fit-to-paper factor
            SYMBOL_SCALE = 2.5

            is_pipe = data["Category"] == "Pipes"

            if not is_pipe:
                 if dxf_file:
                    block_name = os.path.basename(dxf_file).replace(".dxf", "")
                    writer.import_symbol(block_name, dxf_file)
                    writer.place_block(block_name, (pos[0], pos[1], 0), rotation=rotation, scale=SYMBOL_SCALE)
                    # Preview: Add symbol marker (circle/square)
                    preview_data["text"].append({"text": "O", "x": pos[0], "y": pos[1], "h": 5})
                 else:
                    default_dxf = mapper.get_symbol_file("default")
                    if default_dxf:
                        bname = "Generic"
                        writer.import_symbol(bname, default_dxf)
                        writer.place_block(bname, (pos[0], pos[1], 0), rotation=rotation, scale=SYMBOL_SCALE)
                        preview_data["text"].append({"text": "X", "x": pos[0], "y": pos[1], "h": 5})

            # BoQ Logic (omitted for brevity in replacement, assuming it remains mostly same but we focus on visible geometry)
            if is_pipe:
                pts = data.get("Points", [])
                length = 0.0
                if len(pts) == 2:
                    dx = pts[1][0] - pts[0][0]
                    dy = pts[1][1] - pts[0][1]
                    dz = pts[1][2] - pts[0][2]
                    length = (dx*dx+dy*dy+dz*dz)**0.5 / 1000.0  # mm to meters
                boq.add_pipe(data["TypeName"], "N/A", length)
            else:
                 boq.add_item(data["Category"], data.get("FamilyName",""), "N/A")
                 if skey_data.get("gasket"): boq.add_item("GASKET", "Gasket", "N/A")
                 if skey_data.get("bolt"): boq.add_item("BOLT", "Bolt Set", "N/A")

            # Connections
            if eid in builder.adj:
                for nid in builder.adj[eid]:
                    nid_int = int(nid)
                    eid_int = int(eid)
                    if nid_int in scaled_layout and nid_int > eid_int:
                         npos = scaled_layout[nid_int]
                         writer.draw_line((pos[0], pos[1], 0), (npos[0], npos[1], 0))
                         lines_drawn += 1
                         
                         preview_data["lines"].append({"x1": pos[0], "y1": pos[1], "x2": npos[0], "y2": npos[1]})

        # FIXED DIMENSIONING: Pipe End-to-End
        # Iterate over pipes to place dimensions spanning the full segment (Neighbor to Neighbor)
        # FIX: Use builder.elements (dict keyed by element Id) not elements_data (list)
        for eid, pos in scaled_layout.items():
            if eid not in builder.elements:
                continue
            data = builder.elements[eid]

            if data.get("Category") == "Pipes":
                # Get neighbor positions in scaled layout
                neighbors = []
                if eid in builder.adj:
                    for nid in builder.adj[eid]:
                        nid_int = int(nid)
                        if nid_int in scaled_layout:
                            neighbors.append(nid_int)

                # Calculate TRUE real-world length for the dimension text
                # Revit internal units are FEET -> convert to mm
                pts = data.get("Points", [])
                dist_mm = 0.0
                if len(pts) == 2:
                    ddx = pts[1][0] - pts[0][0]
                    ddy = pts[1][1] - pts[0][1]
                    ddz = pts[1][2] - pts[0][2]
                    dist_mm = (ddx*ddx + ddy*ddy + ddz*ddz) ** 0.5

                if dist_mm < 1.0:
                    continue  # Skip zero-length pipes

                # Format as integer mm (e.g. "1524") - override text always wins
                dim_text = "{:.0f}".format(dist_mm)

                # Determine visual endpoints for the dimension line:
                # Case A: 2 neighbours -> span from N1 to N2 (pipe centre is midpoint)
                # Case B: 1 neighbour  -> extrapolate to the open end
                p_start = None
                p_end = None

                if len(neighbors) == 2:
                    n1, n2 = neighbors
                    p_start = scaled_layout[n1]
                    p_end   = scaled_layout[n2]
                elif len(neighbors) == 1:
                    n1      = neighbors[0]
                    p_n1    = scaled_layout[n1]
                    p_center = pos
                    vx = p_center[0] - p_n1[0]
                    vy = p_center[1] - p_n1[1]
                    p_start = p_n1
                    p_end   = (p_center[0] + vx, p_center[1] + vy)
                else:
                    # Isolated pipe: use the pipe's own 3D end-points projected to 2D
                    if len(pts) == 2:
                        import math
                        cos30 = math.cos(math.radians(30))
                        sin30 = math.sin(math.radians(30))
                        def _proj(p):
                            return (p[0] * cos30 - p[1] * cos30,
                                    (p[0] + p[1]) * sin30 + p[2])
                        s2d = _proj(pts[0])
                        e2d = _proj(pts[1])
                        # Fit-to-paper transform
                        p_start = ((s2d[0] - lay_cx) * final_scale + center_x,
                                   (s2d[1] - lay_cy) * final_scale + center_y)
                        p_end   = ((e2d[0] - lay_cx) * final_scale + center_x,
                                   (e2d[1] - lay_cy) * final_scale + center_y)

                if p_start and p_end:
                    # FIX: pass dim_text as forced override so ezdxf does NOT replace it
                    # with the auto-computed 2D distance (which would give 4.33 for 30deg lines)
                    writer.add_dimension(
                        (p_start[0], p_start[1], 0),
                        (p_end[0],   p_end[1],   0),
                        text=dim_text,
                        offset=8
                    )

                    # Preview label at midpoint
                    mx = (p_start[0] + p_end[0]) / 2
                    my = (p_start[1] + p_end[1]) / 2
                    preview_data["text"].append({"text": dim_text, "x": mx, "y": my, "h": 2})

        # Generate BoQ Table — top-right box of A2 template
        # A2 = 594x420 mm. Top-right box starts around X=385, Y=395 (height grows downward).
        boq.generate_table(writer, insert_point=(385, 395, 0))
                                 
        writer.save()
        print("DXF Generated: {}".format(out_path))
        
        # Save Preview JSON
        preview_path = out_path.replace(".dxf", "_preview.json")
        with open(preview_path, 'w') as f:
            json.dump(preview_data, f)
        print("Preview Generated: {}".format(preview_path))
        
        print("DEBUG: Layout Nodes: {}, Lines Drawn: {}".format(len(layout), lines_drawn))
        
    except Exception as e:
        print("CRITICAL ERROR: {}".format(traceback.format_exc()))
        sys.exit(1)

if __name__ == "__main__":
    main()
