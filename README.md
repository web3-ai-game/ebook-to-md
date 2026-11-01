# ebook-to-md

[繁體中文](#zh) · [English](#en)

<a id="zh"></a>

## 繁體中文

把本機的 PDF、EPUB、MOBI、DOCX 轉成 Markdown。模型呼叫與 MongoDB 都是選用。公開副本可以不配任何金鑰就看流程。

### 免設定演示

```bash
python3 demo.py
# or
python3 main.py --demo
```

這會把一篇文件段範例寫到 `data/demo-output/sample.md`。不呼叫 xAI、Gemini、OpenRouter，不連 MongoDB，不讀雲端硬碟。

### 在自己的機器上跑

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

`.env` 只留在本機。路徑用相對目錄 `./data`，不要把家目錄寫進程式。PDF 文字由 PyMuPDF 提取。公開依賴下限已對齊目前的安全版本。

<a id="en"></a>

## English

Convert local PDF, EPUB, MOBI, and DOCX files to Markdown. Model calls and MongoDB are optional. The public copy runs a sample without any key.

### Demo without configuration

```bash
python3 demo.py
# or
python3 main.py --demo
```

It writes a documentation excerpt to `data/demo-output/sample.md`. It does not call xAI, Gemini, or OpenRouter. It does not connect to MongoDB or a cloud drive.

### On your own machine

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

Keep `.env` on the machine. Paths stay under `./data`. Do not hard-code a home directory. PDF text comes from PyMuPDF. Public dependency floors match the current patched releases.

## License

MIT. See [LICENSE](LICENSE) and [SECURITY.md](SECURITY.md).
