"""
Standalone Fabtek-ISO installer - runs directly without PyInstaller wrapping.
Avoids all path/encoding issues of the compiled installer.
"""
import os
import sys
import stat
import shutil

def _force_remove(func, path, exc):
    """onerror handler: chmod write then retry deletion."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass  # best-effort

# ---- PATHS ----------------------------------------------------------------
APPDATA   = os.environ["APPDATA"]
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))   # .../Antigravity-main
CLIENT    = os.path.join(REPO_ROOT, "clients", "fabtek")  # .../clients/fabtek
SRC_DIR   = os.path.join(CLIENT, "src")                   # .../clients/fabtek/src
ISO_EXE   = os.path.join(REPO_ROOT, "iso_builder.exe")           # same folder as script
if not os.path.exists(ISO_EXE):
    ISO_EXE = os.path.join(REPO_ROOT, "dist", "iso_builder.exe") # project dist/ folder

EXT_ROOT  = os.path.join(APPDATA, "pyRevit", "Extensions")
EXT_PATH  = os.path.join(EXT_ROOT, "Fabtek-ISO.extension")
TAB       = os.path.join(EXT_PATH, "Fabtek-ISO.tab")
LIB       = os.path.join(EXT_PATH, "lib")
BIN       = os.path.join(EXT_PATH, "bin")

# ---- VALIDATE ---------------------------------------------------------------
if not os.path.exists(EXT_ROOT):
    print("ERROR: pyRevit Extensions folder not found at:", EXT_ROOT)
    sys.exit(1)

if not os.path.exists(SRC_DIR):
    print("ERROR: src folder not found at:", SRC_DIR)
    sys.exit(1)

# ---- CLEAN ------------------------------------------------------------------
print("Cleaning old extension...")
if os.path.exists(EXT_PATH):
    # Python 3.12+ uses onexc; older versions use onerror
    try:
        shutil.rmtree(EXT_PATH, onexc=_force_remove)
    except TypeError:
        shutil.rmtree(EXT_PATH, onerror=_force_remove)

# ---- CREATE STRUCTURE -------------------------------------------------------
print("Creating extension structure...")

buttons = {
    "Run.panel": ["Generate ISO.pushbutton"],
    "Required Setting.panel": [
        "SKEY Definition.pushbutton",
        "Drawing No. Setup.pushbutton",
    ],
    "Optional Setting.panel": [
        "Generation Options.pushbutton",
        "Advanced Options.pushbutton",
    ],
    "Utils.panel": ["Debug Info.pushbutton"],
}

for panel, btns in buttons.items():
    for btn in btns:
        os.makedirs(os.path.join(TAB, panel, btn), exist_ok=True)

os.makedirs(LIB, exist_ok=True)
os.makedirs(BIN, exist_ok=True)

# ---- COPY LIBRARIES ---------------------------------------------------------
print("Copying libraries...")
shutil.copytree(
    os.path.join(SRC_DIR, "fabtek_iso"),
    os.path.join(LIB, "fabtek_iso")
)
shutil.copytree(
    os.path.join(SRC_DIR, "revit_scripts"),
    os.path.join(LIB, "revit_scripts")
)

# ---- COPY TEMPLATES & CONFIG ------------------------------------------------
for name in ["templates", "config"]:
    src = os.path.join(CLIENT, name)
    dst = os.path.join(EXT_PATH, name)
    if os.path.exists(src):
        print("Copying", name, "...")
        shutil.copytree(src, dst)

# ---- COPY ISO_BUILDER.EXE ---------------------------------------------------
print("Copying iso_builder.exe ...")
dst_exe = os.path.join(BIN, "iso_builder.exe")
os.makedirs(BIN, exist_ok=True)

if os.path.exists(ISO_EXE):
    # If the old exe still exists (survived rmtree due to lock), rename it first.
    # Renaming a locked file usually works on Windows even when deletion doesn't.
    if os.path.exists(dst_exe):
        old_exe = dst_exe + ".old"
        if os.path.exists(old_exe):
            try: os.remove(old_exe)
            except: pass
        try:
            os.rename(dst_exe, old_exe)
            print("  Renamed old exe to iso_builder.exe.old")
        except Exception as e:
            print("  WARNING: Could not rename old exe:", e)
    try:
        shutil.copy2(ISO_EXE, dst_exe)
        print("  OK: iso_builder.exe copied")
    except Exception as e:
        print("  ERROR copying exe:", e)
else:
    print("  WARNING: iso_builder.exe not found at:", ISO_EXE)

# ---- WRITE BUTTON SCRIPTS ---------------------------------------------------
print("Writing button scripts...")

# Generate ISO
gen_btn = os.path.join(TAB, "Run.panel", "Generate ISO.pushbutton", "script.py")
with open(gen_btn, "w") as f:
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
        "except Exception as e:\n"
        "    t.RollBack()\n"
        "    TaskDialog.Show('Error', str(e))\n"
    )

# Config wrappers
config_buttons = [
    ("Required Setting.panel", "SKEY Definition.pushbutton", 0),
    ("Required Setting.panel", "Drawing No. Setup.pushbutton", 1),
    ("Optional Setting.panel", "Generation Options.pushbutton", 2),
    ("Optional Setting.panel", "Advanced Options.pushbutton", 1),
]
for panel, btn, tab_idx in config_buttons:
    path = os.path.join(TAB, panel, btn, "script.py")
    with open(path, "w") as f:
        f.write(
            "import sys\n"
            "from revit_scripts.configure import main\n"
            "try:\n"
            "    main({})\n"
            "except Exception as e:\n"
            "    import clr; clr.AddReference('RevitAPIUI')\n"
            "    from Autodesk.Revit.UI import TaskDialog\n"
            "    TaskDialog.Show('Error', str(e))\n".format(tab_idx)
        )

# Debug button
debug_btn = os.path.join(TAB, "Utils.panel", "Debug Info.pushbutton", "script.py")
with open(debug_btn, "w") as f:
    f.write(
        "import sys, os, clr\n"
        "clr.AddReference('RevitAPIUI')\n"
        "from Autodesk.Revit.UI import TaskDialog\n"
        "ext_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))\n"
        "iso_exe  = os.path.join(ext_root, 'bin', 'iso_builder.exe')\n"
        "msg  = 'EXE exists: ' + str(os.path.exists(iso_exe)) + '\\n' + iso_exe\n"
        "msg += '\\n\\nSys Path:\\n' + '\\n'.join(sys.path)\n"
        "TaskDialog.Show('Debug Info', msg)\n"
    )

print("")
print("===========================================")
print("INSTALLATION COMPLETE!")
print("Extension path:", EXT_PATH)
print("")
print("iso_builder.exe present:", os.path.exists(os.path.join(BIN, "iso_builder.exe")))
print("")
print("Now: 1) In Revit, click pyRevit -> Reload")
print("     2) Generate ISO")
print("===========================================")
