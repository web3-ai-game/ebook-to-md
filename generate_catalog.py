import os
from pathlib import Path
import urllib.parse
import json
import time

def generate_catalog():
    print("📚 正在生成嚴謹的 Markdown 目錄結構...")
    
    base_dir = Path("./data/markdown-output")
    output_file = base_dir / "CATALOG.md"
    json_output = base_dir / "catalog.json"
    
    if not base_dir.exists():
        print("❌ 輸出目錄不存在")
        return

    # Structure: { 'folder': { 'subfolder': [files...], 'files': [] } }
    tree = {}
    total_files = 0
    
    # 1. Traverse directory
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden files/dirs
        files = [f for f in files if not f.startswith('.') and f.endswith('.md') and f != "CATALOG.md"]
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        if not files:
            continue
            
        rel_path = os.path.relpath(root, base_dir)
        if rel_path == ".":
            rel_path = ""
            
        path_parts = rel_path.split(os.sep) if rel_path else []
        
        # Navigate/Create tree node
        current_node = tree
        for part in path_parts:
            if part not in current_node:
                current_node[part] = {"__files__": [], "__dirs__": {}}
            current_node = current_node[part]["__dirs__"]
            
        # Add files to current node (which is the '__dirs__' of parent, or root dict? 
        # Wait, structure needs to be consistent. 
        # Let's fix structure: Node = { "__files__": [], "subdir_name": Node }
        
        # Reset traversal for correct structure
        pass

    # Simplified recursive build
    def build_tree(dir_path):
        node = {"files": [], "dirs": {}}
        try:
            entries = sorted(os.scandir(dir_path), key=lambda e: e.name)
        except OSError:
            return node
            
        for entry in entries:
            if entry.name.startswith('.') or entry.name == "CATALOG.md" or entry.name == "catalog.json":
                continue
                
            if entry.is_file() and entry.name.endswith('.md'):
                size_kb = entry.stat().st_size / 1024
                node["files"].append({
                    "name": entry.name,
                    "path": os.path.relpath(entry.path, base_dir),
                    "size": f"{size_kb:.1f}KB"
                })
            elif entry.is_dir():
                subtree = build_tree(entry.path)
                if subtree["files"] or subtree["dirs"]: # Only add non-empty dirs
                    node["dirs"][entry.name] = subtree
        return node

    tree = build_tree(base_dir)
    
    # 2. Generate Markdown
    lines = []
    lines.append("# 📚 知識庫全題目錄 (Knowledge Base Catalog)")
    lines.append(f"**生成時間**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("> 註：點擊鏈接可直接查看文檔內容。")
    lines.append("")
    
    def dict_to_md(node, level=0):
        content = []
        indent = "  " * level
        
        # Directories first
        for dirname, subnode in node["dirs"].items():
            heading = "#" * (level + 2)
            if level < 4:
                content.append(f"{heading} 📂 {dirname}")
            else:
                content.append(f"{indent}- **📂 {dirname}**")
            
            content.extend(dict_to_md(subnode, level + 1))
            
        # Files
        for file in node["files"]:
            # URL encode path
            encoded_path = urllib.parse.quote(file['path'])
            link = f"[{file['name']}]({encoded_path})"
            content.append(f"{indent}- 📄 {link} `({file['size']})`")
            
        return content

    lines.extend(dict_to_md(tree))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    # 3. Generate JSON
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 目錄已生成: {output_file}")
    print(f"✅ JSON 數據: {json_output}")

if __name__ == "__main__":
    generate_catalog()
