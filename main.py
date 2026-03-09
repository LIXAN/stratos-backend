from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import os # Importante para leer las variables de DigitalOcean

# Base.metadata.create_all(bind=engine) # Se utilizará Alembic mejor

app = FastAPI(
    title="Planimy API - LIXAN", 
    version="1.0.0",
)

from alembic import command
from alembic.config import Config
import traceback

@app.on_event("startup")
def run_migrations():
    try:
        print("Starting Alembic migrations locally via API...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Alembic migrations successful.")
    except Exception as e:
        print(f"Error running migrations: {e}")
        traceback.print_exc()

# Serve uploaded files
import os
os.makedirs("uploads", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

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

import io
from fastapi.responses import PlainTextResponse

@app.get("/run-migrations", response_class=PlainTextResponse)
def trigger_migrations():
    import subprocess
    try:
        from database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Si la tabla de proyectos/tipos existe pero no hay historial de alembic,
        # significa que la BD es vieja y necesitamos sellarla en la versión inicial.
        out = ""
        if "tipos_plantilla" in tables and "alembic_version" not in tables:
            out += "Legacy database detected! Stamping initial schema (1be94bebf9c4)...\n"
            stamp_res = subprocess.run(["alembic", "stamp", "1be94bebf9c4"], capture_output=True, text=True, check=True)
            out += stamp_res.stdout + "\n"
        
        out += "Starting Alembic migrations upgrades...\n"
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True, check=True)
        return "SUCCESS:\n" + out + result.stdout
    except subprocess.CalledProcessError as e:
        return "ERROR:\n" + e.stdout + "\nSTDERR:\n" + e.stderr
    except Exception as e:
        return f"UNEXPECTED ERROR:\n{str(e)}"
        
@app.get("/")
def read_root():
    return {
        "message": "API Backend Planimy funcionando",
        "brand": "LIXAN",
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
        "brand": "LIXAN"
    }