import os
import re
from pathlib import Path
import logging
from mongodb_handler import MongoDBHandler
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def restore_mongo_from_disk():
    print("🚑 啟動 MongoDB 數據修復程序 (Restore Protocol)...")
    
    mongo = MongoDBHandler()
    if not mongo.enabled:
        print("❌ MongoDB 未啟用，無法修復。")
        return

    output_dir = Path("./data/markdown-output")
    
    count = 0
    restored = 0
    skipped = 0
    
    print("📊 正在掃描磁盤 Markdown 文件...")
    
    for md_file in output_dir.glob("*.md"):
        count += 1
        try:
            with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 1. Parse Metadata from Header
            # Format: **原始格式**: .txt
            match = re.search(r"\*\*原始格式\*\*: (\.\w+)", content)
            suffix = match.group(1) if match else ""
            
            # 2. Reconstruct Filename
            stem = md_file.stem
            # If suffix exists, append it. If not, assume .txt or leave as is?
            # Main.py logic: md_filename = Path(filename).stem + '.md'
            # So if we have "foo.md" and suffix ".txt", original was "foo.txt"
            
            if suffix:
                original_filename = f"{stem}{suffix}"
            else:
                original_filename = stem # Fallback
                
            # 3. Check if exists
            if mongo.document_exists(original_filename):
                skipped += 1
                if skipped % 100 == 0:
                    print(f"跳過已存在: {skipped}...", end='\r')
                continue
                
            # 4. Restore to Mongo
            metadata = {
                'filename': original_filename,
                'type': suffix,
                'restored': True,
                'restored_at': datetime.utcnow()
            }
            
            # Upsert
            mongo.save_document(original_filename, content, metadata)
            restored += 1
            
            if restored % 10 == 0:
                print(f"已修復 {restored} 條記錄...", end='\r')
                
        except Exception as e:
            print(f"處理失敗 {md_file.name}: {e}")
            
    print(f"\n✨ 修復完成！")
    print(f"掃描文件: {count}")
    print(f"恢復記錄: {restored}")
    print(f"跳過現有: {skipped}")

if __name__ == "__main__":
    restore_mongo_from_disk()
