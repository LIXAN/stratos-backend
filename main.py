from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import os # Importante para leer las variables de DigitalOcean

# Base.metadata.create_all(bind=engine) # Se utilizará Alembic mejor

app = FastAPI(
    title="Planimy API - Lexian", 
    version="1.0.0",
    description="Backend para la gestión de inventario inmobiliario"
)

# --- CONFIGURACIÓN DE CORS PARA PRODUCCIÓN ---
# Aquí permitimos que el dominio real de Planimy se comunique con la API
origins = [
    "http://localhost:5173",          # Desarrollo local
    "http://127.0.0.1:5173",         # Desarrollo local alterno
    "https://planimy.com",            # Tu dominio principal
    "https://www.planimy.com",        # Versión con www
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IMPORTACIÓN DE ROUTERS ---
from routers import auth_router, proyectos_router, apartamentos_router, rrhh_router

app.include_router(auth_router.router)
app.include_router(proyectos_router.router)
app.include_router(apartamentos_router.router)
app.include_router(rrhh_router.router)

# --- ENDPOINTS DE CONTROL ---

@app.get("/")
def read_root():
    return {
        "message": "API Backend Planimy funcionando",
        "brand": "Lexian",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    raw_url = str(os.getenv("DATABASE_URL", "local"))
    
    # Construimos el prefijo manualmente para evitar el error de "index into str"
    prefix = ""
    for i, char in enumerate(raw_url):
        if i < 15:
            prefix += char
        else:
            break
            
    return {
        "status": "online",
        "environment": f"{prefix}...",
        "version": "1.0.0",
        "brand": "Lexian"
    }