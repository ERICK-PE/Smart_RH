from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import relationship,sessionmaker
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db.database import Base

DATABASE_URL = "postgresql://postgres:password@localhost:3005/smart_rh"

class Cargo(Base):
    __tablename__ = "cargo"

    id_cargo = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String)

    funcionarios = relationship("Funcionario", back_populates="cargo")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

session = SessionLocal()

novo_cargo = Cargo(
    nome="Desenvolvedor",
    descricao="Responsável por desenvolver sistemas"
)
session.refresh(novo_cargo)
print(novo_cargo.id_cargo)

