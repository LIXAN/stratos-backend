from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.models import Empleado, Usuario, RolUsuario, Cargo
from schemas.rrhh_schemas import EmpleadoCreate, EmpleadoUpdate, EmpleadoOut, CargoCreate, CargoUpdate, CargoOut
from routers.auth_router import get_current_user

router = APIRouter(prefix="/rrhh", tags=["RRHH"])

@router.get("/empleados", response_model=List[EmpleadoOut])
def get_empleados(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtiene la lista de todos los empleados."""
    from sqlalchemy.orm import joinedload
    empleados = db.query(Empleado).options(joinedload(Empleado.cargo)).order_by(Empleado.created_at.desc()).offset(skip).limit(limit).all()
    return empleados

@router.post("/empleados", response_model=EmpleadoOut, status_code=status.HTTP_201_CREATED)
def create_empleado(
    empleado_in: EmpleadoCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo empleado."""
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear empleados")

    nuevo_empleado = Empleado(**empleado_in.model_dump())
    db.add(nuevo_empleado)
    db.commit()
    db.refresh(nuevo_empleado)
    return nuevo_empleado

@router.put("/empleados/{empleado_id}", response_model=EmpleadoOut)
def update_empleado(
    empleado_id: UUID,
    empleado_in: EmpleadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza la información de un empleado existente."""
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar empleados")

    empleado_db = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado_db:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    update_data = empleado_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(empleado_db, key, value)

    db.commit()
    db.refresh(empleado_db)
    return empleado_db

@router.delete("/empleados/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_empleado(
    empleado_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina permanentemente un empleado."""
    if current_user.rol not in [RolUsuario.super_admin]:
        raise HTTPException(status_code=403, detail="Solo los super_admin pueden eliminar empleados permanentemente")

    empleado_db = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado_db:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    db.delete(empleado_db)
    db.commit()

# --- Rutas de Cargos ---

@router.get("/cargos", response_model=List[CargoOut])
def get_cargos(db: Session = Depends(get_db)):
    """Obtiene la lista de todos los cargos."""
    return db.query(Cargo).order_by(Cargo.nombre).all()

@router.post("/cargos", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
def create_cargo(
    cargo_in: CargoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo cargo."""
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear cargos")
        
    cargo_existente = db.query(Cargo).filter(Cargo.nombre == cargo_in.nombre).first()
    if cargo_existente:
        raise HTTPException(status_code=400, detail="Este cargo ya existe")

    nuevo_cargo = Cargo(**cargo_in.model_dump())
    db.add(nuevo_cargo)
    db.commit()
    db.refresh(nuevo_cargo)
    return nuevo_cargo

@router.put("/cargos/{cargo_id}", response_model=CargoOut)
def update_cargo(
    cargo_id: UUID,
    cargo_in: CargoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza la información de un cargo existente."""
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar cargos")

    cargo_db = db.query(Cargo).filter(Cargo.id == cargo_id).first()
    if not cargo_db:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")

    update_data = cargo_in.model_dump(exclude_unset=True)
    
    # Simple duplicate check if name is changed
    if "nombre" in update_data and update_data["nombre"] != cargo_db.nombre:
        if db.query(Cargo).filter(Cargo.nombre == update_data["nombre"]).first():
            raise HTTPException(status_code=400, detail="Ya existe otro cargo con ese nombre")

    for key, value in update_data.items():
        setattr(cargo_db, key, value)

    db.commit()
    db.refresh(cargo_db)
    return cargo_db

@router.delete("/cargos/{cargo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cargo(
    cargo_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina permanentemente un cargo."""
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar cargos")

    cargo_db = db.query(Cargo).filter(Cargo.id == cargo_id).first()
    if not cargo_db:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")

    # Check if there are employees using this cargo before deleting
    empleados_con_cargo = db.query(Empleado).filter(Empleado.cargo_id == cargo_id).count()
    if empleados_con_cargo > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar el cargo porque hay empleados asignados a él")

    db.delete(cargo_db)
    db.commit()
