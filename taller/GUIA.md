# Taller de Claude Code — Guía del asistente

Portal de Atención al Estudiante · Universidad Privada Boliviana

Durante las próximas horas vas a trabajar sobre una aplicación real: FastAPI,
Oracle y una interfaz web. **La aplicación tiene problemas a propósito.** Encontrarlos y
resolverlos con Claude Code es exactamente el ejercicio.

No hace falta que sepas FastAPI ni Oracle. Justamente de eso se trata: así es como llega
un sistema que heredaste de otro equipo.

---

## Agenda

| # | Bloque |
|---|---|
| 0 | Puesta en marcha |
| 1 | Entender código que no escribiste |
| 2 | Dirigir a Claude: plan mode y CLAUDE.md |
| 3 | Encontrar un bug de verdad |
| 4 | Una funcionalidad de punta a punta |
| 5 | Revisión de código |
| 6 | Git |

---

## Ejercicio 0 — Puesta en marcha

**Meta:** tener la aplicación corriendo y Claude Code abierto en el proyecto.

```bash
python verificar_entorno.py    # debe terminar sin errores (funciona en Windows, Mac, Linux)
docker compose up -d --build   # base de datos + aplicación
docker compose exec app uv run inicializar-bd   # solo la primera vez, si faltan los datos
```

No necesitas instalar Python ni `uv`: todo corre dentro de Docker. El código se monta como
volumen, así que al editar y guardar un archivo, el servidor se recarga solo.

Abre <http://localhost:8000> y date una vuelta: panel, listado, detalle de una solicitud.

En **otra** terminal, dentro de la carpeta del proyecto:

```bash
claude
```

Puedes probar:

> Dame un recorrido de este proyecto: qué hace, cómo está organizado y por dónde entra
> una petición HTTP. No cambies nada.

**Qué observar:** Claude lee el repositorio por su cuenta. No hace falta que le pegues
archivos.

---

## Ejercicio 1 — Entender código que no escribiste

**Meta:** usar Claude Code como la herramienta que más vas a usar en el trabajo real:
entender un módulo que nadie documentó.

Abre `src/portal/servicios/tiempos_atencion.py` y míralo unos segundos. Es el corazón del
cálculo de SLA y no tiene ni un comentario.

Pruebas a hacer, una por una:

> Explícame qué hace `src/portal/servicios/tiempos_atencion.py`, función por función. No
> modifiques nada todavía.

> ¿Qué significan las variables `acc`, `t0`, `t1` y `u` dentro de `horas_habiles_entre`?

> Hazme un diagrama del flujo de `horas_habiles_entre`.

> ¿Dónde se decide si una solicitud puede pasar de un estado a otro?

Y recién ahora, que ya entendiste el módulo:

> Agrégale docstrings en español a `tiempos_atencion.py`, explicando cada función y las
> constantes. No cambies el comportamiento.

**Qué observar:**
- Decirle «no cambies nada» funciona: contesta sin tocar archivos.
- La última pregunta la responde buscando en todo el repositorio, no solo en el archivo abierto.
- Al final, revisa el diff. ¿Los docstrings dicen la verdad?

---

## Ejercicio 2 — Dirigir a Claude: plan mode y CLAUDE.md

**Meta:** aprender a decidir *antes* de que se escriba el código, y a fijar los estándares
del equipo en un archivo.

### Parte A — Plan mode

Pulsa `Shift+Tab` hasta que aparezca **plan mode**. En ese modo Claude investiga y propone,
pero no edita nada hasta que apruebes.

> Quiero agregar un filtro por rango de fechas al listado de solicitudes. Planifícalo.

Lee el plan. Discútelo. Pídele cambios. Recién entonces apruébalo — o descártalo, que para
este ejercicio da igual: lo que importa es ver la diferencia entre planificar y ejecutar.

### Parte B — CLAUDE.md

Este proyecto no tiene un `CLAUDE.md`. Es el archivo que Claude lee al arrancar en cada
sesión: ahí van las convenciones del equipo. Sin él, cada persona le explica las mismas
reglas a Claude una y otra vez.

Créalo a partir del código, no de memoria:

> Crea un CLAUDE.md para este proyecto. Investiga el código primero y propón 3 o 4 reglas
> concretas que el proyecto ya sigue (convenciones de nombres, estructura de carpetas, cómo
> se manejan los errores, etc.). No inventes reglas genéricas: básate en lo que ves.

Revisa lo que propone — y agrega la regla que le falta:

> Agrega una regla más: todo el SQL debe usar bind variables, nunca interpolación de texto
> con f-strings. Explica por qué y da un ejemplo correcto y uno incorrecto.

Y ahora la pregunta que importa:

> ¿El código de este proyecto cumple la regla que acabamos de escribir? Revísalo.

**Qué observar:**
- Un `CLAUDE.md` útil nace de leer el código, no de reglas genéricas de manual. Por eso
  vale la pena pedirle a Claude que investigue antes de escribir.
- Una regla en `CLAUDE.md` cuesta dos minutos y se aplica a todas las sesiones futuras,
  de todo el equipo, porque va versionada en el repositorio.
- Escribir la regla y verificar que el código la cumple son dos cosas distintas. La segunda
  es la que encuentra problemas.

---

## Ejercicio 3 — Encontrar un bug de verdad

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
  mucho más que «el SLA está mal».
- Pedir la prueba **antes** que la corrección demuestra que el bug existe y que quedó
  resuelto. Sin eso, solo tienes la palabra del modelo.
- Compara el conteo de «SLA vencido» del panel antes y después.

---

## Ejercicio 4 — Una funcionalidad de punta a punta

**Meta:** un cambio que atraviesa todas las capas: base de datos, servicio, API, plantilla,
JavaScript y prueba.

### Lo que falta

Ahora mismo una solicitud queda asignada a un funcionario solo cuando se cargan los datos
de ejemplo. Desde la aplicación **no hay forma de asignarla ni de cambiarle el responsable**.
Ábrete cualquier solicitud y búscalo: en «Datos» ves «Asignada a», pero no puedes editarlo.

### Construirlo

Empieza en **plan mode** (`Shift+Tab`):

> Quiero poder asignar y reasignar una solicitud a un funcionario desde la página de
> detalle. El cambio debe quedar registrado en la línea de tiempo, diciendo quién la
> reasignó y a quién. Planifícalo de punta a punta: servicio, ruta, plantilla, JavaScript
> y prueba.

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

## Ejercicio 5 — Revisión de código

**Meta:** pasar el código por dos revisiones automáticas y decidir qué hallazgos vale la
pena corregir.

### Revisiones

```
/code-review
```

```
/security-review
```

Lee los hallazgos uno por uno. Decide cuáles aceptas — no todo hallazgo merece un cambio.

**Qué observar:**
- `/security-review` debería encontrar el problema de SQL del Ejercicio 2. Si lo ves ahí,
  es la misma falla vista desde otra herramienta.
- Los hallazgos son propuestas, no órdenes. El criterio sigue siendo tuyo.

---

## Ejercicio 6 — Git

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
