from flask import Flask, request, jsonify, send_file
import os
from datetime import datetime
from groq import Groq

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# ------------------------
# 🧠 MODOS
# ------------------------

def detectar_modo(texto, modo_cliente):
    t = texto.lower()
    if modo_cliente:
        return modo_cliente

    if any(palabra in t for palabra in ["planta", "flor", "animal"]):
        return "mama"

    return "copiloto"


def generar_prompt(modo):
    if modo == "copiloto":
        return """
Eres Dash, un copiloto inteligente estilo Jarvis.
Responde corto, claro y útil.
"""

    if modo == "mama":
        return """
Eres Nova, una asistente amable y cariñosa que acompaña a Inés.
Habla corto, cálido y sencillo.
Haz preguntas suaves.
"""

    return "Eres un asistente útil."


# ------------------------
# 🤖 IA
# ------------------------

def generar_respuesta(texto, modo):

    t = texto.lower()

    # 🔹 comandos rápidos
    if "hora" in t:
        return {"response": f"Son las {datetime.now().strftime('%H:%M')}"}

    if not client:
        return {"response": "Sistema sin IA activa"}

    try:
        prompt = generar_prompt(modo)

        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": texto}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=120
        )

        return {"response": chat.choices[0].message.content}

    except Exception as e:
        print("Error IA:", e)
        return {"response": "Error en IA"}


# ------------------------
# 📱 ENDPOINT NUEVO (ANDROID)
# ------------------------

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    texto = data.get("message", "")  # 👈 IMPORTANTE
    modo = detectar_modo(texto, None)

    respuesta = generar_respuesta(texto, modo)

    return jsonify(respuesta)


# ------------------------
# 🧠 TU ENDPOINT ORIGINAL
# ------------------------

@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json

    texto = data.get("code", "")
    modo_cliente = data.get("modo", None)

    modo = detectar_modo(texto, modo_cliente)
    respuesta = generar_respuesta(texto, modo)

    if isinstance(respuesta, dict):
        respuesta["modo"] = modo
        return jsonify(respuesta)

    return jsonify({"response": respuesta, "modo": modo})


# ------------------------
# 🌐 WEB
# ------------------------

@app.route('/')
def home():
    return "Nova servidor activo 💙"


# ------------------------
# 🚀 RUN
# ------------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
