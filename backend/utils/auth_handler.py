from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Usuario
from utils.security import SECRET_KEY, ALGORITHM
import jwt

def obtener_usuario_actual(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=403, detail="Token inválido.")
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="El token ha expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Token inválido.")
