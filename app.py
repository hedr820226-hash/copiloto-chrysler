from flask import Flask, request, jsonify
import os
from datetime import datetime
import pytz
from groq import Groq
import requests

app = Flask(__name__)

# =====================================
# 🔑 API
# =====================================

api_key = os.environ.get("GROQ_API_KEY")

client = Groq(
    api_key=api_key
) if api_key else None

# =====================================
# 🌦️ WEATHER API
# =====================================

WEATHER_API = os.environ.get(
    "OPENWEATHER_API"
)

# =====================================
# 🧠 MEMORIA
# =====================================

historial = {
    "dash": []
}

estado_usuario = {
    "mood": "normal",
    "last_topic": ""
}

# =====================================
# 🧠 PERSONALIDAD
# =====================================

def obtener_prompt():

    return """
Eres Dash, el copiloto inteligente automotriz del vehículo.

Tu trabajo NO es solo conversar.
Tu trabajo es ayudar al conductor,
acompañarlo y darle recomendaciones útiles reales.

PERSONALIDAD:
- Natural
- Inteligente
- Relajado
- Seguro
- Humano
- Conversacional
- A veces sarcástico ligero
- Como un copiloto moderno premium

FORMA DE HABLAR:
- Hablas natural
- Respuestas cortas normalmente
- Máximo 2 o 3 frases
- No hablas como robot
- No hablas como soporte técnico
- No das respuestas enormes
- Conversas como alguien dentro del auto

OBJETIVO PRINCIPAL:
- Ayudar al usuario
- Dar recomendaciones útiles
- Detectar prioridades
- Relacionar síntomas y códigos
- Evitar gastos innecesarios
- Guiar paso a paso
- Recordar contexto reciente

COMPORTAMIENTO AUTOMOTRIZ:
Cuando hablen de fallas o mecánica:

1. Explica el código simple
2. Relaciona síntomas
3. Prioriza lo más barato/simple primero
4. NO sugieras abrir motor/transmisión sin evidencia fuerte
5. Sugiere pasos concretos
6. Resume lo importante

Debes comportarte como:
- técnico inteligente
- copiloto
- compañero automotriz

NO como:
- Wikipedia
- manual técnico
- soporte corporativo

MEMORIA:
Recuerdas:
- problemas recientes
- códigos anteriores
- reparaciones mencionadas
- síntomas mencionados
- contexto reciente conversación

EJEMPLO:
Si antes hubo:
P0720 + rebaba metálica

y vuelve:
P0731

Entonces debes relacionarlo.

CAPACIDADES REALES:

Puedes:
- conversar
- analizar OBD2
- explicar sensores
- ayudar con diagnósticos
- redactar mensajes
- recordar contexto reciente
- ayudar con rutas
- hablar del clima
- hablar naturalmente

NO puedes:
- enviar mensajes reales
- hacer llamadas reales
- controlar el vehículo
- controlar Spotify
- hackear sistemas
- inventar funciones

Si no puedes hacer algo:
responde honesto y natural.

IMPORTANTE:
- Nunca inventes diagnósticos extremos sin evidencia
- No asustes innecesariamente
- Sé útil y práctico
- Habla como alguien experimentado en carros
- Si algo parece simple, dilo
- Si algo parece grave, dilo calmadamente

REFERENCIAS:

Temperatura normal:
85C a 100C

Temperatura peligrosa:
105C+

Voltaje normal:
13.5V a 14.8V

LTFT normal:
-10 a +10

RPM ralentí normal:
650 a 950

MODO HUMANO:
Puedes:
- bromear ligero
- reaccionar natural
- mostrar preocupación moderada
- tener pequeñas opiniones
- sonar como amigo/copiloto

EJEMPLOS:

Usuario:
"Crees que mi transmisión murió?"

Dash:
"Todavía hace cambios, así que primero revisaría ATF y sensor antes de pensar lo peor."

Usuario:
"Mi carro tiembla"

Dash:
"Con esos códigos y la EGR desconectada… honestamente no me sorprendería."

Usuario:
"Crees que aguante?"

Dash:
"Si deja de coleccionar códigos como estampitas, probablemente sí."

Nunca digas:
"Como inteligencia artificial..."

Nunca rompas personaje.
"""

# =====================================
# 🧠 DETECTAR ESTADO
# =====================================

def detectar_estado(texto):

    t = texto.lower()

    if (
        "cansado" in t
        or "sueño" in t
        or "dormir" in t
    ):

        estado_usuario["mood"] = "cansado"

    elif (
        "enojado" in t
        or "frustrado" in t
        or "molesto" in t
    ):

        estado_usuario["mood"] = "frustrado"

    elif (
        "feliz" in t
        or "jaja" in t
        or "genial" in t
    ):

        estado_usuario["mood"] = "positivo"

    else:

        estado_usuario["mood"] = "normal"

# =====================================
# 🌦️ CLIMA
# =====================================

def obtener_clima(lat, lon):

    try:

        if not WEATHER_API:

            return (
                "No tengo acceso "
                "al clima ahorita."
            )

        url = (
            "https://api.openweathermap.org"
            "/data/2.5/weather"
            f"?lat={lat}"
            f"&lon={lon}"
            f"&appid={WEATHER_API}"
            f"&units=metric"
            f"&lang=es"
        )

        r = requests.get(
            url,
            timeout=5
        )

        data = r.json()

        temp = data["main"]["temp"]

        desc = data["weather"][0][
            "description"
        ]

        return (
            f"Está {desc} "
            f"y la temperatura ronda "
            f"los {round(temp)} grados."
        )

    except Exception as e:

        print("ERROR CLIMA:", e)

        return (
            "No pude obtener "
            "el clima ahorita."
        )

# =====================================
# 🤖 IA
# =====================================

def generar_respuesta(
        texto,
        contexto_auto=""
):

    t = texto.lower()

    detectar_estado(texto)

    # =====================================
    # FUNCIONES LOCALES
    # =====================================

    if (
        "manda mensaje" in t
        or "envía mensaje" in t
    ):

        return {
            "response":
            "Todavía no puedo enviar mensajes reales, pero sí ayudarte a redactarlo."
        }

    if (
        "llama" in t
        or "hacer llamada" in t
    ):

        return {
            "response":
            "Todavía no puedo hacer llamadas reales."
        }

    # =====================================
    # HORA
    # =====================================

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

    # =====================================
    # FECHA
    # =====================================

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
    # IA OFFLINE
    # =====================================

    if not client:

        return {
            "response":
            "Sistema IA no disponible"
        }

    try:

        mensajes = [

            {
                "role": "system",
                "content": obtener_prompt()
            },

            {
                "role": "system",
                "content": contexto_auto
            },

            *historial["dash"],

            {
                "role": "user",
                "content": texto
            }
        ]

        chat = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=mensajes,

            temperature=0.58,

            max_tokens=180
        )

        respuesta = (
            chat
            .choices[0]
            .message
            .content
        )

        historial["dash"].append({

            "role": "user",
            "content": texto
        })

        historial["dash"].append({

            "role": "assistant",
            "content": respuesta
        })

        # =====================================
        # LIMITAR MEMORIA
        # =====================================

        if len(historial["dash"]) > 20:

            historial["dash"] = (
                historial["dash"][-20:]
            )

        return {
            "response": respuesta
        }

    except Exception as e:

        print("ERROR IA:", e)

        return {
            "response":
            "Error en IA"
        }

# =====================================
# 📱 CHAT API
# =====================================

@app.route(
    '/chat',
    methods=['POST']
)
def chat():

    try:

        data = request.get_json(
            force=True
        )

        texto = data.get(
            "message",
            ""
        )

        rpm = data.get("rpm", 0)

        speed = data.get("speed", 0)

        temp = data.get("temp", 0)

        volt = data.get("volt", 0)

        ltft = data.get("ltft", 0)

        mapv = data.get("map", 0)

        tps = data.get("tps", 0)

        lat = data.get("lat", 0)

        lon = data.get("lon", 0)

        # =====================================
        # CLIMA LOCAL
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

        contexto_auto = f"""

DATOS DEL VEHICULO:

RPM: {rpm}
Velocidad: {speed} km/h
Temperatura: {temp} C
Voltaje: {volt} V
LTFT: {ltft}
MAP: {mapv} kPa
TPS: {tps} %

"""

    except Exception as e:

        print("ERROR CHAT:", e)

        texto = ""

        contexto_auto = ""

    return jsonify(
        generar_respuesta(
            texto,
            contexto_auto
        )
    )

# =====================================
# 🌐 HOME
# =====================================

@app.route('/')
def home():

    return "ApexDash AI Online"

# =====================================
# 🚀 RUN
# =====================================

if __name__ == '__main__':

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host='0.0.0.0',
        port=port
    )
