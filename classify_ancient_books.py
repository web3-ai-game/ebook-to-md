import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def classify_ancient_books():
    print("🔍 啟動古籍/縣志分類程序...")
    
    base_dir = Path(".")
    categories_file = base_dir / "data/baidu-analysis/file_categories.json"
    output_file = base_dir / "data/ancient_books_list.json"
    
    if not categories_file.exists():
        print("❌ 找不到源文件列表")
        return

    with open(categories_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Combine all potential ebook files
    all_files = []
    for cat in ['pdf_text', 'pdf_scan', 'epub_mobi', 'doc_files', 'other_ebooks']:
        all_files.extend(data.get(cat, []))
        
    keywords = ["县志", "縣志", "古籍", "善本", "方志", "通志", "府志", "州志", "志", "集", "全集"]
    # "志" might be too broad (e.g., "同志"), but in the context of "Knowledge Base/Ancient", it's likely relevant.
    # Better to rely on path keywords too.
    
    path_keywords = ["古籍", "方志", "地方志", "善本", "二十四史", "四库全书"]
    
    ancient_books = []
    
    print(f"正在掃描 {len(all_files)} 個文件...")
    
    for f in all_files:
        name = f['name']
        path = f.get('path', '')
        full_path = f.get('full_path', '')
        
        is_ancient = False
        
        # Check path first (high confidence)
        for kw in path_keywords:
            if kw in path or kw in full_path:
                is_ancient = True
                break
        
        # Check name if path didn't match
        if not is_ancient:
            for kw in keywords:
                if kw in name:
                    # Filter out false positives if needed
                    is_ancient = True
                    break
        
        if is_ancient:
            ancient_books.append(f)

    print("\n" + "="*50)
    print("📜 古籍/縣志分類結果")
    print("="*50)
    print(f"總計發現: {len(ancient_books)} 本")
    
    # Save list
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ancient_books, f, ensure_ascii=False, indent=2)
        
    print(f"💾 列表已保存至: {output_file}")
    
    # Show samples
    print("\n樣本預覽:")
    for b in ancient_books[:10]:
        print(f"- {b['name']}")

if __name__ == "__main__":
    classify_ancient_books()
