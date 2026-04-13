from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from db.database import Base

class AvaliacaoDesempenho(Base):
    __tablename__ = 'avaliacao_desempenho'

    id_avaliacao = Column(Integer, primary_key=True)
    categoria = Column(String(100), nullable=False)
    nota = Column(Float, nullable=False)
    comentario = Column(Text)
    data_avalicao = Column(Date, nullable=False)

    fk_id_funcionario = Column(Integer, ForeignKey('funcionario.id_funcionario'))
    fk_id_avaliador = Column(Integer, ForeignKey('funcionario.id_funcionario'))

    funcionario = relationship('Funcionario', foreign_keys=[fk_id_funcionario], back_populates='avaliacoes_recebidas')
    avaliador = relationship('Funcionario', foreign_keys=[fk_id_avaliador], back_populates='avaliacoes_feitas')