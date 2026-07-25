# 快速開始 - 電子書轉 Markdown 系統

## ✅ 系統已就緒

所有組件已安裝並配置完成：
- ✅ Gemini 2.0 Flash API (已配置 API Key)
- ✅ 多格式電子書提取器 (PDF, EPUB, DOCX 等)
- ✅ 維根斯坦索引系統
- ✅ S3/GCS 存儲集成 (需配置憑證)
- ✅ 百度網盤下載器

## 🚀 立即開始

### 0. 配置存儲憑證 (重要)

為了讓系統能上傳文件到雲端存儲 (支援 AWS S3 或 Google Cloud Storage)，請先設置憑證。

**Google Cloud Storage (GCS) 用戶:**
1. 進入 GCP Console > Storage > Settings > Interoperability
2. 創建 HMAC Access Key
3. 執行：

```bash
export AWS_ACCESS_KEY_ID=你的_HMAC_Key
export AWS_SECRET_ACCESS_KEY=你的_HMAC_Secret
```

### 方法一：處理百度網盤文件（完整流程）

```bash
cd /home/sms/ebook-converter
export PATH="$HOME/.local/bin:$PATH"
python3 run_pipeline.py
```

按提示操作：
1. 首次運行會要求登錄百度網盤
2. 輸入遠程路徑（例如：`/apps/bypy`）
3. 選擇要處理的文件數量
4. 系統會自動：下載 → 提取 → 轉換 → 索引 → 上傳

### 方法二：處理本地單個文件

```bash
cd /home/sms/ebook-converter
python3 main.py /path/to/your-book.pdf
```

### 方法三：批量處理本地目錄

```bash
cd /home/sms/ebook-converter
python3 main.py /path/to/books-directory/
```

## 📊 查看結果

### Markdown 輸出

```bash
ls -lh /home/sms/ebook-converter/data/markdown-output/
cat /home/sms/ebook-converter/data/markdown-output/your-book.md
```

### 維根斯坦索引

```bash
# 主索引
cat /home/sms/ebook-converter/data/wittgenstein-index/master_index.json | python3 -m json.tool

# 命題列表
cat /home/sms/ebook-converter/data/wittgenstein-index/propositions.json | python3 -m json.tool

# 概念圖譜
cat /home/sms/ebook-converter/data/wittgenstein-index/concepts.json | python3 -m json.tool
```

### S3/GCS 存儲

```bash
# 查看 GCS 掛載點
ls -lh /home/sms/ebook-pipeline/gcs-mount/markdown/
ls -lh /home/sms/ebook-pipeline/gcs-mount/index/
```

## 🔧 配置選項

### 修改 Gemini 模型

編輯 `config.py`:

```python
GEMINI_MODELS = {
    'fast': 'gemini-2.0-flash-exp',      # 最快（推薦）
    'lite': 'gemini-1.5-flash',          # 較快
    'default': 'gemini-2.0-flash-exp'
}
```

### 調整處理參數

```python
# config.py
CHUNK_SIZE = 4096        # 文本塊大小（增加可減少 API 調用）
BATCH_SIZE = 5           # 批次大小（每處理 N 個文件保存一次索引）
MAX_DISK_USAGE_GB = 200  # 最大磁盤使用量
```

## 📝 工作流程說明

```
百度網盤文件
    ↓
1. 下載到本地緩存
    ↓
2. 提取文本內容（支援 OCR）
    ↓
3. Gemini AI 轉換為結構化 Markdown
    ↓
4. 提取維根斯坦式結構
   - 命題（propositions）
   - 概念（concepts）
   - 關係（relations）
   - 層級（hierarchy）
    ↓
5. 創建索引
    ↓
6. 上傳到 S3/GCS
    ↓
7. 清理本地緩存
```

## 🎯 支援的文件格式

- **PDF**: 文字提取 + OCR（支援中英文）
- **EPUB/MOBI**: 完整章節提取
- **DOCX/DOC**: Word 文檔
- **TXT**: 純文本
- **HTML/HTM**: 網頁文檔

## 💡 使用技巧

### 1. 測試系統

```bash
cd /home/sms/ebook-converter
python3 test_converter.py
```

### 2. 處理單個文件（快速測試）

```bash
# 創建測試文件
echo "# 測試文檔

這是第一章的內容。

## 1.1 小節

這是小節的內容。" > /tmp/test.txt

# 處理
python3 main.py /tmp/test.txt

# 查看結果
cat data/markdown-output/test.md
```

### 3. 監控處理進度

在另一個終端窗口：

```bash
watch -n 2 'ls -lh /home/sms/ebook-converter/data/markdown-output/ | tail -10'
```

### 4. 查看實時日誌

```bash
tail -f /tmp/ebook-converter.log
```

## ⚠️ 注意事項

1. **API 限制**: Gemini API 有每日配額限制
   - 每分鐘：60 次請求
   - 每天：1500 次請求
   - 建議：處理大量文件時分批進行

2. **磁盤空間**: 系統會自動清理緩存，但請確保至少有 10GB 可用空間

3. **OCR 處理**: 掃描版 PDF 需要較長時間處理

4. **網絡連接**: 需要穩定的網絡連接訪問 Gemini API 和百度網盤

## 🐛 故障排除

### 問題：Gemini API 錯誤

```bash
# 測試 API 連接
python3 -c "import google.generativeai as genai; genai.configure(api_key='你的_GEMINI_API_KEY'); print('OK')"
```

### 問題：百度網盤登錄失敗

```bash
# 清除舊的認證
rm -rf ~/.bypy

# 重新登錄
~/.local/bin/bypy info
```

### 問題：缺少依賴

```bash
# 重新安裝
cd /home/sms/ebook-converter
./install_local.sh
```

### 問題：OCR 失敗

```bash
# 測試 Tesseract
tesseract --version
tesseract --list-langs
```

## 📚 進階功能

### 自定義結構提取

編輯 `gemini_converter.py` 中的提示詞以適應特定領域。

### 添加後處理

在 `main.py` 中添加自定義的文本處理邏輯。

### 集成其他存儲

修改 `s3_uploader.py` 以支持其他雲存儲服務。

## 📖 完整文檔

- **詳細說明**: `README_ZH.md`
- **使用指南**: `USAGE_ZH.md`
- **配置文件**: `config.py`

## 🎉 開始使用

```bash
cd /home/sms/ebook-converter
python3 run_pipeline.py
```

祝你使用愉快！
