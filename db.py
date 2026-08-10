import sqlite3
import os

# Asegurar que la carpeta 'datos' exista para evitar errores de conexión
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, "datos")
os.makedirs(DATOS_DIR, exist_ok=True)

# Cambiamos el nombre de la DB para que refleje el nuevo proyecto
conexion = sqlite3.connect(os.path.join(DATOS_DIR, "ruralconecta.db"))
cursor = conexion.cursor()

# Habilitar el uso de claves foráneas en SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

# --- Tablas de Configuración Base ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS categorias(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    sla_horas INTEGER,
    estacionalidad_alta TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subcategorias(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria_id INTEGER,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS estados_solicitud(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS roles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS permisos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS roles_permisos(
    rol_id INTEGER,
    permiso_id INTEGER,
    PRIMARY KEY(rol_id, permiso_id),
    FOREIGN KEY(rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY(permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS barrios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    zona TEXT
)
""")

# --- NUEVA ESTRUCTURA DE USUARIOS ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    dni TEXT UNIQUE,
    cuil TEXT UNIQUE,
    clave TEXT NOT NULL,
    rol_id INTEGER,
    FOREIGN KEY(rol_id) REFERENCES roles(id)
)
""")

# --- Tabla Principal ---
cursor.execute("""
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
)
""")

# --- Tablas Estratégicas y Analíticas ---
cursor.execute("""
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
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS alertas_anomalias(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_deteccion DATETIME,
    tipo_anomalia TEXT,
    categoria_id INTEGER,
    descripcion TEXT,
    severidad TEXT,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reportes_mensuales(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes INTEGER,
    anio INTEGER,
    metricas_consolidadas TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS encuestas_satisfaccion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id INTEGER,
    puntuacion INTEGER,
    comentario_vecino TEXT,
    fecha_encuesta DATETIME,
    FOREIGN KEY(solicitud_id) REFERENCES solicitudes(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS etiquetas_ia(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id INTEGER,
    keyword TEXT,
    confianza_ia REAL,
    FOREIGN KEY(solicitud_id) REFERENCES solicitudes(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS registro_climatico(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE,
    precipitacion_mm REAL,
    temperatura_promedio REAL,
    eventos_extremos TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS zonas_calientes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER,
    barrio_id INTEGER,
    latitud_centro TEXT,
    longitud_centro TEXT,
    recurrencia INTEGER,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id),
    FOREIGN KEY(barrio_id) REFERENCES barrios(id)
)
""")

conexion.commit()
conexion.close()
print("Base de datos RuralConecta estructurada correctamente.")