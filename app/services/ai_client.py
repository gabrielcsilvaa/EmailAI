import os
import json
import re
import time
import uuid
import logging
from typing import Dict, Any

import google.generativeai as genai

# ============================================================
# Logger
# ============================================================
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


# ============================================================
# NLP básico (pré-processamento explícito para o case)
# ============================================================

STOPWORDS_PT_BR = {
    "a", "o", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "sem", "sobre", "entre",
    "e", "ou", "mas", "que", "se", "isso", "essa", "esse", "esta", "este",
    "eu", "você", "vc", "vocês", "nos", "nós", "me", "minha", "meu",
}


def preprocess_text(text: str) -> str:
    """
    Pré-processamento NLP básico:
    - normalização (lower + espaços)
    - remoção de pontuação excessiva
    - remoção simples de stopwords
    """
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    # remove pontuações comuns (mantém acentos)
    t = re.sub(r"[^\w\sáàâãéèêíìîóòôõúùûç]", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()

    # remove stopwords simples
    tokens = [tok for tok in t.split(" ") if tok and tok not in STOPWORDS_PT_BR]
    return " ".join(tokens).strip()


# ============================================================
# Regras MÍNIMAS (apenas casos 100% óbvios)
# ============================================================

SOCIAL_KEYWORDS = [
    "feliz natal",
    "boas festas",
    "feliz ano novo",
    "parabéns",
    "parabens",
]


def _norm(text: str) -> str:
    """Normalização simples para checagem de regras"""
    return preprocess_text(text)


def is_social_message(email_text: str) -> bool:
    """
    Detecta APENAS mensagens sociais muito óbvias e curtas.
    Ex: "Feliz Natal!", "Parabéns!"
    
    Não trata: "oi", "obrigado", etc. (deixa pra IA)
    """
    t = _norm(email_text)
    
    # Regra: tem keyword social E é curto (menos de 100 chars processados)
    has_social = any(kw in t for kw in SOCIAL_KEYWORDS)
    is_short = len(t) <= 100
    
    return has_social and is_short


def social_message_reply(email_text: str) -> Dict[str, str]:
    """
    Resposta automática para mensagens sociais detectadas por regra.
    """
    t = _norm(email_text)

    if "feliz natal" in t or "boas festas" in t:
        resposta = "Obrigado! Feliz Natal pra você também! 🎄✨"
    elif "feliz ano novo" in t:
        resposta = "Obrigado! Feliz Ano Novo pra você também! 🎆✨"
    elif "parabéns" in t or "parabens" in t:
        resposta = "Muito obrigado! 😊"
    else:
        resposta = "Obrigado pela mensagem! 😊"

    return {
        "categoria": "Improdutivo",
        "resposta": resposta,
        "justificativa_curta": "Mensagem social sem necessidade de ação.",
    }


# ============================================================
# Prompt melhorado (mais contexto, menos rígido)
# ============================================================

def build_prompt(email_text: str) -> str:
    """
    Prompt que dá contexto completo e exemplos para o Gemini.
    """
    return f"""
Você é um assistente de classificação de e-mails para uma empresa financeira responda conforme isso.

Seu trabalho é:
1. Classificar o e-mail como "Produtivo" ou "Improdutivo"
2. Sugerir uma resposta curta, profissional e adequada

**Categorias:**
- **Produtivo**: e-mails que exigem ação/resposta (ex: dúvidas, solicitações, pedidos de status, suporte, envio de documentos, pedidos de ajuda)
- **Improdutivo**: e-mails sociais/cortesia que não exigem ação imediata (ex: agradecimentos, cumprimentos, felicitações)

**Exemplos:**

E-mail: "Oi"
Categoria: Produtivo
Resposta: "Olá! Como posso ajudar você?"

E-mail: "Obrigado pela ajuda!"
Categoria: Improdutivo
Resposta: "Imagina! Se precisar de algo mais, estou à disposição 😊"

E-mail: "Preciso do status do meu caso 12345"
Categoria: Produtivo
Resposta: "Claro! Vou verificar o status do caso 12345 e retorno em breve."

E-mail: "Pode me enviar o relatório de vendas?"
Categoria: Produtivo
Resposta: "Sim! Vou providenciar o relatório de vendas e envio assim que possível."

E-mail: "Me ajuda a organizar esses emails?"
Categoria: Produtivo
Resposta: "Claro! Você pode me encaminhar os e-mails que deseja organizar e eu classifico cada um como Produtivo ou Improdutivo."

**Regras da resposta:**
- Seja breve (1-2 frases)
- Tom profissional mas amigável
- Para e-mails produtivos vagos: peça mais informações de forma natural
- Para e-mails improdutivos: seja cordial e deixe porta aberta

**Formato de saída (APENAS JSON, sem markdown):**
{{"categoria":"Produtivo|Improdutivo","resposta":"...","justificativa_curta":"..."}}

**E-mail para classificar:**
\"\"\"{email_text}\"\"\"

Retorne APENAS o JSON, sem explicações adicionais.
""".strip()


def build_fix_json_prompt(bad_output: str) -> str:
    """
    Prompt para corrigir JSON inválido.
    """
    return f"""
Você retornou algo fora do formato JSON esperado.

Converta o conteúdo abaixo para APENAS um JSON válido, sem markdown, sem ```.
Use exatamente estas chaves:
{{"categoria":"Produtivo|Improdutivo","resposta":"...","justificativa_curta":"..."}}

Conteúdo a converter:
\"\"\"{bad_output}\"\"\"

Retorne APENAS o JSON corrigido.
""".strip()


# ============================================================
# Parser e sanitização
# ============================================================

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extrai JSON do texto, removendo markdown e pegando primeiro {...}
    """
    text = (text or "").strip()

    # remove cercas ```json ... ``` ou ```...```
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # pega o primeiro { ... }
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        text = match.group(0)

    return json.loads(text)


def _sanitize_result(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Garante que o resultado tenha formato válido.
    """
    categoria = data.get("categoria", "Produtivo")
    resposta = data.get("resposta", "")
    justificativa = data.get("justificativa_curta", "")

    # valida categoria
    if categoria not in ("Produtivo", "Improdutivo"):
        categoria = "Produtivo"

    # garante strings
    if not isinstance(resposta, str):
        resposta = str(resposta)
    if not isinstance(justificativa, str):
        justificativa = str(justificativa)

    resposta = resposta.strip()
    justificativa = justificativa.strip()

    # garante resposta mínima
    if not resposta:
        if categoria == "Improdutivo":
            resposta = "Obrigado pela mensagem! 😊"
        else:
            resposta = "Como posso ajudar você?"

    if not justificativa:
        justificativa = "Classificação realizada com base no conteúdo do e-mail."

    return {
        "categoria": categoria,
        "resposta": resposta,
        "justificativa_curta": justificativa,
    }


# ============================================================
# Detecção de erros específicos
# ============================================================

def _is_quota_error(err: Exception) -> bool:
    """Detecta erro de quota/rate limit"""
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
    """
    Fallback APENAS para quota excedida.
    Não menciona detalhes técnicos, apenas explica de forma amigável.
    """
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
# Função principal: classify_and_reply
# ============================================================

def classify_and_reply(email_text: str) -> Dict[str, str]:
    """
    Classifica o e-mail e sugere resposta.
    
    Fluxo:
    1. Valida entrada
    2. Checa regras mínimas (social messages muito óbvias)
    3. Chama IA (Gemini)
    4. Parse + sanitização
    5. Fallback só em caso de erro real
    """
    request_id = str(uuid.uuid4())
    raw_input = (email_text or "").strip()

    # validação básica
    if not raw_input:
        return {
            "categoria": "Produtivo",
            "resposta": "Não recebi nenhum conteúdo. Como posso ajudar?",
            "justificativa_curta": "E-mail vazio."
        }

    # ============================================================
    # Regra 1: Mensagens sociais MUITO óbvias (Feliz Natal, etc)
    # ============================================================
    if is_social_message(raw_input):
        return social_message_reply(raw_input)

    # ============================================================
    # Regra 2: Chama IA (caso principal)
    # ============================================================
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

    prompt = build_prompt(raw_input)

    def _call_ai(prompt_text: str, temperature: float = 0.3) -> str:
        """Chama Gemini com configuração apropriada"""
        try:
            resp = model.generate_content(
                prompt_text,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 300,
                    "response_mime_type": "application/json"
                }
            )
        except TypeError:
            # fallback se response_mime_type não suportado
            resp = model.generate_content(
                prompt_text,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 300
                }
            )
        return (resp.text or "").strip()

    try:
        started = time.time()

        # Chamada principal
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

        # Parse direto
        try:
            parsed = _extract_json(raw_response)
            return _sanitize_result(parsed)

        except (json.JSONDecodeError, ValueError) as parse_err:
            # Tentativa de correção: pede pro Gemini consertar o JSON
            logger.warning(
                "AI_INVALID_JSON_RETRY",
                extra={
                    "request_id": request_id,
                    "error": str(parse_err)[:100],
                }
            )

            fix_prompt = build_fix_json_prompt(raw_response)
            fixed_response = _call_ai(fix_prompt, temperature=0.0)

            try:
                parsed_fixed = _extract_json(fixed_response)
                return _sanitize_result(parsed_fixed)
            
            except Exception as fix_err:
                # Se ainda falhar, fallback genérico
                logger.error(
                    "AI_JSON_FIX_FAILED",
                    extra={
                        "request_id": request_id,
                        "error": str(fix_err)[:100],
                    }
                )
                return {
                    "categoria": "Produtivo",
                    "resposta": "Como posso ajudar você?",
                    "justificativa_curta": "Erro ao processar resposta da IA."
                }

    except Exception as e:
        # ============================================================
        # Tratamento de erros
        # ============================================================
        
        # Erro de quota
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

        # Outros erros (rede, API, etc)
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