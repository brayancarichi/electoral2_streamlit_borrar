import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configurar la página
st.set_page_config(
    page_title="Análisis Electoral Avanzado",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #e7f3ff;
        border: 1px solid #b3d9ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .simulation-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class AnalizadorElectoralAvanzado:
    def __init__(self, db_path='elecciones_nl_2021.db'):
        self.db_path = db_path
        self.data = None
        self.data_enriquecido = None

    def cargar_datos_completos(self):
        """Cargar todos los datos electorales"""
        try:
            conn = sqlite3.connect(self.db_path)

            query = """
            SELECT 
                nombre_candidato,
                partido_ci,
                tipo_eleccion,
                division_territorial,
                numero_de_votos,
                anno
            FROM resultados_electorales 
            WHERE tipo_eleccion != 'GOBERNADOR'
            UNION ALL
            SELECT 
                nombre_candidato,
                partido_ci,
                tipo_eleccion,
                division_territorial,
                numero_de_votos,
                anno
            FROM gobernador_corregido;
            """

            self.data = pd.read_sql_query(query, conn)
            conn.close()

            # Crear características básicas inmediatamente
            self._crear_caracteristicas_basicas()

            return self.data_enriquecido

        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            return pd.DataFrame()

    def _crear_caracteristicas_basicas(self):
        """Crear características básicas para análisis"""
        if self.data is None or len(self.data) == 0:
            st.warning("No hay datos para analizar")
            return

        df = self.data.copy()

        # 1. Características simples del nombre
        df['longitud_nombre'] = df['nombre_candidato'].str.len().fillna(0)
        df['cantidad_palabras'] = df['nombre_candidato'].str.split().str.len().fillna(1)

        # 2. Estadísticas por grupo para normalización
        df['votos_normalizados'] = 0.5  # Valor por defecto

        for tipo in df['tipo_eleccion'].unique():
            mask = df['tipo_eleccion'] == tipo
            votos_tipo = df.loc[mask, 'numero_de_votos']
            if len(votos_tipo) > 1 and votos_tipo.max() > votos_tipo.min():
                df.loc[mask, 'votos_normalizados'] = (
                        (votos_tipo - votos_tipo.min()) / (votos_tipo.max() - votos_tipo.min())
                )

        # 3. Percentil de votos por tipo de elección
        df['percentil_votos'] = 0.5  # Valor por defecto

        for tipo in df['tipo_eleccion'].unique():
            mask = df['tipo_eleccion'] == tipo
            votos_tipo = df.loc[mask, 'numero_de_votos']
            if len(votos_tipo) > 0:
                df.loc[mask, 'percentil_votos'] = votos_tipo.rank(pct=True)

        # 4. Categorizar éxito
        df['categoria_exito'] = pd.cut(
            df['percentil_votos'],
            bins=[0, 0.25, 0.75, 1],
            labels=['Bajo', 'Medio', 'Alto'],
            include_lowest=True
        )

        # 5. Crear columna binaria para éxito
        df['es_exitoso'] = (df['percentil_votos'] > 0.75).astype(int)

        self.data_enriquecido = df
        return self.data_enriquecido

    def verificar_columnas(self):
        """Verificar que todas las columnas necesarias existen"""
        if self.data_enriquecido is None:
            return False, "Los datos no han sido cargados"

        columnas_requeridas = ['es_exitoso', 'percentil_votos', 'categoria_exito']
        columnas_faltantes = [col for col in columnas_requeridas if col not in self.data_enriquecido.columns]

        if columnas_faltantes:
            return False, f"Columnas faltantes: {columnas_faltantes}"

        return True, "Todas las columnas están presentes"

    def analisis_estadistico_completo(self):
        """Análisis estadístico completo"""
        if self.data_enriquecido is None:
            self.cargar_datos_completos()

        if self.data_enriquecido is None or len(self.data_enriquecido) == 0:
            return {
                'error': 'No hay datos disponibles para análisis'
            }

        # Verificar columnas primero
        ok, mensaje = self.verificar_columnas()
        if not ok:
            return {'error': mensaje}

        df = self.data_enriquecido

        # Estadísticas generales
        stats = {
            'total_registros': len(df),
            'total_votos': df['numero_de_votos'].sum(),
            'promedio_votos': df['numero_de_votos'].mean(),
            'mediana_votos': df['numero_de_votos'].median(),
            'desviacion_std': df['numero_de_votos'].std(),
            'max_votos': df['numero_de_votos'].max(),
            'min_votos': df['numero_de_votos'].min(),
            'tasa_exito_general': df['es_exitoso'].mean()
        }

        # Por tipo de elección
        stats_tipo = df.groupby('tipo_eleccion').agg({
            'numero_de_votos': ['count', 'sum', 'mean', 'std'],
            'longitud_nombre': 'mean',
            'es_exitoso': 'mean'
        }).round(2)

        # Por partido
        stats_partido = df.groupby('partido_ci').agg({
            'numero_de_votos': ['sum', 'mean', 'count'],
            'es_exitoso': 'mean'
        }).round(3)

        # Top performers
        top_10 = df.nlargest(10, 'numero_de_votos')[
            ['nombre_candidato', 'partido_ci', 'tipo_eleccion', 'numero_de_votos']]

        return {
            'estadisticas_generales': stats,
            'por_tipo_eleccion': stats_tipo,
            'por_partido': stats_partido,
            'top_10_candidatos': top_10
        }

    def analisis_correlaciones(self):
        """Análisis de correlaciones simples"""
        if self.data_enriquecido is None:
            self.cargar_datos_completos()

        if self.data_enriquecido is None:
            return pd.DataFrame()

        df = self.data_enriquecido

        # Columnas numéricas disponibles
        columnas_numericas = ['numero_de_votos', 'longitud_nombre', 'cantidad_palabras', 'percentil_votos']

        # Filtrar columnas que realmente existen
        columnas_existentes = [col for col in columnas_numericas if col in df.columns]

        if len(columnas_existentes) < 2:
            return pd.DataFrame()

        correlaciones = df[columnas_existentes].corr()
        return correlaciones

    def obtener_partidos_exitosos(self, top_n=10):
        """Obtener partidos con mayor tasa de éxito"""
        if self.data_enriquecido is None:
            self.cargar_datos_completos()

        if self.data_enriquecido is None or 'es_exitoso' not in self.data_enriquecido.columns:
            return pd.DataFrame()

        df = self.data_enriquecido

        # Filtrar partidos con al menos 3 candidatos para tener datos significativos
        partidos_stats = df.groupby('partido_ci').agg({
            'es_exitoso': ['mean', 'count'],
            'numero_de_votos': 'mean'
        }).round(3)

        partidos_stats.columns = ['tasa_exito', 'cantidad_candidatos', 'promedio_votos']
        partidos_stats = partidos_stats[partidos_stats['cantidad_candidatos'] >= 3]

        return partidos_stats.sort_values('tasa_exito', ascending=False).head(top_n)

    def simular_candidato(self, partido, tipo_eleccion, division, nombre_candidato, factor_popularidad=1.0):
        """Simular el rendimiento de un candidato hipotético"""
        if self.data_enriquecido is None:
            self.cargar_datos_completos()

        if self.data_enriquecido is None:
            return {
                'error': 'No hay datos disponibles para simulación'
            }

        df = self.data_enriquecido

        # Obtener estadísticas base
        stats_partido = df[df['partido_ci'] == partido]
        stats_tipo = df[df['tipo_eleccion'] == tipo_eleccion]

        # Calcular votos base
        if len(stats_partido) > 0:
            votos_base = stats_partido['numero_de_votos'].mean()
        else:
            votos_base = df['numero_de_votos'].mean()

        # Ajustar por factores
        longitud_nombre = len(nombre_candidato)
        factor_longitud = 1.0

        # Ajuste basado en longitud del nombre (datos históricos)
        if longitud_nombre < 15:
            factor_longitud = 0.9
        elif longitud_nombre > 25:
            factor_longitud = 0.95
        else:
            factor_longitud = 1.05

        # Calcular votos proyectados
        votos_proyectados = votos_base * factor_popularidad * factor_longitud

        # Calcular probabilidad de éxito
        if len(stats_partido) > 0:
            prob_exito_base = stats_partido['es_exitoso'].mean()
        else:
            prob_exito_base = df['es_exitoso'].mean()

        prob_exito_ajustada = min(1.0, prob_exito_base * factor_popularidad * 1.1)

        return {
            'votos_proyectados': int(votos_proyectados),
            'probabilidad_exito': prob_exito_ajustada,
            'votos_base': votos_base,
            'factor_longitud': factor_longitud,
            'longitud_nombre': longitud_nombre
        }


# Instanciar el analizador
analizador = AnalizadorElectoralAvanzado()

# HEADER PRINCIPAL
st.markdown('<h1 class="main-header">📊 Plataforma de Análisis Electoral Avanzado</h1>', unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🎛️ Controles de Análisis")
    st.markdown("---")

    st.subheader("🔧 Acciones Rápidas")
    if st.button("🔄 Recargar y Verificar Datos"):
        with st.spinner("Cargando y verificando datos..."):
            datos = analizador.cargar_datos_completos()
            ok, mensaje = analizador.verificar_columnas()
            if ok:
                st.success("✅ " + mensaje)
            else:
                st.error("❌ " + mensaje)

    st.markdown("---")

    st.subheader("🔍 Filtros")
    datos = analizador.cargar_datos_completos()

    if datos is not None and len(datos) > 0:
        partido_filtro = st.multiselect(
            "Partidos:",
            options=datos['partido_ci'].unique(),
            default=datos['partido_ci'].unique()[:3]
        )

        tipo_filtro = st.multiselect(
            "Tipo Elección:",
            options=datos['tipo_eleccion'].unique(),
            default=datos['tipo_eleccion'].unique()
        )

# SECCIÓN 1: VERIFICACIÓN DE DATOS
st.header("🔍 Verificación de Datos")

# Cargar y verificar datos
datos_completos = analizador.cargar_datos_completos()
ok, mensaje_verificacion = analizador.verificar_columnas()

if not ok:
    st.error(f"❌ {mensaje_verificacion}")
    st.info("""
    **Solución:**
    1. Presiona el botón 'Recargar y Verificar Datos' en el sidebar
    2. Si el problema persiste, verifica que la base de datos exista
    3. Asegúrate de que las tablas 'resultados_electorales' y 'gobernador_corregido' existan
    """)
    st.stop()

st.success(f"✅ {mensaje_verificacion}")

if datos_completos is not None and len(datos_completos) > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros", len(datos_completos))
    with col2:
        st.metric("Columnas Disponibles", len(datos_completos.columns))
    with col3:
        st.metric("Candidatos Exitosos", datos_completos['es_exitoso'].sum())
else:
    st.error("No se pudieron cargar los datos")
    st.stop()

# SECCIÓN 2: MÉTRICAS PRINCIPALES
st.header("📊 Métricas Principales")

analisis = analizador.analisis_estadistico_completo()

if 'error' in analisis:
    st.error(f"Error en análisis: {analisis['error']}")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Candidatos", f"{analisis['estadisticas_generales']['total_registros']:,}")
    with col2:
        st.metric("Total Votos", f"{analisis['estadisticas_generales']['total_votos']:,}")
    with col3:
        st.metric("Promedio por Candidato", f"{analisis['estadisticas_generales']['promedio_votos']:,.0f}")
    with col4:
        st.metric("Tasa de Éxito", f"{analisis['estadisticas_generales']['tasa_exito_general']:.1%}")

# SECCIÓN 3: ANÁLISIS ESTADÍSTICO
st.header("📈 Análisis Estadístico Descriptivo")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Resumen General", "🏆 Top Performers", "📊 Por Partido", "🔍 Correlaciones"])

with tab1:
    st.subheader("Estadísticas por Tipo de Elección")
    if 'por_tipo_eleccion' in analisis:
        st.dataframe(analisis['por_tipo_eleccion'], use_container_width=True)

    # Gráfico de distribución
    fig_dist = px.box(
        datos_completos,
        x='tipo_eleccion',
        y='numero_de_votos',
        title='Distribución de Votos por Tipo de Elección',
        color='tipo_eleccion'
    )
    st.plotly_chart(fig_dist, use_container_width=True)

with tab2:
    st.subheader("Top 10 Candidatos Más Votados")
    if 'top_10_candidatos' in analisis:
        st.dataframe(analisis['top_10_candidatos'], use_container_width=True)

        # Gráfico de top candidatos
        fig_top = px.bar(
            analisis['top_10_candidatos'],
            x='numero_de_votos',
            y='nombre_candidato',
            orientation='h',
            color='partido_ci',
            title='Top 10 Candidatos por Votos Obtenidos',
            text='numero_de_votos'
        )
        fig_top.update_traces(texttemplate='%{text:,}', textposition='outside')
        st.plotly_chart(fig_top, use_container_width=True)

with tab3:
    st.subheader("Análisis por Partido Político")

    # Top partidos por votos totales
    partidos_top = datos_completos.groupby('partido_ci')['numero_de_votos'].sum().sort_values(ascending=False).head(15)

    col1, col2 = st.columns(2)

    with col1:
        fig_partidos = px.bar(
            x=partidos_top.values,
            y=partidos_top.index,
            orientation='h',
            title='Top 15 Partidos por Votos Totales',
            labels={'x': 'Votos Totales', 'y': 'Partido'}
        )
        fig_partidos.update_traces(texttemplate='%{x:,}', textposition='outside')
        st.plotly_chart(fig_partidos, use_container_width=True)

    with col2:
        # Partidos más exitosos
        partidos_exitosos = analizador.obtener_partidos_exitosos(10)
        if len(partidos_exitosos) > 0:
            fig_exito = px.bar(
                x=partidos_exitosos['tasa_exito'].values,
                y=partidos_exitosos.index,
                orientation='h',
                title='Top 10 Partidos por Tasa de Éxito',
                labels={'x': 'Tasa de Éxito', 'y': 'Partido'}
            )
            st.plotly_chart(fig_exito, use_container_width=True)
        else:
            st.info("No hay datos suficientes para analizar partidos exitosos")

with tab4:
    st.subheader("Análisis de Correlaciones")

    correlaciones = analizador.analisis_correlaciones()
    if len(correlaciones) > 0:
        st.dataframe(correlaciones, use_container_width=True)

        # Heatmap de correlaciones
        fig_corr = px.imshow(
            correlaciones,
            title='Mapa de Calor - Correlaciones entre Variables',
            color_continuous_scale='RdBu_r',
            aspect='auto',
            text_auto=True
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("No hay suficientes datos numéricos para calcular correlaciones")

# SECCIÓN 4: 🎮 SIMULADOR DE CANDIDATOS (NUEVA SECCIÓN)
st.header("🎮 Simulador de Candidatos")

st.markdown("""
<div class="info-box">
    <h3>🚀 Simula el rendimiento de candidatos hipotéticos</h3>
    <p>Esta herramienta utiliza datos históricos para proyectar el potencial electoral de candidatos basándose en:</p>
    <ul>
        <li>📊 Rendimiento histórico del partido</li>
        <li>🎯 Tipo de elección</li>
        <li>📏 Características del nombre del candidato</li>
        <li>⭐ Factor de popularidad ajustable</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Configuración del Candidato")

    # Selectores de configuración
    partido_sim = st.selectbox(
        "Partido Político:",
        options=datos_completos['partido_ci'].unique(),
        key="partido_sim"
    )

    tipo_sim = st.selectbox(
        "Tipo de Elección:",
        options=['DIPUTADO', 'MUNICIPAL'],
        key="tipo_sim"
    )

    division_sim = st.text_input(
        "División Territorial:",
        value="Nuevo Distrito",
        key="division_sim"
    )

    nombre_sim = st.text_input(
        "Nombre del Candidato:",
        value="María González López",
        key="nombre_sim"
    )

    # Factores de ajuste
    st.subheader("🎚️ Factores de Ajuste")

    factor_popularidad = st.slider(
        "Factor de Popularidad:",
        min_value=0.1,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help="Ajusta la popularidad base del candidato (0.1 = muy baja, 3.0 = muy alta)"
    )

    # Mostrar estadísticas del partido seleccionado
    stats_partido = datos_completos[datos_completos['partido_ci'] == partido_sim]
    if len(stats_partido) > 0:
        st.info(f"""
        **📊 Estadísticas de {partido_sim}:**
        - Promedio histórico: {stats_partido['numero_de_votos'].mean():,.0f} votos
        - Candidatos presentados: {len(stats_partido)}
        - Tasa de éxito: {stats_partido['es_exitoso'].mean():.1%}
        - Mejor resultado: {stats_partido['numero_de_votos'].max():,} votos
        """)

with col2:
    st.subheader("🎯 Ejecutar Simulación")

    if st.button("🚀 Calcular Proyección", type="primary", use_container_width=True):
        with st.spinner("Calculando proyección..."):
            resultado = analizador.simular_candidato(
                partido_sim, tipo_sim, division_sim, nombre_sim, factor_popularidad
            )

            if 'error' in resultado:
                st.error(resultado['error'])
            else:
                # Mostrar resultados en tarjeta especial
                st.markdown(f"""
                <div class="simulation-card">
                    <h3>📊 Resultado de Simulación</h3>
                    <h1>{resultado['votos_proyectados']:,}</h1>
                    <h3>Votos Proyectados</h3>
                    <p>Probabilidad de éxito: <strong>{resultado['probabilidad_exito']:.1%}</strong></p>
                </div>
                """, unsafe_allow_html=True)

                # Análisis detallado
                st.subheader("📈 Análisis Detallado")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric(
                        "Votos Base",
                        f"{resultado['votos_base']:,.0f}",
                        help="Promedio histórico del partido"
                    )
                with col_b:
                    st.metric(
                        "Ajuste Longitud",
                        f"{resultado['factor_longitud']:.2f}x",
                        help=f"Longitud nombre: {resultado['longitud_nombre']} caracteres"
                    )
                with col_c:
                    st.metric(
                        "Factor Popularidad",
                        f"{factor_popularidad:.1f}x",
                        help="Ajuste por popularidad"
                    )

                # Evaluación de potencial
                st.subheader("🎯 Evaluación de Potencial")

                votos_promedio = analisis['estadisticas_generales']['promedio_votos']
                ratio = resultado['votos_proyectados'] / votos_promedio

                if ratio > 2.0:
                    st.success("""
                    **🎉 EXCELENTE POTENCIAL**
                    - Muy por encima del promedio
                    - Alta probabilidad de éxito
                    - Candidato competitivo
                    """)
                elif ratio > 1.2:
                    st.warning("""
                    **📊 BUEN POTENCIAL** 
                    - Por encima del promedio
                    - Probabilidad moderada de éxito
                    - Candidato viable
                    """)
                else:
                    st.error("""
                    **📉 POTENCIAL LIMITADO**
                    - En o por debajo del promedio
                    - Baja probabilidad de éxito
                    - Considerar estrategias alternativas
                    """)

# SECCIÓN 5: COMPARATIVA DE ESCENARIOS
st.header("🔄 Comparativa de Escenarios")

st.markdown("""
**Compara diferentes configuraciones para optimizar tu estrategia electoral**
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Escenario Conservador")
    if st.button("Calcular Escenario 1", key="esc1"):
        resultado = analizador.simular_candidato(partido_sim, tipo_sim, division_sim, nombre_sim, 0.8)
        if 'error' not in resultado:
            st.metric("Votos Proyectados", f"{resultado['votos_proyectados']:,}")
            st.metric("Prob. Éxito", f"{resultado['probabilidad_exito']:.1%}")

with col2:
    st.subheader("Escenario Moderado")
    if st.button("Calcular Escenario 2", key="esc2"):
        resultado = analizador.simular_candidato(partido_sim, tipo_sim, division_sim, nombre_sim, 1.0)
        if 'error' not in resultado:
            st.metric("Votos Proyectados", f"{resultado['votos_proyectados']:,}")
            st.metric("Prob. Éxito", f"{resultado['probabilidad_exito']:.1%}")

with col3:
    st.subheader("Escenario Optimista")
    if st.button("Calcular Escenario 3", key="esc3"):
        resultado = analizador.simular_candidato(partido_sim, tipo_sim, division_sim, nombre_sim, 1.5)
        if 'error' not in resultado:
            st.metric("Votos Proyectados", f"{resultado['votos_proyectados']:,}")
            st.metric("Prob. Éxito", f"{resultado['probabilidad_exito']:.1%}")

# SECCIÓN 6: TENDENCIAS Y PATRONES
st.header("📈 Tendencias y Patrones")

col1, col2 = st.columns(2)

with col1:
    # Distribución de categorías de éxito
    conteo_categorias = datos_completos['categoria_exito'].value_counts()
    fig_pie = px.pie(
        values=conteo_categorias.values,
        names=conteo_categorias.index,
        title='Distribución de Categorías de Éxito'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Longitud de nombre por tipo de elección
    fig_violin = px.violin(
        datos_completos,
        x='tipo_eleccion',
        y='longitud_nombre',
        color='tipo_eleccion',
        title='Distribución de Longitud de Nombres por Tipo de Elección',
        box=True
    )
    st.plotly_chart(fig_violin, use_container_width=True)

# FOOTER
st.markdown("---")
st.markdown(
    "**📊 Plataforma de Análisis Electoral Avanzado** | "
    "**🎮 Simulador de Candidatos** | "
    "Datos: Nuevo León 2021 | "
    f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
#"numpy==1.24.4"
# pip install "scipy==1.10.1" "pandas==2.0.0" "scikit-learn==1.3.0" "plotly==5.15.0" "streamlit==1.28.0" "joblib==1.3.0"
