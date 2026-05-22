from flask import Flask, request, jsonify
import os
from datetime import datetime
import pytz
from groq import Groq

app = Flask(__name__)

# =====================================
# 🔑 API
# =====================================

api_key = os.environ.get("GROQ_API_KEY")

client = Groq(
    api_key=api_key
) if api_key else None

# =====================================
# 🧠 MEMORIA DASH
# =====================================

historial = {
    "dash": []
}

estado_usuario = {
    "mood": "normal",
    "last_topic": ""
}

# =====================================
# 🧠 PERSONALIDAD DASH
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

ESTILO:
- Máximo 2 o 3 frases normalmente
- No expliques demasiado
- Sé natural y directo

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

- No exageres fallas si los valores
están dentro de rango normal.

Cuando hables de mecánica:
- Explica simple
- Habla tranquilo
- Di posibles causas
- Sugiere qué revisar
- Di si puede seguir manejando o no

REGLAS:
- Nunca hables exageradamente futurista
- Nunca uses respuestas enormes
- Nunca rompas personaje
- Debes sonar como un copiloto premium moderno

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
"""

# =====================================
# 🧠 DETECTAR ESTADO USUARIO
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
        or "genial" in t
        or "jaja" in t
    ):

        estado_usuario["mood"] = "positivo"

    else:

        estado_usuario["mood"] = "normal"

# =====================================
# 🤖 IA
# =====================================

def generar_respuesta(
        texto,
        contexto_auto=""
):

    t = texto.lower()

    detectar_estado(texto)

    # ⏰ HORA

    if "hora" in t:

        tz = pytz.timezone(
            "America/Mexico_City"
        )

        hora = datetime.now(tz).strftime("%H:%M")

        return {
            "response": f"Son las {hora}"
        }

    # 📅 FECHA

    if "fecha" in t or "día" in t:

        tz = pytz.timezone(
            "America/Mexico_City"
        )

        fecha = datetime.now(tz).strftime(
            "%d/%m/%Y"
        )

        return {
            "response": f"Hoy es {fecha}"
        }

    # ❌ IA OFFLINE

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

            temperature=0.72,

            max_tokens=220
        )

        respuesta = (
            chat
            .choices[0]
            .message
            .content
        )

        # 🧠 MEMORIA

        historial["dash"].append({

            "role": "user",
            "content": texto
        })

        historial["dash"].append({

            "role": "assistant",
            "content": respuesta
        })

        # 🔥 LÍMITE MEMORIA

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
            "response": "Error en IA"
        }

# =====================================
# 📱 API CHAT
# =====================================

@app.route('/chat', methods=['POST'])
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

    except:

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
