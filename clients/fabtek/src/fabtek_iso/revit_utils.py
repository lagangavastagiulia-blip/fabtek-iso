
import sys
import os

# Mocking for IDE/Linter if Revit API is missing
try:
    import clr
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitAPIUI')
    from Autodesk.Revit.DB import *
    from Autodesk.Revit.UI import *
except ImportError:
    # Dummy classes to silence linter
    class ElementId: 
        IntegerValue = 0
        def __init__(self, id): pass
    class BuiltInCategory: 
        OST_PipeCurves = 0
        OST_PipeFitting = 0
        OST_PipeAccessory = 0
        OST_TitleBlocks = 0
    class FilteredElementCollector: 
        def __init__(self, doc): pass
        def OfClass(self, cls): return self
        def OfCategory(self, cat): return self
        def ToElements(self): return []
        def WhereElementIsNotElementType(self): return self
        def WhereElementIsElementType(self): return self
    class ViewFamilyType: 
        ViewFamily = 0
        def __init__(self): self.Id = ElementId(0)
    class ViewFamily: 
        ThreeDimensional = 0
        Drafting = 0
    class View3D: 
        Name = ""
        IsTemplate = False
        Id = ElementId(0)
        Scale = 50
        DetailLevel = 0
        DisplayStyle = 0
        CropBoxActive = False
        CropBoxVisible = False
        def SetOrientation(self, orientation): pass
        def SaveOrientationAndLock(self): pass
        def IsolateElementsTemporary(self, ids): pass
        def ConvertTemporaryHideIsolateToPermanent(self): pass
        @staticmethod
        def Create(*args): return View3D()
        @staticmethod
        def CreateIsometric(doc, type_id): return View3D()
    class ViewDetailLevel: Fine = 0
    class DisplayStyle: Shading = 0; HiddenLine = 0
    class XYZ: 
        def __init__(self, x,y,z): self.X=x; self.Y=y; self.Z=z
        Zero = None
        BasisZ = None
    class ViewOrientation3D: 
        def __init__(self, eye, up, fwd): pass
    class ViewSheet: 
        SheetNumber = ""
        Name = ""
        Id = ElementId(0)
        @staticmethod
        def Create(*args): return ViewSheet()
    class ViewDrafting: 
        Id = ElementId(0)
        Name = ""
        @staticmethod
        def Create(*args): return ViewDrafting()
    class Viewport: 
        @staticmethod
        def Create(*args): pass
    class DWGImportOptions: 
        def __init__(self):
            self.Placement = 0
            self.Unit = 0
    class ImportPlacement: Centered = 0
    class ImportUnit: Millimeter = 0
    class DWGExportOptions: 
        def __init__(self):
            self.MergedViews = False
    class Transaction: 
        def __init__(self, *args): pass
        def Start(self): pass
        def Commit(self): pass
    class TaskDialog: 
        @staticmethod
        def Show(*args): print(args)

    # Mock System types for static analysis
    # We can't easily mock the 'from System... import' inside functions without errors if the module doesn't exist in sys.modules.
    # So we will define a global 'List' shim and usage in the function will be wrapped.

import math
import os

# Helper for generic list
def get_generic_list(element_ids):
    try:
        from System.Collections.Generic import List
        return List[ElementId](element_ids)
    except ImportError:
        # Mock behavior
        return list(element_ids)

def create_3d_view(doc, line_number, elements):
    """
    Creates a 3D view for the pipeline and isolates the elements.
    """
    view_family_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    iso_type = next((t for t in view_family_types if t.ViewFamily == ViewFamily.ThreeDimensional), None)
    
    view_name = "3D_ISO_" + line_number
    # Check if exists
    existing = None
    col = FilteredElementCollector(doc).OfClass(View3D).ToElements()
    for v in col:
        if v.Name == view_name and not v.IsTemplate:
            existing = v
            break
            
    if existing:
        # If exists, we might want to clear it or use it. Let's delete and recreate to be sure of state
        doc.Delete(existing.Id)
        
    view = View3D.CreateIsometric(doc, iso_type.Id)
    view.Name = view_name
    
    # Isolate Elements
    element_ids = [e.Id for e in elements]
    
    # Revit API requires ICollection.
    ids_collection = get_generic_list(element_ids)
    
    view.IsolateElementsTemporary(ids_collection) 
    view.ConvertTemporaryHideIsolateToPermanent()
    
    # Set Style and Detail
    view.DetailLevel = ViewDetailLevel.Fine
    try:
        view.DisplayStyle = DisplayStyle.Shading
    except:
        # Fallback if Shading not supported
        view.DisplayStyle = DisplayStyle.HiddenLine
    
    # Set Isometric Orientation
    # We use "SouthEast" or similar standard ISO.
    # Eye is up, right, front.
    # Eye: (1, -1, 1) direction from Origin
    try:
        eye = XYZ(10.0, -10.0, 10.0)
        up = XYZ(-1.0, 1.0, 2.0) 
        forward = XYZ(-1.0, 1.0, -1.0)
        
        # Or simpler:
        # Standard Isometric: Rot 45 around Z, then 35.26 around X?
        # Let's rely on standard View3D.CreateIsometric if possible?
        # Ah, we used View3D.CreateIsometric above! 
        # But we need to orientations.
        
        # Retrying explicit orientation with slightly zoomed in/out check not needed if we rely on crop box?
        # But we disabled crop box.
        
        # FORCE ORIENTATION:
        eye_pos = XYZ(100, -100, 100)
        forward_dir = XYZ(-1, 1, -1)
        up_dir = XYZ(0, 0, 1)
        
        orientation = ViewOrientation3D(eye_pos, up_dir, forward_dir)
        view.SetOrientation(orientation)
        view.SaveOrientationAndLock()
    except Exception as e:
        pass

    # Set Scale (1:50 is standard for ISO details)
    try:
        view.Scale = 50
    except: pass
    
    view.CropBoxActive = False
    view.CropBoxVisible = False
    
    # ZOOM TO FIT (Workaround: Reset bbox or similar?)
    # In API, "ZoomToFit" is UI method. We can't call it easily on a view created in background.
    # However, setting the orientation usually centers on the origin? No.
    # IsolateElementsTemporary focuses on them?
    # Actually, `IsolateElementsTemporary` isolates them but doesn't auto-zoom.
    # But when placed on sheet, the Viewport should show the extents of visible elements.
    
    return view

def create_sheet(doc, sheet_number, sheet_name, title_block_name="A2"):
    """
    Creates a ViewSheet. Finds TitleBlock by name.
    """
    # Find TitleBlock
    tblocks = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType().ToElements()
    tb_symbol = next((tb for tb in tblocks if title_block_name in tb.FamilyName), None)
    if not tb_symbol:
        if tblocks: tb_symbol = tblocks[0]
        else: return None
        
    # Check/Delete existing
    existing = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
    for s in existing:
        if s.SheetNumber == sheet_number or s.Name == sheet_name:
            doc.Delete(s.Id)
            
    sheet = ViewSheet.Create(doc, tb_symbol.Id)
    sheet.Name = sheet_name
    sheet.SheetNumber = sheet_number
    
    return sheet

def import_dxf_to_drafting_view(doc, dxf_path, view_name):
    """
    Creates a Drafting View and imports the DXF.
    """
    vft = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    drafting_type = next((t for t in vft if t.ViewFamily == ViewFamily.Drafting), None)
    
    # Delete existing
    col = FilteredElementCollector(doc).OfClass(ViewDrafting).ToElements()
    for v in col:
        if v.Name == view_name and not v.IsTemplate:
             doc.Delete(v.Id)
             
    view = ViewDrafting.Create(doc, drafting_type.Id)
    view.Name = view_name
    
    opt = DWGImportOptions()
    opt.Placement = ImportPlacement.Centered
    opt.Unit = ImportUnit.Millimeter 
    
    element_id = clr.Reference[ElementId]()
    doc.Import(dxf_path, opt, view, element_id)
    
    return view

def place_views_on_sheet(doc, sheet, view_3d, drafting_view):
    """
    Places the views on the sheet.
    Returns list of log messages.
    """
    logs = []
    
    # Place Drafting View (ISO) - Left Side
    if drafting_view:
        try:
            # 0.8 ft from left (approx 240mm)
            vp1 = Viewport.Create(doc, sheet.Id, drafting_view.Id, XYZ(0.8, 0.7, 0))
            logs.append("Placed ISO View")
        except Exception as e:
            logs.append("Failed to place ISO View: {}".format(e))
    
    # Place 3D View - Right Side
    if view_3d:
        try:
             # 1.6 ft from left (approx 480mm)
             # Check if view is valid/empty? 
             # Viewport create fails if view is empty? No, usually allows it.
             vp2 = Viewport.Create(doc, sheet.Id, view_3d.Id, XYZ(1.6, 0.7, 0))
             logs.append("Placed 3D View")
        except Exception as e:
             logs.append("Failed to place 3D View: {}".format(e))
    else:
        logs.append("No 3D View provided.")
    
    return logs

def export_view_to_dwg(doc, view, output_folder, filename):
    """
    Exports a specific view to DWG format.
    """
    options = DWGExportOptions()
    options.MergedViews = True
    
    # Ensure export setup
    # We use default settings
    
    # Export
    # Filename should not include .dwg extension for the API call
    name_no_ext = filename.replace(".dwg", "")
    
    import System.Collections.Generic
    views = System.Collections.Generic.List[ElementId]()
    views.Add(view.Id)
    
    try:
        doc.Export(output_folder, name_no_ext, views, options)
        return os.path.join(output_folder, name_no_ext + ".dwg")
    except Exception as e:
        print("Error exporting to DWG: {}".format(e))
        return None
