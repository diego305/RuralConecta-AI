# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import sqlite3
import os
import html
from datetime import datetime

# Importaciones locales del proyecto base
from analizador import analizar_comentario
from respuestas import generar_respuesta
from ia import consultar_ia
from analisis import cargar_datos_completos, generar_estadisticas, DB_PATH
import trazabilidad
import base64

# Cargar logo corporativo oficial en formato base64
def obtener_base64_logo():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logo_muni.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

logo_base64 = obtener_base64_logo()
logo_data_url = f"data:image/png;base64,{logo_base64}" if logo_base64 else ""

# Cargar imagen de la frase/lema corporativo (Rioja Limpia, Rioja Linda)
def obtener_base64_rioja_limpia_linda():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "rioja_limpia_linda.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

limpia_linda_base64 = obtener_base64_rioja_limpia_linda()
limpia_linda_url = f"data:image/png;base64,{limpia_linda_base64}" if limpia_linda_base64 else ""

# Configuración de la página web oficial
st.set_page_config(
    page_title="RuralConecta AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Premium y Personalización ---
st.markdown("""
<style>
    /* Estilos generales */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
    
    .reportview-container, .stApp {
        background-color: #FAFAFA;
    }
    .main-title {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(90deg, #2E7D32 0%, #E6A15C 50%, #00838F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        padding-bottom: 0px;
    }
    .subtitle {
        color: #4B5563;
        font-size: 1.1rem;
        margin-top: 0px;
        margin-bottom: 1.8rem;
        font-family: 'Inter', sans-serif;
    }
    /* Tarjetas tipo Glassmorphism Claras */
    .glass-card {
        background: #ffffff;
        border: 1px solid rgba(229, 231, 235, 0.8);
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03), 0 0 0 1px rgba(0, 0, 0, 0.02);
        transition: box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .glass-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
        border-color: rgba(46, 125, 50, 0.2);
    }
    .kpi-number {
        font-family: 'Outfit', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        color: #2E7D32;
        margin: 0px;
    }
    .kpi-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #4B5563;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    /* Estilos de Badges de Categorías */
    .badge {
        display: inline-block;
        padding: 0.4em 0.8em;
        font-size: 0.8em;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 9999px;
        margin-right: 0.5rem;
        color: white;
        font-family: 'Inter', sans-serif;
    }
    .badge-calles { background-color: #D97706; }
    .badge-alumbrado { background-color: #FDDA24; color: #1F2937; }
    .badge-basura { background-color: #10B981; }
    .badge-arbolado { background-color: #15803D; }
    .badge-saneamiento { background-color: #0D9488; }
    .badge-limpieza { background-color: #16A34A; }
    .badge-higiene { background-color: #2563EB; }
    .badge-conflictos { background-color: #4B5563; }
    .badge-otros { background-color: #6B7280; }

    /* Prioridades */
    .badge-alta { background-color: #DC2626; font-weight: bold; }
    .badge-media { background-color: #F59E0B; }
    .badge-baja { background-color: #10B981; }

    /* Estados */
    .badge-pendiente { background-color: #6B7280; }
    .badge-revision { background-color: #D97706; }
    .badge-proceso { background-color: #2563EB; }
    .badge-resuelto { background-color: #76BC21; }
    .badge-rechazado { background-color: #DC2626; }

    /* Estilos del banner superior */
    .muni-header {
        background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(46, 125, 50, 0.3);
        border-bottom: 4px solid #E6A15C;
    }
    .muni-logo-box {
        display: flex;
        flex-direction: column;
        font-family: 'Outfit', sans-serif;
    }
    .muni-logo-top {
        display: flex;
        align-items: baseline;
        line-height: 1;
    }
    .muni-logo-la {
        font-weight: 300;
        font-size: 1.8rem;
        margin-right: 0.2rem;
        text-transform: lowercase;
    }
    .muni-logo-rioja {
        font-weight: 800;
        font-size: 2.2rem;
        letter-spacing: -0.5px;
    }
    .muni-logo-sub {
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 0.1rem;
        opacity: 0.9;
    }
    .muni-header-right {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .muni-tagline {
        font-family: 'Outfit', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #FFFFFF;
        background-color: rgba(0, 0, 0, 0.15);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        text-align: right;
        display: none;
    }
    @media (min-width: 768px) {
        .muni-tagline {
            display: block;
        }
    }
    .muni-socials {
        display: flex;
        align-items: center;
        gap: 1.1rem;
    }
    .muni-social-icon-new {
        color: white !important;
        text-decoration: none;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, opacity 0.2s;
        opacity: 0.92;
    }
    .muni-social-icon-new:hover {
        transform: scale(1.18);
        opacity: 1;
    }
    .muni-social-divider {
        width: 1px;
        height: 22px;
        background-color: rgba(255, 255, 255, 0.7);
        margin: 0 0.3rem;
    }
    
    /* Contenedor de reportes de auditoría en formato de consola premium */
    .muni-report-box {
        background-color: #0F172A; /* Fondo oscuro tipo consola de administración */
        color: #F1F5F9;            /* Texto de alto contraste y legibilidad */
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #2E7D32; /* Borde verde RuralConecta */
        font-family: 'Consolas', 'Courier New', Courier, monospace;
        font-size: 0.88rem;
        line-height: 1.45;
        overflow-x: auto;
        white-space: pre;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        margin-top: 0.8rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Inicialización de Base de Datos y Datos Semilla ---
def inicializar_base_de_datos_con_semilla():
    # Importar desde main.py la inicialización relacional básica
    from main import inicializar_db_completo
    
    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON;")
    inicializar_db_completo(conexion)
    
    # Comprobar si hay solicitudes. Si no hay, inyectar un par de registros para poblar las estadísticas
    cursor = conexion.cursor()
    # Asegurar usuarios semilla sin sobrescribir usuarios modificados o existentes
    from main import hash_password
    pass_vecino = hash_password("vecino123")
    pass_gestor = hash_password("gestor123")
    
    usuarios_semilla = [
        ("Diego", "Andrada", "27231845", "20272318450", pass_vecino, 1),
        ("Ana", "García", "34567890", "27345678903", pass_vecino, 1),
        ("Gestor", "Municipal", "11223344", "20112233440", pass_gestor, 2)
    ]
    for nom, ape, dni, cuil, pwd, r_id in usuarios_semilla:
        cursor.execute("SELECT id FROM usuarios WHERE dni = ?", (dni,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nom, ape, dni, cuil, pwd, r_id))
    conexion.commit()

    cursor.execute("SELECT COUNT(*) FROM solicitudes")
    solicitudes_existentes = cursor.fetchone()[0]

    if solicitudes_existentes == 0:

        # Asegurar barrios semilla
        cursor.execute("SELECT COUNT(*) FROM barrios")
        if cursor.fetchone()[0] <= 1:
            cursor.executemany("""
                INSERT INTO barrios (nombre, zona)
                VALUES (?, ?)
            """, [
                ("Barrio Sur", "Sur"),
                ("Barrio Norte", "Norte"),
                ("Barrio Este", "Este")
            ])
            conexion.commit()

        # Obtener IDs de referencia
        cursor.execute("SELECT id, nombre FROM categorias")
        cats = {nombre: c_id for c_id, nombre in cursor.fetchall()}
        
        cursor.execute("SELECT id, nombre, categoria_id FROM subcategorias")
        subcats = {}
        for sub_id, name, cat_id in cursor.fetchall():
            subcats.setdefault(cat_id, []).append(sub_id)
            
        cursor.execute("SELECT id FROM barrios")
        barrio_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM usuarios WHERE rol_id = 1")
        vecino_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM estados_solicitud")
        estados_ids = {row[0]: idx for idx, row in enumerate(cursor.fetchall())} # mapeo rapido
        
        # Insertar algunas solicitudes de prueba rurales
        solicitudes_semilla = [
            ("El camino de tierra que conecta con el paraje principal tiene zanjas profundas y pozos peligrosos tras la última lluvia.", "Red Vial Rural y Caminos", "ALTA", 0.1, True),
            ("Se rompió la bomba sumergible del pozo de agua comunitario y el paraje entero se encuentra sin suministro de agua.", "Agua Potable Rural y Riego", "ALTA", 0.1, True),
            ("Hay un poste de luz de madera a punto de caer sobre la banquina en el camino de acceso rural con cables sueltos.", "Electrificación y Alumbrado Rural", "ALTA", 0.2, True),
            ("Se acumularon varios envases de agroquímicos y chatarra en el punto de acopio cerca de la escuela rural.", "Residuos y Limpieza Rural", "MEDIA", 0.3, False),
            ("Hay varios equinos y vacunos sueltos pasteando a la vera de la ruta provincial, gran riesgo de accidente.", "Zoonosis y Control de Plagas Rurales", "ALTA", 0.2, True),
            ("Se observa humo de una quema de pastizales descontrolada cerca del monte nativo y el canal secundario.", "Medio Ambiente y Recurso Forestal", "ALTA", 0.1, True),
            ("Falta señalización y cartelería refractaria en el cruce de caminos del paraje para indicar el puesto sanitario.", "Infraestructura Comunitaria Rural", "MEDIA", 0.4, False),
            ("Disputa entre productores colindantes por la distribución de turnos en el canal de riego comunitario.", "Convivencia y Mediación Rural", "BAJA", 0.5, False),
            ("El puente de madera sobre el arroyo presenta maderas rotas y es peligroso para el paso de vehículos.", "Red Vial Rural y Caminos", "ALTA", 0.1, True),
            ("La luz del alumbrado público frente al salón comunitario del paraje parpadea y queda a oscuras.", "Electrificación y Alumbrado Rural", "BAJA", 0.4, False)
        ]
        
        import random
        from datetime import datetime, timedelta
        
        for comentario, cat_nombre, prioridad, score, urgencia in solicitudes_semilla:
            cat_id = cats.get(cat_nombre, 1)
            sub_id = subcats[cat_id][0] if cat_id in subcats else None
            barrio_id = random.choice(barrio_ids)
            vecino_id = random.choice(vecino_ids)
            estado_id = random.choice([1, 2, 3, 4]) # PENDIENTE, EN REVISION, EN PROCESO, RESUELTO
            
            fecha_creacion = datetime.now() - timedelta(days=random.randint(2, 20), hours=random.randint(1, 10))
            fecha_resolucion = fecha_creacion + timedelta(days=random.randint(1, 4)) if estado_id == 4 else None
            
            cursor.execute("""
                INSERT INTO solicitudes (
                    comentario, categoria_id, subcategoria_id, prioridad, estado_id, 
                    fecha_creacion, fecha_resolucion, barrio_id, score_sentimiento, 
                    urgencia_nlp, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comentario, cat_id, sub_id, prioridad, estado_id, 
                fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"), 
                fecha_resolucion.strftime("%Y-%m-%d %H:%M:%S") if fecha_resolucion else None,
                barrio_id, score, urgencia, vecino_id
            ))
            sol_id = cursor.lastrowid
            
            # Registrar trazabilidad inicial
            trazabilidad.registrar_cambio_estado(conexion, sol_id, None, estado_id, vecino_id)
            
            # Si está resuelta, registrar el historial de transiciones simuladas
            if estado_id == 4:
                trazabilidad.registrar_cambio_estado(conexion, sol_id, 1, 3, 3) # En Proceso por Gestor
                trazabilidad.registrar_cambio_estado(conexion, sol_id, 3, 4, 3) # Resuelto por Gestor
                
        conexion.commit()
    conexion.close()

# Ejecutar inicialización al cargar
inicializar_base_de_datos_con_semilla()

# --- Obtener listas de referencia para selectores ---
def obtener_barrios():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM barrios")
    res = cursor.fetchall()
    conexion.close()
    return res

def obtener_vecinos():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre || ' ' || apellido || ' (DNI: ' || dni || ')' FROM usuarios WHERE rol_id = 1")
    res = cursor.fetchall()
    conexion.close()
    return res

def obtener_estados():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM estados_solicitud")
    res = cursor.fetchall()
    conexion.close()
    return res

def obtener_categorias():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM categorias")
    res = cursor.fetchall()
    conexion.close()
    return res

# Inicializar estado de sesión para el control de acceso
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None

with st.sidebar:
    # Logo municipal oficial de La Rioja en el sidebar
    if logo_data_url:
        st.markdown(f"""
        <div style='background-color: #ED1B24; padding: 1.2rem 1rem; border-radius: 12px; text-align: center; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(237, 27, 36, 0.15); border-bottom: 3px solid #76BC21;'>
            <img src='{logo_data_url}' alt='Logo La Rioja' style='max-width: 100%; height: auto; display: block; margin: 0 auto;'>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background-color: #ED1B24; padding: 1.2rem 1rem; border-radius: 12px; text-align: center; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(237, 27, 36, 0.15); border-bottom: 3px solid #76BC21;'>
            <div style='font-family: "Outfit", sans-serif; color: white; font-weight: 300; font-size: 1.3rem; line-height: 1;'>la <span style='font-weight: 800; font-size: 1.5rem;'>Rioja</span></div>
            <div style='font-family: "Outfit", sans-serif; color: white; font-weight: 600; font-size: 0.6rem; letter-spacing: 1px; margin-top: 0.1rem; opacity: 0.95;'>MUNICIPIO CAPITAL</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h3 style='margin-bottom: 0; font-family: \"Outfit\", sans-serif; color: #1F2937;'>Gestión Municipal</h3>", unsafe_allow_html=True)
    st.write("Atención Vecinal con Inteligencia Artificial")
    st.divider()

    # Construcción de opciones del menú basadas en login y permisos
    if not st.session_state.logged_in:
        menu_options = [
            "🔑 Iniciar Sesión",
            "👤 Gestión de Usuarios (CRUD)"
        ]
    else:
        user = st.session_state.usuario
        permisos = user["permisos"]
        rol_id = user["rol_id"]
        
        menu_options = []
        if rol_id == 2:
            menu_options.append("💬 Conversar con Datos (Chatbot IA)")
            
        menu_options.append("📥 Registrar Reclamo")
        menu_options.append("📜 Ver Historial")
        menu_options.append("✏️ Modificar Reclamo")
        
        if "VER_HISTORIAL_RECLAMOS" in permisos:
            menu_options.append("📊 Panel de Auditoría")
            
        if "GESTIONAR_ROLES_PERPOS" in permisos or "GESTIONAR_ROLES_PERMISOS" in permisos:
            menu_options.append("⚙️ Roles y Permisos")
            
        if rol_id in [2, 3]:
            menu_options.append("🤖 Reporte Ejecutivo IA")
            
        menu_options.append("📖 Guías de Usuario")
        menu_options.append("🚪 Cerrar Sesión")

    seccion = st.radio("Secciones:", menu_options)
    
    st.divider()
    if st.session_state.logged_in:
        st.markdown(f"👤 **Usuario:** {st.session_state.usuario['nombre_completo']}")
        st.markdown(f"💼 **Rol:** {st.session_state.usuario['rol_nombre']}")
    else:
        st.info("📌 **RuralConecta AI v2.0**\n\nDesarrollado para conectar y vincular a los ciudadanos de las zonas rurales.")

# --- Banner Municipal Corporativo ---
if logo_data_url:
    st.markdown(f"""
    <div class='muni-header'>
        <div class='muni-logo-img-container'>
            <img src='{logo_data_url}' alt='Logo La Rioja' style='height: 55px; display: block;'>
        </div>
        <div class='muni-header-right'>
            <div class='muni-socials'>
                <a href='#' class='muni-social-icon-new' title='Radio/TV'>
                    <svg viewBox="0 0 44 34" width="30" height="23" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="9" x2="33" y2="2" />
                        <rect x="2" y="9" width="38" height="23" rx="5" />
                        <circle cx="15" cy="20.5" r="6" />
                        <circle cx="15" cy="20.5" r="2.5" />
                        <path d="M15 13.5v2M15 25.5v-2M8 20.5h2M22 20.5h-2M10.5 16l1.5 1.5M19.5 25l-1.5-1.5M10.5 25l1.5-1.5M19.5 16l-1.5 1.5" stroke-width="1.8" />
                        <circle cx="31" cy="16" r="1.8" fill="white" />
                        <circle cx="31" cy="25" r="1.8" fill="white" />
                    </svg>
                </a>
                <span class='muni-social-divider'></span>
                <a href='#' class='muni-social-icon-new' title='Facebook'>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="white">
                        <path d="M14 13.5h2.5l1-3H14v-2c0-.8.2-1.3 1.3-1.3H17V4.5c-.3 0-1.2-.1-2.2-.1-2.2 0-3.8 1.3-3.8 3.8v2.3H8.5v3H11V22h3v-8.5z"/>
                    </svg>
                </a>
                <a href='#' class='muni-social-icon-new' title='X'>
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="white">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href='#' class='muni-social-icon-new' title='Instagram'>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
                        <circle cx="12" cy="12" r="4"/>
                        <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
                    </svg>
                </a>
                <a href='#' class='muni-social-icon-new' title='TikTok'>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="white">
                        <path d="M12.525.02c1.31.03 2.5.51 3.42 1.34A6.87 6.87 0 0 0 21 3.8v3.2a9.87 9.87 0 0 1-5 1.5v7.5a6 6 0 1 1-6-6c.46 0 .9.05 1.33.15V13.3a2.97 2.97 0 1 0-.33 5.7h.5a3 3 0 0 0 3-3V0h-2z"/>
                    </svg>
                </a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='muni-header'>
        <div class='muni-logo-box'>
            <div class='muni-logo-top'>
                <span class='muni-logo-la'>la</span>
                <span class='muni-logo-rioja'>Rioja</span>
            </div>
            <div class='muni-logo-sub'>MUNICIPIO CAPITAL</div>
        </div>
        <div class='muni-header-right'>
            <div class='muni-socials'>
                <a href='#' class='muni-social-icon-new' title='Radio/TV'>
                    <svg viewBox="0 0 44 34" width="30" height="23" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="9" x2="33" y2="2" />
                        <rect x="2" y="9" width="38" height="23" rx="5" />
                        <circle cx="15" cy="20.5" r="6" />
                        <circle cx="15" cy="20.5" r="2.5" />
                        <path d="M15 13.5v2M15 25.5v-2M8 20.5h2M22 20.5h-2M10.5 16l1.5 1.5M19.5 25l-1.5-1.5M10.5 25l1.5-1.5M19.5 16l-1.5 1.5" stroke-width="1.8" />
                        <circle cx="31" cy="16" r="1.8" fill="white" />
                        <circle cx="31" cy="25" r="1.8" fill="white" />
                    </svg>
                </a>
                <span class='muni-social-divider'></span>
                <a href='#' class='muni-social-icon-new' title='Facebook'>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="white">
                        <path d="M14 13.5h2.5l1-3H14v-2c0-.8.2-1.3 1.3-1.3H17V4.5c-.3 0-1.2-.1-2.2-.1-2.2 0-3.8 1.3-3.8 3.8v2.3H8.5v3H11V22h3v-8.5z"/>
                    </svg>
                </a>
                <a href='#' class='muni-social-icon-new' title='X'>
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="white">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href='#' class='muni-social-icon-new' title='Instagram'>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
                        <circle cx="12" cy="12" r="4"/>
                        <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
                    </svg>
                </a>
                <a href='#' class='muni-social-icon-new' title='TikTok'>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="white">
                        <path d="M12.525.02c1.31.03 2.5.51 3.42 1.34A6.87 6.87 0 0 0 21 3.8v3.2a9.87 9.87 0 0 1-5 1.5v7.5a6 6 0 1 1-6-6c.46 0 .9.05 1.33.15V13.3a2.97 2.97 0 1 0-.33 5.7h.5a3 3 0 0 0 3-3V0h-2z"/>
                    </svg>
                </a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Título Principal ---
if limpia_linda_url:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 0.2rem;">
        <h1 class='main-title' style='margin: 0; display: inline-block;'>RuralConecta AI 🌱</h1>
        <div style="font-family: 'Outfit', sans-serif; color: #2E7D32; font-size: 1.2rem; font-weight: 600; padding: 0.5rem 1rem; border-left: 3px solid #E6A15C; margin-left: 0.5rem;">
            Conectando Parajes, Cultivando Comunidad
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h1 class='main-title'>RuralConecta AI 🌱</h1>", unsafe_allow_html=True)

st.markdown("<p class='subtitle'>Gestión Inteligente de Conectividad y Solicitudes Rurales</p>", unsafe_allow_html=True)

# Helper para cargar datos con usuario_id
def cargar_datos_completos_con_usuario():
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
            s.urgencia_nlp,
            s.usuario_id
        FROM solicitudes s
        LEFT JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN subcategorias sub ON s.subcategoria_id = sub.id
        LEFT JOIN estados_solicitud est ON s.estado_id = est.id
        LEFT JOIN barrios b ON s.barrio_id = b.id
    """
    df = pd.read_sql_query(query, conexion)
    conexion.close()
    return df

def obtener_df_exportacion_completa():
    conexion = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            s.id AS nro_gestion,
            s.fecha_creacion,
            s.fecha_resolucion,
            est.nombre AS estado,
            s.prioridad,
            c.nombre AS categoria,
            sub.nombre AS subcategoria,
            b.nombre AS barrio,
            b.zona AS zona,
            s.comentario,
            s.score_sentimiento,
            CASE WHEN s.urgencia_nlp THEN 'SÍ' ELSE 'NO' END AS es_urgente,
            u_vec.nombre || ' ' || u_vec.apellido AS solicitante_nombre,
            u_vec.dni AS solicitante_dni,
            u_gest.nombre || ' ' || u_gest.apellido AS gestor_asignado
        FROM solicitudes s
        LEFT JOIN categorias c ON s.categoria_id = c.id
        LEFT JOIN subcategorias sub ON s.subcategoria_id = sub.id
        LEFT JOIN estados_solicitud est ON s.estado_id = est.id
        LEFT JOIN barrios b ON s.barrio_id = b.id
        LEFT JOIN usuarios u_vec ON s.usuario_id = u_vec.id
        LEFT JOIN usuarios u_gest ON s.asignado_a = u_gest.id
        ORDER BY s.id DESC
    """
    df = pd.read_sql_query(query, conexion)
    conexion.close()
    return df

def obtener_df_trazabilidad_completa():
    conexion = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            h.id AS trazabilidad_id,
            h.solicitud_id,
            s.comentario AS reclamo,
            e_ant.nombre AS estado_anterior,
            e_nue.nombre AS estado_nuevo,
            u.nombre || ' ' || u.apellido AS operador,
            r.nombre AS rol_operador,
            h.fecha_cambio
        FROM historial_estados h
        LEFT JOIN solicitudes s ON h.solicitud_id = s.id
        LEFT JOIN estados_solicitud e_ant ON h.estado_anterior_id = e_ant.id
        LEFT JOIN estados_solicitud e_nue ON h.estado_nuevo_id = e_nue.id
        LEFT JOIN usuarios u ON h.usuario_id = u.id
        LEFT JOIN roles r ON u.rol_id = r.id
        ORDER BY h.id DESC
    """
    df = pd.read_sql_query(query, conexion)
    conexion.close()
    return df

def generar_respuesta_chatbot_datos(prompt_usuario):
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM solicitudes")
        total_solicitudes = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT es.nombre, COUNT(*) 
            FROM solicitudes s 
            JOIN estados_solicitud es ON s.estado_id = es.id 
            GROUP BY es.nombre
        """)
        estados_map = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT c.nombre, COUNT(*) 
            FROM solicitudes s 
            JOIN categorias c ON s.categoria_id = c.id 
            GROUP BY c.nombre 
            ORDER BY COUNT(*) DESC
        """)
        cats_map = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT b.nombre, COUNT(*) 
            FROM solicitudes s 
            JOIN barrios b ON s.barrio_id = b.id 
            GROUP BY b.nombre 
            ORDER BY COUNT(*) DESC
        """)
        barrios_map = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE prioridad = 'ALTA'")
        total_alta = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE urgencia_nlp = 1 AND estado_id != 4")
        urgentes_abiertas = cursor.fetchone()[0]

        prompt_lower = prompt_usuario.lower()
        contexto_adicional = ""
        
        # Búsqueda semántica de categoría
        for cat in cats_map.keys():
            if any(kw in prompt_lower for kw in cat.lower().split() if len(kw) > 3):
                cursor.execute("""
                    SELECT s.id, s.comentario, s.prioridad, es.nombre, b.nombre
                    FROM solicitudes s
                    JOIN categorias c ON s.categoria_id = c.id
                    JOIN estados_solicitud es ON s.estado_id = es.id
                    JOIN barrios b ON s.barrio_id = b.id
                    WHERE c.nombre = ?
                    ORDER BY s.id DESC LIMIT 3
                """, (cat,))
                muestras = cursor.fetchall()
                contexto_adicional += f"\n- Muestra reciente en categoría '{cat}': {muestras}"
                break
                
        # Búsqueda por persona / vecino
        if "diego" in prompt_lower or "andrada" in prompt_lower:
            cursor.execute("""
                SELECT s.id, c.nombre, s.comentario, es.nombre, s.fecha_creacion
                FROM solicitudes s
                JOIN usuarios u ON s.usuario_id = u.id
                JOIN categorias c ON s.categoria_id = c.id
                JOIN estados_solicitud es ON s.estado_id = es.id
                WHERE u.dni = '27231845' OR LOWER(u.nombre) LIKE '%diego%'
                ORDER BY s.id DESC LIMIT 5
            """)
            vecino_recs = cursor.fetchall()
            contexto_adicional += f"\n- Solicitudes del vecino Diego Andrada: {vecino_recs}"

        conexion.close()
        
        prompt_ia = f"""
        Sos "RuralBot", el chatbot analítico exclusivo para el Gestor Municipal en RuralConecta AI.
        Contestá de forma clara, directa, profesional y amigable la consulta del gestor municipal usando los datos exactos del sistema.

        DATOS VIVOS DE LA BASE DE DATOS MUNICIPAL:
        - Total de solicitudes: {total_solicitudes}
        - Estado de las solicitudes: {estados_map}
        - Solicitudes por Categoría: {cats_map}
        - Solicitudes por Barrio / Paraje: {barrios_map}
        - Reclamos Prioridad ALTA: {total_alta}
        - Reclamos URGENTES abiertos: {urgentes_abiertas}
        {contexto_adicional}

        CONSULTA DEL GESTOR MUNICIPAL:
        "{prompt_usuario}"

        Indicaciones:
        - Responde usando Markdown con emojis amigables.
        - Ofrece cifras numéricas precisas del sistema.
        - Sugiere acciones de gestión municipal breves si aplica.
        """
        
        return consultar_ia(prompt_ia)
    except Exception as e:
        return f"⚠️ Ocurrió un error al procesar la consulta con la base de datos: {e}"

# Helper para capturar salida de reportes de trazabilidad
def obtener_reporte_trazabilidad_texto(reporte_func, *args):
    import io
    from contextlib import redirect_stdout
    conexion = sqlite3.connect(DB_PATH)
    f = io.StringIO()
    with redirect_stdout(f):
        reporte_func(conexion, *args)
    conexion.close()
    return f.getvalue()

# Helper para convertir tablas ASCII de trazabilidad en DataFrames de Pandas
def convertir_tabla_ascii_a_df(texto):
    lines = texto.strip().split('\n')
    data_rows = []
    headers = []
    
    for line in lines:
        line_clean = line.strip()
        # Ignorar líneas decorativas de separadores
        if not line_clean or line_clean.startswith('====') or line_clean.startswith('----'):
            continue
            
        # Si la línea tiene formato de celda de tabla: | valor1 | valor2 |
        if line_clean.startswith('|') and line_clean.endswith('|'):
            # Dividir por '|' y limpiar espacios en blanco
            parts = [p.strip() for p in line_clean.split('|')[1:-1]]
            
            # Evitar las líneas decorativas o cabeceras agregadas de títulos generales
            if len(parts) == 1 and any(keyword in parts[0] for keyword in ['DESEMPEÑO', 'ANÁLISIS', 'TRAZABILIDAD', 'ALERTAS', 'GESTORES']):
                continue
                
            # La primera fila encontrada que califique como celdas de datos es la cabecera
            if not headers:
                headers = parts
            else:
                data_rows.append(parts)
                
    if headers and data_rows:
        return pd.DataFrame(data_rows, columns=headers)
    return None

# =====================================================================
# SECCIÓN: INICIAR SESIÓN (Acceso Diferencial)
# =====================================================================
if seccion == "🔑 Iniciar Sesión":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Iniciar Sesión (Acceso Diferencial)")
    st.write("Ingrese sus credenciales de acceso para habilitar los paneles e inteligencia correspondientes a su perfil.")
    
    col_l1, col_l2 = st.columns([1, 1])
    with col_l1:
        dni_input = st.text_input("DNI de Usuario:")
        clave_input = st.text_input("Contraseña / Clave:", type="password")
        
        if st.button("Ingresar al Sistema", type="primary"):
            if not dni_input.strip() or not clave_input.strip():
                st.error("Debe ingresar tanto el DNI como la contraseña.")
            else:
                from main import verify_password
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                cursor.execute("""
                    SELECT u.id, u.nombre, u.apellido, u.rol_id, r.nombre, u.clave
                    FROM usuarios u
                    LEFT JOIN roles r ON u.rol_id = r.id
                    WHERE u.dni = ?
                """, (dni_input.strip(),))
                usuario = cursor.fetchone()
                
                if usuario:
                    u_id, nombre, apellido, rol_id, rol_nombre, clave_db = usuario
                    
                    if verify_password(clave_input, clave_db) or clave_input == clave_db:
                        # Login Exitoso
                        # Cargar permisos
                        cursor.execute("""
                            SELECT p.nombre 
                            FROM permisos p
                            JOIN roles_permisos rp ON p.id = rp.permiso_id
                            WHERE rp.rol_id = ?
                        """, (rol_id,))
                        permisos = {row[0] for row in cursor.fetchall()}
                        
                        st.session_state.logged_in = True
                        st.session_state.usuario = {
                            "id": u_id,
                            "nombre_completo": f"{nombre} {apellido}",
                            "rol_id": rol_id,
                            "rol_name_original": rol_nombre,
                            "rol_nombre": "Analista" if rol_id == 3 else ("De Gestión" if rol_id == 2 else "Vecino"),
                            "permisos": list(permisos)
                        }
                        conexion.close()
                        st.success(f"¡Bienvenido {nombre} {apellido}! Sesión iniciada como {rol_nombre}.")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas o usuario no registrado.")
                else:
                    st.error("Credenciales incorrectas o usuario no registrado.")
                conexion.close()
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: GESTIÓN DE USUARIOS (CRUD)
# =====================================================================
elif seccion == "👤 Gestión de Usuarios (CRUD)":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Gestión de Usuarios del Sistema (CRUD)")
    st.write("Cree, consulte, modifique o elimine cuentas de acceso al sistema municipal.")
    
    tab_alta, tab_listar, tab_baja, tab_modificar = st.tabs([
        "➕ Alta de Usuario", 
        "📋 Listar Usuarios", 
        "❌ Baja de Usuario", 
        "✏️ Modificar Usuario"
    ])
    
    # Conexión rápida
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Cargar roles
    cursor.execute("SELECT id, nombre FROM roles")
    roles_db = cursor.fetchall()
    roles_dict = {r_id: name for r_id, name in roles_db}
    
    with tab_alta:
        st.markdown("#### Registrar nuevo usuario")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            n_nombre = st.text_input("Nombre:", key="alta_nombre")
            n_apellido = st.text_input("Apellido:", key="alta_apellido")
            n_dni = st.text_input("DNI (Sin puntos):", key="alta_dni")
        with col_a2:
            n_cuil = st.text_input("CUIL (Sin guiones):", key="alta_cuil")
            n_clave = st.text_input("Contraseña:", type="password", key="alta_clave")
            n_rol = st.selectbox("Rol Asignado:", options=list(roles_dict.keys()), format_func=lambda x: roles_dict[x], key="alta_rol")
            
        if st.button("Guardar Usuario", type="primary"):
            if not all([n_nombre.strip(), n_apellido.strip(), n_dni.strip(), n_cuil.strip(), n_clave.strip()]):
                st.warning("Todos los campos son obligatorios.")
            else:
                from main import hash_password
                clave_hash = hash_password(n_clave)
                try:
                    cursor.execute("""
                        INSERT INTO usuarios (nombre, apellido, dni, cuil, clave, rol_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (n_nombre.strip(), n_apellido.strip(), n_dni.strip(), n_cuil.strip(), clave_hash, n_rol))
                    conexion.commit()
                    st.success(f"Usuario '{n_nombre} {n_apellido}' registrado exitosamente.")
                except sqlite3.IntegrityError:
                    st.error("El DNI o CUIL ingresados ya pertenecen a un usuario registrado.")
                except Exception as e:
                    st.error(f"Error al registrar usuario: {e}")
                    
    with tab_listar:
        st.markdown("#### Usuarios registrados")
        cursor.execute("""
            SELECT u.id, u.nombre, u.apellido, u.dni, u.cuil, r.nombre AS rol
            FROM usuarios u
            LEFT JOIN roles r ON u.rol_id = r.id
        """)
        users_data = cursor.fetchall()
        if users_data:
            df_users = pd.DataFrame(users_data, columns=["ID", "Nombre", "Apellido", "DNI", "CUIL", "Rol"])
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("No hay usuarios registrados.")
            
    with tab_baja:
        st.markdown("#### Eliminar usuario")
        cursor.execute("SELECT id, nombre || ' ' || apellido || ' (DNI: ' || dni || ')' FROM usuarios")
        usuarios_list = cursor.fetchall()
        if usuarios_list:
            u_options = {u_id: name for u_id, name in usuarios_list}
            u_baja_sel = st.selectbox("Seleccione usuario a eliminar:", options=list(u_options.keys()), format_func=lambda x: u_options[x], key="baja_usuario_sel")
            
            if st.button("Eliminar Cuenta permanentemente", type="primary"):
                try:
                    cursor.execute("DELETE FROM usuarios WHERE id = ?", (u_baja_sel,))
                    conexion.commit()
                    st.success("Usuario eliminado exitosamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar usuario: {e}")
        else:
            st.info("No hay usuarios registrados.")
            
    with tab_modificar:
        st.markdown("#### Modificar datos de usuario")
        cursor.execute("SELECT id, nombre, apellido, dni, cuil, rol_id FROM usuarios")
        usuarios_list_m = cursor.fetchall()
        if usuarios_list_m:
            u_options_m = {row[0]: f"{row[1]} {row[2]} (DNI: {row[3]})" for row in usuarios_list_m}
            u_mod_sel = st.selectbox("Seleccione usuario a modificar:", options=list(u_options_m.keys()), format_func=lambda x: u_options_m[x], key="mod_usuario_sel")
            
            # Buscar datos cargados
            cursor.execute("SELECT nombre, apellido, dni, cuil, rol_id FROM usuarios WHERE id = ?", (u_mod_sel,))
            user_current = cursor.fetchone()
            
            if user_current:
                curr_nom, curr_ape, curr_dni, curr_cuil, curr_rol = user_current
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    m_nombre = st.text_input("Nombre:", value=curr_nom, key="mod_nombre")
                    m_apellido = st.text_input("Apellido:", value=curr_ape, key="mod_apellido")
                    m_dni = st.text_input("DNI:", value=curr_dni, key="mod_dni")
                with col_m2:
                    m_cuil = st.text_input("CUIL:", value=curr_cuil, key="mod_cuil")
                    m_rol = st.selectbox("Rol:", options=list(roles_dict.keys()), index=list(roles_dict.keys()).index(curr_rol) if curr_rol in roles_dict else 0, format_func=lambda x: roles_dict[x], key="mod_rol")
                    m_clave = st.text_input("Nueva contraseña (Dejar vacío para mantener):", type="password", key="mod_clave")
                    
                if st.button("Guardar Cambios", key="btn_mod_usuario"):
                    if not all([m_nombre.strip(), m_apellido.strip(), m_dni.strip(), m_cuil.strip()]):
                        st.warning("Nombre, Apellido, DNI y CUIL son obligatorios.")
                    else:
                        try:
                            if m_clave.strip():
                                from main import hash_password
                                new_hash = hash_password(m_clave)
                                cursor.execute("""
                                    UPDATE usuarios 
                                    SET nombre = ?, apellido = ?, dni = ?, cuil = ?, clave = ?, rol_id = ?
                                    WHERE id = ?
                                """, (m_nombre.strip(), m_apellido.strip(), m_dni.strip(), m_cuil.strip(), new_hash, m_rol, u_mod_sel))
                            else:
                                cursor.execute("""
                                    UPDATE usuarios 
                                    SET nombre = ?, apellido = ?, dni = ?, cuil = ?, rol_id = ?
                                    WHERE id = ?
                                """, (m_nombre.strip(), m_apellido.strip(), m_dni.strip(), m_cuil.strip(), m_rol, u_mod_sel))
                            conexion.commit()
                            st.success("Usuario modificado exitosamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al modificar usuario: {e}")
        else:
            st.info("No hay usuarios registrados.")
            
    conexion.close()
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: REGISTRAR RECLAMO (Ingreso de Reclamos)
# =====================================================================
elif seccion == "📥 Registrar Reclamo":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Registrar Solicitud Vecinal")
    st.write("Ingrese el reclamo del vecino. La inteligencia del sistema analizará el texto en tiempo real para determinar el área municipal, la urgencia de negocio y sugerir respuestas inmediatas.")
    
    col_v, col_b = st.columns(2)
    
    with col_v:
        # Si está logueado como Vecino, auto-asigna su ID
        if st.session_state.logged_in and st.session_state.usuario["rol_id"] == 1:
            vecino_selec = st.session_state.usuario["id"]
            st.text_input("Vecino Solicitante:", value=st.session_state.usuario["nombre_completo"], disabled=True)
        else:
            vecinos = obtener_vecinos()
            vecino_options = {v_id: label for v_id, label in vecinos}
            vecino_selec = st.selectbox("Vecino Solicitante:", options=list(vecino_options.keys()), format_func=lambda x: vecino_options[x])
        
    with col_b:
        barrios = obtener_barrios()
        barrio_options = {b_id: name for b_id, name in barrios}
        barrio_selec = st.selectbox("Barrio de la Incidencia:", options=list(barrio_options.keys()), format_func=lambda x: barrio_options[x])
        
    comentario = st.text_area("Descripción de la Solicitud / Reclamo:", height=110, placeholder="Ej: Hay un pozo enorme lleno de agua en la calle principal, los autos tienen que esquivarlo y es muy peligroso...")
    
    if st.button("Procesar y Guardar Solicitud", type="primary"):
        if comentario.strip():
            # Procesar el comentario usando el analizador municipal
            analisis = analizar_comentario(comentario)
            cat_nombre = analisis["categoria"]
            subcat_nombre = analisis["subcategoria"]
            prioridad = analisis["prioridad"]
            sentimiento = analisis["score_sentimiento"]
            urgente = analisis["urgencia_nlp"]
            
            # Guardar en base de datos conectando con el esquema relacional
            conexion = sqlite3.connect(DB_PATH)
            cursor = conexion.cursor()
            
            # Obtener IDs
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (cat_nombre,))
            res_cat = cursor.fetchone()
            cat_id = res_cat[0] if res_cat else 1
            
            cursor.execute("SELECT id FROM subcategorias WHERE nombre = ?", (subcat_nombre,))
            res_sub = cursor.fetchone()
            sub_id = res_sub[0] if res_sub else None
            
            # Estado inicial PENDIENTE (id 1 en semilla o buscado)
            cursor.execute("SELECT id FROM estados_solicitud WHERE nombre = 'PENDIENTE'")
            res_est = cursor.fetchone()
            estado_id = res_est[0] if res_est else 1
            
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO solicitudes (
                    comentario, categoria_id, subcategoria_id, prioridad, estado_id, 
                    fecha_creacion, barrio_id, score_sentimiento, urgencia_nlp, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comentario, cat_id, sub_id, prioridad, estado_id, 
                fecha_actual, barrio_selec, sentimiento, urgente, vecino_selec
            ))
            solicitud_id = cursor.lastrowid
            
            # Registrar trazabilidad del cambio
            trazabilidad.registrar_cambio_estado(conexion, solicitud_id, None, estado_id, vecino_selec)
            
            conexion.commit()
            conexion.close()
            
            # Generar sugerencias de respuesta
            respuestas = generar_respuesta(cat_nombre)
            resp_formal = respuestas[0]
            resp_amigable = respuestas[1]
            
            st.success(f"¡Solicitud registrada correctamente en la base de datos! Nro de Gestión: #{solicitud_id}")
            
            # Mostrar resultados del análisis
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📊 Clasificación Automática")
                # Badge con color
                cat_class = cat_nombre.lower().replace(" ", "").replace("/", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                badge_type = "otros"
                for keyword in ["vial", "agua", "electrificacion", "residuos", "zoonosis", "ambiente", "infraestructura", "convivencia", "calles", "alumbrado", "basura"]:
                    if keyword in cat_class:
                        badge_type = keyword
                        break
                        
                st.markdown(f"**Área Municipal:** <span class='badge badge-{badge_type}'>{cat_nombre}</span>", unsafe_allow_html=True)
                st.markdown(f"**Subcategoría:** {subcat_nombre}")
                
                # Prioridad
                prio_class = prioridad.lower()
                st.markdown(f"**Prioridad:** <span class='badge badge-{prio_class}'>{prioridad}</span>", unsafe_allow_html=True)
                
                # Sentimiento y Urgencia
                sent_emoji = "😊" if sentimiento > 0.6 else "😐" if sentimiento >= 0.3 else "😡"
                st.write(f"**Score de Sentimiento:** {sentimiento:.2f} {sent_emoji}")
                
                urg_status = "🚨 SÍ" if urgente else "🟢 NO"
                st.write(f"**Urgencia NLP Detectada:** {urg_status}")
            
            with col2:
                st.markdown("### 📝 Respuestas Sugeridas al Vecino")
                st.info(f"✉️ **Canal Formal:**\n\n*{resp_formal}*")
                st.success(f"💬 **Canal Amigable (WhatsApp/Redes):**\n\n*{resp_amigable}*")
        else:
            st.warning("Debe ingresar la descripción del reclamo antes de procesar.")
            
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: CHATBOT PARA CONVERSAR CON LOS DATOS (Solo Gestor Municipal)
# =====================================================================
elif seccion in ["💬 Conversar con Datos (Chatbot IA)", "Conversar con Datos"]:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("💬 Chatbot Municipal: Conversa con los Datos de RuralConecta AI")
    st.write("Bienvenido, Gestor Municipal. Realice cualquier consulta en lenguaje natural para consultar la base de datos de 500 solicitudes, parajes, SLAs, prioridades o tendencias en tiempo real.")
    
    # Inicializar historial de chat en session_state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "👋 ¡Hola, Gestor Municipal! Soy **RuralBot**, tu asistente inteligente para conversar con la base de datos de solicitudes vecinales en tiempo real.\n\n¿En qué puedo ayudarte hoy? Por ejemplo, puedes preguntarme:\n- *\"¿Cuál es el estado general de las 500 solicitudes?\"*\n- *\"¿Cuáles son los parajes con más problemas de agua o caminos?\"*\n- *\"¿Cuántos reclamos urgentes tenemos pendientes?\"*\n- *\"¿Qué reclamos ingresó el vecino Diego Andrada?\"*"
            }
        ]
        
    # Renderizar mensajes anteriores
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Entrada de texto del chatbot
    if prompt_user := st.chat_input("Escriba su consulta sobre los datos del municipio..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt_user})
        with st.chat_message("user"):
            st.markdown(prompt_user)
            
        with st.spinner("Consultando la base de datos y analizando con IA..."):
            bot_reply = generar_respuesta_chatbot_datos(prompt_user)
            
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
            
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: VER HISTORIAL Y TRAZABILIDAD
# =====================================================================
elif seccion in ["📜 Ver Historial", "📋 Historial y Gestión", "📋 Mis Reclamos", "Ver historial"]:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("📜 Historial de Solicitudes Vecinales")
    
    # Cargar datos con usuario_id
    df = cargar_datos_completos_con_usuario()
    
    # Si es Vecino, filtrar solo sus reclamos
    es_vecino = st.session_state.logged_in and st.session_state.usuario["rol_id"] == 1
    if es_vecino:
        df = df[df["usuario_id"] == st.session_state.usuario["id"]]
        st.write("Consola Vecinal. Revise el historial, estado y seguimiento de sus solicitudes presentadas.")
    else:
        st.write("Consola de Gestión y Auditoría. Consulte los reclamos ingresados y el seguimiento completo de su trazabilidad.")
    
    if df.empty:
        st.info("No hay reclamos registrados para mostrar.")
    else:
        # Filtros interactivos
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            estado_filtro = st.selectbox("Filtrar por Estado:", ["TODOS"] + list(df["estado"].dropna().unique()), key="vh_estado")
        with col_f2:
            barrio_filtro = st.selectbox("Filtrar por Barrio:", ["TODOS"] + list(df["barrio"].dropna().unique()), key="vh_barrio")
        with col_f3:
            prioridad_filtro = st.selectbox("Filtrar por Prioridad:", ["TODOS", "ALTA", "MEDIA", "BAJA"], key="vh_prioridad")
            
        # Aplicar filtros
        df_filtrado = df.copy()
        if estado_filtro != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["estado"] == estado_filtro]
        if barrio_filtro != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["barrio"] == barrio_filtro]
        if prioridad_filtro != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["prioridad"] == prioridad_filtro]
            
        # Mostrar tabla resumida
        st.dataframe(
            df_filtrado[[
                "id", "fecha_creacion", "categoria", "prioridad", "estado", "barrio", "score_sentimiento", "urgencia_nlp"
            ]],
            use_container_width=True,
            column_config={
                "id": "Nro Gestión",
                "fecha_creacion": "Fecha Creación",
                "categoria": "Área Municipal",
                "prioridad": "Prioridad",
                "estado": "Estado",
                "barrio": "Barrio",
                "score_sentimiento": st.column_config.NumberColumn("Sentimiento", format="%.2f"),
                "urgencia_nlp": "Urgente"
            }
        )
        
        # Botones de exportación CSV exclusivos para el perfil Analista
        es_analista = st.session_state.logged_in and st.session_state.usuario["rol_id"] == 3
        if es_analista:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📥 Exportación de Datos para Análisis Externo (CSV)")
            st.write("Descargue la información de las solicitudes vecinales para su procesamiento en Excel, PowerBI o Python.")
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            with col_exp1:
                csv_filt = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar Vista Filtrada (CSV)",
                    data=csv_filt,
                    file_name=f"solicitudes_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="btn_csv_filt",
                    use_container_width=True
                )
            with col_exp2:
                df_comp = obtener_df_exportacion_completa()
                csv_comp = df_comp.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📊 Exportar Base Completa (CSV)",
                    data=csv_comp,
                    file_name=f"ruralconecta_solicitudes_completas_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="btn_csv_comp",
                    use_container_width=True
                )
            with col_exp3:
                df_traz = obtener_df_trazabilidad_completa()
                csv_traz = df_traz.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📜 Exportar Trazabilidad (CSV)",
                    data=csv_traz,
                    file_name=f"ruralconecta_trazabilidad_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="btn_csv_traz",
                    use_container_width=True
                )
        
        # Consulta de Trazabilidad por Solicitud
        st.divider()
        st.subheader("🔍 Detalle y Línea de Tiempo de Trazabilidad")
        
        ids_disponibles = sorted(list(df_filtrado["id"].unique()))
        
        if ids_disponibles:
            col_sel, col_act = st.columns([1, 2])
            
            with col_sel:
                solicitud_id_seleccionada = st.selectbox("Seleccione Nro de Gestión a Consultar:", ids_disponibles, key="vh_sol_sel")
                
                # Cargar datos del registro seleccionado
                sol_info = df[df["id"] == solicitud_id_seleccionada].iloc[0]
                
                st.markdown(f"**Reclamo Original:**\n\n*\"{sol_info['comentario']}\"*")
                st.write(f"**Ubicación/Barrio:** {sol_info['barrio']} (Zona {sol_info['zona']})")
                
                # Mostrar estados actuales en formato badge
                est_class = sol_info['estado'].lower().replace(" ", "")
                st.markdown(f"**Estado actual:** <span class='badge badge-{est_class}'>{sol_info['estado']}</span>", unsafe_allow_html=True)
                
            with col_act:
                st.markdown("#### Historial de Cambios (Auditoría)")
                
                # Consultar historial en la BD
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                cursor.execute("""
                    SELECT 
                        h.fecha_cambio,
                        e_ant.nombre AS estado_anterior,
                        e_nue.nombre AS estado_nuevo,
                        u.nombre || ' ' || u.apellido AS operador
                    FROM historial_estados h
                    LEFT JOIN estados_solicitud e_ant ON h.estado_anterior_id = e_ant.id
                    LEFT JOIN estados_solicitud e_nue ON h.estado_nuevo_id = e_nue.id
                    LEFT JOIN usuarios u ON h.usuario_id = u.id
                    WHERE h.solicitud_id = ?
                    ORDER BY h.fecha_cambio ASC
                """, (int(solicitud_id_seleccionada),))
                
                trazas = cursor.fetchall()
                conexion.close()
                
                if trazas:
                    for fecha, est_ant, est_nue, operador in trazas:
                        ant_label = est_ant if est_ant else "CREACIÓN"
                        st.write(f"🕒 **{fecha}** | `{ant_label}` ➡️ `{est_nue}` | Operador: *{operador or 'Vecino'}*")
                else:
                    st.info("No se registran cambios de estado previos para este reclamo.")
        else:
            st.warning("No hay solicitudes que coincidan con los filtros aplicados.")
            
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: MODIFICAR RECLAMO
# =====================================================================
elif seccion in ["✏️ Modificar Reclamo", "Modificar reclamo"]:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("✏️ Modificación y Control Operativo de Reclamos")
    st.write("Edite el estado, la prioridad, la categoría o el texto descriptivo de una solicitud existente.")
    
    df = cargar_datos_completos_con_usuario()
    
    es_vecino = st.session_state.logged_in and st.session_state.usuario["rol_id"] == 1
    if es_vecino:
        df = df[df["usuario_id"] == st.session_state.usuario["id"]]
    
    if df.empty:
        st.info("No hay reclamos disponibles para modificar.")
    else:
        ids_disponibles = sorted(list(df["id"].unique()))
        sol_id_mod = st.selectbox("Seleccione Nro de Gestión a Modificar:", ids_disponibles, key="mr_sol_id")
        
        sol_info = df[df["id"] == sol_id_mod].iloc[0]
        
        # Resumen del reclamo seleccionado
        st.markdown(f"### Reclamo #{sol_id_mod}")
        est_class = sol_info['estado'].lower().replace(" ", "")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.markdown(f"**Estado actual:** <span class='badge badge-{est_class}'>{sol_info['estado']}</span>", unsafe_allow_html=True)
        with col_r2:
            st.markdown(f"**Área/Categoría:** {sol_info['categoria']}")
        with col_r3:
            prio_class = str(sol_info['prioridad']).lower()
            st.markdown(f"**Prioridad:** <span class='badge badge-{prio_class}'>{sol_info['prioridad']}</span>", unsafe_allow_html=True)
            
        st.write(f"**Barrio:** {sol_info['barrio']} | **Fecha Creación:** {sol_info['fecha_creacion']}")
        st.markdown(f"**Descripción Original:** *\"{sol_info['comentario']}\"*")
        
        st.divider()
        st.markdown("#### Opciones de Edición")
        
        tab_est, tab_prio, tab_cat, tab_txt, tab_del = st.tabs([
            "🔄 Estado", 
            "⚡ Prioridad", 
            "🏷️ Categoría Municipal", 
            "📝 Comentario / Descripción",
            "⚠️ Eliminar"
        ])
        
        # Tab 1: Estado
        with tab_est:
            st.write("Modifique el estado operativo de la solicitud para registrar el avance.")
            list_estados = obtener_estados()
            dict_estados = {name: est_id for est_id, name in list_estados}
            
            idx_est = list(dict_estados.keys()).index(sol_info['estado']) if sol_info['estado'] in dict_estados else 0
            nuevo_estado = st.selectbox("Nuevo Estado:", options=list(dict_estados.keys()), index=idx_est, key="mr_nuevo_estado")
            
            id_operador = st.session_state.usuario["id"] if st.session_state.logged_in else 3
            if st.button("Guardar Nuevo Estado", type="primary", key="btn_mr_estado"):
                estado_actual_nombre = sol_info['estado']
                estado_actual_id = dict_estados.get(estado_actual_nombre)
                nuevo_estado_id = dict_estados.get(nuevo_estado)
                
                if estado_actual_id == nuevo_estado_id:
                    st.warning("La solicitud ya se encuentra en ese estado.")
                else:
                    conexion = sqlite3.connect(DB_PATH)
                    cursor = conexion.cursor()
                    
                    if nuevo_estado in ["RESUELTO", "RECHAZADO"]:
                        fecha_resol = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            UPDATE solicitudes 
                            SET estado_id = ?, fecha_resolucion = ? 
                            WHERE id = ?
                        """, (nuevo_estado_id, fecha_resol, int(sol_id_mod)))
                    else:
                        cursor.execute("""
                            UPDATE solicitudes 
                            SET estado_id = ?, fecha_resolucion = NULL 
                            WHERE id = ?
                        """, (nuevo_estado_id, int(sol_id_mod)))
                        
                    trazabilidad.registrar_cambio_estado(conexion, int(sol_id_mod), estado_actual_id, nuevo_estado_id, id_operador)
                    
                    conexion.commit()
                    conexion.close()
                    st.success(f"¡Estado del reclamo #{sol_id_mod} actualizado a '{nuevo_estado}' con éxito!")
                    st.rerun()

        # Tab 2: Prioridad
        with tab_prio:
            st.write("Ajuste la prioridad asignada al reclamo.")
            prioridades_opt = ["BAJA", "MEDIA", "ALTA"]
            idx_prio = prioridades_opt.index(sol_info['prioridad']) if sol_info['prioridad'] in prioridades_opt else 0
            nueva_prioridad = st.selectbox("Nueva Prioridad:", options=prioridades_opt, index=idx_prio, key="mr_nueva_prio")
            
            if st.button("Guardar Nueva Prioridad", type="primary", key="btn_mr_prio"):
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                cursor.execute("UPDATE solicitudes SET prioridad = ? WHERE id = ?", (nueva_prioridad, int(sol_id_mod)))
                conexion.commit()
                conexion.close()
                st.success(f"¡Prioridad del reclamo #{sol_id_mod} actualizada a '{nueva_prioridad}'!")
                st.rerun()

        # Tab 3: Categoría Municipal
        with tab_cat:
            st.write("Reasigne la categoría / área municipal correspondiente al reclamo.")
            cats_list = obtener_categorias()
            dict_cats = {name: c_id for c_id, name in cats_list}
            idx_cat = list(dict_cats.keys()).index(sol_info['categoria']) if sol_info['categoria'] in dict_cats else 0
            nueva_categoria = st.selectbox("Nueva Categoría Municipal:", options=list(dict_cats.keys()), index=idx_cat, key="mr_nueva_cat")
            
            if st.button("Guardar Nueva Categoría", type="primary", key="btn_mr_cat"):
                cat_id_nueva = dict_cats[nueva_categoria]
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                cursor.execute("UPDATE solicitudes SET categoria_id = ? WHERE id = ?", (cat_id_nueva, int(sol_id_mod)))
                conexion.commit()
                conexion.close()
                st.success(f"¡Categoría del reclamo #{sol_id_mod} actualizada a '{nueva_categoria}'!")
                st.rerun()

        # Tab 4: Comentario / Descripción
        with tab_txt:
            st.write("Edite la descripción o texto original registrado para este reclamo.")
            nuevo_comentario = st.text_area("Descripción / Comentario:", value=str(sol_info['comentario']), height=120, key="mr_nuevo_comentario")
            
            if st.button("Guardar Cambios en Descripción", type="primary", key="btn_mr_comentario"):
                if nuevo_comentario.strip():
                    conexion = sqlite3.connect(DB_PATH)
                    cursor = conexion.cursor()
                    cursor.execute("UPDATE solicitudes SET comentario = ? WHERE id = ?", (nuevo_comentario.strip(), int(sol_id_mod)))
                    conexion.commit()
                    conexion.close()
                    st.success(f"¡Descripción del reclamo #{sol_id_mod} actualizada correctamente!")
                    st.rerun()
                else:
                    st.warning("El texto de la descripción no puede estar vacío.")

        # Tab 5: Eliminar Solicitud
        with tab_del:
            st.markdown("⚠️ **Zona de Peligro**")
            st.write("Eliminar permanentemente esta solicitud y todo su historial de la base de datos.")
            if st.button("Eliminar esta Solicitud Definitivamente", type="primary", key="btn_mr_del"):
                conexion = sqlite3.connect(DB_PATH)
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM historial_estados WHERE solicitud_id = ?", (int(sol_id_mod),))
                cursor.execute("DELETE FROM solicitudes WHERE id = ?", (int(sol_id_mod),))
                conexion.commit()
                conexion.close()
                st.success(f"La solicitud #{sol_id_mod} ha sido eliminada permanentemente.")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: PANEL DE AUDITORÍA Y TRAZABILIDAD
# =====================================================================
elif seccion == "📊 Panel de Auditoría":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Panel de Auditoría y Trazabilidad de Flujo")
    st.write("Consola analítica de auditoría. Monitoree cuellos de botella, niveles de servicio (SLA) y trazabilidad completa.")
    
    es_analista = st.session_state.logged_in and st.session_state.usuario["rol_id"] == 3
    
    # KPI en la web
    kpis = trazabilidad.obtener_kpis_generales(sqlite3.connect(DB_PATH))
    
    col_ak1, col_ak2, col_ak3, col_ak4, col_ak5 = st.columns(5)
    with col_ak1:
        st.metric("Total Reclamos", kpis['total'])
    with col_ak2:
        st.metric("Resueltos / Cerrados", kpis['resueltos'])
    with col_ak3:
        st.metric("Promedio Resolución", f"{kpis['tiempo_promedio_hs']:.1f} hs")
    with col_ak4:
        st.metric("Cumplimiento SLA", f"{kpis['sla_cumplimiento_porc']:.1f}%")
    with col_ak5:
        st.metric("Alertas SLA", kpis['vencidos_abiertos'])
        
    st.divider()
    
    auditoria_opt = st.selectbox(
        "Seleccione Reporte o Acción de Auditoría:",
        [
            "1. Reporte de Desempeño por Categoría",
            "2. Análisis de Cuellos de Botella (Dwell Times)",
            "3. Trazabilidad Cronológica de un Reclamo",
            "4. Ver Alertas de Desviación y SLA Excedido",
            "5. Reporte de Desempeño de Gestores",
            "6. Simular/Resetear Historial de Auditoría (Testing)",
            "7. Visualización Gráfica de Métricas (Original)"
        ]
    )
    
    if auditoria_opt.startswith("1."):
        st.markdown("#### Reporte de Desempeño por Categoría")
        texto_rep = obtener_reporte_trazabilidad_texto(trazabilidad.reporte_desempeno_categorias)
        df_rep = convertir_tabla_ascii_a_df(texto_rep)
        if df_rep is not None:
            st.dataframe(df_rep, use_container_width=True)
            if es_analista:
                csv_rep = df_rep.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Descargar Reporte en CSV", csv_rep, file_name="reporte_desempeno_categorias.csv", mime="text/csv", key="dl_csv_cat")
        else:
            st.markdown(f"<pre class='muni-report-box'>{html.escape(texto_rep)}</pre>", unsafe_allow_html=True)
        
    elif auditoria_opt.startswith("2."):
        st.markdown("#### Análisis de Cuellos de Botella (Dwell Times)")
        texto_rep = obtener_reporte_trazabilidad_texto(trazabilidad.reporte_cuellos_botella)
        df_rep = convertir_tabla_ascii_a_df(texto_rep)
        if df_rep is not None:
            st.dataframe(df_rep, use_container_width=True)
            if es_analista:
                csv_rep = df_rep.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Descargar Reporte en CSV", csv_rep, file_name="analisis_cuellos_botella.csv", mime="text/csv", key="dl_csv_dwell")
        else:
            st.markdown(f"<pre class='muni-report-box'>{html.escape(texto_rep)}</pre>", unsafe_allow_html=True)
        
    elif auditoria_opt.startswith("3."):
        st.markdown("#### Trazabilidad Cronológica de un Reclamo")
        s_id_str = st.text_input("Ingrese ID del Reclamo a Investigar:")
        if s_id_str.strip():
            try:
                s_id_val = int(s_id_str.strip())
                
                # Realizar consulta de detalles del reclamo directamente
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
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
                """, (s_id_val,))
                
                sol = cursor.fetchone()
                
                if not sol:
                    st.warning(f"No se encontró ninguna solicitud con ID {s_id_val}.")
                    conn.close()
                else:
                    s_id, comentario, f_creacion, f_resolucion, prioridad, cat, estado, vecino, gestor = sol
                    
                    # Calcular tiempo de gestión
                    try:
                        fc = datetime.strptime(f_creacion, "%Y-%m-%d %H:%M:%S")
                        if f_resolucion:
                            fr = datetime.strptime(f_resolucion, "%Y-%m-%d %H:%M:%S")
                            tiempo_total_td = fr - fc
                            estado_tiempo_lbl = "Tiempo de Resolución"
                        else:
                            tiempo_total_td = datetime.now() - fc
                            estado_tiempo_lbl = "Tiempo Activo en Bandeja"
                        
                        dias = tiempo_total_td.days
                        horas = tiempo_total_td.seconds // 3600
                        minutos = (tiempo_total_td.seconds % 3600) // 60
                        tiempo_str = f"{dias}d {horas}h {minutos}m"
                    except Exception:
                        tiempo_str = "No disponible"
                        estado_tiempo_lbl = "Tiempo de Gestión"

                    # Asignar colores a estados y prioridades
                    prioridad_color = "#ED1B24" if prioridad == "ALTA" else "#F59E0B" if prioridad == "MEDIA" else "#10B981"
                    estado_clase_map = {
                        "PENDIENTE": "badge-pendiente",
                        "EN REVISION": "badge-revision",
                        "EN PROCESO": "badge-proceso",
                        "RESUELTO": "badge-resuelto",
                        "RECHAZADO": "badge-rechazado"
                    }
                    est_upper = (estado or "PENDIENTE").upper()
                    est_class = estado_clase_map.get(est_upper, "badge-pendiente")
                    
                    # Renderizar tarjeta premium de detalles
                    st.markdown(f"""
                    <div class="glass-card" style="margin-top: 1rem; border-left: 5px solid #ED1B24;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F3F4F6; padding-bottom: 0.8rem; margin-bottom: 1rem;">
                            <span style="font-size: 1.4rem; font-weight: 800; color: #1F2937; font-family: 'Outfit', sans-serif;">Detalles del Reclamo #{s_id}</span>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <span class="badge" style="background-color: {prioridad_color}; font-weight: bold; margin-right: 0px;">{prioridad or 'BAJA'}</span>
                                <span class="badge {est_class}" style="font-weight: bold; margin-right: 0px;">{estado or 'PENDIENTE'}</span>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.2rem; font-family: 'Inter', sans-serif;">
                            <div>
                                <span style="font-size: 0.8rem; color: #6B7280; text-transform: uppercase; font-weight: 600;">Vecino Reportante</span><br/>
                                <span style="color: #1F2937; font-weight: 600; font-size: 0.95rem;">{vecino or 'Anónimo / Sin asignar'}</span>
                            </div>
                            <div>
                                <span style="font-size: 0.8rem; color: #6B7280; text-transform: uppercase; font-weight: 600;">Categoría</span><br/>
                                <span style="color: #1F2937; font-weight: 600; font-size: 0.95rem;">{cat or 'Sin Categoría'}</span>
                            </div>
                            <div>
                                <span style="font-size: 0.8rem; color: #6B7280; text-transform: uppercase; font-weight: 600;">Gestor Asignado</span><br/>
                                <span style="color: #1F2937; font-weight: 600; font-size: 0.95rem;">{gestor or 'Sin Asignar'}</span>
                            </div>
                            <div>
                                <span style="font-size: 0.8rem; color: #6B7280; text-transform: uppercase; font-weight: 600;">Fecha de Ingreso</span><br/>
                                <span style="color: #1F2937; font-weight: 600; font-size: 0.95rem;">{f_creacion}</span>
                            </div>
                            <div>
                                <span style="font-size: 0.8rem; color: #6B7280; text-transform: uppercase; font-weight: 600;">{estado_tiempo_lbl}</span><br/>
                                <span style="color: #ED1B24; font-weight: 800; font-size: 1.1rem;">{tiempo_str}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Comentario original en tarjeta elegante
                    st.markdown("<div style='margin-bottom: 1rem;'>", unsafe_allow_html=True)
                    with st.expander("📝 Ver Comentario / Descripción del Reclamo", expanded=True):
                        st.markdown(f'<div style="font-size: 1.05rem; padding: 0.5rem; color: #374151; font-style: italic; font-family: \'Inter\', sans-serif;">"{comentario}"</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Obtener historial de transiciones como DataFrame
                    df_hist = pd.read_sql_query("""
                        SELECT h.fecha_cambio AS [Fecha de Cambio], 
                               COALESCE(e_ant.nombre, 'Creación') AS [Estado Anterior], 
                               COALESCE(e_nue.nombre, 'PENDIENTE') AS [Estado Nuevo], 
                               COALESCE(u.nombre || ' ' || u.apellido, 'Sistema') AS [Responsable],
                               CASE u.rol_id 
                                   WHEN 1 THEN 'Vecino' 
                                   WHEN 2 THEN 'Gestor' 
                                   WHEN 3 THEN 'Analista' 
                                   ELSE 'Usuario' 
                               END AS [Rol]
                        FROM historial_estados h
                        LEFT JOIN estados_solicitud e_ant ON h.estado_anterior_id = e_ant.id
                        LEFT JOIN estados_solicitud e_nue ON h.estado_nuevo_id = e_nue.id
                        LEFT JOIN usuarios u ON h.usuario_id = u.id
                        WHERE h.solicitud_id = ?
                        ORDER BY h.fecha_cambio ASC
                    """, conn, params=(s_id_val,))
                    
                    # Mostrar las dos vistas: Timeline Visual y Tabla Detallada
                    col_t1, col_t2 = st.columns([1, 1])
                    
                    with col_t1:
                        st.markdown("##### 📅 Línea de Tiempo de Auditoría")
                        
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
                        """, (s_id_val,))
                        historial = cursor.fetchall()
                        
                        if not historial:
                            st.info("No hay transiciones registradas en el historial de este reclamo.")
                        else:
                            timeline_html = "<div style='margin: 0.5rem 0 1.5rem 1rem; border-left: 3px solid #ED1B24; padding-left: 1.5rem; position: relative; font-family: \"Inter\", sans-serif;'>"
                            for idx, (fecha, est_ant, est_nue, operador, rol_id) in enumerate(historial):
                                operador_str = operador or "Sistema (Automático)"
                                rol_desc = "Vecino" if rol_id == 1 else "Gestor" if rol_id == 2 else "Analista" if rol_id == 3 else "Usuario"
                                
                                if est_ant is None:
                                    text_desc = f"Creado e ingresado como <span style='color: #4B5563; font-weight: bold;'>{est_nue}</span>"
                                else:
                                    text_desc = f"Cambio de estado: <span style='color: #4B5563;'>{est_ant}</span> ➡️ <span style='color: #1F2937; font-weight: bold;'>{est_nue}</span>"
                                
                                timeline_html += f"""
                                <div style='position: relative; margin-bottom: 1.5rem;'>
                                    <span style='position: absolute; left: -31px; top: 4px; background-color: #ED1B24; border: 3px solid white; border-radius: 50%; width: 14px; height: 14px; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.15);'></span>
                                    <span style='font-size: 0.8rem; font-weight: bold; color: #ED1B24;'>{fecha}</span><br/>
                                    <span style='font-size: 0.92rem; color: #1F2937; font-weight: 500;'>{text_desc}</span><br/>
                                    <span style='font-size: 0.78rem; color: #6B7280;'>Responsable: <b>{operador_str}</b> ({rol_desc})</span>
                                </div>
                                """
                            timeline_html += "</div>"
                            st.markdown(timeline_html, unsafe_allow_html=True)
                            
                    with col_t2:
                        st.markdown("##### 📋 Historial en Formato de Tabla")
                        st.dataframe(df_hist, use_container_width=True, hide_index=True)
                        
                    conn.close()
            except ValueError:
                st.error("Por favor, ingrese un ID numérico válido.")
                
    elif auditoria_opt.startswith("4."):
        st.markdown("#### Alertas de Desviación y SLA Excedido")
        texto_rep = obtener_reporte_trazabilidad_texto(trazabilidad.reporte_alertas_sla)
        df_rep = convertir_tabla_ascii_a_df(texto_rep)
        if df_rep is not None:
            st.dataframe(df_rep, use_container_width=True)
            if es_analista:
                csv_rep = df_rep.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Descargar Reporte en CSV", csv_rep, file_name="alertas_desviacion_sla.csv", mime="text/csv", key="dl_csv_sla")
        else:
            st.markdown(f"<pre class='muni-report-box'>{html.escape(texto_rep)}</pre>", unsafe_allow_html=True)
        
    elif auditoria_opt.startswith("5."):
        st.markdown("#### Reporte de Desempeño de Gestores")
        texto_rep = obtener_reporte_trazabilidad_texto(trazabilidad.reporte_desempeno_gestores)
        df_rep = convertir_tabla_ascii_a_df(texto_rep)
        if df_rep is not None:
            st.dataframe(df_rep, use_container_width=True)
            if es_analista:
                csv_rep = df_rep.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Descargar Reporte en CSV", csv_rep, file_name="desempeno_gestores.csv", mime="text/csv", key="dl_csv_gestores")
        else:
            st.markdown(f"<pre class='muni-report-box'>{html.escape(texto_rep)}</pre>", unsafe_allow_html=True)
        
    elif auditoria_opt.startswith("6."):
        st.markdown("#### Simulación e Historial de Testing")
        st.warning("Esta acción eliminará el historial de auditoría previo y creará un set coherente de transiciones de prueba para validar el sistema.")
        if st.button("Ejecutar Simulación de Historial", type="primary"):
            conexion = sqlite3.connect(DB_PATH)
            total = trazabilidad.simular_datos_historicos(conexion)
            conexion.close()
            st.success(f"¡Simulación ejecutada correctamente! Se insertaron {total} transiciones de estado en historial_estados.")
            st.rerun()
            
    elif auditoria_opt.startswith("7."):
        st.markdown("#### Visualización Gráfica de Métricas")
        stats = generar_estadisticas()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### Volumen de Reclamos por Categoría")
            if not stats["categorias"].empty:
                st.bar_chart(stats["categorias"])
        with col_g2:
            st.markdown("##### Volumen de Reclamos por Barrio")
            if not stats["barrios"].empty:
                st.bar_chart(stats["barrios"])
                
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            st.markdown("##### Estado de las Solicitudes")
            if not stats["estados"].empty:
                st.bar_chart(stats["estados"])
        with col_g4:
            st.markdown("##### Distribución de Prioridades")
            if not stats["prioridades"].empty:
                st.bar_chart(stats["prioridades"])
                
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: GESTIÓN DE ROLES Y PERMISOS
# =====================================================================
elif seccion == "⚙️ Roles y Permisos":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Gestión de Roles y Permisos del Sistema")
    st.write("Administre los roles del personal municipal y conceda o revoque privilegios en tiempo real.")
    
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    tab_rol_crear, tab_rol_listar, tab_rol_asignar, tab_rol_revocar = st.tabs([
        "➕ Crear Rol",
        "📋 Listar Roles y Permisos",
        "🔑 Asignar Permiso",
        "❌ Revocar Permiso"
    ])
    
    with tab_rol_crear:
        st.markdown("#### Crear Nuevo Rol")
        n_rol_nombre = st.text_input("Nombre del nuevo Rol:", key="crear_rol_nombre")
        if st.button("Crear Rol", key="btn_crear_rol"):
            if not n_rol_nombre.strip():
                st.warning("El nombre del rol no puede estar vacío.")
            else:
                try:
                    cursor.execute("SELECT id FROM roles WHERE LOWER(nombre) = LOWER(?)", (n_rol_nombre.strip(),))
                    if cursor.fetchone():
                        st.warning(f"El rol '{n_rol_nombre.strip()}' ya existe.")
                    else:
                        cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (n_rol_nombre.strip(),))
                        conexion.commit()
                        st.success(f"Rol '{n_rol_nombre.strip()}' creado exitosamente.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al crear el rol: {e}")
                    
    with tab_rol_listar:
        st.markdown("#### Roles y Permisos Asignados")
        cursor.execute("SELECT id, nombre FROM roles")
        roles_list = cursor.fetchall()
        for r_id, r_nom in roles_list:
            cursor.execute("""
                SELECT p.nombre, p.descripcion 
                FROM permisos p
                JOIN roles_permisos rp ON p.id = rp.permiso_id
                WHERE rp.rol_id = ?
            """, (r_id,))
            perms = cursor.fetchall()
            with st.expander(f"💼 Rol: {r_nom} (ID: {r_id})"):
                if perms:
                    for p_nom, p_desc in perms:
                        st.write(f"🔑 **{p_nom}**: *{p_desc}*")
                else:
                    st.info("Este rol no cuenta con ningún permiso asignado actualmente.")
                    
    with tab_rol_asignar:
        st.markdown("#### Asignar Permiso a Rol")
        cursor.execute("SELECT id, nombre FROM roles")
        roles_list = cursor.fetchall()
        cursor.execute("SELECT id, nombre, descripcion FROM permisos")
        permisos_list = cursor.fetchall()
        
        if roles_list and permisos_list:
            r_dict = {r_id: name for r_id, name in roles_list}
            p_dict = {p_id: f"{name} ({desc})" for p_id, name, desc in permisos_list}
            
            sel_r_id = st.selectbox("Seleccione el Rol:", options=list(r_dict.keys()), format_func=lambda x: r_dict[x], key="asignar_rol_sel")
            sel_p_id = st.selectbox("Seleccione el Permiso a conceder:", options=list(p_dict.keys()), format_func=lambda x: p_dict[x], key="asignar_permiso_sel")
            
            if st.button("Conceder Permiso", type="primary", key="btn_asignar_permiso"):
                try:
                    cursor.execute("INSERT INTO roles_permisos (rol_id, permiso_id) VALUES (?, ?)", (sel_r_id, sel_p_id))
                    conexion.commit()
                    st.success("Permiso asignado correctamente al rol.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("El rol ya cuenta con este permiso asignado.")
                except Exception as e:
                    st.error(f"Error al asignar permiso: {e}")
        else:
            st.info("Roles o permisos no disponibles.")
            
    with tab_rol_revocar:
        st.markdown("#### Revocar Permiso de Rol")
        cursor.execute("SELECT id, nombre FROM roles")
        roles_list = cursor.fetchall()
        
        if roles_list:
            r_dict = {r_id: name for r_id, name in roles_list}
            sel_r_id_rev = st.selectbox("Seleccione el Rol:", options=list(r_dict.keys()), format_func=lambda x: r_dict[x], key="revocar_rol_sel")
            
            # Cargar permisos específicos asignados a ese rol
            cursor.execute("""
                SELECT p.id, p.nombre 
                FROM permisos p
                JOIN roles_permisos rp ON p.id = rp.permiso_id
                WHERE rp.rol_id = ?
            """, (sel_r_id_rev,))
            perms_rev = cursor.fetchall()
            
            if perms_rev:
                p_rev_dict = {p_id: name for p_id, name in perms_rev}
                sel_p_id_rev = st.selectbox("Seleccione el Permiso a revocar:", options=list(p_rev_dict.keys()), format_func=lambda x: p_rev_dict[x], key="revocar_permiso_sel")
                
                if st.button("Revocar Permiso", type="primary", key="btn_revocar_permiso"):
                    try:
                        cursor.execute("DELETE FROM roles_permisos WHERE rol_id = ? AND permiso_id = ?", (sel_r_id_rev, sel_p_id_rev))
                        conexion.commit()
                        st.success("Permiso revocado exitosamente del rol.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al revocar permiso: {e}")
            else:
                st.info("Este rol no tiene permisos asignados para revocar.")
        else:
            st.info("Roles no disponibles.")
            
    conexion.close()
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: REPORTE EJECUTIVO IA
# =====================================================================
elif seccion == "🤖 Reporte Ejecutivo IA":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Generador de Reportes de Gestión con IA (Ollama)")
    st.write("Presione el botón inferior para compilar los reclamos actuales y que la Inteligencia Artificial analice el estado urbano, determine las causas raíz y proponga planes de acción al intendente municipal.")
    
    stats = generar_estadisticas()
    
    if stats["total"] == 0:
        st.warning("No hay solicitudes cargadas para generar el reporte.")
    else:
        # Construir prompt
        prompt = f"""
        Sos un analista de gestión municipal experto. Generá un reporte ejecutivo a partir de las siguientes estadísticas de reclamos de vecinos de la ciudad:
        - Total de solicitudes: {stats['total']}
        - Categorías de reclamos y cantidad: {stats['categorias'].to_dict()}
        - Prioridades y cantidad: {stats['prioridades'].to_dict()}
        - Estado de los reclamos: {stats['estados'].to_dict()}
        - Reclamos por barrio: {stats['barrios'].to_dict()}
        - Score promedio de sentimiento vecinal (0 es muy negativo/enojado, 1 es agradable): {stats['sentimiento_promedio']:.2f}
        - Total de casos muy urgentes detectados por NLP: {stats['urgentes_total']}
        
        El informe debe estar formateado en Markdown, ser sumamente profesional, con diagnóstico y recomendaciones operativas aplicables al municipio.
        """
        
        if st.button("Generar Reporte de Gestión", type="primary"):
            with st.spinner("La Inteligencia Artificial está analizando los datos municipales..."):
                reporte = consultar_ia(prompt)
                st.markdown(reporte)
                
                es_analista = st.session_state.logged_in and st.session_state.usuario["rol_id"] == 3
                if es_analista:
                    col_rep1, col_rep2 = st.columns(2)
                    with col_rep1:
                        st.download_button(
                            label="📥 Descargar Reporte Ejecutivo (TXT)",
                            data=reporte,
                            file_name=f"reporte_gestion_municipal_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            key="btn_dl_txt_rep"
                        )
                    with col_rep2:
                        df_exp = obtener_df_exportacion_completa()
                        csv_exp = df_exp.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📊 Descargar Base Completa (CSV)",
                            data=csv_exp,
                            file_name=f"dataset_solicitudes_ejecutivo_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            key="btn_dl_csv_exec"
                        )
                else:
                    st.download_button(
                        label="📥 Descargar Reporte Ejecutivo (TXT)",
                        data=reporte,
                        file_name=f"reporte_gestion_municipal_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        key="btn_dl_txt_rep"
                    )
                
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# SECCIÓN: CERRAR SESIÓN (Logout)
# =====================================================================
# =====================================================================
# SECCIÓN: GUÍAS DE USUARIO
# =====================================================================
elif seccion == "📖 Guías de Usuario":
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.title("📖 Centro de Guías de Usuario")
    st.write("Bienvenido al centro de documentación y manuales de usuario de **SmartAssist Municipal AI**. A continuación encontrará guías completas para cada sección del sistema.")
    
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏛️ 1. Módulo de Auditoría y SLAs", 
        "🔑 2. Acceso, CRUD y Permisos", 
        "📥 3. Registro Inteligente", 
        "📋 4. Consola y Operación",
        "🤖 5. Reporte Ejecutivo con IA"
    ])
    
    with tab1:
        st.markdown("### 🏛️ Módulo de Auditoría y Trazabilidad")
        st.write("El módulo de auditoría es la herramienta de inteligencia de negocio (BI) interna del municipio. Registra automáticamente cada cambio de estado en la vida de un reclamo vecinal, facilitando el monitoreo operativo, control de plazos y auditorías forenses.")
        
        st.markdown("#### Indicadores Clave de Rendimiento (KPIs)")
        
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            st.markdown("""
            <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; font-family: "Inter", sans-serif;'>
                <div style='font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase;'>Total Reclamos</div>
                <div style='font-size: 1.8rem; color: #0F172A; font-weight: 800; margin: 0.2rem 0;'>Volumen Histórico</div>
                <div style='font-size: 0.88rem; color: #475569;'>Conteo acumulado de todas las solicitudes ingresadas en la base de datos municipal.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; font-family: "Inter", sans-serif;'>
                <div style='font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase;'>Promedio de Resolución</div>
                <div style='font-size: 1.8rem; color: #ED1B24; font-weight: 800; margin: 0.2rem 0;'>Tiempo Medio</div>
                <div style='font-size: 0.88rem; color: #475569;'>Diferencia en horas transcurridas desde la fecha de creación hasta el cierre definitivo.</div>
            </div>
            """, unsafe_allow_html=True)

        with col_k2:
            st.markdown("""
            <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; font-family: "Inter", sans-serif;'>
                <div style='font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase;'>Resueltos / Cerrados</div>
                <div style='font-size: 1.8rem; color: #76BC21; font-weight: 800; margin: 0.2rem 0;'>Finalizados</div>
                <div style='font-size: 0.88rem; color: #475569;'>Reclamos que han alcanzado un estado final de cierre (<b>RESUELTO</b> o <b>RECHAZADO</b>).</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; font-family: "Inter", sans-serif;'>
                <div style='font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase;'>Cumplimiento de SLA</div>
                <div style='font-size: 1.8rem; color: #F59E0B; font-weight: 800; margin: 0.2rem 0;'>Efectividad %</div>
                <div style='font-size: 0.88rem; color: #475569;'>Porcentaje de reclamos cerrados dentro del límite de tiempo asignado por su categoría.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🌱 Módulo de Auditoría y Control de Gestión Rural")
        st.write("El panel de control es la herramienta analítica central del sistema. Mide el flujo de solicitudes y el cumplimiento de plazos comprometidos.")
        
        # Fórmulas de auditoría
        st.markdown("#### Métricas Clave y Fórmulas Analíticas")
        st.write("Las métricas agregadas que se visualizan en la interfaz se calculan dinámicamente con las siguientes fórmulas:")
        
        st.latex(r"T_R = \text{FechaResolución} - \text{FechaCreación}")
        st.caption("Fórmula para el tiempo real de resolución de reclamos cerrados.")
        st.latex(r"D_{SLA} = (\text{FechaActual} - \text{FechaCreación}) - \text{SLAHoras}")
        st.caption("Fórmula de desvío. Si es mayor a 0, el caso se clasifica como alerta SLA vencida.")

        st.markdown("#### Reportes de Auditoría Disponibles")
        with st.expander("Ver detalle de reportes analíticos"):
            st.markdown("""
            * **1. Desempeño por Categoría:** Identificación de cuellos de botella por tipo de reclamo y porcentaje de cumplimiento.
            * **2. Cuellos de Botella (Dwell Times):** Mide el tiempo de espera promedio en cada estado (`PENDIENTE`, `EN REVISION`, `EN PROCESO`).
            * **3. Trazabilidad Cronológica:** Historial forense paso a paso por ID de reclamo.
            * **4. Alertas de Desviación:** Lista prioritaria de reclamos vencidos ordenada por prioridad y tiempo de demora.
            * **5. Desempeño de Gestores:** Estadísticas de productividad, resolución y SLA por operador.
            * **6. Simulación/Testing:** Inicializador de transiciones de prueba (borra historial previo e inyecta simulación).
            * **7. Visualización Gráfica:** Gráficos integrados sobre reclamos por paraje, categoría, estados y prioridades.
            """)
            
    with tab2:
        st.markdown("### 🔑 Módulo de Autenticación, Usuarios y Permisos")
        st.write("RuralConecta cuenta con un sistema de acceso diferencial según el perfil del usuario, controlando dinámicamente las secciones visibles en el menú lateral.")
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.markdown("""
            <div style='background-color: #F8FAFC; border-left: 4px solid #2E7D32; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; font-family: "Inter", sans-serif;'>
                <h5 style='color: #1F2937; margin: 0;'>👤 Perfil Ciudadano Rural</h5>
                <p style='color: #4B5563; margin: 5px 0 0 0; font-size: 0.9rem;'>
                    Orientado a los ciudadanos. Permite registrar solicitudes directas y realizar el seguimiento en línea de sus casos presentados mediante la sección 'Mis Reclamos'.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_u2:
            st.markdown("""
            <div style='background-color: #F8FAFC; border-left: 4px solid #E6A15C; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; font-family: "Inter", sans-serif;'>
                <h5 style='color: #1F2937; margin: 0;'>💼 Perfil Gestor / Analista</h5>
                <p style='color: #4B5563; margin: 5px 0 0 0; font-size: 0.9rem;'>
                    Personal de coordinación. Posee acceso al historial global de parajes, cambio de estado de reclamos, emisión de reportes analíticos, y gestión de accesos.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("#### 👤 Gestión de Usuarios (CRUD)")
        st.write("Ubicado en la opción principal del menú lateral cuando no se ha iniciado sesión, o de forma administrativa. Permite realizar las operaciones fundamentales sobre cuentas de acceso:")
        st.markdown("""
        * **Alta de Usuario:** Permite ingresar un nuevo usuario del sistema. Requiere Nombre, Apellido, DNI (sin puntos), CUIL (sin guiones), contraseña y rol. La contraseña se almacena de forma segura usando un hash criptográfico.
        * **Listar Usuarios:** Muestra en una tabla interactiva todos los usuarios registrados indicando su nombre, DNI, CUIL y rol actual.
        * **Baja de Usuario:** Permite borrar permanentemente a un usuario seleccionado de la base de datos.
        * **Modificar Usuario:** Formulario de edición rápida para corregir información o blanquear contraseñas de accesos existentes.
        """)
        
        st.markdown("#### ⚙️ Gestión de Roles y Permisos")
        st.write("Permite la administración de seguridad en tiempo real a través de las siguientes funciones:")
        st.markdown("""
        * **Crear Rol:** Registro de nuevos perfiles de cargos.
        * **Listar Roles y Permisos:** Despliega una vista expandible de los permisos concedidos a cada rol (ej: `VER_HISTORIAL_RECLAMOS`, `GESTIONAR_ROLES_PERMISOS`).
        * **Asignar/Revocar Permiso:** Concede o remueve privilegios de seguridad de forma dinámica. Los cambios impactan de forma inmediata en las secciones del menú lateral de los usuarios.
        """)
        
    with tab3:
        st.markdown("### 📥 Módulo de Registro Inteligente de Solicitudes")
        st.write("Esta sección está diseñada para capturar la solicitud del ciudadano rural e iniciar automáticamente su flujo de atención.")
        
        st.markdown("#### ¿Cómo registrar un caso?")
        st.markdown("""
        1. **Ciudadano Solicitante:** Si el coordinador ingresa la solicitud, selecciona al ciudadano registrado. Si un ciudadano inició sesión, el sistema auto-completa el campo de forma segura.
        2. **Paraje de la Incidencia:** Se debe seleccionar el paraje rural correspondiente para geolocalizar la zona (Centro, Norte, Sur, Este).
        3. **Descripción:** Cuadro de texto libre donde se ingresa la problemática tal como la describe el ciudadano.
        """)
        
        st.markdown("#### 🤖 Procesamiento NLP en Tiempo Real")
        st.write("Al guardar la solicitud, el sistema ejecuta el motor inteligente `analizador.py` que interpreta el texto:")
        
        # Tabla HTML estilizada
        st.markdown("""
        <table style="width:100%; border-collapse: collapse; margin-top: 0.8rem; font-family: 'Inter', sans-serif;">
            <tr style="background-color: #F1F5F9; border-bottom: 2px solid #CBD5E1;">
                <th style="padding: 10px; text-align: left; font-weight: 700; color: #1F2937; width: 30%;">Atributo IA</th>
                <th style="padding: 10px; text-align: left; font-weight: 700; color: #1F2937;">Cómo funciona / Propósito</th>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0;">
                <td style="padding: 10px; font-weight: 600; color: #1F2937;">Clasificación de Área</td>
                <td style="padding: 10px; color: #475569;">Determina automáticamente la categoría (ej. <i>Calles</i>, <i>Alumbrado</i>, <i>Basura</i>) y la subcategoría específica.</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0;">
                <td style="padding: 10px; font-weight: 600; color: #1F2937;">Prioridad Operativa</td>
                <td style="padding: 10px; color: #475569;">Calcula la urgencia técnica (<b>ALTA</b>, <b>MEDIA</b> o <b>BAJA</b>) de acuerdo a las palabras clave detectadas en el reclamo.</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0;">
                <td style="padding: 10px; font-weight: 600; color: #1F2937;">Score de Sentimiento</td>
                <td style="padding: 10px; color: #475569;">Puntaje numérico de 0 a 1 que mide el nivel de malestar o disconformidad expresado por el ciudadano (valores bajos indican enojo/gravedad).</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: 600; color: #1F2937;">Urgencia NLP (Flag)</td>
                <td style="padding: 10px; color: #475569;">Etiqueta booleana (🚨 SÍ / 🟢 NO) que resalta situaciones de riesgo o emergencia rural inminente.</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📝 Respuestas Inmediatas Sugeridas")
        st.write("Para optimizar el servicio de atención, el sistema genera de forma instantánea dos tipos de respuestas en base a la categoría identificada:")
        st.markdown("""
        * **Canal Formal:** Texto redactado de manera institucional, ideal para enviar por correo electrónico o emitir una cédula impresa con el número de gestión único.
        * **Canal Amigable:** Mensaje corto y dinámico (con uso de emojis), optimizado para enviar por WhatsApp o redes sociales para notificar de inmediato al ciudadano sobre el inicio de su trámite.
        """)
        
    with tab4:
        st.markdown("### 📋 Consola de Historial, Gestión y Seguimiento")
        st.write("Esta sección es la bandeja de entrada y control del sistema. La información visible se adapta según el perfil de usuario:")
        st.markdown("""
        * **Vista Ciudadano (Mis Solicitudes):** Bandeja personal. Permite revisar el número de gestión, fecha de creación, categoría y el estado actual de las solicitudes propias.
        * **Vista Gestor (Historial y Gestión):** Consola de administración general. Lista todas las solicitudes de los parajes y habilita los controles operativos.
        """)
        
        st.markdown("#### Filtros Interactivos")
        st.write("Facilitan la búsqueda de expedientes aplicando filtros rápidos por:")
        st.markdown("- **Estado operativo:** Filtrar solicitudes según su etapa actual.")
        st.markdown("- **Paraje:** Segmentar incidentes en parajes geográficos específicos.")
        st.markdown("- **Prioridad:** Centrar la atención en solicitudes con prioridad ALTA, MEDIA o BAJA.")
        
        st.markdown("#### Trazabilidad de Auditoría y Flujo")
        st.write("Al seleccionar una solicitud específica por su Nro de Gestión, se habilitan las herramientas de trazabilidad:")
        
        # Mermaid rendering of flow
        st.markdown("""
        ```mermaid
        graph TD
            A[Ninguno] -->|Ingreso del caso| B(PENDIENTE)
            B -->|Análisis preliminar| C(EN REVISION)
            C -->|Resolución técnica| D(EN PROCESO)
            D -->|Solución efectiva| E(RESUELTO)
            D -->|Caso inválido/duplicado| F(RECHAZADO)
            
            style B fill:#F59E0B,stroke:#D97706,stroke-width:2px,color:#fff
            style C fill:#3B82F6,stroke:#2563EB,stroke-width:2px,color:#fff
            style D fill:#8B5CF6,stroke:#7C3AED,stroke-width:2px,color:#fff
            style E fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
            style F fill:#EF4444,stroke:#DC2626,stroke-width:2px,color:#fff
        ```
        """, unsafe_allow_html=True)
        
        st.markdown("""
        * **Línea de Tiempo de Auditoría:** Muestra cronológicamente cada cambio registrado, indicando la fecha, el cambio de estado (ej: `PENDIENTE` ➡️ `EN PROCESO`), el responsable de la acción y su rol correspondiente.
        * **Actualización Operativa (Solo Gestores):** Permite cambiar el estado de la solicitud. Si se marca como `RESUELTO` o `RECHAZADO`, el sistema guarda automáticamente la fecha de resolución final para los cálculos de SLA.
        * **Eliminación Permanente:** Botón de seguridad ('Zona de Peligro') para depurar registros. Elimina la solicitud y su historial de estados asociado.
        """)
        
    with tab5:
        st.markdown("### 🤖 Reporte Ejecutivo de Gestión con IA (Ollama)")
        st.write("Esta funcionalidad exclusiva para el personal gestor permite redactar un reporte completo y estructurado en segundos utilizando Inteligencia Artificial.")
        
        st.markdown("#### ¿Cómo funciona?")
        st.write("Al ingresar a la sección, el sistema extrae automáticamente la información agregada en tiempo real de la base de datos:")
        st.markdown("""
        - El volumen total de solicitudes activas e históricas.
        - La distribución porcentual de solicitudes por categoría y parajes.
        - El porcentaje de solicitudes clasificadas por su estado operativo y prioridad.
        - El **score de sentimiento promedio** (un indicador del nivel de disconformidad o satisfacción general del ciudadano).
        - La cantidad de casos urgentes identificados automáticamente mediante técnicas NLP.
        """)
        
        st.markdown("#### Análisis y Plan de Acción Operativo")
        st.write("Al presionar **Generar Reporte de Gestión**, la IA de Ollama analiza estos datos para redactar un informe profesional estructurado que incluye:")
        st.markdown("""
        1. **Diagnóstico Operativo:** Resumen ejecutivo de la situación actual y rendimiento de la red de caminos y servicios.
        2. **Causa Raíz:** Análisis de los parajes y categorías con mayor índice de disconformidad y demoras.
        3. **Planes de Acción Rural:** Recomendaciones concretas y priorizadas para reubicar recursos, equipos y mejorar la atención en parajes aislados.
        """)
        
        st.markdown("#### Descarga del Informe")
        st.write("Una vez generado el informe, puede leerse directamente en pantalla con formato Markdown o descargarse en un solo clic como archivo `.txt` mediante el botón **Descargar Reporte en Formato Texto** para ser presentado formalmente a la coordinación general.")
        
    st.markdown("</div>", unsafe_allow_html=True)

elif seccion == "🚪 Cerrar Sesión":
    st.session_state.logged_in = False
    st.session_state.usuario = None
    st.success("Sesión cerrada correctamente.")
    st.rerun()
