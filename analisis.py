import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "datos", "ruralconecta.db")

def cargar_datos_completos():
    """
    Lee todas las solicitudes de la base de datos realizando los JOINs necesarios 
    para obtener los nombres legibles de categorías, subcategorías, estados, barrios y usuarios.
    Retorna un DataFrame.
    """
    columnas = [
        "id", "comentario", "categoria", "subcategoria", "prioridad", "estado", 
        "fecha_creacion", "fecha_resolucion", "barrio", "zona", "score_sentimiento", "urgencia_nlp"
    ]
    try:
        conexion = sqlite3.connect(DB_PATH)
        query = """
            SELECT 
                s.id,
                s.comentario,
                c.nombre AS categoria,
                sub.nombre AS subcategoria,
                s.prioridad,
                est.nombre AS estado,
                s.fecha_creacion,
                s.fecha_resolucion,
                b.nombre AS barrio,
                b.zona AS zona,
                s.score_sentimiento,
                s.urgencia_nlp
            FROM solicitudes s
            LEFT JOIN categorias c ON s.categoria_id = c.id
            LEFT JOIN subcategorias sub ON s.subcategoria_id = sub.id
            LEFT JOIN estados_solicitud est ON s.estado_id = est.id
            LEFT JOIN barrios b ON s.barrio_id = b.id
        """
        df = pd.read_sql_query(query, conexion)
        conexion.close()
        
        if df.empty:
            return pd.DataFrame(columns=columnas)
        return df
    except Exception:
        return pd.DataFrame(columns=columnas)

def generar_estadisticas():
    """
    Genera estadísticas agregadas sobre las solicitudes del municipio usando Pandas.
    """
    df = cargar_datos_completos()
    
    if df.empty:
        return {
            "total": 0,
            "categorias": pd.Series(dtype='int64'),
            "prioridades": pd.Series(dtype='int64'),
            "estados": pd.Series(dtype='int64'),
            "barrios": pd.Series(dtype='int64'),
            "sentimiento_promedio": 0.5,
            "urgentes_total": 0
        }
        
    # Calcular promedio de sentimiento
    sentimiento_promedio = df["score_sentimiento"].mean() if "score_sentimiento" in df.columns else 0.5
    # Calcular total de urgencias
    urgentes_total = int(df["urgencia_nlp"].sum()) if "urgencia_nlp" in df.columns else 0

    return {
        "total": len(df),
        "categorias": df["categoria"].value_counts() if "categoria" in df.columns else pd.Series(dtype='int64'),
        "prioridades": df["prioridad"].value_counts() if "prioridad" in df.columns else pd.Series(dtype='int64'),
        "estados": df["estado"].value_counts() if "estado" in df.columns else pd.Series(dtype='int64'),
        "barrios": df["barrio"].value_counts() if "barrio" in df.columns else pd.Series(dtype='int64'),
        "sentimiento_promedio": float(sentimiento_promedio),
        "urgentes_total": urgentes_total
    }
