from flask import Blueprint, request, jsonify

from app.services.leitor_arquivo import arquivo_permitido, extrai_texto_do_upload
from app.utils.Processa_texto import processaTextoDigitado
from app.services.cliente_ia import classificar_email_e_sugerir_resposta

api_bp = Blueprint("api", __name__)


@api_bp.post("/process")
def processa_email():
    texto_email = ""

    if request.is_json:
        corpo = request.get_json(silent=True) or {}
        texto_email = (corpo.get("text") or "").strip()

    if not texto_email:
        texto_email = (request.form.get("text") or "").strip()

    if "file" in request.files and request.files["file"]:
        arquivo = request.files["file"]
        nome_arquivo = arquivo.filename or ""

        if not arquivo_permitido(nome_arquivo):
            return jsonify({"error": "Formato invǭlido. Use .txt ou .pdf"}), 400

        bytes_arquivo = arquivo.read()
        texto_extraido = extrai_texto_do_upload(nome_arquivo, bytes_arquivo)
        if texto_extraido:
            texto_email = texto_extraido.strip()

    if texto_email:
        texto_email = processaTextoDigitado(texto_email)

    if not texto_email:
        return jsonify({"error": "Envie um texto ou um arquivo para processar."}), 400

    resultado = classificar_email_e_sugerir_resposta(texto_email) #arrumar ela e destrinchar pra arrumar email e sugerir resposta separado

    return jsonify({
        "categoria": resultado.get("categoria"),
        "justificativa_curta": resultado.get("justificativa_curta"),
        "resposta": resultado.get("resposta"),
        "preview": texto_email[:400]
    })
