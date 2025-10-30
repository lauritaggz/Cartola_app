from fastapi import APIRouter, UploadFile, File, HTTPException
from services.parser import load_rules
import json
import os

router = APIRouter(prefix="/reglas", tags=["reglas"])

@router.get("")
def obtener_reglas():
    return load_rules("rules.json")

@router.post("/upload-json")
async def subir_reglas(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Debes subir un .json")
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")
    with open("rules.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True}
