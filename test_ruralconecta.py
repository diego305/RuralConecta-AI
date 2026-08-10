import os
import sys
import io
import sqlite3

# Forzar salida en UTF-8 para soportar emojis en consolas Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Asegurar que el directorio del script esté en el path de importación
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Cambiar el directorio de trabajo al del script para crear la base en datos/
os.chdir(script_dir)

from analizador import analizar_comentario
from respuestas import generar_respuesta
from ia import consultar_ia
import analisis
import trazabilidad

def test_workflow():
    print("--- 1. Probando analizador.py (Categorías Rurales) ---")
    res_basura = analizar_comentario("Falta de recolección de residuos en el centro de acopio rural")
    print(f"Residuos: {res_basura}")
    assert res_basura["categoria"] == "Residuos y Limpieza Rural"
    assert res_basura["prioridad"] == "MEDIA"

    res_luz = analizar_comentario("Toda la calle rural está oscura por poste de luz caído")
    print(f"Electrificación: {res_luz}")
    assert res_luz["categoria"] == "Electrificación y Alumbrado Rural"
    assert res_luz["prioridad"] == "ALTA"

    res_pozo = analizar_comentario("Hay pozos peligrosos en la ruta y el camino rural de ripio está dañado")
    print(f"Red Vial: {res_pozo}")
    assert res_pozo["categoria"] == "Red Vial Rural y Caminos"
    assert res_pozo["prioridad"] == "ALTA"

    print("Analizador rural verificado correctamente.")

    print("\n--- 2. Probando respuestas.py ---")
    resp_luz = generar_respuesta("Electrificación y Alumbrado Rural")
    print(f"Respuestas Electrificación: {resp_luz}")
    assert len(resp_luz) == 2
    assert any(x in resp_luz[0].lower() for x in ["servicio", "electrotecnia", "luz", "luminaria", "reclamo", "estimado"])
    print("respuestas.py verificado correctamente.")

    print("\n--- 3. Probando db.py y main.py (Esquema e Inicialización) ---")
    from main import inicializar_db_completo
    
    # Crear carpeta datos de prueba si no existe
    os.makedirs(os.path.dirname(analisis.DB_PATH), exist_ok=True)
    
    # Inicializar base limpia de prueba
    if os.path.exists(analisis.DB_PATH):
        try:
            os.remove(analisis.DB_PATH)
            print("Base de datos de desarrollo anterior eliminada para una prueba limpia.")
        except Exception as e:
            print(f"Nota: No se pudo eliminar la base de datos previa (tal vez esté en uso): {e}")

    # Forzar la recreación de todas las tablas relacionales y analíticas del módulo db
    import importlib
    import db
    importlib.reload(db)

    conexion = sqlite3.connect(analisis.DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON;")
    inicializar_db_completo(conexion)
    print("Esquema relacional rural estructurado e inicializado.")

    # Guardar solicitud de prueba mediante una inserción directa
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM categorias WHERE nombre = 'Residuos y Limpieza Rural'")
    cat_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM subcategorias WHERE categoria_id = ?", (cat_id,))
    sub_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM barrios LIMIT 1")
    barrio_id = cursor.fetchone()[0]
    
    # Registrar un vecino temporal
    cursor.execute("""
        INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id)
        VALUES ('Test', 'Vecino', '99998888', '20999988889', 'hash123', 1)
    """)
    vecino_id = cursor.lastrowid
    
    # Insertar solicitud
    cursor.execute("""
        INSERT INTO solicitudes (
            comentario, categoria_id, subcategoria_id, prioridad, estado_id, 
            fecha_creacion, barrio_id, score_sentimiento, urgencia_nlp, usuario_id
        ) VALUES (?, ?, ?, ?, 1, '2026-08-06 12:00:00', ?, 0.3, 0, ?)
    """, ("Problemas con basura acumulada en el paraje", cat_id, sub_id, "MEDIA", barrio_id, vecino_id))
    solicitud_id = cursor.lastrowid
    conexion.commit()
    print(f"Solicitud de prueba #{solicitud_id} registrada.")

    # Probando Trazabilidad
    print("\n--- 4. Probando trazabilidad.py ---")
    trazabilidad.registrar_cambio_estado(conexion, solicitud_id, 1, 3, vecino_id) # PENDIENTE -> EN PROCESO
    
    cursor.execute("SELECT estado_nuevo_id FROM historial_estados WHERE solicitud_id = ?", (solicitud_id,))
    res_trazabilidad = cursor.fetchone()
    assert res_trazabilidad[0] == 3
    print("trazabilidad.py verificado correctamente.")
    conexion.close()

    print("\n--- 5. Probando analisis.py (Pandas) ---")
    df = analisis.cargar_datos_completos()
    print(f"Registros leídos por Pandas: {len(df)}")
    assert len(df) >= 1
    
    stats = analisis.generar_estadisticas()
    print(f"Estadísticas Pandas: {stats}")
    assert stats["total"] >= 1
    assert any(c in stats["categorias"] for c in ["Red Vial Rural y Caminos", "Residuos y Limpieza Rural"])
    print("analisis.py verificado correctamente.")

    print("\n--- 6. Probando ia.py (Reporte Ejecutivo local) ---")
    reporte_prompt = f"Sos un consultor de administración pública municipal rural. Redactá un Informe Ejecutivo de Gestión Rural basado en las siguientes estadísticas anónimas agregadas: total reclamos {stats['total']}, categorias: {stats['categorias'].to_dict()}"
    reporte = consultar_ia(reporte_prompt)
    print("Reporte generado con éxito:")
    print("\n".join(reporte.split("\n")[:10])) # Muestra las primeras 10 lineas
    assert len(reporte) > 30
    print("ia.py verificado correctamente.")

    print("\n--- TODO VERIFICADO CORRECTAMENTE ---")

if __name__ == "__main__":
    test_workflow()
