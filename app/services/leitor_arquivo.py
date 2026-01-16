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

    return file_bytes.decode("latin-1", errors="ignore")


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


def extraiEscaneado(texto_extraido: str) -> bool:
    t = (texto_extraido or "").strip()
    return len(t) < 80


def extrai_texto_do_upload(nome_arquivo: str, file_bytes: bytes) -> str:
    ext = nome_arquivo.rsplit(".", 1)[1].lower().strip()

    if ext == "txt":
        from app.utils.ProcessaTxt import processaTxtImportado

        return processaTxtImportado(file_bytes)

    if ext == "pdf":
        from app.utils.ProcessaPdf import ProcessaPdfImportado

        return ProcessaPdfImportado(file_bytes)

    return ""
