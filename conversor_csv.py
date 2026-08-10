import os
import pandas as pd
import sqlite3

# 1. Conectarse a la base de datos
# Definir directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "datos", "ruralconecta.db")
REPORTES_DIR = os.path.join(BASE_DIR, "reportes")

# Asegurar que la carpeta para guardar los CSV exista
os.makedirs(REPORTES_DIR, exist_ok=True)

# 1. Conectarse a la base de datos
conexion = sqlite3.connect(DB_PATH)

# Definir la tabla a exportar
nombre_tabla = "solicitudes"

# 2. Leer la tabla específica
df = pd.read_sql_query(f"SELECT * FROM {nombre_tabla}", conexion)

# 3. Guardar como CSV en la carpeta correspondiente con el mismo nombre de la tabla
csv_path = os.path.join(REPORTES_DIR, f"{nombre_tabla}.csv")
df.to_csv(csv_path, index=False)

# 4. Cerrar la conexión
conexion.close()
print(f"¡Conversión completada con éxito! Archivo guardado en: {csv_path}")
