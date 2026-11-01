#!/usr/bin/env python3
"""
古籍/縣志專用處理管道 (Ancient Book Pipeline)
專門處理豎排、毛筆字、掃描版 PDF
使用 RapidOCR (Angle CLS Enabled) 進行高精度識別
"""
import os
import json
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
        logging.FileHandler("./ancient_book_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AncientBookPipeline")

class AncientBookRunner:
    def __init__(self, 
                 workers=2, 
                 cache_dir="./data/ancient-book-cache",
                 output_dir="./data/markdown-output"):
        self.workers = workers
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.downloader = MultiCloudDownloader(cache_dir=str(self.cache_dir))
        # Processor instantiated per file to ensure thread safety with ONNX
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

    def load_files(self) -> List[Dict]:
        json_path = Path("./data/ancient_books_list.json")
        if not json_path.exists():
            logger.error("找不到古籍列表: ancient_books_list.json")
            return []
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.info(f"加載了 {len(data)} 本古籍任務")
        return data

    def process_single_file(self, file_info):
        filename = file_info['name']
        relative_path = file_info.get('path', '').strip('/')
        
        # remove /知識庫 prefix if present
        safe_rel_path = relative_path
        if safe_rel_path.startswith("知識庫/"):
            safe_rel_path = safe_rel_path[4:]
            
        target_dir = self.output_dir / safe_rel_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = target_dir / (Path(filename).stem + ".md")
        
        if target_file.exists():
            logger.info(f"⏭️ 跳過已存在: {filename}")
            return 'skipped'

        logger.info(f"📥 開始下載古籍: {filename}")
        
        if 'source' not in file_info:
            file_info['source'] = 'baidu'
            
        local_path = self.downloader.download_file(file_info)
        
        if not local_path:
            logger.error(f"❌ 下載失敗: {filename}")
            return 'failed'
            
        try:
            # Instantiate processor (Ancient Mode is default now in PDFProcessor init)
            processor = PDFProcessor() 
            
            logger.info(f"📜 正在識別古籍 (OCR): {filename}")
            processor.extract_content(local_path, str(target_file))
            
            logger.info(f"✅ 處理完成: {filename}")
            return 'success'
            
        except Exception as e:
            logger.error(f"❌ 處理失敗 {filename}: {e}")
            return 'failed'
            
        finally:
            try:
                if local_path and os.path.exists(local_path):
                    os.remove(local_path)
            except:
                pass

    def run(self):
        files = self.load_files()
        self.stats['total'] = len(files)
        
        logger.info(f"🚀 啟動古籍專用管道 (Workers: {self.workers})")
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
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
                    
                processed = self.stats['success'] + self.stats['failed'] + self.stats['skipped']
                if processed % 5 == 0:
                    logger.info(f"📊 古籍進度: {processed}/{self.stats['total']} (S:{self.stats['success']} F:{self.stats['failed']} Sk:{self.stats['skipped']})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=2, help='并发 OCR 进程数')
    args = parser.parse_args()
    
    runner = AncientBookRunner(workers=args.workers)
    runner.run()
