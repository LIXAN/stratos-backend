import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import Base
import enum

class EstadoApartamento(enum.Enum):
    disponible = "disponible"
    reservado = "reservado"
    vendido = "vendido"

class RolUsuario(enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    asesor = "asesor"

class EstadoCredito(enum.Enum):
    preaprobado = "preaprobado"
    aprobado = "aprobado"
    definitivo = "definitivo"

class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Usuario(BaseModel):
    __tablename__ = "usuarios"
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False)
    nombre_completo = Column(String, nullable=False)

class Comprador(BaseModel):
    __tablename__ = "compradores"
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    entidad_financiera = Column(String, nullable=True)
    estado_credito = Column(Enum(EstadoCredito), nullable=True)

class ZonaSocialOpcion(Base):
    __tablename__ = "zona_social_opcion"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, unique=True, nullable=False)

class Proyecto(BaseModel):
    __tablename__ = "proyectos"
    nombre = Column(String, nullable=False)
    departamento = Column(String, nullable=True)
    ciudad = Column(String, nullable=True)
    es_vis = Column(Boolean, default=False)
    tipo_inmueble = Column(String, default="Apartamentos")
    zonas_sociales = Column(JSON, nullable=True)
    imagen_url = Column(String, nullable=True)
    telefono_contacto = Column(String, nullable=True)
    correo_contacto = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    
    torres = relationship("Torre", back_populates="proyecto")
    admin = relationship("Usuario", foreign_keys=[admin_id])
    tipos_plantilla = relationship("TipoPlantilla", back_populates="proyecto")

class Torre(BaseModel):
    __tablename__ = "torres"
    nombre = Column(String, nullable=False)
    numero_pisos = Column(Integer, nullable=False)
    numero_aptos = Column(Integer, default=0, nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"))
    
    proyecto = relationship("Proyecto", back_populates="torres")
    pisos = relationship("Piso", back_populates="torre", cascade="all, delete-orphan")
    
    def get_disponibles(self):
        return sum(a.estado == EstadoApartamento.disponible for p in self.pisos for a in p.apartamentos)
    
    def get_reservados(self):
        return sum(a.estado == EstadoApartamento.reservado for p in self.pisos for a in p.apartamentos)
    
    def get_vendidos(self):
        return sum(a.estado == EstadoApartamento.vendido for p in self.pisos for a in p.apartamentos)

class Piso(BaseModel):
    __tablename__ = "pisos"
    numero_nivel = Column(Integer, nullable=False)
    cantidad_aptos = Column(Integer, nullable=False)
    zona_social = Column(JSON, nullable=True) # Changed from String to JSON to support multiple areas
    torre_id = Column(UUID(as_uuid=True), ForeignKey("torres.id"))
    
    torre = relationship("Torre", back_populates="pisos")
    apartamentos = relationship("Apartamento", back_populates="piso", cascade="all, delete-orphan")

class TipoPlantilla(BaseModel):
    __tablename__ = "tipos_plantilla"
    nombre = Column(String, nullable=False)
    area_construida = Column(Float, nullable=False)
    area_privada = Column(Float, nullable=False)
    habitaciones = Column(Integer, nullable=False)
    banos = Column(Integer, nullable=False)
    imagen_url = Column(String, nullable=True)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True)

    proyecto = relationship("Proyecto", back_populates="tipos_plantilla")

class Apartamento(BaseModel):
    __tablename__ = "apartamentos"
    precio = Column(Float, nullable=False)
    estado = Column(Enum(EstadoApartamento), default=EstadoApartamento.disponible)
    
    tipo_id = Column(UUID(as_uuid=True), ForeignKey("tipos_plantilla.id"))
    piso_id = Column(UUID(as_uuid=True), ForeignKey("pisos.id"))
    asesor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    comprador_id = Column(UUID(as_uuid=True), ForeignKey("compradores.id"), nullable=True)
    
    tipo = relationship("TipoPlantilla")
    piso = relationship("Piso", back_populates="apartamentos")
    asesor = relationship("Usuario", foreign_keys=[asesor_id])
    comprador = relationship("Comprador")

    def reservar(self, asesor_id: uuid.UUID, comprador_id: uuid.UUID):
        if self.estado != EstadoApartamento.disponible:
            raise ValueError("Apartamento no está disponible")
        self.estado = EstadoApartamento.reservado
        self.asesor_id = asesor_id
        self.comprador_id = comprador_id

    def vender(self):
        if self.estado != EstadoApartamento.reservado:
            raise ValueError("Apartamento debe estar reservado antes de vender")
        self.estado = EstadoApartamento.vendido

    def liberar(self):
        self.estado = EstadoApartamento.disponible
        self.asesor_id = None
        self.comprador_id = None

class EstadoEmpleado(enum.Enum):
    activo = "activo"
    inactivo = "inactivo"

class ModalidadTrabajo(enum.Enum):
    presencial = "presencial"
    remoto = "remoto"
    hibrido = "hibrido"

class Cargo(BaseModel):
    __tablename__ = "cargos"
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, nullable=True)

class Empleado(BaseModel):
    __tablename__ = "empleados"
    nombre_completo = Column(String, nullable=False)
    documento_identidad = Column(String, nullable=True)
    cargo_id = Column(UUID(as_uuid=True), ForeignKey("cargos.id"), nullable=True)
    telefono = Column(String, nullable=True)
    fecha_contratacion = Column(DateTime, nullable=True)
    salario = Column(Float, nullable=True)
    estado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.activo)
    modalidad = Column(Enum(ModalidadTrabajo), nullable=True)
    rol = Column(Enum(RolUsuario), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    
    usuario = relationship("Usuario")
    cargo = relationship("Cargo")
