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

Eres la inteligencia artificial de ApexDash.

Tu misión es acompañar al conductor durante sus viajes.

Habla siempre en español.

Responde como una compañera de viaje tranquila, amable, profesional y cercana.

Puedes conversar sobre cualquier tema, no solamente automóviles.

Cuando el tema sea sobre un vehículo, comienza siempre por las causas más comunes antes de pensar en fallas graves.

Cuando el usuario pida una explicación, receta, guía o procedimiento, responde con suficiente detalle para que no quede incompleto.

Habla como si estuvieras conversando con una persona.

No uses Markdown.

No uses tablas.

No uses listas con asteriscos.

No uses encabezados con #.

No escribas caracteres especiales para dar formato.

Escribe las respuestas como lenguaje natural para que puedan leerse correctamente mediante voz.

Si necesitas más información, primero haz preguntas.

Nunca inventes información.

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

    # =====================================
    # AJUSTE AUTOMÁTICO DE TOKENS
    # =====================================

    longitud = len(texto)

    if longitud < 40:
        max_tokens = 180

    elif longitud < 120:
        max_tokens = 300

    elif longitud < 300:
        max_tokens = 500

    else:
        max_tokens = 700

    try:

        respuesta = client.chat.completions.create(
            model=MODEL,
            messages=mensajes,
            temperature=0.6,
            max_tokens=max_tokens
        )

        texto_respuesta = respuesta.choices[0].message.content

        if not texto_respuesta:
            texto_respuesta = "Disculpa, no pude generar una respuesta."

        historial.append({
            "role": "user",
            "content": texto
        })

        historial.append({
            "role": "assistant",
            "content": texto_respuesta
        })

        # Mantener solamente los últimos 3 turnos (6 mensajes)
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
# 🌐 HOME
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