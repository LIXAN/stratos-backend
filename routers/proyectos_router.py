from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import os
import shutil
import boto3
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from models.models import Proyecto, Torre, TipoPlantilla, Usuario, RolUsuario, ZonaSocialOpcion
from schemas.inmob_schemas import ProyectoCreate, ProyectoOut, ProyectoUpdate, TorreCreate, TorreUpdate, TorreOut, TipoPlantillaCreate, TipoPlantillaOut, PisoCreate, PisoOut, TipoPlantillaUpdate, TorreConPisosOut, PisoUpdate, ZonaSocialOpcionCreate, ZonaSocialOpcionOut
from routers.auth_router import get_current_user
import uuid
from models.models import Piso, Apartamento, EstadoApartamento

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])

UPLOAD_DIR = "uploads"
PROYECTOS_DIR = os.path.join(UPLOAD_DIR, "proyectos")
TIPOS_DIR = os.path.join(UPLOAD_DIR, "tipos")

os.makedirs(PROYECTOS_DIR, exist_ok=True)
os.makedirs(TIPOS_DIR, exist_ok=True)

# DigitalOcean Spaces config
SPACES_KEY = os.getenv("SPACES_KEY")
SPACES_SECRET = os.getenv("SPACES_SECRET")
SPACES_URL = os.getenv("SPACES_URL", "https://nyc3.digitaloceanspaces.com")
SPACES_BUCKET = os.getenv("SPACES_BUCKET")

s3_client = None
if SPACES_KEY and SPACES_SECRET and SPACES_BUCKET:
    s3_client = boto3.client('s3',
        region_name='nyc3',
        endpoint_url=SPACES_URL,
        aws_access_key_id=SPACES_KEY,
        aws_secret_access_key=SPACES_SECRET
    )

def upload_to_spaces_or_local(file: UploadFile, directory: str, file_name: str) -> str:
    if s3_client:
        # Subir a DigitalOcean Spaces
        object_name = f"{directory}/{file_name}"
        s3_client.upload_fileobj(
            file.file,
            SPACES_BUCKET,
            object_name,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": file.content_type
            }
        )
        # Reconstruir la URL pública asumiendo el formato estándar de DO Spaces:
        # https://{bucket_name}.{region}.digitaloceanspaces.com/{object_name}
        base_url = SPACES_URL.replace("https://", f"https://{SPACES_BUCKET}.")
        return f"{base_url}/{object_name}"
    else:
        # Subir localmente (fallback para desarrollo)
        dir_path = os.path.join(UPLOAD_DIR, directory)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return f"/api/uploads/{directory}/{file_name}"

@router.post("/upload-image", response_model=dict)
def upload_proyecto_image(file: UploadFile = File(...), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para subir imágenes")
    
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    
    image_url = upload_to_spaces_or_local(file, "proyectos", file_name)
    return {"imagen_url": image_url}

@router.post("/tipos/upload-image", response_model=dict)
def upload_tipo_image(file: UploadFile = File(...), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para subir imágenes")
        
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"

    image_url = upload_to_spaces_or_local(file, "tipos", file_name)
    return {"imagen_url": image_url}

@router.get("/zonas-sociales/opciones", response_model=List[ZonaSocialOpcionOut])
def get_zonas_sociales_opciones(db: Session = Depends(get_db)):
    return db.query(ZonaSocialOpcion).all()

@router.post("/zonas-sociales/opciones", response_model=ZonaSocialOpcionOut)
def create_zona_social_opcion(zona: ZonaSocialOpcionCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear opciones de zonas sociales")
    
    # Check if exists (case insensitive could be better, but exact match for now)
    existing = db.query(ZonaSocialOpcion).filter(ZonaSocialOpcion.nombre == zona.nombre).first()
    if existing:
        raise HTTPException(status_code=400, detail="Esa zona social ya existe")
        
    new_zona = ZonaSocialOpcion(nombre=zona.nombre)
    db.add(new_zona)
    db.commit()
    db.refresh(new_zona)
    return new_zona

@router.get("", response_model=List[ProyectoOut])
def get_proyectos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Proyecto).all()

@router.post("", response_model=ProyectoOut)
def create_proyecto(proyecto: ProyectoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear proyectos")
    
    new_proyecto = Proyecto(**proyecto.model_dump())
    db.add(new_proyecto)
    db.commit()
    db.refresh(new_proyecto)
    return new_proyecto

@router.get("/{proyecto_id}", response_model=ProyectoOut)
def get_proyecto(proyecto_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto

@router.get("/{proyecto_id}/disponibilidad", response_model=List[TorreConPisosOut])
def get_proyecto_disponibilidad(proyecto_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto.torres

@router.put("/{proyecto_id}", response_model=ProyectoOut)
def update_proyecto(proyecto_id: uuid.UUID, proyecto_update: ProyectoUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar proyectos")
    
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    update_data = proyecto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(proyecto, key, value)
        
    db.commit()
    db.refresh(proyecto)
    return proyecto

@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proyecto(proyecto_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != RolUsuario.super_admin:
        raise HTTPException(status_code=403, detail="Solo los super administradores pueden eliminar proyectos")
    
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    db.delete(proyecto)
    db.commit()
    return None

@router.post("/{proyecto_id}/torres", response_model=TorreOut)
def create_torre(proyecto_id: uuid.UUID, torre: TorreCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear torres")
    
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    torre.nombre = " ".join(torre.nombre.split())
    
    existing_torre = db.query(Torre).filter(
        Torre.proyecto_id == proyecto_id,
        func.lower(func.replace(Torre.nombre, ' ', '')) == torre.nombre.lower().replace(' ', '')
    ).first()
    if existing_torre:
        raise HTTPException(status_code=400, detail=f"Ya existe una torre o manzana con el nombre '{existing_torre.nombre}' en este proyecto.")
        
    new_torre = Torre(nombre=torre.nombre, numero_pisos=torre.numero_pisos, proyecto_id=proyecto_id)
    db.add(new_torre)
    db.commit()
    db.refresh(new_torre)
    return new_torre

@router.put("/{proyecto_id}/torres/{torre_id}", response_model=TorreOut)
def update_torre(proyecto_id: uuid.UUID, torre_id: uuid.UUID, torre_update: TorreUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar torres")
    
    torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
        
    if torre_update.nombre:
        torre_update.nombre = " ".join(torre_update.nombre.split())
        existing_torre = db.query(Torre).filter(
            Torre.id != torre_id,
            Torre.proyecto_id == proyecto_id,
            func.lower(func.replace(Torre.nombre, ' ', '')) == torre_update.nombre.lower().replace(' ', '')
        ).first()
        if existing_torre:
            raise HTTPException(status_code=400, detail=f"Ya existe una torre o manzana con el nombre '{existing_torre.nombre}' en este proyecto.")
            
    update_data = torre_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(torre, key, value)
        
    db.commit()
    db.refresh(torre)
    return torre

@router.post("/{proyecto_id}/tipos", response_model=TipoPlantillaOut)
def create_tipo_plantilla(proyecto_id: uuid.UUID, tipo: TipoPlantillaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear tipos de apartamento")
    
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    tipo.nombre = " ".join(tipo.nombre.split())

    # Check for duplicate name (case-insensitive and ignoring spaces)
    existing_tipo = db.query(TipoPlantilla).filter(
        TipoPlantilla.proyecto_id == proyecto_id, 
        func.lower(func.replace(TipoPlantilla.nombre, ' ', '')) == tipo.nombre.lower().replace(' ', '')
    ).first()
    if existing_tipo:
        raise HTTPException(status_code=400, detail=f"Ya existe un tipo de apartamento con el nombre '{existing_tipo.nombre}' en este proyecto.")
        
    new_tipo = TipoPlantilla(**tipo.model_dump(), proyecto_id=proyecto_id)
    db.add(new_tipo)
    db.commit()
    db.refresh(new_tipo)
    return new_tipo
@router.get("/{proyecto_id}/torres/{torre_id}", response_model=TorreConPisosOut)
def get_torre(proyecto_id: uuid.UUID, torre_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
    return torre

@router.post("/{proyecto_id}/torres/{torre_id}/duplicar", response_model=TorreConPisosOut)
def duplicate_torre(proyecto_id: uuid.UUID, torre_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para duplicar torres")
        
    original_torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not original_torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
        
    base_name = original_torre.nombre
    new_torre_name = base_name + " (Copia)"
    counter = 1
    
    while True:
        existing_copy = db.query(Torre).filter(
            Torre.proyecto_id == proyecto_id,
            func.lower(func.replace(Torre.nombre, ' ', '')) == new_torre_name.lower().replace(' ', '')
        ).first()
        if not existing_copy:
            break
        counter += 1
        new_torre_name = f"{base_name} (Copia {counter})"
    
    nuevo_torre = Torre(
        nombre=new_torre_name,
        numero_pisos=original_torre.numero_pisos,
        numero_aptos=original_torre.numero_aptos,
        proyecto_id=proyecto_id
    )
    db.add(nuevo_torre)
    db.flush()
    
    from models.models import Piso, Apartamento
    for original_piso in original_torre.pisos:
        nuevo_piso = Piso(
            numero_nivel=original_piso.numero_nivel,
            cantidad_aptos=original_piso.cantidad_aptos,
            zona_social=original_piso.zona_social,
            torre_id=nuevo_torre.id
        )
        db.add(nuevo_piso)
        db.flush()
        
        for original_apto in original_piso.apartamentos:
            db.add(Apartamento(
                precio=original_apto.precio,
                tipo_id=original_apto.tipo_id,
                piso_id=nuevo_piso.id,
                estado=EstadoApartamento.disponible
            ))
            
    db.commit()
    db.refresh(nuevo_torre)
    return nuevo_torre

@router.post("/{proyecto_id}/torres/{torre_id}/pisos", response_model=PisoOut)
def create_piso(proyecto_id: uuid.UUID, torre_id: uuid.UUID, piso: PisoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear pisos")
    
    torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
        
    existing_piso = db.query(Piso).filter(Piso.torre_id == torre_id, Piso.numero_nivel == piso.numero_nivel).first()
    if existing_piso:
        raise HTTPException(status_code=400, detail=f"Ya existe un piso con el número de nivel {piso.numero_nivel} en esta torre")
        
    # Calculate bounds from input
    cantidad_aptos = sum(apto_tipo.cantidad for apto_tipo in piso.apartamentos_tipos)
    
    new_piso = Piso(numero_nivel=piso.numero_nivel, cantidad_aptos=cantidad_aptos, torre_id=torre_id, zona_social=piso.zona_social)
    db.add(new_piso)
    
    # Update Torre total
    torre.numero_aptos += cantidad_aptos
    
    db.flush() # flush to get new_piso.id
    
    from models.models import Apartamento
    for apto_tipo in piso.apartamentos_tipos:
        for _ in range(apto_tipo.cantidad):
            db.add(Apartamento(
                precio=0.0,
                tipo_id=apto_tipo.tipo_id,
                piso_id=new_piso.id
            ))
            
    db.commit()
    db.refresh(new_piso)
    return new_piso

@router.put("/{proyecto_id}/tipos/{tipo_id}", response_model=TipoPlantillaOut)
def update_tipo_plantilla(proyecto_id: uuid.UUID, tipo_id: uuid.UUID, data: TipoPlantillaUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar tipos de apartamento")
        
    tipo = db.query(TipoPlantilla).filter(TipoPlantilla.id == tipo_id, TipoPlantilla.proyecto_id == proyecto_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de apartamento no encontrado")
        
    if data.nombre is not None:
        data.nombre = " ".join(data.nombre.split())

    if data.nombre is not None and data.nombre.lower().replace(' ', '') != tipo.nombre.lower().replace(' ', ''):
        # Check for duplicate name (case-insensitive and ignoring spaces)
        existing_tipo = db.query(TipoPlantilla).filter(
            TipoPlantilla.proyecto_id == proyecto_id, 
            func.lower(func.replace(TipoPlantilla.nombre, ' ', '')) == data.nombre.lower().replace(' ', '')
        ).first()
        if existing_tipo:
            raise HTTPException(status_code=400, detail=f"Ya existe un tipo de apartamento con el nombre '{existing_tipo.nombre}' en este proyecto.")
            
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tipo, key, value)
        
    db.commit()
    db.refresh(tipo)
    return tipo

@router.delete("/{proyecto_id}/tipos/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_plantilla(proyecto_id: uuid.UUID, tipo_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar tipos de apartamento")
        
    tipo = db.query(TipoPlantilla).filter(TipoPlantilla.id == tipo_id, TipoPlantilla.proyecto_id == proyecto_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de apartamento no encontrado")
        
    from models.models import Apartamento
    aptos_usando_tipo = db.query(Apartamento).filter(Apartamento.tipo_id == tipo_id).count()
    if aptos_usando_tipo > 0:
        raise HTTPException(status_code=400, detail="No procesable: Hay apartamentos existentes que utilizan este Tipo de Plantilla. Bórrelos primero.")
        
    db.delete(tipo)
    db.commit()
    return None

from schemas.inmob_schemas import ApartamentoOut
@router.get("/{proyecto_id}/torres/{torre_id}/pisos/{piso_id}/apartamentos", response_model=List[ApartamentoOut])
def get_apartamentos_por_piso(proyecto_id: uuid.UUID, torre_id: uuid.UUID, piso_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    piso = db.query(Piso).filter(Piso.id == piso_id, Piso.torre_id == torre_id).first()
    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")
        
    from models.models import Apartamento
    apartamentos = db.query(Apartamento).filter(Apartamento.piso_id == piso_id).all()
    return apartamentos

@router.put("/{proyecto_id}/torres/{torre_id}/pisos/{piso_id}", response_model=PisoOut)
def update_piso(proyecto_id: uuid.UUID, torre_id: uuid.UUID, piso_id: uuid.UUID, data: PisoUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar pisos")
        
    torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
        
    piso = db.query(Piso).filter(Piso.id == piso_id, Piso.torre_id == torre_id).first()
    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")
        
    if data.zona_social is not None:
        piso.zona_social = data.zona_social
    if data.numero_nivel is not None and data.numero_nivel != piso.numero_nivel:
        existing_piso = db.query(Piso).filter(Piso.torre_id == torre_id, Piso.numero_nivel == data.numero_nivel).first()
        if existing_piso:
            raise HTTPException(status_code=400, detail=f"Ya existe un piso con el número de nivel {data.numero_nivel} en esta torre")
        piso.numero_nivel = data.numero_nivel
        
    if data.apartamentos_tipos is not None:
        # Reconcile apartments
        current_aptos = db.query(Apartamento).filter(Apartamento.piso_id == piso.id).all()
        current_counts = {}
        for apto in current_aptos:
            tipo_id_str = str(apto.tipo_id)
            if tipo_id_str not in current_counts:
                current_counts[tipo_id_str] = 0
            current_counts[tipo_id_str] += 1
            
        target_counts = {str(item.tipo_id): item.cantidad for item in data.apartamentos_tipos}
        
        # Calculate diffs
        all_tipo_ids = set(current_counts.keys()).union(set(target_counts.keys()))
        
        for tipo_id_str in all_tipo_ids:
            curr = current_counts.get(tipo_id_str, 0)
            target = target_counts.get(tipo_id_str, 0)
            
            if target > curr:
                # Add apartments
                to_add = target - curr
                for _ in range(to_add):
                    db.add(Apartamento(
                        precio=0.0,
                        tipo_id=uuid.UUID(tipo_id_str),
                        piso_id=piso.id
                    ))
                torre.numero_aptos += to_add
                piso.cantidad_aptos += to_add
                
            elif target < curr:
                # Remove apartments safely
                to_remove = curr - target
                # Find available ones of this type
                available_aptos = [a for a in current_aptos if str(a.tipo_id) == tipo_id_str and a.estado == EstadoApartamento.disponible]
                
                if len(available_aptos) < to_remove:
                    # Cannot safely remove
                    raise HTTPException(status_code=400, detail=f"No se puede reducir la cantidad. Hay apartamentos ocupados/reservados que impiden la reducción.")
                    
                for i in range(to_remove):
                    db.delete(available_aptos[i])
                    
                torre.numero_aptos -= to_remove
                piso.cantidad_aptos -= to_remove

    db.commit()
    db.refresh(piso)
    return piso

@router.delete("/{proyecto_id}/torres/{torre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_torre(proyecto_id: uuid.UUID, torre_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar torres")
        
    torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
        
    db.delete(torre)
    db.commit()
    return None

@router.delete("/{proyecto_id}/torres/{torre_id}/pisos/{piso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_piso(proyecto_id: uuid.UUID, torre_id: uuid.UUID, piso_id: uuid.UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar pisos")
        
    torre = db.query(Torre).filter(Torre.id == torre_id, Torre.proyecto_id == proyecto_id).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
        
    piso = db.query(Piso).filter(Piso.id == piso_id, Piso.torre_id == torre_id).first()
    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")
        
    # We must explicitly subtract this floor's capacity from the Tower total
    torre.numero_aptos = max(0, torre.numero_aptos - piso.cantidad_aptos)
    
    db.delete(piso)
    db.commit()
    return None
