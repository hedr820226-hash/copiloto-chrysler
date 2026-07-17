from flask import Flask, request, jsonify, send_from_directory
import os
import sqlite3
import json
import base64
import uuid
import logging
from groq import Groq

# =====================================
# 🚗 APP DASH
# =====================================

app = Flask(__name__, static_folder=".")

# =====================================
# 📝 LOGS
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# =====================================
# 🔑 CONFIGURACIÓN IA
# =====================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

MODEL = os.environ.get(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# =====================================
# 🧠 BASE DE DATOS
# =====================================

DB_PATH = "chat_history.db"


def inicializar_db():

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones (
                session_id TEXT PRIMARY KEY,
                historial TEXT
            )
        """)

        conn.commit()


inicializar_db()


# =====================================
# 🤖 PERSONALIDAD DASH
# =====================================

def obtener_prompt():

    return """
Eres Dash, la IA de ApexDash.

Eres copiloto de conducción y asistente experto de programación.

Hablas siempre en español.

Tu estilo:
- tranquilo
- profesional
- cercano
- explicas paso a paso

Áreas:
- programación
- páginas web
- Android
- Python
- Java
- bases de datos
- servidores
- diagnóstico técnico

REGLAS:

Si es conversación normal:
Responde natural y fácil de escuchar por voz.

Si es programación:
Puedes usar Markdown con bloques de código.

Si analizas errores:
Explica la causa y entrega una solución corregida.

Nunca inventes que ejecutaste algo que no ejecutaste.

Si necesitas modificar archivos:
Primero explica qué cambiarás.

COMANDOS ANDROID:

Cuando sea necesario generar una acción móvil agrega al final:

[ACCION:LLAMAR|contacto]

[ACCION:CORREO|correo|asunto|mensaje]

[ACCION:EXPORTAR|EXCEL|archivo.xlsx|datos]
"""


# =====================================
# 💾 MEMORIA
# =====================================


def obtener_historial_usuario(session_id):

    with sqlite3.connect(DB_PATH) as conn:

        cursor = conn.cursor()

        cursor.execute(
            "SELECT historial FROM conversaciones WHERE session_id=?",
            (session_id,)
        )

        resultado = cursor.fetchone()


    if resultado:

        try:
            return json.loads(resultado[0])

        except Exception:

            return []


    return []



def guardar_historial_usuario(session_id, historial):

    # conservar últimos 10 mensajes

    if len(historial) > 10:

        historial = historial[-10:]


    with sqlite3.connect(DB_PATH) as conn:

        conn.execute(
            """
            INSERT INTO conversaciones(session_id,historial)

            VALUES(?,?)

            ON CONFLICT(session_id)

            DO UPDATE SET historial=excluded.historial

            """,
            (
                session_id,
                json.dumps(
                    historial,
                    ensure_ascii=False
                )
            )
        )

        conn.commit()



# =====================================
# 📂 PROCESAR ARCHIVOS
# =====================================


MAX_ARCHIVO = 20000



def leer_archivo_base64(data):

    contenido = base64.b64decode(data)

    texto = contenido.decode(
        "utf-8",
        errors="ignore"
    )

    return texto[:MAX_ARCHIVO]



# =====================================
# 🧠 GENERADOR DE RESPUESTA
# =====================================


def generar_respuesta(
        texto,
        session_id,
        archivo_adjunto=None
):

    if not client:

        return "Dash no tiene configurada la API de inteligencia artificial."


    historial = obtener_historial_usuario(session_id)


    modelo_usar = MODEL


    contenido_usuario = texto


    # -----------------------------
    # ARCHIVOS
    # -----------------------------

    if archivo_adjunto:


        nombre = archivo_adjunto.get(
            "name",
            "archivo"
        )

        tipo = archivo_adjunto.get(
            "type",
            ""
        )


        datos = archivo_adjunto.get(
            "base64",
            ""
        )


        if tipo.startswith("image/"):


            modelo_usar = "llama-3.2-11b-vision-preview"


            contenido_usuario = [

                {
                    "type":"text",
                    "text":
                    f"""
Analiza esta imagen.

Archivo:
{nombre}

Pregunta:
{texto}
"""
                },

                {
                    "type":"image_url",

                    "image_url":
                    {
                        "url":
                        f"data:{tipo};base64,{datos}"
                    }
                }

            ]


        else:

            try:

                codigo = leer_archivo_base64(datos)


                contenido_usuario = f"""
El usuario envió este archivo:

{nombre}


Contenido:

```text
{codigo}

# =====================================
# 📩 CONSTRUIR MENSAJES PARA GROQ
# =====================================


    mensajes = [

        {
            "role": "system",
            "content": obtener_prompt()
        }

    ]


    mensajes.extend(historial)


    mensajes.append(
        {
            "role": "user",
            "content": contenido_usuario
        }
    )


    # =====================================
    # 🧮 DETECCIÓN DE PROGRAMACIÓN
    # =====================================


    texto_revision = str(contenido_usuario).lower()


    palabras_codigo = [

        "codigo",
        "código",
        "programar",
        "python",
        "java",
        "android",
        "html",
        "css",
        "javascript",
        "error",
        "compile",
        "flask",
        "api"

    ]


    es_programacion = any(
        palabra in texto_revision
        for palabra in palabras_codigo
    )


    if es_programacion or archivo_adjunto:

        max_tokens = 3000

    else:

        if len(texto) < 40:

            max_tokens = 200

        elif len(texto) < 150:

            max_tokens = 400

        else:

            max_tokens = 700



    # =====================================
    # 🤖 LLAMADA A GROQ
    # =====================================


    try:


        respuesta = client.chat.completions.create(

            model=modelo_usar,

            messages=mensajes,

            temperature=0.3,

            max_tokens=max_tokens

        )


        texto_respuesta = (
            respuesta
            .choices[0]
            .message
            .content
        )


        if not texto_respuesta:

            texto_respuesta = (
                "No pude generar una respuesta."
            )



        # =====================================
        # 💾 GUARDAR MEMORIA
        # =====================================


        if archivo_adjunto:


            memoria_usuario = (
                f"[Archivo enviado: "
                f"{archivo_adjunto.get('name','archivo')}] "
                f"{texto}"
            )


        else:


            if len(texto) > 500:

                memoria_usuario = (
                    "[Mensaje largo] "
                    + texto[:200]
                )

            else:

                memoria_usuario = texto



        historial.append(

            {
                "role":"user",
                "content":memoria_usuario
            }

        )


        historial.append(

            {
                "role":"assistant",
                "content":texto_respuesta
            }

        )


        guardar_historial_usuario(
            session_id,
            historial
        )


        return texto_respuesta



    except Exception as e:


        logging.error(
            "ERROR GROQ: %s",
            e
        )


        return (
            "Dash tuvo un problema "
            "procesando la solicitud."
        )



# =====================================
# 📱 API CHAT
# =====================================


@app.route(
    "/chat",
    methods=["POST"]
)

def chat():


    datos = request.get_json() or {}



    mensaje = (

        datos.get("message")

        or datos.get("mensaje")

        or ""

    )



    archivo = datos.get("file")



    # Creamos sesión nueva si no existe

    session_id = (

        datos.get("session_id")

        or str(uuid.uuid4())

    )



    respuesta = generar_respuesta(

        mensaje,

        session_id,

        archivo_adjunto=archivo

    )



    return jsonify(

        {

            "response":respuesta,

            "session_id":session_id

        }

    )



# =====================================
# 🧹 BORRAR MEMORIA
# =====================================


@app.route(

    "/historial/limpiar",

    methods=["POST"]

)

def limpiar():


    datos = request.get_json() or {}


    session_id = (

        datos.get("session_id")

        or ""

    )


    if not session_id:


        return jsonify(

            {
                "response":
                "No existe sesión."
            }

        )



    with sqlite3.connect(DB_PATH) as conn:


        conn.execute(

            "DELETE FROM conversaciones WHERE session_id=?",

            (session_id,)

        )

        conn.commit()



    return jsonify(

        {
            "response":
            "Memoria de Dash limpiada."
        }

    )



# =====================================
# 🌐 PÁGINA WEB
# =====================================


@app.route("/")

def home():


    ruta = os.path.dirname(

        os.path.abspath(__file__)

    )


    return send_from_directory(

        ruta,

        "index.html"

    )



# =====================================
# 📁 ARCHIVOS ESTÁTICOS
# =====================================


@app.route(
    "/<path:archivo>"
)

def archivos(archivo):


    ruta = os.path.dirname(

        os.path.abspath(__file__)

    )


    return send_from_directory(

        ruta,

        archivo

    )



# =====================================
# 🚀 RENDER
# =====================================


if __name__ == "__main__":


    puerto = int(

        os.environ.get(
            "PORT",
            10000
        )

    )


    app.run(

        host="0.0.0.0",

        port=puerto

    )
