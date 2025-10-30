from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Usuario
from utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(nombre: str, email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    nuevo = Usuario(nombre=nombre, email=email, password=hash_password(password))
    db.add(nuevo)
    db.commit()
    return {"ok": True, "mensaje": "Usuario registrado correctamente"}

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_access_token({"sub": user.email})
    return {"ok": True, "access_token": token, "usuario": user.email}
