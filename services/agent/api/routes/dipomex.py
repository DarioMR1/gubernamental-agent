from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import requests
from config import settings

router = APIRouter()

@router.get("/estados")
async def get_estados():
    """Get all Mexican states from DIPOMEX API"""
    try:
        headers = {"APIKEY": settings.dipomex_api_key}
        response = requests.get(f"{settings.dipomex_api_url}/estados", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estados: {str(e)}")

@router.get("/municipios/{estado_id}")
async def get_municipios(estado_id: str):
    """Get municipalities for a specific state"""
    try:
        headers = {"APIKEY": settings.dipomex_api_key}
        params = {"id_estado": estado_id}
        response = requests.get(f"{settings.dipomex_api_url}/municipios", headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener municipios: {str(e)}")

@router.get("/colonias/{estado_id}/{municipio_id}")
async def get_colonias(estado_id: str, municipio_id: str):
    """Get neighborhoods for a specific state and municipality"""
    try:
        headers = {"APIKEY": settings.dipomex_api_key}
        params = {"id_estado": estado_id, "id_mun": municipio_id}
        response = requests.get(f"{settings.dipomex_api_url}/colonias", headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener colonias: {str(e)}")

@router.get("/codigo_postal/{cp}")
async def search_codigo_postal(cp: str):
    """Search address information by postal code"""
    try:
        headers = {"APIKEY": settings.dipomex_api_key}
        params = {"cp": cp}
        response = requests.get(f"{settings.dipomex_api_url}/codigo_postal", headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar código postal: {str(e)}")