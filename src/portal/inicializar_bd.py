"""Crea el esquema y carga los datos semilla del portal.

Se ejecuta con:

    uv run inicializar-bd

El generador usa una semilla fija (``SEMILLA``), así que todos los asistentes del taller
obtienen exactamente el mismo conjunto de datos. Las fechas se calculan relativas al
momento de la ejecución, de modo que el panel siempre muestra actividad reciente.

Si el esquema ya existe, no hace nada: no vuelve a borrar ni recrear las tablas.
"""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import oracledb

from portal.config import RAIZ_PROYECTO, obtener_configuracion

SEMILLA = 20260819
ARCHIVO_ESQUEMA = RAIZ_PROYECTO / "bd" / "01_esquema.sql"

CATEGORIAS = [
    ("Restablecimiento de contraseña", "Recuperación de acceso a la cuenta institucional.", 4),
    ("Acceso a VPN", "Alta, baja y problemas de conexión con la VPN de la universidad.", 8),
    ("Correo institucional", "Fallas de envío, recepción o cuota del correo @upb.edu.", 8),
    (
        "Aula virtual",
        "Acceso a cursos, materiales y entregas en la plataforma de aula virtual.",
        12,
    ),
    ("Certificados y constancias", "Emisión de certificados de notas, egreso y constancias.", 48),
    (
        "Inscripción y horarios",
        "Problemas con la inscripción de materias y choques de horario.",
        24,
    ),
    ("Equipos y laboratorios", "Reserva de laboratorios y fallas de equipos de cómputo.", 24),
    ("Licencias de software", "Solicitud de licencias académicas y activación de software.", 72),
]

FUNCIONARIOS = [
    ("Marcelo Ledezma Rojas", "mledezma@upb.edu", "Mesa de Ayuda"),
    ("Carla Vargas Terceros", "cvargas@upb.edu", "Mesa de Ayuda"),
    ("Rodrigo Peñaranda Ávila", "rpenaranda@upb.edu", "Redes y Comunicaciones"),
    ("Daniela Quisbert Mamani", "dquisbert@upb.edu", "Sistemas Académicos"),
    ("Iván Coronado Suárez", "icoronado@upb.edu", "Soporte Técnico"),
    ("Lucía Antezana Ferrufino", "lantezana@upb.edu", "Soporte Técnico"),
]

NOMBRES = [
    "Ana",
    "Luis",
    "María",
    "Jorge",
    "Camila",
    "Diego",
    "Valeria",
    "Sebastián",
    "Gabriela",
    "Andrés",
    "Fernanda",
    "Mauricio",
    "Paola",
    "Alejandro",
    "Daniela",
    "Rodrigo",
    "Natalia",
    "Javier",
    "Carolina",
    "Fabricio",
]

APELLIDOS = [
    "Choque",
    "Mamani",
    "Quispe",
    "Flores",
    "Rojas",
    "Céspedes",
    "Arispe",
    "Montaño",
    "Salazar",
    "Zeballos",
    "Áñez",
    "Guzmán",
    "Careaga",
    "Vaca",
    "Ribera",
    "Ortiz",
    "Balderrama",
    "Encinas",
    "Villarroel",
    "Nogales",
]

CARRERAS = [
    "Ingeniería de Sistemas Computacionales",
    "Ingeniería Industrial",
    "Ingeniería Mecatrónica",
    "Administración de Empresas",
    "Ingeniería Comercial",
    "Derecho",
    "Comunicación Estratégica y Digital",
    "Arquitectura",
]

# Plantillas de asunto y descripción por categoría (mismo orden que CATEGORIAS).
TEXTOS = {
    "Restablecimiento de contraseña": [
        (
            "No puedo ingresar a mi cuenta institucional",
            "Desde ayer mi contraseña dejó de funcionar y el sistema me indica que la cuenta está bloqueada.",
        ),
        (
            "Olvidé mi contraseña del portal",
            "Necesito restablecer la contraseña porque no recuerdo la actual y debo entregar un trabajo hoy.",
        ),
        (
            "La cuenta se bloquea cada vez que ingreso",
            "Ingreso la contraseña correcta pero después de dos intentos la cuenta queda bloqueada nuevamente.",
        ),
    ],
    "Acceso a VPN": [
        (
            "No logro conectarme a la VPN desde mi casa",
            "El cliente de VPN se queda en 'conectando' y luego expira. Ya reinstalé la aplicación sin éxito.",
        ),
        (
            "Solicito acceso a la VPN para prácticas",
            "Estoy haciendo prácticas en laboratorio y necesito acceso remoto a los servidores de la facultad.",
        ),
        (
            "La VPN se desconecta cada pocos minutos",
            "La conexión se cae aproximadamente cada cinco minutos y tengo que volver a autenticarme.",
        ),
    ],
    "Correo institucional": [
        (
            "No recibo correos de mis docentes",
            "Los compañeros reciben los avisos del curso pero a mí no me llega nada desde hace una semana.",
        ),
        (
            "Mi buzón está lleno y no puedo enviar",
            "El sistema indica que superé la cuota de almacenamiento y rechaza los envíos.",
        ),
        (
            "Correo institucional rebota al enviar a externos",
            "Cuando escribo a direcciones fuera de la universidad recibo un mensaje de error de entrega.",
        ),
    ],
    "Aula virtual": [
        (
            "No veo una materia inscrita en el aula virtual",
            "Estoy inscrito en la materia pero no aparece en mi lista de cursos de la plataforma.",
        ),
        (
            "No puedo subir mi tarea al aula virtual",
            "Al intentar cargar el archivo la página se queda procesando y nunca termina de subir.",
        ),
        (
            "El examen del aula virtual se cerró antes de tiempo",
            "La plataforma cerró mi intento cuando todavía quedaba tiempo disponible según el cronómetro.",
        ),
    ],
    "Certificados y constancias": [
        (
            "Solicito certificado de notas",
            "Necesito un certificado de calificaciones de los últimos dos semestres para una beca.",
        ),
        (
            "Constancia de estudios para trámite migratorio",
            "Requiero una constancia que acredite que soy estudiante regular para un trámite consular.",
        ),
        (
            "Certificado de egreso",
            "Terminé la carga horaria el semestre pasado y necesito el certificado de egreso.",
        ),
    ],
    "Inscripción y horarios": [
        (
            "Choque de horarios entre dos materias",
            "Dos materias obligatorias de mi semestre se dictan en el mismo bloque horario.",
        ),
        (
            "No puedo inscribirme a una materia con cupo",
            "El sistema muestra cupos disponibles pero al confirmar la inscripción arroja un error.",
        ),
        (
            "Necesito cambiar de paralelo",
            "Solicito el cambio al paralelo de la tarde por motivos laborales.",
        ),
    ],
    "Equipos y laboratorios": [
        (
            "Computadora del laboratorio no enciende",
            "El equipo número 12 del laboratorio de redes no enciende desde el lunes.",
        ),
        (
            "Reserva del laboratorio de cómputo",
            "Solicito reservar el laboratorio para una sesión de práctica del grupo de proyecto.",
        ),
        (
            "Proyector del aula sin señal",
            "El proyector del aula 305 no recibe señal desde ninguna laptop.",
        ),
    ],
    "Licencias de software": [
        (
            "Solicito licencia académica de MATLAB",
            "La necesito para la materia de control automático de este semestre.",
        ),
        (
            "Activación de licencia de AutoCAD",
            "Instalé el software pero la licencia académica no se activa con mi cuenta institucional.",
        ),
        (
            "Acceso a la suite estadística",
            "Requiero acceso al paquete estadístico para el trabajo de titulación.",
        ),
    ],
}

PRIORIDADES = ["BAJA", "MEDIA", "MEDIA", "ALTA", "ALTA", "URGENTE"]

RESPUESTAS_FUNCIONARIO = [
    "Recibimos tu solicitud y ya la estamos revisando.",
    "Escalamos el caso al área correspondiente. Te avisamos apenas tengamos novedades.",
    "Necesitamos que nos confirmes desde qué equipo y red estás intentando conectarte.",
    "Realizamos el cambio solicitado. Por favor verifica e infórmanos si persiste el problema.",
    "El trámite quedó registrado. El documento estará disponible en ventanilla en 48 horas.",
    "Revisamos la configuración y encontramos la causa. Estamos aplicando la corrección.",
]

RESPUESTAS_ESTUDIANTE = [
    "Gracias, quedo atento a la respuesta.",
    "Ya probé lo que me indicaron y el problema continúa.",
    "Confirmo que estoy conectado desde mi casa con red doméstica.",
    "Muchas gracias, ya pude ingresar sin problemas.",
    "¿Hay alguna novedad sobre mi solicitud?",
]


def _leer_sentencias(ruta: Path) -> list[str]:
    """Lee un archivo .sql y devuelve la lista de sentencias, sin comentarios."""
    lineas_utiles = [
        linea
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if not linea.strip().startswith("--")
    ]
    texto = "\n".join(lineas_utiles)
    return [sentencia.strip() for sentencia in texto.split(";") if sentencia.strip()]


def _ya_inicializado(conexion: oracledb.Connection) -> bool:
    """
    True si ya hay datos cargados, no solo si existe el esquema.

    Una ejecución anterior interrumpida a mitad de ``insertar_datos`` puede dejar
    las tablas creadas pero vacías; en ese caso se debe volver a sembrar, no omitirlo.
    """
    with conexion.cursor() as cursor:
        try:
            cursor.execute("SELECT COUNT(*) FROM categorias")
        except oracledb.DatabaseError:
            conexion.rollback()
            return False
        (cantidad,) = cursor.fetchone()
    return cantidad > 0


def crear_esquema(conexion: oracledb.Connection) -> None:
    """Ejecuta el DDL de bd/01_esquema.sql."""
    print(f"Creando el esquema desde {ARCHIVO_ESQUEMA.relative_to(RAIZ_PROYECTO)} ...")
    with conexion.cursor() as cursor:
        for sentencia in _leer_sentencias(ARCHIVO_ESQUEMA):
            cursor.execute(sentencia)
    conexion.commit()
    print("  Esquema creado.")


def _en_horario_laboral(momento: datetime) -> bool:
    """True si el momento cae en día hábil y entre las 08:00 y las 18:00."""
    return momento.weekday() < 5 and 8 <= momento.hour < 18


def _fecha_aleatoria(azar: random.Random, ahora: datetime, dias_atras: int) -> datetime:
    """Genera una fecha dentro de los últimos ``dias_atras`` días, en horario laboral."""
    while True:
        momento = ahora - timedelta(
            days=azar.randint(0, dias_atras),
            hours=azar.randint(0, 23),
            minutes=azar.randint(0, 59),
        )
        if _en_horario_laboral(momento):
            return momento


def _fecha_fuera_de_horario(azar: random.Random, ahora: datetime, dias_atras: int) -> datetime:
    """Genera una fecha de día hábil pero **después** del horario laboral (18:00–23:00).

    El panel necesita este tipo de solicitudes para que las métricas de SLA reflejen
    también los casos registrados de noche, que son frecuentes en la mesa de ayuda.
    """
    while True:
        momento = (ahora - timedelta(days=azar.randint(2, dias_atras))).replace(
            hour=azar.randint(18, 23),
            minute=azar.randint(0, 59),
            second=0,
            microsecond=0,
        )
        if momento.weekday() < 5:
            return momento


def insertar_datos(conexion: oracledb.Connection) -> None:
    """Genera y carga los datos semilla."""
    azar = random.Random(SEMILLA)
    ahora = datetime.now().replace(microsecond=0)

    with conexion.cursor() as cursor:
        # --- Categorías ------------------------------------------------------
        cursor.executemany(
            "INSERT INTO categorias (nombre, descripcion, sla_horas) "
            "VALUES (:nombre, :descripcion, :sla_horas)",
            [{"nombre": n, "descripcion": d, "sla_horas": s} for n, d, s in CATEGORIAS],
        )
        print(f"  {len(CATEGORIAS)} categorías")

        # --- Funcionarios ----------------------------------------------------
        cursor.executemany(
            "INSERT INTO funcionarios (nombre, correo, area) VALUES (:nombre, :correo, :area)",
            [{"nombre": n, "correo": c, "area": a} for n, c, a in FUNCIONARIOS],
        )
        print(f"  {len(FUNCIONARIOS)} funcionarios")

        # --- Estudiantes -----------------------------------------------------
        estudiantes = []
        correos_usados: set[str] = set()
        for indice in range(40):
            nombre = azar.choice(NOMBRES)
            apellido_uno = azar.choice(APELLIDOS)
            apellido_dos = azar.choice(APELLIDOS)
            base = f"{nombre[0]}{apellido_uno}".lower()
            base = base.replace("á", "a").replace("é", "e").replace("í", "i")
            base = base.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
            correo = f"{base}@upb.edu"
            if correo in correos_usados:
                correo = f"{base}{indice}@upb.edu"
            correos_usados.add(correo)
            estudiantes.append(
                {
                    "codigo_estudiante": f"UPB{40000 + indice * 7:05d}",
                    "nombres": nombre,
                    "apellidos": f"{apellido_uno} {apellido_dos}",
                    "correo": correo,
                    "carrera": azar.choice(CARRERAS),
                    "semestre": azar.randint(1, 10),
                }
            )
        cursor.executemany(
            "INSERT INTO estudiantes "
            "(codigo_estudiante, nombres, apellidos, correo, carrera, semestre) "
            "VALUES (:codigo_estudiante, :nombres, :apellidos, :correo, :carrera, :semestre)",
            estudiantes,
        )
        print(f"  {len(estudiantes)} estudiantes")

        # Recuperamos los ids que Oracle asignó a las tablas de referencia.
        cursor.execute("SELECT id FROM estudiantes ORDER BY id")
        ids_estudiantes = [fila[0] for fila in cursor.fetchall()]
        cursor.execute("SELECT id FROM funcionarios ORDER BY id")
        ids_funcionarios = [fila[0] for fila in cursor.fetchall()]
        cursor.execute("SELECT id, nombre FROM categorias ORDER BY id")
        categorias = cursor.fetchall()

        # --- Solicitudes -----------------------------------------------------
        solicitudes = []
        for numero in range(1, 151):
            categoria_id, categoria_nombre = azar.choice(categorias)
            asunto, descripcion = azar.choice(TEXTOS[categoria_nombre])

            # Una de cada diez solicitudes se registra fuera del horario laboral.
            if numero % 10 == 0:
                creada_en = _fecha_fuera_de_horario(azar, ahora, 30)
            else:
                creada_en = _fecha_aleatoria(azar, ahora, 90)

            dias_de_antiguedad = (ahora - creada_en).days
            # Cuanto más vieja la solicitud, más probable es que ya esté cerrada.
            if dias_de_antiguedad > 45:
                estado = azar.choices(["CERRADA", "RESUELTA", "RECHAZADA"], weights=[75, 15, 10])[0]
            elif dias_de_antiguedad > 14:
                estado = azar.choices(
                    ["CERRADA", "RESUELTA", "EN_PROCESO", "RECHAZADA"],
                    weights=[45, 25, 20, 10],
                )[0]
            else:
                estado = azar.choices(
                    ["RECIBIDA", "EN_REVISION", "EN_PROCESO", "RESUELTA", "CERRADA"],
                    weights=[30, 20, 25, 15, 10],
                )[0]

            asignable = estado != "RECIBIDA"
            funcionario_id = azar.choice(ids_funcionarios) if asignable else None

            if estado in ("CERRADA", "RESUELTA", "RECHAZADA"):
                cerrada_en = creada_en + timedelta(
                    hours=azar.randint(2, 96), minutes=azar.randint(0, 59)
                )
                cerrada_en = min(cerrada_en, ahora)
                actualizada_en = cerrada_en
            else:
                cerrada_en = None
                actualizada_en = creada_en + timedelta(hours=azar.randint(1, 48))
                actualizada_en = min(actualizada_en, ahora)

            solicitudes.append(
                {
                    "codigo": f"SOL-{ahora.year}-{numero:04d}",
                    "estudiante_id": azar.choice(ids_estudiantes),
                    "categoria_id": categoria_id,
                    "funcionario_id": funcionario_id,
                    "asunto": asunto,
                    "descripcion": descripcion,
                    "estado": estado,
                    "prioridad": azar.choice(PRIORIDADES),
                    "creada_en": creada_en,
                    "actualizada_en": actualizada_en,
                    "cerrada_en": cerrada_en,
                }
            )

        # --- Atención nocturna -----------------------------------------------
        # La mesa de ayuda atiende algunos casos fuera del horario de oficina: el
        # estudiante registra la solicitud de noche y el funcionario de turno la resuelve
        # en el momento. Son pocos casos, pero conviene tenerlos representados.
        for indice, (categoria_id, categoria_nombre) in enumerate(azar.sample(categorias, 6)):
            asunto, descripcion = azar.choice(TEXTOS[categoria_nombre])
            creada_en = _fecha_fuera_de_horario(azar, ahora, 20)
            cerrada_en = creada_en + timedelta(minutes=azar.randint(30, 110))
            solicitudes.append(
                {
                    "codigo": f"SOL-{ahora.year}-{151 + indice:04d}",
                    "estudiante_id": azar.choice(ids_estudiantes),
                    "categoria_id": categoria_id,
                    "funcionario_id": azar.choice(ids_funcionarios),
                    "asunto": asunto,
                    "descripcion": descripcion,
                    "estado": "CERRADA",
                    "prioridad": azar.choice(["ALTA", "URGENTE"]),
                    "creada_en": creada_en,
                    "actualizada_en": cerrada_en,
                    "cerrada_en": cerrada_en,
                }
            )

        cursor.executemany(
            "INSERT INTO solicitudes "
            "(codigo, estudiante_id, categoria_id, funcionario_id, asunto, descripcion, "
            " estado, prioridad, creada_en, actualizada_en, cerrada_en) "
            "VALUES (:codigo, :estudiante_id, :categoria_id, :funcionario_id, :asunto, "
            " :descripcion, :estado, :prioridad, :creada_en, :actualizada_en, :cerrada_en)",
            solicitudes,
        )
        print(f"  {len(solicitudes)} solicitudes")

        # --- Seguimientos ----------------------------------------------------
        cursor.execute("SELECT id, creada_en, estado FROM solicitudes ORDER BY id")
        filas_solicitudes = cursor.fetchall()

        nombres_funcionarios = [nombre for nombre, _, _ in FUNCIONARIOS]
        seguimientos = []
        for solicitud_id, creada_en, estado in filas_solicitudes:
            if estado == "RECIBIDA":
                continue  # todavía nadie la tocó
            cantidad = azar.randint(1, 4)
            momento = creada_en
            for indice in range(cantidad):
                momento = momento + timedelta(
                    hours=azar.randint(1, 20), minutes=azar.randint(0, 59)
                )
                if momento > ahora:
                    break
                es_de_funcionario = indice % 2 == 0
                seguimientos.append(
                    {
                        "solicitud_id": solicitud_id,
                        "autor": (
                            azar.choice(nombres_funcionarios) if es_de_funcionario else "Estudiante"
                        ),
                        "mensaje": azar.choice(
                            RESPUESTAS_FUNCIONARIO if es_de_funcionario else RESPUESTAS_ESTUDIANTE
                        ),
                        "es_interno": 1 if es_de_funcionario and azar.random() < 0.2 else 0,
                        "creado_en": momento,
                    }
                )

        cursor.executemany(
            "INSERT INTO seguimientos (solicitud_id, autor, mensaje, es_interno, creado_en) "
            "VALUES (:solicitud_id, :autor, :mensaje, :es_interno, :creado_en)",
            seguimientos,
        )
        print(f"  {len(seguimientos)} seguimientos")

    conexion.commit()


def main() -> int:
    """Punto de entrada del comando ``inicializar-bd``."""
    config = obtener_configuracion()
    print(f"Conectando a {config.bd_dsn} como {config.bd_usuario} ...")
    try:
        conexion = oracledb.connect(
            user=config.bd_usuario, password=config.bd_clave, dsn=config.bd_dsn
        )
    except oracledb.Error as error:
        print(f"\n  No se pudo conectar a Oracle: {error}", file=sys.stderr)
        print("  ¿Está levantado el contenedor?  docker compose up -d", file=sys.stderr)
        return 1

    with conexion:
        if _ya_inicializado(conexion):
            print("La base de datos ya está inicializada. Nada que hacer.")
            return 0
        crear_esquema(conexion)
        print("Cargando datos semilla ...")
        insertar_datos(conexion)

    print("\nListo. La base de datos está preparada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
