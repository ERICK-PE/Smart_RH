from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class PlanoCarreira(Base):
    __tablename__ = 'plano_carreira'

    id_plano = Column(Integer, primary_key=True, autoincrement=True)

    fk_id_cargo = Column(Integer,ForeignKey('cargo.id_cargo'),nullable=False)

    descricao = Column(Text)
    requisitos = Column(Text)

    cargo = relationship('Cargo',back_populates='planos_carreira')