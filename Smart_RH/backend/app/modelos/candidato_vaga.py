from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class CandidatoVaga(Base):
    __tablename__ = 'candidato_vaga'

    id_candidato = Column(Integer, ForeignKey('candidato.id_candidato'), primary_key=True)
    id_vaga = Column(Integer, ForeignKey('vaga.id_vaga'), primary_key=True)

    status_processo = Column(String(50))

    candidato = relationship('Candidato', back_populates='candidaturas')
    vaga = relationship('Vaga', back_populates='candidatos')