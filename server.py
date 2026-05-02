from flask import Flask, request, jsonify, send_file
from datetime import datetime
from groq import Groq
import os

app = Flask(__name__)

# Carga segura de la API Key
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def generar_respuesta(texto):
    if not client:
        return "Error: API Key no configurada en el servidor."
    
    t = texto.lower()

    # Comandos Rápidos
    if "youtube" in t:
        return {"tipo": "accion", "mensaje": "Abriendo YouTube", "url": "https://youtube.com"}
    if "hora" in t:
        return f"Son las {datetime.now().strftime('%H:%M')}. Mantente enfocado."
    if "gracias" in t:
        return "Siempre a tu servicio."

    # IA (Groq)
    try:
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres un asistente tipo Jarvis para conducción. Respondes claro, breve y natural."},
                {"role": "user", "content": texto}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=120
        )
        return chat.choices[0].message.content
    except Exception as e:
        print(f"Error IA: {e}")
        return "Error procesando la solicitud."

@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json
    texto = data.get("code", "") # Recibe 'code'
    respuesta = generar_respuesta(texto)
    return jsonify({"respuesta": respuesta})

@app.route('/')
def home():
    return send_file('copiloto_local.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
