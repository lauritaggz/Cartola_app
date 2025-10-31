from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import movimientos, auth, reglas



app = FastAPI(
    title="Cartola API",
    description="Backend para análisis de cartolas bancarias",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o ["http://localhost:5173"] si usas Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(movimientos.router)
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(reglas.router, prefix="/reglas", tags=["Reglas"])

@app.get("/")
def root():
    return {"message": "🚀 API de Cartola funcionando correctamente"}
