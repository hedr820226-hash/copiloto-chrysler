# ============================================================
# Dash Server V2 (CORREGIDO PARCHADO)
# app.py
# ============================================================

from flask import Flask, request, jsonify, send_from_directory
import os
import sqlite3
import json
import base64
import uuid
import logging
import mimetypes
from groq import Groq

# ============================================================
# APP - Configurado para servir la carpeta static correctamente
# ============================================================

app = Flask(__name__, static_folder="static", static_url_path="/static")

# ============================================================
# LOGS
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("Dash")

# ============================================================
# CONFIGURACIÓN
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

VISION_MODEL = "llama-3.2-11b-vision-preview"

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ============================================================
# BASE DE DATOS
# ============================================================

DB_PATH = "chat_history.db"

MAX_HISTORIAL = 10

MAX_ARCHIVO = 20000

# ============================================================
# SQLITE
# ============================================================

def inicializar_db():

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones(

                session_id TEXT PRIMARY KEY,

                historial TEXT

            )
        """)

        conn.commit()

inicializar_db()

# ============================================================
# PROMPT
# ============================================================

def obtener_prompt():

    return """
Eres Dash.

Eres la inteligencia artificial de ApexDash.

Tu función principal es ayudar al usuario a construir proyectos completos.

Nunca actúas como profesor si el usuario claramente quiere que desarrolles.

Cuando el usuario diga:

- crea
- desarrolla
- programa
- diseña
- construye

empiezas directamente.

No hagas entrevistas innecesarias.

Haz solamente preguntas cuando falte información realmente importante.

Si puedes asumir algo razonable, lo haces.

Especialidades:

• Python
• Java
• Android
• Kotlin
• HTML
• CSS
• JavaScript
• Node
• Flask
• SQLite
• SQL
• APIs
• Render
• Linux
• Git
• Docker
• IA
• ApexDash
• Apex Market

Cuando analices código:

- explica el problema
- encuentra errores
- propone mejoras
- entrega el código corregido

Cuando recibas imágenes:

analízalas completamente.

Cuando recibas archivos:

léelos completamente antes de responder.

Nunca inventes resultados.

Nunca digas que ejecutaste algo si no puedes hacerlo.

Nunca inventes pruebas.

Puedes analizar comandos peligrosos pero nunca afirmar que fueron ejecutados.

Responde siempre en español.

Para conversación casual responde corto.

Para programación responde completo.

Utiliza Markdown únicamente cuando estés mostrando código.

Piensa como un compañero de programación.
"""

# ============================================================
# MEMORIA
# ============================================================

def obtener_historial_usuario(session_id):

    with sqlite3.connect(DB_PATH) as conn:

        cursor = conn.cursor()

        cursor.execute(

            "SELECT historial FROM conversaciones WHERE session_id=?",

            (session_id,)

        )

        fila = cursor.fetchone()

    if not fila:

        return []

    try:

        return json.loads(fila[0])

    except Exception as e:

        logger.warning("Historial corrupto: %s", e)

        return []

# ============================================================
# GUARDAR MEMORIA
# ============================================================

def guardar_historial_usuario(

        session_id,

        historial

):

    historial = historial[-MAX_HISTORIAL:]

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

                    ensure_ascii=False,

                    separators=(",", ":")

                )

            )

        )

        conn.commit()

# ============================================================
# UTILIDADES
# ============================================================

def leer_archivo_base64(datos):

    contenido = base64.b64decode(datos)

    texto = contenido.decode(

        "utf-8",

        errors="ignore"

    )

    return texto[:MAX_ARCHIVO]

def es_imagen(tipo):

    return tipo.startswith("image/")

def detectar_programacion(texto):

    texto = texto.lower()

    palabras = [

        "python",

        "java",

        "android",

        "html",

        "css",

        "javascript",

        "flask",

        "sqlite",

        "sql",

        "error",

        "compile",

        "codigo",

        "código",

        "api",

        "backend",

        "frontend",

        "render"

    ]

    return any(p in texto for p in palabras)


# ============================================================
# CONSTRUCCIÓN DE MENSAJES
# ============================================================

def construir_mensajes(
        session_id,
        mensaje_usuario
):

    historial = obtener_historial_usuario(session_id)

    mensajes = [

        {
            "role": "system",
            "content": obtener_prompt()
        }

    ]


    for item in historial:

        mensajes.append(

            {

                "role": item["role"],

                "content": item["content"]

            }

        )


    mensajes.append(

        {

            "role": "user",

            "content": mensaje_usuario

        }

    )


    return mensajes



# ============================================================
# GUARDAR CONVERSACIÓN
# ============================================================

def actualizar_memoria(

        session_id,

        pregunta,

        respuesta

):

    historial = obtener_historial_usuario(session_id)


    historial.append(

        {

            "role": "user",

            "content": pregunta

        }

    )


    historial.append(

        {

            "role": "assistant",

            "content": respuesta

        }

    )


    guardar_historial_usuario(

        session_id,

        historial

    )



# ============================================================
# RESPUESTA IA TEXTO
# ============================================================

def preguntar_dash(

        session_id,

        mensaje

):

    if not client:

        return {

            "error":

            "GROQ_API_KEY no configurada"

        }


    try:

        mensajes = construir_mensajes(

            session_id,

            mensaje

        )


        respuesta = client.chat.completions.create(

            model=MODEL,

            messages=mensajes,

            temperature=0.3,

            max_tokens=4096

        )


        texto = respuesta.choices[0].message.content


        actualizar_memoria(

            session_id,

            mensaje,

            texto

        )


        return {

            "respuesta": texto

        }


    except Exception as e:


        logger.error(

            "Error IA: %s",

            e

        )


        return {

            "error":

            str(e)

        }



# ============================================================
# ANALISIS DE IMAGEN
# ============================================================

def analizar_imagen(

        imagen_base64,

        pregunta

):

    if not client:

        return {

            "error":

            "Cliente IA no disponible"

        }


    try:


        contenido = [

            {

                "type": "text",

                "text":

                pregunta

            },


            {

                "type": "image_url",

                "image_url":

                {

                    "url":

                    f"data:image/jpeg;base64,{imagen_base64}"

                }

            }

        ]



        respuesta = client.chat.completions.create(

            model=VISION_MODEL,

            messages=[

                {

                    "role":

                    "system",

                    "content":

                    obtener_prompt()

                },

                {

                    "role":

                    "user",

                    "content":

                    contenido

                }

            ],


            max_tokens=2048

        )



        return {

            "respuesta":

            respuesta.choices[0].message.content

        }


    except Exception as e:


        logger.error(

            "Error visión: %s",

            e

        )


        return {

            "error":

            str(e)

        }



# ============================================================
# PROCESAR ARCHIVOS
# ============================================================

def procesar_archivo(

        archivo

):

    try:

        nombre = archivo.get(

            "nombre",

            "archivo.txt"

        )


        tipo = archivo.get(

            "tipo",

            "text/plain"

        )


        datos = archivo.get(

            "contenido",

            ""

        )


        if es_imagen(tipo):


            return {

                "tipo":

                "imagen",

                "nombre":

                nombre,

                "contenido":

                datos

            }



        texto = leer_archivo_base64(

            datos

        )


        return {

            "tipo":

            "texto",

            "nombre":

            nombre,

            "contenido":

            texto

        }


    except Exception as e:


        logger.error(

            "Error archivo: %s",

            e

        )


        return {

            "error":

            str(e)

        }



# ============================================================
# PREPARAR CONTEXTO ARCHIVO
# ============================================================

def agregar_contexto_archivo(

        mensaje,

        archivo

):


    if not archivo:

        return mensaje



    if archivo.get("tipo") == "texto":


        return f"""

El usuario adjuntó este archivo:

Nombre:
{archivo.get('nombre')}


Contenido:

{archivo.get('contenido')}


Pregunta del usuario:

{mensaje}

"""



    return mensaje


# ============================================================
# RUTA PRINCIPAL (CORREGIDA)
# ============================================================

@app.route("/")
def inicio():
    return send_from_directory(".", "index.html")


# ============================================================
# ESTADO DEL SERVIDOR
# ============================================================

@app.route("/health")
def health():

    return jsonify({

        "server": "online",

        "groq":

            True if client else False,

        "modelo":

            MODEL

    })



# ============================================================
# CHAT PRINCIPAL
# ============================================================

@app.route(
    "/chat",
    methods=["POST"]
)

def chat():


    try:


        datos = request.get_json()


        if not datos:


            return jsonify({

                "error":

                "No se recibió información"

            }),400



        session_id = datos.get(

            "session_id"

        )


        if not session_id:


            session_id = str(

                uuid.uuid4()

            )



        mensaje = datos.get(

            "mensaje",

            ""

        )



        if not mensaje:


            return jsonify({

                "error":

                "Mensaje vacío"

            }),400



        resultado = preguntar_dash(

            session_id,

            mensaje

        )


        resultado["session_id"] = session_id


        return jsonify(resultado)



    except Exception as e:


        logger.error(

            "Error chat: %s",

            e

        )


        return jsonify({

            "error":

            str(e)

        }),500



# ============================================================
# CHAT CON ARCHIVOS
# ============================================================

@app.route(
    "/chat/file",
    methods=["POST"]
)

def chat_archivo():


    try:


        datos = request.get_json()


        session_id = datos.get(

            "session_id",

            str(uuid.uuid4())

        )


        mensaje = datos.get(

            "mensaje",

            ""

        )


        archivo = datos.get(

            "archivo"

        )


        contexto = ""


        if archivo:


            resultado_archivo = procesar_archivo(

                archivo

            )


            if "error" in resultado_archivo:


                return jsonify(resultado_archivo),400



            contexto = agregar_contexto_archivo(

                mensaje,

                resultado_archivo

            )


        else:


            contexto = mensaje



        respuesta = preguntar_dash(

            session_id,

            contexto

        )


        respuesta["session_id"] = session_id


        return jsonify(respuesta)



    except Exception as e:


        logger.error(

            "Error archivo chat: %s",

            e

        )


        return jsonify({

            "error":

            str(e)

        }),500



# ============================================================
# VISION
# ============================================================

@app.route(
    "/vision",
    methods=["POST"]
)

def vision():


    try:


        datos = request.get_json()



        imagen = datos.get(

            "imagen",

            ""

        )


        pregunta = datos.get(

            "pregunta",

            "Analiza esta imagen"

        )



        if not imagen:


            return jsonify({

                "error":

                "No hay imagen"

            }),400



        resultado = analizar_imagen(

            imagen,

            pregunta

        )


        return jsonify(resultado)



    except Exception as e:


        logger.error(

            "Error vision endpoint: %s",

            e

        )


        return jsonify({

            "error":

            str(e)

        }),500



# ============================================================
# OBTENER MEMORIA
# ============================================================

@app.route(
    "/memory/<session_id>",
    methods=["GET"]
)

def memoria(session_id):


    historial = obtener_historial_usuario(

        session_id

    )


    return jsonify({

        "session_id":

        session_id,


        "historial":

        historial

    })



# ============================================================
# BORRAR MEMORIA
# ============================================================

@app.route(
    "/memory/<session_id>",
    methods=["DELETE"]
)

def borrar_memoria(session_id):


    with sqlite3.connect(DB_PATH) as conn:


        conn.execute(

            "DELETE FROM conversaciones WHERE session_id=?",

            (session_id,)

        )


        conn.commit()



    return jsonify({

        "eliminado":

        True

    })



# ============================================================
# SERVIR ARCHIVOS ESTÁTICOS DESDE LA CARPETA FILES
# ============================================================

@app.route(
    "/files/<path:nombre>"
)

def archivos(nombre):


    try:

        return send_from_directory(

            "files",

            nombre

        )


    except Exception as e:


        return jsonify({

            "error":

            str(e)

        }),404



# ============================================================
# MANEJO DE ERRORES GLOBAL
# ============================================================

@app.errorhandler(404)

def no_encontrado(error):


    return jsonify({

        "error":

        "Ruta no encontrada"

    }),404



@app.errorhandler(500)

def error_servidor(error):


    return jsonify({

        "error":

        "Error interno del servidor"

      }),500


# ============================================================
# CORS
# ============================================================

try:

    from flask_cors import CORS

    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*"
            }
        }
    )

    logger.info(
        "CORS activado"
    )


except Exception as e:

    logger.warning(
        "CORS no disponible: %s",
        e
    )



# ============================================================
# CARPETAS DEL SISTEMA
# ============================================================

def crear_carpetas():


    carpetas = [

        "files",

        "uploads",

        "logs",
        
        "static"

    ]


    for carpeta in carpetas:


        if not os.path.exists(carpeta):

            os.makedirs(carpeta)


            logger.info(

                "Creada carpeta: %s",

                carpeta

            )



crear_carpetas()



# ============================================================
# LIMITES DE SEGURIDAD
# ============================================================

@app.before_request

def limitar_peticion():


    tamaño = request.content_length


    if tamaño:


        limite = 25 * 1024 * 1024


        if tamaño > limite:


            return jsonify({

                "error":

                "Archivo demasiado grande"

            }),413




# ============================================================
# INFORMACIÓN DEL SISTEMA
# ============================================================

@app.route("/info")

def informacion():


    return jsonify({

        "nombre":

        "Dash Server V2",


        "proyecto":

        "ApexDash",


        "modelo":

        MODEL,


        "vision":

        VISION_MODEL,


        "memoria":

        "SQLite",


        "estado":

        "operativo"

    })



# ============================================================
# LOG DE CONEXIONES
# ============================================================

@app.before_request

def registrar_peticion():


    logger.info(

        "%s %s",

        request.method,

        request.path

    )



# ============================================================
# INICIALIZACIÓN FINAL
# ============================================================

def iniciar_servidor():


    puerto = int(

        os.getenv(

            "PORT",

            5000

        )

    )


    logger.info(

        "================================"

    )


    logger.info(

        " DASH SERVER V2 INICIADO "

    )


    logger.info(

        "Puerto: %s",

        puerto

    )


    logger.info(

        "Modelo: %s",

        MODEL

    )


    logger.info(

        "================================"

    )


    app.run(

        host="0.0.0.0",

        port=puerto,

        debug=False

    )



# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":


    iniciar_servidor()

# ============================================================
# FIN Dash Server V2
# ============================================================
