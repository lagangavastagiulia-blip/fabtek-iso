
import os
import shutil
import sys
import subprocess
import glob

# Identify target paths
APPDATA = os.getenv('APPDATA')
PYREVIT_EXTENSIONS_DIR = os.path.join(APPDATA, "pyRevit", "Extensions")
TARGET_EXTENSION_NAME = "Fabtek-ISO.extension"
TARGET_EXTENSION_PATH = os.path.join(PYREVIT_EXTENSIONS_DIR, TARGET_EXTENSION_NAME)

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    # Running as compiled exe
    # The 'src' folder should be bundled at root level of the bundle
    SRC_DIR = get_resource_path("src")
else:
    # Running as script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Assuming running from clients/fabtek/installer/
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) # antigravity root
    SRC_DIR = os.path.join(PROJECT_ROOT, "clients", "fabtek", "src")

def install_pyrevit_extension():
    extensions_dir = PYREVIT_EXTENSIONS_DIR
    
    # 1. Check if folder exists, if not check for parent
    if not os.path.exists(extensions_dir):
        parent_dir = os.path.dirname(extensions_dir) # .../Roaming/pyRevit
        if os.path.exists(parent_dir):
            print(f"⚠️ 'Extensions' folder missing in {parent_dir}. Creating it...")
            try:
                os.makedirs(extensions_dir)
            except OSError as e:
                print(f"❌ Failed to create Extensions folder: {e}")
                return False
        else:
            # Check for alternative: pyRevit-Master
            alt_parent = os.path.join(APPDATA, "pyRevit-Master")
            if os.path.exists(alt_parent):
                extensions_dir = os.path.join(alt_parent, "Extensions")
                if not os.path.exists(extensions_dir):
                    try:
                        os.makedirs(extensions_dir)
                    except OSError:
                        pass
            
            # Final check
            if not os.path.exists(extensions_dir):
                print(f"❌ pyRevit not found in standard locations.")
                print(f"   Searched: {PYREVIT_EXTENSIONS_DIR}")
                print(f"   Searched: {os.path.join(APPDATA, 'pyRevit-Master', 'Extensions')}")
                
                user_path = input("👉 Please enter the full path to your pyRevit Extensions folder: ").strip()
                if user_path:
                    extensions_dir = user_path
                    if not os.path.exists(extensions_dir):
                        try:
                            os.makedirs(extensions_dir)
                        except OSError:
                            pass
                else:
                    print("❌ Invalid path or pyRevit not installed.")
                    return False

    target_path = os.path.join(extensions_dir, TARGET_EXTENSION_NAME)
    print(f"🚀 Installing FABTEK Plugin to: {target_path}")

    # 1. Clear existing installation
    if os.path.exists(target_path):
        print("   🧹 Removing old version...")
        shutil.rmtree(target_path)

    # 2. Create Extension Structure
    # Structure: Fabtek-ISO.extension/Fabtek-ISO.tab/
    tab_dir = os.path.join(target_path, "Fabtek-ISO.tab")
    
    # Panels
    run_panel = os.path.join(tab_dir, "Run.panel")
    required_panel = os.path.join(tab_dir, "Required Setting.panel")
    optional_panel = os.path.join(tab_dir, "Optional Setting.panel")
    utils_panel = os.path.join(tab_dir, "Utils.panel")
    
    # Buttons
    # Panel: Run
    btn_generate = os.path.join(run_panel, "Generate ISO.pushbutton")
    
    # Panel: Required Setting
    btn_skey = os.path.join(required_panel, "SKEY Definition.pushbutton")
    btn_drawing_setup = os.path.join(required_panel, "Drawing No. Setup.pushbutton") # Template/Layout
    
    # Panel: Optional Setting
    btn_gen_options = os.path.join(optional_panel, "Generation Options.pushbutton") # BoQ?
    btn_adv_options = os.path.join(optional_panel, "Advanced Options.pushbutton") # Other settings?
    
    # Panel: Utils
    btn_debug = os.path.join(utils_panel, "Debug Info.pushbutton")
    
    lib_dir = os.path.join(target_path, "lib")
    
    # helper to copy icon
    def copy_icon(src_name, dest_folder):
        icon_src = os.path.join(SRC_DIR, "..", "resources", "icons", src_name)
        # If running from source, icons are in clients/fabtek/resources/icons
        # SRC_DIR is clients/fabtek/src
        if not os.path.exists(icon_src):
             # Try installer temp path
             icon_src = os.path.join(get_resource_path("resources"), "icons", src_name)
        
        if os.path.exists(icon_src):
            shutil.copy(icon_src, os.path.join(dest_folder, "icon.png"))
            print("      Key icon: {}".format(src_name))

    for d in [btn_generate, btn_skey, btn_drawing_setup, btn_gen_options, btn_adv_options, btn_debug, lib_dir]:
        os.makedirs(d, exist_ok=True)
        
    copy_icon("generate.png", btn_generate)
    copy_icon("skey_def.png", btn_skey)
    copy_icon("setup.png", btn_drawing_setup)
    copy_icon("options.png", btn_gen_options)
    copy_icon("options.png", btn_adv_options)
    copy_icon("options.png", btn_debug)

    # 3. Copy Libraries
    print("   📦 Installing Core Libraries...")
    
    # Copy fabtek_iso (Core Logic)
    src_lib_core = os.path.join(SRC_DIR, "fabtek_iso")
    dst_lib_core = os.path.join(lib_dir, "fabtek_iso")
    if os.path.exists(dst_lib_core): shutil.rmtree(dst_lib_core)
    shutil.copytree(src_lib_core, dst_lib_core)

    # Copy revit_scripts (as a library for wrappers)
    src_lib_scripts = os.path.join(SRC_DIR, "revit_scripts")
    dst_lib_scripts = os.path.join(lib_dir, "revit_scripts")
    if os.path.exists(dst_lib_scripts): shutil.rmtree(dst_lib_scripts)
    shutil.copytree(src_lib_scripts, dst_lib_scripts)
    
    # Cleanup __pycache__
    for root, dirs, files in os.walk(lib_dir):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
        for f in files:
            if f.endswith(".pyc"):
                os.remove(os.path.join(root, f))
    
    # 3b. Copy Templates
    client_root = os.path.dirname(SRC_DIR)
    src_tpl = os.path.join(client_root, "templates")
    dst_tpl = os.path.join(target_path, "templates")
    if os.path.exists(src_tpl):
         print("   📂 Installing Templates...")
         if os.path.exists(dst_tpl): shutil.rmtree(dst_tpl)
         shutil.copytree(src_tpl, dst_tpl)

    # 3c. Copy Config
    src_cfg = os.path.join(client_root, "config")
    dst_cfg = os.path.join(target_path, "config")
    if os.path.exists(src_cfg):
         print("   ⚙️ Installing Config...")
         if os.path.exists(dst_cfg): shutil.rmtree(dst_cfg)
         shutil.copytree(src_cfg, dst_cfg)

    # 3c. Copy External Binaries (iso_builder.exe)
    print("   🔌 Installing External Engine...")
    bin_dir = os.path.join(target_path, "bin")
    if not os.path.exists(bin_dir): os.makedirs(bin_dir)
    
    # Logic to find bundled EXE
    # PyInstaller add-data "dist/iso_builder.exe;src/bin" puts it in SRC_DIR/bin
    src_exe = os.path.join(SRC_DIR, "bin", "iso_builder.exe")
    dst_exe = os.path.join(bin_dir, "iso_builder.exe")
    
    if os.path.exists(src_exe):
        shutil.copy2(src_exe, dst_exe)
        print("      ✅ Copied iso_builder.exe")
    else:
        print("      ⚠️ Warning: iso_builder.exe not found in source: {}".format(src_exe))

    # 4. Generate Wrapper Scripts
    print("   📜 Generating Button Scripts...")
    
    def write_wrapper(btn_path, module, function, *args):
        script_path = os.path.join(btn_path, "script.py")
        arg_str = ", ".join(map(str, args))
        content = (
            "import sys\n"
            "from {module} import {function}\n"
            "try:\n"
            "    {function}({args})\n"
            "except Exception as e:\n"
            "    import clr\n"
            "    clr.AddReference('RevitAPIUI')\n"
            "    from Autodesk.Revit.UI import TaskDialog\n"
            "    TaskDialog.Show('Error', str(e))\n"
        ).format(module=module, function=function, args=arg_str)
        
        with open(script_path, "w") as f:
            f.write(content)

    # Generate ISO Wrapper
    gen_script = os.path.join(btn_generate, "script.py")
    with open(gen_script, "w") as f:
        f.write(
            "import clr\n"
            "clr.AddReference('RevitAPI')\n"
            "clr.AddReference('RevitAPIUI')\n"
            "from Autodesk.Revit.DB import Transaction\n"
            "from Autodesk.Revit.UI import TaskDialog\n"
            "from revit_scripts.export_iso import main\n"
            "doc = __revit__.ActiveUIDocument.Document\n"
            "t = Transaction(doc, 'Export FABTEK Iso')\n"
            "t.Start()\n"
            "try:\n"
            "    main(doc)\n"
            "    t.Commit()\n"
            "    TaskDialog.Show('Success', 'Export Complete')\n"
            "except Exception as e:\n"
            "    t.RollBack()\n"
            "    TaskDialog.Show('Error', str(e))\n"
        )

    # Config Wrappers (No transaction needed for UI)
    # Config Wrappers (No transaction needed for UI)
    write_wrapper(btn_skey, "revit_scripts.configure", "main", 0)           # SKEY Definition -> Tab 0
    write_wrapper(btn_drawing_setup, "revit_scripts.configure", "main", 1)  # Layout/Template -> Tab 1
    write_wrapper(btn_gen_options, "revit_scripts.configure", "main", 2)    # BoQ/Options -> Tab 2
    write_wrapper(btn_adv_options, "revit_scripts.configure", "main", 1)    # Advanced -> Tab 1 (for now)
    
    # Debug Wrapper
    debug_script = os.path.join(btn_debug, "script.py")
    with open(debug_script, "w") as f:
        f.write(
            "import sys\n"
            "import os\n"
            "import clr\n"
            "clr.AddReference('RevitAPIUI')\n"
            "from Autodesk.Revit.UI import TaskDialog\n"
            "msg = 'Sys Path:\\n' + '\\n'.join(sys.path)\n"
            "msg += '\\n\\nCWD: ' + os.getcwd()\n"
            "TaskDialog.Show('Debug Info', msg)\n"
        )
    
    print("✅ Installation Complete!")
    print("   Please restart Revit or reload pyRevit.")
    return True

if __name__ == "__main__":
    success = install_pyrevit_extension()
    if not success:
        input("Press Enter to exit...")
