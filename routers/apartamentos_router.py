from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from models.models import Apartamento, Usuario, RolUsuario, EstadoApartamento
from schemas.inmob_schemas import ApartamentoOut, ApartamentoReservar
from routers.auth_router import get_current_user

router = APIRouter(prefix="/apartamentos", tags=["Apartamentos"])

@router.get("/", response_model=List[ApartamentoOut])
def get_apartamentos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Apartamento).all()

@router.post("/{apto_id}/reservar", response_model=ApartamentoOut)
def reservar_apartamento(apto_id: UUID, data: ApartamentoReservar, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin, RolUsuario.asesor]:
        raise HTTPException(status_code=403, detail="No tienes permisos para reservar apartamentos")
        
    apto = db.query(Apartamento).filter(Apartamento.id == apto_id).first()
    if not apto:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
    try:
        apto.reservar(asesor_id=data.asesor_id, cliente_id=data.cliente_id)
        db.commit()
        db.refresh(apto)
        return apto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{apto_id}/vender", response_model=ApartamentoOut)
def vender_apartamento(apto_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in [RolUsuario.super_admin, RolUsuario.admin]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden confirmar ventas")
        
    apto = db.query(Apartamento).filter(Apartamento.id == apto_id).first()
    if not apto:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
    try:
        apto.vender()
        db.commit()
        db.refresh(apto)
        return apto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{apto_id}/liberar", response_model=ApartamentoOut)
def liberar_apartamento(apto_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    apto = db.query(Apartamento).filter(Apartamento.id == apto_id).first()
    if not apto:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
        
    apto.liberar()
    db.commit()
    db.refresh(apto)
    return apto
