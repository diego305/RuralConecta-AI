import sqlite3
import random
from datetime import datetime, timedelta
import os
from main import hash_password, inicializar_db_completo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "datos", "ruralconecta.db")

def generar_dataset_500():
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON;")
    cursor = conexion.cursor()
    
    # 1. Asegurar esquema de tablas completo
    inicializar_db_completo(conexion)
    
    # 2. Limpiar solicitudes, historial y encuestas previas para la regeneración limpia
    cursor.execute("DELETE FROM encuestas_satisfaccion")
    cursor.execute("DELETE FROM historial_estados")
    cursor.execute("DELETE FROM solicitudes")
    conexion.commit()

    # 3. Generar pool variado de usuarios vecinos (~50 usuarios)
    nombres = [
        "Carlos", "Lucía", "Mateo", "Sofía", "José", "María", "Gonzalo", "Valeria",
        "Joaquín", "Camila", "Esteban", "Martina", "Lucas", "Agustina", "Santiago",
        "Valentina", "Facundo", "Rocío", "Nicolás", "Lourdes", "Tomás", "Micaela",
        "Javier", "Delfina", "Ignacio", "Paula", "Felipe", "Jimena", "Emiliano",
        "Romina", "Mariano", "Silvina", "Federico", "Carla", "Manuel", "Guadalupe",
        "Rodrigo", "Belén", "Marcos", "Gabriela", "Patricio", "Sabrina", "Gabriel",
        "Noelia", "Leandro", "Verónica", "Sebastián", "Carolina", "Maximiliano", "Melisa"
    ]
    
    apellidos = [
        "Gómez", "Fernández", "Rodríguez", "Juárez", "Martínez", "López", "Pérez",
        "González", "Sánchez", "Romero", "Díaz", "Álvarez", "Torres", "Ruiz",
        "Ramírez", "Flores", "Benítez", "Medina", "Herrera", "Castro", "Ríos",
        "Mendoza", "Morales", "Ortiz", "Gutiérrez", "Vargas", "Rojas", "Navarro",
        "Peralta", "Silva"
    ]

    pass_hashed = hash_password("vecino123")
    
    # Usuarios fijos del sistema
    usuarios_fijos = [
        ("Diego", "Andrada", "27231845", "20272318450", pass_hashed, 1),
        ("Ana", "García", "34567890", "27345678903", pass_hashed, 1),
        ("Florencia", "Sánchez", "23963457", "27239634570", pass_hashed, 1),
        ("Gestor", "Municipal", "11223344", "20112233440", hash_password("gestor123"), 2)
    ]
    
    for nom, ape, dni, cuil, pwd, r_id in usuarios_fijos:
        cursor.execute("SELECT id FROM usuarios WHERE dni = ?", (dni,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id) VALUES (?, ?, ?, ?, ?, ?)", (nom, ape, dni, cuil, pwd, r_id))
    conexion.commit()

    # Generar 50 vecinos aleatorios adicionales
    random.seed(42)
    dni_base = 28000000
    
    for i in range(50):
        nom = nombres[i % len(nombres)]
        ape = apellidos[i % len(apellidos)]
        dni = str(dni_base + i * 137)
        cuil = f"20{dni}5"
        
        cursor.execute("SELECT id FROM usuarios WHERE dni = ?", (dni,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id) VALUES (?, ?, ?, ?, ?, ?)",
                           (nom, ape, dni, cuil, pass_hashed, 1))
            
    conexion.commit()

    # Lista completa de vecinos (rol_id = 1)
    cursor.execute("SELECT id FROM usuarios WHERE rol_id = 1")
    todos_vecino_ids = [r[0] for r in cursor.fetchall()]
    
    # Gestor
    cursor.execute("SELECT id FROM usuarios WHERE rol_id = 2 LIMIT 1")
    gestor_row = cursor.fetchone()
    gestor_id = gestor_row[0] if gestor_row else 4

    # Mapeo de subcategorías por categoría
    cursor.execute("SELECT id, categoria_id FROM subcategorias")
    subcat_rows = cursor.fetchall()
    cat_to_subcats = {}
    for sub_id, cat_id in subcat_rows:
        cat_to_subcats.setdefault(cat_id, []).append(sub_id)
        
    cursor.execute("SELECT id FROM barrios")
    barrio_ids = [r[0] for r in cursor.fetchall()]
    if not barrio_ids:
        barrio_ids = [1]

    # Plantillas de reclamos rurales realistas
    plantillas_reclamos = {
        1: [
            "Camino de tierra con grietas y baches profundos tras la lluvia en el acceso principal.",
            "Tramo intransitable por acumulación de agua y barro en la huella rural.",
            "Zanja de desagüe obstruida provocando desborde hacia los terrenos colindantes.",
            "Badén de hormigón fracturado que dificulta el paso de camionetas y maquinaria agrícola.",
            "Banquinas con maleza alta que tapan la visibilidad en las curvas del camino rural."
        ],
        2: [
            "Pozo comunitario fuera de servicio por falla en la bomba sumergible eléctrica.",
            "Cañería principal con fisura perdiendo caudal de agua potable para el paraje.",
            "Turno de agua de riego interrumpido por sedimentación en el canal secundario.",
            "Tanque elevado con compuerta trabada afectando la presión del suministro.",
            "Turbidez elevada en el agua de red tras la crecida del río del paraje."
        ],
        3: [
            "Poste de madera inclinado en peligro de caída sobre el alambre perimetral.",
            "Corte de suministro eléctrico general en las viviendas del paraje tras la tormenta.",
            "Luminaria pública parpadeando frente al centro comunitario rural.",
            "Cable de alta tensión rozando ramas de árboles con riesgo de cortocircuito.",
            "Baja tensión recurrente al atardecer afectando el funcionamiento de heladeras."
        ],
        4: [
            "Acumulación de envases de agroquímicos vacíos en el punto limpio sin retirar.",
            "Vuelco clandestino de chatarra y residuos en la banquina del camino secundario.",
            "Contenedores comunitarios desbordados por residuos domisanitarios en el paraje.",
            "Microbasural generado cerca de la escuela rural requiriendo desmalezado y saneamiento."
        ],
        5: [
            "Tropa de bovinos y equinos sueltos pastando a la vera de la ruta rural.",
            "Presencia de enjambre de langostas afectando los brotes de huertas comunitarias.",
            "Jauría de perros cimarrones atacando corrales de ovinos y caprinos.",
            "Solicitud de operativo de vacunación antirrábica y castración en el paraje."
        ],
        6: [
            "Quema descontrolada de pastizales cerca de la reserva de monte nativo.",
            "Rama de gran porte caída bloqueando la entrada a dos campos familiares.",
            "Vertido sospechoso de efluentes en el cauce del arroyo del paraje."
        ],
        7: [
            "Techo del salón comunitario rural con filtraciones requiriendo reparación urgente.",
            "Cartelería refractaria de cruce de caminos vandalizada o caída.",
            "Puesto sanitario del paraje requiere mantenimiento de pintura y cerraduras."
        ],
        8: [
            "Desavenencia entre vecinos por el horario de apertura de compuertas de riego.",
            "Diferencias por invasión de animales en predios no alambrados del vecino colindante.",
            "Disputa por deslinde y reparación de alambrado olímpico entre fincas."
        ]
    }

    prioridades = ["ALTA", "MEDIA", "BAJA"]
    
    # Distribución de 500 solicitudes:
    # 310 RESUELTO (62%)
    # 100 EN PROCESO (20%)
    # 50 EN REVISION (10%)
    # 40 PENDIENTE (8%)
    estados_dist = [4]*310 + [3]*100 + [2]*50 + [1]*40
    random.shuffle(estados_dist)

    ahora = datetime.now()

    for i, est_id in enumerate(estados_dist):
        cat_id = random.randint(1, 8)
        subcat_list = cat_to_subcats.get(cat_id, [1])
        subcat_id = random.choice(subcat_list)
        
        texto_base = random.choice(plantillas_reclamos.get(cat_id, plantillas_reclamos[1]))
        comentario = f"{texto_base} (Gestión Rural #{i+1001})"
        
        prio = random.choice(prioridades)
        if cat_id in [1, 2, 3] and random.random() < 0.6:
            prio = "ALTA"
            
        days_ago = random.randint(1, 90)
        hours_ago = random.randint(0, 23)
        fecha_crea = ahora - timedelta(days=days_ago, hours=hours_ago)
        
        if est_id == 4:
            res_days = random.randint(1, 4)
            fecha_reso = fecha_crea + timedelta(days=res_days, hours=random.randint(1, 12))
        else:
            fecha_reso = None
            
        ubi = f"Lat: -29.{random.randint(1000, 9999)}, Lng: -66.{random.randint(1000, 9999)}"
        barrio_id = random.choice(barrio_ids)
        vecino_id = random.choice(todos_vecino_ids)
        
        score_sent = round(random.uniform(-0.9, 0.4), 2)
        urg_nlp = True if prio == "ALTA" else (random.random() < 0.3)
        
        cursor.execute("""
            INSERT INTO solicitudes (
                comentario, categoria_id, subcategoria_id, prioridad, estado_id, 
                fecha_creacion, fecha_resolucion, ubicacion, barrio_id, 
                asignado_a, score_sentimiento, urgencia_nlp, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comentario, cat_id, subcat_id, prio, est_id,
            fecha_crea.strftime("%Y-%m-%d %H:%M:%S"),
            fecha_reso.strftime("%Y-%m-%d %H:%M:%S") if fecha_reso else None,
            ubi, barrio_id, gestor_id, score_sent, urg_nlp, vecino_id
        ))
        sol_id = cursor.lastrowid
        
        # Historial de trazabilidad
        cursor.execute("""
            INSERT INTO historial_estados (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio)
            VALUES (?, NULL, 1, ?, ?)
        """, (sol_id, vecino_id, fecha_crea.strftime("%Y-%m-%d %H:%M:%S")))
        
        t_rev = fecha_crea + timedelta(hours=random.randint(2, 12))
        if est_id in [2, 3, 4]:
            cursor.execute("""
                INSERT INTO historial_estados (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio)
                VALUES (?, 1, 2, ?, ?)
            """, (sol_id, gestor_id, t_rev.strftime("%Y-%m-%d %H:%M:%S")))
            
        t_proc = t_rev + timedelta(hours=random.randint(4, 24))
        if est_id in [3, 4]:
            cursor.execute("""
                INSERT INTO historial_estados (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio)
                VALUES (?, 2, 3, ?, ?)
            """, (sol_id, gestor_id, t_proc.strftime("%Y-%m-%d %H:%M:%S")))
            
        if est_id == 4:
            cursor.execute("""
                INSERT INTO historial_estados (solicitud_id, estado_anterior_id, estado_nuevo_id, usuario_id, fecha_cambio)
                VALUES (?, 3, 4, ?, ?)
            """, (sol_id, gestor_id, fecha_reso.strftime("%Y-%m-%d %H:%M:%S")))
            
            if random.random() < 0.45:
                punt = random.choices([5, 4, 3, 2, 1], weights=[55, 25, 12, 5, 3])[0]
                coms_encuesta = [
                    "Excelente atención y rapidez del equipo municipal.",
                    "Se reparó el camino adecuadamente, muchas gracias.",
                    "Solucionaron el problema de la bomba de agua rápido.",
                    "Muy buen servicio y atención vecinal.",
                    "La cuadrilla trabajó bien en el paraje."
                ]
                cursor.execute("""
                    INSERT INTO encuestas_satisfaccion (solicitud_id, puntuacion, comentario_vecino, fecha_encuesta)
                    VALUES (?, ?, ?, ?)
                """, (sol_id, punt, random.choice(coms_encuesta), (fecha_reso + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")))

    conexion.commit()
    conexion.close()
    print("Dataset de 500 solicitudes generado exitosamente.")

if __name__ == "__main__":
    generar_dataset_500()
