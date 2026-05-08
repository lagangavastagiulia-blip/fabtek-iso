import sys
import os
import shutil
import json
import argparse
import subprocess
from datetime import datetime

# FORCE UTF-8 OUTPUT (WINDOWS)
sys.stdout.reconfigure(encoding='utf-8')

# CONFIGURATION
# CONFIGURATION
BASE_DIR = os.getcwd()
TEMPLATE_MASTER_PATH = os.path.join(BASE_DIR, ".antigravity", "CLIENT_MASTER_TEMPLATE.md")
SOURCE_PERSONAS_DIR = os.path.join(BASE_DIR, ".antigravity", "personas")
SOURCE_SKILLS_DIR = os.path.join(BASE_DIR, ".antigravity", "skills")
# GIT CHECK
GIT_AVAILABLE = False
try:
    subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    GIT_AVAILABLE = True
except (FileNotFoundError, subprocess.CalledProcessError):
    GIT_AVAILABLE = False
    print("⚠️ Git not found. Skipping Git operations (creating folders only).")

def run_command(command, cwd=BASE_DIR, check=True):
    """Running shell commands helper."""
    try:
        result = subprocess.run(command, shell=True, check=check, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        print(f"✅ {command}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running: {command}\n{e.stderr}")
        if check:
            raise
        return ""

def setup_client(client_name, personas, skills):
    """
    1. Create client directory.
    2. Copy Personas + SKILL_CREATOR (Mandatory).
    3. Copy Skills.
    4. Create Client Master.
    5. Git Branch -> Commit.
    6. CLEANUP: Remove global .antigravity folder.
    7. Push.
    """
    client_slug = client_name.lower().replace(" ", "_").replace("-", "_")
    client_dir = os.path.join(BASE_DIR, "clients", client_slug)
    client_personas_dir = os.path.join(client_dir, ".antigravity/personas")
    client_skills_dir = os.path.join(client_dir, ".antigravity/skills")

    print(f"🚀 Initializing Client Environment: {client_name} ({client_slug})")

    # 1. Create Directories (Client Context)
    if os.path.exists(client_dir):
        print(f"⚠️ Directory {client_dir} already exists. Updating...")
    else:
        os.makedirs(client_personas_dir, exist_ok=True)
        os.makedirs(client_skills_dir, exist_ok=True)

    # 2. Copy Logic
    # ALWAYS include SKILL_CREATOR
    if "SKILL_CREATOR" not in personas:
        personas.append("SKILL_CREATOR")

    # Copy Personas
    for p in personas:
        src = os.path.join(SOURCE_PERSONAS_DIR, f"{p}.md")
        dst = os.path.join(client_personas_dir, f"{p}.md")
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"   👤 Copied Persona: {p}")
        else:
            print(f"   ⚠️ Warning: Persona {p} not found.")

    # Copy Skills (Recursive)
    for s in skills:
        src = os.path.join(SOURCE_SKILLS_DIR, s)
        dst = os.path.join(client_skills_dir, s)
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"   🛠️ Copied Skill: {s}")
        else:
            print(f"   ⚠️ Warning: Skill {s} not found.")

    # 3. Create Client Master
    if os.path.exists(TEMPLATE_MASTER_PATH):
        with open(TEMPLATE_MASTER_PATH, "r") as f:
            template = f.read()
        
        # Hydrate Template
        master_content = template.replace("{{CLIENT_NAME}}", client_name)
        master_content = master_content.replace("{{PERSONA_LIST}}", "\n".join([f"- {p}" for p in personas]))
        master_content = master_content.replace("{{SKILL_LIST}}", "\n".join([f"- {s}" for s in skills]))
        
        with open(os.path.join(client_personas_dir, "MASTER.md"), "w") as f:
            f.write(master_content)
        print("   👑 Client Master Created.")
    else:
        print("   ❌ Error: Client Master Template not found.")

    # 4. Git Operations - Create Branch
    if GIT_AVAILABLE:
        branch_name = f"client/{client_slug}"
        print(f"🌿 Git Operations: {branch_name}")
        
        # Check if branch exists
        branches = run_command("git branch --list", check=False)
        if branch_name in branches:
            run_command(f"git checkout {branch_name}")
        else:
            run_command(f"git checkout -b {branch_name}")

        # 5. CLEANUP PHASE (The "Purge")
        # Now that we are on the new branch, we delete the global .antigravity folder
        # This leaves ONLY the client-specific copy we just created.
        global_antigravity = os.path.join(BASE_DIR, ".antigravity")
        if os.path.exists(global_antigravity):
            print("   🧹 Cleaning up global context (Isolating Client Branch)...")
            shutil.rmtree(global_antigravity)
        
        # 6. Commit and Push
        run_command("git add .")
        run_command(f'git commit -m "Initialize client environment for {client_name} (Clean Branch)"')
        
        try:
            run_command(f"git push -u origin {branch_name}")
            print("   ☁️ Pushed to remote.")
        except Exception as e:
            print("   ⚠️ Push failed (might be upstream issue). Check manual.")
    
        # Return to main
        run_command("git checkout main")
        print("✅ Done. Returned to main.")
    else:
        print(f"✅ Done. Client environment created in clients/{client_slug}. (No Git branch created)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Client Builder")
    parser.add_argument("--name", required=True, help="Name of the client")
    parser.add_argument("--personas", required=True, nargs='+', help="List of personas to include")
    parser.add_argument("--skills", required=True, nargs='+', help="List of skills to include")
    
    args = parser.parse_args()
    setup_client(args.name, args.personas, args.skills)
