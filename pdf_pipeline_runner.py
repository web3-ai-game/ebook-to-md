#!/usr/bin/env python3
"""
PDF 處理管道 - 專門處理 PDF 文件 (包含 OCR)
下載 → 智能識別(文字/掃描) → OCR/提取 → 轉 Markdown → 保存
"""
import os
import json
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from multi_cloud_downloader import MultiCloudDownloader
from pdf_processor import PDFProcessor

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./pdf_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PDFPipeline")

class PDFPipelineRunner:
    def __init__(self, 
                 workers=2, 
                 cache_dir="./data/pdf-pipeline-cache",
                 output_dir="./data/markdown-output"):
        self.workers = workers
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.downloader = MultiCloudDownloader(cache_dir=str(self.cache_dir))
        self.processor = PDFProcessor() # Shared resource, but fitz/ocr methods are generally thread-safe or we instantiate per file?
        # RapidOCR might not be thread-safe if sharing same instance across threads. 
        # Better to instantiate inside the worker or use a lock.
        # For safety and simplicity, we'll instantiate inside process_single_file.
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'ocr_pages': 0
        }

    def load_files(self) -> List[Dict]:
        json_path = Path("./data/baidu-analysis/file_categories.json")
        if not json_path.exists():
            logger.error("找不到文件分類列表")
            return []
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Combine all PDF types if needed, but report said they are in 'pdf_text' mostly
        pdfs = data.get('pdf_text', [])
        logger.info(f"加載了 {len(pdfs)} 個 PDF 任務")
        return pdfs

    def process_single_file(self, file_info):
        filename = file_info['name']
        relative_path = file_info.get('path', '').strip('/')
        
        # 1. Check if output exists
        # Construct output path preserving directory structure
        # /知識庫/A/B/file.pdf -> data/markdown-output/知識庫/A/B/file.md
        
        # remove /知識庫 prefix if present to avoid double root
        safe_rel_path = relative_path
        if safe_rel_path.startswith("知識庫/"):
            safe_rel_path = safe_rel_path[4:]
            
        target_dir = self.output_dir / safe_rel_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = target_dir / (Path(filename).stem + ".md")
        
        if target_file.exists():
            logger.info(f"⏭️ 跳過已存在: {filename}")
            return 'skipped'

        logger.info(f"📥 開始下載: {filename}")
        
        # 2. Download
        if 'source' not in file_info:
            file_info['source'] = 'baidu'
            
        local_path = self.downloader.download_file(file_info)
        
        if not local_path:
            logger.error(f"❌ 下載失敗: {filename}")
            return 'failed'
            
        try:
            # 3. Process
            # Instantiate processor here to avoid thread safety issues with ONNX runtime
            processor = PDFProcessor() 
            
            logger.info(f"⚙️ 正在處理 (OCR): {filename}")
            processor.extract_content(local_path, str(target_file))
            
            logger.info(f"✅ 處理完成: {filename}")
            return 'success'
            
        except Exception as e:
            logger.error(f"❌ 處理失敗 {filename}: {e}")
            return 'failed'
            
        finally:
            # 4. Cleanup
            try:
                if local_path and os.path.exists(local_path):
                    os.remove(local_path)
            except:
                pass

    def run(self):
        files = self.load_files()
        self.stats['total'] = len(files)
        
        logger.info(f"🚀 啟動 PDF 處理管道 (Workers: {self.workers})")
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Map futures
            future_to_file = {
                executor.submit(self.process_single_file, f): f 
                for f in files
            }
            
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    result = future.result()
                    self.stats[result] += 1
                except Exception as e:
                    logger.error(f"Unhandled exception for {file_info['name']}: {e}")
                    self.stats['failed'] += 1
                    
                # Log progress
                processed = self.stats['success'] + self.stats['failed'] + self.stats['skipped']
                if processed % 10 == 0:
                    logger.info(f"📊 進度: {processed}/{self.stats['total']} (S:{self.stats['success']} F:{self.stats['failed']} Sk:{self.stats['skipped']})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=2, help='并发 OCR 进程数 (建议 2-4)')
    args = parser.parse_args()
    
    runner = PDFPipelineRunner(workers=args.workers)
    runner.run()
