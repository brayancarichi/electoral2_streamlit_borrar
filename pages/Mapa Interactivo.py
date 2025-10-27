import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import pandas as pd

st.set_page_config(page_title="Mapa MC", layout="wide")
st.title("🗳️ Mapa Interactivo de Municipios - Partido MC")

# Cargar shapefile
ruta_shapefile = "Shapes/resultados.shp"
gdf = gpd.read_file(ruta_shapefile)

# Convertir votos a numérico y porcentaje a float
gdf['numero_de_'] = pd.to_numeric(
    gdf['numero_de_'].astype(str).str.replace(',', '').str.strip(),
    errors='coerce'
).fillna(0).astype(int)

gdf['Porcentaje'] = pd.to_numeric(
    gdf['Porcentaje'].astype(str).str.replace('%','').str.strip(),
    errors='coerce'
).fillna(0)

gdf["PARTIDO_CI"] = gdf["PARTIDO_CI"].astype(str)
gdf["es_MC"] = gdf["PARTIDO_CI"].str.upper() == "MC"

# Centrar mapa
centro = gdf.geometry.centroid.unary_union.centroid
m = folium.Map(location=[centro.y, centro.x], zoom_start=6, tiles="cartodb positron")

# Crear polígonos y popups con mini-barras
for _, row in gdf.iterrows():
    color = "#FF7F00" if row["es_MC"] else "gray"
    fill_color = color if row["es_MC"] else "transparent"
    fill_opacity = 0.8 if row["es_MC"] else 0.2

    porcentaje = row.get("Porcentaje", 0)
    bar_html = f"""
    <div style="background-color: lightgray; width: 100px; height: 10px; border-radius: 3px;">
        <div style="width: {porcentaje}%; height: 100%; background-color: #FF7F00; border-radius: 3px;"></div>
    </div>
    """

    popup_html = f"""
    <div style="font-family:sans-serif; font-size:14px;">
        <b>Municipio:</b> {row['NOMGEO']}<br>
        <b>Estado:</b> {row['NOM_ENT']}<br>
        <b>Candidato:</b> {row['nombre_can']}<br>
        <b>Partido:</b> {row['PARTIDO_CI']}<br>
        <b>Votos:</b> {row['numero_de_']:,}<br>
        <b>Porcentaje:</b> {porcentaje}%<br>
        {bar_html}
    </div>
    """

    popup = folium.Popup(popup_html, max_width=250)

    folium.GeoJson(
        row["geometry"],
        style_function=lambda feature, color=color, fill_color=fill_color, fill_opacity=fill_opacity: {
            "color": color,
            "fillColor": fill_color,
            "weight": 1.5,
            "fillOpacity": fill_opacity,
        },
        popup=popup
    ).add_to(m)

st_folium(m, width=1300, height=600)

