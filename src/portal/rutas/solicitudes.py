"""API REST de solicitudes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from portal.modelos import (
    CambioEstado,
    NuevaSolicitud,
    NuevoSeguimiento,
    Seguimiento,
    Solicitud,
    SolicitudDetalle,
)
from portal.servicios import solicitudes as servicio
from portal.servicios.solicitudes import SolicitudNoEncontrada, TransicionInvalida

router = APIRouter(prefix="/api/solicitudes", tags=["solicitudes"])


@router.get("", response_model=list[Solicitud], summary="Listar solicitudes")
async def listar(
    estado: str | None = Query(default=None, description="Estado exacto o ABIERTAS"),
    categoria_id: int | None = Query(default=None),
    funcionario_id: int | None = Query(default=None),
    prioridad: str | None = Query(default=None),
    busqueda: str | None = Query(default=None, description="Texto a buscar en asunto y código"),
    limite: int = Query(default=100, ge=1, le=500),
) -> list[Solicitud]:
    """Devuelve las solicitudes que cumplen los filtros indicados."""
    return await servicio.listar_solicitudes(
        estado=estado,
        categoria_id=categoria_id,
        funcionario_id=funcionario_id,
        prioridad=prioridad,
        busqueda=busqueda,
        limite=limite,
    )


@router.get("/{solicitud_id}", response_model=SolicitudDetalle, summary="Obtener una solicitud")
async def obtener(solicitud_id: int) -> SolicitudDetalle:
    """Devuelve una solicitud con su línea de tiempo completa."""
    try:
        return await servicio.obtener_solicitud(solicitud_id)
    except SolicitudNoEncontrada as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@router.post(
    "",
    response_model=SolicitudDetalle,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una solicitud",
)
async def crear(datos: NuevaSolicitud) -> SolicitudDetalle:
    """Registra una solicitud nueva en estado RECIBIDA."""
    return await servicio.crear_solicitud(datos)


@router.post(
    "/{solicitud_id}/estado",
    response_model=SolicitudDetalle,
    summary="Cambiar el estado de una solicitud",
)
async def cambiar_estado(solicitud_id: int, cambio: CambioEstado) -> SolicitudDetalle:
    """Mueve la solicitud a otro estado, validando que la transición sea posible."""
    try:
        return await servicio.cambiar_estado(solicitud_id, cambio)
    except SolicitudNoEncontrada as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except TransicionInvalida as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post(
    "/{solicitud_id}/seguimientos",
    response_model=Seguimiento,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar un comentario",
)
async def agregar_seguimiento(solicitud_id: int, datos: NuevoSeguimiento) -> Seguimiento:
    """Agrega un comentario a la línea de tiempo de la solicitud."""
    try:
        return await servicio.agregar_seguimiento(solicitud_id, datos)
    except SolicitudNoEncontrada as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
