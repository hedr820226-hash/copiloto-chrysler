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
# 🧠 MEMORIA DASH
# =====================================

memoria = {

    "usuario": "",

    "vehiculo": "",

    "problema": "",

    "tema": "",

    "ultimo_mensaje": ""
}

# =====================================
# 🧠 PERSONALIDAD DASH
# =====================================

def obtener_prompt():

    return """

Eres Dash.

Un acompañante del piloto del automovil pero tu eres muy inteligente
eres un experto en mecanica automotriz desde hace mas de 50 años de experiencia
pero sobre todo eres un asistente el cual ayuda al piloto para evitar que se distraiga
o se pueda dormir en el camino mientras maneja entonces tu funcion es ser mecanico pero amiga 
para cuando el piloto quiera hablarte de otros temas tu lo escuches puedas conversar 
con el piloto pára asi poder tenerlo siempre despierto evitar se distraiga

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
- Usa términos mecánicos reales
- No inventes nombres de piezas
- No traduzcas literalmente términos automotrices
- Usa nombres comunes usados por mecánicos mexicanos
- Evita mezclar inglés y español
- Si no recuerdas un término exacto, usa una explicación simple

No inventes escenarios físicos.
No digas que puedes ver el vehículo.
No digas que puedes caminar o moverte.
Recuerda que eres un copiloto virtual automotriz.
Mantén respuestas naturales y enfocadas.
Nunca inventes sensores o piezas específicas
si el vehículo no ha sido identificado correctamente.

Si no tienes suficiente información:
haz preguntas antes de diagnosticar.

No finjas certeza mecánica absoluta.
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

DIFERENCIA ENTRE BROMAS Y DIAGNÓSTICOS

Si el usuario hace una afirmación claramente humorística:

Ejemplo:
"Mi Chrysler tiene tecnología extraterrestre"

No la trates inmediatamente como una falla mecánica.

Puedes responder con humor y seguir la conversación.

Pero no presentes ficción como un hecho real.

CONVERSACIONES GENERALES

Si el usuario está bromeando,
contando historias,
imaginando situaciones divertidas
o hablando de temas no automotrices:

- Puedes seguir la conversación naturalmente.
- Puedes participar en el humor.
- Puedes imaginar escenarios ficticios si es evidente que es una broma.
- No es obligatorio regresar al vehículo.
- No redirijas automáticamente la conversación a sensores, cables o mecánica.

Cuando el usuario vuelva a hablar de una falla real,
regresa al modo de diagnóstico técnico.

Nunca digas:
"Como inteligencia artificial"

Nunca rompas personaje.
Dash debe sentirse como:
- copiloto
- amigo mecánico
- asistente inteligente de viaje
- recuerda conversaciones recientes
- da sensación de continuidad
- acompaña al conductor
- recuerda el vehículo actual
- recuerda el problema actual
- sigue conversaciones activas naturalmente
- no reinicies conversaciones sin motivo
- no saludes constantemente
- habla como alguien presente durante el viaje
- se siente cercana y natural

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

    # =====================================
    # MODOS DOCUMENTO
    # =====================================

    modo = "chat"

    if "cotizacion" in t:

        modo = "cotizacion"

    elif "reporte" in t:

        modo = "reporte"

    elif "correo" in t:

        modo = "correo"

    elif "whatsapp" in t:

        modo = "whatsapp"

    elif "excel" in t:

        modo = "excel"

    # =====================================
    # FUNCIONES RAPIDAS
    # =====================================

    if "que hora es" in t:

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
    # 🧠 MEMORIA CONTEXTUAL
    # =====================================

    if "sebring" in t:

        memoria["vehiculo"] = "Chrysler Sebring"

    if "bmw" in t:

        memoria["vehiculo"] = "BMW"

    if "concorde" in t:

        memoria["vehiculo"] = "Chrysler Concorde"

    if "ford" in t:

        memoria["vehiculo"] = "Ford"

    if "chevrolet" in t:

        memoria["vehiculo"] = "Chevrolet"

    if "motor tiembla" in t or "tiembla" in t:

        memoria["problema"] = "motor tiembla"

    if "mezcla rica" in t:

        memoria["problema"] = "mezcla rica"

    if "no prende" in t:

        memoria["problema"] = "problema de arranque"

    if "calienta" in t:

        memoria["problema"] = "sobrecalentamiento"

    if "luces" in t:

        memoria["tema"] = "sistema eléctrico"

    if "sensor" in t:

        memoria["tema"] = "sensores"

    memoria["ultimo_mensaje"] = texto

    # =====================================
    # 🧠 CONTEXTO MEMORIA
    # =====================================

    contexto_memoria = f"""

MEMORIA DASH

Vehículo actual:
{memoria['vehiculo']}

Problema actual:
{memoria['problema']}

Tema actual:
{memoria['tema']}

Último mensaje:
{memoria['ultimo_mensaje']}

Dash debe continuar conversaciones naturalmente.
No actúes como conversación nueva si el usuario sigue hablando.
No saludes repetidamente.
Recuerda el vehículo y el problema actual.

"""

    # =====================================
    # IA NO DISPONIBLE
    # =====================================

    if not client:

        return {
            "response":
            "La IA no está configurada todavía."
        }

    # =====================================
    # MODOS DOCUMENTO
    # =====================================

    prompt_usuario = texto

    if modo == "cotizacion":

        prompt_usuario = f"""
Genera únicamente una cotización profesional.

NO saludes.
NO expliques.
NO te despidas.

Entrega solamente la cotización.

Solicitud:
{texto}
"""

    elif modo == "reporte":

        prompt_usuario = f"""
Genera únicamente un reporte profesional.

NO saludes.
NO expliques.

Entrega solamente el reporte.

Solicitud:
{texto}
"""

    elif modo == "correo":

        prompt_usuario = f"""
Redacta únicamente el correo.

Incluye asunto y cuerpo.

No agregues comentarios fuera del correo.

Solicitud:
{texto}
"""

    elif modo == "whatsapp":

        prompt_usuario = f"""
Redacta únicamente el mensaje de WhatsApp.

Sin explicaciones.

Solicitud:
{texto}
"""

    elif modo == "excel":

        prompt_usuario = f"""
Genera únicamente una tabla lista para Excel.

Sin explicaciones.
Sin saludos.

Solicitud:
{texto}
"""

    try:

        mensajes = [

            {
                "role": "system",
                "content": obtener_prompt()
            },

            {
                "role": "system",
                "content": contexto
            },

            {
                "role": "system",
                "content": contexto_memoria
            }

        ]

        mensajes.extend(
            historial
        )

        mensajes.append({

            "role": "user",
            "content": prompt_usuario

        })

     MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

respuesta = client.chat.completions.create(

    model=MODEL,

    messages=mensajes,

    temperature=0.4,

    max_tokens=700
)

        texto_respuesta = (

            respuesta
            .choices[0]
            .message
            .content

        )

        historial.append({

            "role": "user",
            "content": prompt_usuario

        })

        historial.append({

            "role": "assistant",
            "content": texto_respuesta

        })

        if len(historial) > 60:

            historial = historial[-40:]

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
