/**
 * JavaScript del portal.
 *
 * No hay framework ni proceso de compilación: solo `fetch` contra la API REST que expone
 * FastAPI en /api. Cada formulario dinámico se engancha por su clase.
 */

"use strict";

/**
 * Envía datos en JSON a la API y devuelve la respuesta ya interpretada.
 *
 * @param {string} url Ruta de la API.
 * @param {object} datos Cuerpo de la petición.
 * @returns {Promise<{ok: boolean, estado: number, cuerpo: any}>}
 */
async function enviarJson(url, datos) {
    const respuesta = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
    });

    let cuerpo = null;
    try {
        cuerpo = await respuesta.json();
    } catch {
        cuerpo = null;
    }

    return { ok: respuesta.ok, estado: respuesta.status, cuerpo };
}

/**
 * Extrae el mensaje de error de una respuesta de FastAPI.
 *
 * FastAPI devuelve el detalle en `detail`, que puede ser un texto o una lista de errores
 * de validación de Pydantic.
 */
function mensajeDeError(cuerpo) {
    if (!cuerpo || !cuerpo.detail) {
        return "Ocurrió un error inesperado.";
    }
    if (typeof cuerpo.detail === "string") {
        return cuerpo.detail;
    }
    if (Array.isArray(cuerpo.detail)) {
        return cuerpo.detail.map((error) => error.msg).join(" · ");
    }
    return "Ocurrió un error inesperado.";
}

/** Muestra un mensaje de estado dentro de un formulario. */
function mostrarMensaje(formulario, texto, tipo) {
    const destino = formulario.querySelector(".mensaje-formulario");
    if (!destino) return;
    destino.textContent = texto;
    destino.className = `mensaje-formulario mensaje-formulario--${tipo}`;
}

/** Deshabilita el botón de envío mientras la petición está en curso. */
function bloquearEnvio(formulario, bloqueado) {
    const boton = formulario.querySelector("button[type=submit]");
    if (boton) boton.disabled = bloqueado;
}

// --- Agregar seguimiento -----------------------------------------------------
document.querySelectorAll(".formulario-seguimiento").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const solicitudId = formulario.dataset.solicitud;
        const campos = new FormData(formulario);

        bloquearEnvio(formulario, true);
        const resultado = await enviarJson(`/api/solicitudes/${solicitudId}/seguimientos`, {
            autor: campos.get("autor"),
            mensaje: campos.get("mensaje"),
            es_interno: campos.get("es_interno") === "on",
        });
        bloquearEnvio(formulario, false);

        if (resultado.ok) {
            mostrarMensaje(formulario, "Seguimiento agregado.", "exito");
            window.location.reload();
        } else {
            mostrarMensaje(formulario, mensajeDeError(resultado.cuerpo), "error");
        }
    });
});

// --- Cambiar estado ----------------------------------------------------------
document.querySelectorAll(".formulario-estado").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const solicitudId = formulario.dataset.solicitud;
        const campos = new FormData(formulario);

        bloquearEnvio(formulario, true);
        const resultado = await enviarJson(`/api/solicitudes/${solicitudId}/estado`, {
            estado: campos.get("estado"),
            autor: campos.get("autor"),
            comentario: campos.get("comentario") || null,
        });
        bloquearEnvio(formulario, false);

        if (resultado.ok) {
            mostrarMensaje(formulario, "Estado actualizado.", "exito");
            window.location.reload();
        } else {
            mostrarMensaje(formulario, mensajeDeError(resultado.cuerpo), "error");
        }
    });
});

// --- Registrar una solicitud nueva -------------------------------------------
const formularioNueva = document.getElementById("formulario-nueva-solicitud");
if (formularioNueva) {
    // Muestra el SLA de la categoría elegida mientras se completa el formulario.
    const selectorCategoria = formularioNueva.querySelector("select[name=categoria_id]");
    const ayudaSla = document.getElementById("ayuda-sla");
    selectorCategoria.addEventListener("change", () => {
        const opcion = selectorCategoria.selectedOptions[0];
        const horas = opcion ? opcion.dataset.sla : null;
        ayudaSla.textContent = horas
            ? `Esta categoría se atiende en ${horas} horas hábiles.`
            : "";
    });

    formularioNueva.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const campos = new FormData(formularioNueva);

        bloquearEnvio(formularioNueva, true);
        const resultado = await enviarJson("/api/solicitudes", {
            estudiante_id: Number(campos.get("estudiante_id")),
            categoria_id: Number(campos.get("categoria_id")),
            asunto: campos.get("asunto"),
            descripcion: campos.get("descripcion"),
            prioridad: campos.get("prioridad"),
        });
        bloquearEnvio(formularioNueva, false);

        if (resultado.ok) {
            window.location.href = `/solicitudes/${resultado.cuerpo.id}`;
        } else {
            mostrarMensaje(formularioNueva, mensajeDeError(resultado.cuerpo), "error");
        }
    });
}
