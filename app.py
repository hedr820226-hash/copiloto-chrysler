from flask import Flask, request, jsonify, send_from_directory
import os
from groq import Groq

# =====================================
# 🚗 APP
# =====================================

app = Flask(__name__, static_folder=".")

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

    # Ajuste automático de tokens
    longitud = len(texto)

if longitud < 40:
    max_tokens = 180

elif longitud < 120:
    max_tokens = 300

elif longitud < 300:
    max_tokens = 500

else:
    max_tokens = 800

    try:

        respuesta = client.chat.completions.create(
            model=MODEL,
            messages=mensajes,
            temperature=0.4,
            max_tokens=max_tokens
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

        # Solo conservar los últimos 3 turnos
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

    return jsonify({
        "response": generar_respuesta(mensaje)
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
# 🌐 PÁGINA WEB
# =====================================

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# =====================================
# 📁 ARCHIVOS ESTÁTICOS
# =====================================

@app.route("/<path:archivo>")
def archivos(archivo):
    return send_from_directory(".", archivo)

# =====================================
# 🚀 RENDER
# =====================================

if __name__ == "__main__":

    puerto = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=puerto
    )