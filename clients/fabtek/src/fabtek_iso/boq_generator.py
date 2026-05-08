
class BoQGenerator:
    def __init__(self):
        # Pipes: Key=(Description, Size), Value=Total Length (meters)
        self.pipes = {}
        # Items: Key=(Category, Description, Size), Value=Count
        self.items = {}

    def add_pipe(self, description, size, length_meters):
        key = (description, size)
        if key not in self.pipes:
            self.pipes[key] = 0.0
        self.pipes[key] += length_meters

    def add_item(self, category, description, size, quantity=1):
        key = (category, description, size)
        if key not in self.items:
            self.items[key] = 0
        self.items[key] += quantity

    def calculate_welds(self):
        """
        Estimates weld count based on fittings and valves.
        Heuristic: 2 welds per Fitting/Valve (assuming BW/SW).
        """
        weld_count = 0
        for (cat, desc, size), count in self.items.items():
            if cat in ["FITTING", "VALVE", "FLANGE"]:
                # simple logic: 2 welds per item
                # TODO: Refine based on end type (ButtWeld vs Flanged vs Threaded)
                weld_count += (count * 2)
        
        # Add welds to items list
        if weld_count > 0:
            self.add_item("WELD", "Butt Weld (Estimated)", "VAR", weld_count)

    def get_report(self):
        """
        Returns a list of dictionaries ready for table display.
        """
        report = []
        
        # 1. Pipes
        idx = 1
        for key, length in self.pipes.items():
            desc, size = key
            report.append({
                "Pos": str(idx),
                "Category": "PIPE",
                "Description": "PIPE " + desc,
                "Size": size,
                "Qty": "{:.2f} m".format(length)
            })
            idx += 1
            
        # 2. Other Items
        for key, count in self.items.items():
            cat, desc, size = key
            report.append({
                "Pos": str(idx),
                "Category": cat,
                "Description": desc,
                "Size": size,
                "Qty": str(count)
            })
            idx += 1
            
        return report

    def generate_table(self, writer, insert_point=(200, 50, 0)):
        """Draws the BoQ table at the specified location (Top-Left of table)."""
        report = self.get_report()
        if not report: return

        # Config — sized to fit top-right box of A2 template (~195mm wide)
        row_height = 9
        col_widths = [12, 20, 30, 133]  # Pos, Qty, Size, Description  → total 195mm
        headers = ["POS", "QTY", "SIZE", "DESCRIPTION"]
        
        x0, y0, z0 = insert_point
        total_width = sum(col_widths)
        
        # Draw Header
        # writer.draw_line((x0, y0, 0), (x0 + total_width, y0, 0), layer="ISO_TEXT")
        # writer.draw_line((x0, y0 - row_height, 0), (x0 + total_width, y0 - row_height, 0), layer="ISO_TEXT")
        
        current_y = y0
        
        # Headers
        self._draw_row(writer, x0, current_y, col_widths, headers, is_header=True)
        current_y -= row_height
        
        # Rows
        for item in report:
            row_data = [item["Pos"], item["Qty"], item["Size"], item["Description"]]
            self._draw_row(writer, x0, current_y, col_widths, row_data)
            current_y -= row_height
            
        # Closing Line
        writer.draw_line((x0, current_y, 0), (x0 + total_width, current_y, 0), layer="ISO_TEXT")
        
    def _draw_row(self, writer, x, y, widths, data, is_header=False):
        row_height = 8
        current_x = x
        
        # Top Line
        writer.draw_line((x, y, 0), (x + sum(widths), y, 0), layer="ISO_TEXT")
        
        for i, text in enumerate(data):
            w = widths[i]
            # Vertical Line (Left)
            writer.draw_line((current_x, y, 0), (current_x, y - row_height, 0), layer="ISO_TEXT")
            
            # Text
            text_x = current_x + w / 2
            text_y = y - row_height / 2
            writer.add_text(str(text), (text_x, text_y, 0), height=2.5, rotation=0)
            
            current_x += w
            
        # Final Vertical Line (Right)
        writer.draw_line((current_x, y, 0), (current_x, y - row_height, 0), layer="ISO_TEXT")
