import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

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
    .winner-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid;
        margin-bottom: 0.5rem;
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
    '#2a7ec7', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF',
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

    def obtener_datos_por_division(self, año, tipo_eleccion, division_territorial):
        """Obtener datos filtrados por división territorial específica"""
        with self.conectar(año) as conn:
            query = """
            SELECT * FROM resultados_electorales 
            WHERE tipo_eleccion = ? AND division_territorial = ? 
            ORDER BY numero_de_votos DESC
            """
            return pd.read_sql_query(query, conn, params=(tipo_eleccion, division_territorial))

    def obtener_divisiones_territoriales(self, año, tipo_eleccion):
        """Obtener lista única de divisiones territoriales"""
        with self.conectar(año) as conn:
            query = "SELECT DISTINCT division_territorial FROM resultados_electorales WHERE tipo_eleccion = ? ORDER BY division_territorial"
            return pd.read_sql_query(query, conn, params=(tipo_eleccion,))['division_territorial'].tolist()

    def obtener_ganadores_por_division(self, año, tipo_eleccion):
        """Obtener los ganadores por cada división territorial"""
        with self.conectar(año) as conn:
            query = """
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
            SELECT 
                division_territorial,
                nombre_candidato,
                partido_ci,
                numero_de_votos
            FROM ranked_candidates 
            WHERE rank = 1
            ORDER BY division_territorial;
            """
            return pd.read_sql_query(query, conn, params=(tipo_eleccion,))

    def obtener_zonas_ganadas_por_partido(self, año, tipo_eleccion):
        """Obtener en qué zonas ganó cada partido político"""
        ganadores = self.obtener_ganadores_por_division(año, tipo_eleccion)

        if ganadores.empty:
            return pd.DataFrame()

        # Contar zonas ganadas por partido
        zonas_por_partido = ganadores.groupby('partido_ci').agg({
            'division_territorial': 'count',
            'numero_de_votos': 'sum'
        }).reset_index()

        zonas_por_partido.columns = ['Partido', 'Zonas_Ganadas', 'Total_Votos_Ganadores']
        zonas_por_partido = zonas_por_partido.sort_values('Zonas_Ganadas', ascending=False)

        return zonas_por_partido

    def obtener_detalle_zonas_ganadas(self, año, tipo_eleccion, partido):
        """Obtener el detalle de las zonas ganadas por un partido específico"""
        ganadores = self.obtener_ganadores_por_division(año, tipo_eleccion)
        zonas_partido = ganadores[ganadores['partido_ci'] == partido]
        return zonas_partido

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


# Inicializar dashboard
dashboard = DashboardSimple()

# CREAR PESTAÑAS
tab1, tab2, tab3 = st.tabs(
    ["Dashboard Principal", "Análisis por División Territorial", "Zonas Ganadas por Partido"])

with tab1:
    # TÍTULO PRINCIPAL
    st.markdown('<h1 class="main-title">Elecciones Nuevo León</h1>', unsafe_allow_html=True)

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
        with st.expander(f"Colores de partidos ({año_seleccionado})"):
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
        st.metric("Total Candidatos", datos_filtrados['nombre_candidato'].nunique())

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

    # GRÁFICO ADICIONAL: COMPARATIVA DE VOTOS POR PARTIDO
    st.subheader(f"📊 Comparativa de Votos por Partido")

    votos_totales_por_partido = datos_filtrados.groupby('partido_ci').agg({
        'numero_de_votos': 'sum',
        'nombre_candidato': 'count'
    }).reset_index()
    votos_totales_por_partido.columns = ['Partido', 'Total_Votos', 'Candidatos']

    if not votos_totales_por_partido.empty:
        fig_comparativa = px.bar(
            votos_totales_por_partido,
            x='Total_Votos',
            y='Partido',
            orientation='h',
            title=f'Total de Votos por Partido - {tipo_seleccionado} {año_seleccionado}',
            color='Partido',
            color_discrete_map=colores_map,
            text='Total_Votos',
            hover_data=['Candidatos']
        )
        fig_comparativa.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        fig_comparativa.update_traces(
            texttemplate='%{x:,}',
            textposition='outside'
        )
        st.plotly_chart(fig_comparativa, use_container_width=True)


    # TABLA DE DATOS
    st.subheader("📋 Lista de Candidatos")

    # Mostrar tabla simplificada con colores
    columnas_mostrar = ['nombre_candidato', 'partido_ci', 'division_territorial', 'numero_de_votos']
    st.dataframe(
        datos_filtrados[columnas_mostrar],
        use_container_width=True,
        height=300
    )

    # INFORMACIÓN ADICIONAL
    with st.expander("ℹ️ Información de colores"):
        st.write("""
        **Leyenda de colores:**
        - ⚠️ = Color asignado automáticamente (partido no en la paleta principal)
        - Los colores son consistentes entre 2021 y 2024
        - Partidos principales tienen colores oficiales
        """)

with tab2:
    st.markdown('<h1 class="main-title">🗺️ Análisis por División Territorial</h1>', unsafe_allow_html=True)

    st.write("Selecciona el año, tipo de elección y una división territorial específica para ver análisis detallados:")

    # Controles para la pestaña de divisiones territoriales
    col1, col2 = st.columns(2)

    with col1:
        año_divisiones = st.radio(
            "Año:",
            ['2021', '2024'],
            key="año_divisiones"
        )

    with col2:
        if año_divisiones == '2021':
            tipos_divisiones = ['GOBERNADOR', 'DIPUTADO', 'MUNICIPAL']
        else:
            tipos_divisiones = ['DIPUTADO', 'MUNICIPAL']

        tipo_divisiones = st.selectbox(
            "Tipo de elección:",
            tipos_divisiones,
            key="tipo_divisiones"
        )

    # Obtener las divisiones territoriales
    try:
        divisiones = dashboard.obtener_divisiones_territoriales(año_divisiones, tipo_divisiones)

        if divisiones:
            # Selector de división territorial
            division_seleccionada = st.selectbox(
                "Selecciona una división territorial:",
                divisiones,
                key="division_seleccionada"
            )

            # Obtener datos para la división seleccionada
            datos_division = dashboard.obtener_datos_por_division(
                año_divisiones,
                tipo_divisiones,
                division_seleccionada
            )

            if not datos_division.empty:
                st.success(f"📊 Análisis para: **{division_seleccionada}** - {tipo_divisiones} {año_divisiones}")

                # Obtener colores para los partidos en esta división
                colores_map_division = dashboard.obtener_colores_para_partidos(
                    datos_division['partido_ci'].unique(),
                    año_divisiones
                )

                # MÉTRICAS PARA LA DIVISIÓN SELECCIONADA
                st.subheader(f"📈 Métricas - {division_seleccionada}")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Candidatos", len(datos_division))

                with col2:
                    st.metric("Total Votos", f"{datos_division['numero_de_votos'].sum():,}")

                with col3:
                    st.metric("Partidos", datos_division['partido_ci'].nunique())

                with col4:
                    avg_votos = datos_division['numero_de_votos'].mean()
                    st.metric("Promedio Votos", f"{avg_votos:,.0f}")

                # GRÁFICO PRINCIPAL - TOP CANDIDATOS DE LA DIVISIÓN
                st.subheader(f"🏆 Candidatos - {division_seleccionada}")

                # Mostrar todos los candidatos de la división (no solo top 10)
                fig_division = px.bar(
                    datos_division,
                    x='numero_de_votos',
                    y='nombre_candidato',
                    orientation='h',
                    color='partido_ci',
                    title=f'Resultados en {division_seleccionada} - {tipo_divisiones} {año_divisiones}',
                    labels={'numero_de_votos': 'Votos', 'nombre_candidato': 'Candidato'},
                    color_discrete_map=colores_map_division
                )
                fig_division.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=True,
                    height=max(400, len(datos_division) * 30)  # Altura dinámica según cantidad de candidatos
                )
                fig_division.update_traces(
                    texttemplate='%{x:,}',
                    textposition='outside'
                )
                st.plotly_chart(fig_division, use_container_width=True)

                # GRÁFICOS DE DISTRIBUCIÓN POR PARTIDO
                st.subheader(f"📊 Distribución por Partido - {division_seleccionada}")

                col1, col2 = st.columns(2)

                with col1:
                    # Gráfico de torta - votos por partido
                    votos_por_partido_division = datos_division.groupby('partido_ci')[
                        'numero_de_votos'].sum().reset_index()

                    if not votos_por_partido_division.empty:
                        fig_torta_division = px.pie(
                            votos_por_partido_division,
                            values='numero_de_votos',
                            names='partido_ci',
                            title=f'Distribución de Votos - {division_seleccionada}',
                            color='partido_ci',
                            color_discrete_map=colores_map_division
                        )
                        fig_torta_division.update_traces(
                            textinfo='percent+label',
                            hovertemplate='<b>%{label}</b><br>Votos: %{value:,}<br>Porcentaje: %{percent}'
                        )
                        st.plotly_chart(fig_torta_division, use_container_width=True)

                with col2:
                    # Gráfico de barras - comparativa de partidos
                    if not votos_por_partido_division.empty:
                        fig_barras_division = px.bar(
                            votos_por_partido_division,
                            x='numero_de_votos',
                            y='partido_ci',
                            orientation='h',
                            title=f'Votos por Partido - {division_seleccionada}',
                            color='partido_ci',
                            color_discrete_map=colores_map_division,
                            text='numero_de_votos'
                        )
                        fig_barras_division.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            showlegend=False
                        )
                        fig_barras_division.update_traces(
                            texttemplate='%{x:,}',
                            textposition='outside'
                        )
                        st.plotly_chart(fig_barras_division, use_container_width=True)

                # TABLA DETALLADA DE CANDIDATOS CON COLORES
                st.subheader(f"📋 Detalle de Candidatos - {division_seleccionada}")

                # Crear una tabla con colores en el sidebar para referencia
                with st.expander("🎨 Referencia de colores de partidos"):
                    partidos_division = datos_division['partido_ci'].unique()
                    for partido in partidos_division:
                        color = colores_map_division.get(partido, '#CCCCCC')
                        estilo_texto = "color: black;" if color in ['#FFDE00', '#FFFF99',
                                                                    '#FFD100'] else "color: white;"
                        st.markdown(
                            f"<div style='background-color: {color}; padding: 8px; margin: 3px; border-radius: 5px; {estilo_texto}'>"
                            f"<strong>{partido}</strong></div>",
                            unsafe_allow_html=True
                        )

                # Mostrar tabla con los datos
                columnas_mostrar_division = ['nombre_candidato', 'partido_ci', 'numero_de_votos']
                st.dataframe(
                    datos_division[columnas_mostrar_division],
                    use_container_width=True,
                    height=400
                )

                # Botón de descarga para los datos de la división
                csv_division = datos_division[columnas_mostrar_division].to_csv(index=False)
                st.download_button(
                    label="📥 Descargar datos de esta división",
                    data=csv_division,
                    file_name=f"resultados_{division_seleccionada}_{año_divisiones}_{tipo_divisiones}.csv",
                    mime="text/csv"
                )

            else:
                st.warning(f"No se encontraron datos para la división territorial: {division_seleccionada}")

        else:
            st.warning("No se encontraron divisiones territoriales para los criterios seleccionados")

    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")

with tab3:
    st.markdown('<h1 class="main-title">🏆 Zonas Ganadas por Partido</h1>', unsafe_allow_html=True)

    st.write("Analiza en qué divisiones territoriales ganó cada partido político:")

    # Controles para la pestaña de zonas ganadas
    col1, col2 = st.columns(2)

    with col1:
        año_zonas = st.radio(
            "Año:",
            ['2021', '2024'],
            key="año_zonas"
        )

    with col2:
        if año_zonas == '2021':
            tipos_zonas = ['GOBERNADOR', 'DIPUTADO', 'MUNICIPAL']
        else:
            tipos_zonas = ['DIPUTADO', 'MUNICIPAL']

        tipo_zonas = st.selectbox(
            "Tipo de elección:",
            tipos_zonas,
            key="tipo_zonas"
        )

    try:
        # Obtener resumen de zonas ganadas por partido
        zonas_ganadas = dashboard.obtener_zonas_ganadas_por_partido(año_zonas, tipo_zonas)

        if not zonas_ganadas.empty:
            st.success(f"📈 Resumen de zonas ganadas - {tipo_zonas} {año_zonas}")

            # MÉTRICAS PRINCIPALES
            total_zonas = zonas_ganadas['Zonas_Ganadas'].sum()
            partido_mas_zonas = zonas_ganadas.iloc[0]['Partido']
            zonas_mas_ganadas = zonas_ganadas.iloc[0]['Zonas_Ganadas']

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total de Zonas", total_zonas)

            with col2:
                st.metric("Partidos con Zonas", len(zonas_ganadas))

            with col3:
                st.metric("Partido con Más Zonas", f"{partido_mas_zonas} ({zonas_mas_ganadas})")

            # GRÁFICO DE ZONAS GANADAS POR PARTIDO
            st.subheader("📊 Distribución de Zonas Ganadas por Partido")

            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de barras
                fig_zonas = px.bar(
                    zonas_ganadas,
                    x='Zonas_Ganadas',
                    y='Partido',
                    orientation='h',
                    color='Partido',
                    title=f'Zonas Ganadas por Partido - {tipo_zonas} {año_zonas}',
                    color_discrete_map=dashboard.obtener_colores_para_partidos(zonas_ganadas['Partido'].tolist(),
                                                                               año_zonas),
                    text='Zonas_Ganadas'
                )
                fig_zonas.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=False,
                    height=400
                )
                fig_zonas.update_traces(
                    texttemplate='%{x} zonas',
                    textposition='outside'
                )
                st.plotly_chart(fig_zonas, use_container_width=True)

            with col2:
                # Gráfico de torta
                fig_torta_zonas = px.pie(
                    zonas_ganadas,
                    values='Zonas_Ganadas',
                    names='Partido',
                    title=f'Porcentaje de Zonas Ganadas - {tipo_zonas} {año_zonas}',
                    color='Partido',
                    color_discrete_map=dashboard.obtener_colores_para_partidos(zonas_ganadas['Partido'].tolist(),
                                                                               año_zonas)
                )
                fig_torta_zonas.update_traces(
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Zonas: %{value}<br>Porcentaje: %{percent}'
                )
                st.plotly_chart(fig_torta_zonas, use_container_width=True)

            # TABLA RESUMEN
            st.subheader("📋 Resumen por Partido")

            # Calcular porcentajes
            zonas_ganadas['Porcentaje_Zonas'] = (zonas_ganadas['Zonas_Ganadas'] / total_zonas * 100).round(1)
            zonas_ganadas['Porcentaje_Zonas'] = zonas_ganadas['Porcentaje_Zonas'].astype(str) + '%'

            st.dataframe(
                zonas_ganadas[['Partido', 'Zonas_Ganadas', 'Porcentaje_Zonas', 'Total_Votos_Ganadores']],
                use_container_width=True,
                column_config={
                    'Partido': 'Partido',
                    'Zonas_Ganadas': 'Zonas Ganadas',
                    'Porcentaje_Zonas': '% del Total',
                    'Total_Votos_Ganadores': 'Votos de Ganadores'
                }
            )

            # SELECTOR PARA VER DETALLE POR PARTIDO
            st.subheader("🔍 Detalle de Zonas por Partido")

            partidos_con_zonas = zonas_ganadas['Partido'].tolist()
            partido_detalle = st.selectbox(
                "Selecciona un partido para ver en qué zonas ganó:",
                partidos_con_zonas,
                key="partido_detalle"
            )

            # Obtener detalle de zonas ganadas por el partido seleccionado
            detalle_zonas = dashboard.obtener_detalle_zonas_ganadas(año_zonas, tipo_zonas, partido_detalle)

            if not detalle_zonas.empty:
                st.success(f"**{partido_detalle}** ganó en {len(detalle_zonas)} zonas:")

                # Mostrar las zonas en cards con colores
                num_columnas = 3
                cols = st.columns(num_columnas)

                for i, (_, zona) in enumerate(detalle_zonas.iterrows()):
                    with cols[i % num_columnas]:
                        color_partido = COLORES_PARTIDOS.get(partido_detalle, COLORES_POR_DEFECTO[0])
                        st.markdown(
                            f"""
                            <div class="winner-card" style="border-left-color: {color_partido}">
                                <h4>{zona['division_territorial']}</h4>
                                <p><strong>Ganador:</strong> {zona['nombre_candidato']}</p>
                                <p><strong>Votos:</strong> {zona['numero_de_votos']:,}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                # Tabla detallada expandible
                with st.expander("📋 Ver tabla detallada"):
                    st.dataframe(
                        detalle_zonas[['division_territorial', 'nombre_candidato', 'numero_de_votos']],
                        use_container_width=True,
                        column_config={
                            'division_territorial': 'División Territorial',
                            'nombre_candidato': 'Candidato Ganador',
                            'numero_de_votos': 'Votos Obtenidos'
                        }
                    )

                    # Botón de descarga
                    csv_detalle = detalle_zonas[['division_territorial', 'nombre_candidato', 'numero_de_votos']].to_csv(
                        index=False)
                    st.download_button(
                        label=f"📥 Descargar zonas de {partido_detalle}",
                        data=csv_detalle,
                        file_name=f"zonas_ganadas_{partido_detalle}_{año_zonas}_{tipo_zonas}.csv",
                        mime="text/csv"
                    )
            else:
                st.info(f"El partido {partido_detalle} no ganó en ninguna zona con los criterios seleccionados")

        else:
            st.warning("No se encontraron datos de zonas ganadas para los criterios seleccionados")

    except Exception as e:
        st.error(f"Error al cargar los datos de zonas ganadas: {str(e)}")

# FOOTER SIMPLE
st.markdown("---")
st.caption(f"Dashboard de Elecciones NL | Datos actualizados | Colores consistentes 2021-2024")