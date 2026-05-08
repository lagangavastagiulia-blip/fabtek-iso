
import os

def find_pyrevit_path():
    search_roots = [
        os.path.join(os.getenv('APPDATA'), "Autodesk", "Revit", "Addins"),
        os.path.join(os.getenv('PROGRAMDATA'), "Autodesk", "Revit", "Addins")
    ]
    
    found_installs = set()

    print(f"🔍 Searching for pyRevit in Addin Manifests...")
    
    for addins_root in search_roots:
        if not os.path.exists(addins_root): continue
        
        # Walk year folders: 2020, 2021, etc.
        for item in os.listdir(addins_root):
            ver_dir = os.path.join(addins_root, item)
            if os.path.isdir(ver_dir):
                manifest = os.path.join(ver_dir, "pyRevit.addin")
                if os.path.exists(manifest):
                    try:
                        with open(manifest, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if "<Assembly>" in content:
                                start = content.find("<Assembly>") + len("<Assembly>")
                                end = content.find("</Assembly>")
                                assembly_path = content[start:end].strip()
                                # Installation root is usually 2 levels up from bin/
                                install_dir = os.path.dirname(os.path.dirname(assembly_path))
                                found_installs.add(install_dir)
                                print(f"   Manifest Found: {manifest} -> pointing to {install_dir}")
                    except Exception as e:
                        print(f"   Error reading {manifest}: {e}")

    # Also check common portable install Paths
    common_paths = [
        r"C:\pyRevit-Master",
        r"C:\Program Files\pyRevit-Master",
        r"D:\pyRevit-Master",
        os.path.join(os.getenv('APPDATA'), "pyRevit-Master"),
        os.path.join(os.getenv('APPDATA'), "pyRevit")
    ]
    
    for p in common_paths:
        if os.path.exists(os.path.join(p, "Extensions")):
            found_installs.add(p)
            print(f"   Folder Found: {p}")

    print("\n✅ Valid Extension Folders:")
    valid_count = 0
    if found_installs:
        for p in found_installs:
            ext_path = os.path.join(p, "Extensions")
            if os.path.exists(ext_path):
                print(f"👉 {ext_path}")
                valid_count += 1
            else:
                 # Check if we can create it?
                 print(f"   (Base found at {p}, but Extensions folder missing)")
    
    if valid_count == 0:
        print("❌ Could not locate a valid pyRevit Extensions folder automatically.")

if __name__ == "__main__":
    find_pyrevit_path()
