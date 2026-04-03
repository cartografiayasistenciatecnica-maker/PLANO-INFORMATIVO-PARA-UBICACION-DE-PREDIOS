import streamlit as st
import geopandas as gpd
import ezdxf
import pandas as pd
import io
import os
import tempfile
import zipfile
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon, Point, mapping
from pyproj import Transformer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="BH - Consultoría y Cartografía", page_icon="📐", layout="wide")

# Habilitar soporte KML en Fiona
import fiona
if 'KML' not in fiona.supported_drivers:
    fiona.supported_drivers['KML'] = 'rw'
if 'LIBKML' not in fiona.supported_drivers:
    fiona.supported_drivers['LIBKML'] = 'rw'

# --- FUNCIONES DE CONVERSIÓN Y EXPORTACIÓN ---

def utm_to_latlon(df, zona):
    """Convierte coordenadas UTM a Geográficas para reportes"""
    transformer = Transformer.from_crs(f"EPSG:326{zona}", "EPSG:4326")
    df['Latitud'], df['Longitud'] = transformer.transform(df['X'].values, df['Y'].values)
    return df

def crear_pdf_reporte(df_coords, status_tenencia, ejidos_nombres):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("PLANO INFORMATIVO Y DICTAMEN TÉCNICO", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Responsable Técnico:</b> Ing. Ruben Isai Briceño Hoil", styles['Normal']))
    elements.append(Paragraph(f"<b>Consultoría:</b> Consultoría y Publicidad BH", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Cuadro de Tenencia
    color_t = colors.red if "SOCIAL" in status_tenencia else colors.green
    data_t = [["ESTADO DE TENENCIA DE LA TIERRA"], [status_tenencia]]
    tabla_t = Table(data_t, colWidths=[400])
    tabla_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), color_t),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(tabla_t)
    elements.append(Spacer(1, 20))

    # Cuadro de Construcción
    elements.append(Paragraph("CUADRO DE CONSTRUCCIÓN (COORDENADAS)", styles['Heading2']))
    data_c = [["Vértice", "X (UTM)", "Y (UTM)", "Latitud", "Longitud"]] + df_coords.values.tolist()
    tabla_c = Table(data_c)
    tabla_c.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#012a4a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))
    elements.append(tabla_c)
    
    doc.build(elements)
    return buffer.getvalue()

def exportar_dxf(df_coords):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    puntos = [(row['X'], row['Y']) for _, row in df_coords.iterrows()]
    if puntos:
        puntos.append(puntos[0]) # Cerrar polígono
        msp.add_lwpolyline(puntos)
    
    out_buffer = io.StringIO()
    doc.write(out_buffer)
    return out_buffer.getvalue()

def crear_kmz(gdf):
    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Document><name>Predio BH</name><Placemark><name>Polígono</name>
    {gdf.geometry.iloc[0]._repr_svg_()} 
    </Placemark></Document></kml>"""
    # Nota: Simplificado para el ejemplo, Geopandas to_file es mejor si el driver KML está activo
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.writestr("doc.kml", kml_content)
    return buffer.getvalue()

# --- FUNCIONES DE LECTURA ---

def leer_archivo_geo(file):
    try:
        # Forzar engine fiona para evitar errores de pyogrio en zip/kmz
        gdf = gpd.read_file(file, engine='fiona')
        if gdf.crs is None: gdf.set_crs("EPSG:32616", inplace=True)
        return gdf.to_crs("EPSG:4326")
    except Exception as e:
        st.error(f"Error al leer archivo geográfico: {e}")
        return None

def leer_dxf_puntos(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        tmp.write(file.getvalue())
        path = tmp.name
    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()
        pts = []
        for e in msp.query('LWPOLYLINE'):
            pts.extend([(p[0], p[1]) for p in e.get_points()])
        os.unlink(path)
        if pts:
            df = pd.DataFrame(pts, columns=['X', 'Y']).drop_duplicates()
            df.insert(0, 'Vértice', range(1, len(df)+1))
            return df
        return None
    except:
        return None

# --- INTERFAZ (UI) ---

# Encabezado
c1, c2 = st.columns([1,4])
with c1:
    if os.path.exists("assets/logo_bh.png"): st.image("assets/logo_bh.png", width=150)
    else: st.title("📐 BH")
with c2:
    st.markdown("<h1 style='color:#012a4a;'>Consultoría y Publicidad BH</h1>", unsafe_allow_html=True)
    st.markdown("9994870705 | cartografia.y.asistenciatecnica@gmail.com")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📥 IMPORTAR DATOS")
    tipo_imp = st.selectbox("Tipo de archivo:", ["DXF/DWG", "Shapefile (.zip)", "KMZ/KML"])
    file_in = st.file_uploader(f"Cargar {tipo_imp}")
    
    st.markdown("---")
    st.header("🗺️ BASE REFERENCIA (RAN)")
    file_ran = st.file_uploader("Cargar Polígonos RAN (PHINA)", type=["zip", "geojson"])

# --- LÓGICA PRINCIPAL ---

# 1. Procesar Carga de Datos
if file_in:
    if tipo_imp == "DXF/DWG":
        df_coords = leer_dxf_puntos(file_in)
        if df_coords is not None:
            st.session_state['df_coords'] = df_coords
            st.success("✅ DXF cargado. Define coordenadas UTM para ubicar en mapa.")
    else:
        gdf_predio = leer_archivo_geo(file_in)
        if gdf_predio is not None:
            st.session_state['gdf_predio'] = gdf_predio
            # Extraer coordenadas para el cuadro
            coords = list(gdf_predio.geometry.iloc[0].exterior.coords)
            df_c = pd.DataFrame(coords, columns=['X', 'Y'])
            df_c.insert(0, 'Vértice', range(1, len(df_c)+1))
            st.session_state['df_coords'] = df_c

# 2. Análisis y Visualización
tab1, tab2, tab3 = st.tabs(["📍 UBICACIÓN Y ANÁLISIS", "📊 CUADRO TÉCNICO", "📥 EXPORTAR"])

with tab1:
    col_map, col_info = st.columns([2,1])
    
    if 'gdf_predio' in st.session_state:
        with col_map:
            st.subheader("Ubicación Cartográfica")
            m = folium.Map(location=[st.session_state.gdf_predio.geometry.centroid.y.iloc[0], 
                                     st.session_state.gdf_predio.geometry.centroid.x.iloc[0]], zoom_start=15)
            folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google', name='Satélite').add_to(m)
            folium.GeoJson(st.session_state.gdf_predio, name="Predio").add_to(m)
            st_folium(m, width="100%", height=500)
        
        with col_info:
            st.subheader("Análisis de Tenencia")
            if file_ran:
                ran_gdf = gpd.read_file(file_ran, engine='fiona').to_crs("EPSG:4326")
                inter = gpd.overlay(st.session_state.gdf_predio, ran_gdf, how='intersection')
                if not inter.empty:
                    ejidos = inter['NOMBRE'].unique()
                    st.error(f"¡ALERTA! Predio en TIERRAS EJIDALES.")
                    st.write(f"Núcleos: {', '.join(ejidos)}")
                    st.session_state['status'] = f"SOCIAL (EJIDO {', '.join(ejidos)})"
                else:
                    st.success("Predio en PROPIEDAD PRIVADA.")
                    st.session_state['status'] = "PROPIEDAD PRIVADA"
            else:
                st.warning("Sube la base del RAN para dictaminar.")

with tab2:
    if 'df_coords' in st.session_state:
        st.subheader("Cuadro de Construcción del Predio")
        st.dataframe(st.session_state.df_coords, use_container_width=True)
        
        # Opción para convertir UTM si se cargó DXF
        if tipo_imp == "DXF/DWG":
            zona_utm = st.selectbox("Zona UTM (México):", [14, 15, 16], index=2)
            if st.button("Calcular Lat/Lon para Reporte"):
                df_calc = utm_to_latlon(st.session_state.df_coords.copy(), zona_utm)
                st.session_state['df_coords_full'] = df_calc
                st.dataframe(df_calc)

with tab3:
    st.subheader("Centro de Descargas")
    if 'df_coords' in st.session_state:
        c_p1, c_p2, c_p3 = st.columns(3)
        
        with c_p1:
            st.info("Reporte Oficial")
            # PDF
            if 'df_coords_full' in st.session_state:
                pdf_bytes = crear_pdf_reporte(st.session_state.df_coords_full, 
                                             st.session_state.get('status', 'No dictaminado'), [])
                st.download_button("📥 Descargar Reporte PDF", pdf_bytes, "Reporte_BH.pdf")
            else:
                st.write("Calcula Lat/Lon en la pestaña anterior para PDF.")

        with c_p2:
            st.info("Formatos CAD/GIS")
            # DXF
            dxf_str = exportar_dxf(st.session_state.df_coords)
            st.download_button("📥 Descargar Plano DXF", dxf_str, "Plano_BH.dxf")
            
            # KMZ
            if 'gdf_predio' in st.session_state:
                kmz_bytes = crear_kmz(st.session_state.gdf_predio)
                st.download_button("📥 Descargar KMZ", kmz_bytes, "Ubicacion_BH.kmz")

        with c_p3:
            st.info("Tablas Técnicas")
            # Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state.df_coords.to_excel(writer, index=False, sheet_name='Coordenadas')
            st.download_button("📥 Descargar Cuadro Excel", output.getvalue(), "Cuadro_BH.xlsx")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<center>Consultoría y Publicidad BH © 2024 | Mérida, Yucatán | Especialistas en Propiedad Social</center>", unsafe_allow_html=True)
