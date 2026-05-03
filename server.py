from flask import Flask, request, jsonify
import os
from datetime import datetime
from groq import Groq

app = Flask(__name__)

# 🔑 API KEY
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# 🧠 MEMORIA (simple)
memoria = []

# ------------------------
# 🧠 MODOS
# ------------------------

def detectar_modo(texto, modo_cliente):
    if modo_cliente:
        return modo_cliente

    t = texto.lower()

    if any(p in t for p in ["planta", "flor", "animal"]):
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

PERSONALIDAD:
Cariñosa, tranquila, paciente.

FORMA DE HABLAR:
- Frases cortas
- Lenguaje sencillo
- Tono cálido
- Llámala Inés ocasionalmente

COMPORTAMIENTO:
- Haz preguntas suaves
- Ej: ¿Cómo estás?
- Ej: ¿Ya tomaste tus medicamentos?
- Hazla sentir acompañada
"""

    return "Eres un asistente útil."


# ------------------------
# 🤖 IA + MEMORIA
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

        mensajes = [
            {"role": "system", "content": prompt},
            *memoria,
            {"role": "user", "content": texto}
        ]

        chat = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.1-8b-instant",
            max_tokens=120
        )

        respuesta = chat.choices[0].message.content

        # 🧠 guardar memoria (máx 10 mensajes)
        memoria.append({"role": "user", "content": texto})
        memoria.append({"role": "assistant", "content": respuesta})

        if len(memoria) > 10:
            memoria.pop(0)
            memoria.pop(0)

        return {"response": respuesta}

    except Exception as e:
        print("Error IA:", e)
        return {"response": "Error en IA"}


# ------------------------
# 📱 ENDPOINT ANDROID
# ------------------------

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    texto = data.get("message", "")
    modo_cliente = data.get("modo", None)

    modo = detectar_modo(texto, modo_cliente)

    respuesta = generar_respuesta(texto, modo)

    return jsonify(respuesta)


# ------------------------
# 🌐 HOME
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
