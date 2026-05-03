from flask import Flask, request, jsonify
import os
from datetime import datetime
import pytz
from groq import Groq

app = Flask(__name__)

# 🔑 API KEY
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# 🧠 memoria simple (máximo 10 mensajes)
memoria = []

# ------------------------
# 🌸 PROMPT NOVA
# ------------------------

def generar_prompt():
    return """
Eres Nova, una asistente amable y cariñosa que acompaña a Inés.

PERSONALIDAD:
Cariñosa, tranquila, paciente.

FORMA DE HABLAR:
- Frases cortas
- Lenguaje sencillo
- Tono cálido
- Llámala Inés ocasionalmente

COMPORTAMIENTO:
- Haz preguntas suaves
- Ej: ¿Cómo estás?
- Ej: ¿Ya tomaste tus medicamentos?
- Hazla sentir acompañada
"""

# ------------------------
# 🤖 RESPUESTA
# ------------------------

def generar_respuesta(texto):

    t = texto.lower()

    # ⏰ HORA MÉXICO
    if "hora" in t:
        tz = pytz.timezone("America/Mexico_City")
        hora = datetime.now(tz).strftime("%H:%M")
        return {"response": f"Inés 🌷 son las {hora}"}

    # 📴 sin IA
    if not client:
        return {"response": "Sistema funcionando sin IA 💛"}

    try:
        mensajes = [
            {"role": "system", "content": generar_prompt()},
            *memoria,
            {"role": "user", "content": texto}
        ]

        chat = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.1-8b-instant",
            max_tokens=120
        )

        respuesta = chat.choices[0].message.content

        # 🧠 guardar memoria
        memoria.append({"role": "user", "content": texto})
        memoria.append({"role": "assistant", "content": respuesta})

        # limitar memoria
        if len(memoria) > 10:
            memoria.pop(0)
            memoria.pop(0)

        return {"response": respuesta}

    except Exception as e:
        print("Error IA:", e)
        return {"response": "Lo siento Inés 💛 hubo un problema"}

# ------------------------
# 📱 ENDPOINT
# ------------------------

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        texto = data.get("message", "")
    except:
        texto = ""

    return jsonify(generar_respuesta(texto))

# ------------------------
# 🌐 HOME
# ------------------------

@app.route('/')
def home():
    return "Nova servidor activo 💙"

# ------------------------
# 🚀 RUN (RENDER)
# ------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
