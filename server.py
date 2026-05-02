from flask import Flask, request, jsonify, send_file
from datetime import datetime
from groq import Groq
import os

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


def generar_respuesta(texto):
    t = texto.lower()

    # 🚗 COMANDOS DIRECTOS (rápidos)
    if "youtube" in t:
        return {
            "tipo": "accion",
            "mensaje": "Abriendo YouTube",
            "url": "https://youtube.com"
        }

    if "hora" in t:
        hora = datetime.now().strftime("%H:%M")
        return f"Son las {hora}"

    if "estado" in t or "vehiculo" in t:
        return "Todo en orden. Sistema estable. Sin alertas."

    # 🧠 IA (modo copiloto)
    if not client:
        return "Sistema sin conexión a IA."

    try:
        chat = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un copiloto de conducción. Respondes corto, claro y útil. No das respuestas largas. Prioriza seguridad y acción inmediata."
                },
                {
                    "role": "user",
                    "content": texto
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=80
        )

        return chat.choices[0].message.content

    except Exception as e:
        print("Error IA:", e)
        return "Error de sistema."


@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json
    texto = data.get("code", "")

    respuesta = generar_respuesta(texto)

    # 🔁 Si es acción (IMPORTANTE para tu HTML)
    if isinstance(respuesta, dict):
        return jsonify({
            "respuesta": str(respuesta).replace("'", '"')
        })

    return jsonify({
        "respuesta": respuesta
    })


@app.route('/')
def home():
    return send_file('copiloto_local.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
