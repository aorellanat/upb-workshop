#!/usr/bin/env python3
"""Verifica que el equipo esté listo para el taller de Claude Code.

Uso: python verificar_entorno.py (o ./verificar_entorno.py en Unix)

No modifica nada: solo revisa e informa.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from colorama import init, Fore, Style

    init(autoreset=True)
except ImportError:
    # Fallback si colorama no está instalado
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""

    class Style:
        BRIGHT = ""
        RESET_ALL = ""


VERDE = f"{Fore.GREEN}{Style.BRIGHT}"
ROJO = f"{Fore.RED}{Style.BRIGHT}"
AMARILLO = f"{Fore.YELLOW}{Style.BRIGHT}"
FIN = Style.RESET_ALL

fallos = 0
avisos = 0


def ok(mensaje: str) -> None:
    print(f"  {VERDE}✔{FIN} {mensaje}")


def error(mensaje: str, detalle: str) -> None:
    global fallos
    print(f"  {ROJO}✘{FIN} {mensaje}")
    print(f"      → {detalle}")
    fallos += 1


def aviso(mensaje: str, detalle: str) -> None:
    global avisos
    print(f"  {AMARILLO}!{FIN} {mensaje}")
    print(f"      → {detalle}")
    avisos += 1


def titulo(texto: str) -> None:
    print(f"\n{Style.BRIGHT}{texto}{FIN}")


def comando_existe(nombre: str) -> bool:
    """Verifica si un comando está disponible en el PATH."""
    return shutil.which(nombre) is not None


def ejecutar_comando(
    cmd: list[str], captura: bool = True, timeout: int = 5
) -> tuple[bool, str]:
    """Ejecuta un comando y devuelve (éxito, salida).

    Maneja correctamente las rutas en Windows, macOS y Linux.
    """
    try:
        resultado = subprocess.run(
            cmd,
            capture_output=captura,
            text=True,
            timeout=timeout,
            shell=False,  # Nunca usar shell=True por seguridad
        )
        return resultado.returncode == 0, resultado.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except FileNotFoundError:
        return False, "Comando no encontrado"
    except Exception as e:
        return False, str(e)


def main() -> None:
    global fallos, avisos

    print(f"{Style.BRIGHT}Verificación del entorno — Taller Claude Code UPB{FIN}")

    # --- Herramientas --------------------------------------------------------
    titulo("Herramientas")

    if comando_existe("docker"):
        _, version = ejecutar_comando(["docker", "--version"])
        if version:
            version = version.split()[-1].rstrip(",")
            ok(f"Docker instalado ({version})")

        exito, _ = ejecutar_comando(["docker", "info"])
        if exito:
            ok("El daemon de Docker está corriendo")
        else:
            error(
                "Docker está instalado pero no responde",
                "Abre Docker Desktop y espera a que arranque.",
            )
    else:
        error(
            "Docker no está instalado",
            "Instálalo desde https://www.docker.com/products/docker-desktop/",
        )

    if comando_existe("claude"):
        ok("Claude Code instalado")
    else:
        if platform.system() == "Windows":
            instalar = "winget install Anthropic.Claude"
        else:
            instalar = "curl https://install.claude.ai | bash"
        aviso(
            "Claude Code no está en el PATH",
            f"Instálalo con: {instalar} (no necesitas npm ni Node.js).",
        )

    if comando_existe("git"):
        ok("git instalado")
    else:
        error(
            "git no está instalado",
            "Instálalo con: https://git-scm.com/",
        )

    # --- Proyecto ------------------------------------------------------------
    titulo("Proyecto")

    proyecto_dir = Path(__file__).resolve().parent

    venv_dir = proyecto_dir / ".venv"
    if venv_dir.exists():
        ok("Dependencias instaladas (.venv)")
    else:
        aviso(
            "No hay un entorno local (.venv)",
            "No hace falta: la aplicación corre en Docker. Solo instala dependencias "
            "localmente (uv sync --extra dev) si prefieres correrla fuera de Docker.",
        )

    # --- Base de datos -------------------------------------------------------
    titulo("Base de datos")

    imagen = "gvenzl/oracle-free:23-slim-faststart"

    exito, _ = ejecutar_comando(["docker", "image", "inspect", imagen])
    if exito:
        ok("Imagen de Oracle descargada")
    else:
        error(
            "Falta la imagen de Oracle (~2 GB)",
            f"Descárgala con: docker pull {imagen}",
        )

    exito, estado = ejecutar_comando(
        ["docker", "inspect", "-f", "{{.State.Health.Status}}", "portal_oracle"]
    )

    if estado == "healthy":
        ok("El contenedor de Oracle está sano")

        if venv_dir.exists():
            # Verificar conexión a Oracle y datos
            script_python = (
                "import sys; "
                "from portal.config import obtener_configuracion; "
                "import oracledb; "
                "c = obtener_configuracion(); "
                "try: con = oracledb.connect(user=c.bd_usuario, password=c.bd_clave, dsn=c.bd_dsn); "
                "except Exception as e: print(e, file=sys.stderr); sys.exit(1); "
                "with con.cursor() as cur: "
                "  try: cur.execute('SELECT COUNT(*) FROM solicitudes'); print(cur.fetchone()[0]); "
                "  except Exception: sys.exit(2)"
            )

            try:
                # Ejecutar Python directamente con -c en lugar de archivo temporal
                exito, salida = ejecutar_comando(
                    ["python", "-c", script_python], timeout=10
                )
                if exito:
                    try:
                        conteo = int(salida.strip().split("\n")[-1])
                        ok(f"Datos cargados ({conteo} solicitudes)")
                    except (ValueError, IndexError):
                        error(
                            "No se pudo leer el conteo de solicitudes",
                            "Revisa la configuración de Oracle.",
                        )
                else:
                    error(
                        "No se pudo conectar a Oracle desde Python",
                        "Revisa PORTAL_BD_DSN en tu .env o instala dependencias con: uv sync --extra dev",
                    )
            except Exception as e:
                error(
                    "Error al verificar Oracle",
                    f"Detalle: {e}",
                )

    elif estado == "starting":
        aviso(
            "El contenedor de Oracle está arrancando",
            "Espera un minuto y vuelve a ejecutar este script.",
        )

    elif estado == "unhealthy":
        error(
            "El contenedor de Oracle está en mal estado",
            "Revísalo con: docker compose logs oracle",
        )

    else:
        aviso(
            "El contenedor de Oracle no está levantado",
            "Levántalo con: docker compose up -d",
        )

    # --- Resumen -------------------------------------------------------------
    print()
    if fallos == 0 and avisos == 0:
        print(f"{Style.BRIGHT}{VERDE}Todo listo para el taller.{FIN}")
    elif fallos == 0:
        print(f"{Style.BRIGHT}{AMARILLO}Casi listo:{FIN} {avisos} aviso(s) por revisar.")
    else:
        print(f"{Style.BRIGHT}{ROJO}Faltan cosas:{FIN} {fallos} error(es) y {avisos} aviso(s).")
        print("Resuelve los errores siguiendo las flechas y vuelve a ejecutar este script.")

    sys.exit(fallos)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerificación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{ROJO}Error inesperado:{FIN} {e}")
        sys.exit(1)
