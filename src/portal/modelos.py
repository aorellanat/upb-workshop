"""Modelos Pydantic del portal.

Los modelos que terminan en ``Nueva``/``Cambio`` describen lo que llega desde el cliente;
el resto describe lo que devuelve la API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Estado = Literal["RECIBIDA", "EN_REVISION", "EN_PROCESO", "RESUELTA", "CERRADA", "RECHAZADA"]
Prioridad = Literal["BAJA", "MEDIA", "ALTA", "URGENTE"]


class Categoria(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    sla_horas: int


class Funcionario(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    area: str
    activo: bool = True


class Estudiante(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_estudiante: str
    nombres: str
    apellidos: str
    correo: str
    carrera: str
    semestre: int
    activo: bool = True

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"


class Seguimiento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    solicitud_id: int
    autor: str
    mensaje: str
    es_interno: bool
    creado_en: datetime


class ResumenSla(BaseModel):
    """Estado de SLA calculado para una solicitud."""

    horas_transcurridas: float
    horas_limite: int
    horas_restantes: float
    porcentaje_consumido: float
    vencida: bool
    en_riesgo: bool
    etiqueta: str


class Solicitud(BaseModel):
    """Solicitud con los datos de sus tablas relacionadas ya resueltos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    asunto: str
    descripcion: str
    estado: Estado
    prioridad: Prioridad
    creada_en: datetime
    actualizada_en: datetime
    cerrada_en: datetime | None = None

    estudiante_id: int
    estudiante_nombre: str
    estudiante_codigo: str
    estudiante_correo: str

    categoria_id: int
    categoria_nombre: str
    categoria_sla_horas: int

    funcionario_id: int | None = None
    funcionario_nombre: str | None = None

    sla: ResumenSla | None = None


class SolicitudDetalle(Solicitud):
    """Solicitud con su línea de tiempo de seguimientos."""

    seguimientos: list[Seguimiento] = Field(default_factory=list)


class NuevaSolicitud(BaseModel):
    """Datos para registrar una solicitud."""

    estudiante_id: int
    categoria_id: int
    asunto: str = Field(min_length=5, max_length=200)
    descripcion: str = Field(min_length=10, max_length=2000)
    prioridad: Prioridad = "MEDIA"


class CambioEstado(BaseModel):
    """Datos para mover una solicitud a otro estado."""

    estado: Estado
    autor: str = Field(min_length=2, max_length=150)
    comentario: str | None = Field(default=None, max_length=2000)


class NuevoSeguimiento(BaseModel):
    """Datos para agregar un comentario a la línea de tiempo."""

    autor: str = Field(min_length=2, max_length=150)
    mensaje: str = Field(min_length=2, max_length=2000)
    es_interno: bool = False


class MetricasPanel(BaseModel):
    """Cifras que alimentan el panel de control."""

    total: int
    abiertas: int
    cerradas: int
    vencidas: int
    en_riesgo: int
    por_estado: dict[str, int]
    por_categoria: list[dict[str, object]]
    por_prioridad: dict[str, int]
    carga_por_funcionario: list[dict[str, object]]


__all__ = [
    "Categoria",
    "CambioEstado",
    "Estado",
    "Estudiante",
    "Funcionario",
    "MetricasPanel",
    "NuevaSolicitud",
    "NuevoSeguimiento",
    "Prioridad",
    "ResumenSla",
    "Seguimiento",
    "Solicitud",
    "SolicitudDetalle",
]
