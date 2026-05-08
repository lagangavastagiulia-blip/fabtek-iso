
import json
import os
import sys

class SymbolMapper:
    def __init__(self):
        # Determine paths relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Up 2 levels from src/fabtek_iso -> src -> fabtek
        self.root_dir = os.path.dirname(os.path.dirname(current_dir))
        
        self.config_path = os.path.join(self.root_dir, "config", "mapping.json")
        self.symbols_dir = os.path.join(self.root_dir, "templates", "symbols")
        
        self.mapping = self._load_mapping()

    def _load_mapping(self):
        if not os.path.exists(self.config_path):
            return {"mappings": {}, "default_symbol": "SYMBOL_VALVE_GENERIC.dxf"}
        
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            # Fallback for corrupt config
            return {"mappings": {}, "default_symbol": "SYMBOL_VALVE_GENERIC.dxf"}

    def save_mapping(self):
        """Persists the current mapping state to disk."""
        try:
            # Ensure config dir exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.mapping, f, indent=4)
        except Exception as e:
            # TODO: Log error
            pass

    def get_symbol_file(self, revit_family_name):
        """
        Returns the absolute path to the DXF symbol file.
        If mapped but file missing -> returns None
        If not mapped -> returns None (Trigger UI)
        """
        entry = self.mapping["mappings"].get(revit_family_name)
        
        if not entry:
            return None # Not mapped yet
            
        if isinstance(entry, dict):
            dxf_filename = entry.get("block")
        else:
            dxf_filename = entry
            
        if not dxf_filename:
            return None

        full_path = os.path.join(self.symbols_dir, dxf_filename)
        if os.path.exists(full_path):
            return full_path
        else:
            return None # Mapped but file missing

    def get_skey_data(self, revit_family_name):
        """
        Returns a dict with skey, gasket, bolt info.
        """
        entry = self.mapping["mappings"].get(revit_family_name)
        if isinstance(entry, dict):
            return entry
        return {"skey": "", "gasket": False, "bolt": False}

    def set_mapping(self, revit_family_name, dxf_filename):
        """Updates the mapping and saves."""
        self.mapping["mappings"][revit_family_name] = dxf_filename
        self.save_mapping()

    def get_available_symbols(self):
        """Returns a list of available DXF files in the templates/symbols directory."""
        if not os.path.exists(self.symbols_dir):
            return []
        
        files = [f for f in os.listdir(self.symbols_dir) if f.lower().endswith(".dxf")]
        return files
