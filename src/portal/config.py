"""Configuración de la aplicación, leída desde variables de entorno o del archivo .env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]


class Configuracion(BaseSettings):
    """Parámetros de ejecución del portal.

    Cada campo se puede sobrescribir con una variable de entorno con el prefijo
    ``PORTAL_``. Por ejemplo, ``bd_dsn`` se lee de ``PORTAL_BD_DSN``.
    """

    model_config = SettingsConfigDict(
        env_prefix="PORTAL_",
        env_file=RAIZ_PROYECTO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bd_usuario: str = "portal"
    bd_clave: str = "portal_upb_2026"
    bd_dsn: str = "localhost:1521/FREEPDB1"
    bd_pool_min: int = 1
    bd_pool_max: int = 8

    entorno: str = "desarrollo"

    @property
    def es_desarrollo(self) -> bool:
        return self.entorno == "desarrollo"


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Devuelve la configuración cacheada. Usar siempre esta función, no instanciar directo."""
    return Configuracion()
