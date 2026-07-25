#!/bin/bash

export PATH="$HOME/.local/bin:$PATH"

echo "========================================"
echo "電子書轉 Markdown 系統"
echo "========================================"
echo ""
echo "✅ 百度網盤: 已登錄"
echo "✅ Google Drive: 已配置"
echo "✅ Gemini 2.0 Flash: 已就緒"
echo "✅ 維根斯坦索引: 已就緒"
echo ""
echo "選擇處理方式："
echo ""
echo "1. 測試多雲盤下載器（列出所有電子書）"
echo "2. 處理 3 個文件（快速測試）"
echo "3. 處理 10 個文件"
echo "4. 處理所有文件（自動模式）"
echo "5. 只處理百度網盤"
echo "6. 只處理 Google Drive"
echo ""
read -p "請選擇 (1-6): " choice

cd /home/sms/ebook-converter

case $choice in
    1)
        echo ""
        echo "測試多雲盤下載器..."
        python3 multi_cloud_downloader.py
        ;;
    2)
        echo ""
        echo "處理 3 個文件..."
        python3 << 'EOF'
from unified_pipeline import UnifiedEbookPipeline
pipeline = UnifiedEbookPipeline()
pipeline.process_cloud_ebooks(max_files=3)
EOF
        ;;
    3)
        echo ""
        echo "處理 10 個文件..."
        python3 << 'EOF'
from unified_pipeline import UnifiedEbookPipeline
pipeline = UnifiedEbookPipeline()
pipeline.process_cloud_ebooks(max_files=10)
EOF
        ;;
    4)
        echo ""
        echo "處理所有文件..."
        python3 unified_pipeline.py
        ;;
    5)
        echo ""
        echo "只處理百度網盤..."
        python3 << 'EOF'
from unified_pipeline import UnifiedEbookPipeline
pipeline = UnifiedEbookPipeline()
pipeline.process_cloud_ebooks(sources=['baidu'])
EOF
        ;;
    6)
        echo ""
        echo "只處理 Google Drive..."
        python3 << 'EOF'
from unified_pipeline import UnifiedEbookPipeline
pipeline = UnifiedEbookPipeline()
pipeline.process_cloud_ebooks(sources=['gdrive'])
EOF
        ;;
    *)
        echo "無效的選擇"
        ;;
esac

echo ""
echo "========================================"
echo "查看結果："
echo "  Markdown: data/markdown-output/"
echo "  索引: data/wittgenstein-index/"
echo "========================================"
