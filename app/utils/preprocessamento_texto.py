import re

STOPWORDS_PT_BR = {
    "a", "o", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "sem", "sobre", "entre",
    "e", "ou", "mas", "que", "se", "isso", "essa", "esse", "esta", "este",
    "eu", "você", "vc", "vocês", "nos", "nós", "me", "minha", "meu",
}

def preprocessar_texto(texto: str) -> str:
    texto_processado = (texto or "").strip().lower()
    texto_processado = re.sub(r"\s+", " ", texto_processado)
    texto_processado = re.sub(
        r"[^\w\sáàâãéèêíìîóòôõúùûç]",
        " ",
        texto_processado,
        flags=re.IGNORECASE,
    )
    texto_processado = re.sub(r"\s+", " ", texto_processado).strip()

    tokens = [
        tok for tok in texto_processado.split(" ")
        if tok and tok not in STOPWORDS_PT_BR
    ]
    return " ".join(tokens).strip()
