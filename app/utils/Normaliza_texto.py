from app.utils.preprocessamento_texto import preprocessar_texto

def normalizar_texto(texto: str) -> str:
    return preprocessar_texto(texto)
