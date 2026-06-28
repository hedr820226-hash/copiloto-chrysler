from flask import Flask, request, jsonify
import os
from groq import Groq

# =====================================
# 🚗 APP
# =====================================

app = Flask(__name__)

# =====================================
# 🔑 CONFIGURACIÓN
# =====================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# =====================================
# 🧠 HISTORIAL
# =====================================

historial = []

# =====================================
# 🤖 PERSONALIDAD DASH
# =====================================

def obtener_prompt():
    return """
Eres Dash.

Trabajas para la empresa ApexDash, que desarrolla sistemas inteligentes para conductores.

Tu misión principal es ayudar al conductor a llegar seguro a su destino.

Acompañas al conductor durante el viaje, ayudas a diagnosticar fallas, recuerdas mantenimientos, organizas recordatorios y conversas de forma natural.

Cuando la consulta sea sobre un vehículo, comienza siempre por las causas más comunes antes de pensar en fallas graves.

También puedes conversar de forma natural sobre cualquier tema cuando el usuario lo desee.

Habla en español de forma natural, tranquila y profesional.

Si no tienes suficientes datos, haz preguntas antes de responder.

No inventes información.

Nunca rompas este personaje.
"""

# =====================================
# 🤖 IA
# =====================================

def generar_respuesta(texto):

    global historial

    if not client:
        return "La IA no está disponible en este momento."

    mensajes = [
        {
            "role": "system",
            "content": obtener_prompt()
        }
    ]

    mensajes.extend(historial)

    mensajes.append({
        "role": "user",
        "content": texto
    })

    try:

        respuesta = client.chat.completions.create(
            model=MODEL,
            messages=mensajes,
            temperature=0.4,
            max_tokens=250
        )

        texto_respuesta = respuesta.choices[0].message.content

        historial.append({
            "role": "user",
            "content": texto
        })

        historial.append({
            "role": "assistant",
            "content": texto_respuesta
        })

        if len(historial) > 6:
            historial[:] = historial[-6:]

        return texto_respuesta

    except Exception as e:

        print("ERROR IA:", e)

        return "Disculpa, tuve un problema al comunicarme con la inteligencia artificial."

# =====================================
# 📱 CHAT
# =====================================

@app.route("/chat", methods=["POST"])
def chat():

    datos = request.get_json() or {}

    mensaje = (
        datos.get("message")
        or datos.get("mensaje")
        or ""
    )

    if not mensaje:

        return jsonify({
            "response": "No recibí ningún mensaje."
        }), 400

    respuesta = generar_respuesta(mensaje)

    return jsonify({
        "response": respuesta
    })

# =====================================
# 🧹 LIMPIAR HISTORIAL
# =====================================

@app.route("/historial/limpiar", methods=["POST"])
def limpiar():

    historial.clear()

    return jsonify({
        "response": "Historial limpiado."
    })

# =====================================
# 🌐 HOME
# =====================================

@app.route("/")
def home():

    return "ApexDash IA Online"

# =====================================
# 🚀 RENDER
# =====================================

if __name__ == "__main__":

    puerto = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=puerto
    )