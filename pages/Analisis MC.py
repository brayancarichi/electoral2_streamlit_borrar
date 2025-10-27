import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configurar la página
st.set_page_config(
    page_title="Análisis Movimiento Ciudadano",
    page_icon="🔍",
    layout="wide"
)

# CSS personalizado para MC
st.markdown("""
<style>
    .mc-header {
        background: linear-gradient(135deg, #F58220, #FFA500);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-mc {
        background-color: #FFF5E6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #F58220;
        margin-bottom: 1rem;
    }
    .conflict-card {
        background-color: #FFE8D6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF6B00;
        margin-bottom: 1rem;
    }
    .opportunity-card {
        background-color: #E6F7FF;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1890FF;
        margin-bottom: 1rem;
    }
    .strategy-card {
        background-color: #F0F8FF;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #1E90FF;
        margin-bottom: 1rem;
    }
    .formula-box {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
        font-family: monospace;
    }
    .tab-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Datos geoespaciales básicos para Nuevo León (coordenadas aproximadas de municipios)
MUNICIPIOS_NL = {
    "Monterrey": {"lat": 25.6866, "lon": -100.3161},
    "Guadalupe": {"lat": 25.6770, "lon": -100.2595},
    "San Nicolás de los Garza": {"lat": 25.7417, "lon": -100.3021},
    "San Pedro Garza García": {"lat": 25.6576, "lon": -100.4025},
    "Santa Catarina": {"lat": 25.6734, "lon": -100.4600},
    "Apodaca": {"lat": 25.7819, "lon": -100.1887},
    "Escobedo": {"lat": 25.7953, "lon": -100.1417},
    "García": {"lat": 25.8123, "lon": -100.5980},
    "Juárez": {"lat": 25.6476, "lon": -100.0951},
    "Santiago": {"lat": 25.4256, "lon": -100.1522},
    "Allende": {"lat": 25.2764, "lon": -100.0144},
    "Montemorelos": {"lat": 25.1892, "lon": -99.8236},
    "Linares": {"lat": 24.8578, "lon": -99.5678},
    "Hualahuises": {"lat": 24.8844, "lon": -99.6611},
    "Rayones": {"lat": 25.0178, "lon": -100.0739},
    "Doctor Arroyo": {"lat": 23.6714, "lon": -100.1833},
    "Aramberri": {"lat": 24.0997, "lon": -99.8153},
    "Galeana": {"lat": 24.8261, "lon": -100.0669},
    "Iturbide": {"lat": 24.7250, "lon": -99.9056},
    "Cadereyta Jiménez": {"lat": 25.5833, "lon": -100.0000},
    "El Carmen": {"lat": 25.9361, "lon": -100.3639},
    "Abasolo": {"lat": 25.9450, "lon": -100.3992},
    "Higueras": {"lat": 25.9611, "lon": -100.0167},
    "Salinas Victoria": {"lat": 26.0417, "lon": -100.2917},
    "Ciénega de Flores": {"lat": 25.9542, "lon": -100.1833},
    "Villaldama": {"lat": 26.5042, "lon": -100.4375},
    "Sabinas Hidalgo": {"lat": 26.5083, "lon": -100.1819},
    "Vallecillo": {"lat": 26.6583, "lon": -99.9875},
    "Parás": {"lat": 26.5000, "lon": -99.5167},
    "Agualeguas": {"lat": 26.3125, "lon": -99.5417},
    "Mier y Noriega": {"lat": 23.4167, "lon": -100.1167},
    "Doctor Coss": {"lat": 25.9250, "lon": -99.1417},
    "General Bravo": {"lat": 25.7917, "lon": -99.1750},
    "General Terán": {"lat": 25.2583, "lon": -99.6833},
    "General Zuazua": {"lat": 25.8958, "lon": -100.1083},
    "Marín": {"lat": 25.8792, "lon": -100.0292},
    "Melchor Ocampo": {"lat": 25.0458, "lon": -100.0958},
    "Los Ramones": {"lat": 25.6972, "lon": -99.6250},
    "Los Herreras": {"lat": 25.9069, "lon": -99.4042},
    "Los Aldamas": {"lat": 25.6000, "lon": -99.1167},
    "General Escobedo": {"lat": 25.7953, "lon": -100.1417},
    "Pesquería": {"lat": 25.7850, "lon": -100.0500},
    "China": {"lat": 25.7000, "lon": -99.2333},
    "Anáhuac": {"lat": 27.2417, "lon": -100.1333},
    "Lampazos de Naranjo": {"lat": 27.0250, "lon": -100.5083},
    "Bustamante": {"lat": 26.5333, "lon": -100.5000},
    "Cerralvo": {"lat": 26.0875, "lon": -99.6292},
    "Doctor González": {"lat": 25.8583, "lon": -99.9417},
    "Hidalgo": {"lat": 25.8569, "lon": -100.4333},
    "Mina": {"lat": 26.0000, "lon": -100.5333}
}

# Coordenadas aproximadas para distritos de diputaciones (centros de áreas metropolitanas)
DISTRITOS_DIPUTACIONES = {
    "1. Monterrey": {"lat": 25.6866, "lon": -100.3161},
    "2. Monterrey": {"lat": 25.6700, "lon": -100.3500},
    "3. Monterrey": {"lat": 25.6500, "lon": -100.2900},
    "4. Salinas Victoria": {"lat": 26.0417, "lon": -100.2917},
    "5. Apodaca": {"lat": 25.7819, "lon": -100.1887},
    "6. Monterrey": {"lat": 25.7200, "lon": -100.3100},
    "7. Apodaca": {"lat": 25.7900, "lon": -100.2000},
    "8. Monterrey": {"lat": 25.6800, "lon": -100.3300},
    "9. San Nicolás de los Garza": {"lat": 25.7417, "lon": -100.3021},
    "10. San Nicolás de los Garza": {"lat": 25.7500, "lon": -100.2800},
    "11. Pesquería": {"lat": 25.7850, "lon": -100.0500},
    "12. García": {"lat": 25.8123, "lon": -100.5980},
    "13. Guadalupe": {"lat": 25.6770, "lon": -100.2595},
    "14. Guadalupe": {"lat": 25.6900, "lon": -100.2400},
    "15. Guadalupe": {"lat": 25.6650, "lon": -100.2700},
    "16. Apodaca": {"lat": 25.7700, "lon": -100.1700},
    "17. Gral. Escobedo": {"lat": 25.7953, "lon": -100.1417},
    "18. San Pedro Garza García": {"lat": 25.6576, "lon": -100.4025},
    "19. Santa Catarina": {"lat": 25.6734, "lon": -100.4600},
    "20. García": {"lat": 25.8200, "lon": -100.5800},
    "21. Ciénega de Flores": {"lat": 25.9542, "lon": -100.1833},
    "22. Juárez": {"lat": 25.6476, "lon": -100.0951},
    "23. Juárez": {"lat": 25.6300, "lon": -100.1200},
    "24. Linares": {"lat": 24.8578, "lon": -99.5678},
    "25. Gral. Escobedo": {"lat": 25.8100, "lon": -100.1500},
    "26. Cadereyta Jiménez": {"lat": 25.5833, "lon": -100.0000}
}


class AnalisisMovimientoCiudadano:
    def __init__(self):
        self.dbs = {
            '2021': 'elecciones_nl_2021.db',
            '2024': 'elecciones_nl_2024.db'
        }

    def conectar(self, año):
        return sqlite3.connect(self.dbs[año])

    def obtener_nombre_mc(self, año):
        return 'Movimiento Ciudadano' if año == '2021' else 'MC'

    def obtener_ganadores(self, año, tipo_eleccion):
        """Obtener ganadores por división territorial"""
        nombre_mc = self.obtener_nombre_mc(año)
        with self.conectar(año) as conn:
            query = f"""
            WITH ranked_candidates AS (
                SELECT 
                    division_territorial,
                    nombre_candidato,
                    partido_ci,
                    numero_de_votos,
                    ROW_NUMBER() OVER (PARTITION BY division_territorial ORDER BY numero_de_votos DESC) as rank
                FROM resultados_electorales 
                WHERE tipo_eleccion = ?
            )
            SELECT division_territorial, nombre_candidato, partido_ci, numero_de_votos
            FROM ranked_candidates 
            WHERE rank = 1;
            """
            ganadores = pd.read_sql_query(query, conn, params=(tipo_eleccion,))

            # Filtrar solo los ganadores de MC con el nombre correcto
            mc_ganadores = ganadores[ganadores['partido_ci'] == nombre_mc]
            return mc_ganadores

    def obtener_todos_ganadores(self, año, tipo_eleccion):
        """Obtener todos los ganadores (sin filtrar por partido)"""
        with self.conectar(año) as conn:
            query = f"""
            WITH ranked_candidates AS (
                SELECT 
                    division_territorial,
                    nombre_candidato,
                    partido_ci,
                    numero_de_votos,
                    ROW_NUMBER() OVER (PARTITION BY division_territorial ORDER BY numero_de_votos DESC) as rank
                FROM resultados_electorales 
                WHERE tipo_eleccion = ?
            )
            SELECT division_territorial, nombre_candidato, partido_ci, numero_de_votos
            FROM ranked_candidates 
            WHERE rank = 1;
            """
            return pd.read_sql_query(query, conn, params=(tipo_eleccion,))

    def obtener_datos_mc(self, año, tipo_eleccion):
        """Obtener todos los datos de MC para un tipo de elección"""
        nombre_mc = self.obtener_nombre_mc(año)
        with self.conectar(año) as conn:
            query = """
            SELECT * FROM resultados_electorales 
            WHERE tipo_eleccion = ? AND partido_ci = ?
            ORDER BY numero_de_votos DESC;
            """
            return pd.read_sql_query(query, conn, params=(tipo_eleccion, nombre_mc))

    def analizar_transferencia_votos(self, año):
        """Analizar patrones de transferencia de votos municipal-diputacional"""
        nombre_mc = self.obtener_nombre_mc(año)

        # Obtener datos de ambos tipos de elección
        datos_municipales = self.obtener_datos_mc(año, 'MUNICIPAL')
        datos_diputados = self.obtener_datos_mc(año, 'DIPUTADO')

        # Crear análisis comparativo por municipio
        analisis_transferencia = []

        for _, candidato_mun in datos_municipales.iterrows():
            municipio = candidato_mun['division_territorial']
            votos_mun = candidato_mun['numero_de_votos']

            # Buscar datos de diputados para la misma área
            datos_dip_area = datos_diputados[datos_diputados['division_territorial'].str.contains(municipio[:10])]
            if not datos_dip_area.empty:
                votos_dip = datos_dip_area['numero_de_votos'].iloc[0]
                diferencia = votos_dip - votos_mun
                porcentaje_transferencia = (votos_dip / votos_mun * 100) if votos_mun > 0 else 0

                analisis_transferencia.append({
                    'municipio': municipio,
                    'votos_municipales': votos_mun,
                    'votos_diputacionales': votos_dip,
                    'diferencia': diferencia,
                    'porcentaje_transferencia': porcentaje_transferencia,
                    'tipo_transferencia': 'Positiva' if diferencia > 0 else 'Negativa'
                })

        return pd.DataFrame(analisis_transferencia)

    def identificar_municipios_clave(self, año):
        """Identificar municipios clave para crecimiento estratégico"""
        nombre_mc = self.obtener_nombre_mc(año)

        # Obtener todos los datos municipales
        datos_municipales = self.obtener_datos_mc(año, 'MUNICIPAL')
        ganadores_municipio = self.obtener_todos_ganadores(año, 'MUNICIPAL')

        analisis_municipios = []

        for municipio in datos_municipales['division_territorial'].unique():
            datos_mun = datos_municipales[datos_municipales['division_territorial'] == municipio]
            if len(datos_mun) > 0:
                votos_mc = datos_mun['numero_de_votos'].iloc[0]

                # Obtener total de votos del municipio
                with self.conectar(año) as conn:
                    query = "SELECT SUM(numero_de_votos) as total_votos FROM resultados_electorales WHERE tipo_eleccion = 'MUNICIPAL' AND division_territorial = ?"
                    total_votos_df = pd.read_sql_query(query, conn, params=(municipio,))
                    total_votos = total_votos_df['total_votos'].iloc[0] if not total_votos_df.empty else 0

                # FÓRMULA: Porcentaje de votos de MC
                porcentaje = (votos_mc / total_votos * 100) if total_votos > 0 else 0

                # Obtener ganador del municipio
                ganador_mun = ganadores_municipio[ganadores_municipio['division_territorial'] == municipio]
                ganador = ganador_mun['partido_ci'].iloc[0] if not ganador_mun.empty else "Desconocido"

                # Clasificar municipio usando umbrales estratégicos
                if ganador == nombre_mc:
                    categoria = "Victoria"
                    prioridad = "Consolidar"
                elif porcentaje >= 40:
                    categoria = "Alta Oportunidad"
                    prioridad = "Alta"
                elif porcentaje >= 25:
                    categoria = "Oportunidad Media"
                    prioridad = "Media"
                elif porcentaje >= 15:
                    categoria = "Oportunidad Baja"
                    prioridad = "Baja"
                else:
                    categoria = "Base Débil"
                    prioridad = "Expandir Base"

                analisis_municipios.append({
                    'division': municipio,
                    'votos_mc': votos_mc,
                    'total_votos': total_votos,
                    'porcentaje_mc': porcentaje,
                    'ganador': ganador,
                    'mc_es_ganador': ganador == nombre_mc,
                    'categoria': categoria,
                    'prioridad': prioridad,
                    'tipo': 'Municipio'
                })

        return pd.DataFrame(analisis_municipios)

    def identificar_distritos_clave(self, año):
        """Identificar distritos clave para diputaciones"""
        nombre_mc = self.obtener_nombre_mc(año)

        # Obtener todos los datos de diputados
        datos_diputados = self.obtener_datos_mc(año, 'DIPUTADO')
        ganadores_diputados = self.obtener_todos_ganadores(año, 'DIPUTADO')

        analisis_distritos = []

        for distrito in datos_diputados['division_territorial'].unique():
            datos_dip = datos_diputados[datos_diputados['division_territorial'] == distrito]
            if len(datos_dip) > 0:
                votos_mc = datos_dip['numero_de_votos'].iloc[0]

                # Obtener total de votos del distrito
                with self.conectar(año) as conn:
                    query = "SELECT SUM(numero_de_votos) as total_votos FROM resultados_electorales WHERE tipo_eleccion = 'DIPUTADO' AND division_territorial = ?"
                    total_votos_df = pd.read_sql_query(query, conn, params=(distrito,))
                    total_votos = total_votos_df['total_votos'].iloc[0] if not total_votos_df.empty else 0

                # FÓRMULA: Porcentaje de votos de MC
                porcentaje = (votos_mc / total_votos * 100) if total_votos > 0 else 0

                # Obtener ganador del distrito
                ganador_dip = ganadores_diputados[ganadores_diputados['division_territorial'] == distrito]
                ganador = ganador_dip['partido_ci'].iloc[0] if not ganador_dip.empty else "Desconocido"

                # Clasificar distrito usando umbrales estratégicos
                if ganador == nombre_mc:
                    categoria = "Victoria"
                    prioridad = "Consolidar"
                elif porcentaje >= 40:
                    categoria = "Alta Oportunidad"
                    prioridad = "Alta"
                elif porcentaje >= 25:
                    categoria = "Oportunidad Media"
                    prioridad = "Media"
                elif porcentaje >= 15:
                    categoria = "Oportunidad Baja"
                    prioridad = "Baja"
                else:
                    categoria = "Base Débil"
                    prioridad = "Expandir Base"

                analisis_distritos.append({
                    'division': distrito,
                    'votos_mc': votos_mc,
                    'total_votos': total_votos,
                    'porcentaje_mc': porcentaje,
                    'ganador': ganador,
                    'mc_es_ganador': ganador == nombre_mc,
                    'categoria': categoria,
                    'prioridad': prioridad,
                    'tipo': 'Distrito'
                })

        return pd.DataFrame(analisis_distritos)


# Inicializar análisis
analisis_mc = AnalisisMovimientoCiudadano()

# HEADER PRINCIPAL
st.markdown("""
<div class="mc-header">
    <h1>🔍 ANÁLISIS ESTRATÉGICO AVANZADO</h1>
    <h2>MOVIMIENTO CIUDADANO (2021) - MC (2024)</h2>
    <p>Análisis de transferencia de votos y divisiones clave (Municipios y Distritos de Diputaciones)</p>
</div>
""", unsafe_allow_html=True)

# SELECTOR DE TIPO DE ANÁLISIS
tipo_analisis = st.radio(
    "**Selecciona el tipo de análisis:**",
    ['📊 Transferencia de Votos', '🎯 Municipios Clave', '🏛️ Distritos de Diputaciones'],
    horizontal=True
)

if tipo_analisis == '📊 Transferencia de Votos':
    st.subheader("📊 ANÁLISIS DE TRANSFERENCIA DE VOTOS")

    año_transferencia = st.selectbox("Selecciona el año:", ['2021', '2024'])

    # EXPLICACIÓN DE FÓRMULAS
    with st.expander("🧮 **VER FÓRMULAS MATEMÁTICAS UTILIZADAS**", expanded=True):
        st.markdown("""
        ### Fórmulas de Transferencia de Votos

        **1. Porcentaje de Transferencia:**
        """)
        st.markdown(
            '<div class="formula-box">Porcentaje_Transferencia = (Votos_Diputacionales / Votos_Municipales) × 100</div>',
            unsafe_allow_html=True)
        st.markdown("""
        Donde:
        - **Votos_Municipales** = Número de votos obtenidos por MC en elección municipal
        - **Votos_Diputacionales** = Número de votos obtenidos por MC en elección de diputados del mismo territorio

        **2. Diferencia de Votos:**
        """)
        st.markdown('<div class="formula-box">Diferencia = Votos_Diputacionales - Votos_Municipales</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        **3. Clasificación de Transferencia:**
        - **Transferencia Positiva**: Diferencia > 0 (MC obtiene más votos para diputados que para municipio)
        - **Transferencia Negativa**: Diferencia < 0 (MC obtiene menos votos para diputados que para municipio)

        **Interpretación:**
        - **>100%**: MC tiene mejor desempeño en elecciones de diputados
        - **100%**: Desempeño igual en ambos tipos de elección
        - **<100%**: MC tiene mejor desempeño en elecciones municipales
        """)

    with st.spinner("Analizando patrones de transferencia..."):
        transferencia = analisis_mc.analizar_transferencia_votos(año_transferencia)

    if not transferencia.empty:
        # MÉTRICAS DE TRANSFERENCIA
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            transferencia_positiva = len(transferencia[transferencia['tipo_transferencia'] == 'Positiva'])
            st.metric("Transferencia Positiva", transferencia_positiva)

        with col2:
            transferencia_negativa = len(transferencia[transferencia['tipo_transferencia'] == 'Negativa'])
            st.metric("Transferencia Negativa", transferencia_negativa)

        with col3:
            promedio_transferencia = transferencia['porcentaje_transferencia'].mean()
            st.metric("Transferencia Promedio", f"{promedio_transferencia:.1f}%")

        with col4:
            eficiencia_global = (transferencia_positiva / len(transferencia)) * 100 if len(transferencia) > 0 else 0
            st.metric("Eficiencia Global", f"{eficiencia_global:.1f}%")

        # GRÁFICO DE TRANSFERENCIA
        st.subheader("🔄 Patrones de Transferencia Municipal-Diputacional")

        fig_transferencia = px.scatter(
            transferencia,
            x='votos_municipales',
            y='votos_diputacionales',
            color='tipo_transferencia',
            size='porcentaje_transferencia',
            hover_name='municipio',
            title=f'Transferencia de Votos: Municipal vs Diputacional ({año_transferencia})',
            color_discrete_map={
                'Positiva': '#00C851',
                'Negativa': '#FF4444'
            },
            labels={
                'votos_municipales': 'Votos Municipales',
                'votos_diputacionales': 'Votos Diputacionales',
                'tipo_transferencia': 'Tipo de Transferencia'
            }
        )

        # Línea de referencia (y = x)
        max_votos = max(transferencia[['votos_municipales', 'votos_diputacionales']].max())
        fig_transferencia.add_trace(
            go.Scatter(
                x=[0, max_votos],
                y=[0, max_votos],
                mode='lines',
                line=dict(dash='dash', color='gray'),
                name='Línea de Referencia (igualdad)'
            )
        )

        st.plotly_chart(fig_transferencia, use_container_width=True)

        # ANÁLISIS DETALLADO
        st.subheader("📋 Análisis Detallado por Municipio")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**🏆 Mejor Transferencia Positiva:**")
            top_positivos = transferencia.nlargest(5, 'porcentaje_transferencia')
            for _, municipio in top_positivos.iterrows():
                st.write(f"• **{municipio['municipio']}**: {municipio['porcentaje_transferencia']:.1f}%")
                st.caption(
                    f"  Municipal: {municipio['votos_municipales']:,} | Diputacional: {municipio['votos_diputacionales']:,}")

        with col2:
            st.write("**⚠️ Mayor Transferencia Negativa:**")
            top_negativos = transferencia.nsmallest(5, 'porcentaje_transferencia')
            for _, municipio in top_negativos.iterrows():
                st.write(f"• **{municipio['municipio']}**: {municipio['porcentaje_transferencia']:.1f}%")
                st.caption(
                    f"  Municipal: {municipio['votos_municipales']:,} | Diputacional: {municipio['votos_diputacionales']:,}")

        # TABLA COMPLETA
        with st.expander("📊 Ver tabla completa de transferencia"):
            st.dataframe(
                transferencia.sort_values('porcentaje_transferencia', ascending=False),
                use_container_width=True,
                height=400
            )

    else:
        st.info("No hay datos suficientes para análisis de transferencia")

elif tipo_analisis == '🎯 Municipios Clave':
    st.subheader("🎯 IDENTIFICACIÓN DE MUNICIPIOS CLAVE")

    año_municipio = st.selectbox("Selecciona el año:", ['2021', '2024'], key="municipio_año")

    # EXPLICACIÓN DETALLADA DE LAS FÓRMULAS Y MÉTRICAS
    with st.expander("🧮 **VER METODOLOGÍA Y FÓRMULAS COMPLETAS**", expanded=True):
        st.markdown("""
        ## 📊 Metodología de Clasificación de Municipios

        ### 1. Fórmula Base: Porcentaje de Votos de MC
        """)
        st.markdown('<div class="formula-box">Porcentaje_MC = (Votos_MC / Total_Votos_Municipio) × 100</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        Donde:
        - **Votos_MC** = Número de votos obtenidos por Movimiento Ciudadano en el municipio
        - **Total_Votos_Municipio** = Suma total de todos los votos en elecciones municipales

        ### 2. Umbrales de Clasificación Estratégica

        **🏆 VICTORIA (Consolidar)**
        - **Condición**: MC es el partido ganador en el municipio
        - **Fórmula**: Ganador = 'Movimiento Ciudadano' (2021) o 'MC' (2024)
        - **Estrategia**: Mantener y fortalecer la base electoral existente

        **🎯 ALTA OPORTUNIDAD (Prioridad Alta)**
        - **Condición**: Porcentaje_MC ≥ 40%
        - **Fórmula**: (Votos_MC / Total_Votos) × 100 ≥ 40
        - **Interpretación**: MC tiene alta penetración electoral, alta probabilidad de ganar en próximas elecciones
        - **Estrategia**: Inversión intensiva en campaña

        **📈 OPORTUNIDAD MEDIA (Prioridad Media)**
        - **Condición**: 25% ≤ Porcentaje_MC < 40%
        - **Fórmula**: 25 ≤ (Votos_MC / Total_Votos) × 100 < 40
        - **Interpretación**: MC tiene presencia significativa pero necesita trabajo adicional
        - **Estrategia**: Campañas focalizadas y fortalecimiento de estructura

        **📊 OPORTUNIDAD BAJA (Prioridad Baja)**
        - **Condición**: 15% ≤ Porcentaje_MC < 25%
        - **Fórmula**: 15 ≤ (Votos_MC / Total_Votos) × 100 < 25
        - **Interpretación**: MC tiene base electoral limitada, requiere desarrollo de base
        - **Estrategia**: Trabajo de base y construcción de presencia

        **🔍 BASE DÉBIL (Expandir Base)**
        - **Condición**: Porcentaje_MC < 15%
        - **Fórmula**: (Votos_MC / Total_Votos) × 100 < 15
        - **Interpretación**: MC tiene mínima presencia electoral
        - **Estrategia**: Desarrollo de estructura y penetración inicial
        """)

    with st.spinner("Identificando municipios estratégicos..."):
        municipios_clave = analisis_mc.identificar_municipios_clave(año_municipio)

    if not municipios_clave.empty and 'categoria' in municipios_clave.columns:
        # MÉTRICAS RESUMEN
        st.subheader("📈 RESUMEN ESTRATÉGICO - MUNICIPIOS")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_municipios = len(municipios_clave)
            st.metric("Total Municipios", total_municipios)

        with col2:
            victorias = len(municipios_clave[municipios_clave['categoria'] == 'Victoria'])
            st.metric("Municipios Ganados", victorias)

        with col3:
            alta_oportunidad = len(municipios_clave[municipios_clave['categoria'] == 'Alta Oportunidad'])
            st.metric("Alta Oportunidad", alta_oportunidad)

        with col4:
            porcentaje_cobertura = (victorias / total_municipios * 100) if total_municipios > 0 else 0
            st.metric("Cobertura Actual", f"{porcentaje_cobertura:.1f}%")

        # RESUMEN DE CATEGORÍAS
        st.subheader("📊 Distribución de Municipios por Categoría")

        resumen_categorias = municipios_clave['categoria'].value_counts().reset_index()
        resumen_categorias.columns = ['Categoría', 'Cantidad']

        fig_categorias = px.pie(
            resumen_categorias,
            values='Cantidad',
            names='Categoría',
            title=f'Distribución de Municipios por Categoría Estratégica ({año_municipio})',
            color='Categoría',
            color_discrete_map={
                'Victoria': '#F58220',
                'Alta Oportunidad': '#00C851',
                'Oportunidad Media': '#FFC107',
                'Oportunidad Baja': '#FF9800',
                'Base Débil': '#CCCCCC'
            }
        )
        st.plotly_chart(fig_categorias, use_container_width=True)

        # MAPA DE PRIORIDADES
        st.subheader("🗺️ Mapa de Prioridades Estratégicas - Municipios")

        # Agregar coordenadas a los datos
        municipios_con_coords = []
        for _, municipio in municipios_clave.iterrows():
            nombre_mun = municipio['division']
            if nombre_mun in MUNICIPIOS_NL:
                coords = MUNICIPIOS_NL[nombre_mun]
                municipios_con_coords.append({
                    'division': nombre_mun,
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'categoria': municipio['categoria'],
                    'prioridad': municipio['prioridad'],
                    'porcentaje_mc': municipio['porcentaje_mc'],
                    'votos_mc': municipio['votos_mc'],
                    'total_votos': municipio['total_votos']
                })

        if municipios_con_coords:
            mapa_prioridades = pd.DataFrame(municipios_con_coords)

            fig_mapa_prioridades = px.scatter_mapbox(
                mapa_prioridades,
                lat="lat",
                lon="lon",
                hover_name="division",
                hover_data={
                    "categoria": True,
                    "prioridad": True,
                    "porcentaje_mc": ":.1f",
                    "votos_mc": True,
                    "total_votos": True,
                    "lat": False,
                    "lon": False
                },
                color="prioridad",
                color_discrete_map={
                    "Alta": "#FF4444",
                    "Media": "#FFC107",
                    "Baja": "#FF9800",
                    "Consolidar": "#F58220",
                    "Expandir Base": "#CCCCCC"
                },
                size="porcentaje_mc",
                size_max=20,
                zoom=8,
                height=600,
                title=f"Mapa de Prioridades Estratégicas - Municipios ({año_municipio})",
                labels={
                    "porcentaje_mc": "Porcentaje MC (%)",
                    "prioridad": "Prioridad Estratégica"
                }
            )

            fig_mapa_prioridades.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 30, "l": 0, "b": 0}
            )

            st.plotly_chart(fig_mapa_prioridades, use_container_width=True)

        # TABLAS ESTRATÉGICAS
        st.subheader("📋 ANÁLISIS ESTRATÉGICO POR CATEGORÍA - MUNICIPIOS")

        tab1, tab2, tab3, tab4 = st.tabs(
            ["🎯 Alta Oportunidad", "📈 Oportunidad Media", "🏆 Victorias", "📊 Todas las Categorías"])

        with tab1:
            alta_oportunidad = municipios_clave[municipios_clave['categoria'] == 'Alta Oportunidad']
            if not alta_oportunidad.empty:
                st.write("**🎯 MUNICIPIOS DE ALTA OPORTUNIDAD**")
                st.write("*(Porcentaje MC ≥ 40% - Alta probabilidad de ganar)*")
                st.dataframe(
                    alta_oportunidad[['division', 'votos_mc', 'total_votos', 'ganador']].sort_values(
                        'votos_mc', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No hay municipios en categoría de Alta Oportunidad")

        with tab2:
            media_oportunidad = municipios_clave[municipios_clave['categoria'] == 'Oportunidad Media']
            if not media_oportunidad.empty:
                st.write("**📈 MUNICIPIOS DE OPORTUNIDAD MEDIA**")
                st.write("*(25% ≤ Porcentaje MC < 40% - Requieren trabajo adicional)*")
                st.dataframe(
                    media_oportunidad[['division', 'votos_mc', 'total_votos', 'ganador']].sort_values(
                        'votos_mc', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No hay municipios en categoría de Oportunidad Media")

        with tab3:
            victorias = municipios_clave[municipios_clave['categoria'] == 'Victoria']
            if not victorias.empty:
                st.write("**🏆 MUNICIPIOS GANADOS**")
                st.write("*(MC es el partido ganador - Estrategia de consolidación)*")
                st.dataframe(
                    victorias[['division', 'votos_mc', 'total_votos']].sort_values('votos_mc', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No hay municipios ganados")

        with tab4:
            st.write("**📊 TODOS LOS MUNICIPIOS POR CATEGORÍA**")
            st.dataframe(
                municipios_clave[['division', 'categoria', 'prioridad', 'votos_mc', 'total_votos', 'ganador']].sort_values(['prioridad', 'votos_mc'], ascending=[True, False]),
                use_container_width=True,
                height=400
            )
    else:
        st.error(
            "No se pudieron cargar los datos de municipios clave. Verifique que la base de datos contenga información de elecciones municipales.")

else:  # Distritos de Diputaciones
    st.subheader("🏛️ ANÁLISIS DE DISTRITOS DE DIPUTACIONES")

    año_distrito = st.selectbox("Selecciona el año:", ['2021', '2024'], key="distrito_año")

    # EXPLICACIÓN DETALLADA DE LAS FÓRMULAS Y MÉTRICAS
    with st.expander("🧮 **VER METODOLOGÍA Y FÓRMULAS COMPLETAS**", expanded=True):
        st.markdown("""
        ## 📊 Metodología de Clasificación de Distritos de Diputaciones

        ### 1. Fórmula Base: Porcentaje de Votos de MC
        """)
        st.markdown('<div class="formula-box">Porcentaje_MC = (Votos_MC / Total_Votos_Distrito) × 100</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        Donde:
        - **Votos_MC** = Número de votos obtenidos por Movimiento Ciudadano en el distrito
        - **Total_Votos_Distrito** = Suma total de todos los votos en elecciones de diputados del distrito

        ### 2. Umbrales de Clasificación Estratégica

        **🏆 VICTORIA (Consolidar)**
        - **Condición**: MC es el partido ganador en el distrito
        - **Fórmula**: Ganador = 'Movimiento Ciudadano' (2021) o 'MC' (2024)
        - **Estrategia**: Mantener y fortalecer la base electoral existente

        **🎯 ALTA OPORTUNIDAD (Prioridad Alta)**
        - **Condición**: Porcentaje_MC ≥ 40%
        - **Fórmula**: (Votos_MC / Total_Votos) × 100 ≥ 40
        - **Interpretación**: MC tiene alta penetración electoral, alta probabilidad de ganar en próximas elecciones
        - **Estrategia**: Inversión intensiva en campaña

        **📈 OPORTUNIDAD MEDIA (Prioridad Media)**
        - **Condición**: 25% ≤ Porcentaje_MC < 40%
        - **Fórmula**: 25 ≤ (Votos_MC / Total_Votos) × 100 < 40
        - **Interpretación**: MC tiene presencia significativa pero necesita trabajo adicional
        - **Estrategia**: Campañas focalizadas y fortalecimiento de estructura

        **📊 OPORTUNIDAD BAJA (Prioridad Baja)**
        - **Condición**: 15% ≤ Porcentaje_MC < 25%
        - **Fórmula**: 15 ≤ (Votos_MC / Total_Votos) × 100 < 25
        - **Interpretación**: MC tiene base electoral limitada, requiere desarrollo de base
        - **Estrategia**: Trabajo de base y construcción de presencia

        **🔍 BASE DÉBIL (Expandir Base)**
        - **Condición**: Porcentaje_MC < 15%
        - **Fórmula**: (Votos_MC / Total_Votos) × 100 < 15
        - **Interpretación**: MC tiene mínima presencia electoral
        - **Estrategia**: Desarrollo de estructura y penetración inicial
        """)

    with st.spinner("Analizando distritos de diputaciones..."):
        distritos_clave = analisis_mc.identificar_distritos_clave(año_distrito)

    if not distritos_clave.empty and 'categoria' in distritos_clave.columns:
        # MÉTRICAS RESUMEN
        st.subheader("📈 RESUMEN ESTRATÉGICO - DISTRITOS DE DIPUTACIONES")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_distritos = len(distritos_clave)
            st.metric("Total Distritos", total_distritos)

        with col2:
            victorias = len(distritos_clave[distritos_clave['categoria'] == 'Victoria'])
            st.metric("Distritos Ganados", victorias)

        with col3:
            alta_oportunidad = len(distritos_clave[distritos_clave['categoria'] == 'Alta Oportunidad'])
            st.metric("Alta Oportunidad", alta_oportunidad)

        with col4:
            porcentaje_cobertura = (victorias / total_distritos * 100) if total_distritos > 0 else 0
            st.metric("Cobertura Actual", f"{porcentaje_cobertura:.1f}%")

        # RESUMEN DE CATEGORÍAS
        st.subheader("📊 Distribución de Distritos por Categoría")

        resumen_categorias = distritos_clave['categoria'].value_counts().reset_index()
        resumen_categorias.columns = ['Categoría', 'Cantidad']

        fig_categorias = px.pie(
            resumen_categorias,
            values='Cantidad',
            names='Categoría',
            title=f'Distribución de Distritos por Categoría Estratégica ({año_distrito})',
            color='Categoría',
            color_discrete_map={
                'Victoria': '#F58220',
                'Alta Oportunidad': '#00C851',
                'Oportunidad Media': '#FFC107',
                'Oportunidad Baja': '#FF9800',
                'Base Débil': '#CCCCCC'
            }
        )
        st.plotly_chart(fig_categorias, use_container_width=True)

        # MAPA DE PRIORIDADES
        st.subheader("🗺️ Mapa de Prioridades Estratégicas - Distritos de Diputaciones")

        # Agregar coordenadas a los datos
        distritos_con_coords = []
        for _, distrito in distritos_clave.iterrows():
            nombre_dist = distrito['division']
            if nombre_dist in DISTRITOS_DIPUTACIONES:
                coords = DISTRITOS_DIPUTACIONES[nombre_dist]
                distritos_con_coords.append({
                    'division': nombre_dist,
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'categoria': distrito['categoria'],
                    'prioridad': distrito['prioridad'],
                    'porcentaje_mc': distrito['porcentaje_mc'],
                    'votos_mc': distrito['votos_mc'],
                    'total_votos': distrito['total_votos']
                })

        if distritos_con_coords:
            mapa_prioridades = pd.DataFrame(distritos_con_coords)

            fig_mapa_prioridades = px.scatter_mapbox(
                mapa_prioridades,
                lat="lat",
                lon="lon",
                hover_name="division",
                hover_data={
                    "categoria": True,
                    "prioridad": True,
                    "porcentaje_mc": ":.1f",
                    "votos_mc": True,
                    "total_votos": True,
                    "lat": False,
                    "lon": False
                },
                color="prioridad",
                color_discrete_map={
                    "Alta": "#FF4444",
                    "Media": "#FFC107",
                    "Baja": "#FF9800",
                    "Consolidar": "#F58220",
                    "Expandir Base": "#CCCCCC"
                },
                size="porcentaje_mc",
                size_max=20,
                zoom=8,
                height=600,
                title=f"Mapa de Prioridades Estratégicas - Distritos de Diputaciones ({año_distrito})",
                labels={
                    "porcentaje_mc": "Porcentaje MC (%)",
                    "prioridad": "Prioridad Estratégica"
                }
            )

            fig_mapa_prioridades.update_layout(
                mapbox_style="open-street-map",
                margin={"r": 0, "t": 30, "l": 0, "b": 0}
            )

            st.plotly_chart(fig_mapa_prioridades, use_container_width=True)
        else:
            st.info("No se encontraron coordenadas para mostrar el mapa de distritos")

        # TABLAS ESTRATÉGICAS
        st.subheader("📋 ANÁLISIS ESTRATÉGICO POR CATEGORÍA - DISTRITOS")

        tab1, tab2, tab3, tab4 = st.tabs(
            ["🎯 Alta Oportunidad", "📈 Oportunidad Media", "🏆 Victorias", "📊 Todas las Categorías"])

        with tab1:
            alta_oportunidad = distritos_clave[distritos_clave['categoria'] == 'Alta Oportunidad']
            if not alta_oportunidad.empty:
                st.write("**🎯 DISTRITOS DE ALTA OPORTUNIDAD**")
                st.write("*(Porcentaje MC ≥ 40% - Alta probabilidad de ganar)*")
                st.dataframe(
                    alta_oportunidad[['division', 'votos_mc', 'total_votos', 'ganador']].sort_values(
                        'votos_mc', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No hay distritos en categoría de Alta Oportunidad")

        with tab2:
            media_oportunidad = distritos_clave[distritos_clave['categoria'] == 'Oportunidad Media']
            if not media_oportunidad.empty:
                st.write("**📈 DISTRITOS DE OPORTUNIDAD MEDIA**")
                st.write("*(25% ≤ Porcentaje MC < 40% - Requieren trabajo adicional)*")
                st.dataframe(
                    media_oportunidad[['division', 'votos_mc', 'total_votos', 'ganador']].sort_values(
                        'votos_mc', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No hay distritos en categoría de Oportunidad Media")

        with tab3:
            victorias = distritos_clave[distritos_clave['categoria'] == 'Victoria']
            if not victorias.empty:
                st.write("**🏆 DISTRITOS GANADOS**")
                st.write("*(MC es el partido ganador - Estrategia de consolidación)*")
                st.dataframe(
                    victorias[['division', 'votos_mc', 'total_votos']].sort_values('votos_mc', ascending=False),
                    use_container_width=True
                )
            else:
                st.info("No hay distritos ganados")

        with tab4:
            st.write("**📊 TODOS LOS DISTRITOS POR CATEGORÍA**")
            st.dataframe(
                distritos_clave[['division', 'categoria', 'prioridad', 'votos_mc', 'total_votos', 'ganador']].sort_values(['prioridad', 'votos_mc'], ascending=[True, False]),
                use_container_width=True,
                height=400
            )
    else:
        st.error(
            "No se pudieron cargar los datos de distritos de diputaciones. Verifique que la base de datos contenga información de elecciones de diputados.")

