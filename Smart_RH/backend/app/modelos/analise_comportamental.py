from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class AnaliseComportamental(Base):
    __tablename__ = 'analise_comportamental'
    
    id_analise = Column(Integer, primary_key=True)
    resultado = Column(String(200))
    data_analise = Column(Date, nullable=False)

    fk_id_funcionario = Column(Integer, ForeignKey('funcionario.id_funcionario'))

    funcionario = relationship('Funcionario', back_populates='analises_comportamentais')