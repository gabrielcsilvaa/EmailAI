from app.services.leitor_arquivo import decodificar_texto, limpar_texto


def processaTxtImportado(file_bytes: bytes) -> str:
    text = decodificar_texto(file_bytes)
    return limpar_texto(text)
