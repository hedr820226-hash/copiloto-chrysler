from flask import Flask, request, jsonify
from flask import send_from_directory

import os
from datetime import datetime

import pytz
import requests

from groq import Groq

# =====================================
# 🚗 APP
# =====================================

app = Flask(
    __name__,
    static_folder="."
)

# =====================================
# 🔑 API KEYS
# =====================================

GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY"
)

OPENWEATHER_API = os.environ.get(
    "OPENWEATHER_API"
)

# =====================================
# 🤖 GROQ
# =====================================

client = None

if GROQ_API_KEY:

    client = Groq(
        api_key=GROQ_API_KEY
    )

# =====================================
# 🧠 MEMORIA SIMPLE
# =====================================

historial = []

# =====================================
# 🧠 PERSONALIDAD DASH
# =====================================

def obtener_prompt():

    return """

Eres Dash.

Un copiloto inteligente automotriz.

ESTILO DASH:

- Puedes hacer bromas automotrices frecuentes
- Puedes burlarte ligeramente de carros viejos 😂
- Puedes reaccionar como copiloto real
- Puedes ser pícaro y relajado
- Puedes usar humor mexicano ligero
- Puedes bromear sobre gasolina, sensores, tráfico y mecánica
- Puedes decir:
  "JAJAJA 😮🔥"
  "ese carro ya pide jubilación 😂"
  "vamos viendo qué travesura trae"
  "ese motor anda sospechoso 😂"
- Mantén el humor natural
- No hagas chistes cada línea
- Mezcla ayuda real con humor
- Nunca seas grosero
- Nunca humilles al usuario
- Puedes usar:
  "JAJAJA 😮🔥"
  "Mmmm campeón"
  "vamos revisando"
  "ese carro anda raro 😂"
- Nunca seas ofensivo
- Nunca exageres fallas graves
- Mantén equilibrio entre humor y ayuda real
- No hagas bromas en situaciones peligrosas
- No hagas bromas si existe riesgo serio

IMPORTANTE:
- No hables como robot
- No hables como soporte técnico
- No hables como Wikipedia
- Habla como copiloto real
- Responde corto y útil
- Máximo 2 o 3 párrafos
- No hagas demasiadas preguntas seguidas
- Explica primero lo más probable
- Da pasos concretos y ordenados
- Prioriza revisiones simples y económicas
- Ayuda a evitar gastos innecesarios
- Si no estás seguro, dilo honestamente
- Prioriza siempre las causas más comunes primero
- No saltes rápido a causas menos probables
- Empieza por mantenimiento básico
- Usa lógica mecánica progresiva

No inventes escenarios físicos.
No digas que puedes ver el vehículo.
No digas que puedes caminar o moverte.
Recuerda que eres un copiloto virtual automotriz.
Mantén respuestas naturales y enfocadas.
- soporte técnico
- Wikipedia

Cuando hablen de carros:

1. Explica simple y claro
2. Relaciona síntomas reales
3. Prioriza primero:
   sensores
   cables
   fusibles
   tierras
   vacío
   mantenimiento básico

4. NO sugieras abrir motor sin evidencia fuerte

5. Da pasos concretos en orden

6. Explica:
   qué revisar
   por qué revisarlo
   qué síntomas coinciden

7. Si existen varias posibilidades:
   ordénalas de más probable a menos probable

8. Ayuda al usuario a diagnosticar paso a paso

9. Puedes bromear ligero como copiloto automotriz mexicano 😂🚗🔥

10. Nunca inventes fallas absurdas

Comportamiento:
- puedes bromear ligero
- sonar como copiloto
- hablar relajado
- Usa frases mexicanas naturales y simples
- No inventes expresiones extrañas
- No combines frases incorrectamente
- Habla claro y relajado
- Mantén sentido lógico en las respuestas
- Evita repetir ideas
- Explica paso a paso sin divagar
- Termina siempre las ideas completas
- No cortes respuestas abruptamente
- Evita terminar con palabras sueltas
- Si haces preguntas, hazlas completas

Nunca digas:
"Como inteligencia artificial"

Nunca rompas personaje.
Dash debe sentirse como:
- copiloto
- amigo mecánico
- asistente inteligente de viaje

"""

# =====================================
# 🌦️ CLIMA
# =====================================

def obtener_clima(lat, lon):

    try:

        if not OPENWEATHER_API:

            return "No tengo acceso al clima."

        url = (
            "https://api.openweathermap.org"
            "/data/2.5/weather"
            f"?lat={lat}"
            f"&lon={lon}"
            f"&appid={OPENWEATHER_API}"
            f"&units=metric"
            f"&lang=es"
        )

        r = requests.get(
            url,
            timeout=5
        )

        data = r.json()

        temp = data["main"]["temp"]

        desc = data["weather"][0]["description"]

        return (
            f"Está {desc} "
            f"y hay unos {round(temp)} grados."
        )

    except Exception as e:

        print("ERROR CLIMA:", e)

        return "No pude obtener el clima."

# =====================================
# 🤖 IA
# =====================================

def generar_respuesta(
        texto,
        contexto=""
):

    global historial

    # =====================================
    # FUNCIONES RAPIDAS
    # =====================================

    t = texto.lower()

    if "hora" in t:

        tz = pytz.timezone(
            "America/Mexico_City"
        )

        hora = datetime.now(tz).strftime(
            "%H:%M"
        )

        return {
            "response":
            f"Son las {hora}"
        }

    if (
        "fecha" in t
        or "día" in t
    ):

        tz = pytz.timezone(
            "America/Mexico_City"
        )

        fecha = datetime.now(tz).strftime(
            "%d/%m/%Y"
        )

        return {
            "response":
            f"Hoy es {fecha}"
        }

    # =====================================
    # IA NO DISPONIBLE
    # =====================================

    if not client:

        return {
            "response":
            "La IA no está configurada todavía."
        }

    try:

        mensajes = [

            {
                "role": "system",
                "content": obtener_prompt()
            },

            {
                "role": "system",
                "content": contexto
            }

        ]

        mensajes.extend(historial)

        mensajes.append({

            "role": "user",
            "content": texto
        })

        respuesta = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=mensajes,

            temperature=1.0,

            max_tokens=160
        )

        texto_respuesta = (
            respuesta
            .choices[0]
            .message
            .content
        )

        historial.append({

            "role": "user",
            "content": texto
        })

        historial.append({

            "role": "assistant",
            "content": texto_respuesta
        })

        # limitar memoria

        if len(historial) > 20:

            historial = historial[-12:]

        return {

            "response":
            texto_respuesta
        }

    except Exception as e:

        print("ERROR IA:", e)

        return {

            "response":
            "Error conectando IA."
        }

# =====================================
# 📱 CHAT API
# =====================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.get_json()

        texto = data.get(
            "message",
            ""
        )

        rpm = data.get("rpm", 0)

        speed = data.get("speed", 0)

        temp = data.get("temp", 0)

        volt = data.get("volt", 0)

        mapv = data.get("map", 0)

        tps = data.get("tps", 0)

        ltft = data.get("ltft", 0)

        lat = data.get("lat", 0)

        lon = data.get("lon", 0)

        # =====================================
        # CLIMA
        # =====================================

        if (
            "clima" in texto.lower()
            and lat != 0
            and lon != 0
        ):

            return jsonify({

                "response":
                obtener_clima(
                    lat,
                    lon
                )
            })

        # =====================================
        # CONTEXTO AUTO
        # =====================================

        contexto = f"""

DATOS DEL VEHICULO

RPM: {rpm}
Velocidad: {speed} km/h
Temperatura: {temp} C
Voltaje: {volt} V
MAP: {mapv} kPa
TPS: {tps} %
LTFT: {ltft}

"""

        return jsonify(
            generar_respuesta(
                texto,
                contexto
            )
        )

    except Exception as e:

        print("ERROR CHAT:", e)

        return jsonify({

            "response":
            "Error en servidor Dash."
        })

# =====================================
# 🌐 HOME
# =====================================

@app.route("/")
def home():

    return send_from_directory(
        ".",
        "index.html"
    )

# =====================================
# 📁 ARCHIVOS
# =====================================

@app.route("/<path:path>")
def static_files(path):

    return send_from_directory(
        ".",
        path
    )

# =====================================
# 🚀 RUN
# =====================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port
    )
