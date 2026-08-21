"""API REST de las métricas del panel de control."""

from __future__ import annotations

from fastapi import APIRouter

from portal.modelos import MetricasPanel
from portal.servicios import metricas as servicio

router = APIRouter(prefix="/api/metricas", tags=["métricas"])


@router.get("", response_model=MetricasPanel, summary="Métricas del panel")
async def obtener_metricas() -> MetricasPanel:
    """Devuelve las cifras agregadas que alimentan el panel de control."""
    return await servicio.obtener_metricas()
