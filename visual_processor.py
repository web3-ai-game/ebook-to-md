#!/usr/bin/env python3
"""
可視化流式處理管道 (Rich UI) - 煉金術士模型 V3
實時監控轉換進度，支持字符級流式顯示
"""
import os
import json
import time
import logging
import threading
import queue
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

from dedup_processor import DedupProcessor
from main import EbookConverterPipeline
from gemini_converter import GeminiConverter
from multi_cloud_downloader import MultiCloudDownloader

# 配置日誌文件，但不在控制台輸出，以免干擾 Rich UI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/visual_pipeline.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

class VisualPipelineProcessor:
    def __init__(self, 
                 cache_dir="./data/pipeline-cache",
                 batch_size=100,
                 max_cache_gb=80):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.batch_size = batch_size
        self.max_cache_bytes = max_cache_gb * 1024 * 1024 * 1024
        
        self.analysis_dir = Path("./data/baidu-analysis")
        self.categories_file = self.analysis_dir / "file_categories.json"
        
        self.dedup = DedupProcessor()
        self.downloader = MultiCloudDownloader(cache_dir=str(self.cache_dir))
        
        # 初始化 pipeline 但替換 gemini 為流式
        self.converter_pipeline = EbookConverterPipeline()
        self.gemini = self.converter_pipeline.gemini # 複用實例
        self.indexer = self.converter_pipeline.indexer # 複用索引器
        
        self.mongo_backup = Path("./data/mongodb-backup.jsonl")
        
        self.stats = {
            'total': 0, 'success': 0, 'failed': 0, 'skipped': 0, 
            'chars_processed': 0, 'files_processing': 0
        }
        
        # 用於 UI 通信的隊列
        self.log_queue = queue.Queue()
        self.stream_queue = queue.Queue() # 用於顯示實時文本流
        
        # 實時流日誌文件
        self.stream_log_file = Path("./data/live_stream.log")
        self.stream_log_file.parent.mkdir(parents=True, exist_ok=True)
        # Touch file immediately
        with open(self.stream_log_file, 'w') as f:
            f.write("=== 實時轉換流啟動 ===\n")
            
    def load_txt_files(self) -> List[Dict]:
        with open(self.categories_file, 'r', encoding='utf-8') as f:
            categories = json.load(f)
        return categories.get('txt_files', [])

    def read_file_safe(self, file_path: Path) -> str:
        encodings = ['utf-8', 'gb18030', 'gbk', 'big5', 'latin1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except: continue
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def process_single_file_stream(self, file_info: Dict, task_id, progress, dry_run=False):
        filename = file_info['name']
        try:
            # 1. 下載 (模擬或實際)
            if dry_run:
                # Dry run 模式：模擬延遲和內容
                time.sleep(1)
                content = f"# {filename}\n\n這是一個測試內容，用於演示流式傳輸效果。\n\n## 章節一\n\n測試文本..." * 5
                self.log_queue.put(f"[blue][Dry Run] 模擬讀取[/]: {filename}")
                local_path = self.cache_dir / f"mock_{filename}"
            else:
                # 使用 MultiCloudDownloader 下載
                # 確保 file_info 包含 source
                if 'source' not in file_info:
                    file_info['source'] = 'baidu' # 默認假設為百度網盤
                
                local_path_str = self.downloader.download_file(file_info)
                
                if not local_path_str or not Path(local_path_str).exists():
                    raise Exception("下載失敗")
                
                local_path = Path(local_path_str)
                content = self.read_file_safe(local_path)
                self.log_queue.put(f"[blue]讀取完成[/]: {filename} ({len(content)} 字符)")
            
            # 3. 流式轉換
            metadata = {'filename': filename, 'type': 'txt'}
            markdown_content = ""
            
            if dry_run:
                # 模擬流式輸出
                for char in content:
                    markdown_content += char
                    self.stream_queue.put(char)
                    progress.advance(task_id, advance=1)
                    time.sleep(0.001) # 模擬生成速度
            else:
                # 使用流式接口
                stream = self.gemini.convert_text_to_markdown_stream(content, metadata)
                
                for chunk in stream:
                    markdown_content += chunk
                    self.stream_queue.put(chunk) # 發送到 UI
                    # 更新進度條
                    progress.advance(task_id, advance=len(chunk))
            
            # 4. 保存
            md_path = Path("./data/markdown-output") / f"{Path(filename).stem}.md"
            if not dry_run:
                md_path.parent.mkdir(parents=True, exist_ok=True)
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
            
            # 5. 提取結構與索引 (新增)
            self.log_queue.put(f"[yellow]提取結構[/]: {filename}")
            if dry_run:
                time.sleep(0.5)
                structure = {"propositions": [], "mock": True}
            else:
                structure = self.gemini.extract_structure(markdown_content, filename)
                
                self.log_queue.put(f"[cyan]建立索引[/]: {filename}")
                self.indexer.add_document(str(local_path), str(md_path), structure)
                self.indexer.save_index() # 實時保存
            
            self.stats['success'] += 1
            self.log_queue.put(f"[green]處理完成[/]: {filename}")
            
            # 6. 備份
            if not dry_run:
                record = {
                    'filename': filename,
                    'status': 'success',
                    'timestamp': time.time()
                }
                with open(self.mongo_backup, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    
                # 清理下載的文件
                if local_path.exists():
                    os.remove(local_path)
            
        except Exception as e:
            self.stats['failed'] += 1
            self.log_queue.put(f"[red]失敗[/]: {filename} - {e}")
        finally:
            self.stats['files_processing'] -= 1

    def run(self, max_files=None, max_workers=100, dry_run=False):
        console = Console(force_terminal=True)
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )
        layout["main"].split_row(
            Layout(name="progress"),
            Layout(name="stream", ratio=2)
        )
        
        # Load files or mock files for dry run
        if dry_run and not self.categories_file.exists():
            files = [{'name': f'mock_book_{i}.txt', 'full_path': f'/mock/path/{i}', 'size': 1000} for i in range(10)]
            self.log_queue.put("[yellow]Dry Run: 使用模擬文件列表[/]")
        else:
            files = self.load_txt_files()
            
        new_files = self.dedup.filter_new_files(files)
        if max_files: new_files = new_files[:max_files]
        
        self.stats['total'] = len(new_files)
        
        # 進度條
        overall_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn()
        )
        overall_task = overall_progress.add_task("[yellow]總進度", total=len(new_files))
        
        # 實時文本緩衝區
        stream_buffer = [""] * 20
        
        with Live(layout, refresh_per_second=10, screen=True) as live:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                # 啟動任務
                for f in new_files:
                    self.stats['files_processing'] += 1
                    # 傳遞 dry_run 參數
                    fut = executor.submit(self.process_single_file_stream, f, overall_task, overall_progress, dry_run)
                    futures.append(fut)
                    
                    # 更新 UI (Loop logic same as before, simplified copy here)
                    # We need to process queues frequently to avoid blocking
                    start_time = time.time()
                    while time.time() - start_time < 0.1: # Process queues for a bit
                        while not self.log_queue.empty():
                            msg = self.log_queue.get()
                            # Optional: Display logs in footer or separate panel
                            
                        while not self.stream_queue.empty():
                            chunk = self.stream_queue.get()
                            with open(self.stream_log_file, 'a', encoding='utf-8') as log_f:
                                log_f.write(chunk)
                            
                            last_line = stream_buffer[-1] + chunk
                            if "\n" in last_line:
                                parts = last_line.split("\n")
                                stream_buffer[-1] = parts[0]
                                stream_buffer.extend(parts[1:])
                                stream_buffer = stream_buffer[-20:]
                            else:
                                stream_buffer[-1] = last_line
                        
                        layout["header"].update(Panel(f"🚀 煉金術士引擎 | 總任務: {self.stats['total']} | 處理中: {self.stats['files_processing']} | 成功: {self.stats['success']} | 模式: {'Dry Run' if dry_run else 'Production'}", style="bold blue"))
                        layout["progress"].update(Panel(overall_progress, title="任務隊列"))
                        text_display = "\n".join(stream_buffer)
                        layout["stream"].update(Panel(Syntax(text_display, "markdown"), title="實時轉換流 (Live Stream)"))
                        overall_progress.update(overall_task, advance=0)
                    
                    # Limit submission rate slightly
                    time.sleep(0.05)
                
                # 等待完成
                while any(f.running() for f in futures):
                     # Process queues
                    while not self.log_queue.empty(): self.log_queue.get()
                    while not self.stream_queue.empty():
                        chunk = self.stream_queue.get()
                        last_line = stream_buffer[-1] + chunk
                        if "\n" in last_line:
                            parts = last_line.split("\n")
                            stream_buffer[-1] = parts[0]
                            stream_buffer.extend(parts[1:])
                            stream_buffer = stream_buffer[-20:]
                        else:
                            stream_buffer[-1] = last_line
                            
                    completed_count = sum(1 for f in futures if f.done())
                    overall_progress.update(overall_task, completed=completed_count)
                    
                    layout["header"].update(Panel(f"🚀 煉金術士引擎 | 總任務: {self.stats['total']} | 處理中: {self.stats['files_processing']} | 成功: {self.stats['success']}", style="bold blue"))
                    text_display = "\n".join(stream_buffer)
                    layout["stream"].update(Panel(Syntax(text_display, "markdown"), title="實時轉換流 (Live Stream)"))
                    
                    time.sleep(0.1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num', type=int, default=500)
    parser.add_argument('-w', '--workers', type=int, default=50)
    parser.add_argument('--dry-run', action='store_true', help='模擬運行，不實際下載和調用API')
    args = parser.parse_args()
    
    processor = VisualPipelineProcessor()
    processor.run(max_files=args.num, max_workers=args.workers, dry_run=args.dry_run)
