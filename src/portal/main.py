"""Aplicación FastAPI del Portal de Atención al Estudiante."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from portal import basedatos
from portal.config import obtener_configuracion
from portal.rutas import catalogos, metricas, solicitudes, vistas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

DIRECTORIO_ESTATICOS = Path(__file__).resolve().parent / "estaticos"


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Abre el pool de Oracle al arrancar y lo cierra al apagar."""
    await basedatos.iniciar_pool()
    try:
        yield
    finally:
        await basedatos.cerrar_pool()


app = FastAPI(
    title="Portal de Atención al Estudiante - UPB",
    description=(
        "Registro y seguimiento de solicitudes de atención de estudiantes, "
        "con control de SLA por categoría."
    ),
    version="0.1.0",
    lifespan=ciclo_de_vida,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.mount("/estaticos", StaticFiles(directory=str(DIRECTORIO_ESTATICOS)), name="estaticos")

app.include_router(vistas.router)
app.include_router(solicitudes.router)
app.include_router(catalogos.router)
app.include_router(metricas.router)


@app.get("/salud", tags=["operación"], summary="Estado del servicio")
async def salud() -> JSONResponse:
    """Comprueba que la aplicación responde y que Oracle está accesible."""
    bd_disponible = await basedatos.verificar_conexion()

    cantidad_solicitudes = None
    if bd_disponible:
        fila = await basedatos.consultar_uno("SELECT COUNT(*) AS total FROM solicitudes")
        cantidad_solicitudes = int(fila["total"]) if fila else 0

    cuerpo = {
        "estado": "ok" if bd_disponible else "degradado",
        "base_de_datos": "conectada" if bd_disponible else "sin conexión",
        "solicitudes": cantidad_solicitudes,
    }
    return JSONResponse(cuerpo, status_code=200 if bd_disponible else 503)


def ejecutar() -> None:
    """Punto de entrada del comando ``portal``: levanta uvicorn."""
    import uvicorn

    config = obtener_configuracion()
    uvicorn.run(
        "portal.main:app",
        host="127.0.0.1",
        port=8000,
        reload=config.es_desarrollo,
        reload_dirs=[str(Path(__file__).resolve().parent)],
    )
