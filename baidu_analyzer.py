#!/usr/bin/env python3
"""百度網盤電子書庫分析器 - 建立目錄結構並分類"""
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaiduLibraryAnalyzer:
    """百度網盤電子書庫分析器"""
    
    def __init__(self, output_dir="./data/baidu-analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件分類
        self.categories = {
            'txt_files': [],           # TXT 文本（優先處理）
            'epub_mobi': [],           # EPUB/MOBI（優先處理）
            'ancient_books': [],       # 縣誌/方誌/古籍（S3 索引，不轉 Markdown）
            'pdf_text': [],            # PDF 文字版（需檢測）
            'pdf_scan': [],            # PDF 掃描版（最後處理）
            'doc_files': [],           # DOC/DOCX
            'other_ebooks': [],        # 其他電子書格式
            'junk_files': []           # 垃圾文件
        }
        
        # 關鍵詞定義
        self.ancient_keywords = ['县志', '方志', '古籍', '扫描', '影印', '全集', '史料', '通鉴']
        
        # 格式定義
        self.priority_formats = ['.txt', '.epub', '.mobi', '.azw', '.azw3']
        self.doc_formats = ['.doc', '.docx', '.rtf', '.odt']
        self.other_formats = ['.djvu', '.fb2', '.md', '.html', '.htm']
        self.junk_formats = ['.exe', '.dll', '.ini', '.db', '.bat', '.chm', '.url', '.lnk']
        
        self.stats = {
            'total_dirs': 0,
            'total_files': 0,
            'total_size': 0
        }
    
    def scan_directory(self, remote_path="/知識庫", max_depth=10, _depth=0) -> Dict:
        """遞歸掃描百度網盤目錄"""
        if _depth > max_depth:
            logger.warning(f"達到最大深度 {max_depth}，停止掃描: {remote_path}")
            return {}
        
        indent = "  " * _depth
        logger.info(f"{indent}📂 掃描: {remote_path}")
        
        directory_tree = {
            'path': remote_path,
            'name': os.path.basename(remote_path) or remote_path,
            'type': 'directory',
            'children': [],
            'files': [],
            'stats': {'dirs': 0, 'files': 0, 'size': 0}
        }
        
        try:
            result = subprocess.run(
                ["bypy", "list", remote_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            lines = result.stdout.strip().split('\n')
            subdirs = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('/apps/bypy') or '($t $f $s $m $d)' in line:
                    continue
                
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                file_type = parts[0]
                filename = parts[1]
                
                # 目錄
                if file_type == 'D':
                    subdir_path = f"{remote_path}/{filename}".replace('//', '/')
                    subdirs.append((filename, subdir_path))
                    self.stats['total_dirs'] += 1
                    continue
                
                # 文件
                if file_type == 'F':
                    size = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                    ext = os.path.splitext(filename)[1].lower()
                    
                    file_info = {
                        'name': filename,
                        'source': 'baidu',
                        'path': remote_path,
                        'full_path': f"{remote_path}/{filename}".replace('//', '/'),
                        'size': size,
                        'ext': ext,
                        'type': self._classify_file(filename, ext)
                    }
                    
                    directory_tree['files'].append(file_info)
                    directory_tree['stats']['files'] += 1
                    directory_tree['stats']['size'] += size
                    
                    self.stats['total_files'] += 1
                    self.stats['total_size'] += size
                    
                    # 分類
                    self._categorize_file(file_info)
            
            # 遞歸掃描子目錄
            if subdirs:
                logger.info(f"{indent}  📁 發現 {len(subdirs)} 個子目錄")
                
            for subdir_name, subdir_path in subdirs:
                try:
                    subtree = self.scan_directory(subdir_path, max_depth, _depth + 1)
                    if subtree:
                        directory_tree['children'].append(subtree)
                        directory_tree['stats']['dirs'] += 1 + subtree['stats']['dirs']
                        directory_tree['stats']['files'] += subtree['stats']['files']
                        directory_tree['stats']['size'] += subtree['stats']['size']
                except Exception as e:
                    logger.warning(f"{indent}  ✗ 無法掃描 {subdir_name}: {e}")
            
            # 顯示當前目錄統計
            if directory_tree['files'] or directory_tree['children']:
                logger.info(f"{indent}  ✓ 本層: {len(directory_tree['files'])} 文件, "
                          f"{len(directory_tree['children'])} 子目錄")
            
            return directory_tree
            
        except subprocess.TimeoutExpired:
            logger.error(f"{indent}✗ 掃描超時: {remote_path}")
            return {}
        except Exception as e:
            logger.error(f"{indent}✗ 掃描失敗 {remote_path}: {e}")
            return {}
    
    def _classify_file(self, filename: str, ext: str) -> str:
        """分類文件類型"""
        # 1. 優先檢查是否為古籍/縣誌 (基於文件名關鍵詞)
        if any(kw in filename for kw in self.ancient_keywords):
            return 'ancient'

        if ext in self.priority_formats:
            return 'priority'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in self.doc_formats:
            return 'document'
        elif ext in self.other_formats:
            return 'other_ebook'
        elif ext in self.junk_formats:
            return 'junk'
        else:
            return 'unknown'
    
    def _categorize_file(self, file_info: Dict):
        """將文件歸類到對應類別"""
        ext = file_info['ext']
        file_type = file_info['type']
        
        if file_type == 'ancient':
            self.categories['ancient_books'].append(file_info)
        elif file_type == 'priority':
            if ext == '.txt':
                self.categories['txt_files'].append(file_info)
            else:
                self.categories['epub_mobi'].append(file_info)
        elif file_type == 'pdf':
            # PDF 暫時都歸類為待檢測
            self.categories['pdf_text'].append(file_info)
        elif file_type == 'document':
            self.categories['doc_files'].append(file_info)
        elif file_type == 'other_ebook':
            self.categories['other_ebooks'].append(file_info)
        elif file_type == 'junk':
            self.categories['junk_files'].append(file_info)
    
    def save_results(self, directory_tree: Dict):
        """保存分析結果"""
        # 1. 保存完整目錄樹
        tree_file = self.output_dir / "directory_tree.json"
        with open(tree_file, 'w', encoding='utf-8') as f:
            json.dump(directory_tree, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 目錄樹已保存: {tree_file}")
        
        # 2. 保存分類結果
        categories_file = self.output_dir / "file_categories.json"
        with open(categories_file, 'w', encoding='utf-8') as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 分類結果已保存: {categories_file}")
        
        # 3. 生成 Markdown 報告
        self._generate_markdown_report(directory_tree)
        
        # 4. 生成處理計劃
        self._generate_processing_plan()
    
    def _generate_markdown_report(self, directory_tree: Dict):
        """生成 Markdown 格式的分析報告"""
        report_file = self.output_dir / "analysis_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 百度網盤電子書庫分析報告\n\n")
            f.write(f"生成時間: {os.popen('date').read().strip()}\n\n")
            f.write("---\n\n")
            
            # 總體統計
            f.write("## 📊 總體統計\n\n")
            f.write(f"- **總目錄數**: {self.stats['total_dirs']}\n")
            f.write(f"- **總文件數**: {self.stats['total_files']}\n")
            f.write(f"- **總大小**: {self.stats['total_size'] / 1024 / 1024 / 1024:.2f} GB\n\n")
            
            # 分類統計
            f.write("## 📚 文件分類統計\n\n")
            f.write("### 📜 縣誌/方誌/古籍（僅索引）\n\n")
            f.write(f"- **文件數**: {len(self.categories['ancient_books'])} 個\n")
            f.write("- **策略**: 跳過 OCR，直接上傳 S3 並建立索引\n\n")

            f.write("### 優先處理（便宜、快速）\n\n")
            f.write(f"- **TXT 文件**: {len(self.categories['txt_files'])} 個\n")
            f.write(f"- **EPUB/MOBI**: {len(self.categories['epub_mobi'])} 個\n\n")
            
            f.write("### 標準處理\n\n")
            f.write(f"- **DOC/DOCX**: {len(self.categories['doc_files'])} 個\n")
            f.write(f"- **其他電子書**: {len(self.categories['other_ebooks'])} 個\n\n")
            
            f.write("### PDF 文件（需進一步檢測）\n\n")
            f.write(f"- **PDF 總數**: {len(self.categories['pdf_text'])} 個\n")
            f.write(f"- ⚠️ 需要檢測是文字版還是掃描版\n\n")
            
            f.write("### 垃圾文件\n\n")
            f.write(f"- **垃圾文件**: {len(self.categories['junk_files'])} 個\n")
            f.write(f"- 格式: {', '.join(self.junk_formats)}\n\n")
            
            # 處理建議
            f.write("## 🎯 處理建議\n\n")
            f.write("### 第一階段：優先處理（立即開始）\n\n")
            f.write(f"處理 {len(self.categories['txt_files']) + len(self.categories['epub_mobi'])} 個 TXT/EPUB 文件\n")
            f.write("- 成本低\n")
            f.write("- 速度快\n")
            f.write("- 可使用 Gemini Flash 模型\n\n")
            
            f.write("### 第二階段：標準處理\n\n")
            f.write(f"處理 {len(self.categories['doc_files'])} 個 DOC/DOCX 文件\n\n")
            
            f.write("### 第三階段：PDF 檢測與分流\n\n")
            f.write(f"檢測 {len(self.categories['pdf_text'])} 個 PDF 文件\n")
            f.write("- 文字版 PDF → 直接處理\n")
            f.write("- 掃描版 PDF → 按需處理（成本高）\n\n")
            
            # 目錄結構預覽
            f.write("## 📁 目錄結構預覽\n\n")
            f.write("```\n")
            self._write_tree_preview(f, directory_tree, 0, max_depth=3)
            f.write("```\n\n")
            
            # Top 10 最大文件
            f.write("## 📦 Top 10 最大文件\n\n")
            all_files = []
            for category in self.categories.values():
                all_files.extend(category)
            all_files.sort(key=lambda x: x['size'], reverse=True)
            
            for i, file_info in enumerate(all_files[:10], 1):
                size_mb = file_info['size'] / 1024 / 1024
                f.write(f"{i}. **{file_info['name']}** ({size_mb:.1f} MB) - {file_info['type']}\n")
                f.write(f"   - 路徑: `{file_info['full_path']}`\n\n")
        
        logger.info(f"✓ Markdown 報告已生成: {report_file}")
    
    def _write_tree_preview(self, f, node: Dict, depth: int, max_depth: int):
        """寫入目錄樹預覽"""
        if depth > max_depth:
            return
        
        indent = "  " * depth
        f.write(f"{indent}{node['name']}/\n")
        
        # 顯示文件數量
        if node['files']:
            f.write(f"{indent}  ({len(node['files'])} 個文件)\n")
        
        # 遞歸顯示子目錄
        for child in node['children'][:5]:  # 只顯示前5個子目錄
            self._write_tree_preview(f, child, depth + 1, max_depth)
        
        if len(node['children']) > 5:
            f.write(f"{indent}  ... 還有 {len(node['children']) - 5} 個子目錄\n")
    
    def _generate_processing_plan(self):
        """生成處理計劃"""
        plan_file = self.output_dir / "processing_plan.md"
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write("# 電子書處理計劃\n\n")
            f.write("## 階段 0: 古籍/縣誌歸檔 (Fast Track)\n\n")
            f.write(f"- 文件數: {len(self.categories['ancient_books'])}\n")
            f.write("- 操作: 僅下載 -> S3 備份 -> 建立元數據索引\n")
            f.write("- 預計速度: 極快 (僅受帶寬限制)\n\n")

            f.write("## 階段 1: TXT 文件（優先）\n\n")
            f.write(f"- 文件數: {len(self.categories['txt_files'])}\n")
            f.write(f"- 預計時間: {len(self.categories['txt_files']) / 20:.1f} 分鐘（20文件/分鐘）\n")
            f.write(f"- 成本: 極低\n\n")
            
            f.write("## 階段 2: EPUB/MOBI\n\n")
            f.write(f"- 文件數: {len(self.categories['epub_mobi'])}\n")
            f.write(f"- 預計時間: {len(self.categories['epub_mobi']) / 15:.1f} 分鐘（15文件/分鐘）\n")
            f.write(f"- 成本: 低\n\n")
            
            f.write("## 階段 3: DOC/DOCX\n\n")
            f.write(f"- 文件數: {len(self.categories['doc_files'])}\n")
            f.write(f"- 預計時間: {len(self.categories['doc_files']) / 10:.1f} 分鐘（10文件/分鐘）\n")
            f.write(f"- 成本: 中等\n\n")
            
            f.write("## 階段 4: PDF 檢測\n\n")
            f.write(f"- 文件數: {len(self.categories['pdf_text'])}\n")
            f.write(f"- 需要先檢測是文字版還是掃描版\n")
            f.write(f"- 文字版可直接處理，掃描版按需處理\n\n")
            
            f.write("## 垃圾清理\n\n")
            f.write(f"- 垃圾文件: {len(self.categories['junk_files'])} 個\n")
            f.write(f"- 建議: 直接忽略\n\n")
        
        logger.info(f"✓ 處理計劃已生成: {plan_file}")


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='百度網盤電子書庫分析器')
    parser.add_argument('-p', '--path', default='/知識庫', help='百度網盤路徑')
    parser.add_argument('-d', '--depth', type=int, default=10, help='最大掃描深度')
    
    args = parser.parse_args()
    
    analyzer = BaiduLibraryAnalyzer()
    
    logger.info("=" * 80)
    logger.info("🚀 百度網盤電子書庫分析器啟動")
    logger.info("=" * 80)
    
    # 掃描目錄
    directory_tree = analyzer.scan_directory(args.path, max_depth=args.depth)
    
    # 保存結果
    if directory_tree:
        analyzer.save_results(directory_tree)
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 分析完成！")
        logger.info("=" * 80)
        logger.info(f"總目錄: {analyzer.stats['total_dirs']}")
        logger.info(f"總文件: {analyzer.stats['total_files']}")
        logger.info(f"總大小: {analyzer.stats['total_size'] / 1024 / 1024 / 1024:.2f} GB")
        logger.info(f"\n報告位置: {analyzer.output_dir}/analysis_report.md")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
