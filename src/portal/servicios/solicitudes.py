"""Lógica de negocio de las solicitudes.

Toda transición de estado pasa por este módulo. Las rutas HTTP no cambian el estado de una
solicitud escribiendo directamente en la base de datos: llaman a :func:`cambiar_estado`,
que valida la transición y deja registro en la línea de tiempo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from portal import basedatos
from portal.modelos import (
    CambioEstado,
    NuevaSolicitud,
    NuevoSeguimiento,
    ResumenSla,
    Seguimiento,
    Solicitud,
    SolicitudDetalle,
)
from portal.servicios.tiempos_atencion import calcular_sla

# Transiciones permitidas. Una solicitud CERRADA o RECHAZADA es terminal.
TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "RECIBIDA": {"EN_REVISION"},
    "EN_REVISION": {"EN_PROCESO", "RECHAZADA"},
    "EN_PROCESO": {"RESUELTA"},
    "RESUELTA": {"CERRADA", "EN_PROCESO"},  # se puede reabrir si el problema persiste
    "CERRADA": set(),
    "RECHAZADA": set(),
}

ESTADOS_ABIERTOS = ("RECIBIDA", "EN_REVISION", "EN_PROCESO")
ESTADOS_CERRADOS = ("RESUELTA", "CERRADA", "RECHAZADA")


class TransicionInvalida(Exception):
    """Se intentó mover una solicitud a un estado al que no puede pasar."""

    def __init__(self, estado_actual: str, estado_destino: str) -> None:
        self.estado_actual = estado_actual
        self.estado_destino = estado_destino
        permitidos = TRANSICIONES_VALIDAS.get(estado_actual, set())
        detalle = ", ".join(sorted(permitidos)) if permitidos else "ninguno (estado final)"
        super().__init__(
            f"No se puede pasar de {estado_actual} a {estado_destino}. "
            f"Destinos válidos desde {estado_actual}: {detalle}."
        )


class SolicitudNoEncontrada(Exception):
    """No existe una solicitud con el identificador pedido."""

    def __init__(self, solicitud_id: int) -> None:
        self.solicitud_id = solicitud_id
        super().__init__(f"No existe la solicitud {solicitud_id}.")


# Consulta base reutilizada por el listado y el detalle: resuelve estudiante, categoría y
# funcionario en un solo viaje a la base de datos.
_SELECT_SOLICITUD = """
    SELECT s.id,
           s.codigo,
           s.asunto,
           s.descripcion,
           s.estado,
           s.prioridad,
           s.creada_en,
           s.actualizada_en,
           s.cerrada_en,
           e.id                                  AS estudiante_id,
           e.nombres || ' ' || e.apellidos       AS estudiante_nombre,
           e.codigo_estudiante                   AS estudiante_codigo,
           e.correo                              AS estudiante_correo,
           c.id                                  AS categoria_id,
           c.nombre                              AS categoria_nombre,
           c.sla_horas                           AS categoria_sla_horas,
           f.id                                  AS funcionario_id,
           f.nombre                              AS funcionario_nombre
      FROM solicitudes s
      JOIN estudiantes e ON e.id = s.estudiante_id
      JOIN categorias  c ON c.id = s.categoria_id
      LEFT JOIN funcionarios f ON f.id = s.funcionario_id
"""


def _adjuntar_sla(fila: dict[str, Any], ahora: datetime | None = None) -> Solicitud:
    """Convierte una fila en :class:`Solicitud` y le calcula el estado de SLA."""
    estado_sla = calcular_sla(
        creada_en=fila["creada_en"],
        horas_limite=fila["categoria_sla_horas"],
        cerrada_en=fila.get("cerrada_en"),
        ahora=ahora,
    )
    solicitud = Solicitud.model_validate(fila)
    solicitud.sla = ResumenSla(
        horas_transcurridas=estado_sla.horas_transcurridas,
        horas_limite=estado_sla.horas_limite,
        horas_restantes=estado_sla.horas_restantes,
        porcentaje_consumido=estado_sla.porcentaje_consumido,
        vencida=estado_sla.vencida,
        en_riesgo=estado_sla.en_riesgo,
        etiqueta=estado_sla.etiqueta,
    )
    return solicitud


async def listar_solicitudes(
    estado: str | None = None,
    categoria_id: int | None = None,
    funcionario_id: int | None = None,
    prioridad: str | None = None,
    busqueda: str | None = None,
    limite: int = 100,
) -> list[Solicitud]:
    """Devuelve las solicitudes que cumplen los filtros, de la más reciente a la más antigua.

    Args:
        estado: Filtra por un estado exacto. ``"ABIERTAS"`` agrupa los tres estados abiertos.
        categoria_id: Filtra por categoría.
        funcionario_id: Filtra por funcionario asignado.
        prioridad: Filtra por prioridad.
        busqueda: Texto libre que se busca en el asunto y en el código.
        limite: Máximo de filas a devolver.
    """
    condiciones: list[str] = []
    parametros: dict[str, Any] = {}

    if estado == "ABIERTAS":
        marcadores = ", ".join(f":estado_{i}" for i in range(len(ESTADOS_ABIERTOS)))
        condiciones.append(f"s.estado IN ({marcadores})")
        parametros.update({f"estado_{i}": v for i, v in enumerate(ESTADOS_ABIERTOS)})
    elif estado:
        condiciones.append("s.estado = :estado")
        parametros["estado"] = estado

    if categoria_id is not None:
        condiciones.append("s.categoria_id = :categoria_id")
        parametros["categoria_id"] = categoria_id

    if funcionario_id is not None:
        condiciones.append("s.funcionario_id = :funcionario_id")
        parametros["funcionario_id"] = funcionario_id

    if prioridad:
        condiciones.append("s.prioridad = :prioridad")
        parametros["prioridad"] = prioridad

    if busqueda:
        texto = busqueda.upper()
        condiciones.append(
            f"(UPPER(s.asunto) LIKE '%{texto}%' OR UPPER(s.codigo) LIKE '%{texto}%')"
        )

    sql = _SELECT_SOLICITUD
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY s.creada_en DESC FETCH FIRST :limite ROWS ONLY"
    parametros["limite"] = limite

    filas = await basedatos.consultar(sql, parametros)
    ahora = datetime.now()
    return [_adjuntar_sla(fila, ahora) for fila in filas]


async def obtener_solicitud(solicitud_id: int) -> SolicitudDetalle:
    """Devuelve una solicitud con su línea de tiempo.

    Raises:
        SolicitudNoEncontrada: Si el identificador no existe.
    """
    fila = await basedatos.consultar_uno(
        _SELECT_SOLICITUD + " WHERE s.id = :solicitud_id", {"solicitud_id": solicitud_id}
    )
    if fila is None:
        raise SolicitudNoEncontrada(solicitud_id)

    base = _adjuntar_sla(fila)
    seguimientos = await listar_seguimientos(solicitud_id)
    return SolicitudDetalle(**base.model_dump(), seguimientos=seguimientos)


async def listar_seguimientos(solicitud_id: int) -> list[Seguimiento]:
    """Devuelve la línea de tiempo de una solicitud, de la más antigua a la más reciente."""
    filas = await basedatos.consultar(
        "SELECT id, solicitud_id, autor, mensaje, es_interno, creado_en "
        "  FROM seguimientos "
        " WHERE solicitud_id = :solicitud_id "
        " ORDER BY creado_en",
        {"solicitud_id": solicitud_id},
    )
    return [Seguimiento.model_validate(fila) for fila in filas]


async def _siguiente_codigo() -> str:
    """Genera el siguiente código correlativo del año en curso (``SOL-2026-0151``)."""
    anio = datetime.now().year
    fila = await basedatos.consultar_uno(
        "SELECT NVL(MAX(TO_NUMBER(SUBSTR(codigo, 10))), 0) AS ultimo "
        "  FROM solicitudes "
        " WHERE codigo LIKE :patron",
        {"patron": f"SOL-{anio}-%"},
    )
    ultimo = int(fila["ultimo"]) if fila else 0
    return f"SOL-{anio}-{ultimo + 1:04d}"


async def crear_solicitud(datos: NuevaSolicitud) -> SolicitudDetalle:
    """Registra una solicitud nueva en estado ``RECIBIDA``."""
    codigo = await _siguiente_codigo()
    nuevo_id = await basedatos.ejecutar_con_retorno(
        "INSERT INTO solicitudes "
        "  (codigo, estudiante_id, categoria_id, asunto, descripcion, prioridad, estado) "
        "VALUES (:codigo, :estudiante_id, :categoria_id, :asunto, :descripcion, "
        "        :prioridad, 'RECIBIDA') "
        "RETURNING id INTO :nuevo_id",
        {
            "codigo": codigo,
            "estudiante_id": datos.estudiante_id,
            "categoria_id": datos.categoria_id,
            "asunto": datos.asunto,
            "descripcion": datos.descripcion,
            "prioridad": datos.prioridad,
        },
        variable_retorno="nuevo_id",
    )
    return await obtener_solicitud(int(nuevo_id))


async def cambiar_estado(solicitud_id: int, cambio: CambioEstado) -> SolicitudDetalle:
    """Mueve una solicitud a otro estado y lo registra en la línea de tiempo.

    Valida la transición contra :data:`TRANSICIONES_VALIDAS` antes de tocar la base de datos.
    Al pasar a un estado final se completa ``cerrada_en``.

    Raises:
        SolicitudNoEncontrada: Si el identificador no existe.
        TransicionInvalida: Si el estado destino no es alcanzable desde el actual.
    """
    actual = await basedatos.consultar_uno(
        "SELECT estado FROM solicitudes WHERE id = :solicitud_id",
        {"solicitud_id": solicitud_id},
    )
    if actual is None:
        raise SolicitudNoEncontrada(solicitud_id)

    estado_actual = actual["estado"]
    if cambio.estado not in TRANSICIONES_VALIDAS.get(estado_actual, set()):
        raise TransicionInvalida(estado_actual, cambio.estado)

    cierra = cambio.estado in ("CERRADA", "RECHAZADA")
    await basedatos.ejecutar(
        "UPDATE solicitudes "
        "   SET estado = :estado, "
        "       actualizada_en = SYSTIMESTAMP, "
        "       cerrada_en = CASE WHEN :cierra = 1 THEN SYSTIMESTAMP ELSE cerrada_en END "
        " WHERE id = :solicitud_id",
        {"estado": cambio.estado, "cierra": 1 if cierra else 0, "solicitud_id": solicitud_id},
    )

    mensaje = f"Estado cambiado de {estado_actual} a {cambio.estado}."
    if cambio.comentario:
        mensaje = f"{mensaje} {cambio.comentario}"
    await agregar_seguimiento(
        solicitud_id,
        NuevoSeguimiento(autor=cambio.autor, mensaje=mensaje, es_interno=False),
    )

    return await obtener_solicitud(solicitud_id)


async def agregar_seguimiento(solicitud_id: int, datos: NuevoSeguimiento) -> Seguimiento:
    """Agrega un comentario a la línea de tiempo de una solicitud.

    Raises:
        SolicitudNoEncontrada: Si el identificador no existe.
    """
    existe = await basedatos.consultar_uno(
        "SELECT id FROM solicitudes WHERE id = :solicitud_id", {"solicitud_id": solicitud_id}
    )
    if existe is None:
        raise SolicitudNoEncontrada(solicitud_id)

    nuevo_id = await basedatos.ejecutar_con_retorno(
        "INSERT INTO seguimientos (solicitud_id, autor, mensaje, es_interno) "
        "VALUES (:solicitud_id, :autor, :mensaje, :es_interno) "
        "RETURNING id INTO :nuevo_id",
        {
            "solicitud_id": solicitud_id,
            "autor": datos.autor,
            "mensaje": datos.mensaje,
            "es_interno": 1 if datos.es_interno else 0,
        },
        variable_retorno="nuevo_id",
    )

    await basedatos.ejecutar(
        "UPDATE solicitudes SET actualizada_en = SYSTIMESTAMP WHERE id = :solicitud_id",
        {"solicitud_id": solicitud_id},
    )

    fila = await basedatos.consultar_uno(
        "SELECT id, solicitud_id, autor, mensaje, es_interno, creado_en "
        "  FROM seguimientos WHERE id = :id",
        {"id": int(nuevo_id)},
    )
    return Seguimiento.model_validate(fila)


def estados_alcanzables(estado_actual: str) -> list[str]:
    """Devuelve los estados a los que se puede pasar desde ``estado_actual``.

    Lo usa la interfaz para mostrar solo los botones de acción que tienen sentido.
    """
    return sorted(TRANSICIONES_VALIDAS.get(estado_actual, set()))
