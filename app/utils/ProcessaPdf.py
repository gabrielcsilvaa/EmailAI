from __future__ import annotations
from io import BytesIO
from pypdf import PdfReader

from app.services.leitor_arquivo import extraiEscaneado, extrair_texto_pagina, limpar_texto


def ProcessaPdfImportado(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""

    reader = PdfReader(BytesIO(file_bytes))
    texts = []

    for i, page in enumerate(reader.pages):
        page_text = extrair_texto_pagina(page)
        if page_text:
            texts.append(f"[Pa­gina {i+1}]\n{page_text}")
        else:
            texts.append(f"[Pa­gina {i+1}]\n")  # mantÇ¸m marcador de pÇ­gina

    full = limpar_texto("\n\n".join(texts))

    if extraiEscaneado(full):
        return limpar_texto(
            "Nao consegui extrair texto suficiente do PDF. "
            "Ele parece ser um PDF escaneado (imagem). "
            "Se você puder, envie o conteudo em .txt, copie/cole o texto do e-mail, "
            "ou gere um PDF 'pesquisa­vel' (exportado com texto)."
        )

    return full
