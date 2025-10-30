from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.session import Base

# === USUARIO ===
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(200), nullable=False)

    # Relación con movimientos
    movimientos = relationship("Movimiento", back_populates="usuario")


# === MOVIMIENTO ===
class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(50))
    detalle = Column(String(255))
    cargos = Column(Float, default=0)
    abonos = Column(Float, default=0)
    categoria = Column(String(100))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    # Relación inversa
    usuario = relationship("Usuario", back_populates="movimientos")
