#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from prepare_git_backup import prepare_backup

def run_cmd(cmd, cwd=None):
    try:
        print(f"Exec: {cmd}")
        subprocess.run(cmd, check=True, cwd=cwd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(e)
        return False
    return True

def setup_git(repo_url):
    base_dir = Path("/home/sms/ebook-converter")
    
    print("="*60)
    print("🛠️  Setting up Git Backup")
    print("="*60)

    print("\n1. Preparing files for backup (splitting large files)...")
    try:
        prepare_backup()
    except Exception as e:
        print(f"Warning during backup preparation: {e}")
    
    print("\n2. Initializing Git repository...")
    if not (base_dir / ".git").exists():
        run_cmd("git init", cwd=base_dir)
        run_cmd("git branch -M main", cwd=base_dir)
    else:
        print("Git repo already initialized.")
    
    print(f"\n3. Configuring remote: origin -> {repo_url}")
    # Remove existing origin if any to ensure clean slate
    subprocess.run("git remote remove origin", cwd=base_dir, shell=True, capture_output=True)
    if not run_cmd(f"git remote add origin {repo_url}", cwd=base_dir):
        return
    
    print("\n4. Checking .gitignore...")
    # Double check important ignores
    gitignore_path = base_dir / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        needed = ["__pycache__", "*.pyc", "*.log", "data/baidu-cache/", "data/pipeline-cache/", ".env"]
        with open(gitignore_path, 'a') as f:
            for n in needed:
                if n not in content:
                    f.write(f"\n{n}")
    
    print("\n5. Staging files (git add)...")
    run_cmd("git add .", cwd=base_dir)
    
    print("\n6. Committing changes...")
    # Check if there are changes to commit
    status = subprocess.run("git status --porcelain", cwd=base_dir, shell=True, capture_output=True, text=True)
    if status.stdout.strip():
        run_cmd('git commit -m "Backup: Ebook Converter Pipeline Update"', cwd=base_dir)
    else:
        print("No changes to commit.")
    
    print("\n7. Pushing to remote...")
    if run_cmd("git push -u origin main", cwd=base_dir):
        print("\n✅ Backup completed successfully!")
    else:
        print("\n❌ Push failed.")
        print("Possible reasons:")
        print("1. Authentication failed (Check SSH keys or HTTPS token)")
        print("2. Repository does not exist")
        print("3. Network issues")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 setup_git_backup.py <private_repo_url>")
        print("Example: python3 setup_git_backup.py git@github.com:username/repo.git")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    setup_git(repo_url)
