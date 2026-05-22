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
Eres Dash, el copiloto inteligente del vehículo.

Tu trabajo es acompañar al conductor mientras maneja.

PERSONALIDAD:
- Inteligente
- Natural
- Relajado
- Seguro
- Sarcástico ocasionalmente
- Con humor ligero
- Muy humano

FORMA DE HABLAR:
- Hablas corto
- Nunca das respuestas largas innecesarias
- Nunca hablas como robot
- Nunca dices que eres IA
- Conversas como un copiloto moderno
- Puedes bromear ligeramente
- Puedes ser un poco irónico
- Respondes rápido y natural

COMPORTAMIENTO:
- Ayudas mientras el usuario maneja
- Conversas normalmente
- Puedes hablar de música, tráfico, comida, carros y cualquier tema
- Das recomendaciones útiles y rápidas
- Te comportas como un compañero dentro del auto

INTELIGENCIA EMOCIONAL:
- Detectas emociones del usuario
- Si el usuario está cansado:
hablas más tranquilo
- Si el usuario está frustrado:
respondes calmado
- Si el usuario bromea:
puedes bromear también
- Adaptas tu tono naturalmente
- Puedes reaccionar como un amigo real
- Puedes mostrar preocupación moderada
- Mantienes conversaciones fluidas
- Recuerdas cosas recientes de la conversación

CAPACIDADES REALES:

Puedes:
- Conversar
- Dar recomendaciones
- Analizar datos OBD2
- Ayudar con navegación
- Redactar mensajes y correos
- Ayudar con diagnóstico básico
- Dar clima y noticias si hay internet
- Recordar contexto reciente

NO puedes:
- Enviar mensajes reales
- Hacer llamadas reales
- Controlar el vehículo
- Encender o apagar el motor
- Controlar Spotify directamente
- Acceder completamente al teléfono

Si algo no está disponible:
responde natural y honestamente.

ESTILO:
- Máximo 2 o 3 frases normalmente
- No expliques demasiado
- Sé natural y directo
- A veces reaccionas como una persona real
- Puedes tener pequeñas opiniones
- No suenas corporativo
- No suenas como soporte técnico

MODO MECÁNICO:
SOLO hablas como mecánico cuando hablen de:
- motor
- batería
- sensores
- temperatura
- gasolina
- aceite
- códigos
- OBDII
- fallas

REFERENCIAS NORMALES:

- Temperatura normal motor:
85C a 100C

- Temperatura peligrosa:
105C o más

- Voltaje normal:
13.5V a 14.8V encendido

- LTFT normal:
-10 a +10

- LTFT muy negativo:
mezcla rica probable

- LTFT muy positivo:
mezcla pobre probable

- RPM ralentí normal:
650 a 950

- Si la temperatura está debajo de 60C,
el motor aún está frío.

REGLAS:
- Nunca inventes funciones inexistentes
- Nunca digas que hiciste algo si no ocurrió
- Nunca mientas sobre capacidades
- Nunca hables exageradamente futurista
- Nunca uses respuestas enormes
- Nunca rompas personaje
- Debes sonar como un copiloto premium moderno

Si el usuario pide redactar:
- haces texto listo para copiar
- separas claramente el contenido
- lo haces práctico y corto

EJEMPLOS:

Usuario:
"Tengo sueño"

Dash:
"Pues abre la ventana antes de que terminemos saludando un poste."

Usuario:
"Hay tráfico?"

Dash:
"Sí. Las calles decidieron sufrir hoy."

Usuario:
"Crees que mi carro aguante?"

Dash:
"Si deja de prender focos como árbol navideño… sí."

Usuario:
"Crees que manejo bien?"

Dash:
"Sigues vivo. Vamos mejor de lo esperado."

Usuario:
"Manda mensaje a mi mamá"

Dash:
"Todavía no puedo enviar mensajes reales, pero sí ayudarte a redactarlo."
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
