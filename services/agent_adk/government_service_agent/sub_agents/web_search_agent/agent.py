import os
from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Cargar variables de entorno
load_dotenv()

def search_web_with_tavily(
    tool_context: ToolContext, 
    query: str, 
    search_depth: str = 'advanced', 
    include_domains: Optional[List[str]] = None, 
    topic: str = 'general', 
    days: int = 3
) -> dict:
    """
    Realiza una búsqueda directa en internet utilizando la API de Tavily.
    """
    try:
        from tavily import TavilyClient
    except ImportError:
        return {"status": "error", "message": "Falta librería tavily-python."}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"status": "error", "message": "Falta TAVILY_API_KEY"}

    try:
        tavily = TavilyClient(api_key=api_key)
        
        # --- BÚSQUEDA DIRECTA (SIN MAGIA EXTRA) ---
        response = tavily.search(
            query=query,
            search_depth=search_depth,
            include_domains=include_domains,
            max_results=5,
            include_answer=True,
            topic=topic,
            days=days
        )
        
        results = response.get("results", [])
        
        # Guardar historial simple
        if tool_context.state:
            current_history = tool_context.state.get("interaction_history", [])
            new_history = current_history.copy()
            new_history.append({
                "action": "web_search", 
                "query": query,
                "results": len(results),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            tool_context.state["interaction_history"] = new_history

        return {
            "status": "success",
            "summary": response.get("answer", ""),
            "results": results
        }

    except Exception as e:
        return {"status": "error", "message": f"Error en Tavily: {str(e)}"}

def get_page_content(tool_context: ToolContext, url: str) -> dict:
    """Extrae el contenido de una URL específica."""
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        tavily = TavilyClient(api_key=api_key)
        
        response = tavily.search(url=url, search_depth="advanced", max_results=1)
        content = ""
        if response.get("results"):
            content = response["results"][0].get("content", "Sin contenido extraíble.")
            
        return {"status": "success", "url": url, "content": content[:5000]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- AGENTE SIMPLIFICADO ---

web_search_agent = Agent(
    name="web_search_agent",
    model="gemini-2.0-flash",
    description="""
    Use this agent for ANY general query, news, weather, or information lookups.
    """,
    instruction=f"""
    Eres un Investigador Web eficiente.
    
    FECHA: {datetime.now().strftime("%d %B %Y")}
    AÑO: {datetime.now().year}

    ### INSTRUCCIONES:
    1. **Busca directamente:** Usa `search_web_with_tavily` cuando necesites información.
    2. **Parámetros:**
       - Usa `topic='news'` SOLO para noticias muy recientes.
       - Usa `topic='general'` para todo lo demás.
    3. **Contexto:** Si el usuario no especifica país, asume **México**.
    4. **Silencio:** No anuncies lo que vas a hacer, solo entrega los resultados.
    
    Cita tus fuentes al final.
    """,
    tools=[
        search_web_with_tavily,
        get_page_content
    ],
    sub_agents=[],
)