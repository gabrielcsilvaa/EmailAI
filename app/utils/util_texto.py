import re

def processaTextoDigitado(texto: str) -> str:
    texto = (texto or "").strip()
    texto = re.sub(r"\r\n", "\n", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto
