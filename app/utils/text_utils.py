import re

def normalize_text(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text
