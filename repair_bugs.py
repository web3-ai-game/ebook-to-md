import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def repair_bugs():
    print("🔧 啟動修復程序 (Repair Protocol)...")
    
    bug_list_file = Path("./bug_list.json")
    
    if not bug_list_file.exists():
        print("❌ 找不到錯誤列表 (bug_list.json)")
        return

    with open(bug_list_file, 'r', encoding='utf-8') as f:
        bad_files = json.load(f)
        
    if not bad_files:
        print("✅ 沒有需要修復的文件")
        return
        
    print(f"🔥 準備刪除 {len(bad_files)} 個損壞的文件，以便管道重新抓取...")
    
    deleted_count = 0
    for item in bad_files:
        file_path = Path(item['path'])
        if file_path.exists():
            try:
                os.remove(file_path)
                deleted_count += 1
                if deleted_count % 10 == 0:
                    print(f"已刪除 {deleted_count} 個...", end='\r')
            except Exception as e:
                print(f"無法刪除 {file_path.name}: {e}")
                
    print(f"\n✨ 修復完成！已刪除 {deleted_count} 個文件。")
    print("🚀 管道程序 (Pipeline) 將自動檢測缺失並重新處理這些文件。")
    
    # Optional: Remove the bug list
    os.remove(bug_list_file)

if __name__ == "__main__":
    repair_bugs()
