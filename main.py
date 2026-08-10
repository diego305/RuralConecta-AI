from analizador import analizar_comentario
from respuestas import generar_respuesta
import sqlite3
from datetime import datetime
import os
import typing_extensions
import hashlib
import trazabilidad

def hash_password(clave_plana):
    salt = "ruralconecta_secure_salt_2026"
    return hashlib.sha256((clave_plana + salt).encode()).hexdigest()

def verify_password(clave_plana, clave_hasheada):
    return hash_password(clave_plana) == clave_hasheada

def guardar_reclamo_db(comentario, analisis, usuario_id=None, conexion=None):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "datos", "ruralconecta.db")
        
        cerrar_conexion = False
        if conexion is None:
            conexion = sqlite3.connect(db_path)
            conexion.execute("PRAGMA foreign_keys = ON;")
            cerrar_conexion = True
            
        cursor = conexion.cursor()
        
        cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (analisis["categoria"],))
        res_cat = cursor.fetchone()
        cat_id = res_cat[0] if res_cat else 1
        
        cursor.execute("SELECT id FROM subcategorias WHERE nombre = ?", (analisis["subcategoria"],))
        sub_res = cursor.fetchone()
        sub_id = sub_res[0] if sub_res else None
        
        cursor.execute("SELECT id FROM estados_solicitud WHERE nombre = 'PENDIENTE'")
        res_est = cursor.fetchone()
        estado_id = res_est[0] if res_est else 1
        
        cursor.execute("SELECT id FROM barrios LIMIT 1")
        barrio_res = cursor.fetchone()
        barrio_id = barrio_res[0] if barrio_res else 1
        
        cursor.execute("""
        INSERT INTO solicitudes(
            comentario, categoria_id, subcategoria_id, prioridad, estado_id, 
            fecha_creacion, score_sentimiento, urgencia_nlp, usuario_id, barrio_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comentario, cat_id, sub_id, analisis["prioridad"], estado_id, 
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), analisis["score_sentimiento"], analisis["urgencia_nlp"],
            usuario_id, barrio_id
        ))
        
        last_id = cursor.lastrowid
        
        # Registrar la creación en el historial
        try:
            trazabilidad.registrar_cambio_estado(conexion, last_id, None, estado_id, usuario_id)
        except Exception as e:
            print(f"Error al registrar historial inicial: {e}")
            
        conexion.commit()
        
        if cerrar_conexion:
            conexion.close()
            
        return last_id
    except Exception as e:
        print(f"Error al guardar en base de datos: {e}")
        return None

def inicializar_db_completo(conexion):
    cursor = conexion.cursor()
    
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
    
    # NUEVA ESTRUCTURA DE USUARIOS
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
    CREATE TABLE IF NOT EXISTS barrios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        zona TEXT
    )
    """)
    
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

    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO roles (id, nombre) VALUES (?, ?)", [
            (1, "Ciudadano Rural"),
            (2, "De Gestión")
        ])
        conexion.commit()

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
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO categorias (nombre, sla_horas, estacionalidad_alta) VALUES (?, ?, ?)", categorias)
        conexion.commit()

    cursor.execute("SELECT COUNT(*) FROM subcategorias")
    if cursor.fetchone()[0] == 0:
        subcategorias_data = {
            "Red Vial Rural y Caminos": [
                "Baches y Pozos en Caminos de Tierra / Ripio",
                "Caminos Intransitables por Lluvias o Inundación",
                "Zanjeo, Cunetas y Escurrimiento de Agua",
                "Puentes y Badenes en Mal Estado",
                "Desmalezado de Banquinas y Caminos Rurales"
            ],
            "Agua Potable Rural y Riego": [
                "Falta de Agua en Tanque / Pozo Comunitario",
                "Rotura de Cañería / Red de Agua Rural",
                "Problemas en Canales de Riego / Acequias",
                "Bomba de Agua Defectuosa o Sin Funcionamiento",
                "Calidad o Turbidez del Agua"
            ],
            "Electrificación y Alumbrado Rural": [
                "Corte de Luz en Paraje / Zona Rural",
                "Poste Caído o En Peligro",
                "Luminaria Pública Defectuosa en Paraje",
                "Cables Sueltos o Con Riesgo Eléctrico",
                "Baja Tensión / Fluctuación Eléctrica en Red Rural"
            ],
            "Residuos y Limpieza Rural": [
                "Retiro de Residuos en Puntos de Acopio Rurales",
                "Microbasural o Vuelco Clandestino en Caminos",
                "Limpieza de Espacios Públicos y Plazas de Parajes",
                "Acumulación de Chatarra o Envases Agroquímicos"
            ],
            "Zoonosis y Control de Plagas Rurales": [
                "Animales de Granja o Equinos Sueltos en Rutas/Caminos",
                "Plagas Agrícolas / Invertebrados (Langostas, Mosquitos, Roedores)",
                "Vacunación y Castración en Parajes Rurales",
                "Ataque de Depredadores / Control de Animales Silvestres"
            ],
            "Medio Ambiente y Recurso Forestal": [
                "Riesgo de Incendio Forestal / Quemas No Autorizadas",
                "Caída de Árboles o Ramas Grandes en Caminos",
                "Contaminación de Cauces de Agua o Suelos",
                "Poda y Despeje de Cableado en Zonas Rurales"
            ],
            "Infraestructura Comunitaria Rural": [
                "Mantenimiento de Centro Comunitario / Salón del Paraje",
                "Falta de Señalización en Caminos Rurales",
                "Paradas de Colectivo Rural en Mal Estado",
                "Salud Rural / Puesto Sanitario"
            ],
            "Convivencia y Mediación Rural": [
                "Disputas por Límites de Propiedad o Alambrados",
                "Uso Compartido de Agua de Riego",
                "Conflictos por Animales Invasores en Cultivos",
                "Ruidos Molestos o Eventos No Autorizados"
            ]
        }
        for cat_nombre, subcats in subcategorias_data.items():
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (cat_nombre,))
            res = cursor.fetchone()
            if res:
                cat_id = res[0]
                for sub in subcats:
                    cursor.execute("INSERT INTO subcategorias (nombre, categoria_id) VALUES (?, ?)", (sub, cat_id))
        conexion.commit()

    estados = [("PENDIENTE",), ("EN REVISION",), ("EN PROCESO",), ("RESUELTO",), ("RECHAZADO",)]
    cursor.execute("SELECT COUNT(*) FROM estados_solicitud")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO estados_solicitud (nombre) VALUES (?)", estados)
        conexion.commit()
        
    cursor.execute("SELECT COUNT(*) FROM barrios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO barrios (nombre, zona) VALUES ('Paraje Centro', 'Centro')")
        conexion.commit()

    # Inicializar catálogo de permisos
    cursor.execute("SELECT COUNT(*) FROM permisos")
    if cursor.fetchone()[0] == 0:
        permisos_seed = [
            ("CREAR_RECLAMO", "Permite ingresar reclamos en el sistema."),
            ("VER_RECLAMOS_PROPIOS", "Permite al vecino seguir y ver sus propios reclamos."),
            ("VER_HISTORIAL_RECLAMOS", "Permite ver el historial completo de reclamos del municipio."),
            ("MODIFICAR_RECLAMO", "Permite editar información y estados de los reclamos."),
            ("ELIMINAR_RECLAMO", "Permite borrar reclamos del sistema."),
            ("GESTIONAR_USUARIOS", "Permite realizar operaciones CRUD de usuarios."),
            ("GESTIONAR_ROLES_PERMISOS", "Permite crear roles y asociar/revocar permisos.")
        ]
        cursor.executemany("INSERT INTO permisos (nombre, descripcion) VALUES (?, ?)", permisos_seed)
        conexion.commit()

    # Inicializar mapeo roles_permisos
    cursor.execute("SELECT COUNT(*) FROM roles_permisos")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, nombre FROM permisos")
        permiso_ids = {nombre: p_id for p_id, nombre in cursor.fetchall()}
        
        roles_permisos_seed = []
        # Vecino (ID 1)
        vecino_permisos = ["CREAR_RECLAMO", "VER_RECLAMOS_PROPIOS"]
        for perm in vecino_permisos:
            if perm in permiso_ids:
                roles_permisos_seed.append((1, permiso_ids[perm]))
                
        # De Gestión (ID 2)
        gestion_permisos = [
            "CREAR_RECLAMO", 
            "VER_HISTORIAL_RECLAMOS", 
            "MODIFICAR_RECLAMO", 
            "ELIMINAR_RECLAMO", 
            "GESTIONAR_USUARIOS", 
            "GESTIONAR_ROLES_PERMISOS"
        ]
        for perm in gestion_permisos:
            if perm in permiso_ids:
                roles_permisos_seed.append((2, permiso_ids[perm]))
                
        cursor.executemany("INSERT INTO roles_permisos (rol_id, permiso_id) VALUES (?, ?)", roles_permisos_seed)
        conexion.commit()

def listar_usuarios(conexion):
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre || ' ' || u.apellido AS nombre_completo, r.nombre 
        FROM usuarios u 
        LEFT JOIN roles r ON u.rol_id = r.id
    """)
    usuarios = cursor.fetchall()
    if not usuarios:
        print("\n[i] No hay usuarios registrados en el sistema.")
        return []
    
    print("\n" + "-"*55)
    print(f"{'ID':<5} | {'Nombre Completo':<30} | {'Rol':<15}")
    print("-"*55)
    for u_id, nombre, rol in usuarios:
        print(f"{u_id:<5} | {nombre:<30} | {rol or 'Sin Rol':<15}")
    print("-"*55)
    return usuarios

def alta_usuario(conexion):
    print("\n--- Alta de Usuario ---")
    print("Seleccione el rol:")
    print("1. Vecino")
    print("2. De Gestión")
    rol_opt = input("Opción (1 o 2): ").strip()
    
    if rol_opt == "1":
        rol_id = 1
    elif rol_opt == "2":
        rol_id = 2
    else:
        print("[-] Opción de rol inválida. Registro cancelado.")
        return

    nombre = input("Ingrese el Nombre: ").strip()
    apellido = input("Ingrese el Apellido: ").strip()
    dni = input("Ingrese el DNI: ").strip()
    cuil = input("Ingrese el CUIL: ").strip()
    clave = input("Cree una clave para loggearse: ").strip()

    if not nombre or not apellido or not dni or not cuil or not clave:
        print("[-] Todos los campos son obligatorios. Registro cancelado.")
        return
        
    cursor = conexion.cursor()
    try:
        clave_hasheada = hash_password(clave)
        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, dni, cuil, clave_hasheada, rol_id))
        conexion.commit()
        print(f"[+] Usuario '{nombre} {apellido}' creado con éxito. ID asignado: {cursor.lastrowid}")
    except sqlite3.IntegrityError:
        print("[-] Error: El DNI o CUIL ya se encuentran registrados en el sistema.")
    except Exception as e:
        print(f"[-] Error al crear el usuario: {e}")

def baja_usuario(conexion):
    print("\n--- Baja de Usuario ---")
    usuarios = listar_usuarios(conexion)
    if not usuarios:
        return
    
    u_id_str = input("Ingrese el ID del usuario a eliminar (o Enter para cancelar): ").strip()
    if not u_id_str:
        return
    
    try:
        u_id = int(u_id_str)
    except ValueError:
        print("[-] ID inválido.")
        return
    
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre || ' ' || apellido FROM usuarios WHERE id = ?", (u_id,))
    res = cursor.fetchone()
    if not res:
        print("[-] No se encontró ningún usuario con ese ID.")
        return
    
    nombre_completo = res[0]
    confirmar = input(f"¿Está seguro de eliminar al usuario '{nombre_completo}' (ID: {u_id})? (s/n): ").strip().lower()
    if confirmar == "s":
        try:
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (u_id,))
            conexion.commit()
            print(f"[+] Usuario '{nombre_completo}' (ID: {u_id}) eliminado correctamente.")
        except sqlite3.IntegrityError:
            print(f"\n[-] Error: No se puede eliminar a '{nombre_completo}' porque tiene reclamos asociados.")
        except Exception as e:
            print(f"[-] Error al eliminar usuario: {e}")

def modificar_usuario(conexion):
    print("\n--- Modificar Usuario ---")
    usuarios = listar_usuarios(conexion)
    if not usuarios:
        return
        
    u_id_str = input("Ingrese el ID del usuario a modificar (o Enter para cancelar): ").strip()
    if not u_id_str:
        return
        
    try:
        u_id = int(u_id_str)
    except ValueError:
        print("[-] ID inválido.")
        return
        
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, apellido, dni, cuil, rol_id FROM usuarios WHERE id = ?", (u_id,))
    res = cursor.fetchone()
    if not res:
        print("[-] No se encontró ningún usuario con ese ID.")
        return
        
    nombre_actual, apellido_actual, dni_actual, cuil_actual, rol_id_actual = res
    print(f"Nombre actual: {nombre_actual}")
    nuevo_nombre = input("Nuevo nombre (deje vacío para no cambiar): ").strip() or nombre_actual
    
    print(f"Apellido actual: {apellido_actual}")
    nuevo_apellido = input("Nuevo apellido (deje vacío para no cambiar): ").strip() or apellido_actual
        
    print(f"Rol actual: {'Vecino' if rol_id_actual == 1 else 'De Gestión' if rol_id_actual == 2 else 'Desconocido'}")
    print("Nuevo Rol:")
    print("1. Vecino")
    print("2. De Gestión")
    nuevo_rol_opt = input("Seleccione nuevo rol (deje vacío para no cambiar): ").strip()
    
    if nuevo_rol_opt == "1":
        nuevo_rol_id = 1
    elif nuevo_rol_opt == "2":
        nuevo_rol_id = 2
    else:
        nuevo_rol_id = rol_id_actual
        
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET nombre = ?, apellido = ?, rol_id = ? 
            WHERE id = ?
        """, (nuevo_nombre, nuevo_apellido, nuevo_rol_id, u_id))
        conexion.commit()
        print(f"[+] Usuario ID {u_id} modificado exitosamente.")
    except Exception as e:
        print(f"[-] Error al modificar usuario: {e}")

def menu_gestion_usuarios(conexion):
    while True:
        print("\n=== Gestión de Usuarios ===")
        print("1. Alta de Usuario")
        print("2. Baja de Usuario")
        print("3. Modificación de Usuario")
        print("4. Listar Usuarios")
        print("5. Volver al Menú Principal")
        print("-" * 27)
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "1":
            alta_usuario(conexion)
        elif opcion == "2":
            baja_usuario(conexion)
        elif opcion == "3":
            modificar_usuario(conexion)
        elif opcion == "4":
            listar_usuarios(conexion)
        elif opcion == "5":
            break
        else:
            print("[-] Opción inválida.")

def ingresar_reclamo_vecino(conexion, usuario_id):
    print("\n--- Ingresar Reclamo (Vecino) ---")
    comentario = input("Ingrese su reclamo o reporte vecinal: ").strip()
    if not comentario:
        print("[-] El comentario no puede estar vacío.")
        return
        
    resultado = analizar_comentario(comentario)
    respuesta = generar_respuesta(resultado["categoria"], resultado["urgencia_nlp"])
    
    print("\n[Análisis del Sistema]")
    print(f"- Categoría detectada: {resultado['categoria']}")
    print(f"- Subcategoría detectada: {resultado['subcategoria']}")
    print(f"- Prioridad asignada: {resultado['prioridad']}")
    print(f"- Urgencia NLP: {'Sí' if resultado['urgencia_nlp'] else 'No'}")
    print(f"- Score de Sentimiento: {resultado['score_sentimiento']}")
    
    print("\n[Respuesta para el Vecino]")
    print(respuesta)
    
    reclamo_id = guardar_reclamo_db(comentario, resultado, usuario_id=usuario_id, conexion=conexion)
    if reclamo_id:
        print(f"\n[+] El reclamo ha sido almacenado con éxito. ID del Reclamo: {reclamo_id}")
    else:
        print("\n[-] Hubo un problema al almacenar el reclamo.")

def seguimiento_reclamos_vecino(conexion, usuario_id):
    print("\n--- Seguimiento de mis Reclamos ---")
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT s.id, s.fecha_creacion, c.nombre, e.nombre, s.prioridad, s.comentario
        FROM solicitudes s
        LEFT JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN estados_solicitud e ON s.estado_id = e.id
        WHERE s.usuario_id = ?
        ORDER BY s.fecha_creacion DESC
    """, (usuario_id,))
    reclamos = cursor.fetchall()
    
    if not reclamos:
        print("[i] Usted no tiene reclamos registrados.")
        return
        
    print("\n" + "-"*110)
    print(f"{'ID':<5} | {'Fecha':<20} | {'Categoría':<25} | {'Estado':<12} | {'Prioridad':<10} | {'Comentario (resumen)':<30}")
    print("-"*110)
    for r_id, fecha, cat, estado, prio, com in reclamos:
        fecha_str = fecha[:19] if fecha else "N/A"
        cat_str = cat[:23] if cat else "Otros"
        est_str = estado or "PENDIENTE"
        prio_str = prio or "BAJA"
        com_resumen = com[:27] + "..." if len(com) > 27 else com
        print(f"{r_id:<5} | {fecha_str:<20} | {cat_str:<25} | {est_str:<12} | {prio_str:<10} | {com_resumen:<30}")
    print("-"*110)

def menu_vecino(conexion, usuario_id, nombre_usuario, permisos):
    while True:
        print(f"\n=== Menú Vecino: {nombre_usuario} ===")
        print("1. Ingresar Reclamo")
        print("2. Seguimiento de Reclamos")
        print("3. Cerrar Sesión")
        print("-" * (19 + len(nombre_usuario)))
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            if "CREAR_RECLAMO" in permisos:
                ingresar_reclamo_vecino(conexion, usuario_id)
            else:
                print("[-] No tiene permiso para ingresar reclamos.")
        elif opcion == "2":
            if "VER_RECLAMOS_PROPIOS" in permisos:
                seguimiento_reclamos_vecino(conexion, usuario_id)
            else:
                print("[-] No tiene permiso para ver el seguimiento de sus reclamos.")
        elif opcion == "3":
            print("[i] Sesión cerrada.")
            break
        else:
            print("[-] Opción inválida.")

def nuevo_reclamo_gestion(conexion):
    print("\n--- Nuevo Reclamo (De Gestión) ---")
    cursor = conexion.cursor()
    
    asociar = input("¿Desea asociar este reclamo a un vecino específico? (s/n): ").strip().lower()
    vecino_id = None
    if asociar == "s":
        cursor.execute("SELECT u.id, u.nombre || ' ' || u.apellido AS nombre_completo FROM usuarios u WHERE u.rol_id = 1")
        vecinos = cursor.fetchall()
        if not vecinos:
            print("[i] No hay vecinos registrados en el sistema. Se registrará sin asociar a un vecino.")
        else:
            print("\nVecinos registrados:")
            for v_id, v_nom in vecinos:
                print(f"ID: {v_id} | Nombre: {v_nom}")
            v_id_str = input("Seleccione el ID del vecino: ").strip()
            if v_id_str:
                try:
                    selected_id = int(v_id_str)
                    if any(v[0] == selected_id for v in vecinos):
                        vecino_id = selected_id
                    else:
                        print("[-] ID de vecino no válido. Se registrará sin asociar.")
                except ValueError:
                    print("[-] ID inválido. Se registrará sin asociar.")
                    
    comentario = input("Ingrese el reclamo o reporte vecinal: ").strip()
    if not comentario:
        print("[-] El comentario no puede estar vacío.")
        return
        
    resultado = analizar_comentario(comentario)
    
    reclamo_id = guardar_reclamo_db(comentario, resultado, usuario_id=vecino_id, conexion=conexion)
    if reclamo_id:
        print(f"\n[+] El reclamo ha sido almacenado. ID asignado: {reclamo_id}")
    else:
        print("\n[-] Hubo un problema al almacenar el reclamo.")

def ver_historial_gestion(conexion):
    print("\n--- Historial General de Reclamos ---")
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT s.id, s.fecha_creacion, u.nombre || ' ' || u.apellido AS nombre_completo, 
               c.nombre, e.nombre, s.prioridad, s.comentario
        FROM solicitudes s
        LEFT JOIN usuarios u ON s.usuario_id = u.id
        LEFT JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN estados_solicitud e ON s.estado_id = e.id
        ORDER BY s.fecha_creacion DESC
    """)
    reclamos = cursor.fetchall()
    
    if not reclamos:
        print("[i] No hay reclamos registrados en el sistema.")
        return
        
    print("\n" + "-"*120)
    print(f"{'ID':<5} | {'Fecha':<20} | {'Vecino (Creador)':<20} | {'Categoría':<25} | {'Estado':<12} | {'Prioridad':<10} | {'Comentario':<15}")
    print("-"*120)
    for r_id, fecha, vecino, cat, estado, prio, com in reclamos:
        fecha_str = fecha[:19] if fecha else "N/A"
        vecino_str = vecino[:18] if vecino else "Sin asignar"
        cat_str = cat[:23] if cat else "Otros"
        est_str = estado or "PENDIENTE"
        prio_str = prio or "BAJA"
        com_resumen = com[:12] + "..." if len(com) > 12 else com
        print(f"{r_id:<5} | {fecha_str:<20} | {vecino_str:<20} | {cat_str:<25} | {est_str:<12} | {prio_str:<10} | {com_resumen:<15}")
    print("-"*120)

def modificar_reclamo_gestion(conexion, usuario_id=None):
    print("\n--- Modificar Reclamo ---")
    cursor = conexion.cursor()
    
    r_id_str = input("Ingrese el ID del reclamo a modificar (o Enter para cancelar): ").strip()
    if not r_id_str:
        return
        
    try:
        r_id = int(r_id_str)
    except ValueError:
        print("[-] ID inválido.")
        return
        
    cursor.execute("""
        SELECT s.id, s.comentario, c.nombre, e.nombre, s.prioridad
        FROM solicitudes s
        LEFT JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN estados_solicitud e ON s.estado_id = e.id
        WHERE s.id = ?
    """, (r_id,))
    reclamo = cursor.fetchone()
    if not reclamo:
        print("[-] No se encontró ningún reclamo con ese ID.")
        return
        
    r_id, comentario, cat_nombre, est_nombre, prioridad = reclamo
    print(f"\nReclamo #{r_id}:")
    print(f"Comentario: {comentario}")
    print(f"Categoría: {cat_nombre}")
    print(f"Estado: {est_nombre}")
    print(f"Prioridad: {prioridad}")
    print("-" * 40)
    
    print("¿Qué desea modificar?")
    print("1. Estado")
    print("2. Prioridad")
    print("3. Categoría")
    print("4. Comentario")
    print("5. Cancelar")
    opt = input("Seleccione una opción: ").strip()
    
    if opt == "1":
        cursor.execute("SELECT id, nombre FROM estados_solicitud")
        estados = cursor.fetchall()
        print("\nEstados disponibles:")
        for e_id, e_nom in estados:
            print(f"{e_id}. {e_nom}")
        e_opt = input("Seleccione el ID del nuevo estado: ").strip()
        try:
            nuevo_est_id = int(e_opt)
            if any(e[0] == nuevo_est_id for e in estados):
                # Obtener estado anterior
                cursor.execute("SELECT estado_id FROM solicitudes WHERE id = ?", (r_id,))
                res_est_ant = cursor.fetchone()
                estado_anterior_id = res_est_ant[0] if res_est_ant else None
                
                # Actualizar solicitud
                cursor.execute("UPDATE solicitudes SET estado_id = ? WHERE id = ?", (nuevo_est_id, r_id))
                
                # Actualizar fecha_resolucion si corresponde
                estados_resueltos = trazabilidad.obtener_estados_resueltos(conexion)
                if nuevo_est_id in estados_resueltos:
                    cursor.execute("UPDATE solicitudes SET fecha_resolucion = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), r_id))
                else:
                    cursor.execute("UPDATE solicitudes SET fecha_resolucion = NULL WHERE id = ?", (r_id,))
                    
                # Registrar cambio de estado en el historial
                trazabilidad.registrar_cambio_estado(conexion, r_id, estado_anterior_id, nuevo_est_id, usuario_id)
                
                conexion.commit()
                print("[+] Estado modificado correctamente y registrado en auditoría.")
            else:
                print("[-] ID de estado inválido.")
        except ValueError:
            print("[-] Entrada inválida.")
            
    elif opt == "2":
        print("\nPrioridades disponibles: BAJA, MEDIA, ALTA")
        nueva_prio = input("Ingrese la nueva prioridad: ").strip().upper()
        if nueva_prio in ["BAJA", "MEDIA", "ALTA"]:
            cursor.execute("UPDATE solicitudes SET prioridad = ? WHERE id = ?", (nueva_prio, r_id))
            conexion.commit()
            print("[+] Prioridad modificada correctamente.")
        else:
            print("[-] Prioridad inválida.")
            
    elif opt == "3":
        cursor.execute("SELECT id, nombre FROM categorias")
        cats = cursor.fetchall()
        print("\nCategorías disponibles:")
        for c_id, c_nom in cats:
            print(f"{c_id}. {c_nom}")
        c_opt = input("Seleccione el ID de la nueva categoría: ").strip()
        try:
            nueva_cat_id = int(c_opt)
            if any(c[0] == nueva_cat_id for c in cats):
                cursor.execute("UPDATE solicitudes SET categoria_id = ? WHERE id = ?", (nueva_cat_id, r_id))
                conexion.commit()
                print("[+] Categoría modificada correctamente.")
            else:
                print("[-] ID de categoría inválido.")
        except ValueError:
            print("[-] Entrada inválida.")
            
    elif opt == "4":
        nuevo_com = input("Ingrese el nuevo comentario: ").strip()
        if nuevo_com:
            resultado = analizar_comentario(nuevo_com)
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (resultado["categoria"],))
            res_cat = cursor.fetchone()
            cat_id = res_cat[0] if res_cat else 1
            
            cursor.execute("SELECT id FROM subcategorias WHERE nombre = ?", (resultado["subcategoria"],))
            sub_res = cursor.fetchone()
            sub_id = sub_res[0] if sub_res else None
            
            cursor.execute("""
                UPDATE solicitudes 
                SET comentario = ?, categoria_id = ?, subcategoria_id = ?, 
                    prioridad = ?, score_sentimiento = ?, urgencia_nlp = ?
                WHERE id = ?
            """, (
                nuevo_com, cat_id, sub_id, resultado["prioridad"], 
                resultado["score_sentimiento"], resultado["urgencia_nlp"], r_id
            ))
            conexion.commit()
            print("[+] Comentario y análisis NLP actualizados correctamente.")
        else:
            print("[-] El comentario no puede estar vacío.")
    elif opt == "5":
        print("[i] Modificación cancelada.")

def eliminar_reclamo_gestion(conexion):
    print("\n--- Eliminar Reclamo ---")
    cursor = conexion.cursor()
    
    r_id_str = input("Ingrese el ID del reclamo a eliminar (o Enter para cancelar): ").strip()
    if not r_id_str:
        return
        
    try:
        r_id = int(r_id_str)
    except ValueError:
        print("[-] ID inválido.")
        return
        
    cursor.execute("SELECT comentario FROM solicitudes WHERE id = ?", (r_id,))
    res = cursor.fetchone()
    if not res:
        print("[-] No se encontró ningún reclamo con ese ID.")
        return
        
    comentario = res[0]
    print(f"Reclamo #{r_id}: {comentario}")
    confirmar = input(f"¿Está seguro de eliminar el reclamo #{r_id}? (s/n): ").strip().lower()
    if confirmar == "s":
        try:
            cursor.execute("DELETE FROM solicitudes WHERE id = ?", (r_id,))
            conexion.commit()
            print(f"[+] Reclamo #{r_id} eliminado exitosamente.")
        except Exception as e:
            print(f"[-] Error al eliminar el reclamo: {e}")

def menu_gestion(conexion, usuario_id, nombre_usuario, permisos):
    while True:
        print(f"\n=== Menú de Gestión: {nombre_usuario} ===")
        print("1. Nuevo Reclamo")
        print("2. Ver Historial")
        print("3. Modificar Reclamo")
        print("4. Eliminar Reclamo")
        
        # Módulo de trazabilidad y auditoría
        mostrar_trazabilidad = "VER_HISTORIAL_RECLAMOS" in permisos
        if mostrar_trazabilidad:
            print("5. Auditoría y Trazabilidad Administrativa")
            
        mostrar_admin_roles = "GESTIONAR_ROLES_PERPOS" in permisos or "GESTIONAR_ROLES_PERMISOS" in permisos
        if mostrar_admin_roles:
            print("6. Gestión de Roles y Permisos")
            print("7. Salir")
        else:
            if mostrar_trazabilidad:
                print("6. Salir")
            else:
                print("5. Salir")
            
        print("-" * (21 + len(nombre_usuario)))
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            if "CREAR_RECLAMO" in permisos:
                nuevo_reclamo_gestion(conexion)
            else:
                print("[-] No tiene permiso para crear reclamos.")
        elif opcion == "2":
            if "VER_HISTORIAL_RECLAMOS" in permisos:
                ver_historial_gestion(conexion)
            else:
                print("[-] No tiene permiso para ver el historial.")
        elif opcion == "3":
            if "MODIFICAR_RECLAMO" in permisos:
                modificar_reclamo_gestion(conexion, usuario_id)
            else:
                print("[-] No tiene permiso para modificar reclamos.")
        elif opcion == "4":
            if "ELIMINAR_RECLAMO" in permisos:
                eliminar_reclamo_gestion(conexion)
            else:
                print("[-] No tiene permiso para eliminar reclamos.")
        elif opcion == "5" and mostrar_trazabilidad:
            trazabilidad.mostrar_menu_auditoria(conexion, usuario_id)
        elif opcion == "6" and mostrar_trazabilidad and mostrar_admin_roles:
            menu_roles_permisos(conexion)
        elif (opcion == "6" and mostrar_trazabilidad and not mostrar_admin_roles) or \
             (opcion == "7" and mostrar_trazabilidad and mostrar_admin_roles) or \
             (opcion == "5" and not mostrar_trazabilidad and not mostrar_admin_roles):
            print("[i] Sesión cerrada.")
            break
        else:
            print("[-] Opción inválida.")

def crear_rol(conexion):
    print("\n--- Crear Nuevo Rol ---")
    nombre_rol = input("Ingrese el nombre del nuevo rol: ").strip()
    if not nombre_rol:
        print("[-] El nombre del rol no puede estar vacío.")
        return
        
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM roles WHERE LOWER(nombre) = LOWER(?)", (nombre_rol,))
    if cursor.fetchone():
        print(f"[!] El rol '{nombre_rol}' ya existe.")
        return
    try:
        cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (nombre_rol,))
        conexion.commit()
        print(f"[+] Rol '{nombre_rol}' creado exitosamente. ID asignado: {cursor.lastrowid}")
    except Exception as e:
        print(f"[-] Error al crear el rol: {e}")

def listar_roles_con_permisos(conexion):
    print("\n--- Roles y sus Permisos ---")
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id, nombre FROM roles")
    roles = cursor.fetchall()
    
    if not roles:
        print("[i] No hay roles registrados.")
        return
        
    for rol_id, rol_nombre in roles:
        print(f"\nRol: {rol_nombre} (ID: {rol_id})")
        cursor.execute("""
            SELECT p.nombre, p.descripcion 
            FROM permisos p
            JOIN roles_permisos rp ON p.id = rp.permiso_id
            WHERE rp.rol_id = ?
        """, (rol_id,))
        permisos = cursor.fetchall()
        
        if not permisos:
            print("  (Sin permisos asignados)")
        else:
            for p_nombre, p_desc in permisos:
                print(f"  - {p_nombre}: {p_desc}")
    print("-" * 35)

def asignar_permiso_a_rol(conexion):
    print("\n--- Asignar Permiso a Rol ---")
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id, nombre FROM roles")
    roles = cursor.fetchall()
    print("Roles disponibles:")
    for r_id, r_nom in roles:
        print(f"ID: {r_id} | Rol: {r_nom}")
        
    r_id_str = input("Ingrese el ID del rol a modificar: ").strip()
    try:
        rol_id = int(r_id_str)
        if not any(r[0] == rol_id for r in roles):
            print("[-] ID de rol inválido.")
            return
    except ValueError:
        print("[-] ID inválido.")
        return
        
    cursor.execute("SELECT id, nombre, descripcion FROM permisos")
    permisos = cursor.fetchall()
    print("\nPermisos del sistema:")
    for p_id, p_nom, p_desc in permisos:
        print(f"ID: {p_id} | Permiso: {p_nom} ({p_desc})")
        
    p_id_str = input("Ingrese el ID del permiso a asignar: ").strip()
    try:
        permiso_id = int(p_id_str)
        if not any(p[0] == permiso_id for p in permisos):
            print("[-] ID de permiso inválido.")
            return
    except ValueError:
        print("[-] ID inválido.")
        return
        
    try:
        cursor.execute("INSERT INTO roles_permisos (rol_id, permiso_id) VALUES (?, ?)", (rol_id, permiso_id))
        conexion.commit()
        print("[+] Permiso asignado correctamente.")
    except sqlite3.IntegrityError:
        print("[-] El rol ya posee este permiso.")
    except Exception as e:
        print(f"[-] Error al asignar permiso: {e}")

def revocar_permiso_de_rol(conexion):
    print("\n--- Revocar Permiso de Rol ---")
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id, nombre FROM roles")
    roles = cursor.fetchall()
    print("Roles disponibles:")
    for r_id, r_nom in roles:
        print(f"ID: {r_id} | Rol: {r_nom}")
        
    r_id_str = input("Ingrese el ID del rol: ").strip()
    try:
        rol_id = int(r_id_str)
        if not any(r[0] == rol_id for r in roles):
            print("[-] ID de rol inválido.")
            return
    except ValueError:
        print("[-] ID inválido.")
        return
        
    cursor.execute("""
        SELECT p.id, p.nombre 
        FROM permisos p
        JOIN roles_permisos rp ON p.id = rp.permiso_id
        WHERE rp.rol_id = ?
    """, (rol_id,))
    permisos_asignados = cursor.fetchall()
    
    if not permisos_asignados:
        print("[i] El rol seleccionado no tiene permisos asignados.")
        return
        
    print("\nPermisos asignados al rol:")
    for p_id, p_nom in permisos_asignados:
        print(f"ID: {p_id} | Permiso: {p_nom}")
        
    p_id_str = input("Ingrese el ID del permiso a revocar: ").strip()
    try:
        permiso_id = int(p_id_str)
        if not any(p[0] == permiso_id for p in permisos_asignados):
            print("[-] El rol no posee ese permiso asignado o el ID es inválido.")
            return
    except ValueError:
        print("[-] ID inválido.")
        return
        
    try:
        cursor.execute("DELETE FROM roles_permisos WHERE rol_id = ? AND permiso_id = ?", (rol_id, permiso_id))
        conexion.commit()
        print("[+] Permiso revocado correctamente.")
    except Exception as e:
        print(f"[-] Error al revocar permiso: {e}")

def menu_roles_permisos(conexion):
    while True:
        print("\n=== Gestión de Roles y Permisos ===")
        print("1. Crear Nuevo Rol")
        print("2. Listar Roles y sus Permisos")
        print("3. Asignar Permiso a Rol")
        print("4. Revocar Permiso de Rol")
        print("5. Volver")
        print("-" * 34)
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            crear_rol(conexion)
        elif opcion == "2":
            listar_roles_con_permisos(conexion)
        elif opcion == "3":
            asignar_permiso_a_rol(conexion)
        elif opcion == "4":
            revocar_permiso_de_rol(conexion)
        elif opcion == "5":
            break
        else:
            print("[-] Opción inválida.")

def login_usuario(conexion):
    print("\n--- Iniciar Sesión ---")
    
    dni_ingresado = input("Ingrese su DNI: ").strip()
    clave_ingresada = input("Ingrese su Clave: ").strip()
    
    if not dni_ingresado or not clave_ingresada:
        print("[-] Debe ingresar DNI y Clave.")
        return
 
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre, u.apellido, u.rol_id, r.nombre, u.clave
        FROM usuarios u
        LEFT JOIN roles r ON u.rol_id = r.id
        WHERE u.dni = ?
    """, (dni_ingresado,))
    
    usuario = cursor.fetchone()
    if not usuario:
        print("[-] Credenciales incorrectas o usuario no registrado.")
        return
        
    u_id, nombre, apellido, rol_id, rol_nombre, clave_db = usuario
    
    # Validar contraseña con soporte de migración al vuelo
    if verify_password(clave_ingresada, clave_db):
        pass
    elif clave_ingresada == clave_db:
        # Migración al vuelo
        print("[i] Migrando credenciales antiguas a un formato seguro...")
        clave_hasheada = hash_password(clave_ingresada)
        cursor.execute("UPDATE usuarios SET clave = ? WHERE id = ?", (clave_hasheada, u_id))
        conexion.commit()
    else:
        print("[-] Credenciales incorrectas o usuario no registrado.")
        return
        
    nombre_completo = f"{nombre} {apellido}"
    print(f"\n[+] Acceso concedido como: {nombre_completo} ({rol_nombre})")
    
    # Cargar permisos del rol del usuario
    cursor.execute("""
        SELECT p.nombre 
        FROM permisos p
        JOIN roles_permisos rp ON p.id = rp.permiso_id
        WHERE rp.rol_id = ?
    """, (rol_id,))
    permisos = {row[0] for row in cursor.fetchall()}
    
    if rol_id == 1:
        menu_vecino(conexion, u_id, nombre_completo, permisos)
    elif rol_id == 2:
        menu_gestion(conexion, u_id, nombre_completo, permisos)
    else:
        if "VER_HISTORIAL_RECLAMOS" in permisos:
            menu_gestion(conexion, u_id, nombre_completo, permisos)
        else:
            menu_vecino(conexion, u_id, nombre_completo, permisos)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    datos_dir = os.path.join(base_dir, "datos")
    os.makedirs(datos_dir, exist_ok=True)
    db_path = os.path.join(datos_dir, "ruralconecta.db")
    
    conexion = sqlite3.connect(db_path)
    conexion.execute("PRAGMA foreign_keys = ON;")
    
    inicializar_db_completo(conexion)
    
    while True:
        print("\n" + "="*50)
        print("--- Bienvenido a RuralConecta - Gestión Rural ---")
        print("="*50)
        print("1. Iniciar Sesión (Acceso Diferencial)")
        print("2. Gestión de Usuarios (CRUD)")
        print("3. Salir")
        print("-" * 50)
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            login_usuario(conexion)
        elif opcion == "2":
            menu_gestion_usuarios(conexion)
        elif opcion == "3":
            print("\n¡Gracias por usar RuralConecta! Hasta luego.")
            break
        else:
            print("[-] Opción inválida.")
            
    conexion.close()

if __name__ == "__main__":
    main()