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


# ==========================
#  FUNCIÓN: Parser de PDF
# ==========================
def read_pdf(uploaded_file) -> pd.DataFrame:
    """
    Lee una cartola bancaria en PDF y devuelve un DataFrame
    con las columnas: FECHA, DETALLE, CARGOS, ABONOS
    """
    rows = []
    
    with pdfplumber.open(uploaded_file) as pdf:        
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detectar líneas con fecha al inicio (formato DD/MM)
                fecha_match = re.match(r"^(\d{1,2}/\d{1,2})\s+(.+)", line)
                if fecha_match:
                    fecha = fecha_match.group(1)
                    resto_linea = fecha_match.group(2).strip()
                    
                    # Ignorar saldo inicial
                    if "SALDO INICIAL" in resto_linea.upper():
                        continue
                    
                    # Buscar números al final de la línea
                    numeros = re.findall(r"[\d\.\,]+", resto_linea)
                    montos = []
                    
                    for num in numeros:
                        if re.match(r"^[\d\.\,]+$", num) and len(num) >= 3:
                            monto = int(num.replace(".", "").replace(",", ""))
                            if monto > 0:
                                montos.append(monto)
                    
                    if montos:
                        # Para este formato: último número es saldo, anterior es el monto de transacción
                        if len(montos) >= 2:
                            monto_transaccion = montos[-2]
                        else:
                            monto_transaccion = montos[0]
                        
                        # Determinar si es cargo o abono
                        resto_upper = resto_linea.upper()
                        palabras_abono = ["ABONO", "DEPOSITO", "SUELDO", "TRASPASO DE"]
                        es_abono = any(palabra in resto_upper for palabra in palabras_abono)
                        
                        if es_abono:
                            cargo = 0
                            abono = monto_transaccion
                        else:
                            cargo = monto_transaccion
                            abono = 0
                        
                        # Extraer descripción limpia
                        descripcion = limpiar_descripcion_numerica(resto_linea, numeros)
                        # Limpiar palabras innecesarias
                        palabras_innecesarias = ["INTERNET", "WEB", "ONLINE", "MOVIL", "APP", "DIGITAL", "VIRTUAL","OF.", "OF LLOLLEO", "LLOLLEO"]
                        for palabra in palabras_innecesarias:
                            descripcion = descripcion.replace(palabra, "").strip()
                        
                        descripcion = re.sub(r"\s+", " ", descripcion).strip()
                        descripcion = descripcion.rstrip(":")
                        
                        rows.append([fecha, descripcion, cargo, abono])
    
    if not rows:
        raise ValueError("⚠️ No se detectaron movimientos en el PDF.")
    
    return pd.DataFrame(rows, columns=["FECHA", "DETALLE", "CARGOS", "ABONOS"])


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
    detalle_norm = ''.join(c for c in unicodedata.normalize('NFD', detalle_norm)
                          if unicodedata.category(c) != 'Mn')
    detalle_norm = re.sub(r'[^A-Z0-9]', '', detalle_norm)
    
    # Buscar coincidencias
    for categoria, palabras_clave in rules.items():
        if categoria == "Sin Clasificacion":
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
        
        mes_nombres = {7: "Jul", 8: "Ago", 9: "Sep"}
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


# ==========================
#  INTERFAZ PRINCIPAL
# ==========================

st.title("📊 Analizador de Cartola Bancaria")

# Subir archivo de cartola
uploaded_file = st.file_uploader(
    "Sube tu cartola (PDF, CSV o Excel)", 
    type=["pdf", "csv", "xlsx"]
)

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
    # Leer cartola según formato
    if uploaded_file.name.endswith(".pdf"):
        df = read_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("❌ Formato de archivo no soportado")
        st.stop()

    # Guardar CSV limpio
    if st.button("💾 Guardar como CSV"):
        df.to_csv("cartola_limpia.csv", index=False, encoding="utf-8-sig")
        st.success("✅ Cartola guardada como cartola_limpia.csv")

    # Resumen financiero
    st.subheader("💰 Resumen Financiero")
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
    st.subheader("📊 Gastos por Transferencia")

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
    else:
        st.info("No hay gastos para mostrar")