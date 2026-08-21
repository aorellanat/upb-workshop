# Portal de Atención al Estudiante — UPB

Aplicación de práctica diseñada para el taller de cómo usar **Claude Code** en el desarrollo real.

Una aplicación FastAPI + Oracle que gestiona solicitudes de atención de estudiantes: registro, clasificación, asignación y seguimiento de SLA. El código contiene defectos intencionales para que practiques encontrarlos y repararlos con Claude Code.

> **Antes de usar este código:** Empieza por [`taller/GUIA.md`](taller/GUIA.md) — es una guía con 6 ejercicios progresivos.

---

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — es lo único que necesitas.

No hace falta instalar Python ni `uv`: la aplicación corre dentro de un contenedor que ya
trae todo lo necesario.

---

## Guía rápida

**Verifica que todo esté listo:**

```bash
python verificar_entorno.py  # funciona en Windows, Mac, Linux
```

**Luego levanta todo (base de datos + aplicación):**

```bash
docker compose up -d --build                    # primer arranque de Oracle: 1-2 min
docker compose exec app uv run inicializar-bd    # solo la primera vez
```

Abre <http://localhost:8000>.

El código en `src/` se monta dentro del contenedor: al editar y guardar un archivo, el
servidor se recarga solo — igual que en un entorno local.

---

## Stack

- **Backend:** FastAPI + Python 3.12
- **Base de datos:** Oracle Database 23ai Free (en contenedor)
- **Frontend:** Jinja2 + CSS + JavaScript nativo (sin build ni npm)

---

## Estructura

```
src/portal/
├── main.py           Aplicación FastAPI
├── config.py         Configuración
├── basedatos.py      Pool de Oracle
├── modelos.py        Modelos Pydantic
├── rutas/            Vistas HTML y endpoints de la API
├── servicios/        Lógica de negocio (estados, SLA, métricas)
├── plantillas/       Plantillas Jinja2
└── estaticos/        CSS y JavaScript

bd/01_esquema.sql     Esquema de la base de datos
taller/               Guía y ejercicios
Dockerfile            Imagen de la app (Python + dependencias)
docker-compose.yml    Servicios: base de datos y aplicación
```
