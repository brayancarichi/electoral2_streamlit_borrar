import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configurar la página
st.set_page_config(
    page_title="Elecciones NL 2021 & 2024",
    page_icon="🗳️",
    layout="wide"
)

# CSS simple
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .mc-header {
        background: linear-gradient(135deg, #F58220, #FFA500);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# PALETA DE COLORES COMPLETA PARA PARTIDOS (2021 + 2024)
COLORES_PARTIDOS = {
    # Partidos principales
    'PAN': '#0F6BB6',  # Azul
    'PRI': '#009640',  # Verde
    'PRD': '#FFDE00',  # Amarillo
    'PVEM': '#00A650',  # Verde claro
    'PT': '#EE3D44',  # Rojo
    'MC': '#F58220',  # Naranja
    'MORENA': '#B52E6E',  # Magenta
    'PES': '#8EC641',  # Verde lima
    'RSP': '#FFD100',  # Amarillo oro
    'FXM': '#8B008B',  # Púrpura oscuro

    # Partidos locales NL
    'FCXNL': '#6A1E55',  # Morado
    'SHHNL': '#00A2B8',  # Turquesa
    'VIDA': '#FF6B00',  # Naranja fuerte
    'ESO': '#8B4513',  # Café
    'PL': '#FF69B4',  # Rosa
    'PJ': '#800080',  # Púrpura

    # Candidaturas independientes y especiales
    'CAND_IND_1': '#A9A9A9',  # Gris
    'CAND_IND_2': '#808080',  # Gris medio
    'CAND_IND_3': '#696969',  # Gris oscuro
    'INDEPENDIENTE': '#A9A9A9',  # Gris

    # Estados especiales
    'Registro cancelado': '#666666',  # Gris oscuro
    'NULO': '#000000',  # Negro
    'NO REGISTRADO': '#CCCCCC'  # Gris claro
}

# COLORES POR DEFECTO PARA PARTIDOS NO LISTADOS (generados automáticamente)
COLORES_POR_DEFECTO = [
    '#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF',
    '#FFB366', '#B366FF', '#66FFB3', '#FF66B3', '#B3FF66', '#66B3FF',
    '#FFCC99', '#CC99FF', '#99FFCC', '#FF99CC', '#CCFF99', '#99CCFF',
    '#E6B3B3', '#B3E6B3', '#B3B3E6', '#E6E6B3', '#E6B3E6', '#B3E6E6'
]


class DashboardSimple:
    def __init__(self):
        self.dbs = {
            '2021': 'elecciones_nl_2021.db',
            '2024': 'elecciones_nl_2024.db'
        }
        self._cache_partidos = {}  # Cache para partidos por año

    def conectar(self, año):
        return sqlite3.connect(self.dbs[año])

    def obtener_datos(self, año, tipo_eleccion):
        with self.conectar(año) as conn:
            query = "SELECT * FROM resultados_electorales WHERE tipo_eleccion = ? ORDER BY numero_de_votos DESC"
            return pd.read_sql_query(query, conn, params=(tipo_eleccion,))

    def obtener_todos_los_partidos(self, año):
        """Obtener todos los partidos únicos de un año específico"""
        if año in self._cache_partidos:
            return self._cache_partidos[año]

        with self.conectar(año) as conn:
            query = "SELECT DISTINCT partido_ci FROM resultados_electorales ORDER BY partido_ci"
            partidos = pd.read_sql_query(query, conn)['partido_ci'].tolist()
            self._cache_partidos[año] = partidos
            return partidos

    def obtener_colores_para_partidos(self, partidos, año):
        """Obtener colores para una lista de partidos, asignando colores por defecto si es necesario"""
        colores_map = {}
        color_index = 0

        for partido in partidos:
            if partido in COLORES_PARTIDOS:
                colores_map[partido] = COLORES_PARTIDOS[partido]
            else:
                # Asignar color por defecto
                colores_map[partido] = COLORES_POR_DEFECTO[color_index % len(COLORES_POR_DEFECTO)]
                color_index += 1

        return colores_map

    def obtener_leyenda_partidos(self, año):
        """Obtener la leyenda de colores para los partidos de un año específico"""
        partidos_año = self.obtener_todos_los_partidos(año)
        colores_map = self.obtener_colores_para_partidos(partidos_año, año)

        leyenda = []
        for partido in partidos_año:
            color = colores_map[partido]
            leyenda.append({
                'partido': partido,
                'color': color,
                'es_default': partido not in COLORES_PARTIDOS
            })

        return leyenda


class AnalisisMC:
    def __init__(self, dashboard):
        self.dashboard = dashboard

    def obtener_nombre_mc_por_año(self, año):
        """Obtener el nombre correcto de MC según el año"""
        if año == '2021':
            return 'Movimiento Ciudadano'
        else:
            return 'MC'

    def obtener_ganadores_por_division(self, año, tipo_eleccion):
        """Obtener ganadores por división territorial"""
        with self.dashboard.conectar(año) as conn:
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
            WHERE rank = 1
            ORDER BY numero_de_votos DESC;
            """
            return pd.read_sql_query(query, conn, params=(tipo_eleccion,))

    def analizar_desempeno_mc(self, año):
        """Análisis completo del desempeño de MC"""
        nombre_mc = self.obtener_nombre_mc_por_año(año)

        # Obtener datos de ambos tipos de elección
        datos_municipales = self.dashboard.obtener_datos(año, 'MUNICIPAL')
        datos_diputados = self.dashboard.obtener_datos(año, 'DIPUTADO')

        # Ganadores por municipio y distrito
        ganadores_municipio = self.obtener_ganadores_por_division(año, 'MUNICIPAL')
        ganadores_distrito = self.obtener_ganadores_por_division(año, 'DIPUTADO')

        # Municipios donde MC ganó
        mc_gana_municipio = ganadores_municipio[ganadores_municipio['partido_ci'] == nombre_mc]

        # Municipios donde MC perdió
        mc_pierde_municipio = ganadores_municipio[ganadores_municipio['partido_ci'] != nombre_mc]

        # Distritos donde MC ganó
        mc_gana_distrito = ganadores_distrito[ganadores_distrito['partido_ci'] == nombre_mc]

        # Distritos donde MC perdió
        mc_pierde_distrito = ganadores_distrito[ganadores_distrito['partido_ci'] != nombre_mc]

        # Análisis de correlación: dónde ganó municipio pero perdió diputación
        municipios_mc_gana = set(mc_gana_municipio['division_territorial'])
        distritos_mc_pierde = set(mc_pierde_distrito['division_territorial'])

        conflicto_municipio_gana_diputacion_pierde = municipios_mc_gana.intersection(distritos_mc_pierde)

        # Análisis de votos promedio
        votos_mc_municipales = datos_municipales[datos_municipales['partido_ci'] == nombre_mc]['numero_de_votos']
        votos_mc_diputados = datos_diputados[datos_diputados['partido_ci'] == nombre_mc]['numero_de_votos']

        # Eficiencia por división territorial
        eficiencia_municipio = []
        for municipio in datos_municipales['division_territorial'].unique():
            datos_mun = datos_municipales[datos_municipales['division_territorial'] == municipio]
            if nombre_mc in datos_mun['partido_ci'].values:
                votos_mc = datos_mun[datos_mun['partido_ci'] == nombre_mc]['numero_de_votos'].iloc[0]
                votos_totales = datos_mun['numero_de_votos'].sum()
                porcentaje = (votos_mc / votos_totales) * 100
                ganador = \
                ganadores_municipio[ganadores_municipio['division_territorial'] == municipio]['partido_ci'].iloc[0]
                eficiencia_municipio.append({
                    'municipio': municipio,
                    'votos_mc': votos_mc,
                    'porcentaje_mc': porcentaje,
                    'ganador': ganador,
                    'mc_es_ganador': ganador == nombre_mc
                })

        eficiencia_municipio_df = pd.DataFrame(eficiencia_municipio)

        return {
            'nombre_mc': nombre_mc,
            'gana_municipio': mc_gana_municipio,
            'pierde_municipio': mc_pierde_municipio,
            'gana_distrito': mc_gana_distrito,
            'pierde_distrito': mc_pierde_distrito,
            'conflicto_municipio_gana_diputacion_pierde': list(conflicto_municipio_gana_diputacion_pierde),
            'estadisticas_votos': {
                'promedio_municipales': votos_mc_municipales.mean() if len(votos_mc_municipales) > 0 else 0,
                'promedio_diputados': votos_mc_diputados.mean() if len(votos_mc_diputados) > 0 else 0,
                'maximo_municipales': votos_mc_municipales.max() if len(votos_mc_municipales) > 0 else 0,
                'maximo_diputados': votos_mc_diputados.max() if len(votos_mc_diputados) > 0 else 0,
                'total_candidatos_municipales': len(votos_mc_municipales),
                'total_candidatos_diputados': len(votos_mc_diputados)
            },
            'eficiencia_municipio': eficiencia_municipio_df
        }

    def analizar_tendencias_competencia(self, año):
        """Analizar contra qué partidos compite principalmente MC"""
        nombre_mc = self.obtener_nombre_mc_por_año(año)

        # Obtener ganadores donde MC no ganó
        ganadores_municipio = self.obtener_ganadores_por_division(año, 'MUNICIPAL')
        ganadores_sin_mc = ganadores_municipio[ganadores_municipio['partido_ci'] != nombre_mc]

        # Contar frecuencia de partidos ganadores
        competencia_municipio = ganadores_sin_mc['partido_ci'].value_counts().reset_index()
        competencia_municipio.columns = ['partido', 'municipios_ganados']

        return competencia_municipio


# Inicializar dashboards
dashboard = DashboardSimple()
analisis_mc = AnalisisMC(dashboard)

# CREAR PESTAÑAS
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Principal", "🗺️ Zonas Ganadas por Partido", "🔍 Análisis MC"])

with tab1:
    # TÍTULO PRINCIPAL
    st.markdown('<h1 class="main-title">🗳️ Elecciones Nuevo León</h1>', unsafe_allow_html=True)

    # SIDEBAR SIMPLE
    with st.sidebar:
        st.header("Controles")

        # Selección de año
        año_seleccionado = st.radio(
            "Selecciona el año:",
            ['2021', '2024'],
            index=1
        )

        # Selección de tipo de elección
        if año_seleccionado == '2021':
            tipos = ['GOBERNADOR', 'DIPUTADO', 'MUNICIPAL']
        else:
            tipos = ['DIPUTADO', 'MUNICIPAL']

        tipo_seleccionado = st.selectbox(
            "Tipo de elección:",
            tipos
        )

        # Filtro por partido
        datos = dashboard.obtener_datos(año_seleccionado, tipo_seleccionado)
        partidos = datos['partido_ci'].unique().tolist()
        partido_seleccionado = st.multiselect(
            "Partidos:",
            partidos,
            default=partidos
        )

        # Mostrar leyenda de colores para el año seleccionado
        with st.expander(f"🎨 Colores de partidos ({año_seleccionado})"):
            leyenda = dashboard.obtener_leyenda_partidos(año_seleccionado)

            for item in leyenda:
                partido = item['partido']
                color = item['color']
                es_default = item['es_default']

                if partido in partidos:  # Solo mostrar partidos disponibles en los datos actuales
                    estilo_texto = "color: black;" if color in ['#FFDE00', '#FFFF99', '#FFD100'] else "color: white;"
                    marca_default = " ⚠️" if es_default else ""

                    st.markdown(
                        f"<div style='background-color: {color}; padding: 8px; margin: 3px; border-radius: 5px; {estilo_texto}'>"
                        f"<strong>{partido}</strong>{marca_default}</div>",
                        unsafe_allow_html=True
                    )

    # APLICAR FILTROS
    if partido_seleccionado:
        datos_filtrados = datos[datos['partido_ci'].isin(partido_seleccionado)]
    else:
        datos_filtrados = datos

    # Obtener mapa de colores para los partidos filtrados
    colores_map = dashboard.obtener_colores_para_partidos(
        datos_filtrados['partido_ci'].unique(),
        año_seleccionado
    )

    # MÉTRICAS PRINCIPALES
    st.subheader(f"📊 Resumen {año_seleccionado} - {tipo_seleccionado}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Candidatos", len(datos_filtrados))

    with col2:
        st.metric("Total Votos", f"{datos_filtrados['numero_de_votos'].sum():,}")

    with col3:
        st.metric("Partidos", datos_filtrados['partido_ci'].nunique())

    with col4:
        avg_votos = datos_filtrados['numero_de_votos'].mean()
        st.metric("Promedio Votos", f"{avg_votos:,.0f}")

    # GRÁFICO PRINCIPAL - TOP 10 CANDIDATOS
    st.subheader(f"🏆 Top 10 Candidatos - {año_seleccionado}")

    top_10 = datos_filtrados.head(10)

    if not top_10.empty:
        fig = px.bar(
            top_10,
            x='numero_de_votos',
            y='nombre_candidato',
            orientation='h',
            color='partido_ci',
            title=f'Top 10 Candidatos Más Votados - {tipo_seleccionado} {año_seleccionado}',
            labels={'numero_de_votos': 'Votos', 'nombre_candidato': 'Candidato'},
            color_discrete_map=colores_map
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=True,
            height=500
        )
        fig.update_traces(
            texttemplate='%{x:,}',
            textposition='outside'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar")

    # GRÁFICO DE PARTIDOS
    st.subheader(f"📈 Distribución por Partido - {año_seleccionado}")

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de torta - votos por partido
        votos_por_partido = datos_filtrados.groupby('partido_ci')['numero_de_votos'].sum().reset_index()

        if not votos_por_partido.empty:
            fig_torta = px.pie(
                votos_por_partido,
                values='numero_de_votos',
                names='partido_ci',
                title=f'Votos por Partido - {tipo_seleccionado}',
                color='partido_ci',
                color_discrete_map=colores_map
            )
            fig_torta.update_traces(
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Votos: %{value:,}<br>Porcentaje: %{percent}'
            )
            st.plotly_chart(fig_torta, use_container_width=True)

    with col2:
        # Gráfico de barras - candidatos por partido
        candidatos_por_partido = datos_filtrados.groupby('partido_ci').size().reset_index(name='candidatos')

        if not candidatos_por_partido.empty:
            fig_barras = px.bar(
                candidatos_por_partido,
                x='candidatos',
                y='partido_ci',
                orientation='h',
                title=f'Candidatos por Partido - {tipo_seleccionado}',
                color='partido_ci',
                color_discrete_map=colores_map,
                text='candidatos'
            )
            fig_barras.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            fig_barras.update_traces(
                texttemplate='%{x}',
                textposition='outside'
            )
            st.plotly_chart(fig_barras, use_container_width=True)

    # COMPARATIVA ENTRE AÑOS (solo si hay datos comparables)
    if tipo_seleccionado in ['DIPUTADO', 'MUNICIPAL']:
        st.subheader("🔄 Comparativa entre Años")

        try:
            # Obtener datos del otro año
            otro_año = '2024' if año_seleccionado == '2021' else '2021'
            datos_otro_año = dashboard.obtener_datos(otro_año, tipo_seleccionado)

            # Comparar totales
            col1, col2 = st.columns(2)

            with col1:
                votos_actual = datos_filtrados['numero_de_votos'].sum()
                st.metric(
                    f"Total Votos {año_seleccionado}",
                    f"{votos_actual:,}",
                    delta=None
                )

            with col2:
                votos_otro = datos_otro_año['numero_de_votos'].sum()
                diferencia = votos_actual - votos_otro
                st.metric(
                    f"Total Votos {otro_año}",
                    f"{votos_otro:,}",
                    delta=f"{diferencia:+,}"
                )

        except:
            st.info("No hay datos comparables para el otro año")

    # TABLA DE DATOS
    st.subheader("📋 Lista de Candidatos")

    # Mostrar tabla simplificada con colores
    columnas_mostrar = ['nombre_candidato', 'partido_ci', 'division_territorial', 'numero_de_votos']
    st.dataframe(
        datos_filtrados[columnas_mostrar],
        use_container_width=True,
        height=300
    )

with tab2:
    st.header("🗺️ Zonas Ganadas por Partido")

    # Selector de año para esta pestaña
    año_zona = st.radio("Selecciona el año:", ['2021', '2024'], key="zona_año", horizontal=True)

    # Selector de tipo de elección
    tipo_zona = st.selectbox("Tipo de elección:", ['MUNICIPAL', 'DIPUTADO'], key="zona_tipo")

    # Obtener ganadores
    ganadores = analisis_mc.obtener_ganadores_por_division(año_zona, tipo_zona)

    if not ganadores.empty:
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Divisiones", len(ganadores))

        with col2:
            st.metric("Partidos Ganadores", ganadores['partido_ci'].nunique())

        with col3:
            partido_mas_ganador = ganadores['partido_ci'].mode()[0]
            st.metric("Partido con Más Victorias", partido_mas_ganador)

        # Gráfico de distribución
        distribucion = ganadores['partido_ci'].value_counts().reset_index()
        distribucion.columns = ['Partido', 'Victorias']

        fig_dist = px.bar(
            distribucion,
            x='Victorias',
            y='Partido',
            orientation='h',
            title=f'Distribución de Victorias por Partido - {tipo_zona} {año_zona}',
            color='Partido',
            color_discrete_map=dashboard.obtener_colores_para_partidos(distribucion['Partido'].tolist(), año_zona)
        )
        fig_dist.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_dist, use_container_width=True)

        # Tabla de ganadores
        st.subheader("🏆 Lista Completa de Ganadores")
        st.dataframe(ganadores, use_container_width=True, height=400)
    else:
        st.info("No hay datos de ganadores disponibles")

with tab3:
    st.markdown('<div class="mc-header"><h2>🔍 ANÁLISIS AVANZADO - MOVIMIENTO CIUDADANO</h2></div>',
                unsafe_allow_html=True)

    # Selector de año para análisis MC
    año_mc = st.radio("Selecciona el año para análisis:", ['2021', '2024'], key="mc_año", horizontal=True)

    # Ejecutar análisis completo
    with st.spinner("Realizando análisis avanzado de MC..."):
        analisis = analisis_mc.analizar_desempeno_mc(año_mc)
        competencia = analisis_mc.analizar_tendencias_competencia(año_mc)

    nombre_mc = analisis['nombre_mc']

    # MÉTRICAS PRINCIPALES MC
    st.subheader("📈 Métricas Clave de Movimiento Ciudadano")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Municipios Ganados", len(analisis['gana_municipio']))

    with col2:
        st.metric("Distritos Ganados", len(analisis['gana_distrito']))

    with col3:
        total_municipios = len(analisis['gana_municipio']) + len(analisis['pierde_municipio'])
        porcentaje_ganados = (len(analisis['gana_municipio']) / total_municipios * 100) if total_municipios > 0 else 0
        st.metric("Eficiencia Municipal", f"{porcentaje_ganados:.1f}%")

    with col4:
        st.metric("Conflicto Muni-Gana/Dip-Pierde", len(analisis['conflicto_municipio_gana_diputacion_pierde']))

    # ANÁLISIS DE CONFLICTOS
    st.subheader("⚡ Análisis de Conflictos Estratégicos")

    if analisis['conflicto_municipio_gana_diputacion_pierde']:
        st.warning(
            f"**Zonas críticas encontradas:** {len(analisis['conflicto_municipio_gana_diputacion_pierde'])} municipios donde MC ganó la alcaldía pero perdió la diputación")

        conflicto_df = pd.DataFrame({
            'Municipio': analisis['conflicto_municipio_gana_diputacion_pierde']
        })
        st.dataframe(conflicto_df, use_container_width=True)

        st.info("""
        **Interpretación:** Estas zonas representan oportunidades estratégicas donde MC tiene presencia municipal 
        pero necesita fortalecer su estructura para elecciones de diputados. Son áreas clave para inversión 
        en campañas futuras.
        """)
    else:
        st.success("✅ No se encontraron conflictos estratégicos significativos")

    # COMPARATIVA DE DESEMPEÑO
    st.subheader("📊 Comparativa de Desempeño por Tipo de Elección")

    col1, col2 = st.columns(2)

    with col1:
        fig_comparativa = go.Figure()

        fig_comparativa.add_trace(go.Indicator(
            mode="number+delta",
            value=analisis['estadisticas_votos']['promedio_municipales'],
            title={"text": "Votos Promedio<br>Municipales"},
            number={'valueformat': ',.0f'},
            domain={'row': 0, 'column': 0}
        ))

        fig_comparativa.add_trace(go.Indicator(
            mode="number+delta",
            value=analisis['estadisticas_votos']['promedio_diputados'],
            title={"text": "Votos Promedio<br>Diputados"},
            number={'valueformat': ',.0f'},
            domain={'row': 0, 'column': 1}
        ))

        fig_comparativa.update_layout(
            grid={'rows': 1, 'columns': 2, 'pattern': "independent"},
            height=200
        )

        st.plotly_chart(fig_comparativa, use_container_width=True)

    with col2:
        # Gráfico de candidatos presentados
        candidatos_data = {
            'Tipo': ['Municipales', 'Diputados'],
            'Cantidad': [
                analisis['estadisticas_votos']['total_candidatos_municipales'],
                analisis['estadisticas_votos']['total_candidatos_diputados']
            ]
        }

        fig_candidatos = px.bar(
            candidatos_data,
            x='Tipo',
            y='Cantidad',
            title='Candidatos Presentados por MC',
            color='Tipo',
            color_discrete_sequence=['#F58220', '#FFA500']
        )
        st.plotly_chart(fig_candidatos, use_container_width=True)

    # ANÁLISIS DE COMPETENCIA
    st.subheader("🎯 Análisis de Competencia Principal")

    if not competencia.empty:
        fig_competencia = px.bar(
            competencia.head(10),
            x='municipios_ganados',
            y='partido',
            orientation='h',
            title=f'Principales Competidores de MC - Municipios Ganados {año_mc}',
            color='partido',
            color_discrete_map=dashboard.obtener_colores_para_partidos(competencia['partido'].tolist(), año_mc)
        )
        fig_competencia.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_competencia, use_container_width=True)
    else:
        st.info("No hay datos de competencia disponibles")

    # EFICIENCIA POR MUNICIPIO
    st.subheader("🏆 Eficiencia de MC por Municipio")

    if not analisis['eficiencia_municipio'].empty:
        # Top 10 municipios con mejor desempeño de MC
        top_eficiencia = analisis['eficiencia_municipio'].nlargest(10, 'porcentaje_mc')

        fig_eficiencia = px.bar(
            top_eficiencia,
            x='porcentaje_mc',
            y='municipio',
            orientation='h',
            title=f'Top 10 Municipios - Porcentaje de Votos MC {año_mc}',
            color='mc_es_ganador',
            color_discrete_map={True: '#F58220', False: '#CCCCCC'},
            hover_data=['votos_mc']
        )
        fig_eficiencia.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=True
        )
        st.plotly_chart(fig_eficiencia, use_container_width=True)

        # Mostrar tabla completa de eficiencia
        with st.expander("📋 Ver eficiencia completa por municipio"):
            st.dataframe(
                analisis['eficiencia_municipio'].sort_values('porcentaje_mc', ascending=False),
                use_container_width=True,
                height=400
            )

    # RECOMENDACIONES ESTRATÉGICAS
    st.subheader("💡 Recomendaciones Estratégicas")

    if len(analisis['conflicto_municipio_gana_diputacion_pierde']) > 0:
        st.error("""
        **🚨 ACCIÓN PRIORITARIA REQUERIDA:**

        Se detectaron zonas donde MC tiene presencia municipal pero no diputacional. Recomendamos:

        1. **Fortalecer estructura partidista** en municipios con conflicto
        2. **Capitalizar alcaldías** para impulsar candidaturas diputacionales
        3. **Desarrollar campañas específicas** para elecciones intermedias
        """)

    if len(analisis['gana_municipio']) > len(analisis['gana_distrito']):
        st.warning("""
        **📈 OPORTUNIDAD DE CRECIMIENTO:**

        MC tiene mayor fuerza municipal que diputacional. Estrategia recomendada:

        - Transferir capital político de alcaldías a diputaciones
        - Usar estructura municipal como base para campañas estatales
        - Desarrollar candidatos puente entre niveles de gobierno
        """)

    if analisis['estadisticas_votos']['promedio_municipales'] > analisis['estadisticas_votos']['promedio_diputados']:
        st.info("""
        **🎯 EFICIENCIA MUNICIPAL SUPERIOR:**

        Los candidatos municipales de MC obtienen más votos en promedio. Sugerencias:

        - Replicar estrategias municipales exitosas a nivel diputacional
        - Identificar y entrenar a los mejores operadores municipales
        - Crear programas de transferencia de conocimiento
        """)

# FOOTER SIMPLE
st.markdown("---")
st.caption("Dashboard de Elecciones NL | Análisis avanzado de Movimiento Ciudadano | Datos 2021-2024")