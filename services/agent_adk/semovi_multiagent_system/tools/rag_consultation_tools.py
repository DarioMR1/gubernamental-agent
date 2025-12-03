# Copyright 2024 SEMOVI Multiagent System

"""RAG tools for querying official SEMOVI documentation using Vertex AI."""

import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional

from google.adk.tools.tool_context import ToolContext
from vertexai import rag
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RAG Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
DEFAULT_TOP_K = 5
DEFAULT_DISTANCE_THRESHOLD = 0.5
DEFAULT_CORPUS_NAME = "semovi"

logger = logging.getLogger(__name__)


def rag_query_semovi(
    query: str,
    tool_context: ToolContext,
    filter_by_section: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query SEMOVI official documentation using Vertex AI RAG.
    
    Args:
        query: User question or query about SEMOVI procedures
        tool_context: Context for accessing session state
        filter_by_section: Optional filter by document section (not implemented in Vertex AI RAG)
        
    Returns:
        Dict with RAG query results and structured information
    """
    try:
        # Always use the default SEMOVI corpus
        corpus_name = DEFAULT_CORPUS_NAME

        # Validate query
        if not query or len(query.strip()) < 3:
            return {
                "status": "error",
                "message": "La consulta debe tener al menos 3 caracteres.",
                "query": query,
                "corpus_name": corpus_name,
            }

        # Check if the corpus exists
        if not check_corpus_exists(corpus_name, tool_context):
            return {
                "status": "error", 
                "message": "Lo siento, no puedo acceder a la información de trámites en este momento. Por favor intenta más tarde.",
                "query": query,
                "corpus_name": corpus_name,
            }

        # Get the corpus resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name, tool_context)

        # Configure retrieval parameters
        rag_retrieval_config = rag.RagRetrievalConfig(
            top_k=DEFAULT_TOP_K,
            filter=rag.Filter(vector_distance_threshold=DEFAULT_DISTANCE_THRESHOLD),
        )

        # Perform the query
        logger.info(f"Performing RAG query: {query}")
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=corpus_resource_name,
                )
            ],
            text=query,
            rag_retrieval_config=rag_retrieval_config,
        )

        # Process the response into a more usable format
        results = []
        if hasattr(response, "contexts") and response.contexts:
            for ctx_group in response.contexts.contexts:
                result = {
                    "source_uri": (
                        ctx_group.source_uri if hasattr(ctx_group, "source_uri") else ""
                    ),
                    "source_name": (
                        ctx_group.source_display_name
                        if hasattr(ctx_group, "source_display_name")
                        else ""
                    ),
                    "content": ctx_group.text if hasattr(ctx_group, "text") else "",
                    "score": ctx_group.score if hasattr(ctx_group, "score") else 0.0,
                    "source_section": "Documentación SEMOVI",
                    "confidence_score": ctx_group.score if hasattr(ctx_group, "score") else 0.0,
                }
                results.append(result)
        
        # Store query in session history
        if "information_queries" not in tool_context.state:
            tool_context.state["information_queries"] = {"queries_made": []}
        
        queries_made = tool_context.state["information_queries"].get("queries_made", [])
        queries_made.append({
            "query": query,
            "filter": filter_by_section,
            "timestamp": datetime.now().isoformat(),
            "results_found": len(results),
            "confidence_score": max([r.get("score", 0.0) for r in results]) if results else 0.0
        })
        
        tool_context.state["information_queries"]["queries_made"] = queries_made

        # If we didn't find any results
        if not results:
            return {
                "status": "warning",
                "message": "No encontré información específica sobre tu consulta en los documentos de trámites disponibles.",
                "query": query,
                "corpus_name": corpus_name,
                "results": [],
                "results_count": 0,
            }

        return {
            "status": "success",
            "message": "Encontré información relevante sobre tu consulta",
            "query": query,
            "corpus_name": corpus_name,
            "results": results,
            "results_count": len(results),
            "confidence_score": max([r.get("score", 0.0) for r in results]) if results else 0.0,
        }
        
    except Exception as e:
        error_msg = f"Error al consultar la información: {str(e)}"
        logger.error(error_msg)
        
        tool_context.state["last_error"] = {
            "tool": "rag_query_semovi",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": "Lo siento, ocurrió un error al buscar la información. Por favor intenta de nuevo.",
            "query": query,
            "corpus_name": corpus_name,
        }


def get_corpus_resource_name(corpus_name: str, tool_context: ToolContext = None) -> str:
    """
    Convert a corpus name to its full resource name if needed.
    Handles various input formats and ensures the returned name follows Vertex AI's requirements.

    Args:
        corpus_name (str): The corpus name or display name
        tool_context (ToolContext): Optional tool context to check for saved resource names

    Returns:
        str: The full resource name of the corpus
    """
    logger.info(f"Getting resource name for corpus: {corpus_name}")

    # First, check if we have the resource name saved in the tool context
    if tool_context and tool_context.state:
        saved_resource_name = tool_context.state.get(f"corpus_resource_name_{corpus_name}")
        if saved_resource_name:
            logger.info(f"Found saved resource name: {saved_resource_name}")
            return saved_resource_name

    # If it's already a full resource name with the projects/locations/ragCorpora format
    if re.match(r"^projects/[^/]+/locations/[^/]+/ragCorpora/[^/]+$", corpus_name):
        return corpus_name

    # Check if this is a display name of an existing corpus
    try:
        # List all corpora and check if there's a match with the display name
        corpora = rag.list_corpora()
        for corpus in corpora:
            if hasattr(corpus, "display_name") and corpus.display_name == corpus_name:
                # Save the mapping for future use if we have tool_context
                if tool_context and tool_context.state:
                    tool_context.state[f"corpus_resource_name_{corpus_name}"] = corpus.name
                return corpus.name
    except Exception as e:
        logger.warning(f"Error when checking for corpus display name: {str(e)}")
        # If we can't check, continue with the default behavior
        pass

    # If it contains partial path elements, extract just the corpus ID
    if "/" in corpus_name:
        # Extract the last part of the path as the corpus ID
        corpus_id = corpus_name.split("/")[-1]
    else:
        corpus_id = corpus_name

    # Remove any special characters that might cause issues
    corpus_id = re.sub(r"[^a-zA-Z0-9_-]", "_", corpus_id)

    # Construct the standardized resource name
    return f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{corpus_id}"


def check_corpus_exists(corpus_name: str, tool_context: ToolContext) -> bool:
    """
    Check if a corpus with the given name exists.

    Args:
        corpus_name (str): The name of the corpus to check
        tool_context (ToolContext): The tool context for state management

    Returns:
        bool: True if the corpus exists, False otherwise
    """
    # Check state first if tool_context is provided
    if tool_context.state.get(f"corpus_exists_{corpus_name}"):
        return True

    try:
        # Get full resource name
        corpus_resource_name = get_corpus_resource_name(corpus_name, tool_context)

        # List all corpora and check if this one exists
        corpora = rag.list_corpora()
        for corpus in corpora:
            if (
                corpus.name == corpus_resource_name
                or corpus.display_name == corpus_name
            ):
                # Update state
                tool_context.state[f"corpus_exists_{corpus_name}"] = True
                # Save the actual resource name for future use
                tool_context.state[f"corpus_resource_name_{corpus_name}"] = corpus.name
                # Also set this as the current corpus if no current corpus is set
                if not tool_context.state.get("current_corpus"):
                    tool_context.state["current_corpus"] = corpus_name
                return True

        return False
    except Exception as e:
        logger.error(f"Error checking if corpus exists: {str(e)}")
        # If we can't check, assume it doesn't exist
        return False


def validate_information_query(query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Validate if a query is appropriate for SEMOVI information search.

    Args:
        query: Query string to validate
        tool_context: Tool context for state access
        
    Returns:
        Dict with validation results
    """
    try:
        # Define valid query topics
        valid_topics = [
            "licencia", "requisitos", "documentos", "examen", "curso",
            "costo", "precio", "oficina", "horario", "tramite", 
            "procedimiento", "reposicion", "renovacion", "expedicion",
            "semovi", "manejo", "conducir", "vehiculo", "motocicleta"
        ]
        
        query_lower = query.lower()
        
        # Check for valid topic keywords
        has_valid_topic = any(topic in query_lower for topic in valid_topics)
        
        # Check query length
        is_appropriate_length = 3 <= len(query.strip()) <= 200
        
        # Check for inappropriate content (basic filter)
        inappropriate_keywords = ["hack", "sql", "injection", "admin", "password"]
        has_inappropriate_content = any(keyword in query_lower for keyword in inappropriate_keywords)
        
        is_valid = has_valid_topic and is_appropriate_length and not has_inappropriate_content
        
        validation_result = {
            "is_valid": is_valid,
            "has_valid_topic": has_valid_topic,
            "is_appropriate_length": is_appropriate_length,
            "has_inappropriate_content": has_inappropriate_content,
            "query_length": len(query.strip())
        }
        
        if is_valid:
            message = "La consulta es válida para búsqueda de información SEMOVI"
        else:
            issues = []
            if not has_valid_topic:
                issues.append("consulta no relacionada con servicios SEMOVI")
            if not is_appropriate_length:
                issues.append("longitud de consulta inapropiada")
            if has_inappropriate_content:
                issues.append("consulta contiene contenido inapropiado")
            message = f"Validación de consulta falló: {', '.join(issues)}"
        
        return {
            "status": "success",
            "validation": validation_result,
            "message": message
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error validando consulta: {str(e)}"
        }