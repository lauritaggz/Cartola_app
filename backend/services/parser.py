# backend/services/parser.py
import pandas as pd
import pdfplumber
import json
import re
import unicodedata
from io import BytesIO
# reportlab imports si usarás PDF:
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch

def read_pdf(archivo, password=None) -> tuple:
    """
    Lee una cartola bancaria en PDF y devuelve un DataFrame y los saldos
    con las columnas: FECHA, DETALLE, CARGOS, ABONOS
    Retorna: (DataFrame, saldo_inicial, saldo_final)
    """
    rows = []
    saldo_inicial = None
    saldo_final = None
    
    try:
        with pdfplumber.open(archivo, password=password) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                
                if tables:
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        # Normalizar encabezado
                        header = [str(h).strip().upper() for h in table[0] if h]
                        
                        # Detectar si hay encabezados claros
                        tiene_encabezado = any(
                            any(palabra in h for palabra in ["FECHA", "DESCRIP", "DETALLE", "CARGO", "ABONO", "SALDO"])
                            for h in header
                        )
                        
                        # 🟢 NUEVO: si hay encabezados, mapear dinámicamente (Falabella, Scotiabank, etc.)
                        if tiene_encabezado:
                            idx_fecha = next((i for i, h in enumerate(header) if "FECHA" in h), None)
                            idx_detalle = next((i for i, h in enumerate(header) if "DESCRIP" in h or "DETALLE" in h), None)
                            idx_cargo = next((i for i, h in enumerate(header) if "CARGO" in h or "DÉBITO" in h), None)
                            idx_abono = next((i for i, h in enumerate(header) if "ABONO" in h or "CRÉDITO" in h), None)
                            
                            # Si alguna columna clave no existe, saltamos
                            if idx_fecha is None or idx_detalle is None:
                                continue
                            
                            # Procesar filas desde la segunda
                            for row in table[1:]:
                                try:
                                    fecha = str(row[idx_fecha]).strip()
                                    descripcion = str(row[idx_detalle]).strip()
                                    cargos_str = str(row[idx_cargo]) if idx_cargo is not None and len(row) > idx_cargo else "0"
                                    abonos_str = str(row[idx_abono]) if idx_abono is not None and len(row) > idx_abono else "0"

                                    # Limpieza de montos
                                    def limpiar_monto(v):
                                        try:
                                            return int(str(v).replace("$", "").replace(".", "").replace(",", "").strip() or "0")
                                        except:
                                            return 0
                                    
                                    cargo = limpiar_monto(cargos_str)
                                    abono = limpiar_monto(abonos_str)

                                    if cargo > 0 or abono > 0:
                                        rows.append([fecha, descripcion, cargo, abono])
                                except Exception:
                                    continue
                            
                            # Ir a la siguiente tabla
                            continue
                        
                        # 🔵 Si no hay encabezado, seguir con el modo clásico (BancoEstado / BancoChile)
                        for row in table:
                            if not row or len(row) < 3:
                                continue
                            
                            # Buscar saldos
                            if row[0] and "Saldo Anterior" or "SALDO INICIAL" in str(row[0]):
                                try:
                                    saldo_inicial = int(str(row[1]).replace(".", "").replace(",", "").replace("$", "").strip())
                                except:
                                    pass
                            if row[0] and "Saldo Final" in str(row[0]):
                                try:
                                    saldo_final = int(str(row[1]).replace(".", "").replace(",", "").replace("$", "").strip())
                                except:
                                    pass
                            
                            # Detectar filas con fecha (ej: "11/Ago." o "28/Jul.")
                            fecha_str = str(row[0]).strip() if row[0] else ""
                            if re.match(r"^\d{1,2}/[A-Za-z]{3}", fecha_str):
                                try:
                                    fecha = fecha_str
                                    descripcion = str(row[2]) if len(row) > 2 else ""
                                    abonos_str = str(row[3]) if len(row) > 3 else ""
                                    cargos_str = str(row[4]) if len(row) > 4 else ""
                                    
                                    abono = 0
                                    cargo = 0
                                    
                                    if abonos_str.strip() and abonos_str != "None":
                                        try:
                                            abono = int(abonos_str.replace("$", "").replace(".", "").replace(",", "").strip())
                                        except:
                                            pass
                                    if cargos_str.strip() and cargos_str != "None":
                                        try:
                                            cargo = int(cargos_str.replace("$", "").replace(".", "").replace(",", "").strip())
                                        except:
                                            pass
                                    
                                    if cargo > 0 or abono > 0:
                                        descripcion = descripcion.strip()
                                        rows.append([fecha, descripcion, cargo, abono])
                                except:
                                    continue
                
                # 🟠 Fallback: modo texto si no hay tablas detectadas
                if not rows:
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Saldos
                        if "SALDO ANTERIOR" in line.upper():
                            nums = re.findall(r"[\d\.\,]+", line)
                            if nums:
                                try:
                                    saldo_inicial = int(nums[-1].replace(".", "").replace(",", ""))
                                except:
                                    pass
                            continue
                        if "SALDO FINAL" in line.upper():
                            nums = re.findall(r"[\d\.\,]+", line)
                            if nums:
                                try:
                                    saldo_final = int(nums[-1].replace(".", "").replace(",", ""))
                                except:
                                    pass
                            continue
                        
                        # Movimientos (formato texto)
                        fecha_match = re.match(r"^(\d{1,2}/(?:\d{1,2}|[A-Za-z]{3}\.?))\s+(.+)", line)
                        if fecha_match:
                            fecha = fecha_match.group(1)
                            resto = fecha_match.group(2).strip()
                            numeros = re.findall(r"[\d\.\,]+", resto)
                            montos = [int(n.replace(".", "").replace(",", "")) for n in numeros if len(n) >= 3]
                            
                            if montos:
                                monto = montos[-2] if len(montos) >= 2 else montos[0]
                                es_abono = any(w in resto.upper() for w in ["ABONO", "DEPOSITO", "SUELDO", "TRASPASO DE", "TEF DESDE"])
                                cargo, abono = (0, monto) if es_abono else (monto, 0)
                                
                                descripcion = limpiar_descripcion_numerica(resto, numeros)
                                descripcion = re.sub(r"\s+", " ", descripcion).strip().rstrip(":")
                                rows.append([fecha, descripcion, cargo, abono])
        
        if not rows:
            raise ValueError("⚠️ No se detectaron movimientos en el PDF.")
        
        return pd.DataFrame(rows, columns=["FECHA", "DETALLE", "CARGOS", "ABONOS"]), saldo_inicial, saldo_final
    
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise ValueError("🔒 El PDF está protegido con contraseña")
        else:
            raise e


        
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

def load_rules(file_path="/rules.json"):
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
        r"TEF\s+(DESDE)[\s:]",
        r"TRANSF\s+(DE)[\s:]",
        r"TRANSF\s+(PARA)[\s:]",
    ]
    
    for patron in patrones_transferencia:
        if re.search(patron, detalle_norm_original):
            es_transferencia = True
            break
    
    # También detectar si contiene TRASPASO o TRANSFERENCIA (sin comisión ya verificada arriba)
    if not es_transferencia:
        palabras_transferencia = ["TRASPASO", "TRANSFERENCIA","TRANSF"]
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

