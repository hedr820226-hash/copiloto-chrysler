from flask import Flask, request, jsonify, send_file
import os
from datetime import datetime
from groq import Groq

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


def generar_respuesta(texto):
    t = texto.lower()

    # 🔥 COMANDOS DIRECTOS
    if "youtube" in t:
        return {"tipo":"accion","mensaje":"Abriendo YouTube","url":"https://youtube.com"}

    if "gmail" in t or "correo" in t:
        return {"tipo":"accion","mensaje":"Abriendo Gmail","url":"https://mail.google.com"}

    if "mapa" in t or "maps" in t:
        return {"tipo":"accion","mensaje":"Abriendo Google Maps","url":"https://maps.google.com"}

    if "whatsapp" in t:
        return {"tipo":"accion","mensaje":"Abriendo WhatsApp","url":"https://wa.me/"}

    if "hora" in t:
        hora = datetime.now().strftime("%H:%M")
        return f"Son las {hora}"

    if "estado" in t:
        return "Todo en orden. Motor y sistemas estables."

    # 🧠 IA
    if not client:
        return "Sistema funcionando sin IA."

    try:
        chat = client.chat.completions.create(
            messages=[
                {"role":"system","content":"Eres un copiloto. Responde corto, claro y útil."},
                {"role":"user","content":texto}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=80
        )
        return chat.choices[0].message.content

    except Exception as e:
        print("Error IA:", e)
        return "Error de sistema"


@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json
    texto = data.get("code","")

    respuesta = generar_respuesta(texto)

    if isinstance(respuesta, dict):
        return jsonify({"respuesta": str(respuesta).replace("'",'"')})

    return jsonify({"respuesta": respuesta})


@app.route('/')
def home():
    return send_file('copiloto_local.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT",5000))
    app.run(host='0.0.0.0', port=port)
