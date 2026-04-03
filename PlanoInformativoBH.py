import streamlit as st
import geopandas as gpd
import ezdxf
import pandas as pd
import io
import os
import tempfile
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon, Point
from pyproj import Transformer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- Configuración de la aplicación ---
st.set_page_config(page_title="Consultoría y Publicidad BH", page_icon="📐", layout="wide")

# --- Funciones de Procesamiento Geoespacial ---

@st.cache_data
def cargar_base_ran(file):
    """Carga la base de datos del RAN (PHINA) usando el motor fiona para evitar errores"""
    if file is not None:
        try:
            # Leemos directamente del buffer usando fiona
            gdf = gpd.read_file(file, engine='fiona')
            # Estandarizar a WGS84
            if gdf.crs is None:
                gdf.set_crs("EPSG:4326", inplace=True)
            else:
                gdf = gdf.to_crs("EPSG:4326")
            return gdf
        except Exception as e:
            st.error(f"Error al cargar base RAN: {e}")
    return None

def procesar_predio_usuario(file):
    """Procesa el archivo .zip o .geojson del usuario"""
    try:
        gdf = gpd.read_file(file, engine='fiona')
        # Normalizar coordenadas a WGS84 para el mapa
        if gdf.crs is None:
            gdf.set_crs("EPSG:32616", inplace=True) # Asumir Zona 16N si no tiene
        gdf = gdf.to_crs("EPSG:4326")
        return gdf
    except Exception as e:
        st.error(f"Error al procesar predio: {e}")
        return None

def extraer_vertices_dxf(file):
    """Extrae coordenadas de un DXF usando un archivo temporal seguro"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        
        doc = ezdxf.readfile(tmp_path)
        msp = doc.modelspace()
        puntos = []
        for e in msp.query('LWPOLYLINE LINE'):
            if e.dxftype() == 'LWPOLYLINE':
                puntos.extend([(p[0], p[1]) for p in e.get_points()])
            elif e.dxftype() == 'LINE':
                puntos.append((e.dxf.start.x, e.dxf.start.y))
                puntos.append((e.dxf.end.x, e.dxf.end.y))
        
        os.unlink(tmp_path) # Limpieza
        if puntos:
            df = pd.DataFrame(puntos, columns=['X', 'Y']).drop_duplicates()
            df.insert(0, 'Vértice', range(1, len(df) + 1))
            return df
        return None
    except Exception as e:
        st.error(f"Error en DXF: {e}")
        return None

# --- Interfaz de Usuario (UI) ---

# Encabezado Corporativo
col1, col2 = st.columns([1,4])
with col1:
    if os.path.exists("assets/logo_bh.png"):
        st.image("assets/logo_bh.png", width=150)
    else:
        st.markdown("### 📐 BH")

with col2:
    st.markdown("<h1 style='color:#012a4a; margin-bottom:0;'>Consultoría y Publicidad BH</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#b8860b; margin-top:0;'>Dictaminación Técnica y Cartográfica</h3>", unsafe_allow_html=True)
    st.caption("Ing. Ruben Isai Briceño Hoil | WhatsApp: 9994870705 | Mérida, Yucatán")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Panel de Control")
    opcion = st.radio("Seleccione Acción:", 
        ["Análisis de Tenencia (RAN)", "Importar Plano CAD", "Generar Documentación"])
    
    st.markdown("---")
    st.subheader("Carga de Datos Maestros")
    archivo_ran = st.file_uploader("Base de Datos RAN (.zip / .geojson)", type=["zip", "geojson"])
    ran_gdf = cargar_base_ran(archivo_ran)
    if ran_gdf is not None:
        st.success("✅ Base RAN lista")

# --- Lógica de Secciones ---

if opcion == "Análisis de Tenencia (RAN)":
    st.subheader("🛰️ Ubicación de Predio y Verificación de Tenencia")
    st.info("Sube el polígono de tu predio para verificar traslapes con la propiedad social (Ejidos).")
    
    archivo_p = st.file_uploader("Sube Polígono del Predio (.zip / .geojson)", type=["zip", "geojson"])
    
    if archivo_p:
        predio_gdf = procesar_predio_usuario(archivo_p)
        
        if predio_gdf is not None:
            # Análisis de Intersección
            if ran_gdf is not None:
                interseccion = gpd.overlay(predio_gdf, ran_gdf, how='intersection')
                
                if not interseccion.empty:
                    ejidos = interseccion['NOMBRE'].unique()
                    st.error(f"⚠️ EL PREDIO RECAE EN PROPIEDAD SOCIAL (EJIDAL).")
                    st.write(f"**Núcleos afectados:** {', '.join(ejidos)}")
                    st.session_state['status_tenencia'] = f"SOCIAL (Ejido: {', '.join(ejidos)})"
                else:
                    st.success("✅ EL PREDIO SE UBICA EN PROPIEDAD PRIVADA / SIN AFECTACIÓN.")
                    st.session_state['status_tenencia'] = "PRIVADA"
            else:
                st.warning("Carga la base del RAN en el menú lateral para realizar la validación técnica.")

            # Mapa Folium
            m = folium.Map(location=[predio_gdf.geometry.centroid.y.iloc[0], 
                                     predio_gdf.geometry.centroid.x.iloc[0]], zoom_start=15)
            folium.TileLayer('openstreetmap').add_to(m)
            folium.GeoJson(predio_gdf, name="Predio", style_function=lambda x: {'color':'blue', 'fillOpacity':0.5}).add_to(m)
            
            st_folium(m, width="100%", height=400)
            st.session_state['predio_gdf'] = predio_gdf

elif opcion == "Importar Plano CAD":
    st.subheader("📂 Extracción de Coordenadas de DXF")
    archivo_cad = st.file_uploader("Sube tu archivo DXF", type=["dxf"])
    
    if archivo_cad:
        df_coords = extraer_vertices_dxf(archivo_cad)
        if df_coords is not None:
            st.write("### Cuadro de Construcción (Vértices detectados)")
            st.dataframe(df_coords, use_container_width=True)
            st.session_state['df_coords'] = df_coords
            
            # Botón para descargar Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_coords.to_excel(writer, index=False, sheet_name='Coordenadas')
            st.download_button("Descargar Excel de Vértices", output.getvalue(), "Cuadro_Tecnico.xlsx")

elif opcion == "Generar Documentación":
    st.subheader("📄 Reportes y Dictámenes")
    
    if 'status_tenencia' in st.session_state:
        st.write(f"**Estado detectado:** {st.session_state['status_tenencia']}")
        
        # Función simple para crear PDF
        def generar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = [
                Paragraph("DICTAMEN TÉCNICO GEOGRÁFICO", styles['Title']),
                Spacer(1, 12),
                Paragraph(f"<b>Responsable:</b> Ruben Isai Briceño Hoil", styles['Normal']),
                Paragraph(f"<b>Estatus de Tenencia:</b> {st.session_state['status_tenencia']}", styles['Normal']),
                Spacer(1, 20),
                Paragraph("Este documento es informativo y se basa en la cartografía pública del RAN.", styles['Italic'])
            ]
            doc.build(elements)
            return buffer.getvalue()

        st.download_button("Descargar Dictamen PDF", generar_pdf(), "Dictamen_BH.pdf")
    else:
        st.warning("Debe realizar primero un análisis en la sección 'Análisis de Tenencia'.")

# --- Pie de página ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 12px;'>Consultoría y Publicidad BH © 2024 | Mérida, Yucatán, México</p>", unsafe_allow_html=True)
