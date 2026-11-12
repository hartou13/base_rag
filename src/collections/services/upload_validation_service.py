"""Upload validation: size, magic bytes, filename, and PDF safety checks. Pure functions, no I/O besides the upload."""
import io
import re
from pathlib import Path

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from src.rag.services import rag_config as cfg

_CHUNK = 1024 * 1024
_ALLOWED = {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/markdown"}


def safe_filename(name: str | None) -> str:
    """Strip any path part (POSIX or Windows style), control characters, and cap the length."""
    base = (name or "").replace("\\", "/").split("/")[-1]
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip().strip(".")
    if len(base) > 150:
        stem, ext = Path(base).stem, Path(base).suffix
        base = stem[: 150 - len(ext)] + ext
    return base or "file"


async def read_limited(upload: UploadFile, limit: int | None = None) -> bytes:
    """Read the upload in chunks and stop as soon as it exceeds the limit."""
    limit = limit or cfg.MAX_UPLOAD_BYTES
    buf = bytearray()
    while chunk := await upload.read(_CHUNK):
        buf.extend(chunk)
        if len(buf) > limit:
            raise HTTPException(status_code=413, detail=f"File too large (max {limit // (1024 * 1024)} MB)")
    return bytes(buf)


def _pdf_has_javascript(reader: PdfReader) -> bool:
    def is_js_action(action) -> bool:
        action = action.get_object() if action is not None else None
        return hasattr(action, "get") and (action.get("/S") == "/JavaScript" or "/JS" in action)

    root = reader.trailer["/Root"]
    if "/OpenAction" in root and is_js_action(root["/OpenAction"]):
        return True
    if "/AA" in root:
        return True
    names = root.get("/Names")
    if names is not None and "/JavaScript" in names.get_object():
        return True
    for page in reader.pages:
        if "/AA" in page:
            return True
        for annot in page.get("/Annots") or []:
            annot = annot.get_object()
            if "/AA" in annot or ("/A" in annot and is_js_action(annot["/A"])):
                return True
    return False


def validate_pdf(content: bytes) -> None:
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise HTTPException(status_code=422, detail="Encrypted PDFs are not accepted")
        if len(reader.pages) > cfg.MAX_PDF_PAGES:
            raise HTTPException(status_code=422, detail=f"PDF has too many pages (max {cfg.MAX_PDF_PAGES})")
        if _pdf_has_javascript(reader):
            raise HTTPException(status_code=422, detail="PDFs with embedded JavaScript are not accepted")
    except HTTPException:
        raise
    except Exception:  # pypdf raises many types on malformed input (PdfReadError, KeyError, ...)
        raise HTTPException(status_code=422, detail="The PDF is invalid or corrupted")


def validate_upload(filename: str | None, content: bytes) -> tuple[str, str]:
    """Check the content by its magic bytes (the extension is only a hint).
    Returns (safe_name, detected_content_type); raises HTTPException otherwise."""
    safe = safe_filename(filename)
    ext = Path(safe).suffix.lower()
    if ext not in _ALLOWED:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{ext}'. Supported: {sorted(_ALLOWED)}")
    if not content:
        raise HTTPException(status_code=422, detail="The file is empty")
    if content[:5] == b"%PDF-":
        detected = ".pdf"
    else:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            detected = None
        else:
            detected = None if b"\x00" in content else ".txt"  # text content; .md is text too
    if detected is None or (ext == ".pdf") != (detected == ".pdf"):
        raise HTTPException(status_code=415, detail="The file content does not match its extension")
    if detected == ".pdf":
        validate_pdf(content)
    return safe, _ALLOWED[ext]
