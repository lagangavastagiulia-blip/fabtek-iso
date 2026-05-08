
import sys
import os
import clr

# ADD CORE LIBRARY TO PATH
SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.dirname(SCRIPT_DIR)
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

try:
    from fabtek_iso.ui.config_ui import ConfigurationWindow
except ImportError as e:
    # Fallback or error
    print("Error importing UI: {}".format(e))
    # In Revit we might use TaskDialog
    raise

def main(tab_index=0):
    # Paths
    ui_dir = os.path.join(SRC_DIR, "fabtek_iso", "ui")
    xaml_path = os.path.join(ui_dir, "configuration_window.xaml")
    
    # Config Paths
    # Assuming config is in clients/fabtek/config/mapping.json
    # SRC_DIR is clients/fabtek/src
    client_root = os.path.dirname(SRC_DIR)
    config_file = os.path.join(client_root, "config", "mapping.json")
    
    # Symbols Path
    symbols_dir = os.path.join(client_root, "templates", "symbols")
    
    if not os.path.exists(config_file):
        # Create empty if not exists
        folder = os.path.dirname(config_file)
        if not os.path.exists(folder): os.makedirs(folder)
        with open(config_file, 'w') as f:
            f.write('{"mappings": {}, "default_symbol": "default.dxf"}')

    if not os.path.exists(symbols_dir):
        if not os.path.exists(symbols_dir): os.makedirs(symbols_dir)

    # Launch UI with specific tab
    doc = None
    try:
        doc = __revit__.ActiveUIDocument.Document
    except:
        pass
        
    win = ConfigurationWindow(xaml_path, config_file, symbols_dir, doc=doc, initial_tab=tab_index)
    win.show()

if __name__ == "__main__":
    # check for args if needed, or default
    main()
