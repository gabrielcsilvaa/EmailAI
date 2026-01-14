from io import BytesIO
from pypdf import PdfReader

ALLOWED_EXTENSIONS = {"txt", "pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def read_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")

def read_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)

def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    ext = filename.rsplit(".", 1)[1].lower()
    if ext == "txt":
        return read_txt(file_bytes)
    if ext == "pdf":
        return read_pdf(file_bytes)
    return ""