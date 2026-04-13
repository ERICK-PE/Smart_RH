from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class Vaga(Base):
    __tablename__ = 'vaga'

    id_vaga = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(150))
    descricao = Column(Text)
    data_publicacao = Column(Date)

    fk_id_setor = Column(Integer, ForeignKey('setor.id_setor'))

    setor = relationship('Setor', back_populates='vagas')
    candidatos = relationship('CandidatoVaga', back_populates='vaga')