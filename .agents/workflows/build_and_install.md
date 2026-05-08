---
description: Build e installa il plugin FABTEK-ISO (pyinstaller + do_install)
---

# Build e Install FABTEK-ISO

// turbo-all

## Steps

1. Build l'exe con PyInstaller
```powershell
pyinstaller --clean iso_builder.spec
```

2. Installa in pyRevit
```powershell
python do_install.py
```

3. In Revit: **pyRevit → Reload → Generate ISO**
