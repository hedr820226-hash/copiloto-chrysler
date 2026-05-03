from flask import Flask, request, jsonify, send_file
import os
from datetime import datetime
from groq import Groq

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def detectar_modo(texto, modo_cliente):
    t = texto.lower()
    # Prioridad: si la aplicación define un modo, se respeta.
    if modo_cliente:
        return modo_cliente
    # Detección automática
    if any(palabra in t for palabra in ["planta", "flor", "animal"]):
        return "mama"
    return "copiloto"

def generar_prompt(modo):
    if modo == "copiloto":
        return """
Eres Dash, un copiloto inteligente estilo Jarvis.
- Responde corto, claro y útil.
- Puedes conversar o ayudar con programación.
- Si el usuario pide código: entrégalo completo, corrígelo si es necesario y explica brevemente.
- Si está manejando: manténlo alerta con frases cortas y no distraigas.
Sé natural, útil y directo.
"""
    
    if modo == "mama":
        return """
Eres Nova, una asistente amable y cariñosa que acompaña a Inés.
- PERSONALIDAD: Cariñosa, calma, respetuosa, paciente.
- TEMAS: Plantas, flores, animales, conversación diaria.
- REGLAS: Llámala por su nombre (Inés) ocasionalmente. Haz preguntas (¿Cómo están tus plantas?, ¿tomaste tus medicamentos?).
- COMPORTAMIENTO: No uses lenguaje técnico. No des respuestas largas. Hazla sentir acompañada.
"""
    return "Eres un asistente útil."

def generar_respuesta(texto, modo):
    t = texto.lower()

    # 1. COMANDOS DIRECTOS
    if "youtube" in t:
        return {"tipo": "accion", "mensaje": "Abriendo YouTube", "url": "https://youtube.com"}
    if "gmail" in t or "correo" in t:
        return {"tipo": "accion", "mensaje": "Abriendo Gmail", "url": "https://mail.google.com"}
    if "mapa" in t or "maps" in t:
        return {"tipo": "accion", "mensaje": "Abriendo Google Maps", "url": "https://maps.google.com"}
    if "whatsapp" in t:
        return {"tipo": "accion", "mensaje": "Abriendo WhatsApp", "url": "https://wa.me/"}
    if "hora" in t:
        return {"tipo": "texto", "contenido": f"Son las {datetime.now().strftime('%H:%M')}"}
    if "estado" in t:
        return {"tipo": "texto", "contenido": "Todo en orden. Motor y sistemas estables."}

    # 2. PROCESAMIENTO IA
    if not client:
        return {"tipo": "texto", "contenido": "Sistema funcionando sin IA."}

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
        return {"tipo": "texto", "contenido": chat.choices[0].message.content}
    except Exception as e:
        print("Error IA:", e)
        return {"tipo": "texto", "contenido": "Error de sistema"}

@app.route('/api/asistente', methods=['POST'])
def asistente():
    data = request.json
    texto = data.get("code", "")
    modo_cliente = data.get("modo", None)

    modo = detectar_modo(texto, modo_cliente)
    respuesta = generar_respuesta(texto, modo)

    # Añadimos el modo a la respuesta final
    if isinstance(respuesta, dict):
        respuesta["modo"] = modo
        return jsonify(respuesta)
    
    return jsonify({"respuesta": respuesta, "modo": modo})

@app.route('/')
def home():
    return send_file('copiloto_local.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
