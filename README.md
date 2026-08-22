# Taller de Claude Code - Portal de Atención al Estudiante

Universidad Privada Boliviana

Durante las próximas horas vas a trabajar sobre una aplicación real: FastAPI,
Oracle y una interfaz web. **La aplicación tiene problemas a propósito.** Encontrarlos y
resolverlos con Claude Code es exactamente el ejercicio.

No hace falta que sepas FastAPI ni Oracle. Justamente de eso se trata: así es como llega
un sistema que heredaste de otro equipo.

Solo necesitas [Docker Desktop](https://www.docker.com/products/docker-desktop/). Nada más:
todo corre dentro de un contenedor.

---

## Agenda

| # | Bloque |
|---|---|
| 0 | Puesta en marcha |
| 1 | Entender código que no escribiste |
| 2 | CLAUDE.md |
| 3 | Encontrar un bug de verdad |
| 4 | Una funcionalidad de punta a punta |
| 5 | Revisión de código |
| 6 | Git |

---

## Ejercicio 0 - Puesta en marcha

**Meta:** tener la aplicación corriendo y Claude Code abierto en el proyecto.

Levanta la base de datos y la aplicación (la primera vez carga los datos de ejemplo sola):

```bash
docker compose up -d --build
```

No necesitas instalar nada más: todo corre dentro de Docker. El código se monta como
volumen, así que al editar y guardar un archivo, el servidor se recarga solo.

Abre <http://localhost:8000> y date una vuelta: panel, listado, detalle de una solicitud.
Vas a ver la sigla **SLA** en varios lados: es el *plazo de atención*, el tiempo límite para
resolver una solicitud. Cada categoría tiene su propio límite: unas se resuelven en horas,
otras en días.

### Conéctate a Claude Code

En **otra** terminal, dentro de la carpeta del proyecto:

**macOS / Linux:**

```bash
ANTHROPIC_BASE_URL=http://research.upb.edu:8317 \
ANTHROPIC_AUTH_TOKEN=sk-DfyNPtUPMiLnctlPfazM8YLNwPyqKh1tQZRWiA4Wu7af3KPY \
ANTHROPIC_DEFAULT_OPUS_MODEL=Qwen3.8-27B \
ANTHROPIC_DEFAULT_SONNET_MODEL=Qwen3.8-27B \
ANTHROPIC_DEFAULT_HAIKU_MODEL=Qwen3.8-27B \
API_TIMEOUT_MS=120000 \
CLAUDE_CODE_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}' \
CLAUDE_CODE_EFFORT_LEVEL=low \
CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1 \
claude
```

**Windows (PowerShell):**

```powershell
Remove-Item Env:\ANTHROPIC_MODEL -ErrorAction SilentlyContinue; $env:ANTHROPIC_BASE_URL="http://research.upb.edu:8317"; $env:ANTHROPIC_AUTH_TOKEN="sk-DfyNPtUPMiLnctlPfazM8YLNwPyqKh1tQZRWiA4Wu7af3KPY"; $env:ANTHROPIC_DEFAULT_OPUS_MODEL="Qwen3.8-27B"; $env:ANTHROPIC_DEFAULT_SONNET_MODEL="Qwen3.8-27B"; $env:ANTHROPIC_DEFAULT_HAIKU_MODEL="Qwen3.8-27B"; $env:API_TIMEOUT_MS="120000"; $env:CLAUDE_CODE_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}'; $env:CLAUDE_CODE_EFFORT_LEVEL="low"; $env:CLAUDE_CODE_ALWAYS_ENABLE_EFFORT="1"; claude
```

Para usar el otro endpoint, cambia solo `ANTHROPIC_BASE_URL` (o `$env:ANTHROPIC_BASE_URL`)
a `https://eu-begp.upb.edu/llmproxy`.

### Primer prompt

Con Claude Code ya abierto, puedes probar:

> Dame un recorrido de este proyecto: qué hace y cómo está organizado. No cambies nada.

**Qué observar:** Claude lee el repositorio por su cuenta. No hace falta que le pegues
archivos.

---

## Ejercicio 1 - Entender código que no escribiste

**Meta:** usar Claude Code como la herramienta que más vas a usar en el trabajo real:
entender un módulo que nadie documentó.

Abre `src/portal/servicios/tiempos_atencion.py` y míralo unos segundos. Pruebas a hacer:

> Explícame qué hace `src/portal/servicios/tiempos_atencion.py`

Y recién ahora, que ya entendiste el módulo:

> Agrégale comentarios a `tiempos_atencion.py`, explicando cada función y las
> constantes

---

## Ejercicio 2 - CLAUDE.md

**Meta:** fijar los estándares del equipo en un archivo, en vez de repetírselos a Claude
en cada sesión.

Este proyecto no tiene un `CLAUDE.md`. Es el archivo que Claude lee al arrancar en cada
sesión: ahí van las convenciones del equipo. Sin él, cada persona le explica las mismas
reglas a Claude una y otra vez.

Créalo a partir del código, no de memoria:

> Crea un CLAUDE.md para este proyecto.

Revisa lo que propone.

**Qué observar:**
- Un `CLAUDE.md` útil nace de leer el código, no de reglas genéricas de manual. Por eso
  vale la pena pedirle a Claude que investigue antes de escribir.

---

## Ejercicio 3 - Encontrar un bug de verdad

**Meta:** ir de un síntoma a una causa raíz, con una prueba que lo demuestre.

### El reporte

Llega este ticket a la mesa de ayuda:

> «El panel dice que tenemos 20 solicitudes con SLA vencido, pero yo conté más a mano.
> Y hay solicitudes que muestran tiempo transcurrido **negativo**.»

### Reproducirlo

En el navegador, escribe `-015` en el buscador del listado. Salen las últimas seis
solicitudes, cuyos códigos terminan en `0151` a `0156`. Abre cualquiera de ellas y mira el
recuadro de **SLA** en la columna derecha.

Anota lo que ves antes de seguir.

### Diagnosticarlo

> En la solicitud <PEGA AQUÍ EL CÓDIGO> el tiempo transcurrido sale negativo, y las horas
> restantes son más que el límite de la categoría. Investiga por qué pasa esto. No
> corrijas nada todavía, primero explícame la causa.

Pon el código y el valor exacto que ves en pantalla: mientras más concreto el síntoma,
mejor el diagnóstico.

Cuando estés de acuerdo con el diagnóstico:

> Escribe una prueba en `tests/test_tiempos_atencion.py` que falle por este bug. Solo la prueba.

Córrela y confirma que falla:

```bash
docker compose exec app uv run pytest tests/test_tiempos_atencion.py -v
```

### Corregirlo

> Ahora corrige el bug. La prueba debe pasar y las demás deben seguir pasando.

```bash
docker compose exec app uv run pytest
```

Recarga el navegador y vuelve a mirar la solicitud y el panel.

**Qué observar:**
- Darle el síntoma concreto («horas transcurridas negativas en esta solicitud») rinde
  mucho más que «el plazo de atención está mal».
- Pedir la prueba **antes** que la corrección demuestra que el bug existe y que quedó
  resuelto. Sin eso, solo tienes la palabra del modelo.
- Compara el conteo de «SLA vencido» del panel antes y después.

---

## Ejercicio 4 - Una funcionalidad de punta a punta

**Meta:** un cambio que toca toda la aplicación, no solo una parte: la base de datos, el
código del servidor, la página que ves en el navegador y una prueba que lo confirme.

### Lo que falta

Ahora mismo una solicitud queda asignada a un funcionario solo cuando se cargan los datos
de ejemplo. Desde la aplicación **no hay forma de asignarla ni de cambiarle el responsable**.
Ábrete cualquier solicitud y búscalo: en «Datos» ves «Asignada a», pero no puedes editarlo.

### Construirlo

Pulsa `Shift+Tab` hasta que aparezca **plan mode**. En ese modo Claude investiga y propone,
pero no edita nada hasta que apruebes. Empieza ahí:

> Quiero poder asignar y reasignar una solicitud a un funcionario desde la página de
> detalle. El cambio debe quedar registrado en la línea de tiempo, diciendo quién la
> reasignó y a quién. Planifícalo de punta a punta.

Revisa el plan. Verifica que contemple:

- función nueva en `src/portal/servicios/solicitudes.py`
- endpoint nuevo en `src/portal/rutas/solicitudes.py`
- control en `src/portal/plantillas/solicitud_detalle.html`
- manejador en `src/portal/estaticos/app.js`
- prueba en `tests/`

Apruébalo y déjalo trabajar. Después pruébalo en el navegador de verdad.

**Qué observar:**
- Con plan mode, el trabajo grande se revisa antes de existir, no después.
- No hace falta tocar el esquema: la columna `funcionario_id` y la tabla `seguimientos` ya
  están. Que Claude lo note por su cuenta es buena señal.
- Pruébalo en el navegador. Que las pruebas pasen no garantiza que la interfaz funcione.

---

## Ejercicio 5 - Revisión de código

**Meta:** revisar el código automáticamente y decidir qué hallazgos vale la
pena corregir.

### Revisiones

```
/code-review
```

Lee los hallazgos uno por uno. Decide cuáles aceptas: no todo hallazgo merece un cambio.

---

## Ejercicio 6 - Git

**Meta:** cerrar el círculo dejando el trabajo del taller en una rama con su commit.

> Crea una rama con todo lo que hicimos hoy y haz commit con un mensaje descriptivo

---

## Tips

| Atajo | Qué hace |
|---|---|
| `Shift+Tab` | Cambia de modo (normal → auto-aceptar → plan) |
| `Esc` | Interrumpe a Claude mientras trabaja |
| `Esc` `Esc` | Vuelve atrás a un mensaje anterior |
| `/clear` | Limpia el contexto y empieza de cero |
| `/undo` | Deshace el último cambio en archivos |
| `#` al inicio | Guarda algo en la memoria del proyecto |
| `@archivo` | Menciona un archivo concreto |
| `!comando` | Corre un comando de shell directamente |

---

## Stack y estructura

- **Backend:** FastAPI + Python 3.12
- **Base de datos:** Oracle Database 23ai Free (en contenedor)
- **Frontend:** Jinja2 + CSS + JavaScript nativo (sin build ni npm)

```
src/portal/
├── main.py           Aplicación FastAPI
├── config.py         Configuración
├── basedatos.py      Pool de Oracle
├── modelos.py        Modelos Pydantic
├── rutas/            Vistas HTML y endpoints de la API
├── servicios/        Lógica de negocio (estados, plazo de atención, métricas)
├── plantillas/       Plantillas Jinja2
└── estaticos/        CSS y JavaScript

bd/01_esquema.sql     Esquema de la base de datos
Dockerfile            Imagen de la app (Python + dependencias)
docker-compose.yml    Servicios: base de datos y aplicación
```
