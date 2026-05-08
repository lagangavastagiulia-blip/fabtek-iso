
import clr
import sys
import os
import json
from System.Collections.ObjectModel import ObservableCollection

# WPF References
try:
    clr.AddReference("PresentationCore")
    clr.AddReference("PresentationFramework")
    clr.AddReference("WindowsBase")
    clr.AddReference("System.Windows.Forms")
    
    from System.Windows import Application, Window
    from System.Windows.Markup import XamlReader
    from System.IO import FileStream, FileMode, FileAccess
except:
    pass

class ConfigurationWindow(object):
    def __init__(self, xaml_file, mapping_file, symbols_dir, doc=None, initial_tab=0):
        self.xaml_file = xaml_file
        self.mapping_file = mapping_file
        self.symbols_dir = symbols_dir
        self.doc = doc
        self.initial_tab = initial_tab
        self.window = None
        self.mappings = ObservableCollection[MappingItem]()
        self.available_symbols = []

    def show(self):
        # Load XAML
        try:
            stream = FileStream(self.xaml_file, FileMode.Open, FileAccess.Read)
            self.window = XamlReader.Load(stream)
            stream.Close()
        except Exception as e:
            print("Error loading XAML: {}".format(e))
            return 
        
        # Load Data
        self._load_symbols()
        self._load_mapping()
        
        # Scan for new families if doc is available
        if self.doc:
            self._scan_families()
        
        # Set Initial Tab
        try:
            tab_ctrl = self.window.FindName("MainTabControl")
            if tab_ctrl:
                tab_ctrl.SelectedIndex = self.initial_tab
        except Exception as e:
            print("Error setting tab: {}".format(e))
        
        # Bind Controls
        self.window.DataContext = self
        
        grid = self.window.FindName("MappingGrid")
        grid.ItemsSource = self.mappings
        
        # Bind Events
        self.window.FindName("BtnSave").Click += self.save_click
        self.window.FindName("BtnCancel").Click += self.cancel_click
        self.window.FindName("BtnReloadFamilies").Click += self.reload_click
        self.window.FindName("BtnOpenFolder").Click += self.open_folder_click
        
        btn_browse = self.window.FindName("BtnBrowseTemplate")
        if btn_browse:
            btn_browse.Click += self.browse_template_click

        # Show
        self.window.ShowDialog()

    def _load_symbols(self):
        self.available_symbols = []
        if os.path.exists(self.symbols_dir):
            files = [f for f in os.listdir(self.symbols_dir) if f.lower().endswith(".dxf")]
            self.available_symbols = files
        
    @property
    def AvailableSymbols(self):
        return self.available_symbols

    # Template Properties
    def get_TemplatePath(self):
        return self._template_path
    def set_TemplatePath(self, value):
        self._template_path = value
        
    TemplatePath = property(get_TemplatePath, set_TemplatePath)

    def _load_mapping(self):
        self.mappings.Clear()
        data = {}
        self._template_path = ""
        
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r') as f:
                try:
                    full_json = json.load(f)
                    data = full_json.get("mappings", {})
                    self._template_path = full_json.get("template_path", "")
                except:
                   data = {}
        
        for k, v in data.items():
            self.mappings.Add(MappingItem(k, v))
            
        # Update Text Box manually if binding fails in IronPython sometimes
        txt = self.window.FindName("TxtTemplatePath")
        if txt: txt.Text = self._template_path

    def _scan_families(self):
        """Scans the Revit Doc for Pipe Fittings/Accessories not yet in mapping."""
        if not self.doc: return
        
        import clr
        clr.AddReference('RevitAPI')
        from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId
        
        cats = [
            BuiltInCategory.OST_PipeFitting,
            BuiltInCategory.OST_PipeAccessory,
            BuiltInCategory.OST_PipeCurves # Maybe mapping for Pipe Types too? Usually just Fittings/Accessories.
        ]
        
        found_families = set()
        
        for cat in cats:
            # We want FamilySymbols (Types) or Instances?
            # Let's get instances to see what is actually used, 
            # OR get all FamilySymbols of those categories.
            # Getting instances is safer to only map what's used.
            col = FilteredElementCollector(self.doc).OfCategory(cat).WhereElementIsNotElementType().ToElements()
            for el in col:
                # Get Family Name
                # Some elements might be direct shapes, but usually they have a Symbol
                if hasattr(el, "Symbol") and el.Symbol:
                     fam_name = el.Symbol.FamilyName
                     found_families.add(fam_name)
        
        # Add to mappings if not exists
        existing_names = set([m.FamilyName for m in self.mappings])
        
        for name in found_families:
            if name not in existing_names:
                # Propose defaults
                default_data = self._propose_defaults(name)
                self.mappings.Add(MappingItem(name, default_data))

    def _propose_defaults(self, family_name):
        """Guess SKEY/Block based on name."""
        name_lower = family_name.lower()
        block = ""
        skey = ""
        gasket = False
        bolt = False
        
        if "elbow" in name_lower or "gomito" in name_lower:
            block = "Elbow_90.dxf"
            skey = "EL**"
        elif "tee" in name_lower:
            block = "Tee.dxf"
            skey = "TE**"
        elif "valve" in name_lower or "valvola" in name_lower:
             if "ball" in name_lower or "sfera" in name_lower:
                 block = "Valve_Ball.dxf"
                 skey = "VB**"
             elif "check" in name_lower or "ritegno" in name_lower:
                 block = "Valve_Check.dxf"
                 skey = "VC**"
             else:
                 block = "Valve_Gate.dxf"
                 skey = "VG**"
             # Valves usually need gaskets/bolts
             gasket = True
             bolt = True
        elif "flange" in name_lower or "flangia" in name_lower:
            block = "Flange.dxf"
            skey = "FL**"
            bolt = True
            gasket = True
        elif "cap" in name_lower or "tappo" in name_lower:
            block = "Cap.dxf"
            skey = "CP**"
        elif "reducer" in name_lower or "riduzione" in name_lower:
             block = "Reducer_Conc.dxf"
             skey = "RC**"
        elif "guide" in name_lower or "guida" in name_lower or "support" in name_lower or "supporto" in name_lower:
             block = "Guide.dxf"
             skey = "GU**"  
        elif "accessory" in name_lower or "accessorio" in name_lower:
             block = "Guide.dxf"
             skey = "AC**"

        return {
            "block": block,
            "skey": skey,
            "gasket": gasket,
            "bolt": bolt
        }

    def browse_template_click(self, sender, args):
        from System.Windows.Forms import OpenFileDialog, DialogResult
        dialog = OpenFileDialog()
        dialog.Filter = "DXF Files (*.dxf)|*.dxf|DWG Files (*.dwg)|*.dwg|All Files (*.*)|*.*"
        dialog.Title = "Select ISO Template"
        
        if dialog.ShowDialog() == DialogResult.OK:
            self.TemplatePath = dialog.FileName
            # Update UI
            txt = self.window.FindName("TxtTemplatePath")
            if txt: txt.Text = self.TemplatePath

    def save_click(self, sender, args):
        # Save to JSON
        new_map = {}
        for item in self.mappings:
            entry = {
                "block": item.DxfFileName if item.DxfFileName else "",
                "skey": item.Skey if item.Skey else "",
                "gasket": item.HasGasket,
                "bolt": item.HasBolt
            }
            new_map[item.FamilyName] = entry
        
        full_data = {
            "mappings": new_map, 
            "default_symbol": "default.dxf",
            "template_path": self.TemplatePath
        }
        
        with open(self.mapping_file, 'w') as f:
            json.dump(full_data, f, indent=4)
            
        print("Configuration Saved.")
        self.window.Close()

    def cancel_click(self, sender, args):
        print("Cancelled.")
        self.window.Close()

    def reload_click(self, sender, args):
        self._scan_families()

    def open_folder_click(self, sender, args):
        try:
            from System.Diagnostics import Process
            if os.path.exists(self.symbols_dir):
                Process.Start("explorer.exe", '"{}"'.format(self.symbols_dir))
            else:
                print("Folder not found: {}".format(self.symbols_dir))
        except Exception as e:
            print("Error opening folder: {}".format(e))

class MappingItem(object):
    def __init__(self, family_name, data):
        self.FamilyName = family_name
        # Handle both old string format and new dict format
        if isinstance(data, dict):
            self.DxfFileName = data.get("block", "")
            self.Skey = data.get("skey", "")
            self.HasGasket = data.get("gasket", False)
            self.HasBolt = data.get("bolt", False)
        else:
            self.DxfFileName = str(data)
            self.Skey = ""
            self.HasGasket = False
            self.HasBolt = False
