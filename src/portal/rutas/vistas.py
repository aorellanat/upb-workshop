"""Vistas HTML del portal, renderizadas con Jinja2."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from portal import basedatos
from portal.servicios import metricas as servicio_metricas
from portal.servicios import solicitudes as servicio_solicitudes
from portal.servicios.solicitudes import SolicitudNoEncontrada

DIRECTORIO_PLANTILLAS = Path(__file__).resolve().parent.parent / "plantillas"
plantillas = Jinja2Templates(directory=str(DIRECTORIO_PLANTILLAS))

router = APIRouter(tags=["vistas"])

ETIQUETAS_ESTADO = {
    "RECIBIDA": "Recibida",
    "EN_REVISION": "En revisión",
    "EN_PROCESO": "En proceso",
    "RESUELTA": "Resuelta",
    "CERRADA": "Cerrada",
    "RECHAZADA": "Rechazada",
}

ETIQUETAS_PRIORIDAD = {
    "BAJA": "Baja",
    "MEDIA": "Media",
    "ALTA": "Alta",
    "URGENTE": "Urgente",
}

# Disponibles en todas las plantillas para traducir los códigos de la base de datos.
plantillas.env.globals["etiquetas_estado"] = ETIQUETAS_ESTADO
plantillas.env.globals["etiquetas_prioridad"] = ETIQUETAS_PRIORIDAD


@router.get("/", response_class=HTMLResponse, summary="Panel de control")
async def panel(request: Request) -> HTMLResponse:
    """Página principal con las cifras generales de atención."""
    datos = await servicio_metricas.obtener_metricas()
    return plantillas.TemplateResponse(
        request=request,
        name="panel.html",
        context={"metricas": datos, "titulo": "Panel de control"},
    )


@router.get("/solicitudes", response_class=HTMLResponse, summary="Listado de solicitudes")
async def listado(
    request: Request,
    estado: str | None = None,
    categoria_id: int | None = None,
    prioridad: str | None = None,
    busqueda: str | None = None,
) -> HTMLResponse:
    """Listado de solicitudes con filtros por estado, categoría, prioridad y texto."""
    resultados = await servicio_solicitudes.listar_solicitudes(
        estado=estado,
        categoria_id=categoria_id,
        prioridad=prioridad,
        busqueda=busqueda,
    )
    categorias = await basedatos.consultar("SELECT id, nombre FROM categorias ORDER BY nombre")
    return plantillas.TemplateResponse(
        request=request,
        name="solicitudes_lista.html",
        context={
            "solicitudes": resultados,
            "categorias": categorias,
            "filtros": {
                "estado": estado or "",
                "categoria_id": categoria_id or "",
                "prioridad": prioridad or "",
                "busqueda": busqueda or "",
            },
            "titulo": "Solicitudes",
        },
    )


@router.get("/solicitudes/nueva", response_class=HTMLResponse, summary="Formulario de registro")
async def formulario_nueva(request: Request) -> HTMLResponse:
    """Formulario para registrar una solicitud nueva."""
    categorias = await basedatos.consultar(
        "SELECT id, nombre, sla_horas FROM categorias ORDER BY nombre"
    )
    estudiantes = await basedatos.consultar(
        "SELECT id, codigo_estudiante, nombres, apellidos "
        "  FROM estudiantes WHERE activo = 1 ORDER BY apellidos, nombres"
    )
    return plantillas.TemplateResponse(
        request=request,
        name="solicitud_nueva.html",
        context={
            "categorias": categorias,
            "estudiantes": estudiantes,
            "titulo": "Nueva solicitud",
        },
    )


@router.get(
    "/solicitudes/{solicitud_id}", response_class=HTMLResponse, summary="Detalle de solicitud"
)
async def detalle(request: Request, solicitud_id: int) -> HTMLResponse:
    """Detalle de una solicitud con su línea de tiempo y las acciones disponibles."""
    try:
        solicitud = await servicio_solicitudes.obtener_solicitud(solicitud_id)
    except SolicitudNoEncontrada as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error

    return plantillas.TemplateResponse(
        request=request,
        name="solicitud_detalle.html",
        context={
            "solicitud": solicitud,
            "estados_alcanzables": servicio_solicitudes.estados_alcanzables(solicitud.estado),
            "titulo": solicitud.codigo,
        },
    )
