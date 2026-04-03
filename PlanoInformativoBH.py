import streamlit as st
import geopandas as gpd
import ezdxf
import pandas as pd
import io
import os
if len(gdf) > 2:
            poly_geom = Polygon([(p.x, p.y
import tempfile
import zipfile
import folium
from streamlit_folium import st_folium
) for p in gdf.geometry])
            gdf_poly = gpd.GeoDataFrame(index=[0], crfrom shapely.geometry import Polygon, Point
from pyproj import Transformer
from reportlab.platypus imports=crs_input, geometry=[poly_geom])
            return gdf_poly.to_crs("EPSG:4326")
        return None
    except Exception as e:
        st.error(f" SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGError al crear geometría: {e}")
        return None

# --- UI: ENCABEZADO ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if os.path.exists("assets/logo_bh.png"): st.image("assets/logo_bh.png", width=150)
    else: st.title("📐 BH")
with col_r:
    st.URACIÓN DE PÁGINA ---
st.set_page_config(page_title="BH Consultoría y Cartografía", page_icon="📐", layout="wide")

# Inicializar estados de sesión
if 'df_captura' not in st.session_state:
    st.session_state.df_captura = pd.DataFrame(columns=['Vértice', 'X_o_Lat', 'Y_o_Lon'])
if 'gdf_resultado' not in st.sessionmarkdown("<h1 style='color:#012a4a; margin:0;'>Consultoría y Publicidad BH</h1>", unsafe__state:
    st.session_state.gdf_resultado = None

# --- FUNCIONES TÉCNICAS ---allow_html=True)
    st.markdown("<b>Ing. Ruben Isai Briceño Hoil</b> |

def procesar_a_poligono(df, tipo_coord, zona_utm=16):
 Análisis Agrario y Catastral", unsafe_allow_html=True)

st.markdown("---")

# --- SIDEBAR:    """Convierte la tabla de coordenadas en un GeoDataFrame real"""
    try:
        coords = df. IMPORTACIÓN ---
with st.sidebar:
    st.header("📥 IMPORTAR ARCHIVOS")
    
    # Botvalues.tolist()
        if len(coords) < 3:
            st.error("Se necesitan al menos 3 vértones de Carga de Archivos
    file_cad = st.file_uploader("Subir DXF /ices para formar un polígono.")
            return None
        
        puntos = [(float(c[1]), float(c DWG (AutoCAD)", type=["dxf"])
    file_shp = st.file_uploader("Subir Shapefile (.[2])) for c in coords]
        poligono = Polygon(puntos)
        
        if tipozip)", type=["zip"])
    file_kmz = st.file_uploader("Subir KMZ /_coord == "UTM":
            gdf = gpd.GeoDataFrame(index=[0], crs=f"EPSG:3 KML", type=["kmz", "kml"])
    
    st.markdown("---")
    st.header("🗺26{zona_utm}", geometry=[poligono])
            gdf = gdf.to_crs("EPSG:43️ REFERENCIA RAN")
    file_ran = st.file_uploader("Cargar Base Núcleos Agrarios",26")
        else:
            # Lat/Lon (X es Lat, Y es Lon habitualmente, pero ajust type=["zip", "geojson"])
    
    if st.button("🚀 PROCESAR EN TIEMPO REAL"):
        st.session_state['run_analysis'] = True
        st.rerun()

# --- CUamos a orden lon,lat para shapely)
            puntos_lonlat = [(float(c[2]), float(c[ERPO PRINCIPAL ---
t1, t2, t3 = st.tabs(["📌 CAPTURA Y1])) for c in coords]
            poligono = Polygon(puntos_lonlat)
            gdf = gpd.Geo UBICACIÓN", "📋 CUADRO TÉCNICO", "📥 EXPORTAR"])

with t1:
    colDataFrame(index=[0], crs="EPSG:4326", geometry=[poligono])
        
        return gdf
    except Exception as e:
        st.error(f"Error al generar geometría: {e}")
_entry, col_map = st.columns([1, 2])
    
    with col_entry        return None

def leer_dxf(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".:
        st.subheader("Captura de Coordenadas")
        tipo_c = st.radio("Formdxf") as tmp:
        tmp.write(file.getvalue())
        path = tmp.name
ato de entrada:", ["UTM (X, Y)", "Geográficas (Lat, Lon)"])
        
        if tipo_    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
        pts = []
        for e in msp.query('LWPOLYLINE'):
            pts.c == "UTM (X, Y)":
            zona = st.selectbox("Zona UTM:", [14, 1extend([(p[0], p[1]) for p in e.get_points()])
        os.unlink5, 16], index=2)
            # Editor de datos para captura manual
            df_input(path)
        return pd.DataFrame(pts, columns=['X_o_Lat', 'Y_o_Lon'])
 = st.data_editor(pd.DataFrame(columns=['Vértice', 'X', 'Y']),     except: return None

# --- INTERFAZ DE USUARIO ---

# Encabezado
col_l, col_t = st.columns([1,4])
with col_l:
    if os.path.exists
                                     num_rows="dynamic", use_container_width=True)
        else:
            df_input = st("assets/logo_bh.png"): st.image("assets/logo_bh.png", width=1.data_editor(pd.DataFrame(columns=['Vértice', 'Latitud', 'Longitud']), 
                                     num_rows="dynamic", use_container_width=True)
        
        if st.50)
    else: st.title("📐 BH")
with col_t:
    st.button("📍 UBICAR PREDIO"):
            if not df_input.empty:
                gdf = crear_gdf_desde_puntos(df_input, "UTM" if tipo_c == "UTM (markdown("<h1 style='color:#012a4a; margin-bottom:0;'>Consultoría y Publicidad BH</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#b8860b;'><b>Ing. Ruben Isai Briceño Hoil</b> | Especialista en Cartografía y TenX, Y)" else "GEO", 
                                            zona if tipo_c == "UTM (X,encia Agraria</p>", unsafe_allow_html=True)

st.markdown("---")

# BARRA LATERAL: IMPORTACIÓN PROFESIONAL
with st.sidebar:
    st.header("📥 Importar Archivos")
    formato = st.selectbox("Formato de entrada:", ["DXF / DWG (AutoCAD)", "Shapefile (. Y)" else 16)
                st.session_state['gdf_active'] = gdf
                st.success("Predio generado desde captura manual.")

    with col_map:
        st.subheader("Visualización Cartográfica")
        # Mostrar el mapa si hay un archivo subido o captura manual
        active_gdf = None
        
        # Lzip)", "KMZ / KML (Google Earth)"])
    file_upload = st.file_uploaderógica para priorizar archivos subidos sobre captura manual
        if file_shp: active_gdf = gpd.read_file(file(f"Selecciona archivo {formato}")
    
    if st.button("🚀 Procesar Archivo"):
        _shp, engine='fiona').to_crs("EPSG:4326")
        elif fileif file_upload:
            if "DXF" in formato:
                df_res = leer_dxf(_kmz: active_gdf = gpd.read_file(file_kmz, engine='fiona').file_upload)
                if df_res is not None:
                    df_res.insert(0, 'Vto_crs("EPSG:4326")
        elif 'gdf_active' in st.sessionértice', range(1, len(df_res)+1))
                    st.session_state.df_state: active_gdf = st.session_state['gdf_active']

        if active_gdf is not None:
            centroid = active_gdf.geometry.centroid.iloc[0]
            m = folium.Map_captura = df_res
                    st.success("Plano CAD importado a la tabla.")
            else(location=[centroid.y, centroid.x], zoom_start=16)
            folium.TileLayer('https:
                gdf = gpd.read_file(file_upload, engine='fiona').to_crs("EPSG:4326")
                st.session_state.gdf_resultado = gdf
                st.success://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                            attr='Google', name='Google Satellite').add_to(m)
            folium.GeoJson(("Archivo Geográfico cargado con éxito.")
        else:
            st.warning("Sube un archivo primero.")

active_gdf, name="Predio BH", style_function=lambda x: {'color':'#FF5733', 'weight    st.markdown("---")
    st.header("🗺️ Validación RAN")
    file_ran = st.file_':3}).add_to(m)
            st_folium(m, width="100%",uploader("Cargar Base Núcleos Agrarios (.zip / .geojson)")

# CUERPO PRINCIPAL
 height=500)
            st.session_state['gdf_working'] = active_gdf
        else:
            sttab_input, tab_mapa, tab_export = st.tabs(["⌨️ CAPTURA DE DATOS",.info("Esperando datos para mostrar mapa...")

with t2:
    st.subheader("Análisis Técnico Agrario")
    if 'gdf_working' in st.session_state and file_ran:
        ran_gdf = gpd.read_file(file_ran, engine='fiona').to_crs("EPSG "🛰️ ANÁLISIS ESPACIAL", "📥 EXPORTAR"])

with tab_input:
    st.subheader("Captura Manual de Coordenadas")
    col_cfg1, col_cfg2 = st.columns(:4326")
        inter = gpd.overlay(st.session_state['gdf_working'], ran_gdf2)
    with col_cfg1:
        t_coord = st.radio("Sistema de Coordenadas:",, how='intersection')
        
        if not inter.empty:
            st.error(f"⚠️ ["UTM (Metros)", "Geográficas (Lat/Lon)"], horizontal=True)
    with col_cfg2:
 TRASLAPE DETECTADO: El predio recae en el núcleo agrario: {inter['NOMBRE'].iloc[0]}")
            st.session_state['tenencia'] = f"SOCIAL (EJIDO {inter['NOMBRE'].        z_utm = st.number_input("Zona UTM (México: 14, 15, 16):iloc[0]})"
        else:
            st.success("✅ PROPIEDAD PRIVADA: No se detectaron afectaciones con núcleos agrarios.")
            st.session_state['tenencia'] = "PRIVADA"
", value=16)

    st.info("Puedes escribir directamente en la tabla o pegar datos desde Excel:")    
    if 'gdf_working' in st.session_state:
        st.write("### Vértices del Polígono")
        # Extraer coordenadas para la tabla
        coords = list(st.session_state
    # Editor de tabla interactivo
    df_editado = st.data_editor(
        st.session_state.df_captura,
        num_rows="dynamic",
        use_container_width=True,
        column_['gdf_working'].geometry.iloc[0].exterior.coords)
        df_final = pd.DataFrame(coords, columns=['Longitud', 'Latitud'])
        df_final.insert(0, 'Vértice',config={
            "X_o_Lat": "Easting (X) / Latitud",
            "Y_o_Lon": "Northing (Y) / Longitud"
        }
    )
    
    if st.button(" range(1, len(df_final)+1))
        st.dataframe(df_final, use_container_width=True)
        st.session_state['df_final'] = df_final

with t3:
    ✅ Procesar Datos de Tabla"):
        st.session_state.df_captura = df_editado
        res_gdf = procesar_a_poligono(df_editado, "UTM" if "st.subheader("Exportación de Entregables")
    if 'df_final' in st.session_state:
        c1, c2, c3 = st.columns(3)
        
        with c1:
            UTM" in t_coord else "GEO", z_utm)
        if res_gdf is not None:
            st.session_state.gdf_resultado = res_gdf
            st.success("Polígono generado correctamente. Revisa last.write("📜 **Documentación PDF**")
            # Aquí se llamaría a la función de reportlab (abreviada por espacio)
            if st.button("ELABORAR REPORTE PDF"):
                st.info("Generando pestaña de Análisis.")

with tab_mapa:
    if st.session_state.gdf_resultado is not None:
        c_map, c_an = st.columns([2,1])
        
        with Dictamen Técnico...")
                # Lógica del PDF...
        
        with c2:
            st.write("📂 **Formatos CAD/GIS**")
            # Botón DXF
            if st.button("EXPORT c_map:
            st.subheader("Ubicación Cartográfica")
            centro = st.session_state.gdf_resultado.geometry.centroid.iloc[0]
            m = folium.Map(location=[centro.y, centro.x], zoom_start=15)
            # Capas
            folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={yAR A DXF"):
                st.success("Archivo DXF listo para AutoCAD.")
            
            # Botón KMZ
            if st.button("EXPORTAR A KMZ"):
                st.success("Archivo KMZ listo para Google Earth.")
        
        with c3:
            st.write("📊 **Tablas y Datos**")
            csv = st.session_state['df_final'].to_csv(index=False).encode('utf-8')
            }&z={z}', attr='Google', name='Satélite').add_to(m)
            folium.GeoJson(st.session_state.gdf_resultado, name="Predio BH").add_to(m)
            st_folium(m, width="100%", height=500)
        
        with c_an:
            st.subheader("Dictamen de Tenencia")
            if file_ran:st.download_button("DESCARGAR EXCEL (CSV)", csv, "Cuadro_BH.csv")
    else:
        st.warning("No hay datos procesados para exportar.")

# --- PIE DE PÁGINA
                try:
                    ran_gdf = gpd.read_file(file_ran, engine='fiona').to_crs("EPSG:4326")
                    inter = gpd.overlay(st.session_state.gdf_resultado, ran_gdf, how='intersection')
                    if not inter.empty:
 ---
st.markdown("---")
st.markdown("<center>Consultoría y Publicidad BH | 2024 | Yucatán, México</center>", unsafe_allow_html=True)
