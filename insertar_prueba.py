import sqlite3
import random
from datetime import datetime, timedelta

# 1. Conexión a la base de datos
conn = sqlite3.connect('datos/ruralconecta.db')
cursor = conn.cursor()

# 2. Creación de la estructura de tablas (DDL)[cite: 1]
cursor.executescript("""
    CREATE TABLE IF NOT EXISTS roles(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS permisos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL UNIQUE, 
        descripcion TEXT
    );
    CREATE TABLE IF NOT EXISTS roles_permisos(
        rol_id INTEGER, 
        permiso_id INTEGER, 
        PRIMARY KEY(rol_id, permiso_id), 
        FOREIGN KEY(rol_id) REFERENCES roles(id) ON DELETE CASCADE, 
        FOREIGN KEY(permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        apellido TEXT NOT NULL, 
        dni TEXT UNIQUE, 
        cuil TEXT UNIQUE, 
        clave TEXT NOT NULL, 
        rol_id INTEGER, 
        FOREIGN KEY(rol_id) REFERENCES roles(id)
    );
    CREATE TABLE IF NOT EXISTS categorias(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        sla_horas INTEGER, 
        estacionalidad_alta TEXT
    );
    CREATE TABLE IF NOT EXISTS subcategorias(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        categoria_id INTEGER, 
        FOREIGN KEY(categoria_id) REFERENCES categorias(id)
    );
    CREATE TABLE IF NOT EXISTS estados_solicitud(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS barrios(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nombre TEXT NOT NULL, 
        zona TEXT
    );
    CREATE TABLE IF NOT EXISTS solicitudes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        comentario TEXT, 
        categoria_id INTEGER, 
        subcategoria_id INTEGER, 
        prioridad TEXT, 
        estado_id INTEGER, 
        fecha_creacion DATETIME, 
        fecha_resolucion DATETIME, 
        ubicacion TEXT, 
        barrio_id INTEGER, 
        asignado_a INTEGER, 
        score_sentimiento REAL, 
        urgencia_nlp BOOLEAN, 
        usuario_id INTEGER, 
        FOREIGN KEY(categoria_id) REFERENCES categorias(id), 
        FOREIGN KEY(subcategoria_id) REFERENCES subcategorias(id), 
        FOREIGN KEY(estado_id) REFERENCES estados_solicitud(id), 
        FOREIGN KEY(barrio_id) REFERENCES barrios(id), 
        FOREIGN KEY(asignado_a) REFERENCES usuarios(id), 
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
    CREATE TABLE IF NOT EXISTS historial_estados(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        solicitud_id INTEGER, 
        estado_anterior_id INTEGER, 
        estado_nuevo_id INTEGER, 
        usuario_id INTEGER, 
        fecha_cambio DATETIME, 
        FOREIGN KEY(solicitud_id) REFERENCES solicitudes(id), 
        FOREIGN KEY(estado_anterior_id) REFERENCES estados_solicitud(id), 
        FOREIGN KEY(estado_nuevo_id) REFERENCES estados_solicitud(id), 
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
    CREATE TABLE IF NOT EXISTS reportes_mensuales(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        mes INTEGER, 
        anio INTEGER, 
        metricas_consolidadas TEXT
    );
    CREATE TABLE IF NOT EXISTS alertas_anomalias(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        fecha_deteccion DATETIME, 
        tipo_anomalia TEXT, 
        categoria_id INTEGER, 
        descripcion TEXT, 
        severidad TEXT, 
        FOREIGN KEY(categoria_id) REFERENCES categorias(id)
    );
    CREATE TABLE IF NOT EXISTS zonas_calientes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        categoria_id INTEGER, 
        barrio_id INTEGER, 
        latitud_centro TEXT, 
        longitud_centro TEXT, 
        recurrencia INTEGER, 
        FOREIGN KEY(categoria_id) REFERENCES categorias(id), 
        FOREIGN KEY(barrio_id) REFERENCES barrios(id)
    );
    CREATE TABLE IF NOT EXISTS registro_climatico(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        fecha DATE, 
        precipitacion_mm REAL, 
        temperatura_promedio REAL, 
        eventos_extremos TEXT
    );
    CREATE TABLE IF NOT EXISTS etiquetas_ia(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        solicitud_id INTEGER, 
        keyword TEXT, 
        confianza_ia REAL, 
        FOREIGN KEY(solicitud_id) REFERENCES solicitudes(id)
    );
    CREATE TABLE IF NOT EXISTS encuestas_satisfaccion(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        solicitud_id INTEGER, 
        puntuacion INTEGER, 
        comentario_vecino TEXT, 
        fecha_encuesta DATETIME, 
        FOREIGN KEY(solicitud_id) REFERENCES solicitudes(id)
    );
""")

# 3. Inserción de Catálogos (Basado en el dump original)
roles = ["Analista", "De Gestión", "Ciudadano Rural"]
for r in roles:
    cursor.execute("SELECT id FROM roles WHERE LOWER(nombre) = LOWER(?)", (r,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (r,))

estados = ["RECHAZADO", "RESUELTO", "EN PROCESO", "EN REVISION", "PENDIENTE"] #[cite: 1]
for e in estados:
    cursor.execute("SELECT id FROM estados_solicitud WHERE LOWER(nombre) = LOWER(?)", (e,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO estados_solicitud (nombre) VALUES (?)", (e,))

categorias = [
    ("Red Vial Rural y Caminos", 72, "LLUVIAS / INVIERNO"),
    ("Agua Potable Rural y Riego", 24, "VERANO"),
    ("Electrificación y Alumbrado Rural", 48, "N/A"),
    ("Residuos y Limpieza Rural", 48, "VERANO"),
    ("Zoonosis y Control de Plagas Rurales", 48, "VERANO"),
    ("Medio Ambiente y Recurso Forestal", 72, "OTOÑO / PRIMAVERA"),
    ("Infraestructura Comunitaria Rural", 96, "N/A"),
    ("Convivencia y Mediación Rural", 96, "N/A")
]
for cat in categorias:
    cursor.execute("SELECT id FROM categorias WHERE LOWER(nombre) = LOWER(?)", (cat[0],))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO categorias (nombre, sla_horas, estacionalidad_alta) VALUES (?, ?, ?)", cat)

subcategorias = [
    ("Baches y Pozos en Caminos de Tierra / Ripio", 1),
    ("Caminos Intransitables por Lluvias o Inundación", 1),
    ("Falta de Agua en Tanque / Pozo Comunitario", 2),
    ("Bomba de Agua Defectuosa o Sin Funcionamiento", 2),
    ("Corte de Luz en Paraje / Zona Rural", 3),
    ("Poste Caído o En Peligro", 3),
    ("Retiro de Residuos en Puntos de Acopio Rurales", 4),
    ("Microbasural o Vuelco Clandestino en Caminos", 4),
    ("Animales de Granja o Equinos Sueltos en Rutas/Caminos", 5),
    ("Plagas Agrícolas / Invertebrados (Langostas, Mosquitos, Roedores)", 5),
    ("Riesgo de Incendio Forestal / Quemas No Autorizadas", 6),
    ("Caída de Árboles o Ramas Grandes en Caminos", 6),
    ("Mantenimiento de Centro Comunitario / Salón del Paraje", 7),
    ("Falta de Señalización en Caminos Rurales", 7),
    ("Disputas por Límites de Propiedad o Alambrados", 8),
    ("Uso Compartido de Agua de Riego", 8)
]
for subcat in subcategorias:
    cursor.execute("SELECT id FROM subcategorias WHERE LOWER(nombre) = LOWER(?)", (subcat[0],))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO subcategorias (nombre, categoria_id) VALUES (?, ?)", subcat)

barrios = [("Paraje Centro", "Centro"), ("Paraje Sur", "Sur"), ("Paraje Norte", "Norte")]
for b in barrios:
    cursor.execute("SELECT id FROM barrios WHERE LOWER(nombre) = LOWER(?)", (b[0],))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO barrios (nombre, zona) VALUES (?, ?)", b)

from main import hash_password

usuarios = [
    ("Diego", "Andrada", "27231845", "20272318450", hash_password("vecino123"), 1), 
    ("Florencia", "Sánchez", "23963457", "27239634570", hash_password("florencia123"), 1), 
    ("Test", "Vecino", "99999999", "20999999999", hash_password("vecino123"), 1),
    ("Gestor", "Municipal", "11223344", "20112233440", hash_password("gestor123"), 2)
]
for nom, ape, dni, cuil, pwd, r_id in usuarios:
    cursor.execute("SELECT id FROM usuarios WHERE dni = ?", (dni,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id) VALUES (?, ?, ?, ?, ?, ?)", (nom, ape, dni, cuil, pwd, r_id))

# 4. Generación de 500 Registros en solicitudes y sus trazabilidades
from generar_base_500 import generar_dataset_500
conn.close()

generar_dataset_500()
print("Base de datos 'ruralconecta.db' generada exitosamente con 500 registros en solicitudes.")

