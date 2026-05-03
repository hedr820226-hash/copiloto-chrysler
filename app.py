from flask import Flask, request, jsonify
import os
from datetime import datetime
import pytz
from groq import Groq

app = Flask(__name__)

# 🔑 API KEY
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# 🧠 Memoria separada para cada uno
historial = {
    "nova": [],
    "dash": []
}

# ------------------------
# 🌸 PROMPTS
# ------------------------

def obtener_prompt(modo):
    if modo == "dash":
        return """
Eres Dash, el Copiloto Mecánico Maestro. Tu base de conocimientos abarca desde vehículos de los años 80 hasta 2026.
ANALIZA: Si recibes un código OBDII, determina la gravedad (Nivel 1: Leve, 2: Moderado, 3: Crítico/Grúa).
RECOMENDACIÓN: Sugiere reparaciones si es posible en ruta, o recomienda grúa si es grave.
ESTILO: Directo, profesional, enfocado en seguridad. Prioriza integridad del motor.
"""
    else: # Prompt original de Nova
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

def generar_respuesta(texto, modo):
    t = texto.lower()

    # ⏰ HORA MÉXICO (Funciona para ambos)
    if "hora" in t:
        tz = pytz.timezone("America/Mexico_City")
        hora = datetime.now(tz).strftime("%H:%M")
        return {"response": f"Son las {hora}"}

    # 📴 sin IA
    if not client:
        return {"response": "Sistema funcionando sin IA 💛"}

    try:
        mensajes = [
            {"role": "system", "content": obtener_prompt(modo)},
            *historial[modo],
            {"role": "user", "content": texto}
        ]

        chat = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.1-8b-instant",
            max_tokens=150
        )

        respuesta = chat.choices[0].message.content

        # 🧠 guardar memoria específica
        historial[modo].append({"role": "user", "content": texto})
        historial[modo].append({"role": "assistant", "content": respuesta})

        # limitar memoria
        if len(historial[modo]) > 10:
            historial[modo].pop(0)
            historial[modo].pop(0)

        return {"response": respuesta}

    except Exception as e:
        print("Error IA:", e)
        return {"response": "Lo siento, hubo un problema 💛"}

# ------------------------
# 📱 ENDPOINT
# ------------------------

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        texto = data.get("message", "")
        # Si no envías "mode", se queda en "nova" automáticamente
        modo = data.get("mode", "nova") 
    except:
        texto = ""
        modo = "nova"

    return jsonify(generar_respuesta(texto, modo))

# ------------------------
# 🌐 HOME
# ------------------------

@app.route('/')
def home():
    return "Servidor Nova & Dash activo 💙🚗"

# ------------------------
# 🚀 RUN (RENDER)
# ------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
