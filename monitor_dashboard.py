#!/usr/bin/env python3
"""實時監控面板 - 顯示電子書轉換進度和系統狀態"""
import os
import sys
import time
import json
import psutil
from pathlib import Path
from datetime import datetime
import subprocess

class MonitorDashboard:
    """實時監控面板"""
    
    def __init__(self):
        self.start_time = time.time()
        self.processed_files = 0
        self.failed_files = 0
        self.total_size_mb = 0
        self.index_dir = Path("./data/wittgenstein-index")
        self.output_dir = Path("./data/markdown-output")
        
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_system_stats(self):
        """獲取系統狀態"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # 獲取 CPU 溫度（如果可用）
        try:
            temp_output = subprocess.run(
                ['cat', '/sys/class/thermal/thermal_zone0/temp'],
                capture_output=True,
                text=True
            )
            cpu_temp = int(temp_output.stdout.strip()) / 1000
        except:
            cpu_temp = 0
        
        return {
            'cpu_percent': cpu_percent,
            'cpu_temp': cpu_temp,
            'mem_total_gb': mem.total / (1024**3),
            'mem_used_gb': mem.used / (1024**3),
            'mem_percent': mem.percent,
            'disk_total_gb': disk.total / (1024**3),
            'disk_used_gb': disk.used / (1024**3),
            'disk_free_gb': disk.free / (1024**3),
            'disk_percent': disk.percent
        }
    
    def get_processing_stats(self):
        """獲取處理統計"""
        # 讀取主索引
        index_file = self.index_dir / "master_index.json"
        if index_file.exists():
            with open(index_file) as f:
                index_data = json.load(f)
                self.processed_files = len(index_data.get('documents', {}))
        
        # 統計輸出文件
        if self.output_dir.exists():
            md_files = list(self.output_dir.glob("*.md"))
            total_size = sum(f.stat().st_size for f in md_files)
            self.total_size_mb = total_size / (1024**2)
            
        # 獲取 PDF 處理詳情 (從日誌或狀態文件)
        pdf_stats = {'total_pages': 0, 'processed_pages': 0, 'current_file': 'None'}
        status_file = Path("/tmp/pdf_processing_status.json")
        if status_file.exists():
            try:
                with open(status_file) as f:
                    pdf_stats = json.load(f)
            except: pass
        
        # 計算速度
        elapsed = time.time() - self.start_time
        speed = self.processed_files / elapsed if elapsed > 0 else 0
        
        return {
            'processed': self.processed_files,
            'failed': self.failed_files,
            'total_size_mb': self.total_size_mb,
            'elapsed_seconds': elapsed,
            'speed_per_min': speed * 60,
            'pdf_stats': pdf_stats
        }
    
    def draw_progress_bar(self, percent, width=50):
        """繪製進度條"""
        filled = int(width * percent / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {percent:.1f}%"
    
    def format_time(self, seconds):
        """格式化時間"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def display(self):
        """顯示監控面板"""
        self.clear_screen()
        
        sys_stats = self.get_system_stats()
        proc_stats = self.get_processing_stats()
        
        # 標題
        print("=" * 80)
        print("🚀 電子書轉 Markdown 實時監控面板 | Gemini 2.5 Flash".center(80))
        print("=" * 80)
        print()
        
        # 系統狀態
        print("📊 系統狀態 (4vCPU / 16GB RAM)")
        print("-" * 80)
        
        # CPU
        cpu_bar = self.draw_progress_bar(sys_stats['cpu_percent'], 40)
        cpu_color = "🔴" if sys_stats['cpu_percent'] > 80 else "🟡" if sys_stats['cpu_percent'] > 50 else "🟢"
        print(f"CPU:  {cpu_bar} {cpu_color}")
        if sys_stats['cpu_temp'] > 0:
            print(f"      溫度: {sys_stats['cpu_temp']:.1f}°C")
        
        # 內存
        mem_bar = self.draw_progress_bar(sys_stats['mem_percent'], 40)
        mem_color = "🔴" if sys_stats['mem_percent'] > 80 else "🟡" if sys_stats['mem_percent'] > 50 else "🟢"
        print(f"RAM:  {mem_bar} {mem_color}")
        print(f"      {sys_stats['mem_used_gb']:.1f}GB / {sys_stats['mem_total_gb']:.1f}GB")
        
        # 磁盤
        disk_bar = self.draw_progress_bar(sys_stats['disk_percent'], 40)
        disk_color = "🔴" if sys_stats['disk_percent'] > 90 else "🟡" if sys_stats['disk_percent'] > 70 else "🟢"
        print(f"DISK: {disk_bar} {disk_color}")
        print(f"      剩餘: {sys_stats['disk_free_gb']:.1f}GB / {sys_stats['disk_total_gb']:.1f}GB")
        
        print()
        
        # 處理進度
        print("📈 處理進度")
        print("-" * 80)
        print(f"✅ 已完成: {proc_stats['processed']} 個文件")
        print(f"❌ 失敗:   {proc_stats['failed']} 個文件")
        print(f"📦 輸出:   {proc_stats['total_size_mb']:.1f} MB")
        print(f"⏱️  運行時間: {self.format_time(proc_stats['elapsed_seconds'])}")
        print(f"⚡ 處理速度: {proc_stats['speed_per_min']:.2f} 文件/分鐘")
        
        # PDF 詳細進度
        pdf_stats = proc_stats.get('pdf_stats', {})
        if pdf_stats.get('current_file') != 'None':
            print("-" * 80)
            print(f"📄 當前 PDF: {pdf_stats.get('current_file')}")
            total_p = pdf_stats.get('total_pages', 0)
            curr_p = pdf_stats.get('processed_pages', 0)
            if total_p > 0:
                percent = (curr_p / total_p) * 100
                p_bar = self.draw_progress_bar(percent, 40)
                print(f"   頁面進度: {p_bar} {curr_p}/{total_p}")
                print(f"   當前階段: {pdf_stats.get('stage', 'Processing')}")
        
        print()
        
        # 實時日誌
        print("📝 最新處理文件")
        print("-" * 80)
        if self.output_dir.exists():
            md_files = sorted(
                self.output_dir.glob("*.md"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:5]
            
            for i, f in enumerate(md_files, 1):
                size_kb = f.stat().st_size / 1024
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                time_str = mtime.strftime("%H:%M:%S")
                print(f"{i}. [{time_str}] {f.name[:50]:50s} ({size_kb:6.1f} KB)")
        
        print()
        print("=" * 80)
        print(f"⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("按 Ctrl+C 停止監控")
        print("=" * 80)
    
    def run(self, interval=1):
        """運行監控面板"""
        try:
            while True:
                self.display()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n監控已停止")


if __name__ == "__main__":
    dashboard = MonitorDashboard()
    dashboard.run(interval=1)  # 每秒刷新
