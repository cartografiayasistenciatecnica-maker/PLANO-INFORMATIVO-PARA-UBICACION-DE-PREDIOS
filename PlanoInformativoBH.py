import streamlit as st
import geopandas as gpd
import ezdxf
import pandas as pd
import io, zipfile
from shapely.geometry import LineString
from pyproj import Transformer
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# --- Configuración de la aplicación ---
st.set_page_config(page_title="Consultoría y Publicidad BH", page_icon="📐", layout="wide")

# --- Encabezado con logotipo y título ---
col1, col2 = st.columns([1,4])
with col1:
    st.image("assets/logo_bh.png", width=150)  # coloca tu logotipo en /assets/logo_bh.png
with col2:
    st.markdown("<h1 style='color:#012a4a;'>Consultoría y Publicidad BH</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#b8860b;'>Importación y Exportación de Planos</h3>", unsafe_allow_html=True)
    st.markdown("<p><b>Contacto:</b> WhatsApp 9994870705 | cartografia.y.asistenciatecnica@gmail.com</p>", unsafe_allow_html=True)

st.markdown("---")

# --- Función para crear PDF corporativo ---
def crear_pdf(df_cuadro, zona_utm):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Portada corporativa
    elements.append(Paragraph("Plano Informativo de Ubicación de Predio", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Elaborado por: Ruben Isai Briceño Hoil", styles['Normal']))
    elements.append(Paragraph("Consultoría y Publicidad BH", styles['Normal']))
    elements.append(Paragraph("WhatsApp: 9994870705", styles['Normal']))
    elements.append(Paragraph("Correo: cartografia.y.asistenciatecnica@gmail.com", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Conversión UTM → Geográficas
    tf = Transformer.from_crs(f"EPSG:326{zona_utm}", "EPSG:4326")
    df_cuadro['Latitud'] = df_cuadro.apply(lambda row: f"{tf.transform(row['Coordenada X'], row['Coordenada Y'])[0]:.6f}", axis=1)
    df_cuadro['Longitud'] = df_cuadro.apply(lambda row: f"{tf.transform(row['Coordenada X'], row['Coordenada Y'])[1]:.6f}", axis=1)

    # Cuadro de construcción
    elements.append(Paragraph("CUADRO DE CONSTRUCCIÓN", styles['Heading2']))
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

# --- Función para exportar KMZ con Excel ---
def exportar_kmz(df_cuadro):
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_cuadro.to_excel(writer, index=False, sheet_name="Cuadro_Tecnico")
        workbook = writer.book
        worksheet_graph = workbook.add_worksheet("Gráfico_Polígono")

        chart = workbook.add_chart({'type': 'scatter', 'subtype': 'straight_with_markers'})
        chart.add_series({
            'name': 'Predio',
            'categories': ['Cuadro_Tecnico', 1, df_cuadro.columns.get_loc("Coordenada X"), len(df_cuadro), df_cuadro.columns.get_loc("Coordenada X")],
            'values':     ['Cuadro_Tecnico', 1, df_cuadro.columns.get_loc("Coordenada Y"), len(df_cuadro), df_cuadro.columns.get_loc("Coordenada Y")],
            'marker': {'type': 'circle', 'size': 6, 'fill': {'color': 'blue'}},
            'data_labels': {'value': True, 'font': {'color': 'blue', 'bold': True}}
        })
        chart.set_title({'name': 'Polígono del Predio'})
        worksheet_graph.insert_chart('B2', chart)

    excel_buffer.seek(0)
    excel_bytes = excel_buffer.read()

    kmz_buffer = io.BytesIO()
    with zipfile.ZipFile(kmz_buffer, 'w') as zf:
        # Ejemplo KML simple
        zf.writestr("Predio.kml", """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<Placemark>
<name>Predio</name>
<Polygon>
<outerBoundaryIs>
<LinearRing>
<coordinates>
-89.700,20.900,0 -89.701,20.901,0 -89.702,20.902,0 -89.700,20.900,0
</coordinates>
</LinearRing>
</outerBoundaryIs>
</Polygon>
</Placemark>
</Document>
</kml>""")
        zf.writestr("Cuadro_Tecnico.xlsx", excel_bytes)
    kmz_buffer.seek(0)
    return kmz_buffer.getvalue()

# --- Menú lateral ---
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["Importar Shapefile", "Importar DWG/DXF", "Exportar PDF", "Exportar KMZ"],
    index=0
)

# --- Opciones del menú ---
if opcion == "Importar Shapefile":
    archivo = st.file_uploader("Sube tu archivo Shapefile (.shp)", type=["shp"])
    if archivo:
        gdf = gpd.read_file(archivo)
        st.success("✅ Shapefile importado correctamente.")
        st.write(gdf.head())

elif opcion == "Importar DWG/DXF":
    archivo = st.file_uploader("Sube tu archivo DWG/DXF", type=["dwg","dxf"])
    if archivo:
        if archivo.name.endswith(".dxf"):
            doc = ezdxf.readfile(archivo)
            msp = doc.modelspace()
            st.success("✅ DXF importado correctamente.")
            st.write(f"Elementos encontrados: {len(msp)}")
        else:
            st.warning("Convierte DWG a DXF antes de procesarlo.")

elif opcion == "Exportar PDF":
    st.info("📄 Generando PDF corporativo...")
    df_cuadro = pd.DataFrame({
        "Vértice":[1,2,3],
        "Coordenada X":[100,200,300],
        "Coordenada Y":[400,500,600],
        "Fuente":["Archivo","Manual","Archivo"]
    })
    pdf_bytes = crear_pdf(df_cuadro, zona_utm=16)
    st.download_button("Descargar PDF", pdf_bytes, file_name="Plano.pdf")

elif opcion == "Exportar KMZ":
    st.info("🌍 Generando KMZ corporativo...")
    df_cuadro = pd.DataFrame({
        "Vértice":[1,2,3],
        "Coordenada X":[100,200,300],
        "Coordenada Y":[400,500,600],
        "Fuente":["Archivo","Manual","Archivo"]
    })
    kmz_bytes = exportar_kmz(df_cuadro)
    st.download_button("Descargar KMZ", kmz_bytes, file_name="Plano.kmz")
