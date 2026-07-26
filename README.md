[PUBLIC-READY]

# 电子书转 Markdown 流水线 / Ebook-to-Markdown Pipeline

多格式电子书批量转 Markdown 的个人工具链，LLM 智能转换 + 知识库索引，已实跑转换 5,153 份文档。
A personal batch pipeline that converts ebooks into Markdown using LLM-assisted parsing, with knowledge-base indexing — has processed 5,153 real documents in production use.

## 技术栈 / Stack

Python 3 + `requirements.txt`：`google-generativeai`、`PyPDF2`、`ebooklib`、`python-docx`、`beautifulsoup4`、`pymupdf`、`pdf2image` + `pytesseract`（OCR）、`boto3`/`bypy`（S3/百度网盘）。容器化：`Dockerfile` + `docker-compose.yml`。持久化：MongoDB。

Python 3 with the deps above; containerized via Docker Compose; MongoDB for persistence; LLM backends are X.AI Grok-3 (primary) with Gemini 2.0 Flash as fallback (`llm_converter.py`).

## 功能 / Features

- **格式支持**：PDF（文字提取 + 中英文 OCR）、EPUB/MOBI、TXT、DOCX、HTML（`ebook_extractor.py`）
- **LLM 转换**：X.AI Grok-3 → Gemini 2.0 Flash 自动降级，智能识别标题/段落/列表结构（`llm_converter.py`）
- **批量流水线**：多来源（百度网盘、Google Drive、本地目录），并行处理，断点续传（`pipeline_processor.py`、`multi_source_processor.py`、`parallel_processor.py`/`ultra_parallel_processor.py`）
- **知识索引**：维特根斯坦式命题结构提取，概念与关系映射，JSON 输出（`wittgenstein_indexer.py`）
- **存储后端**：MongoDB 持久化（`mongodb_handler.py`）+ S3/GCS 上传（`s3_uploader.py`）
- 另有大量辅助脚本：质量审计（`audit_quality.py`）、去重（`dedup_processor.py`）、书签抓取转换（`bookmark_converter.py`）、监控面板（`monitor_dashboard.py`）等

---

- **Formats**: PDF (text extraction + CN/EN OCR), EPUB/MOBI, TXT, DOCX, HTML (`ebook_extractor.py`)
- **LLM conversion**: X.AI Grok-3 with automatic fallback to Gemini 2.0 Flash; structure-aware heading/paragraph/list detection (`llm_converter.py`)
- **Batch pipeline**: multi-source (Baidu Netdisk, Google Drive, local), parallel workers, resumable (`pipeline_processor.py`, `multi_source_processor.py`, `parallel_processor.py`/`ultra_parallel_processor.py`)
- **Knowledge indexing**: Wittgenstein-style proposition extraction, concept/relation mapping, JSON output (`wittgenstein_indexer.py`)
- **Storage**: MongoDB persistence (`mongodb_handler.py`) + S3/GCS upload (`s3_uploader.py`)
- Plus a large set of utility scripts: quality audit (`audit_quality.py`), dedup (`dedup_processor.py`), bookmark scraping (`bookmark_converter.py`), monitoring dashboard (`monitor_dashboard.py`), and more

## 本地运行 / Getting started

```bash
pip install -r requirements.txt

# OCR 支持（可选）/ optional OCR support
apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra poppler-utils

cp .env.example .env   # 填入真实值 / fill in real values

python main.py /path/to/your/ebook.pdf
```

Docker 部署 / Docker deployment:
```bash
docker compose up -d
docker exec -it ebook-converter bash
```

## 环境变量 / Env

来自 `.env.example`，值均为占位符，真实值由 Doppler 注入：
Keys below are from `.env.example`; all values are placeholders — real values are injected via Doppler.

```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
GEMINI_API_KEY=
GEMINI_API_KEY_1=
GEMINI_API_KEY_2=
GEMINI_API_KEY_3=
XAI_API_KEY_1=
XAI_API_KEY_2=
MONGODB_URI=
```

## 完成度 / Status

能跑 — 个人生产工具，已处理 5,153 份文档、约 3.8GB Markdown 输出；脚本较多且部分为一次性/调试用途，尚未整理成规范化的公开工具包结构。
Working — a personal production tool that has processed 5,153 documents (~3.8GB of Markdown output); the script collection is large and includes one-off/debug utilities not yet organized into a clean public-package layout.
