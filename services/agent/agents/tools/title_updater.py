from langchain.tools import tool
from typing import Optional
from data.database import get_database
from data.repositories import ConversationRepository
from langchain_openai import ChatOpenAI
from config import settings

# Initialize LLM for title generation
title_llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # Use cheaper model for titles
    temperature=0.3,
    max_tokens=50,
    openai_api_key=settings.openai_api_key
)

TITLE_GENERATION_PROMPT = """Basándote en el siguiente mensaje del usuario, genera un título corto y descriptivo para esta conversación.

El título debe:
- Ser máximo 50 caracteres
- Capturar el tema principal del mensaje
- Ser claro y específico
- Estar en español

Mensaje del usuario: "{user_message}"

Título:"""

TITLE_UPDATE_ANALYSIS_PROMPT = """Analiza si el título actual de la conversación necesita actualizarse basándose en el nuevo contexto.

TÍTULO ACTUAL: "{current_title}"

CONTEXTO DE LA CONVERSACIÓN:
{conversation_context}

NUEVO MENSAJE: "{new_message}"

¿El título actual sigue siendo apropiado o necesita cambiar?

Responde SOLO con:
- "MANTENER" si el título actual es apropiado
- "CAMBIAR: [nuevo título]" si necesita actualizarse

El nuevo título debe:
- Ser máximo 50 caracteres
- Reflejar el tema principal o los temas múltiples
- Ser claro y específico
- Estar en español

Respuesta:"""


@tool
def update_conversation_title(conversation_id: str, user_message: str) -> str:
    """
    Actualiza automáticamente el título de una conversación basándose en el primer mensaje del usuario.
    
    Args:
        conversation_id: ID de la conversación a actualizar
        user_message: Mensaje del usuario para generar el título
    
    Returns:
        str: El nuevo título generado o mensaje de error
    """
    try:
        # Get database session
        db = next(get_database())
        conversation_repo = ConversationRepository(db)
        
        # Get the conversation
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            return f"Error: Conversación {conversation_id} no encontrada"
        
        # Only update title if it's currently null/empty
        if conversation.title:
            return f"La conversación ya tiene título: {conversation.title}"
        
        # Generate title using LLM
        prompt = TITLE_GENERATION_PROMPT.format(user_message=user_message)
        response = title_llm.invoke(prompt)
        generated_title = response.content.strip().replace('"', '').replace("'", "")
        
        # Ensure title is not too long
        if len(generated_title) > 50:
            generated_title = generated_title[:47] + "..."
        
        # Update conversation title
        conversation.title = generated_title
        db.commit()
        db.refresh(conversation)
        
        return f"Título actualizado exitosamente: {generated_title}"
        
    except Exception as e:
        return f"Error al actualizar título: {str(e)}"
    finally:
        db.close()


@tool 
def set_conversation_title(conversation_id: str, title: str) -> str:
    """
    Establece manualmente un título específico para una conversación.
    
    Args:
        conversation_id: ID de la conversación a actualizar
        title: Título a establecer
    
    Returns:
        str: Mensaje de confirmación o error
    """
    try:
        # Get database session
        db = next(get_database())
        conversation_repo = ConversationRepository(db)
        
        # Get the conversation
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            return f"Error: Conversación {conversation_id} no encontrada"
        
        # Validate and clean title
        clean_title = title.strip()
        if len(clean_title) > 50:
            clean_title = clean_title[:47] + "..."
        
        if not clean_title:
            return "Error: El título no puede estar vacío"
        
        # Update conversation title
        conversation.title = clean_title
        db.commit()
        db.refresh(conversation)
        
        return f"Título establecido exitosamente: {clean_title}"
        
    except Exception as e:
        return f"Error al establecer título: {str(e)}"
    finally:
        db.close()


@tool
def analyze_and_update_title(conversation_id: str, user_message: str, conversation_context: str) -> str:
    """
    Analiza si el título de la conversación necesita actualizarse basándose en el contexto actual.
    
    Args:
        conversation_id: ID de la conversación
        user_message: Nuevo mensaje del usuario  
        conversation_context: Contexto de los últimos mensajes
    
    Returns:
        str: Resultado del análisis y actualización
    """
    try:
        # Get database session
        db = next(get_database())
        conversation_repo = ConversationRepository(db)
        
        # Get the conversation
        conversation = conversation_repo.get_conversation(conversation_id)
        if not conversation:
            return f"Error: Conversación {conversation_id} no encontrada"
        
        current_title = conversation.title or "Sin título"
        
        # Si no hay título, crear uno nuevo
        if not conversation.title:
            return update_conversation_title.invoke({
                "conversation_id": conversation_id,
                "user_message": user_message
            })
        
        # Analizar si el título necesita actualizarse
        analysis_prompt = TITLE_UPDATE_ANALYSIS_PROMPT.format(
            current_title=current_title,
            conversation_context=conversation_context,
            new_message=user_message
        )
        
        response = title_llm.invoke(analysis_prompt)
        analysis_result = response.content.strip()
        
        if analysis_result.startswith("MANTENER"):
            return f"Título mantenido: {current_title}"
        elif analysis_result.startswith("CAMBIAR:"):
            # Extraer el nuevo título
            new_title = analysis_result.replace("CAMBIAR:", "").strip()
            
            # Limpiar y validar el nuevo título
            if len(new_title) > 50:
                new_title = new_title[:47] + "..."
            
            # Actualizar en la base de datos
            conversation.title = new_title
            db.commit()
            db.refresh(conversation)
            
            return f"Título actualizado: {new_title}"
        else:
            # Fallback: mantener título actual
            return f"Análisis inconcluso, título mantenido: {current_title}"
            
    except Exception as e:
        return f"Error en análisis de título: {str(e)}"
    finally:
        db.close()