from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from models.models import EstadoEmpleado, ModalidadTrabajo, RolUsuario

class CargoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CargoCreate(CargoBase):
    pass

class CargoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class CargoOut(CargoBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class EmpleadoBase(BaseModel):
    nombre_completo: str
    documento_identidad: Optional[str] = None
    cargo_id: Optional[UUID] = None
    telefono: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    salario: Optional[float] = None
    estado: EstadoEmpleado = EstadoEmpleado.activo
    modalidad: Optional[ModalidadTrabajo] = None
    rol: Optional[RolUsuario] = None
    usuario_id: Optional[UUID] = None

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    documento_identidad: Optional[str] = None
    cargo_id: Optional[UUID] = None
    telefono: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    salario: Optional[float] = None
    estado: Optional[EstadoEmpleado] = None
    modalidad: Optional[ModalidadTrabajo] = None
    rol: Optional[RolUsuario] = None
    usuario_id: Optional[UUID] = None

class EmpleadoOut(EmpleadoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
