from __future__ import annotations
from io import BytesIO
from pypdf import PdfReader

ALLOWED_EXTENSIONS = {"txt", "pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



def _cleanup_text(t: str) -> str:

    if not t:
        return ""

    t = t.replace("\r\n", "\n").replace("\r", "\n")

    t = t.replace("\ufeff", "")

    lines = [ln.strip() for ln in t.split("\n")]

    out = []
    empty_run = 0
    for ln in lines:
        if ln == "":
            empty_run += 1
            if empty_run <= 1:
                out.append("")
        else:
            empty_run = 0
            out.append(ln)

    return "\n".join(out).strip()


def _decode_text(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""

    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue

    # Último fallback: ignora erros
    return file_bytes.decode("latin-1", errors="ignore")


def read_txt(file_bytes: bytes) -> str:
    text = _decode_text(file_bytes)
    return _cleanup_text(text)



def _extract_page_text(page) -> str:
    try:
        txt = page.extract_text(extraction_mode="layout")  # type: ignore
        if txt and txt.strip():
            return txt
    except TypeError:
        pass
    except Exception:
        pass
    try:
        txt = page.extract_text()
        if txt and txt.strip():
            return txt
    except Exception:
        pass

    return ""


def _is_probably_scanned(extracted_text: str) -> bool:
    t = (extracted_text or "").strip()
    return len(t) < 80


def read_pdf(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""

    reader = PdfReader(BytesIO(file_bytes))
    texts = []

    for i, page in enumerate(reader.pages):
        page_text = _extract_page_text(page)
        if page_text:
            texts.append(f"[Página {i+1}]\n{page_text}")
        else:
            texts.append(f"[Página {i+1}]\n")  # mantém marcador de página

    full = _cleanup_text("\n\n".join(texts))

    if _is_probably_scanned(full):
        return _cleanup_text(
            "Não consegui extrair texto suficiente do PDF. "
            "Ele parece ser um PDF escaneado (imagem). "
            "Se você puder, envie o conteúdo em .txt, copie/cole o texto do e-mail, "
            "ou gere um PDF 'pesquisável' (exportado com texto)."
        )

    return full


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    ext = filename.rsplit(".", 1)[1].lower().strip()

    if ext == "txt":
        return read_txt(file_bytes)

    if ext == "pdf":
        return read_pdf(file_bytes)

    return ""
