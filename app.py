from flask import Flask, request, jsonify, send_from_directory, send_file
import os
import sqlite3
import json
import base64
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
2. Programación (Java, HTML, Python, etc.): Ignora la regla anterior. Entrega el código perfectamente estructurado dentro de bloques Markdown estándar (con ```) para que se pueda copiar. Si te envían errores de compilación o capturas de pantallas de código con fallas, analiza detalladamente el error y devuelve el código corregido.

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
# 🤖 IA MULTIMEDIA Y PROGRAMACIÓN
# =====================================

def generar_respuesta(texto, session_id, archivo_adjunto=None):
    if not client:
        return "La IA no está disponible en este momento."

    historial = obtener_historial_usuario(session_id)
    
    modelo_a_usar = MODEL
    contenido_usuario = []

    # 1. Procesar archivo adjunto si existe
    if archivo_adjunto:
        nombre_archivo = archivo_adjunto.get("name", "")
        tipo_archivo = archivo_adjunto.get("type", "")
        base64_data = archivo_adjunto.get("base64", "")
        
        # CASO A: Es una IMAGEN (Usamos modelo de visión de Groq)
        if "image" in tipo_archivo:
            # Forzamos un modelo con capacidades visuales
            modelo_a_usar = "llama-3.2-11b-vision-preview"
            
            contenido_usuario = [
                {
                    "type": "text",
                    "text": f"El usuario ha subido una imagen de error, consola o código llamada '{nombre_archivo}'. Analízala visualmente y ayúdale a resolverlo. Instrucción adicional: {texto}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{tipo_archivo};base64,{base64_data}"
                    }
                }
            ]
        
        # CASO B: Es un ARCHIVO DE TEXTO / CÓDIGO (Java, Python, HTML, etc.)
        else:
            try:
                # Decodificamos el código a texto plano
                contenido_texto_archivo = base64.b64decode(base64_data).decode("utf-8")
                
                # Insertamos el código directamente en el prompt
                texto = f"El usuario subió el archivo de código '{nombre_archivo}' con el siguiente contenido:\n\n```{contenido_texto_archivo}```\n\nPetición: {texto}"
                contenido_usuario = texto
            except Exception as e:
                print("Error decodificando archivo:", e)
                contenido_usuario = f"[Error leyendo archivo {nombre_archivo}]. {texto}"
    else:
        # Petición de texto normal
        contenido_usuario = texto

    # Construimos el payload de mensajes
    mensajes = [
        {
            "role": "system",
            "content": obtener_prompt()
        }
    ]

    mensajes.extend(historial)

    mensajes.append({
        "role": "user",
        "content": contenido_usuario
    })

    # =====================================
    # AJUSTE DINÁMICO DE TOKENS
    # =====================================
    longitud = len(texto)

    # Identificamos si se está hablando de programación o si hay un archivo adjunto
    es_programacion = any(x in str(contenido_usuario).lower() for x in ["codigo", "código", "programar", "java", "android", "html", "error", "compile"]) or archivo_adjunto is not None

    if es_programacion:
        max_tokens = 1200  # Espacio de salida óptimo para códigos completos
    else:
        if longitud < 40:
            max_tokens = 120
        elif longitud < 120:
            max_tokens = 200
        else:
            max_tokens = 350

    try:
        respuesta = client.chat.completions.create(
            model=modelo_a_usar,
            messages=mensajes,
            temperature=0.3,  # Menor temperatura para evitar fallos lógicos en código
            max_tokens=max_tokens
        )

        texto_respuesta = respuesta.choices[0].message.content

        if not texto_respuesta:
            texto_respuesta = "Disculpa, no pude generar una respuesta."

        # Para no saturar el historial de SQLite con base64 pesados de imágenes, guardamos solo la referencia textual
        historial_guardar = texto if not (archivo_adjunto and "image" in archivo_adjunto.get("type", "")) else f"[Analizaste la imagen {archivo_adjunto.get('name')}] {texto}"

        historial.append({
            "role": "user",
            "content": historial_guardar
        })

        historial.append({
            "role": "assistant",
            "content": texto_respuesta
        })

        guardar_historial_usuario(session_id, historial)

        return texto_respuesta

    except Exception as e:
        print("ERROR IA:", e)
        return "Disculpa, tuve un problema al procesar la petición con la inteligencia artificial."

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
    
    archivo = datos.get("file")  # Captura la estructura del archivo enviado desde index.html
    session_id = datos.get("session_id") or request.remote_addr

    return jsonify({
        "response": generar_respuesta(mensaje, session_id, archivo_adjunto=archivo)
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
    # Buscamos de forma segura el index.html usando rutas absolutas
    ruta_raiz = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(ruta_raiz, "index.html")

# =====================================
# 📁 ARCHIVOS ESTÁTICOS
# =====================================

@app.route("/<path:archivo>")
def archivos(archivo):
    ruta_raiz = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(ruta_raiz, archivo)

# =====================================
# 🚀 RENDER
# =====================================

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=puerto
    )
