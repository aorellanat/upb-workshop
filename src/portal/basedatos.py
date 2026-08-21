"""Acceso a Oracle: pool de conexiones y ayudantes de consulta.

Todo el acceso a datos del portal pasa por este módulo. Las funciones ``consultar``,
``consultar_uno`` y ``ejecutar`` reciben los parámetros por separado y los envían como
*bind variables*, nunca interpolados en el texto del SQL.

Usamos ``python-oracledb`` en modo *thin*: conecta directo a Oracle sin necesidad de
instalar el Oracle Instant Client.
"""

from __future__ import annotations

import logging
from typing import Any

import oracledb

from portal.config import obtener_configuracion

_log = logging.getLogger(__name__)

_pool: oracledb.AsyncConnectionPool | None = None


async def iniciar_pool() -> None:
    """Crea el pool de conexiones. Se llama una sola vez, al arrancar la aplicación."""
    global _pool
    if _pool is not None:
        return

    config = obtener_configuracion()
    _pool = oracledb.create_pool_async(
        user=config.bd_usuario,
        password=config.bd_clave,
        dsn=config.bd_dsn,
        min=config.bd_pool_min,
        max=config.bd_pool_max,
        increment=1,
    )
    _log.info("Pool de Oracle creado sobre %s", config.bd_dsn)


async def cerrar_pool() -> None:
    """Cierra el pool de conexiones al apagar la aplicación."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        _log.info("Pool de Oracle cerrado")


def obtener_pool() -> oracledb.AsyncConnectionPool:
    """Devuelve el pool activo. Falla si la aplicación todavía no arrancó."""
    if _pool is None:
        raise RuntimeError(
            "El pool de Oracle no está iniciado. ¿Olvidaste llamar a iniciar_pool()?"
        )
    return _pool


def _filas_como_diccionarios(cursor: Any) -> None:
    """Hace que el cursor devuelva diccionarios con las claves en minúscula."""
    columnas = [d.name.lower() for d in cursor.description]

    def constructor(*valores):
        return dict(zip(columnas, valores, strict=True))

    cursor.rowfactory = constructor


async def consultar(sql: str, parametros: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Ejecuta un SELECT y devuelve todas las filas como diccionarios.

    Args:
        sql: Sentencia SELECT con marcadores de bind (``:nombre``).
        parametros: Valores para los marcadores. Nunca se interpolan en el texto del SQL.

    Ejemplo:
        >>> await consultar(
        ...     "SELECT id, asunto FROM solicitudes WHERE estado = :estado",
        ...     {"estado": "RECIBIDA"},
        ... )
    """
    async with obtener_pool().acquire() as conexion:
        with conexion.cursor() as cursor:
            await cursor.execute(sql, parametros or {})
            _filas_como_diccionarios(cursor)
            return await cursor.fetchall()


async def consultar_uno(
    sql: str, parametros: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Ejecuta un SELECT y devuelve la primera fila, o ``None`` si no hay resultados."""
    async with obtener_pool().acquire() as conexion:
        with conexion.cursor() as cursor:
            await cursor.execute(sql, parametros or {})
            _filas_como_diccionarios(cursor)
            return await cursor.fetchone()


async def ejecutar(sql: str, parametros: dict[str, Any] | None = None) -> int:
    """Ejecuta un INSERT, UPDATE o DELETE y confirma la transacción.

    Returns:
        Cantidad de filas afectadas.
    """
    async with obtener_pool().acquire() as conexion:
        with conexion.cursor() as cursor:
            await cursor.execute(sql, parametros or {})
            filas = cursor.rowcount
            await conexion.commit()
            return filas


async def ejecutar_con_retorno(sql: str, parametros: dict[str, Any], variable_retorno: str) -> Any:
    """Ejecuta un INSERT con cláusula RETURNING y devuelve el valor generado.

    Se usa para recuperar el ``id`` de una fila recién insertada.

    Args:
        sql: INSERT que termina en ``RETURNING <col> INTO :<variable_retorno>``.
        parametros: Valores de los binds de entrada.
        variable_retorno: Nombre del bind de salida declarado en el RETURNING.
    """
    async with obtener_pool().acquire() as conexion:
        with conexion.cursor() as cursor:
            salida = cursor.var(oracledb.NUMBER)
            await cursor.execute(sql, {**parametros, variable_retorno: salida})
            await conexion.commit()
            return salida.getvalue()[0]


async def verificar_conexion() -> bool:
    """Comprueba que la base de datos responde. Se usa en el endpoint /salud."""
    try:
        fila = await consultar_uno("SELECT 1 AS uno FROM dual")
        return fila is not None and fila["uno"] == 1
    except Exception:
        _log.exception("Falló la verificación de conexión a Oracle")
        return False
