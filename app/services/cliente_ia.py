import os
import json
import re
import time
import uuid
import logging
from typing import Dict, Any
from app.utils.Respostas import (
gerar_resposta_mensagem_social,gerar_resposta_trivial,gerar_resposta_spam,gerar_resposta_email_noreply, mensagem_social, mensagem_trivial, gerar_resposta_quota_excedida)
from app.services.prompt.prompt import construir_prompt_classificacao
import google.generativeai as genai

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

PALAVRAS_CHAVE_SPAM_FORTE = [
    "promoção", "promocao", "oferta", "desconto", "imperdível", "imperdivel",
    "compre", "comprar", "cupom", "frete grátis", "frete gratis",
    "clique aqui", "ganhe", "aproveite", "newsletter", "assinatura",
    "unsubscribe", "descadastrar", "descadastre", "remover inscrição", "remover inscricao",
    "marketing", "publicidade", "propaganda", "anúncio", "anuncio",
    "black friday", "liquidação", "liquidacao",
]

REGEX_URL = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)



def spam_forte(texto_email: str) -> bool:
    texto_bruto = (texto_email or "").strip()
    texto_minusculo = texto_bruto.lower()

    tem_url = bool(REGEX_URL.search(texto_bruto))

    contador_palavras_spam = 0
    for palavra_chave in PALAVRAS_CHAVE_SPAM_FORTE:
        if palavra_chave in texto_minusculo:
            contador_palavras_spam += 1

    if tem_url and contador_palavras_spam >= 1:
        return True
    if contador_palavras_spam >= 2:
        return True
    if "unsubscribe" in texto_minusculo or "descadastrar" in texto_minusculo or "remover inscr" in texto_minusculo:
        return True

    return False


REGEX_NOREPLY = re.compile(
    r"\b(no[-_.]?reply|donotreply|do[-_.]?not[-_.]?reply|noreply)\b",
    re.IGNORECASE
)


def email_noreply(texto_email: str) -> bool:
    return bool(REGEX_NOREPLY.search(texto_email))


def limitar_texto_para_ia(texto: str, maximo_caracteres: int = 6000) -> str:
    texto_limpo = (texto or "").strip()
    if len(texto_limpo) <= maximo_caracteres:
        return texto_limpo

    tamanho_inicio = int(maximo_caracteres * 0.7)
    tamanho_fim = maximo_caracteres - tamanho_inicio

    return (
        texto_limpo[:tamanho_inicio]
        + "\n\n[...trecho do e-mail truncado para análise...]\n\n"
        + texto_limpo[-tamanho_fim:]
    )



def construir_prompt_correcao_json(saida_invalida: str) -> str:
    return f"""
Reescreva o conteúdo abaixo como APENAS um JSON válido (sem texto antes ou depois).
Não use markdown, não use ```.

O JSON deve conter exatamente:
{{"categoria":"Produtivo|Improdutivo","resposta":"...","justificativa_curta":"..."}}

Conteúdo:
\"\"\"{saida_invalida}\"\"\"

Retorne SOMENTE o JSON.
""".strip()


def extrair_json_do_texto(texto: str) -> Dict[str, Any]:
    texto_limpo = (texto or "").strip()

    texto_limpo = re.sub(r"^```json\s*", "", texto_limpo)
    texto_limpo = re.sub(r"^```\s*", "", texto_limpo)
    texto_limpo = re.sub(r"\s*```$", "", texto_limpo)

    match = re.search(r"\{.*?\}", texto_limpo, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))

    inicio = texto_limpo.find("{")
    fim = texto_limpo.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        return json.loads(texto_limpo[inicio:fim+1])

    raise json.JSONDecodeError("No JSON object found", texto_limpo, 0)


def reparar_json_flexivel(texto: str) -> Dict[str, Any]:
    texto_limpo = (texto or "").strip()

    texto_limpo = re.sub(r"^```json\s*", "", texto_limpo)
    texto_limpo = re.sub(r"^```\s*", "", texto_limpo)
    texto_limpo = re.sub(r"\s*```$", "", texto_limpo)

    inicio = texto_limpo.find("{")
    fim = texto_limpo.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        texto_limpo = texto_limpo[inicio:fim+1]

    texto_limpo = texto_limpo.replace(""", '"').replace(""", '"').replace("'", "'")
    texto_limpo = re.sub(r",\s*([}\]])", r"\1", texto_limpo)

    try:
        return json.loads(texto_limpo)
    except Exception:
        pass

    texto_corrigido = re.sub(r"(?<=\{|,)\s*'([^']+)'\s*:", r'"\1":', texto_limpo)
    texto_corrigido = re.sub(r":\s*'([^']*)'\s*(?=[,}])", r': "\1"', texto_corrigido)
    texto_corrigido = re.sub(r",\s*([}\]])", r"\1", texto_corrigido)

    return json.loads(texto_corrigido)


def sanitizar_resultado_ia(dados: Dict[str, Any]) -> Dict[str, str]:
    categoria = dados.get("categoria", "Produtivo")
    resposta = dados.get("resposta", "")
    justificativa = dados.get("justificativa_curta", "")

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


def erro_de_quota(erro: Exception) -> bool:
    mensagem_erro = str(erro).lower()
    return (
        "429" in mensagem_erro
        or "resource_exhausted" in mensagem_erro
        or "quota" in mensagem_erro
        or "rate limit" in mensagem_erro
        or "too many requests" in mensagem_erro
        or "exceeded" in mensagem_erro
    )



def classificar_email_e_sugerir_resposta(texto_email: str) -> Dict[str, str]:
    id_requisicao = str(uuid.uuid4())
    texto_original = (texto_email or "").strip()

    if not texto_original:
        return {
            "categoria": "Improdutivo",
            "resposta": "Mensagem recebida.",
            "justificativa_curta": "Conteúdo vazio."
        }

    if mensagem_social(texto_original):
        return gerar_resposta_mensagem_social(texto_original)

    if mensagem_trivial(texto_original):
        return gerar_resposta_trivial()

    if spam_forte(texto_original):
        return gerar_resposta_spam()

    if email_noreply(texto_original):
        return gerar_resposta_email_noreply()

    chave_api = os.getenv("GEMINI_API_KEY", "")
    nome_modelo = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

    if not chave_api:
        return {
            "categoria": "Produtivo",
            "resposta": "Como posso ajudar você?",
            "justificativa_curta": "Sistema de IA não configurado."
        }

    genai.configure(api_key=chave_api)
    modelo = genai.GenerativeModel(nome_modelo)

    texto_para_ia = limitar_texto_para_ia(texto_original, maximo_caracteres=6000)
    prompt = construir_prompt_classificacao(texto_para_ia)

    def chamar_ia(texto_prompt: str, temperatura: float = 0.2) -> str:
        resposta = modelo.generate_content(
            texto_prompt,
            generation_config={
                "temperature": temperatura,
                "max_output_tokens": 800,
            }
        )
        return (getattr(resposta, "text", "") or "").strip()
    
    print("\n===== INPUT_TO_AI (preview) =====", flush=True)
    print(texto_para_ia[:1200], flush=True)
    print("===== /INPUT_TO_AI =====\n", flush=True)

    try:
        inicio = time.time()
        resposta_bruta = chamar_ia(prompt)

        tempo_decorrido_ms = int((time.time() - inicio) * 1000)
        logger.info(
            "AI_CALL_SUCCESS",
            extra={
                "request_id": id_requisicao,
                "model": nome_modelo,
                "text_len": len(texto_original),
                "elapsed_ms": tempo_decorrido_ms,
            }
        )

        try:
            dados_parseados = extrair_json_do_texto(resposta_bruta)
            resultado = sanitizar_resultado_ia(dados_parseados)
        except (json.JSONDecodeError, ValueError) as erro_parse:
            try:
                dados_reparados = reparar_json_flexivel(resposta_bruta)
                resultado = sanitizar_resultado_ia(dados_reparados)
            except Exception:
                logger.warning(
                    "AI_INVALID_JSON_RETRY",
                    extra={
                        "request_id": id_requisicao,
                        "error": str(erro_parse)[:120],
                    }
                )
                print("\n===== RAW_RESPONSE (preview) =====", flush=True)
                print(resposta_bruta[:2000], flush=True)
                print("===== /RAW_RESPONSE =====\n", flush=True)

                prompt_correcao = construir_prompt_correcao_json(resposta_bruta)
                resposta_corrigida = chamar_ia(prompt_correcao, temperatura=0.0)

                print("\n===== FIXED_RESPONSE (preview) =====", flush=True)
                print(resposta_corrigida[:2000], flush=True)
                print("===== /FIXED_RESPONSE =====\n", flush=True)

                try:
                    dados_corrigidos = extrair_json_do_texto(resposta_corrigida)
                    resultado = sanitizar_resultado_ia(dados_corrigidos)
                except Exception:
                    try:
                        dados_reparados_final = reparar_json_flexivel(resposta_corrigida)
                        resultado = sanitizar_resultado_ia(dados_reparados_final)
                    except Exception:
                        logger.error(
                            "AI_JSON_FIX_FAILED",
                            extra={
                                "request_id": id_requisicao,
                                "error": "Failed to parse/recover JSON after retry.",
                            }
                        )
                        return {
                            "categoria": "Produtivo",
                            "resposta": "Como posso ajudar você?",
                            "justificativa_curta": "Erro ao processar resposta da IA."
                        }

        if resultado.get("categoria") == "Produtivo":
            if spam_forte(texto_original) or mensagem_trivial(texto_original) or mensagem_social(texto_original):
                return {
                    "categoria": "Improdutivo",
                    "resposta": "Obrigado pela mensagem.",
                    "justificativa_curta": "Conteúdo sem necessidade de ação (social/trivial/spam)."
                }

        return resultado

    except Exception as erro:
        if erro_de_quota(erro):
            logger.warning(
                "AI_QUOTA_EXCEEDED",
                extra={
                    "request_id": id_requisicao,
                    "model": nome_modelo,
                    "error": str(erro)[:200],
                }
            )
            return gerar_resposta_quota_excedida()

        logger.error(
            "AI_CALL_ERROR",
            extra={
                "request_id": id_requisicao,
                "model": nome_modelo,
                "text_len": len(texto_original),
                "error_type": type(erro).__name__,
                "error": str(erro)[:200],
            }
        )

        return {
            "categoria": "Produtivo",
            "resposta": "Como posso ajudar você?",
            "justificativa_curta": f"Erro ao processar ({type(erro).__name__})."
        }