"""API REST de los catálogos: estudiantes, categorías y funcionarios.

Son datos de referencia, de solo lectura desde la aplicación. Alimentan los desplegables
del formulario de registro y los filtros del listado.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from portal import basedatos
from portal.modelos import Categoria, Estudiante, Funcionario

router = APIRouter(prefix="/api", tags=["catálogos"])


@router.get("/categorias", response_model=list[Categoria], summary="Listar categorías")
async def listar_categorias() -> list[Categoria]:
    """Devuelve las categorías de atención con su SLA en horas hábiles."""
    filas = await basedatos.consultar(
        "SELECT id, nombre, descripcion, sla_horas FROM categorias ORDER BY nombre"
    )
    return [Categoria.model_validate(fila) for fila in filas]


@router.get("/funcionarios", response_model=list[Funcionario], summary="Listar funcionarios")
async def listar_funcionarios(
    solo_activos: bool = Query(default=True),
) -> list[Funcionario]:
    """Devuelve el personal que atiende las solicitudes."""
    sql = "SELECT id, nombre, correo, area, activo FROM funcionarios"
    parametros: dict[str, object] = {}
    if solo_activos:
        sql += " WHERE activo = :activo"
        parametros["activo"] = 1
    sql += " ORDER BY nombre"

    filas = await basedatos.consultar(sql, parametros)
    return [Funcionario.model_validate(fila) for fila in filas]


@router.get("/estudiantes", response_model=list[Estudiante], summary="Listar estudiantes")
async def listar_estudiantes(
    busqueda: str | None = Query(default=None, description="Busca por nombre, apellido o código"),
    limite: int = Query(default=50, ge=1, le=200),
) -> list[Estudiante]:
    """Devuelve los estudiantes, con búsqueda opcional por nombre o código."""
    sql = (
        "SELECT id, codigo_estudiante, nombres, apellidos, correo, carrera, semestre, activo "
        "  FROM estudiantes"
    )
    parametros: dict[str, object] = {}

    if busqueda:
        sql += (
            " WHERE UPPER(nombres) LIKE :busqueda"
            "    OR UPPER(apellidos) LIKE :busqueda"
            "    OR UPPER(codigo_estudiante) LIKE :busqueda"
        )
        parametros["busqueda"] = f"%{busqueda.upper()}%"

    sql += " ORDER BY apellidos, nombres FETCH FIRST :limite ROWS ONLY"
    parametros["limite"] = limite

    filas = await basedatos.consultar(sql, parametros)
    return [Estudiante.model_validate(fila) for fila in filas]
