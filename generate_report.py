import json
import os
import time
from pathlib import Path
from collections import Counter
import datetime

def generate_report():
    print("正在生成全量深度探測報告...")
    
    # Paths
    base_dir = Path(".")
    data_dir = base_dir / "data"
    categories_file = data_dir / "baidu-analysis/file_categories.json"
    mongo_backup = data_dir / "mongodb-backup.jsonl"
    output_dir = data_dir / "markdown-output"
    report_file = Path("./data/baidu_probe_report.md")
    
    # 1. Load Baidu Content Analysis
    if not categories_file.exists():
        print(f"Error: {categories_file} not found.")
        return

    with open(categories_file, 'r', encoding='utf-8') as f:
        categories = json.load(f)
    
    # Calculate totals for ALL categories
    all_files = []
    category_stats = {}
    
    grand_total_size = 0
    grand_total_files = 0
    
    # Categories to include
    target_cats = ['txt_files', 'pdf_text', 'epub_mobi', 'doc_files', 'other_ebooks', 'pdf_scan']
    
    for cat in target_cats:
        file_list = categories.get(cat, [])
        count = len(file_list)
        size = sum(f.get('size', 0) for f in file_list)
        
        category_stats[cat] = {
            'count': count,
            'size': size
        }
        
        grand_total_files += count
        grand_total_size += size
        all_files.extend(file_list)
        
    # TXT specific for current pipeline status
    txt_files = categories.get('txt_files', [])
    txt_total = len(txt_files)
    
    # 2. Load Conversion Progress
    processed_records = []
    if mongo_backup.exists():
        with open(mongo_backup, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    processed_records.append(json.loads(line))
                except:
                    pass
    
    # 3. Analyze Progress
    status_counts = Counter(r.get('status', 'unknown') for r in processed_records)
    processed_filenames = set(r.get('filename') for r in processed_records if r.get('status') == 'success')
    
    # 4. Check Actual Output
    actual_markdown_files = list(output_dir.rglob("*.md"))
    actual_count = len(actual_markdown_files)
    actual_size = sum(f.stat().st_size for f in actual_markdown_files)
    
    # 5. Calculate Metrics (TXT Only for now)
    success_count = status_counts.get('success', 0)
    failed_count = status_counts.get('failed', 0)
    skipped_count = status_counts.get('skipped', 0)
    
    unique_success = len(processed_filenames)
    # Remaining for TXT pipeline
    remaining_txt = txt_total - unique_success
    
    # Overall Progress (against ALL files)
    total_progress_percent = (unique_success / grand_total_files * 100) if grand_total_files > 0 else 0
    
    # 6. Generate Report Content
    lines = []
    lines.append(f"# 百度網盤全量內容深度探測報告")
    lines.append(f"**生成時間**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    lines.append(f"## 1. 全量知識庫概覽 (真實規模)")
    lines.append(f"> ⚠️ **發現**: 之前僅統計了 TXT 格式。實際上還有大量 PDF 和其他電子書格式。")
    lines.append(f"- **總文件數**: **{grand_total_files:,}**")
    lines.append(f"- **總體積**: **{grand_total_size / (1024*1024*1024):.2f} GB**")
    
    lines.append(f"\n### 格式分佈詳情")
    lines.append(f"| 格式類型 | 文件數量 | 總大小 | 處理難度 | 當前狀態 |")
    lines.append(f"|---|---|---|---|---|")
    
    # Map for friendly names
    cat_map = {
        'txt_files': ('純文本 (TXT)', '⭐⭐ (易)', '🔥 進行中'),
        'pdf_text': ('PDF (文字版)', '⭐⭐⭐⭐ (中)', '⏳ 待啟動'),
        'pdf_scan': ('PDF (掃描版)', '⭐⭐⭐⭐⭐ (難)', '⏳ 待啟動'),
        'epub_mobi': ('EPUB/MOBI', '⭐⭐⭐ (中)', '⏳ 待啟動'),
        'doc_files': ('Word (DOC/DOCX)', '⭐⭐⭐ (中)', '⏳ 待啟動'),
        'other_ebooks': ('其他格式', '⭐⭐⭐', '⏳ 待啟動')
    }
    
    for cat in target_cats:
        stats = category_stats.get(cat)
        if stats and stats['count'] > 0:
            name, diff, status = cat_map.get(cat, (cat, '未知', '待定'))
            size_str = f"{stats['size'] / (1024*1024):.2f} MB"
            if stats['size'] > 1024*1024*1024:
                size_str = f"{stats['size'] / (1024*1024*1024):.2f} GB"
                
            lines.append(f"| {name} | {stats['count']:,} | {size_str} | {diff} | {status} |")
    
    lines.append(f"\n## 2. 當前處理進度 (僅 TXT 管道)")
    lines.append(f"- **TXT 轉化進度**: {unique_success}/{txt_total} ({(unique_success/txt_total*100):.2f}%)")
    lines.append(f"- **實際產出**: {actual_count:,} 個 Markdown 文件 ({actual_size / (1024*1024):.2f} MB)")
    
    # Progress Bar (TXT)
    bar_len = 20
    txt_percent = (unique_success / txt_total * 100) if txt_total > 0 else 0
    filled = int(txt_percent / 100 * bar_len)
    bar = '█' * filled + '░' * (bar_len - filled)
    lines.append(f"`TXT管道: [{bar}] {txt_percent:.2f}%`")

    lines.append(f"\n## 3. 下一步擴展計劃")
    lines.append(f"1. **PDF 處理 (重點)**: 發現 5000+ 個 PDF 文件，需部署 OCR/PDF 解析管道 (如 pdfplumber/PaddleOCR)。")
    lines.append(f"2. **EPUB/MOBI 解析**: 使用 ebooklib 進行結構化提取。")
    lines.append(f"3. **Word 解析**: 使用 python-docx 提取。")

    # 4. Detailed folder breakdown (keep top 20)
    lines.append(f"\n## 4. 頂層目錄內容分佈 (Top 20)")
    folder_counts = Counter()
    for f in all_files:
        path_parts = f.get('full_path', '').split('/')
        if len(path_parts) > 2:
            top_folder = path_parts[1]
            folder_counts[top_folder] += 1
            
    lines.append(f"| 目錄 | 文件數 |")
    lines.append(f"|---|---|")
    for folder, count in folder_counts.most_common(20):
        lines.append(f"| {folder} | {count:,} |")

    # Write Report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    print(f"全量報告已生成: {report_file}")
    print("\n" + "\n".join(lines[:35]))

if __name__ == "__main__":
    generate_report()
