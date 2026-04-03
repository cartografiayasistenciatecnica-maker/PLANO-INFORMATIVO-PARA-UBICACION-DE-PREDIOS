import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import math
import simplekml
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# --- 1. CONFIGURACIÓN DE MARCA Y ESTILO ---
st.set_page_config(page_title="GEO-AGRARIO PRO", layout="wide")

def aplicar_estilo():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #012a4a; color: white; }
        .stDownloadButton button { 
            background-color: #ffc107; color: black; border-radius: 10px; width: 100%;
        }
        .main { background-color: #f8f9fa; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE CÁLCULO TOPOGRÁFICO ---
def formatear_gms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = round((((deg - d) * 60) - m) * 60, 2)
    return f"{d}°{m}'{s}\""

def calcular_rumbo(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    distancia = math.sqrt(dx**2 + dy**2)
    azimut = math.degrees(math.atan2(dx, dy)) % 360
    if 0 <= azimut < 90: r = f"N {formatear_gms(azimut)} E"
    elif 90 <= azimut < 180: r = f"S {formatear_gms(180-azimut)} E"
    elif 180 <= azimut < 270: r = f"S {formatear_gms(azimut-180)} W"
    else: r = f"N {formatear_gms(360-azimut)} W"
    return r, distancia

def generar_cuadro_df(df):
    filas = []
    for i in range(len(df)):
        p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
        rumbo, dist = calcular_rumbo(p1['Este_X'], p1['Norte_Y'], p2['Este_X'], p2['Norte_Y'])
        filas.append({
            'Est': i+1, 'PV': (i+2) if (i+1) < len(df) else 1,
            'Rumbo': rumbo, 'Distancia': f"{dist:.3f} m",
            'Vértice': i+1, 'Coordenada X': f"{p1['Este_X']:.3f}", 'Coordenada Y': f"{p1['Norte_Y']:.3f}"
        })
    return pd.DataFrame(filas)

# --- 3. GENERACIÓN DE REPORTES (PDF Y KMZ) ---
def crear_pdf(df_cuadro):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("PLANO INFORMATIVO DE UBICACIÓN", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>NOTA:</b> Este documento es informativo y no constituye un título de propiedad.", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    data = [df_cuadro.columns.to_list()] + df_cuadro.values.tolist()
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#012a4a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    elements.append(t)
    doc.build(elements)
    return buffer.getvalue()

# --- 4. INTERFAZ PRINCIPAL ---
aplicar_estilo()

# Encabezado con espacio para Logo
col_l, col_t = st.columns([1, 4])
with col_l:
    # st.image("tu_logo.png", width=120) # Descomenta cuando subas tu logo a GitHub
    st.info("LOGO AQUÍ")
with col_t:
    st.title("SISTEMA DE GESTIÓN GEO-AGRARIA")
    st.caption("Ubicación de predios, Cuadros de Construcción y Análisis RAN")

st.sidebar.header("⚙️ Configuración")
zona_utm = st.sidebar.number_input("Zona UTM (México 11-16)", min_value=11, max_value=16, value=14)
archivo = st.sidebar.file_uploader("Cargar archivo (CSV o Excel)", type=['csv', 'xlsx'])

if archivo:
    try:
        df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        cuadro_df = generar_cuadro_df(df)
        
        # Conversión de coordenadas
        tf = Transformer.from_crs(f"EPSG:326{zona_utm}", "EPSG:4326")
        coords_mapa = [tf.transform(row['Este_X'], row['Norte_Y']) for _, row in df.iterrows()]
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.subheader("📍 Visualización Geo-Agraria")
            # SOLUCIÓN ERROR REMOVECHILD: ID dinámico único
            map_key = f"mapa_{archivo.name}_{len(df)}"
            
            centro = [sum(c[0] for c in coords_mapa)/len(coords_mapa), sum(c[1] for c in coords_mapa)/len(coords_mapa)]
            m = folium.Map(location=centro, zoom_start=16)
            
            # Capas
            folium.TileLayer('https://google.com{x}&y={y}&z={z}', attr='Google', name='Google Híbrido').add_to(m)
            folium.WmsTileLayer(
                url="http://ran.gob.mx",
                layers="nucleos_agrarios",
                fmt="image/png",
                transparent=True,
                name="Ejidos y Comunidades (RAN)"
            ).add_to(m)
            
            folium.Polygon(locations=coords_mapa, color="yellow", fill=True, weight=4).add_to(m)
            folium.LayerControl().add_to(m)
            
            # Renderizado con returned_objects=[] para evitar errores de sincronización
            st_folium(m, width=800, height=500, key=map_key, returned_objects=[])

        with col2:
            st.subheader("📋 Datos Técnicos")
            st.dataframe(cuadro_df[['Est', 'PV', 'Rumbo', 'Distancia']], use_container_width=True)
            
            # Generar archivos para descarga
            pdf_bytes = crear_pdf(cuadro_df)
            
            kml = simplekml.Kml()
            kml_coords = [(c[1], c[0]) for c in coords_mapa] # Long, Lat para KML
            pol = kml.newpolygon(name="Predio", outerboundaryis=kml_coords)
            pol.style.linestyle.color, pol.style.linestyle.width = simplekml.Color.yellow, 4
            
            st.download_button("📄 Descargar Plano PDF", data=pdf_bytes, file_name=f"Plano_{archivo.name}.pdf")
            st.download_button("🌍 Descargar KMZ (Google Earth)", data=kml.kml(), file_name=f"Predio_{archivo.name}.kmz")
            
            st.warning("⚠️ Verifique si el polígono amarillo coincide con las zonas coloreadas del RAN.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}. Asegúrese de usar las columnas: Vértice, Este_X, Norte_Y")
else:
    st.write("👋 Bienvenido. Por favor, cargue un archivo en la barra lateral para comenzar.")
