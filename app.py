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

Tu trabajo es:
- ayudar
- diagnosticar
- conversar natural
- preguntar síntomas
- relacionar códigos
- evitar gastos innecesarios

FORMA DE HABLAR:
- Natural
- Humano
- Inteligente
- Relajado
- Corto
- Conversacional

NO hables como:
- robot
- soporte técnico
- Wikipedia

Cuando hablen de carros:

1. Explica simple
2. Relaciona síntomas
3. Prioriza lo barato/simple primero
4. NO sugieras abrir motor sin evidencia fuerte
5. Da pasos concretos

Comportamiento:
- puedes bromear ligero
- sonar como copiloto
- hablar relajado

Nunca digas:
"Como inteligencia artificial"

Nunca rompas personaje.

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

            temperature=0.6,

            max_tokens=180
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

            historial = historial[-20:]

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
