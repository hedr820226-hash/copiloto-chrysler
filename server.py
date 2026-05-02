from flask import Flask, request, jsonify, send_file
from datetime import datetime
from groq import Groq
import os

app = Flask(__name__)

# 🔑 API KEY desde variables de entorno (Render)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 🧠 FUNCIÓN PRINCIPAL
def generar_respuesta(texto):
    t = texto.lower()

    # ⚡ COMANDOS RÁPIDOS
    if "youtube" in t:
        return {
            "tipo": "accion",
            "mensaje": "Abriendo YouTube",
            "url": "https://youtube.com"
        }

    if "hora" in t:
        hora = datetime.now().strftime("%H:%M")
        return f"Son las {hora}. Mantente enfocado."

    if "gracias" in t:
        return "Siempre a tu servicio."

    # 🧠 IA REAL (modo copiloto / jarvis básico)
    try:
        chat = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente tipo Jarvis para conducción. Respondes claro, breve, natural y útil, como un copiloto en tiempo real."
                },
                {
                    "role": "user",
                    "content": texto
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=120
        )

        return chat.choices[0].message.content

    except Exception as e:
        print("ERROR IA:", e)
        return "Error procesando la solicitud."

# 🚀 API
@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json
    texto = data.get("code", "")

    respuesta = generar_respuesta(texto)

    # 🔁 Si es acción
    if isinstance(respuesta, dict):
        return jsonify({
            "respuesta": str(respuesta).replace("'", '"')
        })

    # 🔁 Texto normal
    return jsonify({
        "respuesta": respuesta
    })

# 🌐 HTML principal
@app.route('/')
def home():
    return send_file('copiloto_local.html')

# ▶️ INICIO (IMPORTANTE PARA RENDER)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
