"""
Extractor Module
Handles the selection and filtering of Revit elements based on 'Line Number' and 'isopage'.
"""
import clr
try:
    # Revit API References (for intellisense/mocking)
    clr.AddReference('RevitAPI')
    from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId
except ImportError:
    # Fallback for non-Revit environments (testing)
    pass

class IsoExtractor:
    def __init__(self, doc):
        self.doc = doc

    def get_all_piping_elements(self):
        """
        Collects all Pipe Curves, Pipe Fittings, and Pipe Accessories.
        """
        categories = [
            BuiltInCategory.OST_PipeCurves,
            BuiltInCategory.OST_PipeFitting,
            BuiltInCategory.OST_PipeAccessory
        ]
        
        elements = []
        for cat in categories:
            collector = FilteredElementCollector(self.doc).OfCategory(cat).WhereElementIsNotElementType()
            elements.extend(list(collector))
        
        return elements

    def group_by_line_number(self, elements, param_name="Line Number"):
        """
        Groups elements by 'Line Number' (or selected parameter).
        Returns a dict: { "L-100": [Element, Element...], ... }
        """
        grouped = {}
        for el in elements:
            param = el.LookupParameter(param_name)
            line_number = param.AsString() if param and param.HasValue else "UNASSIGNED"
            
            if line_number not in grouped:
                grouped[line_number] = []
            grouped[line_number].append(el)
        return grouped

    def group_by_page(self, elements, param_name="isopage"):
        """
        Groups elements by 'Page Number' (or selected parameter).
        Returns a dict: { "Code1": [Element...], ... }
        """
        grouped = {}
        for el in elements:
            param = el.LookupParameter(param_name)
            
            if param and param.HasValue:
                try:
                    val = str(param.AsInteger())
                except:
                    val = param.AsString()
            else:
                val = "UNASSIGNED"
            
            if val not in grouped:
                grouped[val] = []
            grouped[val].append(el)
        return grouped

    def get_element_data(self, element):
        """
        Extracts Geometry/Connectivity data for processing.
        Returns a dict:
        {
            "Id": int,
            "Category": str,
            "FamilyName": str,
            "TypeName": str,
            "Points": [(x,y,z), ...], # Start/End for Curve, Origin for Point
            "ConnectedIds": [int, ...], # List of connected Element Ids
             # ... other properties
        }
        """
        data = {
            "Id": element.Id.IntegerValue,
            "Category": element.Category.Name,
            "FamilyName": element.Symbol.FamilyName if hasattr(element, "Symbol") else "",
            "TypeName": element.Name,
            "Points": [],
            "ConnectedIds": []
        }

        # 1. Geometry (simplified)
        loc = element.Location
        if hasattr(loc, "Curve"):
             # Pipe Curve
             curve = loc.Curve
             p1 = curve.GetEndPoint(0)
             p2 = curve.GetEndPoint(1)
             data["Points"] = [(p1.X, p1.Y, p1.Z), (p2.X, p2.Y, p2.Z)]
        elif hasattr(loc, "Point"):
             # Fitting/Accessory Point
             p = loc.Point
             data["Points"] = [(p.X, p.Y, p.Z)]
        
        # 2. Connectivity
        # Scan connectors
        if hasattr(element, "Measures"): # Sometimes helpful check, but checking Connectors is better
             pass
        
        # Access Connector Manager
        cm = None
        if hasattr(element, "ConnectorManager"):
            cm = element.ConnectorManager
        elif hasattr(element, "MePModel") and hasattr(element.MePModel, "ConnectorManager"):
             cm = element.MePModel.ConnectorManager
        
        if cm:
            for connector in cm.Connectors:
                if connector.IsConnected:
                    for ref in connector.AllRefs:
                        # Skip if ref is the element itself or non-physical
                        if ref.Owner.Id != element.Id and ref.ConnectorType.ToString() != "Logical":
                            data["ConnectedIds"].append(ref.Owner.Id.IntegerValue)
                            
        return data
