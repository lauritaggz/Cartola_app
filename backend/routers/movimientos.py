
import pandas as pd
from services.parser import read_pdf, load_rules, categorizar
import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query

# Si no estás usando base de datos real:
from typing import Optional
from fastapi import Depends

# Simulación de una sesión vacía (placeholder)
class FakeDB:
    def add(self, *args, **kwargs): pass
    def commit(self): pass
    def query(self, *args, **kwargs): return []

def get_db():
    return FakeDB()

Session = FakeDB  # Evita error de tipo

router = APIRouter(prefix="/movimientos", tags=["movimientos"])

# 🧠 almacenamiento temporal en memoria
MOVIMIENTOS_CACHE = []

@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    password: str = Form(None),  # 👈 Recibir contraseña opcional
    db: Session = Depends(get_db)
):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Sube un PDF válido")

    import io
    content = await file.read()
    buffer = io.BytesIO(content)

    try:
        df, saldo_inicial, saldo_final = read_pdf(buffer, password=password)  # 👈 Se pasa el password
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error al leer PDF: {e}")


    rules = load_rules("rules.json")
    df["CATEGORIA"] = df["DETALLE"].apply(lambda x: categorizar(x, rules))

    # Guardar temporalmente en memoria
    MOVIMIENTOS_CACHE.clear()
    for _, row in df.iterrows():
        MOVIMIENTOS_CACHE.append({
            "fecha": str(row["FECHA"]),
            "detalle": str(row["DETALLE"]),
            "cargos": float(row["CARGOS"]) if pd.notnull(row["CARGOS"]) else 0.0,
            "abonos": float(row["ABONOS"]) if pd.notnull(row["ABONOS"]) else 0.0,
            "categoria": str(row["CATEGORIA"]) if pd.notnull(row["CATEGORIA"]) else None,
        })

    return {
        "ok": True,
        "insertados": len(df),
        "saldo_inicial": saldo_inicial,
        "saldo_final": saldo_final
    }


@router.get("")
def listar_movimientos():
    return MOVIMIENTOS_CACHE
