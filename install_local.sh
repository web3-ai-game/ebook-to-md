#!/bin/bash

echo "========================================"
echo "本地安裝電子書轉換系統"
echo "========================================"

cd /home/sms/ebook-converter

echo "1. 安裝系統依賴..."
sudo apt-get update
sudo apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    libreoffice \
    pandoc \
    python3-pip

echo ""
echo "2. 安裝 Python 依賴..."
pip3 install --break-system-packages \
    google-generativeai \
    PyPDF2 \
    ebooklib \
    python-docx \
    beautifulsoup4 \
    markdown \
    boto3 \
    bypy \
    requests \
    tqdm \
    python-magic \
    Pillow \
    pdf2image \
    pytesseract \
    pymupdf

echo ""
echo "3. 創建數據目錄..."
mkdir -p data/{baidu-cache,markdown-output,wittgenstein-index}

echo ""
echo "4. 配置環境變量..."
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "========================================"
echo "✓ 安裝完成！"
echo "========================================"
echo ""
echo "測試系統:"
echo "  python3 test_converter.py"
echo ""
echo "運行管道:"
echo "  python3 run_pipeline.py"
echo ""
echo "處理單個文件:"
echo "  python3 main.py /path/to/book.pdf"
echo ""
