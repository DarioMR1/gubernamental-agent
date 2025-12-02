# Copyright 2024 SEMOVI Multiagent System

"""RAG tools for querying official SEMOVI documentation using Vertex AI."""

import os
from datetime import datetime
from typing import Optional

from google.adk.tools.tool_context import ToolContext
# Note: RAG functionality simplified to not depend on external libraries


def rag_query_semovi(
    query: str,
    tool_context: ToolContext,
    filter_by_section: Optional[str] = None
) :
    """
    Query SEMOVI official documentation using Vertex AI RAG.
    
    Args:
        tool_context: Context for accessing session state
        query: User question or query about SEMOVI procedures
        filter_by_section: Optional filter by document section
        
    Returns:
        Dict with RAG query results and structured information
    """
    try:
        # Validate query
        if not query or len(query.strip()) < 3:
            return {
                "status": "error",
                "message": "Query must be at least 3 characters long"
            }
        
        # For now, simulate RAG responses based on common SEMOVI queries
        # In production, this would connect to actual Vertex AI RAG
        rag_results = _simulate_rag_query(query, filter_by_section)
        corpus_name = "semovi_procedures"
        
        # Store query in session history
        queries_made = tool_context.state.get("information_queries", {}).get("queries_made", [])
        queries_made.append({
            "query": query,
            "filter": filter_by_section,
            "timestamp": datetime.now().isoformat(),
            "results_found": len(rag_results.get("results", [])),
            "satisfaction_score": rag_results.get("confidence_score", 0.0)
        })
        
        tool_context.state["information_queries"]["queries_made"] = queries_made
        
        return {
            "status": "success",
            "query": query,
            "filter_section": filter_by_section,
            "results": rag_results.get("results", []),
            "results_count": len(rag_results.get("results", [])),
            "confidence_score": rag_results.get("confidence_score", 0.0),
            "corpus_name": corpus_name,
            "message": f"Found {len(rag_results.get('results', []))} relevant results for your query"
        }
        
    except Exception as e:
        tool_context.state["last_error"] = {
            "tool": "rag_query_semovi",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error querying SEMOVI documentation: {str(e)}"
        }


def _build_filter_expression(section):
    """Build filter expression for RAG query based on section."""
    section_filters = {
        "requirements": "metadata.section = 'requirements'",
        "procedures": "metadata.section = 'procedures'",
        "costs": "metadata.section = 'costs'",
        "offices": "metadata.section = 'offices'",
        "medical": "metadata.section = 'medical_exams'",
        "courses": "metadata.section = 'driving_courses'"
    }
    
    return section_filters.get(section.lower(), "")


def _simulate_rag_query(query, filter_section = None):
    """
    Simulate RAG query results based on common SEMOVI questions.
    In production, this would be replaced with actual Vertex AI RAG calls.
    """
    query_lower = query.lower()
    
    # Define knowledge base responses
    knowledge_responses = {
        "licencia tipo a requisitos": {
            "content": "Para tramitar una Licencia Tipo A se requiere: 1) Identificacion oficial vigente (INE/Pasaporte), 2) CURP, 3) Comprobante de domicilio no mayor a 3 meses, 4) Acta de nacimiento certificada, 5) Examen medico vigente, 6) Constancia de curso de manejo, 7) RFC en caso de ser aplicable. El costo es de $866.00 pesos mexicanos.",
            "source_section": "Licencia Tipo A - Requisitos",
            "confidence_score": 0.95,
            "page_reference": "Pagina 3-4"
        },
        "examen medico": {
            "content": "El examen medico debe incluir: evaluacion de agudeza visual, prueba de reflejos y coordinacion, examen de audicion, y certificado medico general. Debe ser expedido por medico autorizado y tener vigencia maxima de 30 dias naturales. Costo aproximado: $200-400 pesos.",
            "source_section": "Examenes Medicos Requeridos",
            "confidence_score": 0.92,
            "page_reference": "Pagina 8"
        },
        "curso de manejo": {
            "content": "El curso de manejo es obligatorio para expedicion de licencias. Incluye teoria vial, senales de transito, y practica de manejo. Duracion minima: 20 horas teoricas y 10 horas practicas. Debe ser en escuela autorizada por SEMOVI. Costo promedio: $1,500-3,000 pesos.",
            "source_section": "Cursos de Manejo Obligatorios",
            "confidence_score": 0.88,
            "page_reference": "Pagina 12"
        },
        "reposicion por robo": {
            "content": "Para reposicion por robo se requiere adicionalmente: denuncia ante Ministerio Publico, declaracion bajo protesta de decir verdad, identificacion oficial adicional. Costo adicional: $158.00 pesos sobre el costo base de la licencia.",
            "source_section": "Procedimientos de Reposicion",
            "confidence_score": 0.90,
            "page_reference": "Pagina 15"
        },
        "horarios oficinas": {
            "content": "Las oficinas SEMOVI atienden de lunes a viernes de 8:00 AM a 3:00 PM. Sabados y domingos cerrado. Se recomienda llegar 15 minutos antes de la cita. Es indispensable agendar cita previa.",
            "source_section": "Horarios y Ubicaciones",
            "confidence_score": 0.85,
            "page_reference": "Pagina 2"
        }
    }
    
    # Find best matching response
    best_match = None
    best_score = 0.0
    
    for key_phrase, response in knowledge_responses.items():
        # Simple keyword matching
        keywords = key_phrase.split()
        matches = sum(1 for keyword in keywords if keyword in query_lower)
        score = matches / len(keywords) if keywords else 0.0
        
        if score > best_score and score > 0.3:  # Minimum 30% keyword match
            best_match = response
            best_score = score
    
    # Apply section filter if specified
    if filter_section and best_match:
        section_keywords = {
            "requirements": ["requisitos", "documentos"],
            "procedures": ["procedimiento", "tramite", "proceso"],
            "costs": ["costo", "precio", "pago"],
            "offices": ["oficina", "horario", "ubicacion"],
            "medical": ["medico", "examen"],
            "courses": ["curso", "manejo", "teoria"]
        }
        
        filter_keywords = section_keywords.get(filter_section, [])
        if not any(keyword in query_lower for keyword in filter_keywords):
            best_match = None
    
    if best_match:
        return {
            "results": [best_match],
            "confidence_score": best_score * 0.9  # Slightly reduce for simulation
        }
    else:
        # Return generic helpful response
        return {
            "results": [{
                "content": "La informacion solicitada no se encuentra en la documentacion disponible. Para consultas especificas, te recomiendo contactar directamente a SEMOVI o visitar una oficina para asesoria personalizada.",
                "source_section": "Consulta General",
                "confidence_score": 0.5,
                "page_reference": "Informacion no disponible"
            }],
            "confidence_score": 0.5
        }


def search_requirements_by_license(
    tool_context,
    license_type,
    procedure_type
) :
    """
    Search specific requirements for a license type and procedure using RAG.
    
    Args:
        tool_context: Tool context for state access
        license_type: Type of license (A, A1, A2)
        procedure_type: Type of procedure (expedition, renewal, replacement)
        
    Returns:
        Dict with specific requirements found via RAG
    """
    try:
        # Build specific query for requirements
        query = f"requisitos licencia tipo {license_type} {procedure_type}"
        
        # Execute RAG query with requirements filter
        rag_result = rag_query_semovi(
            tool_context, 
            query, 
            filter_by_section="requirements"
        )
        
        if rag_result["status"] != "success":
            return rag_result
        
        results = rag_result.get("results", [])
        
        if not results:
            return {
                "status": "not_found",
                "message": f"No specific requirements found for {license_type} {procedure_type}"
            }
        
        # Format requirements for display
        formatted_requirements = []
        for result in results:
            content = result.get("content", "")
            # Extract numbered requirements if present
            if "1)" in content:
                requirements_text = content.split("se requiere:")[1] if "se requiere:" in content else content
                formatted_requirements.append(requirements_text.strip())
        
        return {
            "status": "success",
            "license_type": license_type,
            "procedure_type": procedure_type,
            "requirements_found": formatted_requirements,
            "rag_results": results,
            "confidence_score": rag_result.get("confidence_score", 0.0),
            "message": f"Found specific requirements for {license_type} {procedure_type}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching requirements: {str(e)}"
        }


def get_procedure_details(procedure_name: str, tool_context: ToolContext) :
    """
    Get detailed information about a specific SEMOVI procedure using RAG.
    
    Args:
        tool_context: Tool context for state access
        procedure_name: Name of the procedure to get details for
        
    Returns:
        Dict with detailed procedure information
    """
    try:
        # Map procedure names to search queries
        procedure_queries = {
            "expedicion_licencia_a": "como tramitar licencia tipo A primera vez expedicion",
            "renovacion_licencia_a1": "renovar licencia tipo A1 vencida procedimiento",
            "reposicion_por_robo": "reposicion licencia por robo extravio requisitos",
            "examen_medico_proceso": "examen medico licencia donde cuando requisitos",
            "curso_manejo_requisitos": "curso de manejo obligatorio donde tomar duracion"
        }
        
        query = procedure_queries.get(procedure_name)
        if not query:
            return {
                "status": "error",
                "message": f"Unknown procedure: {procedure_name}"
            }
        
        # Execute RAG query with procedures filter
        rag_result = rag_query_semovi(
            tool_context,
            query,
            filter_by_section="procedures"
        )
        
        if rag_result["status"] != "success":
            return rag_result
        
        results = rag_result.get("results", [])
        
        if not results:
            return {
                "status": "not_found", 
                "message": f"No details found for procedure: {procedure_name}"
            }
        
        # Format procedure details
        procedure_details = {
            "procedure_name": procedure_name,
            "details": results[0].get("content", ""),
            "source": results[0].get("source_section", ""),
            "reference": results[0].get("page_reference", ""),
            "confidence": results[0].get("confidence_score", 0.0)
        }
        
        return {
            "status": "success",
            "procedure_details": procedure_details,
            "all_results": results,
            "message": f"Retrieved details for {procedure_name}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting procedure details: {str(e)}"
        }


def validate_information_query(query: str, tool_context: ToolContext) :
    """
    Validate if a query is appropriate for SEMOVI information search.
    
    Args:
        tool_context: Tool context for state access
        query: Query string to validate
        
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
            message = "Query is valid for SEMOVI information search"
        else:
            issues = []
            if not has_valid_topic:
                issues.append("query not related to SEMOVI services")
            if not is_appropriate_length:
                issues.append("query length inappropriate")
            if has_inappropriate_content:
                issues.append("query contains inappropriate content")
            message = f"Query validation failed: {', '.join(issues)}"
        
        return {
            "status": "success",
            "validation": validation_result,
            "message": message
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error validating query: {str(e)}"
        }