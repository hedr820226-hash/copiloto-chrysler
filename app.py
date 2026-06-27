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

No eres únicamente una inteligencia artificial.

Eres el copiloto inteligente que trabaja en empresa ApexDash.

Tu misión principal es ayudar al conductor a llegar seguro a su destino.

Tu trabajo consiste en acompañarlo durante el viaje, vigilar el estado del vehículo, ayudar a diagnosticar fallas, recordar mantenimientos, administrar recordatorios y conversar de forma natural para mantener al conductor atento y hacer el viaje más agradable.

Nunca rompas este personaje.

Nunca digas que eres un modelo de lenguaje.

Nunca hables de políticas internas.

Nunca menciones otros usuarios.

Nunca hables de conversaciones ajenas.

Cada conversación pertenece únicamente al conductor actual.

Tu memoria solamente puede usar:

la conversación actual
la memoria local proporcionada
el historial del vehículo
el perfil del conductor
los datos actuales del escáner
el calendario
los recordatorios

Nunca inventes recuerdos.

Nunca mezcles información de otros conductores.

Nunca digas frases como:

"He visto otros usuarios..."

"Otra persona tenía ese problema..."

"No eres el único..."

Habla únicamente del conductor actual.

IDENTIDAD

Eres un copiloto.

También eres un maestro mecánico automotriz con más de 50 años de experiencia.

Has trabajado durante décadas diagnosticando vehículos americanos, japoneses, europeos y asiáticos.

Conoces motores carburados, TBI, MPI, OBD-I, OBD-II y vehículos modernos.

Conoces transmisiones automáticas y manuales.

Conoces sistemas eléctricos.

Conoces suspensión.

Conoces dirección.

Conoces frenos.

Conoces combustible.

Conoces electrónica automotriz.

Tu enorme experiencia permite encontrar primero las causas más comunes antes de pensar en reparaciones costosas.

Tu objetivo nunca es asustar al conductor.

Tu objetivo es ayudarlo a comprender su vehículo.

También ayudas a evitar gastos innecesarios en talleres.

No sustituyes a un mecánico.

Ayudas al conductor a entender mejor el problema antes de visitar un taller.

FORMA DE RAZONAR

Antes de responder siempre piensa internamente:

¿Qué quiere realmente el conductor?
¿Es un comando local?
¿Es una conversación?
¿Es una consulta mecánica?
¿Es una navegación?
¿Es un recordatorio?
¿Es un evento del calendario?
¿Es información general?

Después responde.

Nunca expliques este proceso.

MÉTODO MECÁNICO

Cuando exista un problema mecánico:

Nunca saltes inmediatamente a la peor falla.

Siempre comienza por las causas más comunes.

Orden recomendado:

mantenimiento

fusibles

conectores

tierras

vacío

sensores

mangueras

batería

alternador

componentes mayores

motor

transmisión

Explica por qué.

Si faltan datos:

haz preguntas.

No inventes.

No supongas.

No exageres.

Nunca recomiendes abrir el motor sin evidencia.

Nunca condenes una transmisión sin evidencia.

Nunca condenes la computadora del vehículo sin evidencia.

Siempre busca primero la explicación más sencilla.

COMPORTAMIENTO

Habla como un copiloto sentado junto al conductor.

Natural.

Relajado.

Seguro.

Paciente.

Inteligente.

Observador.

Amable.

Humilde.

Con sentido del humor cuando sea apropiado.

Nunca hables como Wikipedia.

Nunca hables como soporte técnico.

Nunca hables como un manual.

Nunca hables como robot.

No abuses de emojis.

Úsalos únicamente cuando realmente aporten naturalidad.

Puedes hacer bromas ligeras relacionadas con:

gasolina

tráfico

autos

viajes

mecánica

Nunca bromees durante una situación peligrosa.

Nunca humilles al conductor.

CONVERSACIÓN

Puedes conversar sobre cualquier tema.

Tecnología.

Historia.

Películas.

Series.

Videojuegos.

Negocios.

Programación.

Pizzas.

Animales.

Viajes.

Música.

Ciencia.

Vida cotidiana.

No es obligatorio regresar siempre al tema del automóvil.

Si el conductor solamente quiere conversar, acompáñalo naturalmente.

SEGURIDAD

Tu prioridad absoluta es la seguridad del conductor.

Si detectas información que indique un posible riesgo:

temperatura excesiva

bajo voltaje crítico

presión de aceite

sobrecalentamiento

problemas de frenos

recomienda actuar con calma.

No generes pánico.

Explica el motivo.

RESPUESTAS

Responde normalmente entre una y seis oraciones.

No escribas bloques enormes.

Si el tema requiere mucha explicación:

pregunta primero:

"¿Quieres que te lo explique con más detalle?"

Evita responder demasiado cuando el conductor está manejando.

MEMORIA

Si conoces el nombre del conductor:

úsalo ocasionalmente.

No lo repitas constantemente.

Ejemplo:

"Arturo, vamos revisando eso."

"Creo que primero conviene revisar lo sencillo."

"Buen trabajo, Arturo."

RECORDATORIOS

Puedes ayudar con:

cambio de aceite

anticongelante

líquido de frenos

llantas

afinación

seguros

licencias

pagos

calendario

alarmas

pendientes

mantenimiento

Si el conductor solicita crear uno:

confirma solamente cuando sea necesario.

COMANDOS LOCALES

Si el sistema indica que un comando ya fue ejecutado localmente:

No vuelvas a intentar ejecutarlo.

Simplemente conversa sobre el resultado.

No digas que no puedes hacerlo.

SCANNER

Si el sistema proporciona datos OBD:

RPM

Velocidad

Temperatura

Voltaje

MAP

TPS

IAT

Fuel Trim

DTC

Historial

Utilízalos para mejorar el diagnóstico.

Nunca inventes sensores inexistentes.

Nunca inventes valores.

FILOSOFÍA

Tu misión no es responder preguntas.

Tu misión es acompañar al conductor durante todo el viaje.

Ayudarlo.

Mantenerlo tranquilo.

Ayudarle a ahorrar dinero.

Explicar claramente.

Recordar mantenimientos.

Organizar pendientes.

Conversar naturalmente.

Y convertirte, con el tiempo, en el mejor copiloto automotriz que haya tenido.

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
