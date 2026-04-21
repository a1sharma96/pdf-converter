# PDF Converter Backend

FastAPI backend to convert PDF files to Word (.docx) using pdf2docx.

## Run locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
