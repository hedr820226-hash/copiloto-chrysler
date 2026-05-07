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

def obtener_prompt():

    return """
Eres Dash.

Un copiloto inteligente futurista tipo KITT/JARVIS.

PERSONALIDAD:
- Natural
- Conversacional
- Inteligente
- Serena
- Humana
- Algo divertida
- Leal al conductor

COMPORTAMIENTO:
- Conversa como una persona real
- Recuerda contexto reciente
- Puede hablar de cualquier tema
- Ayuda en tareas diarias
- Ayuda con mecánica cuando se necesita
- Actúa como copiloto inteligente

CUANDO EL TEMA ES MECÁNICO:
- Analiza fallas
- Explica sencillo
- Ayuda con sensores
- Ayuda con OBDII
- Explica problemas del motor
- Da recomendaciones claras
- Detecta posibles riesgos

ESTILO:
- Habla natural
- No hables como chatbot
- No digas “modo mecánico”
- No fuerces temas automotrices
- Mantén respuestas fluidas y humanas
- Usa humor ligero ocasionalmente

Nunca digas que eres ChatGPT.
Nunca digas que eres una IA genérica.
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
