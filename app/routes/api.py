from flask import Blueprint, request, jsonify

from app.services.file_reader import allowed_file, extract_text_from_upload
from app.utils.text_utils import normalize_text
from app.services.ai_client import classify_and_reply

api_bp = Blueprint("api", __name__)

@api_bp.post("/process")
def process_email():
    """
    Aceita:
    - JSON: { "text": "..." }
    OU
    - multipart/form-data:
        - file: arquivo .txt/.pdf
        - text: (opcional) texto manual
    Retorna:
    - { categoria, justificativa_curta, resposta, preview }
    """

    email_text = ""

    # 1) JSON
    if request.is_json:
        body = request.get_json(silent=True) or {}
        email_text = (body.get("text") or "").strip()

    # 2) form-data (texto)
    if not email_text:
        email_text = (request.form.get("text") or "").strip()

    # 3) form-data (arquivo)
    if "file" in request.files and request.files["file"]:
        f = request.files["file"]
        filename = f.filename or ""

        if not allowed_file(filename):
            return jsonify({"error": "Formato inválido. Use .txt ou .pdf"}), 400

        file_bytes = f.read()
        extracted = extract_text_from_upload(filename, file_bytes)
        if extracted:
            email_text = extracted.strip()

    email_text = normalize_text(email_text)

    if not email_text:
        return jsonify({"error": "Envie um texto ou um arquivo para processar."}), 400

    result = classify_and_reply(email_text)

    return jsonify({
        "categoria": result.get("categoria"),
        "justificativa_curta": result.get("justificativa_curta"),
        "resposta": result.get("resposta"),
        "preview": email_text[:400]
    })
