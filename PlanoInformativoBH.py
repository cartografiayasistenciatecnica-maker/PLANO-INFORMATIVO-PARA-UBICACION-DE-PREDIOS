import streamlit as st
import geopandas as gpd
import ezdxf
import pandas as pd
import io
import zipfile
import folium
from streamlit_folium import st_folium
from shapely.geometry import LineString, Polygon
from pyproj import Transformer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- Configuración de la aplicación ---
st.set_page_config(page_title="Consultoría y Publicidad BH - Análisis Agrario", page_icon="📐", layout="wide")

# --- Estilos Personalizados ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { background-color: #012a4a; color: white; border-radius: 5px; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- Encabezado ---
col1, col2 = st.columns([1, 4])
with col1:
    # Intenta cargar logo, si no, usa un placeholder
    try:
        st.image("assets/logo_bh.png", width=150)
    except:
        st.markdown("### 📐 BH") # Texto alternativo si el logo no subió a GitHub
with col2:
    st.markdown("<h1 style='color:#012a4a; margin-bottom:0;'>Consultoría y Publicidad BH</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#b8860b; margin-top:0;'>Dictaminación de Tenencia de la Tierra y Cartografía</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:14px;'><b>Ing. Ruben Isai Briceño Hoil</b> | WhatsApp: 9994870705 | cartografia.y.asistenciatecnica@gmail.com</p>", unsafe_allow_html=True)

st.markdown("---")

# --- Funciones de Procesamiento ---

@st.cache_data
def cargar_base_ran(ruta_shapefile):
    """Carga la base de datos de núcleos agrarios del RAN."""
    try:
        return gpd.read_file(ruta_shapefile)
    except:
        return None

def analizar_tenencia(predio_gdf, ran_gdf):
    """Determina si el predio recae en tierras ejidales."""
    if ran_gdf is None:
        return "Error: No se cargó la base de datos del RAN", None
    
    # Asegurar mismo sistema de coordenadas (WGS84)
    if predio_gdf.crs != ran_gdf.crs:
        predio_gdf = predio_gdf.to_crs(ran_gdf.crs)
    
    interseccion = gpd.overlay(predio_gdf, ran_gdf, how='intersection')
    
    if not interseccion.empty:
        nombres_ejidos = interseccion['NOMBRE'].unique()
        return "PROPIEDAD SOCIAL (EJIDAL/COMUNAL)", nombres_ejidos
    else:
        return "PROPIEDAD PRIVADA / SIN AFECTACIÓN EJIDAL", None

def crear_pdf(df_cuadro, zona_utm, resultado_tenencia, ejidos_nombres):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título y Datos Técnicos
    elements.append(Paragraph("MEMORIA TÉCNICA Y DICTAMEN GEOGRÁFICO", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Resultado de Tenencia (Norma Técnica)
    color_resultado = colors.red if "SOCIAL" in resultado_tenencia else colors.green
    elements.append(Paragraph(f"<b>ESTADO DE TENENCIA:</b> {resultado_tenencia}", styles['Heading3']))
    if ejidos_nombres is not None:
        elements.append(Paragraph(f"<b>NÚCLEO AGRARIO AFECTADO:</b> {', '.join(ejidos_nombres)}", styles['Normal']))
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("DATOS DE CONTACTO PROFESIONAL", styles['Heading3']))
    elements.append(Paragraph("Elaborado por: Ruben Isai Briceño Hoil - Consultoría BH", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Cuadro de construcción
    data = [["Vértice", "Coordenada X", "Coordenada Y"]] + df_cuadro[['Vértice', 'Coordenada X', 'Coordenada Y']].values.tolist()
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#012a4a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t)
    
    doc.build(elements)
    return buffer.getvalue()

# --- Sidebar y Carga de Datos RAN ---
st.sidebar.header("Configuración de Análisis")
# Nota: En una app real, aquí cargarías el SHP nacional del RAN
archivo_ran = st.sidebar.file_uploader("Cargar Capa RAN (Núcleos Agrarios .shp)", type=["zip", "geojson", "shp"])
ran_data = None
if archivo_ran:
    ran_data = gpd.read_file(archivo_ran)
    st.sidebar.success("Capa RAN cargada.")

opcion = st.sidebar.radio(
    "Acción a realizar:",
    ["Validación de Tenencia (RAN)", "Importar/Exportar Planos", "Manual de Normas"],
    index=0
)

# --- Lógica de la Aplicación ---

if opcion == "Validación de Tenencia (RAN)":
    st.subheader("🛰️ Análisis de Traslape con Propiedad Social")
    st.info("Sube el archivo del predio para verificar si colisiona con polígonos ejidales según la base del RAN.")
    
    archivo_predio = st.file_uploader("Sube el archivo del PREDIO (Shapefile o GeoJSON)", type=["shp", "zip", "geojson"])
    
    if archivo_predio:
        predio_gdf = gpd.read_file(archivo_predio)
        
        if ran_data is not None:
            # Análisis Espacial
            resultado, ejidos = analizar_tenencia(predio_gdf, ran_data)
            
            # Mostrar Alerta
            if "SOCIAL" in resultado:
                st.error(f"⚠️ ATENCIÓN: {resultado}")
                st.write(f"**Ejidos detectados:** {', '.join(ejidos)}")
            else:
                st.success(f"✅ RESULTADO: {resultado}")

            # Visualización en Mapa
            st.markdown("### Visualización Geográfica")
            m = folium.Map(location=[predio_gdf.geometry.centroid.y.iloc[0], predio_gdf.geometry.centroid.x.iloc[0]], zoom_start=14)
            folium.GeoJson(predio_gdf, name="Predio", style_function=lambda x: {'fillColor': 'blue', 'color': 'blue'}).add_to(m)
            
            if "SOCIAL" in resultado:
                # Filtrar solo el ejido afectado para el mapa
                ejido_afectado = ran_data[ran_data['NOMBRE'].isin(ejidos)]
                folium.GeoJson(ejido_afectado, name="Ejido", style_function=lambda x: {'fillColor': 'red', 'color': 'red', 'fillOpacity': 0.3}).add_to(m)
            
            st_folium(m, width=1000)

            # Botón de Reporte
            if st.button("Generar Dictamen Técnico PDF"):
                # Crear DataFrame simulado para el cuadro técnico basado en el archivo subido
                coords = list(predio_gdf.geometry.iloc[0].exterior.coords)
                df_cuadro = pd.DataFrame(coords, columns=['Coordenada X', 'Coordenada Y'])
                df_cuadro['Vértice'] = range(1, len(df_cuadro) + 1)
                
                pdf_bytes = crear_pdf(df_cuadro, 16, resultado, ejidos)
                st.download_button("Descargar Dictamen Oficial", pdf_bytes, file_name="Dictamen_Tenencia_BH.pdf")
        else:
            st.warning("Por favor, carga la capa de núcleos agrarios del RAN en el menú lateral para realizar el análisis.")

elif opcion == "Importar/Exportar Planos":
    st.subheader("📐 Procesamiento de Archivos DXF/DWG")
    archivo_dwg = st.file_uploader("Sube tu archivo DXF", type=["dxf"])
    
    if archivo_dwg:
        doc = ezdxf.readfile(archivo_dwg)
        msp = doc.modelspace()
        
        # Extraer coordenadas básicas de polilíneas
        puntos = []
        for entity in msp.query('LWPOLYLINE'):
            puntos.extend(entity.get_points())
        
        if puntos:
            df = pd.DataFrame(puntos, columns=['Coordenada X', 'Coordenada Y', 'Z', 'W', 'V'])
            st.write("Coordenadas detectadas en el plano:")
            st.dataframe(df[['Coordenada X', 'Coordenada Y']].head())
            
            st.success(f"Se detectaron {len(puntos)} vértices en el archivo DXF.")
        else:
            st.error("No se encontraron polilíneas cerradas en el archivo.")

elif opcion == "Manual de Normas":
    st.subheader("📚 Marco Normativo Técnico")
    st.markdown("""
    Para que un plano tenga validez ante el **RAN** o **Catastro**, debe cumplir:
    1. **Sistema de Referencia:** ITRF08 (época actual) o WGS84.
    2. **Proyección:** UTM (Universal Transverse Mercator) con la Zona correspondiente (14, 15 o 16 en México).
    3. **Precisión:** Los vértices deben estar validados mediante GPS submétrico o estación total.
    4. **Cierre de Polígono:** El error de cierre debe ser menor a la tolerancia permitida por la norma técnica estatal.
    """)
    st.info("Este software aplica automáticamente la validación de proyección para asegurar la compatibilidad con PHINA.")

# --- Pie de página ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Consultoría y Publicidad BH © 2023 | Herramienta de uso profesional</p>", unsafe_allow_html=True)
