# Taller de Claude Code - Portal de Atención al Estudiante

Universidad Privada Boliviana

Durante las próximas horas vas a trabajar sobre una aplicación real: FastAPI,
Oracle y una interfaz web. **La aplicación tiene problemas a propósito.** Encontrarlos y
resolverlos con Claude Code es exactamente el ejercicio.

No hace falta que sepas FastAPI ni Oracle. Justamente de eso se trata: así es como llega
un sistema que heredaste de otro equipo.

---

## Requisitos previos

Instala estas tres herramientas antes de empezar. No necesitas nada más: la aplicación
corre dentro de un contenedor.

| Herramienta | Para qué | Descarga |
|---|---|---|
| Git | Clonar el repositorio y versionar tu trabajo | <https://git-scm.com/downloads> |
| Visual Studio Code | Editar el código y leer los archivos del proyecto | <https://code.visualstudio.com/download> |
| Docker Desktop | Levantar la base de datos y la aplicación | <https://www.docker.com/products/docker-desktop/> |

Deja Docker Desktop abierto y corriendo antes del Ejercicio 0.

### Instala Claude Code

**macOS, Linux, WSL:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://claude.ai/install.ps1 | iex
```

**Windows (CMD):**

```
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Cierra y vuelve a abrir la terminal, y comprueba que quedó instalado:

```bash
claude --version
```

---

## Agenda

| Bloque | Contenido |
|---|---|
| Puesta en marcha | Levantar la aplicación y conectar Claude Code |
| Primeros pasos con Claude | Entender código nuevo, documentarlo, refactorizarlo, limpiar valores hardcodeados y arreglar un bug |
| Ejercicio 1 | `CLAUDE.md` |
| Ejercicio 2 | Crear y usar una skill |
| Ejercicio 3 | Crear y usar un comando |
| Ejercicio 4 | Una funcionalidad de punta a punta (planning) |
| Ejercicio 5 | Revisión de código del feature implementado |
| Ejercicio 6 | Conectar Claude a la base de datos (MCP) |
| Cierre | Dejar el trabajo en una rama con commit (Git) |

---

## Puesta en marcha

**Meta:** tener la aplicación corriendo y Claude Code abierto en el proyecto.

Clona el repositorio y entra en la carpeta:

```bash
git clone https://github.com/aorellanat/upb-workshop.git
cd upb-workshop
```

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

```
Dame un recorrido de este proyecto: qué hace y cómo está organizado. No cambies nada.
```

**Qué observar:** Claude lee el repositorio por su cuenta. No hace falta que le pegues
archivos.

---

## Primeros pasos con Claude

**Meta:** pasar por el flujo básico de trabajar con Claude Code sobre código ajeno, antes de
meterte a los ejercicios grandes: entenderlo, documentarlo, dejarlo más legible, sacarle los
valores hardcodeados y arreglarle un bug.

### Preguntar sobre un código que nunca viste

Usa Claude Code para entender un módulo que nadie documentó.

Abre `src/portal/servicios/tiempos_atencion.py` y míralo unos segundos. Después:

```
Explícame qué hace src/portal/servicios/tiempos_atencion.py
```

**Qué observar:** Claude puede explicar el código antes de que tú lo entiendas del todo. Es
el punto de partida para todo lo que sigue en este bloque.

### Documentar funciones

Y recién ahora, que ya entendiste el módulo:

```
Agrégale comentarios a tiempos_atencion.py, explicando cada función y las constantes
```

**Qué observar:** documentar antes de tocar el código te obliga a confirmar que entendiste
bien. Si algo del comentario que propone Claude no te cierra, es señal de que hay que
preguntar más antes de seguir.

### Refactorizar código

**Meta:** mejorar la legibilidad de un código que ya entendiste, sin alterar lo que hace.
Esa es la disciplina básica de cualquier refactor.

Nombres como `HI`, `HF`, `FF`, `_v`, `d`, `u`, `r`, `t0`, `t1` tienen sentido para quien lo
escribió. Para todos los demás, no.

Antes de tocar nada, abre cualquier solicitud abierta en el navegador y anota lo que
muestra el recuadro de **SLA**: horas transcurridas y porcentaje consumido. Vas a comparar
contra esto después.

```
Refactoriza src/portal/servicios/tiempos_atencion.py: dale nombres claros a las variables y
funciones, y ordena la lógica en pasos entendibles. No cambies ninguna regla de negocio ni
ningún resultado de cálculo, solo la legibilidad.
```

Recarga esa misma solicitud y compara el SLA contra lo que anotaste. Tiene que ser idéntico.

### Buenas prácticas: limpieza de variables hardcodeadas

```
Revisa src/portal/config.py. bd_clave tiene una contraseña como valor por defecto en el
código fuente. Corrígelo: la credencial no debería tener un valor por defecto en el código,
sino leerse desde un archivo .env.
```

Antes de aceptar el cambio, confirma que `docker compose up` sigue funcionando igual: las
credenciales ya le llegan por variables de entorno desde `docker-compose.yml`, así que
sacarlas del código no debería romper nada.

### Describir un bug y arreglarlo

#### El reporte

Llega este ticket a la mesa de ayuda:

> «El panel de control no cuadra: el total de solicitudes es mucho más alto que lo que
> suman abiertas y cerradas.»

#### Reproducirlo

Abre el panel (`http://localhost:8000`) y mira las cuatro tarjetas de arriba: **Total**,
**Abiertas**, **Vencidas**, **Cerradas**. Suma Abiertas + Cerradas a mano y compárala con
Total.

#### Diagnosticarlo

```
En el panel de control, el número de "Total" no coincide con la suma de "Abiertas" más
"Cerradas". Investiga por qué. No corrijas nada todavía, primero explícame la causa.
```

Cuando estés de acuerdo con el diagnóstico:

```
Corrígelo.
```

Recarga el panel y confirma que Abiertas + Cerradas ahora sí coincide con Total.

---

## Ejercicio 1 - CLAUDE.md

**Meta:** fijar los estándares del equipo en un archivo, en vez de repetírselos a Claude
en cada sesión.

Este proyecto no tiene un `CLAUDE.md`. Es el archivo que Claude lee al arrancar en cada
sesión: ahí van las convenciones del equipo. Sin él, cada persona le explica las mismas
reglas a Claude una y otra vez.

Créalo a partir del código, no de memoria:

```
Crea un CLAUDE.md para este proyecto.
```

Revisa lo que propone.

**Qué observar:**
- Un `CLAUDE.md` útil nace de leer el código, no de reglas genéricas de manual. Por eso
  vale la pena pedirle a Claude que investigue antes de escribir.

---

## Ejercicio 2 - Crear y usar una skill

**Meta:** empaquetar un procedimiento que se repite en una **skill**, para no tener que
explicárselo a Claude de cero cada vez.

Dirección Académica pide seguido un reporte en PDF de los problemas del panel, las
solicitudes vencidas y en riesgo, y hasta ahora alguien tiene que armarlo a mano cada vez:
copiar los datos, pegar el logo, acomodar el formato. Es el tipo de pedido que conviene
empaquetar, no formatear de nuevo cada vez.

```
Crea una skill llamada reporte-pdf. Cuando le pida un reporte de los problemas del panel de
control, debe generar un PDF con las solicitudes vencidas y en riesgo, agrupadas por
categoría. El PDF siempre debe llevar el logo de src/portal/assets/upb-logo.png y decir
"Universidad Privada Boliviana", sin que yo tenga que pedirlo cada vez. Guarda el PDF en una
carpeta reportes/ en la raíz del repo (agrégala al .gitignore), no en un directorio temporal.
```

Revisa el archivo que crea Claude (algo como `.claude/skills/reporte-pdf/SKILL.md`): fíjate
en la descripción, que es lo que Claude usa para decidir cuándo activarla sola. El proyecto
ya trae instalada `fpdf2` para armar el PDF.

Úsala:

```
/reporte-pdf
```

Abre el PDF que genera en `reportes/` y confirma que el logo y el nombre de la universidad
están ahí.

---

## Ejercicio 3 - Crear y usar un comando

**Meta:** crear un **comando** para una acción puntual que tú mismo disparas, a diferencia
de la skill del ejercicio anterior, que Claude decide cuándo usar.

```
Crea un comando /documentar que reciba la ruta de un script como argumento y le agregue
documentación: qué hace el archivo, qué hace cada función, y qué reciben y devuelven.
```

Revisa el archivo que crea Claude (algo como `.claude/commands/documentar.md`). Úsalo sobre
un script que todavía no tiene mucha documentación:

```
/documentar src/portal/inicializar_bd.py
```

---

## Ejercicio 4 - Una funcionalidad de punta a punta

**Meta:** un cambio que toca toda la aplicación, no solo una parte: la base de datos, el
código del servidor, la página que ves en el navegador y una prueba que lo confirme.

### Lo que falta

El portal no tiene ninguna forma de recoger la opinión de un estudiante. No hay encuesta de
satisfacción ni un canal para dejar una queja: si algo salió mal, no tiene dónde decirlo.

### Construirlo

Pulsa `Shift+Tab` hasta que aparezca **plan mode**. En ese modo Claude investiga y propone,
pero no edita nada hasta que apruebes. Empieza ahí:

```
Quiero agregar una encuesta de satisfacción al portal. Necesito un botón junto a "Panel" en
la barra de navegación que lleve a un formulario simple donde cualquier estudiante pueda
calificar su experiencia (1 a 5) y dejar un comentario libre que también sirva para
registrar una queja. No hace falta vincularlo a una solicitud existente ni a un estudiante
registrado: nombre y correo son opcionales. Planifícalo de punta a punta.
```

Revisa el plan. Verifica que contemple:

- tabla nueva `encuestas` en `bd/01_esquema.sql`
- modelos nuevos en `src/portal/modelos.py`
- servicio nuevo en `src/portal/servicios/encuestas.py`
- endpoint nuevo en `src/portal/rutas/encuestas.py`
- vista y plantilla nuevas (`src/portal/rutas/vistas.py` y una plantilla en `src/portal/plantillas/`)
- botón en `src/portal/plantillas/base.html`
- manejador en `src/portal/estaticos/app.js`
- prueba en `tests/`

Apruébalo y déjalo trabajar. Después pruébalo en el navegador de verdad.

---

## Ejercicio 5 - Revisión de código del feature implementado

**Meta:** revisar automáticamente lo que acabas de construir en el ejercicio anterior y
decidir qué hallazgos vale la pena corregir.

```
/code-review
```

Lee los hallazgos uno por uno. Decide cuáles aceptas: no todo hallazgo merece un cambio.

---

## Ejercicio 6 - Conectar Claude a la base de datos (MCP)

**Meta:** darle a Claude una herramienta que no tenía, una base de datos real, y usarla
para resolver un pedido como los que llegan de verdad: un reporte para el viernes.

Hasta ahora Claude solo leyó archivos del proyecto. Un **MCP** (Model Context Protocol) es
la forma de conectarle herramientas externas: una base de datos, Jira, GitHub, lo que sea.
Aquí le vamos a conectar una base de datos académica de la universidad (Postgres, aparte
del portal: son sistemas distintos).

### Conectar el servidor

Sal de Claude Code (`Ctrl+C` dos veces) y, en la carpeta del proyecto:

```bash
claude mcp add --transport stdio dbtest -- npx -y @bytebase/dbhub \
  --dsn 'postgresql://postgres:Alpaca24@research.upb.edu:5432/dbtest'
```

**Windows (PowerShell)**, en una sola línea:

```powershell
claude mcp add --transport stdio dbtest -- npx -y @bytebase/dbhub --dsn 'postgresql://postgres:Alpaca24@research.upb.edu:5432/dbtest'
```

Vuelve a abrir Claude Code (el mismo comando largo de **Puesta en marcha**) y verifica:

```
/mcp
```

`dbtest` tiene que aparecer conectado. Fíjate en lo que **no** hiciste: no instalaste un
cliente de base de datos ni escribiste código para conectarte.

### El pedido

Llega este correo de Dirección Académica:

> «Necesitamos el **cuadro de honor** de este semestre: los 5 mejores estudiantes de cada
> carrera con su promedio. Para el viernes.»

Nadie te dice en qué tablas está eso. Así llegan los pedidos.

### Primero el SQL

Antes de pedir el reporte, pide la consulta:

```
Tengo conectada la base de datos dbtest por MCP. Explórala y escríbeme el SQL del cuadro de
honor de este semestre: los 5 mejores estudiantes por carrera, con código, nombre, carrera
y promedio. Solo el SQL, no me generes el reporte todavía. Explícame qué decisiones tomaste.
```

Léelo antes de correrlo. Deberías poder contestar estas tres preguntas mirando la consulta:

- ¿Qué periodo eligió como «este semestre»? En la base hay más de uno.
- Este semestre todavía no tiene nota final cargada. Entonces, ¿de dónde sale el promedio,
  y qué pasa con las ponderaciones de las evaluaciones que aún no se rindieron?
- ¿Deja fuera las inscripciones retiradas y a los estudiantes que no están activos?

Si algo no cierra, díselo y que lo corrija. **Esa conversación es el ejercicio**, no el SQL.

Cuando te convenza, córrelo tú en DBeaver (o el visor que uses):

| | |
|---|---|
| Host | `research.upb.edu` |
| Puerto | `5432` |
| Base | `dbtest` |
| Usuario | `postgres` |
| Contraseña | `Alpaca24` |

Son 6 carreras: tienen que salir 30 filas, 5 por carrera.

### Ahora sí, el reporte

Ya confías en la consulta, así que sáltate el paso manual:

```
Ejecuta esa consulta por MCP y guárdame el resultado en reportes/cuadro_de_honor.csv, con
una columna de puesto, ordenado por carrera y puesto.
```

Ábrelo. Eso es lo que mandas el viernes.

**Qué observar:**
- Claude no adivinó el esquema: lo consultó. Sin el MCP, la misma pregunta habría empezado
  con «pásame el esquema» y habría terminado con nombres de tablas inventados.
- Mira el pedido de permiso cada vez que toca la base. El MCP le da a Claude **las mismas
  credenciales que le pasaste**: si ese usuario puede borrar, Claude puede borrar. Para
  reportes conéctate con un usuario de solo lectura (o agrega `--readonly` al comando de
  dbhub).
- El paso manual por DBeaver no fue burocracia: sirvió para revisar la consulta una vez.
  Revisada, el resto se automatiza.

---

## Cierre - Git

**Meta:** cerrar el círculo dejando el trabajo del taller en una rama con su commit.

```
Crea una rama con todo lo que hicimos hoy y haz commit con un mensaje descriptivo
```

---

## Tips

| Atajo | Qué hace |
|---|---|
| `Shift+Tab` | Cambia de modo (normal → auto-aceptar → plan) |
| `Esc` | Interrumpe a Claude mientras trabaja |
| `Esc` `Esc` | Vuelve atrás a un mensaje anterior |
| `/clear` | Limpia el contexto y empieza de cero |
| `/undo` | Deshace el último cambio en archivos |
| `/mcp` | Muestra los servidores MCP conectados |
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
