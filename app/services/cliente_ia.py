import os
import json
import re
import time
import uuid
import logging
from typing import Dict, Any

import google.generativeai as genai


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

STOPWORDS_PT_BR = {
    "a", "o", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "sem", "sobre", "entre",
    "e", "ou", "mas", "que", "se", "isso", "essa", "esse", "esta", "este",
    "eu", "você", "vc", "vocês", "nos", "nós", "me", "minha", "meu",
}


def preprocess_text(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\sáàâãéèêíìîóòôõúùûç]", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()

    tokens = [tok for tok in t.split(" ") if tok and tok not in STOPWORDS_PT_BR]
    return " ".join(tokens).strip()


def _norm(text: str) -> str:
    return preprocess_text(text)

SOCIAL_KEYWORDS = [
    "feliz natal",
    "boas festas",
    "feliz ano novo",
    "parabéns",
    "parabens",
]

TRIVIAL_PATTERNS = [
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

SPAM_STRONG_KEYWORDS = [
    "promoção", "promocao", "oferta", "desconto", "imperdível", "imperdivel",
    "compre", "comprar", "cupom", "frete grátis", "frete gratis",
    "clique aqui", "ganhe", "aproveite", "newsletter", "assinatura",
    "unsubscribe", "descadastrar", "descadastre", "remover inscrição", "remover inscricao",
    "marketing", "publicidade", "propaganda", "anúncio", "anuncio",
    "black friday", "liquidação", "liquidacao",
]

URL_REGEX = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)


def is_social_message(email_text: str) -> bool:
    t = _norm(email_text)
    has_social = any(kw in t for kw in SOCIAL_KEYWORDS)
    is_short = len(t) <= 120
    return has_social and is_short


def social_message_reply(email_text: str) -> Dict[str, str]:
    t = _norm(email_text)

    if "feliz natal" in t or "boas festas" in t:
        resposta = "Obrigado pela mensagem! Feliz Natal pra você também! 🎄✨"
    elif "feliz ano novo" in t:
        resposta = "Obrigado pela mensagem! Feliz Ano Novo pra você também! 🎆✨"
    elif "parabéns" in t or "parabens" in t:
        resposta = "Muito obrigado! 😊"
    else:
        resposta = "Obrigado pela mensagem! 😊"

    return {
        "categoria": "Improdutivo",
        "resposta": resposta,
        "justificativa_curta": "Mensagem social sem necessidade de ação.",
    }


def is_trivial_message(email_text: str) -> bool:
    raw = (email_text or "").strip().lower()
    if not raw:
        return True

    # Se é literalmente só cumprimento/ok, pega pelos patterns
    for pat in TRIVIAL_PATTERNS:
        if re.match(pat, raw):
            return True

    # Heurística curta: poucas palavras e SEM sinais de contexto de trabalho
    # (evita marcar "status caso 123" como trivial)
    norm = _norm(raw)
    words = [w for w in norm.split() if w]
    if len(words) <= 2:
        # Se contém palavra de trabalho, NÃO é trivial
        work_hints = ["caso", "chamado", "status", "suporte", "erro", "problema", "documento", "contrato", "pagamento"]
        if any(h in norm for h in work_hints):
            return False
        return True

    return False


def is_strong_spam(email_text: str) -> bool:
    raw = (email_text or "").strip()
    t = raw.lower()

    has_url = bool(URL_REGEX.search(raw))

    hits = 0
    for kw in SPAM_STRONG_KEYWORDS:
        if kw in t:
            hits += 1

    if has_url and hits >= 1:
        return True
    if hits >= 2:
        return True
    if "unsubscribe" in t or "descadastrar" in t or "remover inscr" in t:
        return True

    return False

NOREPLY_REGEX = re.compile(
    r"\b(no[-_.]?reply|donotreply|do[-_.]?not[-_.]?reply|noreply)\b",
    re.IGNORECASE
)

def is_noreply_email(email_text: str) -> bool:
    return bool(NOREPLY_REGEX.search(email_text))


def spam_reply() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "resposta": "Obrigado pela mensagem.",
        "justificativa_curta": "Conteúdo com características de spam/propaganda, sem necessidade de ação.",
    }


def trivial_reply() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "resposta": "Olá! Se precisar de algo relacionado ao trabalho, fico à disposição.",
        "justificativa_curta": "Mensagem muito curta e sem contexto de trabalho.",
    }
    
def noreply_email_reply() -> Dict[str, str]:
    return {
        "categoria": "Improdutivo",
        "resposta": "Mensagem recebida. Este é um e-mail automático que não requer resposta.",
        "justificativa_curta": "E-mail automático identificado como 'no-reply', sem necessidade de resposta."
    }

def _limit_text_for_ai(text: str, max_chars: int = 6000) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t

    head = int(max_chars * 0.7)
    tail = max_chars - head

    return (
        t[:head]
        + "\n\n[...trecho do e-mail truncado para análise...]\n\n"
        + t[-tail:]
    )

def build_prompt(email_text: str) -> str:
    return f"""
Você é um assistente de classificação de e-mails para uma empresa do setor financeiro.

Tarefa:
1) Classificar o e-mail como "Produtivo" ou "Improdutivo"
2) Sugerir uma resposta curta, profissional e adequada

DEFINIÇÕES IMPORTANTES:
- Produtivo:
  - E-mails de TRABALHO que exigem ação ou resposta objetiva
  - Solicitações, dúvidas, pedidos de status, suporte, envio/validação de documentos, processos internos, assuntos da empresa

- Improdutivo:
  - Spam, propaganda, marketing, anúncios, newsletter
  - Mensagens sociais/cortesia sem ação imediata (felicitações, agradecimentos)
  - Cumprimentos genéricos ou vazios como: "oi", "olá", "bom dia", "ok"

EXEMPLOS:
E-mail: "Oi"
Categoria: Improdutivo
Resposta: "Olá! Se precisar de algo relacionado ao trabalho, fico à disposição."

E-mail: "Promoção imperdível! Clique aqui: http://..."
Categoria: Improdutivo
Resposta: "Obrigado pela mensagem."

E-mail: "Obrigado pela ajuda!"
Categoria: Improdutivo
Resposta: "Por nada! Se precisar de algo mais, fico à disposição."

E-mail: "Preciso do status do meu chamado 12345"
Categoria: Produtivo
Resposta: "Vou verificar o status do chamado 12345 e retorno em breve."

E-mail: "Pode me enviar o relatório de vendas?"
Categoria: Produtivo
Resposta: "Claro! Vou providenciar o relatório e envio assim que possível."

REGRAS DA RESPOSTA:
- 1 a 2 frases
- Tom profissional e amigável
- Não invente dados (se faltar informação, peça de forma objetiva)
- Retorne APENAS um JSON válido (sem texto antes ou depois, sem markdown)
- Não use blocos de código (não use ```)

FORMATO DE SAÍDA:
{{"categoria":"Produtivo|Improdutivo","resposta":"...","justificativa_curta":"..."}}

E-mail para classificar:
\"\"\"{email_text}\"\"\"

Retorne APENAS o JSON.
""".strip()


def build_fix_json_prompt(bad_output: str) -> str:
    return f"""
Reescreva o conteúdo abaixo como APENAS um JSON válido (sem texto antes ou depois).
Não use markdown, não use ```.

O JSON deve conter exatamente:
{{"categoria":"Produtivo|Improdutivo","resposta":"...","justificativa_curta":"..."}}

Conteúdo:
\"\"\"{bad_output}\"\"\"

Retorne SOMENTE o JSON.
""".strip()

# ============================================================
# Parser e sanitização
# ============================================================

def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()

    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    m = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if m:
        return json.loads(m.group(0))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end+1])

    raise json.JSONDecodeError("No JSON object found", text, 0)


def _repair_json_loose(text: str) -> Dict[str, Any]:
    t = (text or "").strip()

    t = re.sub(r"^```json\s*", "", t)
    t = re.sub(r"^```\s*", "", t)
    t = re.sub(r"\s*```$", "", t)

    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        t = t[start:end+1]

    t = t.replace("“", '"').replace("”", '"').replace("’", "'")
    t = re.sub(r",\s*([}\]])", r"\1", t)

    try:
        return json.loads(t)
    except Exception:
        pass

    t2 = re.sub(r"(?<=\{|,)\s*'([^']+)'\s*:", r'"\1":', t)
    t2 = re.sub(r":\s*'([^']*)'\s*(?=[,}])", r': "\1"', t2)
    t2 = re.sub(r",\s*([}\]])", r"\1", t2)

    return json.loads(t2)


def _sanitize_result(data: Dict[str, Any]) -> Dict[str, str]:
    categoria = data.get("categoria", "Produtivo")
    resposta = data.get("resposta", "")
    justificativa = data.get("justificativa_curta", "")

    if categoria not in ("Produtivo", "Improdutivo"):
        categoria = "Produtivo"

    if not isinstance(resposta, str):
        resposta = str(resposta)
    if not isinstance(justificativa, str):
        justificativa = str(justificativa)

    resposta = resposta.strip()
    justificativa = justificativa.strip()

    if not resposta:
        resposta = "Obrigado pela mensagem." if categoria == "Improdutivo" else "Como posso ajudar você?"
    if not justificativa:
        justificativa = "Classificação realizada com base no conteúdo do e-mail."

    return {
        "categoria": categoria,
        "resposta": resposta,
        "justificativa_curta": justificativa,
    }

# ============================================================
# Erros específicos
# ============================================================

def _is_quota_error(err: Exception) -> bool:
    msg = str(err).lower()
    return (
        "429" in msg
        or "resource_exhausted" in msg
        or "quota" in msg
        or "rate limit" in msg
        or "too many requests" in msg
        or "exceeded" in msg
    )


def _quota_fallback() -> Dict[str, str]:
    return {
        "categoria": "Produtivo",
        "resposta": (
            "No momento, o sistema está com alto volume de processamento. "
            "Pode me dar mais detalhes sobre o que você precisa? "
            "(ex: status de um caso, envio de documento, dúvida específica)"
        ),
        "justificativa_curta": "Sistema temporariamente indisponível (alto volume)."
    }

# ============================================================
# Função principal
# ============================================================

def classify_and_reply(email_text: str) -> Dict[str, str]:
    request_id = str(uuid.uuid4())
    raw_input = (email_text or "").strip()

    if not raw_input:
        return {
            "categoria": "Improdutivo",
            "resposta": "Mensagem recebida.",
            "justificativa_curta": "Conteúdo vazio."
        }

    # Micro-regras (só casos óbvios)
    if is_social_message(raw_input):
        return social_message_reply(raw_input)

    if is_trivial_message(raw_input):
        return trivial_reply()

    if is_strong_spam(raw_input):
        return spam_reply()
    # Micro-regra 4: E-mail automático (no-reply)
    if is_noreply_email(raw_input):
        return noreply_email_reply()


    api_key = os.getenv("GEMINI_API_KEY", "")
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

    if not api_key:
        return {
            "categoria": "Produtivo",
            "resposta": "Como posso ajudar você?",
            "justificativa_curta": "Sistema de IA não configurado."
        }

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    email_for_ai = _limit_text_for_ai(raw_input, max_chars=6000)
    prompt = build_prompt(email_for_ai)


    def _call_ai(prompt_text: str, temperature: float = 0.2) -> str:
        resp = model.generate_content(
            prompt_text,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 800,
            }
        )
        return (getattr(resp, "text", "") or "").strip()
    
    print("\n===== INPUT_TO_AI (preview) =====", flush=True)
    print(email_for_ai[:1200], flush=True)
    print("===== /INPUT_TO_AI =====\n", flush=True)

    
    try:
        started = time.time()
        raw_response = _call_ai(prompt)

        elapsed_ms = int((time.time() - started) * 1000)
        logger.info(
            "AI_CALL_SUCCESS",
            extra={
                "request_id": request_id,
                "model": model_name,
                "text_len": len(raw_input),
                "elapsed_ms": elapsed_ms,
            }
        )

        # 1) tenta parse direto
        try:
            parsed = _extract_json(raw_response)
            result = _sanitize_result(parsed)
        except (json.JSONDecodeError, ValueError) as parse_err:
            # 2) tenta reparar localmente
            try:
                repaired = _repair_json_loose(raw_response)
                result = _sanitize_result(repaired)
            except Exception:
                # 3) log + print do que veio
                logger.warning(
                    "AI_INVALID_JSON_RETRY",
                    extra={
                        "request_id": request_id,
                        "error": str(parse_err)[:120],
                    }
                )
                print("\n===== RAW_RESPONSE (preview) =====", flush=True)
                print(raw_response[:2000], flush=True)
                print("===== /RAW_RESPONSE =====\n", flush=True)

                # 4) tenta pedir pro Gemini corrigir
                fix_prompt = build_fix_json_prompt(raw_response)
                fixed_response = _call_ai(fix_prompt, temperature=0.0)

                # print do consertado também
                print("\n===== FIXED_RESPONSE (preview) =====", flush=True)
                print(fixed_response[:2000], flush=True)
                print("===== /FIXED_RESPONSE =====\n", flush=True)

                # tenta parse do consertado
                try:
                    parsed_fixed = _extract_json(fixed_response)
                    result = _sanitize_result(parsed_fixed)
                except Exception:
                    try:
                        repaired_fixed = _repair_json_loose(fixed_response)
                        result = _sanitize_result(repaired_fixed)
                    except Exception:
                        logger.error(
                            "AI_JSON_FIX_FAILED",
                            extra={
                                "request_id": request_id,
                                "error": "Failed to parse/recover JSON after retry.",
                            }
                        )
                        return {
                            "categoria": "Produtivo",
                            "resposta": "Como posso ajudar você?",
                            "justificativa_curta": "Erro ao processar resposta da IA."
                        }

        # Guard rail final (corrige casos óbvios)
        if result.get("categoria") == "Produtivo":
            if is_strong_spam(raw_input) or is_trivial_message(raw_input) or is_social_message(raw_input):
                return {
                    "categoria": "Improdutivo",
                    "resposta": "Obrigado pela mensagem.",
                    "justificativa_curta": "Conteúdo sem necessidade de ação (social/trivial/spam)."
                }

        return result

    except Exception as e:
        if _is_quota_error(e):
            logger.warning(
                "AI_QUOTA_EXCEEDED",
                extra={
                    "request_id": request_id,
                    "model": model_name,
                    "error": str(e)[:200],
                }
            )
            return _quota_fallback()

        logger.error(
            "AI_CALL_ERROR",
            extra={
                "request_id": request_id,
                "model": model_name,
                "text_len": len(raw_input),
                "error_type": type(e).__name__,
                "error": str(e)[:200],
            }
        )

        return {
            "categoria": "Produtivo",
            "resposta": "Como posso ajudar você?",
            "justificativa_curta": f"Erro ao processar ({type(e).__name__})."
        }
