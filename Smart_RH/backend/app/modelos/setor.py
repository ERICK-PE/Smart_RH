from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

class Setor(Base):
    __tablename__ = "setor"

    id_setor = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String)

    funcionarios = relationship("Funcionario", back_populates="setor")
    vagas = relationship('Vaga', back_populates='setor')