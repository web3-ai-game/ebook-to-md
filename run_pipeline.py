#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

from multi_cloud_downloader import MultiCloudDownloader
from pipeline_processor import PipelineProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import argparse

def main():
    parser = argparse.ArgumentParser(description='電子書轉換管道 - 煉金術士版')
    parser.add_argument('--path', type=str, default='/apps/bypy', help='百度網盤路徑')
    parser.add_argument('--workers', type=int, default=50, help='並發線程數')
    parser.add_argument('--limit', type=int, default=None, help='限制處理文件數量')
    parser.add_argument('--yes', '-y', action='store_true', help='自動確認所有提示')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("電子書轉換管道 - 煉金術士版 (X.AI + MongoDB + S3)")
    logger.info("=" * 70)
    
    logger.info("\n步驟 1: 初始化組件")
    # 用於列出文件
    downloader = MultiCloudDownloader(cache_dir="./data/baidu-cache")
    
    # 高並發處理器
    processor = PipelineProcessor(
        cache_dir="./data/pipeline-cache",
        batch_size=args.workers,  # 批次大小等於並發數
        max_cache_gb=200
    )
    
    logger.info("\n步驟 2: 配置運行參數")
    if not args.yes:
        remote_path = input(f"請輸入百度網盤路徑 (預設: {args.path}): ").strip() or args.path
        
        # 默認全量，但允許用戶限制
        max_files_input = input(f"要處理多少個文件？(預設: 全部 - 流式處理): ").strip()
        max_files = int(max_files_input) if max_files_input else args.limit
        
        # 默認滿載
        max_workers_input = input(f"並發線程數？(預設: {args.workers} - 滿載模式): ").strip()
        max_workers = int(max_workers_input) if max_workers_input else args.workers
    else:
        remote_path = args.path
        max_files = args.limit
        max_workers = args.workers
    
    logger.info(f"\n步驟 3: 啟動流式處理")
    logger.info(f"- 遠程路徑: {remote_path}")
    logger.info(f"- 並發線程: {max_workers}")
    logger.info(f"- 數量限制: {max_files if max_files else '無限制'}")
    
    # 使用生成器獲取文件流
    file_generator = downloader.yield_baidu_files(remote_path)
    
    logger.info(f"\n🚀 啟動滿載模式: {max_workers} 線程並行處理 (流式輸入)...")
    
    # 運行管道
    processor.run(files=file_generator, max_files=max_files, max_workers=max_workers)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n用戶中斷，正在保存進度...")
    except Exception as e:
        logger.error(f"\n\n發生錯誤: {e}", exc_info=True)
