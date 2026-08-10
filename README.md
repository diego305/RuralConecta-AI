# 🌾 RuralConecta AI v2.0 - Plataforma Inteligente de Gestión Municipal Rural

**RuralConecta AI** es una solución integral basada en Inteligencia Artificial y Streamlit diseñada para la gestión, seguimiento, auditoría y análisis predicitivo de solicitudes y reclamos vecinales en distritos y parajes rurales.

---

## 🚀 Características Principales

- **📥 Registro Inteligente de Incidencias**: Clasificación automática con NLP, cálculo de score de sentimiento y detección de urgencia.
- **📜 Consola de Historial y Trazabilidad**: Gestión de estados en tiempo real (*PENDIENTE, EN REVISIÓN, EN PROCESO, RESUELTO, RECHAZADO*) con trazabilidad cronológica auditable.
- **💬 RuralBot - Chatbot para Conversar con los Datos**: Exclusivo para el Gestor Municipal. Permite interactuar mediante preguntas en lenguaje natural sobre las 500 solicitudes vecinales, prioridades y parajes.
- **📊 Panel de Auditoría y SLAs**: Métricas de dwell time (tiempos de permanencia), alertas de desviación de SLA y desempeño por categoría y gestor.
- **🤖 Reporte Ejecutivo IA**: Generador de diagnósticos y planes de acción municipales impulsado por IA.
- **📥 Exportación de Datos en CSV**: Descargas completas y filtradas en formato CSV (encoding `utf-8-sig`) optimizadas para Microsoft Excel, PowerBI y Python (exclusivo perfil Analista).

---

## 👥 Roles del Sistema

| Rol | Descripción | Accesos |
|---|---|---|
| **Ciudadano Rural (Vecino)** | Vecinos de la comunidad | Registro de reclamos, seguimiento propio y guías. |
| **De Gestión (Gestor Municipal)** | Equipo operativo y directivo | Chatbot de datos (`RuralBot`), consola de historial, auditoría, reportes IA y gestión de roles. |
| **Analista (Analista Municipal)** | Equipo de analistas de datos | Consola de historial, auditoría, reportes IA y **exportación a CSV de bases completas y trazabilidad**. |

---

## 🛠️ Tecnologías Utilizadas

- **Python 3.11+**
- **Streamlit** (Interfaz Web)
- **SQLite3** (Base de datos transaccional `ruralconecta.db`)
- **Pandas** (Procesamiento de datos y reportes)
- **Ollama / LLMs local** (Integración de IA conversacional)
- **Python-PPTX** (Generación de presentaciones institucionales)

---

## 💻 Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/diego305/RuralConecta-AI.git
   cd RuralConecta-AI
   ```

2. **Crear y activar entorno virtual:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar la aplicación:**
   ```bash
   streamlit run app.py
   ```

---

## 📄 Licencia

Desarrollado para la optimización de la gestión pública municipal en zonas rurales. Todos los derechos reservados.
