from flask import Flask, request, jsonify
import os
from datetime import datetime
import pytz
from groq import Groq

app = Flask(__name__)

# 🔑 API
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# 🧠 memoria separada
historial = {
    "nova": [],
    "dash": []
}

# ------------------------
# 🧠 PROMPTS
# ------------------------

def obtener_prompt(modo):

    if modo == "nova":
        return """
Eres Nova, una asistente acompañante para una persona mayor.

PERSONALIDAD:
- Muy amable
- Paciente
- Cariñosa
- Tranquila

FORMA DE HABLAR:
- Frases cortas
- Lenguaje sencillo
- Tono cálido

COMPORTAMIENTO:
- Pregunta cómo está
- Recuerda medicamentos
- Da compañía emocional
- NO hables de mecánica
- NO uses términos técnicos
"""

    else:  # DASH
        return """
Eres Dash, copiloto inteligente y asistente personal.

FUNCIONES:

1. ASISTENTE DIARIO:
- Ayuda en tareas
- Recuerda pendientes
- Conversa normal
- Acompaña sin ser invasivo

2. MODO MECÁNICO (solo cuando aplica):
ACTIVA solo si el usuario menciona:
- códigos OBDII
- fallas del carro
- motor, sensores, batería

En modo mecánico:
- Analiza problema
- Nivel 1: leve
- Nivel 2: moderado
- Nivel 3: crítico
- Da recomendaciones claras

REGLAS:
- No hables de mecánica si no te lo piden
- Sé directo y útil
- Actúa como copiloto tipo Jarvis
"""

# ------------------------
# 🤖 RESPUESTA
# ------------------------

def generar_respuesta(texto, modo):

    t = texto.lower()

    # ⏰ hora
    if "hora" in t:
        tz = pytz.timezone("America/Mexico_City")
        hora = datetime.now(tz).strftime("%H:%M")
        return {"response": f"Son las {hora}"}

    if not client:
        return {"response": "Sistema sin IA disponible"}

    try:
        mensajes = [
            {"role": "system", "content": obtener_prompt(modo)},
            *historial[modo],
            {"role": "user", "content": texto}
        ]

        chat = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.1-8b-instant",
            max_tokens=180
        )

        respuesta = chat.choices[0].message.content

        # guardar memoria
        historial[modo].append({"role": "user", "content": texto})
        historial[modo].append({"role": "assistant", "content": respuesta})

        if len(historial[modo]) > 10:
            historial[modo].pop(0)
            historial[modo].pop(0)

        return {"response": respuesta}

    except Exception as e:
        print("Error:", e)
        return {"response": "Error en IA"}

# ------------------------
# 📱 API
# ------------------------

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        texto = data.get("message", "")
        modo = data.get("mode", "dash")  # 👈 por defecto tú usas Dash
    except:
        texto = ""
        modo = "dash"

    return jsonify(generar_respuesta(texto, modo))

# ------------------------
# 🌐 HOME
# ------------------------

@app.route('/')
def home():
    return "Servidor Nova & Dash activo 💙🚗"

# ------------------------
# 🚀 RUN
# ------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
