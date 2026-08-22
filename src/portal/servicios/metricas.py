"""Cifras agregadas que alimentan el panel de control.

Los conteos simples los resuelve Oracle con ``GROUP BY``. El estado de SLA, en cambio, se
calcula en Python: depende de horas hábiles y feriados, reglas que viven en
:mod:`portal.servicios.tiempos_atencion` y que no queremos duplicar en SQL.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from portal import basedatos
from portal.modelos import MetricasPanel
from portal.servicios.tiempos_atencion import calcular_sla

ESTADOS_ABIERTOS = ("RECIBIDA", "EN_REVISION", "EN_PROCESO")
ESTADOS_CERRADOS = ("RESUELTA", "CERRADA", "RECHAZADA")


async def _conteo_por_columna(columna: str) -> dict[str, int]:
    """Cuenta solicitudes agrupadas por una columna.

    ``columna`` no viene del usuario: la llama este módulo con valores fijos.
    """
    filas = await basedatos.consultar(
        f"SELECT {columna} AS clave, COUNT(*) AS total FROM solicitudes GROUP BY {columna}"
    )
    return {fila["clave"]: int(fila["total"]) for fila in filas}


async def _por_categoria() -> list[dict[str, Any]]:
    """Devuelve el total de solicitudes por categoría, de mayor a menor."""
    filas = await basedatos.consultar(
        "SELECT c.nombre AS categoria, "
        "       COUNT(s.id) AS total, "
        "       SUM(CASE WHEN s.estado IN ('RECIBIDA', 'EN_REVISION', 'EN_PROCESO') "
        "                THEN 1 ELSE 0 END) AS abiertas "
        "  FROM categorias c "
        "  LEFT JOIN solicitudes s ON s.categoria_id = c.id "
        " GROUP BY c.nombre "
        " ORDER BY total DESC"
    )
    return [
        {
            "categoria": fila["categoria"],
            "total": int(fila["total"]),
            "abiertas": int(fila["abiertas"] or 0),
        }
        for fila in filas
    ]


async def _carga_por_funcionario() -> list[dict[str, Any]]:
    """Devuelve cuántas solicitudes abiertas tiene cada funcionario activo."""
    marcadores = ", ".join(f":estado_{i}" for i in range(len(ESTADOS_ABIERTOS)))
    filas = await basedatos.consultar(
        "SELECT f.nombre AS funcionario, "
        "       f.area   AS area, "
        "       COUNT(s.id) AS abiertas "
        "  FROM funcionarios f "
        f"  LEFT JOIN solicitudes s ON s.funcionario_id = f.id AND s.estado IN ({marcadores}) "
        " WHERE f.activo = 1 "
        " GROUP BY f.nombre, f.area "
        " ORDER BY abiertas DESC",
        {f"estado_{i}": valor for i, valor in enumerate(ESTADOS_ABIERTOS)},
    )
    return [
        {
            "funcionario": fila["funcionario"],
            "area": fila["area"],
            "abiertas": int(fila["abiertas"]),
        }
        for fila in filas
    ]


async def _conteo_sla_abiertas() -> tuple[int, int]:
    """Cuenta cuántas solicitudes abiertas están vencidas y cuántas en riesgo."""
    marcadores = ", ".join(f":estado_{i}" for i in range(len(ESTADOS_ABIERTOS)))
    filas = await basedatos.consultar(
        "SELECT s.creada_en, c.sla_horas "
        "  FROM solicitudes s "
        "  JOIN categorias c ON c.id = s.categoria_id "
        f" WHERE s.estado IN ({marcadores})",
        {f"estado_{i}": valor for i, valor in enumerate(ESTADOS_ABIERTOS)},
    )

    ahora = datetime.now()
    vencidas = 0
    en_riesgo = 0
    for fila in filas:
        estado = calcular_sla(fila["creada_en"], int(fila["sla_horas"]), ahora=ahora)
        if estado.vencida:
            vencidas += 1
        elif estado.en_riesgo:
            en_riesgo += 1
    return vencidas, en_riesgo


async def obtener_metricas() -> MetricasPanel:
    """Reúne todas las cifras del panel de control."""
    por_estado = await _conteo_por_columna("estado")
    por_prioridad = await _conteo_por_columna("prioridad")
    por_categoria = await _por_categoria()
    carga = await _carga_por_funcionario()
    vencidas, en_riesgo = await _conteo_sla_abiertas()

    abiertas = sum(por_estado.get(estado, 0) for estado in ESTADOS_ABIERTOS)
    cerradas = sum(por_estado.get(estado, 0) for estado in ESTADOS_CERRADOS)
    total = (
        sum(por_estado.values())
        + sum(por_prioridad.values())
        + sum(fila["total"] for fila in por_categoria)
    )

    return MetricasPanel(
        total=total,
        abiertas=abiertas,
        cerradas=cerradas,
        vencidas=vencidas,
        en_riesgo=en_riesgo,
        por_estado=por_estado,
        por_categoria=por_categoria,
        por_prioridad=por_prioridad,
        carga_por_funcionario=carga,
    )
