"""
🤖 Asistente General
Agente para conversación general y asistencia básica.
"""

from dotenv import load_dotenv
import os

# Definir la ruta base
BASEDIR = os.path.abspath(os.path.dirname(__file__))
# Cargar variables de entorno desde el archivo .env
load_dotenv(os.path.join(BASEDIR, "../.env"))

from google.adk.agents import Agent
from .tools import ALL_TOOL_FUNCTIONS

# Create the root agent that Google ADK will find automatically
root_agent = Agent(
    name="AsistenteGeneral",
    model="gemini-2.0-flash",
    tools=ALL_TOOL_FUNCTIONS,
    instruction="""
Eres un asistente amigable y útil. Puedes ayudar con preguntas generales, conversación casual y tareas básicas. Responde de manera clara y concisa.
""",
    output_key="respuesta"
)