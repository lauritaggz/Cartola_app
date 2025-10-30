from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -----------------------------------------------------------
# 🚀 CONFIGURACIÓN DE LA BASE DE DATOS
# -----------------------------------------------------------

# ⚙️ Cambia 'cartola_db' si tu base tiene otro nombre
DATABASE_URL = "mysql+pymysql://root:@localhost/cartola_db"

# 🧠 Crear el motor de conexión
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Muestra en consola las consultas SQL (útil para debug)
)

# 🧱 Declarar la clase Base (fundamental para los modelos)
Base = declarative_base()

# 🔄 Crear la sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------------------------------------
# 💾 Dependencia para FastAPI (inyecta la sesión en endpoints)
# -----------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
