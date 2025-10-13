# ==========================
#  IMPORTS
# ==========================
import streamlit as st
import pandas as pd
import re
import pdfplumber
import json
import unicodedata
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import tempfile


# ==========================
#  FUNCIÓN: Parser de PDF con contraseña
# ==========================
def read_pdf(uploaded_file, password=None) -> tuple:
    """
    Lee una cartola bancaria en PDF y devuelve un DataFrame y los saldos
    con las columnas: FECHA, DETALLE, CARGOS, ABONOS
    Retorna: (DataFrame, saldo_inicial, saldo_final)
    """
    rows = []
    saldo_inicial = None
    saldo_final = None
    
    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            # Intentar extraer como tabla primero (para formatos estructurados)
            for page_num, page in enumerate(pdf.pages, 1):
                # Extraer tablas
                tables = page.extract_tables()
                
                if tables:
                    # Procesar tablas estructuradas
                    for table in tables:
                        for row in table:
                            if not row or len(row) < 3:
                                continue
                            
                            # Buscar saldo anterior
                            if row[0] and "Saldo Anterior" in str(row[0]):
                                try:
                                    saldo_inicial = int(str(row[1]).replace(".", "").replace(",", "").replace("$", "").strip())
                                except:
                                    pass
                            
                            # Buscar saldo final
                            if row[0] and "Saldo Final" in str(row[0]):
                                try:
                                    saldo_final = int(str(row[1]).replace(".", "").replace(",", "").replace("$", "").strip())
                                except:
                                    pass
                            
                            # Detectar filas de movimientos (tienen fecha)
                            fecha_str = str(row[0]).strip() if row[0] else ""
                            # Formato: "11/Ago." o "28/Jul."
                            if re.match(r"^\d{1,2}/[A-Za-z]{3}", fecha_str):
                                try:
                                    # Extraer componentes
                                    fecha = fecha_str
                                    n_operacion = str(row[1]) if len(row) > 1 else ""
                                    descripcion = str(row[2]) if len(row) > 2 else ""
                                    abonos_str = str(row[3]) if len(row) > 3 else ""
                                    cargos_str = str(row[4]) if len(row) > 4 else ""
                                    
                                    # Limpiar y convertir montos
                                    abono = 0
                                    cargo = 0
                                    
                                    if abonos_str and abonos_str.strip() and abonos_str != "None":
                                        try:
                                            abono = int(abonos_str.replace("$", "").replace(".", "").replace(",", "").strip())
                                        except:
                                            pass
                                    
                                    if cargos_str and cargos_str.strip() and cargos_str != "None":
                                        try:
                                            cargo = int(cargos_str.replace("$", "").replace(".", "").replace(",", "").strip())
                                        except:
                                            pass
                                    
                                    # Solo agregar si hay al menos un monto
                                    if cargo > 0 or abono > 0:
                                        # Limpiar descripción
                                        descripcion = descripcion.strip()
                                        rows.append([fecha, descripcion, cargo, abono])
                                
                                except Exception as e:
                                    continue
                
                # Si no se encontraron tablas, intentar extracción por texto
                if not rows:
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    lines = text.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Capturar saldo anterior
                        if "SALDO ANTERIOR" in line.upper() or "Saldo Anterior" in line:
                            numeros = re.findall(r"[\d\.\,]+", line)
                            if numeros:
                                for num in numeros:
                                    if len(num) >= 3:
                                        try:
                                            saldo_inicial = int(num.replace(".", "").replace(",", ""))
                                            break
                                        except:
                                            pass
                            continue
                        
                        # Capturar saldo final
                        if "SALDO FINAL" in line.upper() or "Saldo Final" in line:
                            numeros = re.findall(r"[\d\.\,]+", line)
                            if numeros:
                                for num in numeros:
                                    if len(num) >= 3:
                                        try:
                                            saldo_final = int(num.replace(".", "").replace(",", ""))
                                            break
                                        except:
                                            pass
                            continue
                        
                        # Detectar líneas con fecha al inicio (formato DD/MM o DD/Mes)
                        fecha_match = re.match(r"^(\d{1,2}/(?:\d{1,2}|[A-Za-z]{3}\.?))\s+(.+)", line)
                        if fecha_match:
                            fecha = fecha_match.group(1)
                            resto_linea = fecha_match.group(2).strip()
                            
                            # Buscar números al final de la línea
                            numeros = re.findall(r"[\d\.\,]+", resto_linea)
                            montos = []
                            
                            for num in numeros:
                                if re.match(r"^[\d\.\,]+$", num) and len(num) >= 3:
                                    try:
                                        monto = int(num.replace(".", "").replace(",", ""))
                                        if monto > 0:
                                            montos.append(monto)
                                    except:
                                        pass
                            
                            if montos:
                                # Para este formato: último número es saldo, anterior es el monto de transacción
                                if len(montos) >= 2:
                                    monto_transaccion = montos[-2]
                                else:
                                    monto_transaccion = montos[0]
                                
                                # Determinar si es cargo o abono
                                resto_upper = resto_linea.upper()
                                palabras_abono = ["ABONO", "DEPOSITO", "SUELDO", "TRASPASO DE", "TEF DESDE"]
                                es_abono = any(palabra in resto_upper for palabra in palabras_abono)
                                
                                if es_abono:
                                    cargo = 0
                                    abono = monto_transaccion
                                else:
                                    cargo = monto_transaccion
                                    abono = 0
                                
                                # Extraer descripción limpia
                                descripcion = limpiar_descripcion_numerica(resto_linea, numeros)
                                palabras_innecesarias = ["INTERNET", "WEB", "ONLINE", "MOVIL", "APP", "DIGITAL", "VIRTUAL","OF.", "OF LLOLLEO", "LLOLLEO"]
                                for palabra in palabras_innecesarias:
                                    descripcion = descripcion.replace(palabra, "").strip()
                                
                                descripcion = re.sub(r"\s+", " ", descripcion).strip()
                                descripcion = descripcion.rstrip(":")
                                
                                rows.append([fecha, descripcion, cargo, abono])
        
        if not rows:
            raise ValueError("⚠️ No se detectaron movimientos en el PDF.")
        
        return pd.DataFrame(rows, columns=["FECHA", "DETALLE", "CARGOS", "ABONOS"]), saldo_inicial, saldo_final
    
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise ValueError("🔒 El PDF está protegido con contraseña")
        else:
            raise e


# ==========================
#  FUNCIONES: Reglas de categorías
# ==========================
def limpiar_descripcion_numerica(descripcion, numeros_encontrados):
    """
    Limpia la descripción eliminando los últimos N números que aparecen al final
    """
    if not numeros_encontrados:
        return descripcion
    
    # Dividir descripción en palabras
    palabras = descripcion.split()
    
    # Contar cuántas palabras del final contienen números
    palabras_con_numeros = 0
    for palabra in reversed(palabras):
        if any(char.isdigit() for char in palabra):
            palabras_con_numeros += 1
        else:
            break  # Si encontramos una palabra sin números, paramos
    
    # Si encontramos palabras con números al final, las quitamos
    if palabras_con_numeros > 0:
        descripcion_limpia = " ".join(palabras[:-palabras_con_numeros])
    else:
        descripcion_limpia = descripcion
    
    return descripcion_limpia.strip()


def load_rules(file_path="rules.json"):
    """
    Carga las reglas de categorización desde un archivo JSON.
    Devuelve un diccionario con categorías y sus palabras clave.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"Sin Clasificacion": []}


def categorizar(detalle: str, rules: dict) -> str:
    """
    Categoriza un detalle basado en las reglas proporcionadas
    """
    if not detalle or not isinstance(detalle, str):
        return "Sin Clasificacion"
    
    # Normalizar detalle
    detalle_norm = detalle.upper()
    detalle_norm_original = detalle.upper()  # Guardar versión con espacios para verificaciones
    detalle_norm = ''.join(c for c in unicodedata.normalize('NFD', detalle_norm)
                          if unicodedata.category(c) != 'Mn')
    detalle_norm = re.sub(r'[^A-Z0-9]', '', detalle_norm)
    
    # REGLA ESPECIAL 1: Identificar comisiones bancarias ANTES de transferencias
    palabras_comision = ["COMISION", "CARGO", "MANTENCION", "MANTENSION", "CUOTA"]
    if any(palabra in detalle_norm_original for palabra in palabras_comision):
        # Es una comisión, no una transferencia
        if "Servicios Financieros" in rules:
            return "Servicios Financieros"
        else:
            return "Comisiones Bancarias"
    
    # REGLA ESPECIAL 2: Verificar si es una transferencia real
    es_transferencia = False
    
    # Patrones de transferencias (cubren múltiples formatos de bancos)
    patrones_transferencia = [
        r"TEF\s+(A|DE)[\s:]",      # TEF A NOMBRE o TEF DE NOMBRE (Banco Estado)
        r"TRASPASO\s+(A|DE)[\s:]",  # TRASPASO A:/DE: (Banco Chile) o TRASPASO A/DE (otros)
        r"TRANSFERENCIA\s+(A|DE)[\s:]", # TRANSFERENCIA A/DE
        r"GIRO\s+(A|DE)[\s:]",      # GIRO A/DE
        r"ENVIO\s+(A|DE)[\s:]",      # ENVIO A/DE
        r"TEF\s+(DESDE)[\s:]"
    ]
    
    for patron in patrones_transferencia:
        if re.search(patron, detalle_norm_original):
            es_transferencia = True
            break
    
    # También detectar si contiene TRASPASO o TRANSFERENCIA (sin comisión ya verificada arriba)
    if not es_transferencia:
        palabras_transferencia = ["TRASPASO", "TRANSFERENCIA", "ABONO"]
        for palabra in palabras_transferencia:
            if palabra in detalle_norm_original:
                es_transferencia = True
                break
    
    if es_transferencia:
        if "Transferencias" in rules:
            return "Transferencias"
        else:
            return "TRANSFERENCIAS"
    
    # REGLA NORMAL: Buscar coincidencias en las reglas
    for categoria, palabras_clave in rules.items():
        if categoria == "Sin Clasificacion":
            continue
        
        # Saltar categoría de transferencias ya que la manejamos arriba
        if categoria.upper() in ["TRANSFERENCIAS", "TRANSFERENCIA"]:
            continue
            
        for palabra in palabras_clave:
            palabra_norm = palabra.upper()
            palabra_norm = ''.join(c for c in unicodedata.normalize('NFD', palabra_norm)
                                  if unicodedata.category(c) != 'Mn')
            palabra_norm = re.sub(r'[^A-Z0-9]', '', palabra_norm)
            
            if palabra_norm and palabra_norm in detalle_norm:
                return categoria
    
    return "Sin Clasificacion"


def obtener_rango_fecha(fecha_str):
    """
    Convierte fecha DD/MM a rangos semanales
    """
    try:
        # Convertir fecha DD/MM a datetime
        fecha_dt = pd.to_datetime('2025/' + fecha_str, format='%Y/%d/%m')
        mes = fecha_dt.month
        dia = fecha_dt.day
        
        mes_nombres = {7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
        mes_nombre = mes_nombres.get(mes, str(mes))
        
        if dia <= 7:
            return f"📅 1-7 {mes_nombre}"
        elif dia <= 14:
            return f"📅 8-14 {mes_nombre}"
        elif dia <= 21:
            return f"📅 15-21 {mes_nombre}"
        elif dia <= 28:
            return f"📅 22-28 {mes_nombre}"
        else:
            return f"📅 29+ {mes_nombre}"
    except:
        return "Sin fecha"


def generar_pdf_reporte(df, gastos_cat, saldo_inicial, saldo_final, total_gastos, total_abonos):
    """
    Genera un reporte PDF con resumen y gráfico
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    title = Paragraph("<b>Reporte Financiero - Cartola Bancaria</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Resumen de saldos
    if saldo_inicial is not None:
        saldo_text = Paragraph(f"<b>Saldo Inicial:</b> ${saldo_inicial:,.0f}", styles['Normal'])
        elements.append(saldo_text)
    
    if saldo_final is not None:
        saldo_text = Paragraph(f"<b>Saldo Final:</b> ${saldo_final:,.0f}", styles['Normal'])
        elements.append(saldo_text)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Resumen financiero
    resumen_data = [
        ['Concepto', 'Monto'],
        ['Total Gastos', f'${total_gastos:,.0f}'],
        ['Total Ingresos', f'${total_abonos:,.0f}'],
        ['Saldo Neto', f'${total_abonos - total_gastos:,.0f}']
    ]
    
    resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(resumen_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de gastos por categoría
    categoria_title = Paragraph("<b>Gastos por Categoría</b>", styles['Heading2'])
    elements.append(categoria_title)
    elements.append(Spacer(1, 0.1*inch))
    
    gastos_data = [['Categoría', 'Monto']]
    for _, row in gastos_cat.iterrows():
        gastos_data.append([row['CATEGORIA'], f"${row['CARGOS']:,.0f}"])
    
    gastos_table = Table(gastos_data, colWidths=[3*inch, 2*inch])
    gastos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(gastos_table)
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================
#  INTERFAZ PRINCIPAL
# ==========================

st.title("📊 Analizador de Cartola Bancaria")

# Subir archivo de cartola
uploaded_file = st.file_uploader(
    "Sube tu cartola (PDF, CSV o Excel)", 
    type=["pdf", "csv", "xlsx"]
)

# Campo de contraseña para PDFs protegidos
pdf_password = None
if uploaded_file and uploaded_file.name.endswith(".pdf"):
    with st.expander("🔒 ¿Tu PDF está protegido con contraseña?"):
        pdf_password = st.text_input("Ingresa la contraseña del PDF", type="password")

# Subir archivo JSON de reglas personalizadas
uploaded_json = st.file_uploader(
    "Opcional: sube tus reglas de categorías (rules.json)", 
    type=["json"]
)

# Usar reglas personalizadas si el usuario subió un JSON
if uploaded_json:
    rules = json.load(uploaded_json)
    st.success("✅ Se cargaron reglas personalizadas desde JSON")
else:
    rules = load_rules()


# ==========================
#  PROCESAMIENTO DE ARCHIVO
# ==========================

if uploaded_file:
    try:
        # Leer cartola según formato
        saldo_inicial = None
        saldo_final = None
        
        if uploaded_file.name.endswith(".pdf"):
            try:
                df, saldo_inicial, saldo_final = read_pdf(uploaded_file, password=pdf_password if pdf_password else None)
            except Exception as pdf_error:
                if "password" in str(pdf_error).lower() or "encrypted" in str(pdf_error).lower():
                    st.error("🔒 El PDF está protegido con contraseña. Por favor, ingrésala arriba.")
                    st.stop()
                else:
                    st.error(f"❌ Error al leer PDF: {pdf_error}")
                    st.info("💡 Verifica que el PDF tenga el formato correcto de cartola bancaria")
                    st.stop()
        elif uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            # Para CSV/Excel, verificar que tenga las columnas necesarias
            if not all(col in df.columns for col in ["FECHA", "DETALLE", "CARGOS", "ABONOS"]):
                st.error("❌ El CSV debe tener las columnas: FECHA, DETALLE, CARGOS, ABONOS")
                st.stop()
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
            # Para CSV/Excel, verificar que tenga las columnas necesarias
            if not all(col in df.columns for col in ["FECHA", "DETALLE", "CARGOS", "ABONOS"]):
                st.error("❌ El Excel debe tener las columnas: FECHA, DETALLE, CARGOS, ABONOS")
                st.stop()
        else:
            st.error("❌ Formato de archivo no soportado")
            st.stop()
    
    except ValueError as e:
        st.error(f"❌ Error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error inesperado al procesar el archivo: {e}")
        st.info("💡 Por favor, verifica que el archivo tenga el formato correcto")
        st.stop()

    # Guardar CSV limpio
    if st.button("💾 Guardar como CSV"):
        df.to_csv("cartola_limpia.csv", index=False, encoding="utf-8-sig")
        st.success("✅ Cartola guardada como cartola_limpia.csv")

    # Resumen financiero con saldos inicial y final
    st.subheader("💰 Resumen Financiero")
    
    # Primera fila: Saldo inicial y final
    if saldo_inicial is not None or saldo_final is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            if saldo_inicial is not None:
                st.metric("🏦 Saldo Inicial", f"${saldo_inicial:,.0f}")
        with col2:
            if saldo_final is not None:
                st.metric("🏦 Saldo Final", f"${saldo_final:,.0f}")
        with col3:
            if saldo_inicial is not None and saldo_final is not None:
                variacion = saldo_final - saldo_inicial
                st.metric("📈 Variación", f"${variacion:,.0f}", delta=f"{variacion:,.0f}")
    
    # Segunda fila: Totales
    col1, col2, col3 = st.columns(3)

    total_gastos = df["CARGOS"].sum()
    total_abonos = df["ABONOS"].sum()
    saldo_neto = total_abonos - total_gastos

    with col1:
        st.metric("💸 Total Gastos", f"${total_gastos:,.0f}")
    with col2:
        st.metric("💰 Total Ingresos", f"${total_abonos:,.0f}")
    with col3:
        st.metric("📊 Saldo Neto", f"${saldo_neto:,.0f}")

    # Categorización automática
    df["CATEGORIA"] = df["DETALLE"].apply(lambda x: categorizar(x, rules))

    st.subheader("📌 Todos los Movimientos Categorizados")
    st.write(f"**Total de movimientos:** {len(df)}")

    # Tabla editable
    edited_df = st.data_editor(
        df,
        column_config={
            "CATEGORIA": st.column_config.SelectboxColumn(
                "Categoría",
                help="Selecciona la categoría correcta",
                width="medium",
                options=list(rules.keys()),
                required=True,
            )
        },
        disabled=["FECHA", "DETALLE", "CARGOS", "ABONOS"],
        use_container_width=True,
        height=600
    )

    # Filtros avanzados
    st.subheader("🔍 Filtros Avanzados")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Filtro por categoría
        categorias_disponibles = edited_df["CATEGORIA"].unique().tolist()
        categoria_seleccionada = st.selectbox("Categoría:", ["Todas"] + categorias_disponibles)

    with col2:
        # Filtro por tipo de gasto
        tipo_gasto = st.selectbox("Tipo:", ["Todos", "Solo Gastos", "Solo Ingresos"])

    with col3:
        # Filtro por rangos de fechas
        rangos_unicos = edited_df['FECHA'].apply(obtener_rango_fecha).unique()
        rangos_disponibles = ["Todas"] + sorted(rangos_unicos)
        semana_seleccionada = st.selectbox("Período:", rangos_disponibles)

    # Aplicar filtros
    df_filtrado = edited_df.copy()

    # Filtrar por categoría
    if categoria_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["CATEGORIA"] == categoria_seleccionada]

    # Filtrar por tipo de gasto
    if tipo_gasto == "Solo Gastos":
        df_filtrado = df_filtrado[df_filtrado["CARGOS"] > 0]
    elif tipo_gasto == "Solo Ingresos":
        df_filtrado = df_filtrado[df_filtrado["ABONOS"] > 0]

    # Filtrar por semana
    if semana_seleccionada != "Todas":
        mask_semana = df_filtrado['FECHA'].apply(lambda x: obtener_rango_fecha(x) == semana_seleccionada)
        df_filtrado = df_filtrado[mask_semana]

    # Mostrar resultados filtrados
    if len(df_filtrado) > 0:
        st.write(f"**Movimientos encontrados:** {len(df_filtrado)}")
        
        # Métricas del filtro
        col1, col2, col3 = st.columns(3)
        with col1:
            total_gastos_filtro = df_filtrado["CARGOS"].sum()
            st.metric("💸 Gastos", f"${total_gastos_filtro:,.0f}")
        with col2:
            total_ingresos_filtro = df_filtrado["ABONOS"].sum()
            st.metric("💰 Ingresos", f"${total_ingresos_filtro:,.0f}")
        with col3:
            saldo_filtro = total_ingresos_filtro - total_gastos_filtro
            st.metric("📊 Saldo", f"${saldo_filtro:,.0f}")
        
        st.dataframe(df_filtrado, use_container_width=True, height=400)
    else:
        st.warning("⚠️ No se encontraron movimientos con los filtros seleccionados")

    # Gráficos
    st.subheader("📊 Gastos por Categoría")

    # Separar transferencias del resto
    df_sin_transferencias = edited_df[
        (edited_df["CARGOS"] > 0) & 
        (~edited_df["CATEGORIA"].str.contains("TRANSFERENCIA|TRASPASO", case=False, na=False))
    ]

    # Calcular total de transferencias
    transferencias_df = edited_df[
        (edited_df["CARGOS"] > 0) & 
        (edited_df["CATEGORIA"].str.contains("TRANSFERENCIA|TRASPASO", case=False, na=False))
    ]
    total_transferencias = transferencias_df["CARGOS"].sum()

    # Mostrar total de transferencias por separado
    if total_transferencias > 0:
        st.metric("💸 Total Transferencias", f"${total_transferencias:,.0f}")

    # Gráfico sin transferencias
    gastos_cat = df_sin_transferencias.groupby("CATEGORIA")["CARGOS"].sum().reset_index()
    gastos_cat = gastos_cat.sort_values("CARGOS", ascending=False)

    if len(gastos_cat) > 0:
        fig_bar = px.bar(
            gastos_cat, 
            x="CATEGORIA", 
            y="CARGOS",
            title="Distribución de Gastos por Categoría",
            color="CARGOS",
            color_continuous_scale="Reds"
        )
        fig_bar.update_xaxes(tickangle=45)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Gráfico circular
        fig_pie = px.pie(
            gastos_cat, 
            values="CARGOS", 
            names="CATEGORIA",
            title="Distribución Porcentual de Gastos"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Botón para exportar reporte en PDF
        st.subheader("📄 Exportar Reporte")
        if st.button("📥 Descargar Reporte en PDF"):
            pdf_buffer = generar_pdf_reporte(
                edited_df, 
                gastos_cat, 
                saldo_inicial, 
                saldo_final, 
                total_gastos, 
                total_abonos
            )
            
            st.download_button(
                label="💾 Descargar PDF",
                data=pdf_buffer,
                file_name="reporte_financiero.pdf",
                mime="application/pdf"
            )
    else:
        st.info("No hay gastos para mostrar")