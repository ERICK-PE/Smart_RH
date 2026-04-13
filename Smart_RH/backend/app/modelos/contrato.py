from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from db.database import Base

class Contrato(Base):
    __tablename__ = 'contrato'

    id_contrato = Column(Integer, primary_key=True, autoincrement=True)

    fk_id_funcionario = Column(
        Integer,
        ForeignKey('funcionario.id_funcionario'),
        nullable=False
    )

    tipo_contrato = Column(String(50))
    salario = Column(Numeric(10, 2))
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)

    funcionario = relationship('Funcionario',back_populates='contratos')