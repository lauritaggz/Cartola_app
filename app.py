# ==========================
#  IMPORTS
# ==========================
import streamlit as st
import pandas as pd
import re
import pdfplumber
import json
import matplotlib.pyplot as plt
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
        st.info(f"📄 Procesando PDF con {len(pdf.pages)} páginas...")
        
        for page_num, page in enumerate(pdf.pages, 1):
            st.write(f"Procesando página {page_num}...")
            
            # Extraer texto completo de la página
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detectar líneas con fecha al inicio
                fecha_match = re.match(r"(\d{1,2}/\d{1,2})(.+)", line)
                if fecha_match:
                    fecha = fecha_match.group(1)
                    resto_linea = fecha_match.group(2).strip()
                    
                    # Buscar números al final de la línea
                    numeros = re.findall(r"[\d\.\,]+", resto_linea)
                    montos = []
                    
                    for num in numeros:
                        if re.match(r"^[\d\.\,]+$", num) and len(num) >= 3:
                            monto = int(num.replace(".", "").replace(",", ""))
                            if monto > 0:
                                montos.append(monto)
                    
                    if montos:
                        if len(montos) >= 2:
                            cargo = montos[-2]
                            abono = montos[-1]
                        else:
                            monto = montos[0]
                            resto_upper = resto_linea.upper()
                            
                            palabras_abono = ["ABONO", "DEPOSITO", "TRANSFERENCIA", "SUELDO"]
                            es_abono = any(palabra in resto_upper for palabra in palabras_abono)
                            
                            if es_abono:
                                cargo = 0
                                abono = monto
                            else:
                                cargo = monto
                                abono = 0
                        
                        # Extraer descripción
                        descripcion = resto_linea
                        for num in reversed(numeros):
                            descripcion = descripcion.replace(num, "").strip()
                        
                        descripcion = re.sub(r"\s+", " ", descripcion).strip()
                        rows.append([fecha, descripcion, cargo, abono])
    
    if not rows:
        raise ValueError("⚠️ No se detectaron movimientos en el PDF.")
    
    return pd.DataFrame(rows, columns=["FECHA", "DETALLE", "CARGOS", "ABONOS"])
# ==========================
#  FUNCIONES: Reglas de categorías
# ==========================

# Cargar reglas desde un archivo JSON
def load_rules(file_path="rules.json"):
    """
    Carga las reglas de categorización desde un archivo JSON.
    Devuelve un diccionario con categorías y sus palabras clave.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"Otros": []}  # fallback en caso de error

def normalizar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto = texto.upper()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    # Quitar caracteres no alfanuméricos, dejar solo letras y números
    texto = re.sub(r'[^A-Z0-9]', ' ', texto)
    # Quitar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto
def categorizar(detalle: str, rules: dict) -> str:
    if not detalle or not isinstance(detalle, str):
        return "Otros"
    
    # Normalizar detalle
    detalle_norm = detalle.upper()
    detalle_norm = ''.join(c for c in unicodedata.normalize('NFD', detalle_norm)
                          if unicodedata.category(c) != 'Mn')
    detalle_norm = re.sub(r'[^A-Z0-9]', '', detalle_norm)
    
    # Buscar coincidencias (SIN prints de debug)
    for categoria, palabras_clave in rules.items():
        if categoria == "Otros":
            continue
            
        for palabra in palabras_clave:
            palabra_norm = palabra.upper()
            palabra_norm = ''.join(c for c in unicodedata.normalize('NFD', palabra_norm)
                                  if unicodedata.category(c) != 'Mn')
            palabra_norm = re.sub(r'[^A-Z0-9]', '', palabra_norm)
            
            if palabra_norm and palabra_norm in detalle_norm:
                return categoria
    
    return "Otros"
# Función de categorización
def load_user_categories(file_path="user_categories.json"):
    """Carga categorías editadas manualmente por el usuario"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def save_user_categories(edited_df, original_df):
    """Guarda SOLO las categorías que el usuario cambió"""
    user_edits = {}
    
    for index, row in edited_df.iterrows():
        detalle = str(row["DETALLE"])
        categoria_editada = str(row["CATEGORIA"])
        categoria_original = str(original_df.iloc[index]["CATEGORIA"])
        
        # Solo guardar si el usuario la cambió
        if categoria_editada != categoria_original:
            user_edits[detalle] = categoria_editada
    
    try:
        with open("user_categories.json", "w", encoding="utf-8") as f:
            json.dump(user_edits, f, ensure_ascii=False, indent=2)
        return len(user_edits)
    except Exception as e:
        st.error(f"Error: {e}")
        return 0






# Agregar después de las funciones de categorización





def limpiar_detalle(detalle: str) -> str:
    if not isinstance(detalle, str):
        return ""
    detalle = detalle.upper()
    # Quitar tildes
    detalle = ''.join(
        c for c in unicodedata.normalize('NFD', detalle)
        if unicodedata.category(c) != 'Mn'
    )
    # Quitar caracteres no alfanuméricos
    detalle = re.sub(r'[^A-Z0-9 ]', ' ', detalle)
    # Unir palabras: PEDIDOS YA -> PEDIDOSYA
    detalle = detalle.replace(" ", "")
    return detalle


# Test con debug





# Cargar reglas iniciales
rules = load_rules()

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
    rules = load_rules()  # usa el archivo local rules.json
# ==========================
#  PROCESAMIENTO DE ARCHIVO
# ==========================

if uploaded_file:
    # --- Leer cartola según formato ---
    if uploaded_file.name.endswith(".pdf"):
        df = read_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("❌ Formato de archivo no soportado")
        st.stop()


    # --- Vista previa ---
    st.subheader("📄 Vista previa de tu cartola")
    st.dataframe(df.head(20))

    # --- Guardar CSV limpio ---
    if st.button("💾 Guardar como CSV"):
        df.to_csv("cartola_limpia.csv", index=False, encoding="utf-8-sig")
        st.success("✅ Cartola guardada como cartola_limpia.csv")

    # --- Resumen financiero mejorado ---
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


    # --- Categorización con sistema de capas ---
   # --- Categorización automática + ediciones del usuario ---
    df["CATEGORIA"] = df["DETALLE"].apply(lambda x: categorizar(x, rules))

    # Aplicar ediciones del usuario si existen
    user_categories = load_user_categories()
    cambios_aplicados = 0

    for index, row in df.iterrows():
        detalle = str(row["DETALLE"])
        if detalle in user_categories:
            df.at[index, "CATEGORIA"] = user_categories[detalle]
            cambios_aplicados += 1

    if cambios_aplicados > 0:
        st.info(f"✏️ Se aplicaron {cambios_aplicados} ediciones del usuario")

    st.subheader("📌 Todos los Movimientos Categorizados")
    st.write(f"**Total de movimientos:** {len(df)}")

    # Guardar DataFrame original para comparar cambios
    df_original = df.copy()

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

    # Botones simples
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Guardar Cambios"):
            cambios = save_user_categories(edited_df, df_original)
            if cambios > 0:
                st.success(f"✅ Guardados {cambios} cambios")
                df = edited_df.copy()
            else:
                st.info("ℹ️ No hay cambios nuevos")

    with col2:
        if st.button("🔄 Eliminar Ediciones"):
            import os
            if os.path.exists("user_categories.json"):
                os.remove("user_categories.json")
                st.success("✅ Ediciones eliminadas")
                st.experimental_rerun()
            else:
                st.info("ℹ️ No hay ediciones que eliminar")
    # --- Mostrar estadísticas de edición ---
    # --- Mostrar estadísticas de edición ---
    
    # --- Filtros interactivos (como antes) ---
    st.subheader("🔍 Filtrar por Categoría")
    categorias_disponibles = edited_df["CATEGORIA"].unique().tolist()
    categoria_seleccionada = st.selectbox("Selecciona una categoría:", ["Todas"] + categorias_disponibles)

    if categoria_seleccionada != "Todas":
        df_filtrado = edited_df[edited_df["CATEGORIA"] == categoria_seleccionada]
        st.write(f"**Movimientos de {categoria_seleccionada}:** {len(df_filtrado)}")
        st.dataframe(df_filtrado, use_container_width=True)
        
        total_categoria = df_filtrado["CARGOS"].sum()
        if total_categoria > 0:
            st.metric(f"💸 Total gastado en {categoria_seleccionada}", f"${total_categoria:,.0f}")

    # Mostrar TODOS los movimientos, no solo los primeros 20
    st.dataframe(df, use_container_width=True, height=600)

    if categoria_seleccionada != "Todas":
        df_filtrado = df[df["CATEGORIA"] == categoria_seleccionada]
        st.write(f"**Movimientos de {categoria_seleccionada}:** {len(df_filtrado)}")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Mostrar total de esa categoría
        total_categoria = df_filtrado["CARGOS"].sum()
        if total_categoria > 0:
            st.metric(f"💸 Total gastado en {categoria_seleccionada}", f"${total_categoria:,.0f}")

    # --- Gráfico de barras con Plotly ---
    st.subheader("📊 Gastos por Categoría")
    gastos_cat = edited_df[edited_df["CARGOS"] > 0].groupby("CATEGORIA")["CARGOS"].sum().reset_index()
    gastos_cat = gastos_cat.sort_values("CARGOS", ascending=False)

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

    # --- Gráfico circular con Plotly ---
    fig_pie = px.pie(
        gastos_cat, 
        values="CARGOS", 
        names="CATEGORIA",
        title="Distribución Porcentual de Gastos"
    )
    st.plotly_chart(fig_pie, use_container_width=True)