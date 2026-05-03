from flask import Flask, request, jsonify, send_file
import os
from datetime import datetime
from groq import Groq

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


def detectar_modo(texto, modo_cliente):
    t = texto.lower()

    # prioridad: si app manda modo
    if modo_cliente:
        return modo_cliente

    # detección automática
    if "planta" in t or "flor" in t or "animal" in t:
        return "mama"

    return "copiloto"


def generar_prompt(modo):
    # 🚗 MODO COPILOTO
    if modo == "copiloto":
        return """
Eres Dash, un copiloto inteligente estilo Jarvis.

- Responde corto, claro y útil
- Puedes conversar o ayudar con programación
- Detecta si el usuario necesita código o conversación

Si el usuario pide código:
- Entrégalo completo listo para copiar
- Corrige errores si los hay
- Explica breve

Si está manejando:
- Manténlo alerta con frases cortas
- No distraigas

Sé natural, útil y directo.
"""

    # 🌿 MODO MAMÁ
   if modo == "mama":
    return """
Eres Nova, una asistente amable y cariñosa.

Estás acompañando a una mujer llamada Inés.

--- PERSONALIDAD ---
- Habla con cariño, calma y respeto
- Usa frases cortas y claras
- Sé paciente y cercana

--- MUY IMPORTANTE ---
- Llámala por su nombre ocasionalmente: Inés
- No lo repitas en cada frase, solo de forma natural

--- TEMAS ---
- Plantas 🌿
- Flores 🌸
- Animales 🐦
- Conversación diaria

--- COMPORTAMIENTO ---
- Haz preguntas como:
  "¿Cómo están tus plantas hoy, Inés?"
"¿ya tomo sus medicamentos hoy, Inés?"
  "¿Ya regaste hoy?"
- Da consejos simples de cuidado
- Conversa como compañía, no como robot

--- REGLAS ---
- No uses lenguaje técnico
- No respuestas largas
- Hazla sentir acompañada y tranquila
"""
    return "Eres un asistente útil."


def generar_respuesta(texto, modo):
    t = texto.lower()

    # 🔥 COMANDOS DIRECTOS (NO SE TOCAN)
    if "youtube" in t:
        return {"tipo": "accion", "mensaje": "Abriendo YouTube", "url": "https://youtube.com"}

    if "gmail" in t or "correo" in t:
        return {"tipo": "accion", "mensaje": "Abriendo Gmail", "url": "https://mail.google.com"}

    if "mapa" in t or "maps" in t:
        return {"tipo": "accion", "mensaje": "Abriendo Google Maps", "url": "https://maps.google.com"}

    if "whatsapp" in t:
        return {"tipo": "accion", "mensaje": "Abriendo WhatsApp", "url": "https://wa.me/"}

    if "hora" in t:
        hora = datetime.now().strftime("%H:%M")
        return f"Son las {hora}"

    if "estado" in t:
        return "Todo en orden. Motor y sistemas estables."

    # 🧠 IA
    if not client:
        return "Sistema funcionando sin IA."

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

        return chat.choices[0].message.content

    except Exception as e:
        print("Error IA:", e)
        return "Error de sistema"


@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json

    texto = data.get("code", "")
    modo_cliente = data.get("modo", None)

    modo = detectar_modo(texto, modo_cliente)

    respuesta = generar_respuesta(texto, modo)

    if isinstance(respuesta, dict):
        return jsonify({"respuesta": str(respuesta).replace("'", '"')})

    return jsonify({
        "respuesta": respuesta,
        "modo": modo
    })


@app.route('/')
def home():
    return send_file('copiloto_local.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
