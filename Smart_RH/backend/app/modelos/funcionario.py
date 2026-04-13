from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class Funcionario(Base):
    __tablename__ = "funcionario"

    id_funcionario = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    email = Column(String(150), unique=True)
    telefone = Column(String(20))
    data_admissao = Column(Date, nullable=False)

    fk_id_setor = Column(Integer, ForeignKey("setor.id_setor"), nullable=False)
    fk_id_cargo = Column(Integer, ForeignKey("cargo.id_cargo"), nullable=False)

    setor = relationship("Setor", back_populates="funcionarios")
    cargo = relationship("Cargo", back_populates="funcionarios")
    analises_comportamentais = relationship('AnaliseComportamental', back_populates='funcionario')
    avaliacoes_recebidas = relationship('AvaliacaoDesempenho', foreign_keys='AvaliacaoDesempenho.fk_id_funcionario', back_populates='funcionario')
    avaliacoes_feitas = relationship('AvaliacaoDesempenho', foreign_keys='AvaliacaoDesempenho.fk_id_avaliador', back_populates='avaliador')
    contratos = relationship('Contrato', back_populates='funcionario')