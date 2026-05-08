
import sys
import os
import shutil

import ezdxf
import ezdxf.bbox
from ezdxf.addons import Importer

class IsoDxfWriter:
    def __init__(self, output_path, template_path=None):
        self.output_path = output_path
        self.template_extents = None  # (xmin, ymin, xmax, ymax) if template loaded

        if template_path and os.path.exists(template_path):
            try:
                self.doc = ezdxf.readfile(template_path)
            except Exception as e:
                print("Error reading template: {}".format(e))
                self.doc = ezdxf.new("AC1015") # R2000
        else:
            self.doc = ezdxf.new("AC1015")

        self.msp = self.doc.modelspace()
        self.doc.header['$INSUNITS'] = 4 # Millimeters
        self._imported_blocks = set()

        # Auto-detect template coordinate extents using bbox
        try:
            cache = ezdxf.bbox.Cache()
            extents = ezdxf.bbox.extents(self.msp, cache=cache)
            if not extents.is_empty:
                self.template_extents = (extents.extmin.x, extents.extmin.y,
                                         extents.extmax.x, extents.extmax.y)
                print("Template extents detected: ({:.1f},{:.1f}) -> ({:.1f},{:.1f})".format(
                    *self.template_extents))
            else:
                # Fallback to header — but only if the values look real (not ezdxf sentinels ±1e20)
                emin = self.doc.header.get('$EXTMIN', None)
                emax = self.doc.header.get('$EXTMAX', None)
                if (emin and emax and
                        abs(emin[0]) < 1e15 and abs(emin[1]) < 1e15 and
                        abs(emax[0]) < 1e15 and abs(emax[1]) < 1e15 and
                        (emax[0] - emin[0]) > 10):
                    self.template_extents = (emin[0], emin[1], emax[0], emax[1])
                    print("Template extents (from header): ({:.1f},{:.1f}) -> ({:.1f},{:.1f})".format(
                        *self.template_extents))
                # else: leave template_extents=None → use A2 fallback defaults in builder
        except Exception as e:
            print("Template extents detection failed: {}".format(e))
            pass  # Use defaults in builder

        # Define Layers
        # 1 = Red (Pipes)
        # 2 = Yellow (Dimensions/Text)
        # 7 = White/Black (General)
        # Lineweights: 35 = 0.35mm, 50 = 0.50mm, 70 = 0.70mm, -3 = Default
        if 'ISO_PIPE' not in self.doc.layers:
            self.doc.layers.add(name='ISO_PIPE', color=1, lineweight=70) # Thick Line (0.70mm)
        if 'ISO_DIM' not in self.doc.layers:
            self.doc.layers.add(name='ISO_DIM', color=2, lineweight=25) # Thin Line (0.25mm)
        if 'ISO_TEXT' not in self.doc.layers:
             self.doc.layers.add(name='ISO_TEXT', color=2, lineweight=25)

    def import_symbol(self, block_name, dxf_file_path):
        """ Imports a block definition from another DXF file """
        if block_name in self.doc.blocks:
            return True # Already exists
            
        if not os.path.exists(dxf_file_path):
            print("Warning: Symbol file not found: {}".format(dxf_file_path))
            return False

        try:
            source_doc = ezdxf.readfile(dxf_file_path)
            importer = Importer(source_doc, self.doc)
            # Import the block definition (modelspace content of source -> block in dest)
            # Actually ezdxf Importer imports entities. 
            # Simplified approach: Source DXF *is* the symbol. We import its ModelSpace as a Block.
            
            # TODO: Robust Block Import
            # For now, let's assume specific block management or use ezdxf.addons.Importer
            importer.import_blocks([block_name], rename=False)
            return True
        except Exception as e:
            print("Failed to import symbol {}: {}".format(block_name, e))
            return False

    def draw_line(self, start, end, layer="ISO_PIPE"):
        self.msp.add_line(start, end, dxfattribs={'layer': layer})

    def place_block(self, block_name, location, rotation=0, scale=1):
        if block_name not in self.doc.blocks:
            print("Error: Block {} not defined in document.".format(block_name))
            return
        
        self.msp.add_blockref(block_name, location, dxfattribs={
            'rotation': rotation,
            'xscale': scale,
            'yscale': scale,
            'zscale': scale
        })

    def add_text(self, text, location, height=2.5, rotation=0):
        # Use set_placement for alignment
        self.msp.add_text(text, dxfattribs={
            'height': height,
            'rotation': rotation
        }).set_placement(location, align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    def add_dimension(self, start_point, end_point, text="<>", offset=5, layer="ISO_DIM"):
        """
        Adds an ALIGNED dimension suited for Isometric lines.

        IMPORTANT: ezdxf's add_aligned_dim auto-calculates the 2D distance between
        p1 and p2. For isometric 30-degree lines this gives wrong values like 4.33
        (= 5 * cos30) instead of the real 3D pipe length.
        We FORCE the text by:
          1. Calling set_text() before render()
          2. Directly setting dxf.text on the underlying entity
        This prevents ezdxf from overwriting with the measured 2D value.

        TEXT ROTATION FIX:
          dimtih=1 -> text INSIDE dimension lines is always horizontal
          dimtoh=1 -> text OUTSIDE dimension lines is always horizontal
        This overrides the default ezdxf behaviour of rotating text parallel
        to the dimension line (which causes rotated text on isometric 30/150/90deg lines).
        """
        override = {
            'dimtih': 1,   # text inside  -> always horizontal
            'dimtoh': 1,   # text outside -> always horizontal
        }

        dim = self.msp.add_aligned_dim(
            p1=start_point,
            p2=end_point,
            distance=offset,
            dimstyle='ISO-25',
            override=override,
            dxfattribs={'layer': layer}
        )

        # Force the text override BEFORE render so it is burnt into the entity
        if text and text != "<>":
            try:
                # Method 1: ezdxf high-level API
                dim.set_text(text)
            except Exception:
                pass
            try:
                # Method 2: directly write to the DXF attribute (works in all ezdxf versions)
                dim.dxf.text = text
            except Exception:
                pass

        dim.render()

    def save(self):
        try:
            self.doc.saveas(self.output_path)
            return True
        except Exception as e:
            print("Error saving DXF: {}".format(e))
            return False
