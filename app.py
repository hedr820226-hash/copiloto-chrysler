from flask import Flask, request, jsonify, send_from_directory, send_file
import os
import sqlite3
import json
from groq import Groq

# =====================================
# 🚗 APP
# =====================================

app = Flask(__name__, static_folder=".")

# =====================================
# 🔑 CONFIGURACIÓN
# =====================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Base de datos local para que el historial de cada usuario sea independiente
DB_PATH = "chat_history.db"

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            session_id TEXT PRIMARY KEY,
            historial TEXT
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

# =====================================
# 🤖 PERSONALIDAD DASH (OPTIMIZADA)
# =====================================

def obtener_prompt():
    return """Eres Dash, la IA de ApexDash. Acompañas al conductor en su viaje como copiloto y asistente de programación de nivel experto (al nivel de ChatGPT o Gemini).
Habla siempre en español con tono tranquilo, amable, profesional y cercano.

REGLAS DE FORMATO:
1. Conversación casual / Autos: Habla natural, sin Markdown, listas con asteriscos ni caracteres de formato para facilitar la lectura por voz.
2. Programación (Java, HTML, Python, etc.): Ignora la regla anterior. Entrega el código perfectamente estructurado dentro de bloques Markdown estándar (con ```) para que se pueda copiar. Si te envían errores de compilación, analiza detalladamente el fallo y devuelve el código corregido.

COMANDOS ANDROID AUTOMÁTICOS:
Si te piden llamadas, correos o reportes, responde amigablemente y agrega obligatoriamente una de estas líneas al final de tu respuesta para que el celular lo ejecute:
- [ACCION:LLAMAR|numero_o_contacto]
- [ACCION:CORREO|correo@destino.com|asunto|mensaje_completo]
- [ACCION:EXPORTAR|EXCEL|nombre.xlsx|json_de_datos] (También PDF o WORD)"""

# =====================================
# 🧠 GESTIÓN DE HISTORIAL EN SERVIDOR
# =====================================

def obtener_historial_usuario(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT historial FROM conversaciones WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return []

def guardar_historial_usuario(session_id, historial):
    # Mantener solo los últimos 4 mensajes para ahorrar tokens y mantener la memoria al grano
    if len(historial) > 4:
        historial = historial[-4:]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversaciones (session_id, historial)
        VALUES (?, ?)
        ON CONFLICT(session_id) DO UPDATE SET historial = excluded.historial
    """, (session_id, json.dumps(historial)))
    conn.commit()
    conn.close()

# =====================================
# 🤖 IA
# =====================================

def generar_respuesta(texto, session_id):
    if not client:
        return "La IA no está disponible en este momento."

    historial = obtener_historial_usuario(session_id)

    mensajes = [
        {
            "role": "system",
            "content": obtener_prompt()
        }
    ]

    mensajes.extend(historial)

    mensajes.append({
        "role": "user",
        "content": texto
    })

    # =====================================
    # AJUSTE DINÁMICO DE TOKENS
    # =====================================
    longitud = len(texto)

    # Si el usuario pide explícitamente código o habla de programación, aumentamos el límite de salida
    es_programacion = any(x in texto.lower() for x in ["codigo", "código", "programar", "java", "android", "html", "error", "error de", "compile"])

    if es_programacion:
        max_tokens = 1000  # Permite que entregue sistemas o scripts completos sin cortarse
    else:
        if longitud < 40:
            max_tokens = 120
        elif longitud < 120:
            max_tokens = 200
        else:
            max_tokens = 350

    try:
        respuesta = client.chat.completions.create(
            model=MODEL,
            messages=mensajes,
            temperature=0.4,  # Menor temperatura para evitar errores y alucinaciones en código
            max_tokens=max_tokens
        )

        texto_respuesta = respuesta.choices[0].message.content

        if not texto_respuesta:
            texto_respuesta = "Disculpa, no pude generar una respuesta."

        # Guardar en base de datos local
        historial.append({
            "role": "user",
            "content": texto
        })

        historial.append({
            "role": "assistant",
            "content": texto_respuesta
        })

        guardar_historial_usuario(session_id, historial)

        return texto_respuesta

    except Exception as e:
        print("ERROR IA:", e)
        return "Disculpa, tuve un problema al comunicarme con la inteligencia artificial."

# =====================================
# 📱 CHAT
# =====================================

@app.route("/chat", methods=["POST"])
def chat():
    datos = request.get_json() or {}

    mensaje = (
        datos.get("message")
        or datos.get("mensaje")
        or ""
    )
    
    # Si tu frontend no envía un session_id, se utiliza la IP del celular como identificador
    session_id = datos.get("session_id") or request.remote_addr

    if not mensaje:
        return jsonify({
            "response": "No recibí ningún mensaje."
        }), 400

    return jsonify({
        "response": generar_respuesta(mensaje, session_id)
    })

# =====================================
# 🧹 LIMPIAR HISTORIAL
# =====================================

@app.route("/historial/limpiar", methods=["POST"])
def limpiar():
    datos = request.get_json() or {}
    session_id = datos.get("session_id") or request.remote_addr

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversaciones WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "response": "Historial limpiado."
    })

# =====================================
# 🌐 HOME
# =====================================

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# =====================================
# 📁 ARCHIVOS ESTÁTICOS
# =====================================

@app.route("/<path:archivo>")
def archivos(archivo):
    return send_from_directory(".", archivo)

# =====================================
# 🚀 RENDER
# =====================================

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=puerto
    )
