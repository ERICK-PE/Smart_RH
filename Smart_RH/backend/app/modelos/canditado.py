from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from db.database import Base

class Candidato(Base):
    __tablename__ = 'candidato'

    id_candidato = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(150))
    email = Column(String(150))
    telefone = Column(String(20))
    curriculo = Column(Text)

    candidaturas = relationship('CandidatoVaga', back_populates='candidato')