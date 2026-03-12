from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime
from models.models import EstadoApartamento, EstadoCredito

class ZonaSocialOpcionBase(BaseModel):
    nombre: str

class ZonaSocialOpcionCreate(ZonaSocialOpcionBase):
    pass

class ZonaSocialOpcionOut(ZonaSocialOpcionBase):
    id: UUID

class ProyectoBase(BaseModel):
    nombre: str
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    es_vis: bool = False
    tipo_inmueble: Optional[str] = "Apartamentos"
    zonas_sociales: Optional[Any] = None
    imagen_url: Optional[str] = None
    telefono_contacto: Optional[str] = None
    correo_contacto: Optional[str] = None
    direccion: Optional[str] = None
    admin_id: Optional[UUID] = None

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    es_vis: Optional[bool] = None
    tipo_inmueble: Optional[str] = None
    zonas_sociales: Optional[Any] = None
    imagen_url: Optional[str] = None
    telefono_contacto: Optional[str] = None
    correo_contacto: Optional[str] = None
    direccion: Optional[str] = None

class TorreBase(BaseModel):
    nombre: str
    numero_pisos: int

class TorreCreate(TorreBase):
    pass

class TorreUpdate(BaseModel):
    nombre: Optional[str] = None
    numero_pisos: Optional[int] = None

class TorreOut(TorreBase):
    numero_aptos: int
    id: UUID
    proyecto_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TipoPlantillaBase(BaseModel):
    nombre: str
    area_construida: float
    area_privada: float
    habitaciones: int
    banos: int
    imagen_url: Optional[str] = None

class TipoPlantillaCreate(TipoPlantillaBase):
    pass

class TipoPlantillaOut(TipoPlantillaBase):
    id: UUID
    proyecto_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProyectoOut(ProyectoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    torres: List[TorreOut] = []
    tipos_plantilla: List[TipoPlantillaOut] = []

    class Config:
        from_attributes = True

class ApartamentoBase(BaseModel):
    precio: float
    estado: EstadoApartamento = EstadoApartamento.disponible
    tipo_id: UUID
    piso_id: UUID
    asesor_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None

class AsesorBasico(BaseModel):
    id: UUID
    nombre_completo: str
    email: str

    class Config:
        from_attributes = True

class ApartamentoOut(ApartamentoBase):
    id: UUID
    cliente: Optional['ClienteOut'] = None
    asesor: Optional[AsesorBasico] = None

    class Config:
        from_attributes = True

class ApartamentoReservar(BaseModel):
    asesor_id: UUID
    cliente_id: UUID

class ApartamentoTipoCreate(BaseModel):
    tipo_id: UUID
    cantidad: int

class PisoBase(BaseModel):
    numero_nivel: int
    cantidad_aptos: int
    zona_social: Optional[List[str]] = None

class PisoCreate(BaseModel):
    numero_nivel: int
    apartamentos_tipos: List[ApartamentoTipoCreate]
    zona_social: Optional[List[str]] = None

class PisoOut(PisoBase):
    id: UUID
    torre_id: UUID
    apartamentos: List[ApartamentoOut] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TorreConPisosOut(TorreOut):
    pisos: List[PisoOut] = []

    class Config:
        from_attributes = True

class TipoPlantillaUpdate(BaseModel):
    nombre: Optional[str] = None
    area_construida: Optional[float] = None
    area_privada: Optional[float] = None
    habitaciones: Optional[int] = None
    banos: Optional[int] = None
    imagen_url: Optional[str] = None

class PisoUpdate(BaseModel):
    numero_nivel: Optional[int] = None
    zona_social: Optional[List[str]] = None
    apartamentos_tipos: Optional[List[ApartamentoTipoCreate]] = None

class ClienteBase(BaseModel):
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    documento_identidad: Optional[str] = None
    entidad_financiera: Optional[str] = None
    estado_credito: Optional[EstadoCredito] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    documento_identidad: Optional[str] = None
    entidad_financiera: Optional[str] = None
    estado_credito: Optional[EstadoCredito] = None

class ClienteOut(ClienteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
