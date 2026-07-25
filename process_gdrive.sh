#!/bin/bash

export PATH="$HOME/.local/bin:$PATH"

echo "========================================"
echo "🚀 處理 Google Drive 電子書"
echo "使用 Gemini 2.5 flash-lite"
echo "========================================"
echo ""

cd /home/sms/ebook-converter

# 詢問處理數量
echo "選擇處理數量:"
echo "1. 測試 (5 個文件)"
echo "2. 小批量 (10 個文件)"
echo "3. 中批量 (20 個文件)"
echo "4. 大批量 (50 個文件)"
echo ""
read -p "請選擇 (1-4): " choice

case $choice in
    1) NUM=5 ;;
    2) NUM=10 ;;
    3) NUM=20 ;;
    4) NUM=50 ;;
    *) echo "無效選擇"; exit 1 ;;
esac

echo ""
echo "開始處理 Google Drive 的 $NUM 個文件..."
echo ""

# 運行處理器（只處理 Google Drive）
python3 << EOF
from unified_pipeline import UnifiedEbookPipeline
pipeline = UnifiedEbookPipeline()
pipeline.process_cloud_ebooks(max_files=$NUM, sources=['gdrive'])
EOF

echo ""
echo "========================================"
echo "處理完成！"
echo "========================================"
echo ""
echo "查看結果:"
echo "  ls -lh data/markdown-output/"
echo "  cat data/processing_stats.json | python3 -m json.tool"
echo ""
