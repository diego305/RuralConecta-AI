import sqlite3
from datetime import datetime, timedelta
import random

def obtener_mapeo_estados(conexion):
    """
    Retorna dos diccionarios para mapear dinámicamente los estados de solicitud:
    - id_a_nombre: {id: nombre_estado}
    - nombre_a_id: {nombre_estado_mayuscula: id}
    """
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM estados_solicitud")
    estados = cursor.fetchall()
    id_a_nombre = {e_id: e_nombre for e_id, e_nombre in estados}
    nombre_a_id = {e_nombre.upper(): e_id for e_id, e_nombre in estados}
    return id_a_nombre, nombre_a_id

def obtener_estados_resueltos(conexion):
    """Retorna un conjunto con los IDs de los estados que representan cierre (RESUELTO, RECHAZADO)"""
    _, nombre_a_id = obtener_mapeo_estados(conexion)
    resueltos = set()
    for name in ["RESUELTO", "RECHAZADO"]:
        if name in nombre_a_id:
            resueltos.add(nombre_a_id[name])
    return resueltos

def registrar_cambio_estado(conexion, solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id):
    """Inserta un registro de auditoría en historial_estados"""
    cursor = conexion.cursor()
    fecha_cambio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO historial_estados (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio)
        VALUES (?, ?, ?, ?, ?)
    """, (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio))
    conexion.commit()

def simular_datos_historicos(conexion):
    """
    Pobla la tabla historial_estados con transiciones coherentes para las solicitudes
    existentes para poder probar el motor de auditoría de inmediato.
    """
    cursor = conexion.cursor()
    
    # 1. Limpiar historial previo para evitar duplicaciones
    cursor.execute("DELETE FROM historial_estados")
    conexion.commit()
    
    # 2. Obtener todas las solicitudes
    cursor.execute("SELECT id, fecha_creacion, fecha_resolucion, estado_id, usuario_id, asignado_a FROM solicitudes")
    solicitudes = cursor.fetchall()
    
    id_a_nombre, nombre_a_id = obtener_mapeo_estados(conexion)
    
    # Asegurar que existan los estados típicos
    pendiente_id = nombre_a_id.get('PENDIENTE', 5)
    revision_id = nombre_a_id.get('EN REVISION', 4)
    proceso_id = nombre_a_id.get('EN PROCESO', 3)
    resuelto_id = nombre_a_id.get('RESUELTO', 2)
    rechazado_id = nombre_a_id.get('RECHAZADO', 1)
    
    gestor_por_defecto_id = 4  # ID de Gestor Municipal insertado en pruebas
    registros = []
    
    for s_id, f_creacion_str, f_resolucion_str, est_id, vecino_id, gestor_id in solicitudes:
        # Resolver gestor y vecino responsables
        g_id = gestor_id if gestor_id else gestor_por_defecto_id
        v_id = vecino_id if vecino_id else 1
        
        try:
            f_creacion = datetime.strptime(f_creacion_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            f_creacion = datetime.now() - timedelta(days=random.randint(10, 30))
            f_creacion_str = f_creacion.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE solicitudes SET fecha_creacion = ? WHERE id = ?", (f_creacion_str, s_id))
            
        # Transición inicial: creación (None -> PENDIENTE)
        registros.append((s_id, None, pendiente_id, v_id, f_creacion_str))
        
        if est_id == pendiente_id:
            continue
            
        # Si tiene fecha de resolución o es un estado cerrado
        if est_id in (resuelto_id, rechazado_id):
            if f_resolucion_str:
                try:
                    f_resolucion = datetime.strptime(f_resolucion_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    f_resolucion = f_creacion + timedelta(days=random.randint(1, 5), hours=random.randint(1, 24))
                    f_resolucion_str = f_resolucion.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("UPDATE solicitudes SET fecha_resolucion = ? WHERE id = ?", (f_resolucion_str, s_id))
            else:
                f_resolucion = f_creacion + timedelta(days=random.randint(1, 5), hours=random.randint(1, 24))
                f_resolucion_str = f_resolucion.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE solicitudes SET fecha_resolucion = ? WHERE id = ?", (f_resolucion_str, s_id))
                
            delta = f_resolucion - f_creacion
            segundos_totales = delta.total_seconds()
            
            # PENDIENTE -> EN REVISION (ocurre al 15% del tiempo total)
            f_rev = f_creacion + timedelta(seconds=segundos_totales * 0.15)
            registros.append((s_id, pendiente_id, revision_id, g_id, f_rev.strftime("%Y-%m-%d %H:%M:%S")))
            
            # EN REVISION -> EN PROCESO (ocurre al 50% del tiempo total)
            f_proc = f_creacion + timedelta(seconds=segundos_totales * 0.50)
            registros.append((s_id, revision_id, proceso_id, g_id, f_proc.strftime("%Y-%m-%d %H:%M:%S")))
            
            # EN PROCESO -> RESUELTO/RECHAZADO (al final del tiempo)
            registros.append((s_id, proceso_id, est_id, g_id, f_resolucion_str))
            
        elif est_id == revision_id:
            # PENDIENTE -> EN REVISION (entre 1 y 24 horas después de creación)
            f_rev = f_creacion + timedelta(hours=random.randint(1, 24))
            registros.append((s_id, pendiente_id, revision_id, g_id, f_rev.strftime("%Y-%m-%d %H:%M:%S")))
            
        elif est_id == proceso_id:
            # PENDIENTE -> EN REVISION (1 a 12 horas después)
            f_rev = f_creacion + timedelta(hours=random.randint(1, 12))
            registros.append((s_id, pendiente_id, revision_id, g_id, f_rev.strftime("%Y-%m-%d %H:%M:%S")))
            
            # EN REVISION -> EN PROCESO (12 a 36 horas después)
            f_proc = f_rev + timedelta(hours=random.randint(12, 36))
            registros.append((s_id, revision_id, proceso_id, g_id, f_proc.strftime("%Y-%m-%d %H:%M:%S")))

    # Guardar en base de datos
    cursor.executemany("""
        INSERT INTO historial_estados (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio)
        VALUES (?, ?, ?, ?, ?)
    """, registros)
    conexion.commit()
    return len(registros)

def obtener_kpis_generales(conexion):
    """Calcula y retorna indicadores de rendimiento administrativo consolidados"""
    cursor = conexion.cursor()
    
    # 1. Total reclamos
    cursor.execute("SELECT COUNT(*) FROM solicitudes")
    total = cursor.fetchone()[0]
    
    # 2. Resueltos
    resolved_ids = obtener_estados_resueltos(conexion)
    if not resolved_ids:
        return {"total": total, "resueltos": 0, "tiempo_promedio_hs": 0, "sla_cumplimiento_porc": 0, "vencidos_abiertos": 0}
        
    resolved_placeholders = ",".join("?" for _ in resolved_ids)
    
    cursor.execute(f"SELECT COUNT(*) FROM solicitudes WHERE estado_id IN ({resolved_placeholders})", list(resolved_ids))
    resueltos = cursor.fetchone()[0]
    
    # 3. Tiempo promedio de resolución (en horas)
    cursor.execute(f"""
        SELECT fecha_creacion, fecha_resolucion 
        FROM solicitudes 
        WHERE estado_id IN ({resolved_placeholders}) AND fecha_creacion IS NOT NULL AND fecha_resolucion IS NOT NULL
    """, list(resolved_ids))
    fechas = cursor.fetchall()
    
    tiempo_total_hs = 0.0
    validos = 0
    for f_c_str, f_r_str in fechas:
        try:
            fc = datetime.strptime(f_c_str, "%Y-%m-%d %H:%M:%S")
            fr = datetime.strptime(f_r_str, "%Y-%m-%d %H:%M:%S")
            diff_hs = (fr - fc).total_seconds() / 3600.0
            tiempo_total_hs += diff_hs
            validos += 1
        except Exception:
            pass
            
    tiempo_promedio = (tiempo_total_hs / validos) if validos > 0 else 0.0
    
    # 4. Cumplimiento de SLA
    cursor.execute(f"""
        SELECT s.fecha_creacion, s.fecha_resolucion, c.sla_horas 
        FROM solicitudes s
        JOIN categorias c ON s.categoria_id = c.id
        WHERE s.estado_id IN ({resolved_placeholders}) AND s.fecha_creacion IS NOT NULL AND s.fecha_resolucion IS NOT NULL
    """, list(resolved_ids))
    sla_data = cursor.fetchall()
    
    a_tiempo = 0
    total_con_sla = 0
    for f_c_str, f_r_str, sla_hs in sla_data:
        try:
            fc = datetime.strptime(f_c_str, "%Y-%m-%d %H:%M:%S")
            fr = datetime.strptime(f_r_str, "%Y-%m-%d %H:%M:%S")
            diff_hs = (fr - fc).total_seconds() / 3600.0
            limite = sla_hs if sla_hs is not None else 24
            if diff_hs <= limite:
                a_tiempo += 1
            total_con_sla += 1
        except Exception:
            pass
            
    sla_cumplimiento = (a_tiempo / total_con_sla * 100) if total_con_sla > 0 else 0.0
    
    # 5. Reclamos abiertos que ya superaron su SLA
    cursor.execute(f"""
        SELECT s.fecha_creacion, c.sla_horas 
        FROM solicitudes s
        JOIN categorias c ON s.categoria_id = c.id
        WHERE s.estado_id NOT IN ({resolved_placeholders}) AND s.fecha_creacion IS NOT NULL
    """, list(resolved_ids))
    abiertos = cursor.fetchall()
    
    ahora = datetime.now()
    vencidos = 0
    for f_c_str, sla_hs in abiertos:
        try:
            fc = datetime.strptime(f_c_str, "%Y-%m-%d %H:%M:%S")
            diff_hs = (ahora - fc).total_seconds() / 3600.0
            limite = sla_hs if sla_hs is not None else 24
            if diff_hs > limite:
                vencidos += 1
        except Exception:
            pass
            
    return {
        "total": total,
        "resueltos": resueltos,
        "tiempo_promedio_hs": tiempo_promedio,
        "sla_cumplimiento_porc": sla_cumplimiento,
        "vencidos_abiertos": vencidos
    }

def reporte_desempeno_categorias(conexion):
    """Genera e imprime un reporte estructurado de rendimiento por categoría"""
    cursor = conexion.cursor()
    resolved_ids = obtener_estados_resueltos(conexion)
    resolved_placeholders = ",".join("?" for _ in resolved_ids)
    
    # Obtener todas las categorías
    cursor.execute("SELECT id, nombre, sla_horas FROM categorias")
    categorias = cursor.fetchall()
    
    print("\n" + "="*144)
    print(f"| {'DESEMPEÑO POR CATEGORÍA DE SERVICIO':^140} |")
    print("="*144)
    print(f"| {'Categoría':<35} | {'SLA (Horas)':<11} | {'Total':<5} | {'Resueltos':<9} | {'Promedio Resolución (Horas)':<28} | {'Cumplimiento SLA':<16} | {'Vencidos Activos':<16} |")
    print("-"*144)
    
    ahora = datetime.now()
    
    for cat_id, nombre, sla_hs in categorias:
        limite = sla_hs if sla_hs is not None else 24
        
        # 1. Total en esta categoría
        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE categoria_id = ?", (cat_id,))
        cat_total = cursor.fetchone()[0]
        
        # 2. Resueltos
        query_resueltos = f"SELECT COUNT(*) FROM solicitudes WHERE categoria_id = ? AND estado_id IN ({resolved_placeholders})"
        cursor.execute(query_resueltos, [cat_id] + list(resolved_ids))
        cat_resueltos = cursor.fetchone()[0]
        
        # 3. Promedio e SLA
        query_fechas = f"""
            SELECT fecha_creacion, fecha_resolucion 
            FROM solicitudes 
            WHERE categoria_id = ? AND estado_id IN ({resolved_placeholders}) AND fecha_creacion IS NOT NULL AND fecha_resolucion IS NOT NULL
        """
        cursor.execute(query_fechas, [cat_id] + list(resolved_ids))
        fechas = cursor.fetchall()
        
        tiempo_total_hs = 0.0
        validos = 0
        a_tiempo = 0
        for f_c_str, f_r_str in fechas:
            try:
                fc = datetime.strptime(f_c_str, "%Y-%m-%d %H:%M:%S")
                fr = datetime.strptime(f_r_str, "%Y-%m-%d %H:%M:%S")
                diff_hs = (fr - fc).total_seconds() / 3600.0
                tiempo_total_hs += diff_hs
                validos += 1
                if diff_hs <= limite:
                    a_tiempo += 1
            except Exception:
                pass
                
        cat_promedio = (tiempo_total_hs / validos) if validos > 0 else 0.0
        cat_sla_porc = (a_tiempo / validos * 100) if validos > 0 else 100.0 if cat_total == 0 else 0.0
        
        # 4. Abiertos vencidos
        query_abiertos = f"""
            SELECT fecha_creacion 
            FROM solicitudes 
            WHERE categoria_id = ? AND estado_id NOT IN ({resolved_placeholders}) AND fecha_creacion IS NOT NULL
        """
        cursor.execute(query_abiertos, [cat_id] + list(resolved_ids))
        abiertos = cursor.fetchall()
        
        cat_vencidos = 0
        for (f_c_str,) in abiertos:
            try:
                fc = datetime.strptime(f_c_str, "%Y-%m-%d %H:%M:%S")
                diff_hs = (ahora - fc).total_seconds() / 3600.0
                if diff_hs > limite:
                    cat_vencidos += 1
            except Exception:
                pass
                
        nombre_corto = nombre[:33] + ".." if len(nombre) > 35 else nombre
        sla_cumplimiento_formato = f"{cat_sla_porc:.1f}%"
        print(f"| {nombre_corto:<35} | {limite:<11} | {cat_total:<5} | {cat_resueltos:<9} | {cat_promedio:<28.1f} | {sla_cumplimiento_formato:<16} | {cat_vencidos:<16} |")
        
    print("="*144)

def reporte_cuellos_botella(conexion):
    """
    Analiza el flujo de trabajo midiendo el tiempo promedio de permanencia
    por estado utilizando la tabla historial_estados.
    """
    cursor = conexion.cursor()
    id_a_nombre, nombre_a_id = obtener_mapeo_estados(conexion)
    resolved_ids = obtener_estados_resueltos(conexion)
    
    # 1. Obtener todas las transiciones en historial
    cursor.execute("""
        SELECT solicitud_id, estado_anterior_id, estado_nuevo_id, fecha_cambio 
        FROM historial_estados 
        ORDER BY solicitud_id, fecha_cambio ASC
    """)
    transiciones = cursor.fetchall()
    
    if not transiciones:
        print("\n[i] No hay registros en el historial de estados para realizar el análisis de cuellos de botella.")
        print("[!] Por favor, ejecute primero la opción de 'Simulación de Historial' en este menú.")
        return
        
    # 2. Obtener fechas de creación y finalización de cada solicitud
    cursor.execute("SELECT id, fecha_creacion, fecha_resolucion, estado_id FROM solicitudes")
    solicitud_limites = {row[0]: {"creacion": row[1], "resolucion": row[2], "estado_actual_id": row[3]} for row in cursor.fetchall()}
    
    # Estructura para agrupar transiciones por solicitud
    transiciones_por_solicitud = {}
    for s_id, est_ant, est_nue, f_cambio_str in transiciones:
        if s_id not in transiciones_por_solicitud:
            transiciones_por_solicitud[s_id] = []
        transiciones_por_solicitud[s_id].append((est_ant, est_nue, f_cambio_str))
        
    # Variables de acumulación: {estado_id: (tiempo_total_segundos, cantidad_visitas)}
    tiempo_por_estado = {}
    ahora = datetime.now()
    
    for s_id, data in solicitud_limites.items():
        # Obtener puntos de control en el tiempo para la solicitud
        checkpoints = [] # lista de (estado_id, datetime_objeto)
        
        # Fecha de creación como inicio
        try:
            fc = datetime.strptime(data["creacion"], "%Y-%m-%d %H:%M:%S")
            # El estado inicial asumido es PENDIENTE (o el primero registrado)
            checkpoints.append((nombre_a_id.get('PENDIENTE', 5), fc))
        except Exception:
            continue
            
        # Añadir cambios de estado del historial
        s_transiciones = transiciones_por_solicitud.get(s_id, [])
        for est_ant, est_nue, f_cambio_str in s_transiciones:
            try:
                ft = datetime.strptime(f_cambio_str, "%Y-%m-%d %H:%M:%S")
                # Si es la primera transición None -> PENDIENTE, ajusta la fecha si es necesario
                if est_ant is None:
                    # Sobrescribir el checkpoint inicial con la fecha del historial
                    checkpoints[0] = (est_nue, ft)
                else:
                    checkpoints.append((est_nue, ft))
            except Exception:
                pass
                
        # Asegurar orden cronológico de checkpoints
        checkpoints.sort(key=lambda x: x[1])
        
        # Agregar punto de control final
        estado_final_id = data["estado_actual_id"]
        if estado_final_id in resolved_ids and data["resolucion"]:
            try:
                fr = datetime.strptime(data["resolucion"], "%Y-%m-%d %H:%M:%S")
                checkpoints.append((estado_final_id, fr))
            except Exception:
                checkpoints.append((estado_final_id, ahora))
        else:
            checkpoints.append((estado_final_id, ahora))
            
        # Calcular duración en cada intervalo
        for i in range(len(checkpoints) - 1):
            est_id = checkpoints[i][0]
            dt_inicio = checkpoints[i][1]
            dt_fin = checkpoints[i+1][1]
            
            duracion_seg = (dt_fin - dt_inicio).total_seconds()
            if duracion_seg < 0:
                duracion_seg = 0  # Evitar inconsistencias de reloj
                
            if est_id not in tiempo_por_estado:
                tiempo_por_estado[est_id] = [0.0, 0]
            tiempo_por_estado[est_id][0] += duracion_seg
            # Solo incrementamos visitas si la duración fue significativa (> 0.1 min) o es cambio de estado
            tiempo_por_estado[est_id][1] += 1
            
    # Imprimir Reporte de Cuello de Botella
    print("\n" + "="*65)
    print(f"| {'ANÁLISIS DE CUELLOS DE BOTELLA (TIEMPOS DE PERMANENCIA)':^61} |")
    print("="*65)
    print(f"| {'Estado de la Solicitud':<25} | {'Visitas':<10} | {'Permanencia Promedio':<22} |")
    print("-"*65)
    
    # Ordenar estados del flujo típico: PENDIENTE, EN REVISION, EN PROCESO, etc.
    orden_sugerido = ['PENDIENTE', 'EN REVISION', 'EN PROCESO', 'RESUELTO', 'RECHAZADO']
    orden_ids = []
    
    for nombre in orden_sugerido:
        if nombre in nombre_a_id:
            orden_ids.append(nombre_a_id[nombre])
            
    # Añadir cualquier otro ID de estado no considerado en el orden sugerido
    for est_id in tiempo_por_estado.keys():
        if est_id not in orden_ids:
            orden_ids.append(est_id)
            
    for est_id in orden_ids:
        if est_id not in tiempo_por_estado:
            continue
            
        segundos_totales, visitas = tiempo_por_estado[est_id]
        visitas_reales = max(1, visitas)
        segundos_promedio = segundos_totales / visitas_reales
        
        # Formatear la permanencia de forma legible (Días, Horas, Minutos)
        horas = segundos_promedio / 3600.0
        if horas >= 24:
            dias = int(horas // 24)
            hs_restantes = horas % 24
            permanencia_str = f"{dias}d {hs_restantes:.1f}h"
        elif horas >= 1:
            permanencia_str = f"{horas:.1f} horas"
        else:
            minutos = segundos_promedio / 60.0
            permanencia_str = f"{minutos:.1f} minutos"
            
        nombre_estado = id_a_nombre.get(est_id, f"ID: {est_id}")
        
        # Para estados de cierre, la permanencia representa el tiempo acumulado hasta el archivo final
        if est_id in resolved_ids:
            nombre_estado += " (Cierre)"
            
        print(f"| {nombre_estado:<25} | {visitas:<10} | {permanencia_str:<22} |")
        
    print("="*65)
    print("[Nota] La permanencia promedio mide el tiempo neto que una solicitud")
    print("       espera en ese estado antes de ser promovida o cerrada.")

def trazabilidad_solicitud(conexion, solicitud_id):
    """Muestra la hoja de ruta y auditoría de flujo para una solicitud específica"""
    cursor = conexion.cursor()
    id_a_nombre, _ = obtener_mapeo_estados(conexion)
    
    # 1. Buscar detalles de la solicitud
    cursor.execute("""
        SELECT s.id, s.comentario, s.fecha_creacion, s.fecha_resolucion, s.prioridad, 
               c.nombre AS cat_nombre, e.nombre AS est_nombre, 
               u_vec.nombre || ' ' || u_vec.apellido AS vecino_completo,
               u_gest.nombre || ' ' || u_gest.apellido AS gestor_completo
        FROM solicitudes s
        LEFT JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN estados_solicitud e ON s.estado_id = e.id
        LEFT JOIN usuarios u_vec ON s.usuario_id = u_vec.id
        LEFT JOIN usuarios u_gest ON s.asignado_a = u_gest.id
        WHERE s.id = ?
    """, (solicitud_id,))
    
    sol = cursor.fetchone()
    if not sol:
        print(f"[-] No se encontró ninguna solicitud con ID {solicitud_id}.")
        return
        
    s_id, comentario, f_creacion, f_resolucion, prioridad, cat, estado, vecino, gestor = sol
    
    print("\n" + "="*70)
    print(f"| {'HOJA DE TRAZABILIDAD DEL RECLAMO #' + str(s_id):^66} |")
    print("="*70)
    print(f"Vecino Reportante : {vecino or 'Anónimo / Sin asignar'}")
    print(f"Categoría         : {cat or 'Sin Categoría'}")
    print(f"Prioridad         : {prioridad or 'Baja'}")
    print(f"Estado Actual     : {estado or 'PENDIENTE'}")
    print(f"Gestor Asignado   : {gestor or 'Sin Asignar'}")
    print(f"Fecha de Ingreso  : {f_creacion}")
    print(f"Fecha de Cierre   : {f_resolucion or 'Activo / En Gestión'}")
    print("-" * 70)
    print("Comentario original:")
    print(f'"{comentario}"')
    print("-" * 70)
    
    # 2. Consultar historial de transiciones
    cursor.execute("""
        SELECT h.fecha_cambio, 
               e_ant.nombre AS estado_anterior, 
               e_nue.nombre AS estado_nuevo, 
               u.nombre || ' ' || u.apellido AS responsable,
               u.rol_id
        FROM historial_estados h
        LEFT JOIN estados_solicitud e_ant ON h.estado_anterior_id = e_ant.id
        LEFT JOIN estados_solicitud e_nue ON h.estado_nuevo_id = e_nue.id
        LEFT JOIN usuarios u ON h.usuario_id = u.id
        WHERE h.solicitud_id = ?
        ORDER BY h.fecha_cambio ASC
    """, (solicitud_id,))
    
    historial = cursor.fetchall()
    
    print("CRONOLOGÍA DE AUDITORÍA Y FLUJO:")
    if not historial:
        print("  (No hay eventos de transición registrados en historial_estados para este reclamo)")
    else:
        for idx, (fecha, est_ant, est_nue, operador, rol_id) in enumerate(historial):
            operador_str = operador or "Sistema (Automático)"
            rol_desc = "Vecino" if rol_id == 1 else "Gestor" if rol_id == 2 else "Analista" if rol_id == 3 else "Usuario"
            
            if est_ant is None:
                print(f"  [{fecha}] -> CREADO e ingresado como '{est_nue}' por {operador_str} ({rol_desc})")
            else:
                print(f"  [{fecha}] -> CAMBIO DE ESTADO: '{est_ant}' ===> '{est_nue}'")
                print(f"                 Autorizado por: {operador_str} ({rol_desc})")
                
    # 3. Calcular tiempo transcurrido
    try:
        fc = datetime.strptime(f_creacion, "%Y-%m-%d %H:%M:%S")
        if f_resolucion:
            fr = datetime.strptime(f_resolucion, "%Y-%m-%d %H:%M:%S")
            tiempo_total = fr - fc
            print("-" * 70)
            print(f"TIEMPO TOTAL DE RESOLUCIÓN: {tiempo_total.days} días, {tiempo_total.seconds // 3600} horas, {(tiempo_total.seconds % 3600) // 60} minutos.")
        else:
            tiempo_total = datetime.now() - fc
            print("-" * 70)
            print(f"TIEMPO ACTIVO EN BANDEJA: {tiempo_total.days} días, {tiempo_total.seconds // 3600} horas, {(tiempo_total.seconds % 3600) // 60} minutos.")
    except Exception:
        pass
        
    print("="*70)

def reporte_alertas_sla(conexion):
    """Muestra las solicitudes abiertas que excedieron el tiempo límite estipulado por el SLA"""
    cursor = conexion.cursor()
    resolved_ids = obtener_estados_resueltos(conexion)
    resolved_placeholders = ",".join("?" for _ in resolved_ids)
    
    # Obtener solicitudes abiertas
    cursor.execute(f"""
        SELECT s.id, s.fecha_creacion, s.prioridad, c.nombre AS cat_nombre, c.sla_horas,
               u_gest.nombre || ' ' || u_gest.apellido AS gestor_nombre,
               e.nombre AS est_nombre
        FROM solicitudes s
        JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN usuarios u_gest ON s.asignado_a = u_gest.id
        LEFT JOIN estados_solicitud e ON s.estado_id = e.id
        WHERE s.estado_id NOT IN ({resolved_placeholders}) AND s.fecha_creacion IS NOT NULL
        ORDER BY s.fecha_creacion ASC
    """, list(resolved_ids))
    
    abiertos = cursor.fetchall()
    ahora = datetime.now()
    alertas = []
    
    for s_id, f_creacion_str, prioridad, cat, sla_hs, gestor, estado in abiertos:
        try:
            fc = datetime.strptime(f_creacion_str, "%Y-%m-%d %H:%M:%S")
            diff_hs = (ahora - fc).total_seconds() / 3600.0
            limite = sla_hs if sla_hs is not None else 24
            
            if diff_hs > limite:
                horas_exceso = diff_hs - limite
                alertas.append({
                    "id": s_id,
                    "fecha_creacion": f_creacion_str,
                    "prioridad": prioridad or "BAJA",
                    "categoria": cat,
                    "sla_limite": limite,
                    "retraso_hs": horas_exceso,
                    "gestor": gestor or "Sin Asignar",
                    "estado": estado
                })
        except Exception:
            pass
            
    # Ordenar alertas: Prioridad (ALTA, MEDIA, BAJA) y luego por retraso DESC
    prioridad_map = {"ALTA": 1, "MEDIA": 2, "BAJA": 3}
    alertas.sort(key=lambda x: (prioridad_map.get(x["prioridad"], 3), -x["retraso_hs"]))
    
    print("\n" + "="*95)
    print(f"| {'ALERTAS CRÍTICAS: RECLAMOS ABIERTOS FUERA DE SLA':^91} |")
    print("="*95)
    print(f"| {'ID':<5} | {'Prioridad':<9} | {'Categoría':<25} | {'Estado':<12} | {'SLA Lím':<8} | {'Retraso':<11} | {'Gestor Asignado':<16} |")
    print("-"*95)
    
    if not alertas:
        print(f"| {'Felicidades! No hay reclamos activos fuera de SLA en este momento.':^91} |")
    else:
        for a in alertas:
            retraso = a["retraso_hs"]
            if retraso >= 24:
                retraso_str = f"{int(retraso // 24)}d {retraso % 24:.1f}h"
            else:
                retraso_str = f"{retraso:.1f} hs"
                
            cat_corta = a["categoria"][:23] + ".." if len(a["categoria"]) > 25 else a["categoria"]
            gestor_corto = a["gestor"][:14] + ".." if len(a["gestor"]) > 16 else a["gestor"]
            
            print(f"| {a['id']:<5} | {a['prioridad']:<9} | {cat_corta:<25} | {a['estado']:<12} | {a['sla_limite']:<4} hs  | {retraso_str:<11} | {gestor_corto:<16} |")
            
    print("="*95)
    print(f"[Total de Alertas Activas: {len(alertas)} reclamos demorados]")

def reporte_desempeno_gestores(conexion):
    """Analiza la carga y eficiencia de resolución de los diferentes gestores de la administración"""
    cursor = conexion.cursor()
    id_a_nombre, _ = obtener_mapeo_estados(conexion)
    resolved_ids = obtener_estados_resueltos(conexion)
    resolved_placeholders = ",".join("?" for _ in resolved_ids)
    
    # Obtener todos los usuarios del rol de gestión (De Gestión = 2, o cualquier otro asignado)
    cursor.execute("""
        SELECT u.id, u.nombre || ' ' || u.apellido AS nombre_completo 
        FROM usuarios u
        WHERE u.rol_id = 2 OR u.id IN (SELECT DISTINCT asignado_a FROM solicitudes WHERE asignado_a IS NOT NULL)
    """)
    gestores = cursor.fetchall()
    
    print("\n" + "="*85)
    print(f"| {'DESEMPEÑO Y CARGA DE TRABAJO POR GESTOR':^81} |")
    print("="*85)
    print(f"| {'Nombre del Gestor':<25} | {'Activos':<8} | {'Resueltos':<10} | {'Prom.Resol(h)':<13} | {'SLA Cumplim.':<12} |")
    print("-"*85)
    
    for g_id, nombre in gestores:
        # 1. Solicitudes activas asignadas a él
        cursor.execute(f"SELECT COUNT(*) FROM solicitudes WHERE asignado_a = ? AND estado_id NOT IN ({resolved_placeholders})", [g_id] + list(resolved_ids))
        activos = cursor.fetchone()[0]
        
        # 2. Solicitudes cerradas (historial indica que él hizo el cambio al estado resuelto/rechazado)
        # O simplemente asignadas a él y resueltas. Vamos a cruzar con solicitudes asignadas y resueltas
        cursor.execute(f"""
            SELECT s.fecha_creacion, s.fecha_resolucion, c.sla_horas
            FROM solicitudes s
            JOIN categorias c ON s.categoria_id = c.id
            WHERE s.asignado_a = ? AND s.estado_id IN ({resolved_placeholders}) AND s.fecha_creacion IS NOT NULL AND s.fecha_resolucion IS NOT NULL
        """, [g_id] + list(resolved_ids))
        resueltos_data = cursor.fetchall()
        
        resueltos_cant = len(resueltos_data)
        
        tiempo_total_hs = 0.0
        a_tiempo = 0
        validos = 0
        
        for f_c_str, f_r_str, sla_hs in resueltos_data:
            try:
                fc = datetime.strptime(f_c_str, "%Y-%m-%d %H:%M:%S")
                fr = datetime.strptime(f_r_str, "%Y-%m-%d %H:%M:%S")
                diff_hs = (fr - fc).total_seconds() / 3600.0
                tiempo_total_hs += diff_hs
                validos += 1
                limite = sla_hs if sla_hs is not None else 24
                if diff_hs <= limite:
                    a_tiempo += 1
            except Exception:
                pass
                
        promedio_hs = (tiempo_total_hs / validos) if validos > 0 else 0.0
        sla_porc = (a_tiempo / validos * 100) if validos > 0 else 100.0 if resueltos_cant == 0 else 0.0
        
        print(f"| {nombre:<25} | {activos:<8} | {resueltos_cant:<10} | {promedio_hs:<13.1f} | {sla_porc:<11.1f}% |")
        
    print("="*85)

def mostrar_menu_auditoria(conexion, usuario_id):
    """Interfaz de línea de comandos para el módulo de auditoría de rendimiento"""
    while True:
        kpis = obtener_kpis_generales(conexion)
        
        print("\n" + "="*50)
        print("=== PANEL DE AUDITORÍA Y TRAZABILIDAD DE FLUJO ===")
        print("="*50)
        print(f" Reclamos en Sistema  : {kpis['total']}")
        print(f" Resueltos / Cerrados : {kpis['resueltos']}")
        print(f" Promedio Resolución  : {kpis['tiempo_promedio_hs']:.1f} horas")
        print(f" Cumplimiento de SLA  : {kpis['sla_cumplimiento_porc']:.1f}%")
        print(f" Alertas Activas (SLA): {kpis['vencidos_abiertos']} demorados")
        print("-" * 50)
        print("1. Reporte de Desempeño por Categoría")
        print("2. Análisis de Cuellos de Botella (Dwell Times)")
        print("3. Trazabilidad Cronológica de un Reclamo")
        print("4. Ver Alertas de Desviación y SLA Excedido")
        print("5. Reporte de Desempeño de Gestores")
        print("6. Simular/Resetear Historial de Auditoría (Testing)")
        print("7. Volver al Menú Principal")
        print("-" * 50)
        
        opcion = input("Seleccione un reporte u opción: ").strip()
        
        if opcion == "1":
            reporte_desempeno_categorias(conexion)
            input("\nPresione Enter para continuar...")
        elif opcion == "2":
            reporte_cuellos_botella(conexion)
            input("\nPresione Enter para continuar...")
        elif opcion == "3":
            s_id_str = input("\nIngrese el ID de la solicitud a investigar: ").strip()
            if s_id_str:
                try:
                    s_id = int(s_id_str)
                    trazabilidad_solicitud(conexion, s_id)
                except ValueError:
                    print("[-] ID inválido.")
            input("\nPresione Enter para continuar...")
        elif opcion == "4":
            reporte_alertas_sla(conexion)
            input("\nPresione Enter para continuar...")
        elif opcion == "5":
            reporte_desempeno_gestores(conexion)
            input("\nPresione Enter para continuar...")
        elif opcion == "6":
            confirmar = input("\n¿Está seguro de reiniciar y simular el historial de transiciones? (s/n): ").strip().lower()
            if confirmar == "s":
                print("[...] Generando base histórica de auditoría (100% consistente)...")
                total_creado = simular_datos_historicos(conexion)
                print(f"[+] Simulación exitosa. Se insertaron {total_creado} transiciones de estado.")
            input("\nPresione Enter para continuar...")
        elif opcion == "7":
            break
        else:
            print("[-] Opción inválida.")
