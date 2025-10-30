from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.movimientos import router as movimientos_router

app = FastAPI(title="Cartola API (modo sin DB)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movimientos_router)

@app.get("/")
def root():
    return {"ok": True, "mensaje": "API funcionando sin base de datos 🚀"}
