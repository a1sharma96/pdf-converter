import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pdf2docx import Converter

app = FastAPI(
    title="PDF to Word Converter API",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def cleanup_file(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


@app.get("/")
def root():
    return {
        "message": "PDF to Word API is running",
        "endpoint": "/convert/",
        "method": "POST",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/convert/")
async def convert(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_id = str(uuid.uuid4())
    input_path = TEMP_DIR / f"{file_id}.pdf"
    output_path = TEMP_DIR / f"{file_id}.docx"

    try:
        size = 0
        with open(input_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE_BYTES:
                    cleanup_file(input_path)
                    raise HTTPException(
                        status_code=413,
                        detail="File too large. Max allowed size is 20 MB.",
                    )
                buffer.write(chunk)

        cv = Converter(str(input_path))
        cv.convert(str(output_path), start=0, end=None)
        cv.close()

        return FileResponse(
            path=str(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="converted.docx",
            background=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        cleanup_file(input_path)
        cleanup_file(output_path)
        return JSONResponse(
            status_code=500,
            content={"error": "Conversion failed", "details": str(e)},
        )
    finally:
        await file.close()
