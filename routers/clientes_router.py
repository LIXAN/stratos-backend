from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.models import Cliente, Usuario, RolUsuario
from schemas.inmob_schemas import ClienteCreate, ClienteOut, ClienteUpdate
from routers.auth_router import get_current_user

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteOut])
def get_clientes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Cliente).all()

@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def create_cliente(cliente_data: ClienteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Validate unique email if provided
    if cliente_data.email:
        existing_email = db.query(Cliente).filter(Cliente.email == cliente_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
            
    # Validate unique doc if provided
    if cliente_data.documento_identidad:
        existing_doc = db.query(Cliente).filter(Cliente.documento_identidad == cliente_data.documento_identidad).first()
        if existing_doc:
            raise HTTPException(status_code=400, detail="El documento ya está registrado")

    new_cliente = Cliente(**cliente_data.model_dump())
    db.add(new_cliente)
    db.commit()
    db.refresh(new_cliente)
    return new_cliente

@router.put("/{cliente_id}", response_model=ClienteOut)
def update_cliente(cliente_id: UUID, cliente_update: ClienteUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    update_data = cliente_update.model_dump(exclude_unset=True)
    
    if 'email' in update_data and update_data['email']:
        existing_email = db.query(Cliente).filter(Cliente.email == update_data['email'], Cliente.id != cliente_id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="El email ya está registrado por otro cliente")
            
    if 'documento_identidad' in update_data and update_data['documento_identidad']:
        existing_doc = db.query(Cliente).filter(Cliente.documento_identidad == update_data['documento_identidad'], Cliente.id != cliente_id).first()
        if existing_doc:
            raise HTTPException(status_code=400, detail="El documento ya está registrado por otro cliente")

    for key, value in update_data.items():
        setattr(cliente, key, value)
        
    db.commit()
    db.refresh(cliente)
    return cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(cliente_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar clientes")
        
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    try:
        db.delete(cliente)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se puede eliminar el cliente porque tiene registros asociados (ej. apartamentos).")
