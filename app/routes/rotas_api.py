from flask import Blueprint, request, jsonify

from app.services.leitor_arquivo import arquivo_permitido, extrai_texto_do_upload
from app.utils.Processa_texto import processaTextoDigitado
from app.services.cliente_ia import classificar_email_e_sugerir_resposta

api_bp = Blueprint("api", __name__)


@api_bp.post("/process")
def processa_email():
    texto_email = (
        (request.get_json(silent=True) or {}).get("text", "").strip()
        if request.is_json
        else (request.form.get("text") or "").strip()
    )

    arquivo = request.files.get("file")
    if arquivo and arquivo.filename:
        nome = arquivo.filename.strip()
        if not arquivo_permitido(nome):
            return jsonify({"error": "Formato invalido. Use .txt ou .pdf"}), 400

        texto_extraido = extrai_texto_do_upload(nome, arquivo.read())
        texto_email = texto_extraido.strip() if texto_extraido else texto_email

    if not texto_email:
        return jsonify({"error": "Envie um texto ou um arquivo para processar."}), 400

    texto_email = processaTextoDigitado(texto_email)
    resultado = classificar_email_e_sugerir_resposta(texto_email)

    return jsonify({
        "categoria": resultado.get("categoria"),
        "justificativa_curta": resultado.get("justificativa_curta"),
        "resposta": resultado.get("resposta"),
        "preview": texto_email[:400],
    })
