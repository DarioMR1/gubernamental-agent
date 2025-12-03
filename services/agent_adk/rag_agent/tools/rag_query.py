"""
Tool for querying Vertex AI RAG corpora and retrieving relevant information.
"""

import logging
from typing import Dict, Any

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

from ..config import (
    DEFAULT_DISTANCE_THRESHOLD,
    DEFAULT_TOP_K,
    DEFAULT_CORPUS_NAME,
)
from .utils import check_corpus_exists, get_corpus_resource_name


def rag_query(
    query: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """
    Query the SEMOVI documents corpus to answer user questions about vehicle procedures.

    Args:
        query (str): The user's question about SEMOVI procedures
        tool_context (ToolContext): The tool context

    Returns:
        Dict[str, Any]: The query results and status
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
        print("Performing retrieval query...")
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
                    "text": ctx_group.text if hasattr(ctx_group, "text") else "",
                    "score": ctx_group.score if hasattr(ctx_group, "score") else 0.0,
                }
                results.append(result)

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
        }

    except Exception as e:
        error_msg = f"Error al consultar la información: {str(e)}"
        logging.error(error_msg)
        return {
            "status": "error",
            "message": "Lo siento, ocurrió un error al buscar la información. Por favor intenta de nuevo.",
            "query": query,
            "corpus_name": corpus_name,
        }