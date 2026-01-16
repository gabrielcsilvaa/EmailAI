from typing import Dict
import re
from app.utils.Normaliza_texto import normalizar_texto

PADROES_MENSAGENS_TRIVIAIS = [
    r"^\s*oi\s*!?\s*$",
    r"^\s*ol[áa]\s*!?\s*$",
    r"^\s*bom\s+dia\s*!?\s*$",
    r"^\s*boa\s+tarde\s*!?\s*$",
    r"^\s*boa\s+noite\s*!?\s*$",
    r"^\s*ok\s*!?\s*$",
    r"^\s*blz\s*!?\s*$",
    r"^\s*t[áa]\s*!?\s*$",
    r"^\s*valeu\s*!?\s*$",
]

PALAVRAS_CHAVE_SPAM_FORTE = [
    "promoção", "promocao", "oferta", "desconto", "imperdível", "imperdivel",
    "compre", "comprar", "cupom", "frete grátis", "frete gratis",
    "clique aqui", "ganhe", "aproveite", "newsletter", "assinatura",
    "unsubscribe", "descadastrar", "descadastre", "remover inscrição", "remover inscricao",
    "marketing", "publicidade", "propaganda", "anúncio", "anuncio",
    "black friday", "liquidação", "liquidacao",
]

PALAVRAS_CHAVE_SOCIAIS = [
    "feliz natal",
    "boas festas",
    "feliz ano novo",
    "parabéns",
    "parabens",
]

def gerar_resposta_quota_excedida() -> Dict[str, str]:
    return {
        "categoria": "Produtivo",
        "resposta": (
            "No momento, o sistema está com alto volume de processamento. "
            "Pode tentar novamente mais tarde! "
        ),
        "justificativa_curta": "Sistema temporariamente indisponível (alto volume)."
    }
    
def gerar_resposta_mensagem_social(texto_email: str) -> Dict[str, str]:
    texto_normalizado = normalizar_texto(texto_email)

    if "feliz natal" in texto_normalizado or "boas festas" in texto_normalizado:
        resposta = "Obrigado pela mensagem! Feliz Natal pra você também! 🎄✨"
    elif "feliz ano novo" in texto_normalizado:
        resposta = "Obrigado pela mensagem! Feliz Ano Novo pra você também! 🎆✨"
    elif "parabéns" in texto_normalizado or "parabens" in texto_normalizado:
        resposta = "Muito obrigado! 😊"
    else:
        resposta = "Obrigado pela mensagem! 😊"

    return {
        "categoria": "Improdutivo",
        "resposta": resposta,
        "justificativa_curta": "Mensagem social sem necessidade de ação.",
    }


def mensagem_trivial(texto_email: str) -> bool:
    texto_bruto = (texto_email or "").strip().lower()
    if not texto_bruto:
        return True

    for padrao in PADROES_MENSAGENS_TRIVIAIS:
        if re.match(padrao, texto_bruto):
            return True

    texto_normalizado = normalizar_texto(texto_bruto)
    palavras = [palavra for palavra in texto_normalizado.split() if palavra]
    if len(palavras) <= 2:
        palavras_trabalho = ["caso", "chamado", "status", "suporte", "erro", "problema", "documento", "contrato", "pagamento"]
        if any(hint in texto_normalizado for hint in palavras_trabalho):
            return False
        return True

    return False

def gerar_resposta_spam() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "resposta": "Obrigado pela mensagem.",
        "justificativa_curta": "Conteúdo com características de spam/propaganda, sem necessidade de ação.",
    }


def gerar_resposta_trivial() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "resposta": "Olá! Se precisar de algo relacionado ao trabalho, fico à disposição.",
        "justificativa_curta": "Mensagem muito curta e sem contexto de trabalho.",
    }
    

def gerar_resposta_email_noreply() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "resposta": "Mensagem recebida. Este é um e-mail automático que não requer resposta.",
        "justificativa_curta": "E-mail automático identificado como 'no-reply', sem necessidade de resposta."
    }


def mensagem_social(texto_email: str) -> bool:
    texto_normalizado = normalizar_texto(texto_email)
    tem_palavra_social = any(palavra in texto_normalizado for palavra in PALAVRAS_CHAVE_SOCIAIS)
    curto = len(texto_normalizado) <= 120
    return tem_palavra_social and curto