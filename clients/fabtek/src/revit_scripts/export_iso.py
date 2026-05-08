"""
FABTEK ISO EXPORTER
Main script to execute within Revit (Dynamo / pyRevit context).
"""
# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for System.Diagnostics.Process
from Autodesk.Revit.DB import Transaction

import sys
import os

# ADD CORE LIBRARY TO PATH
# Assuming this script runs from clients/fabtek/src/revit_scripts/
# We need to add clients/fabtek/src to sys.path (which is usually lib in extensions)
SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.dirname(SCRIPT_DIR)
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# Define main FIRST to ensure it exists even if imports fail later
def main(doc=None):
    # Lazy imports
    try:
        from fabtek_iso.extractor import IsoExtractor
        # Removed imports that depend on ezdxf (SchematicBuilder, IsoDxfWriter, BoQGenerator)
        # as they are now used only in the external iso_builder.exe
    except ImportError as e:
        from Autodesk.Revit.UI import TaskDialog
        TaskDialog.Show("Error", "Failed to import fabtek_iso: {}".format(str(e)))
        return

    if doc is None:
        import __main__
        if hasattr(__main__, '__revit__'):
            doc = __main__.__revit__.ActiveUIDocument.Document
        else:
             try:
                 doc = __revit__.ActiveUIDocument.Document
             except:
                 pass
    
    if not doc:
        from Autodesk.Revit.UI import TaskDialog
        TaskDialog.Show("Error", "Could not determine Active Document")
        return
        
    # Import Enums for TaskDialog
    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult

    extractor = IsoExtractor(doc)

    # Capture view orientation NOW, before any dialogs change the active view.
    # Default: SE direction = correct for SW-top 3D view (NE pipes go 30deg right)
    view_right = [0.707, -0.707, 0.0]
    view_up    = [0.0,   0.0,    1.0]
    try:
        active_view = doc.ActiveView
        r = active_view.RightDirection
        u = active_view.UpDirection
        view_right = [r.X, r.Y, r.Z]
        view_up    = [u.X, u.Y, u.Z]
    except Exception:
        pass  # keep defaults if not a 3D view
    
    # 0. Setup Output Directory
    # docs_folder = os.path.join(os.getenv('USERPROFILE'), 'Documents', 'Fabtek', 'Iso')
    # if not os.path.exists(docs_folder):
    #     os.makedirs(docs_folder)
    
    # 1. Collect elements
    elements = extractor.get_all_piping_elements()
    if not elements:
        TaskDialog = __import__('Autodesk.Revit.UI', fromlist=['TaskDialog']).TaskDialog
        TaskDialog.Show("Warning", "No piping elements found.")
        return

    # 2. Get Unique Parameters from Elements
    # Scan first few elements to get available parameters
    sample_size = min(len(elements), 50)
    param_names = set()
    for i in range(sample_size):
        el = elements[i]
        for p in el.Parameters:
            if p.HasValue:
                # Filter useful parameters (Text or Integer usually)
                param_names.add(p.Definition.Name)
    
    sorted_params = sorted(list(param_names))
    
    # 3. UI for Parameter Selection
    from pyrevit import forms
    import json
    
    # 0. Load Template from Config (Persistent)
    # docs_folder is defined later, but config is in .../config/mapping.json
    # SRC_DIR = .../src
    # client_root = .../fabtek
    client_root = os.path.dirname(SRC_DIR)
    config_file = os.path.join(client_root, "config", "mapping.json")
    
    template_path = ""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                template_path = data.get("template_path", "")
        except:
            pass
            
    # If template is missing, warn or just proceed (iso_builder handles empty template by creating new)
    if template_path and not os.path.exists(template_path):
        # Maybe it was moved/deleted
        pass 
    
    # We do NOT ask the user anymore, as requested.
    # template_path = forms.pick_file(...) # REMOVED
    
    # Select Line Number Parameter
    line_param = forms.SelectFromList.show(
        sorted_params,
        title="Select Line Number Parameter",
        multiselect=False,
        default="Line Number" if "Line Number" in sorted_params else None
    )
    
    if not line_param:
        TaskDialog.Show("Cancelled", "Operation cancelled by user.")
        return

    # Select Page/Sheet Parameter
    page_param = forms.SelectFromList.show(
        sorted_params,
        title="Select Page/Sheet Parameter",
        multiselect=False,
        default="4DCode" if "4DCode" in sorted_params else ("isopage" if "isopage" in sorted_params else None)
    )
    
    if not page_param:
        TaskDialog.Show("Cancelled", "Operation cancelled by user.")
        return
    # Select Output Folder
    docs_folder = forms.pick_folder(
        title="Select Output Folder for ISO Drawings",
        owner=doc.Application
    )
    
    if not docs_folder:
        # Fallback or Cancel?
        # Let's cancel to be explicit
        TaskDialog.Show("Cancelled", "Output folder not selected.")
        return

    # Ask for 3D View (User Request: "dove seleziono il 3d?")
    include_3d = forms.alert("Vuoi includere la vista 3D nel foglio?", options=["Si", "No"])
    if include_3d == "Si":
        create_3d = True
    else:
        create_3d = False

    # 4. Group by Selected Parameters
    by_line = extractor.group_by_line_number(elements, param_name=line_param)
    
    report_msg = "Export Report (Line: {}, Page: {}):\n".format(line_param, page_param)
    
    for line_num, line_elements in by_line.items():
        # 3. Sub-group by Page Code (User Selected)
        by_page = extractor.group_by_page(line_elements, param_name=page_param)
        
        line_folder = os.path.join(docs_folder, line_num)
        if not os.path.exists(line_folder): os.makedirs(line_folder)

        for page_code, page_elements in by_page.items():
            
            # 4. Prepare Data
            data_list = [extractor.get_element_data(el) for el in page_elements]
            
            # 5. External Builders Call
            import json
            import subprocess
            
            # Serialize Data
            import codecs
            # Filename using Page Code (4DCode)
            json_file = os.path.join(line_folder, "iso_data_{}_{}.json".format(line_num, page_code))
            filename = "Line_{}_Page_{}.dxf".format(line_num, page_code)
            out_path = os.path.join(line_folder, filename)
            
            payload = {
                "line_number": line_num,
                "iso_page": page_code,
                "output_path": out_path,
                "template_path": template_path if template_path else "",
                "view_right": view_right,
                "view_up":    view_up,
                "elements": data_list
            }
            
            # Use codecs to ensure UTF-8 encoding for file writing
            # And use json.dumps with ensure_ascii=True to escape non-ascii chars like deg
            with codecs.open(json_file, 'w', encoding='utf-8') as f:
                # payload might contain unicode strings from Revit
                # json.dump in IronPython 2.7 will default to ascii escape for non-ascii chars
                # This is safe.
                json.dump(payload, f, indent=2, ensure_ascii=True)
                
            # Call External EXE
            exe_name = "iso_builder.exe"
            # 1. Look in same folder (Dev/Test)
            exe_path = os.path.join(SCRIPT_DIR, exe_name)
            
            if not os.path.exists(exe_path):
                 # 2. Look in ../bin/ (Installer legacy path?)
                 exe_path = os.path.join(SRC_DIR, "bin", exe_name)

            if not os.path.exists(exe_path):
                 # 3. Look in ../../bin/ (Production Install: extension/bin/iso_builder.exe)
                 # SCRIPT_DIR = extension/lib/revit_scripts
                 # SRC_DIR = extension/lib
                 # ../../bin = extension/bin
                 extension_root = os.path.dirname(SRC_DIR)
                 exe_path = os.path.join(extension_root, "bin", exe_name)
                 
            if not os.path.exists(exe_path):
                 # 4. Look in AppData\Local\Fabtek-ISO (permanent Defender-excluded user folder)
                 fabtek_local = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Fabtek-ISO")
                 exe_path = os.path.join(fabtek_local, exe_name)

            if not os.path.exists(exe_path):
                 report_msg += "EXE not found: {}\n".format(exe_path)
                 continue
                 
            try:
                from System.Diagnostics import Process, ProcessStartInfo
                
                info = ProcessStartInfo(exe_path, '"{}"'.format(json_file))
                info.UseShellExecute = False
                info.CreateNoWindow = True
                info.RedirectStandardOutput = True
                info.RedirectStandardError = True
                
                proc = Process.Start(info)
                output = proc.StandardOutput.ReadToEnd()
                error = proc.StandardError.ReadToEnd()
                proc.WaitForExit()
                
                if proc.ExitCode != 0:
                     report_msg += "Builder Failed (Code {}): {}\n".format(proc.ExitCode, out_path)
                     report_msg += "    STDOUT: {}\n".format(output)
                     report_msg += "    STDERR: {}\n".format(error)
                     continue
                     
                report_msg += "Generated ISO: {}\n".format(out_path)
                report_msg += "    STDOUT: {}\n".format(output)

                # 6. Preview & Confirmation
                preview_json = out_path.replace(".dxf", "_preview.json")
                ui_dir = os.path.join(SRC_DIR, "fabtek_iso", "ui")
                xaml_path = os.path.join(ui_dir, "preview_window.xaml")

                preview_ok = False
                try:
                    if os.path.exists(preview_json) and os.path.exists(xaml_path):
                        from fabtek_iso.ui.preview_ui import PreviewWindow
                        preview_win = PreviewWindow(xaml_path, preview_json)
                        preview_win.ShowDialog()
                        if not preview_win.result:
                            report_msg += "User cancelled at Preview.\n"
                            continue
                        preview_ok = True
                except Exception as ex:
                    report_msg += "Preview window error (fallback to simple dialog): {}\n".format(ex)

                if not preview_ok:
                    # Fallback: open DXF directly + simple TaskDialog
                    try:
                        os.startfile(out_path)
                    except Exception:
                        pass
                    result = TaskDialog.Show(
                        "ISO Generated",
                        "DXF: {}\n\nProceed to create Revit Sheet?".format(filename),
                        TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
                    )
                    if result == TaskDialogResult.No:
                        continue
            
            except Exception as e:
                report_msg += "Error running builder: {}\n".format(e)
                continue
            
            # 7. Revit Sheet Generation
            try:
                from fabtek_iso import revit_utils
                
                # Get Revit elements for this page
                page_ids = {d["Id"] for d in data_list}
                page_elements_revit = [el for el in elements if el.Id.IntegerValue in page_ids]
                
                # Create 3D View?
                view_3d = None
                if create_3d:
                    try:
                        view_3d = revit_utils.create_3d_view(doc, "{}_{}".format(line_num, page_code), page_elements_revit)
                    except Exception as e3d:
                        report_msg += "    Error creating 3D View: {}\n".format(e3d)
                
                # Create Sheet
                sheet_num = "ISO-{}-{}".format(line_num, page_code)
                sheet_name = "Isometric {} - {}".format(line_num, page_code)
                sheet = revit_utils.create_sheet(doc, sheet_num, sheet_name)
                
                if sheet:
                    # Import DXF
                    drafting_view = revit_utils.import_dxf_to_drafting_view(doc, out_path, "Drafting_{}_{}".format(line_num, page_code))
                    
                    # Place Views
                    placement_logs = revit_utils.place_views_on_sheet(doc, sheet, view_3d, drafting_view)
                    for log in placement_logs:
                        report_msg += "    {}\n".format(log)
                    
                    report_msg += "Created Sheet: {}\n".format(sheet_num)
                    
                    # 8. Export Sheet to DWG (User Request)
                    dwg_filename = "ISO-{}-{}.dwg".format(line_num, page_code)
                    revit_utils.export_view_to_dwg(doc, sheet, line_folder, dwg_filename)
                    report_msg += "Exported DWG: {}\n".format(dwg_filename)
                    
                else:
                    report_msg += "Failed to create Sheet (TitleBlock not found?)\n"
                    
            except ImportError:
                 report_msg += "Revit Utils not found. Skipping Sheet generation.\n"
            except Exception as ex:
                 report_msg += "Error creating Sheet: {}\n".format(ex)
    
    from Autodesk.Revit.UI import TaskDialog
    TaskDialog.Show("Detailed Report", report_msg)


if __name__ == "__main__":
    doc = __revit__.ActiveUIDocument.Document
    t = Transaction(doc, "Export FABTEK Iso")
    t.Start()
    try:
        main(doc)
        t.Commit()
        TaskDialog.Show("Success", "Isometric Export Completed.")
    except Exception as e:
        t.RollBack()
        TaskDialog.Show("Error", "Export Failed: {}".format(e))
