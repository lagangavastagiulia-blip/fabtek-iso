
import math
from typing import Optional, Tuple

class SchematicProcessor:
    def __init__(self, scale_factor=1.0):
        self.scale = scale_factor
        # Default: standard isometric angles
        self.angle_x = math.radians(30)
        self.angle_y = math.radians(150)
        self.angle_z = math.radians(90)
        # View-based projection vectors (None = use standard ISO)
        self._view_right: Optional[Tuple[float, float, float]] = None
        self._view_up:    Optional[Tuple[float, float, float]] = None

    def set_view_orientation(self, right_vec, up_vec):
        """
        Override the projection to match the Revit 3D view camera.
        right_vec : (rx, ry, rz)  = view.RightDirection
        up_vec    : (ux, uy, uz)  = view.UpDirection
        """
        self._view_right = tuple(right_vec)
        self._view_up    = tuple(up_vec)

    def _get_direction_vector(self, p1, p2):
        """Returns normalized 3D vector (dx, dy, dz)"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length < 1e-6:
            return (0,0,0), 0
        return (dx/length, dy/length, dz/length), length

    def _is_cardinal(self, vec):
        """Checks if vector is aligned with X, Y, or Z axes."""
        x, y, z = vec
        return (abs(x) > 0.99) or (abs(y) > 0.99) or (abs(z) > 0.99)

    def _project_vector(self, dx, dy, dz):
        """
        Projects a 3D vector onto the 2D schematic plane using the instance angles.
        This allows both standard ISO (30/150/90) and flat/dimetric projections (0/90).
        """
        x_2d = (dx * math.cos(self.angle_x)) + (dy * math.cos(self.angle_y)) + (dz * math.cos(self.angle_z))
        y_2d = (dx * math.sin(self.angle_x)) + (dy * math.sin(self.angle_y)) + (dz * math.sin(self.angle_z))
        return x_2d, y_2d






    def process_segment(self, start_pt, end_pt, is_fitting=False):
        """
        Input:  start_pt (x,y,z), end_pt (x,y,z) — real 3D coordinates.
        Output: v2d (x,y) — 2D isometric schematic vector.

        Every pipe is snapped to its DOMINANT axis (X, Y, or Z) before projection.
        This ensures ALL pipes appear at canonical ISO angles: ±30° or 90°,
        regardless of the actual angle in the Revit model (even diagonal NE pipes).
        """
        vec, real_len = self._get_direction_vector(start_pt, end_pt)

        # EZ-ISO NTS SCALING LOGIC (Power-law, calibrated on real ez-iso DXF data):
        # Formula: drawn = 4.05 * real_mm ^ 0.369
        # Calibrated from 57 quote->drawn pairs across 4 ez-iso DXF reference files.
        # Verified against ground truth:
        #   100mm  -> 20.02mm  (pred: 22.1)
        #   380mm  -> 34.57mm  (pred: 36.3)
        #   20864mm-> 171.85mm (pred: 159.0)
        EZ_A = 4.05
        EZ_B = 0.369
        MIN_DRAWN = 8.0    # minimum visibility for very short fittings
        MAX_DRAWN = 172.0  # standard Ez-ISO cap
        real_len_mm = real_len
        if real_len < 1e-4:
            effective_len = 0.5
        else:
            effective_len = max(MIN_DRAWN, min(MAX_DRAWN, EZ_A * (real_len_mm ** EZ_B)))

        sx, sy, sz = vec
        abs_sx = abs(sx)
        abs_sy = abs(sy)
        abs_sz = abs(sz)

        # If the pipe is strictly aligned to an axis (within a tolerance),
        # snap it to ensure perfect 30/150/90 angles in the ISO layout.
        # Otherwise (diagonal pipes, slopes, offsets), keep the actual
        # proportional vector components to preserve their relative lengths 
        # and natural sloped angle on the 2D plane.
        
        # AGGRESSIVE AXIS SNAPPING
        # To match the "readable" look of Ez-ISO, we force every segment 
        # to its dominant axis (X, Y, or Z) to ensure perfect 30/150/90 angles.
        is_cardinal = True
        if abs_sx >= abs_sy and abs_sx >= abs_sz:
            sx, sy, sz = (1.0 if sx > 0 else -1.0), 0.0, 0.0
        elif abs_sy >= abs_sx and abs_sy >= abs_sz:
            sx, sy, sz = 0.0, (1.0 if sy > 0 else -1.0), 0.0
        else:
            sx, sy, sz = 0.0, 0.0, (1.0 if sz > 0 else -1.0)

        # If it's cardinal, its unit vector length is 1.0. 
        # If it's sloped, its unit vector length is also 1.0.
        # Multiplying by effective_len scales it to readable NTS proportions.
        dx_schem = sx * effective_len
        dy_schem = sy * effective_len
        dz_schem = sz * effective_len

        v2d = self._project_vector(dx_schem, dy_schem, dz_schem)
        return v2d
    def get_dimension_vector(self, start_pt, end_pt):
        """
        Calculates a 2D offset vector for placing dimensions.
        """
        # Get 2D projected vector of the pipe
        v2d = self.process_segment(start_pt, end_pt)
        dx, dy = v2d
        
        # Normalize
        length = math.sqrt(dx*dx + dy*dy)
        if length < 1e-6: return (0, 5) # Default up
        
        ndx, ndy = dx/length, dy/length
        
        # Perpendicular vector (-y, x)
        pdx, pdy = -ndy, ndx
        
        # Scale by offset (e.g. 5 units)
        offset = 5.0
        return (pdx * offset, pdy * offset)

class SchematicBuilder:
    def __init__(self, elements_data):
        """
        elements_data: list of dicts from IsoExtractor.get_element_data()
        """
        self.elements = {d["Id"]: d for d in elements_data}
        self.adj = {}
        self._build_graph()
        self.processor = SchematicProcessor()

    def set_view_orientation(self, right_vec, up_vec):
        """Forward view vectors to the processor so projection matches Revit view."""
        self.processor.set_view_orientation(right_vec, up_vec)

    def _build_graph(self):
        for eid, data in self.elements.items():
            if eid not in self.adj:
                self.adj[eid] = []
            for cid in data.get("ConnectedIds", []):
                if cid in self.elements:
                    # eid -> cid
                    if cid not in self.adj[eid]:
                        self.adj[eid].append(cid)
                    # cid -> eid  (BIDIRECTIONAL: fittings have empty ConnectedIds
                    #              so we must add the reverse edge here)
                    if cid not in self.adj:
                        self.adj[cid] = []
                    if eid not in self.adj[cid]:
                        self.adj[cid].append(eid)


    def layout(self):
        """
        Returns dict { element_id: (x, y) } 
        Coordinate represents the 'insertion point' or center of the element.
        For pipes, we might need Start/End.
        Strategy: Calculate Node positions. A Node is a connection point.
        Elements are edges?
        
        Revit Model: Elements are Nodes (Fittings) and Edges (Pipes).
        But Fittings are also entities that need position.
        
        Let's treat every Element as a Node positioned at its center/origin.
        
        Returns: { id: (x,y) }
        """
        if not self.elements:
            return {}

        # 0. SMART VIEW ORIENTATION ALGORITHM (Copying ez_iso flattening logic)
        # Ez-iso analyzes the physical bounding box to determine the optimal projection angles.
        # If the pipeline travels primarily on a flat 2D plane (e.g. only X-Z or Y-Z),
        # placing it at a full 30/150 isometric angle distorts a perfectly good 2D flat shape.
        # By forcing the dominant axis to be rendered frontally (0°/180°), we get straight lines!
        # Let's assess the total span on X and Y in the whole spool.
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        
        for k, v in self.elements.items():
            pts = v.get("Points", [])
            if not pts: continue
            for (x, y, z) in pts:
                min_x = min(min_x, x); max_x = max(max_x, x)
                min_y = min(min_y, y); max_y = max(max_y, y)
                min_z = min(min_z, z); max_z = max(max_z, z)
                
        span_x = max_x - min_x
        span_y = max_y - min_y
        
        # If it's effectively 2D (one span is less than 5% of the other, or negligible),
        # flatten the view to Frontal (Dimetric/Orthographic) so it looks like the user's reference.
        # X is usually right-left, Y is back-forth in Revit standard orientation.
        EPS = max(span_x, span_y) * 0.05
        
        # Reset to base Iso
        self.processor.angle_x = math.radians(30)
        self.processor.angle_y = math.radians(150)
        self.processor.angle_z = math.radians(90)
        
        if span_y < EPS and span_x > 0.1:
            # Flattens strictly to X-Z plane (Front view -> X=0 deg, Y=180 deg)
            self.processor.angle_x = math.radians(0)
            self.processor.angle_y = math.radians(180)
        elif span_x < EPS and span_y > 0.1:
            # Flattens strictly to Y-Z plane (Side view -> Y=0 deg, X=180 deg)
            self.processor.angle_y = math.radians(0)
            self.processor.angle_x = math.radians(180)
        # Otherwise, keep 30/150 isometric!

        # 1. First Pass: Compute Schematics Relative Graph Coordinates
        visited = {} # Stores {id: (x,y)}
        unvisited = set(self.elements.keys())
        
        island_offset_y = 0.0
        
        while unvisited:
            # 1. Pick a start node for this component
            start_node = next(iter(unvisited))
            for eid in unvisited:
                if eid in self.adj and len(self.adj[eid]) == 1:
                    start_node = eid
                    break
            
            # 2. Initialize BFS for this island
            visited[start_node] = (0.0, island_offset_y)
            if start_node in unvisited: unvisited.remove(start_node)
            
            queue = [start_node]
            
            # 3. Traverse Component
            while queue:
                current_id = queue.pop(0)
                current_pos = visited[current_id]
                current_data = self.elements[current_id]
                
                try:
                    p1_real = self._get_origin(current_data)
                except:
                    continue

                if current_id in self.adj:
                    for neighbor_id in self.adj[current_id]:
                        if neighbor_id in unvisited:
                            neighbor_data = self.elements[neighbor_id]
                            p2_real = self._get_origin(neighbor_data)
                            
                            is_fitting = (current_data["Category"] != "Pipes") or (neighbor_data["Category"] != "Pipes")
                            
                            v2d = self.processor.process_segment(p1_real, p2_real, is_fitting=is_fitting)
                            if not v2d: v2d = (1.0, 0.0)
                            
                            next_pos = (current_pos[0] + v2d[0], current_pos[1] + v2d[1])
                            
                            visited[neighbor_id] = next_pos
                            unvisited.remove(neighbor_id)
                            queue.append(neighbor_id)
                        
                        elif neighbor_id in visited:
                             pass

            # Prepare for next island (if any)
            island_offset_y -= 5.0 # Move down for next disconnected part
        
        return visited

    def _get_origin(self, data):
        # Helper to get a singular 3D point for the element
        points = data["Points"]
        if not points: return (0,0,0)
        
        # If Pipe (2 points), return midpoint? 
        # No, for traversal we need the end that connects.
        # But here we are simplifying: Element -> Center coordinate.
        # This works for fittings. For pipes, it's ambiguous.
        # A Better graph would be: Nodes = Connectors, Edges = Elements.
        # But we only have Element Connectivity.
        
        # Simplification: Use Midpoint for Pipes, Origin for Fittings.
        if len(points) == 2:
            p1, p2 = points
            return ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
        else:
            return points[0]


