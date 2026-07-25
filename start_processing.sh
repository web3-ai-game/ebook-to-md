#!/bin/bash

export PATH="$HOME/.local/bin:$PATH"

echo "========================================"
echo "🚀 電子書轉 Markdown 處理系統"
echo "========================================"
echo ""
echo "系統配置:"
echo "  - CPU: 4 vCPU"
echo "  - RAM: 16 GB"
echo "  - 模型: Gemini 1.5 Flash 8B (最快)"
echo "  - 並發: 3 個線程"
echo ""
echo "選擇處理模式:"
echo ""
echo "1. 測試模式 (處理 5 個文件)"
echo "2. 小批量 (處理 20 個文件)"
echo "3. 中批量 (處理 50 個文件)"
echo "4. 大批量 (處理 100 個文件)"
echo "5. 全部文件 (自動處理所有)"
echo "6. 自定義數量"
echo ""
read -p "請選擇 (1-6): " choice

cd /home/sms/ebook-converter

case $choice in
    1)
        NUM=5
        ;;
    2)
        NUM=20
        ;;
    3)
        NUM=50
        ;;
    4)
        NUM=100
        ;;
    5)
        NUM=""
        ;;
    6)
        read -p "輸入要處理的文件數量: " NUM
        ;;
    *)
        echo "無效的選擇"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "準備啟動..."
echo "========================================"
echo ""
echo "將在兩個終端窗口中運行:"
echo "  1. 處理進程 (當前窗口)"
echo "  2. 監控面板 (請在新終端運行)"
echo ""
echo "在新終端中執行以下命令查看實時監控:"
echo ""
echo "  cd /home/sms/ebook-converter"
echo "  python3 monitor_dashboard.py"
echo ""
read -p "按 Enter 開始處理..."

echo ""
echo "🚀 開始處理..."
echo ""

if [ -z "$NUM" ]; then
    python3 parallel_processor.py -w 3
else
    python3 parallel_processor.py -w 3 -n $NUM
fi

echo ""
echo "========================================"
echo "處理完成！"
echo "========================================"
echo ""
echo "查看結果:"
echo "  Markdown: data/markdown-output/"
echo "  索引: data/wittgenstein-index/"
echo ""
echo "查看統計:"
echo "  cat data/processing_stats.json | python3 -m json.tool"
echo ""
