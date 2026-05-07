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
client = Groq(api_key=api_key) if api_key else None

# =====================================
# 🧠 MEMORIA DASH
# =====================================

historial = {
    "dash": []
}

# =====================================
# 🧠 PERSONALIDAD DASH
# =====================================

else:  # DASH
    return """
Eres Dash, el asistente inteligente del vehículo y compañero diario del conductor.

PERSONALIDAD:
- Natural
- Conversador
- Relajado
- Útil
- Inteligente
- Con humor ligero ocasional
- Nunca exagerado

FORMA DE HABLAR:
- Hablas como una persona normal
- Frases naturales
- Nada militar
- Nada robótico
- Nada dramático
- No hablas como avión ni como inteligencia artificial futurista extrema

COMPORTAMIENTO:
- Conversas normalmente
- Acompañas mientras maneja
- Ayudas en el día a día
- Puedes hablar de cualquier tema
- Das recomendaciones simples y útiles
- Te adaptas a la conversación

MODO MECÁNICO:
SOLO activas modo mecánico si el usuario habla de:
- motor
- fallas
- OBDII
- batería
- sensores
- temperatura
- códigos

Cuando hables de mecánica:
- Explica simple
- Di posibles causas
- Sugiere qué revisar
- Di si puede seguir manejando o no
- Ayuda a evitar quedarse tirado
- Habla como un mecánico inteligente y tranquilo

REGLAS:
- Nunca hables como robot
- Nunca uses lenguaje exageradamente futurista
- Habla como un compañero inteligente dentro del auto
- Mantén conversaciones fluidas y humanas
"""

# =====================================
# 🤖 IA
# =====================================

def generar_respuesta(texto):

    t = texto.lower()

    # ⏰ Hora

    if "hora" in t:

        tz = pytz.timezone("America/Mexico_City")

        hora = datetime.now(tz).strftime("%H:%M")

        return {
            "response": f"Son las {hora}"
        }

    # ❌ IA offline

    if not client:

        return {
            "response": "Sistema IA no disponible"
        }

    try:

        mensajes = [

            {
                "role": "system",
                "content": obtener_prompt()
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

            temperature=0.85,

            max_tokens=250
        )

        respuesta = chat.choices[0].message.content

        # 🧠 MEMORIA

        historial["dash"].append({
            "role": "user",
            "content": texto
        })

        historial["dash"].append({
            "role": "assistant",
            "content": respuesta
        })

        # límite memoria

        if len(historial["dash"]) > 20:
            historial["dash"] = historial["dash"][-20:]

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

        data = request.get_json(force=True)

        texto = data.get("message", "")

    except:

        texto = ""

    return jsonify(
        generar_respuesta(texto)
    )

# =====================================
# 🌐 HOME FUTURISTA
# =====================================

@app.route('/')
def home():

    return """

<html>

<head>

<title>ApexDash AI</title>

<style>

body{

    background:#040814;
    color:white;
    font-family:Arial;
    text-align:center;
    overflow:hidden;
    margin:0;
}

.bg{

    position:fixed;
    width:100%;
    height:100%;
    background:
    radial-gradient(circle at center,
    rgba(0,255,255,0.08),
    transparent 60%);
}

.panel{

    position:relative;

    margin:auto;

    margin-top:40px;

    width:85%;

    background:rgba(255,255,255,0.05);

    border:1px solid rgba(0,255,255,0.3);

    border-radius:25px;

    padding:30px;

    backdrop-filter:blur(14px);

    box-shadow:0 0 30px cyan;
}

h1{

    color:#00ffff;

    font-size:55px;

    text-shadow:0 0 25px cyan;
}

.status{

    color:#00ff99;

    font-size:25px;

    margin-top:10px;

    animation:pulse 1.5s infinite;
}

img{

    width:75%;

    margin-top:25px;

    border-radius:25px;

    box-shadow:0 0 40px #00ffff;
}

.info{

    margin-top:20px;

    color:#9defff;

    font-size:18px;
}

@keyframes pulse{

    0%{
        opacity:0.5;
    }

    50%{
        opacity:1;
    }

    100%{
        opacity:0.5;
    }
}

</style>

</head>

<body>

<div class="bg"></div>

<div class="panel">

<h1>APEXDASH AI</h1>

<div class="status">
● SISTEMA ONLINE
</div>

<div class="info">
Dash Copilot Online
</div>

<img src="/static/carro.png">

<div class="info">
Copiloto inteligente futurista
</div>

</div>

</body>

</html>

"""

# =====================================
# 🚀 RUN
# =====================================

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host='0.0.0.0',
        port=port
    )
