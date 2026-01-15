from __future__ import annotations
from io import BytesIO
from pypdf import PdfReader

ALLOWED_EXTENSIONS = {"txt", "pdf"}


def arquivo_permitido(nome_arquivo: str) -> bool:
    return "." in nome_arquivo and nome_arquivo.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



def limpar_texto(t: str) -> str:

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


def decodificar_texto(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""

    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue

    # Último fallback: ignora erros
    return file_bytes.decode("latin-1", errors="ignore")


def processaTxtImportado(file_bytes: bytes) -> str:
    text = decodificar_texto(file_bytes)
    return limpar_texto(text)



def extrair_texto_pagina(page) -> str:
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


def provavelmente_escaneado(texto_extraido: str) -> bool:
    t = (texto_extraido or "").strip()
    return len(t) < 80


def ProcessaPdfImportado(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""

    reader = PdfReader(BytesIO(file_bytes))
    texts = []

    for i, page in enumerate(reader.pages):
        page_text = extrair_texto_pagina(page)
        if page_text:
            texts.append(f"[Página {i+1}]\n{page_text}")
        else:
            texts.append(f"[Página {i+1}]\n")  # mantém marcador de página

    full = limpar_texto("\n\n".join(texts))

    if provavelmente_escaneado(full):
        return limpar_texto(
            "Não consegui extrair texto suficiente do PDF. "
            "Ele parece ser um PDF escaneado (imagem). "
            "Se você puder, envie o conteúdo em .txt, copie/cole o texto do e-mail, "
            "ou gere um PDF 'pesquisável' (exportado com texto)."
        )

    return full


def extrai_texto_do_upload(nome_arquivo: str, file_bytes: bytes) -> str:
    ext = nome_arquivo.rsplit(".", 1)[1].lower().strip()

    if ext == "txt":
        return processaTxtImportado(file_bytes)

    if ext == "pdf":
        return ProcessaPdfImportado(file_bytes)

    return ""
