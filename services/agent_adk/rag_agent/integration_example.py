"""
Example of how to integrate the Gubernamental RAG Agent with the existing system.

This shows how to use the RAG agent alongside other agents in the multiagent system.
"""

from google.adk.tools.tool_context import ToolContext
from rag_agent.tools.rag_query import rag_query


def integrate_rag_with_semovi_agent(user_query: str, tool_context: ToolContext):
    """
    Example function showing how to integrate RAG queries with the existing SEMOVI agent.
    
    This could be called from the semovi_multiagent_system when users ask questions
    that might benefit from official document consultation.
    """
    
    # Check if the query seems like it would benefit from RAG consultation
    rag_keywords = [
        'requisitos', 'documentos', 'procedimiento', 'tramite', 'regulacion',
        'ley', 'reglamento', 'normativa', 'oficina', 'horario', 'costo',
        'precio', 'tarifa', 'multa', 'sancion', 'licencia', 'permiso'
    ]
    
    query_lower = user_query.lower()
    might_benefit_from_rag = any(keyword in query_lower for keyword in rag_keywords)
    
    if not might_benefit_from_rag:
        return {
            "use_rag": False,
            "reason": "Query doesn't seem to require official document consultation"
        }
    
    # Perform RAG query
    try:
        rag_result = rag_query(user_query, tool_context)
        
        if rag_result.get('status') == 'success' and rag_result.get('results_count', 0) > 0:
            return {
                "use_rag": True,
                "rag_result": rag_result,
                "official_info_found": True,
                "message": "Found relevant official documentation"
            }
        else:
            return {
                "use_rag": True,
                "rag_result": rag_result,
                "official_info_found": False,
                "message": "No relevant official documentation found, using general knowledge"
            }
            
    except Exception as e:
        return {
            "use_rag": False,
            "error": str(e),
            "message": "Error accessing official documentation, using general knowledge"
        }


def enhance_semovi_response_with_rag(base_response: str, rag_results: dict) -> str:
    """
    Example function to enhance SEMOVI agent responses with RAG information.
    """
    
    if not rag_results.get('official_info_found'):
        return base_response
    
    rag_data = rag_results.get('rag_result', {})
    results = rag_data.get('results', [])
    
    if not results:
        return base_response
    
    # Build enhanced response
    enhanced_response = base_response + "\n\n"
    enhanced_response += "📋 **Información Oficial Adicional:**\n\n"
    
    for i, result in enumerate(results[:2], 1):  # Only show top 2 results
        content = result.get('text', '').strip()
        source = result.get('source_name', 'Documento oficial')
        score = result.get('score', 0)
        
        if content:
            enhanced_response += f"**{i}. {source}** (relevancia: {score:.2f})\n"
            enhanced_response += f"{content}\n\n"
    
    enhanced_response += "💡 *Esta información proviene de documentos oficiales pre-cargados en el sistema.*"
    
    return enhanced_response


# Example of how to modify an existing SEMOVI agent tool to use RAG
def enhanced_license_consultation(
    license_type: str,
    procedure_type: str,
    tool_context: ToolContext
):
    """
    Enhanced version of license consultation that uses RAG for official information.
    """
    
    # Build specific query for the license consultation
    query = f"requisitos licencia tipo {license_type} procedimiento {procedure_type}"
    
    # Check for RAG enhancement
    rag_integration = integrate_rag_with_semovi_agent(query, tool_context)
    
    # Base consultation logic (your existing implementation)
    base_result = {
        "license_type": license_type,
        "procedure_type": procedure_type,
        "status": "success",
        # ... your existing logic
    }
    
    # Enhance with RAG if available
    if rag_integration.get('official_info_found'):
        rag_result = rag_integration.get('rag_result')
        
        # Add official documentation references
        base_result['official_documentation'] = {
            "found": True,
            "results_count": rag_result.get('results_count', 0),
            "results": rag_result.get('results', [])
        }
        
        # Enhance the response message
        base_response = base_result.get('message', '')
        base_result['message'] = enhance_semovi_response_with_rag(
            base_response, 
            rag_integration
        )
    else:
        base_result['official_documentation'] = {
            "found": False,
            "message": rag_integration.get('message', 'No official documentation available')
        }
    
    return base_result


if __name__ == "__main__":
    # Example usage
    print("RAG Integration Example")
    print("This file shows how to integrate the RAG agent with existing SEMOVI agents.")
    print("Copy the patterns shown here to enhance your existing agent tools.")