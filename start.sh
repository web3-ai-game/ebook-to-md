#!/bin/bash

echo "========================================"
echo "電子書轉 Markdown 轉換系統"
echo "使用 Gemini 2.0 Flash + 維根斯坦索引"
echo "========================================"
echo ""

cd /home/sms/ebook-converter

echo "1. 檢查 Docker 服務..."
if ! sudo systemctl is-active --quiet docker; then
    echo "   啟動 Docker..."
    sudo systemctl start docker
fi
echo "   ✓ Docker 運行中"

echo ""
echo "2. 構建容器（首次運行需要幾分鐘）..."
sudo docker-compose build

echo ""
echo "3. 啟動容器..."
sudo docker-compose up -d

echo ""
echo "4. 檢查容器狀態..."
sudo docker-compose ps

echo ""
echo "========================================"
echo "系統已就緒！"
echo "========================================"
echo ""
echo "使用方法："
echo ""
echo "方法一：進入容器運行完整管道"
echo "  sudo docker exec -it ebook-converter bash"
echo "  python3 run_pipeline.py"
echo ""
echo "方法二：處理本地文件"
echo "  sudo docker exec -it ebook-converter python3 main.py /baidu-source/book.pdf"
echo ""
echo "方法三：查看日誌"
echo "  sudo docker logs -f ebook-converter"
echo ""
echo "數據目錄："
echo "  - Markdown 輸出: ./data/markdown-output/"
echo "  - 索引文件: ./data/wittgenstein-index/"
echo "  - 百度緩存: ./data/baidu-cache/"
echo ""
echo "========================================"
