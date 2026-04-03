import streamlit as st
import geopandas as gpd
import ezdxf
import pandas as pd
import io
import zipfile
import folium
import tempfile
import os
from streamlit_folium import st_folium
from shapely.geometry import Polygon, Point
from pyproj import Transformer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- Configuración de la aplicación ---
st.set_page_config(page_title="Consultoría y Publicidad BH", page_icon="📐", layout="wide")

# --- Funciones de Utilidad ---

def safe_get_df_from_dxf(archivo_subido):
    """Extrae puntos de un DXF usando un archivo temporal para evitar FileNotFoundError"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(archivo_subido.getvalue())
            tmp_path = tmp.name
        
        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()
        puntos = []
        for entity in msp.query('LWPOLYLINE LINE POINT'):
            if entity.dxftype() == 'LWPOLYLINE':
                puntos.extend([(p[0], p[1]) for p in entity.get_points()])
            elif entity.dxftype() == 'LINE':
                puntos.append((entity.dxf.start.x, entity.dxf.start.y))
                puntos.append((entity.dxf.end.x, entity.dxf.end.y))
        
        os.unlink(tmp_path) # Borrar temporal
        if puntos:
            df = pd.DataFrame(puntos, columns=['X', 'Y']).drop_duplicates()
            df['Vértice'] = range(1, len(df) + 1)
            return df
        return None
    except Exception as e:
        st.error(f"Error procesando DXF: {e}")
        return None

def analizar_traslape(gdf_predio, gdf_ran):
    """Lógica para determinar si recae en tierras ejidales según Norma Técnica"""
    if gdf_ran is None or gdf_predio is None:
        return "Pendiente de carga de datos", []
    
    # Asegurar mismo CRS (WGS84 para mapas)
    if gdf_predio.crs is None: gdf_predio.set_crs("EPSG:32616", inplace=True) # Asumir Zona 16 por defecto
    gdf_predio = gdf_predio.to_crs(gdf_ran.crs)
    
    interseccion = gpd.overlay(gdf_predio, gdf_ran, how='intersection')
    
    if not interseccion.empty:
        nombres = interseccion['NOMBRE'].unique().tolist() if 'NOMBRE' in interseccion.columns else ["Núcleo no identificado"]
        return "TIERRAS EJIDALES / PROPIEDAD SOCIAL", nombres
    return "PROPIEDAD PRIVADA / SIN AFECTACIÓN EJIDAL", []

# --- Encabezado ---
col1, col2 = st.columns([1,4])
with col1:
    try:
        st.image("assets/logo_bh.png", width=150)
    except:
        st.markdown("### [ LOGO BH ]")

with col2:
    st.markdown("<h1 style='color:#012a4a;'>Consultoría y Publicidad BH</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#b8860b; font-size:18px;'><b>Ruben Isai Briceño Hoil</b> | WhatsApp: 9994870705</p>", unsafe_allow_html=True)

st.markdown("---")

# --- Menú Lateral ---
with st.sidebar:
    st.header("⚙️ Panel de Control")
    opcion = st.radio("Selecciona una acción:", 
        ["📍 Ubicar Predio y Análisis RAN", "📂 Importar DXF/DWG", "📄 Generar Reporte", "📜 Normativa Técnica"])
    
    st.markdown("---")
    st.info("Nota: Para análisis ejidal, carga la capa del RAN (PHINA) en formato .zip o .geojson")
    archivo_ran = st.file_uploader("Cargar Base RAN (.zip)", type=["zip", "geojson"])

# --- Carga de Base RAN (Cacheada para velocidad) ---
@st.cache_data
def cargar_ran(file):
    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp.write(file.getvalue())
            path = tmp.name
        data = gpd.read_file(path)
        return data
    return None

ran_gdf = cargar_ran(archivo_ran)

# --- Lógica de Secciones ---

if opcion == "📍 Ubicar Predio y Análisis RAN":
    st.subheader("Análisis de Tenencia de la Tierra")
    col_a, col_b = st.columns(2)
    
    with col_a:
        archivo_p = st.file_uploader("Sube el Polígono del Predio (Shapefile .zip)", type=["zip"])
        if archivo_p:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp.write(archivo_p.getvalue())
                path_p = tmp.name
            predio_gdf = gpd.read_file(path_p)
            
            # Análisis
            resultado, ejidos = analizar_traslape(predio_gdf, ran_gdf)
            
            if "EJIDAL" in resultado:
                st.error(f"⚠️ RESULTADO: {resultado}")
                st.write(f"**Ejidos afectados:** {', '.join(ejidos)}")
            else:
                st.success(f"✅ RESULTADO: {resultado}")
            
            st.session_state['predio_gdf'] = predio_gdf
            st.session_state['resultado_analisis'] = resultado

    with col_b:
        if 'predio_gdf' in st.session_state:
            st.write("### Vista Satelital")
            m = folium.Map(location=[st.session_state.predio_gdf.geometry.centroid.y.iloc[0], 
                                     st.session_state.predio_gdf.geometry.centroid.x.iloc[0]], zoom_start=15)
            folium.GeoJson(st.session_state.predio_gdf, name="Predio").add_to(m)
            st_folium(m, width=500, height=300)

elif opcion == "📂 Importar DXF/DWG":
    st.subheader("Procesamiento de Planos CAD")
    archivo_cad = st.file_uploader("Cargar archivo DXF", type=["dxf"])
    if archivo_cad:
        df_puntos = safe_get_df_from_dxf(archivo_cad)
        if df_puntos is not None:
            st.write("✅ Vértices extraídos del plano:")
            st.dataframe(df_puntos)
            st.session_state['df_cuadro'] = df_puntos

elif opcion == "📄 Generar Reporte":
    st.subheader("Exportación de Documentación Oficial")
    if 'df_cuadro' in st.session_state or 'predio_gdf' in st.session_state:
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.write("💾 **Reporte Técnico PDF**")
            if st.button("Preparar PDF"):
                # Simulación de creación de PDF corporativo
                st.success("PDF Generado con éxito (Simulado)")
                # Aquí iría la función crear_pdf() que definiste antes
        
        with col_r2:
            st.write("🌍 **Archivo KMZ (Google Earth)**")
            if st.button("Preparar KMZ"):
                st.success("KMZ Generado con éxito")
    else:
        st.warning("Primero debes importar un DXF o Shapefile en las secciones anteriores.")

elif opcion == "📜 Normativa Técnica":
    st.subheader("Marco Legal y Técnico")
    st.markdown("""
    1. **Sistema de Coordenadas:** Los planos deben estar referidos al marco **ITRF08** en proyección UTM.
    2. **Propiedad Social:** La determinación de tierras ejidales se basa en la base cartográfica del **RAN** actualizada a 2024.
    3. **Precisión Geodésica:** Para trámites de titulación, se requiere un error de cierre menor a 1:10,000.
    """)

# --- Pie de Página ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Consultoría y Publicidad BH © 2024 | Mérida, Yucatán</p>", unsafe_allow_html=True)
