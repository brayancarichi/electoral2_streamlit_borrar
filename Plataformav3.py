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

# INFORMACIÓN ADICIONAL
with st.expander("ℹ️ Información de colores"):
    st.write("""
    **Leyenda de colores:**
    - ⚠️ = Color asignado automáticamente (partido no en la paleta principal)
    - Los colores son consistentes entre 2021 y 2024
    - Partidos principales tienen colores oficiales
    """)

# FOOTER SIMPLE
st.markdown("---")
st.caption(f"Dashboard de Elecciones NL - {año_seleccionado} | Datos actualizados | Colores consistentes 2021-2024")