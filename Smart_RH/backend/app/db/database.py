from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from db.config import DATABASE_URL

# cria engine (conexão com o banco)
engine = create_engine(
    DATABASE_URL,
    echo=True  # exibe as consultas SQL no console
)

# cria sessão (interface para interagir com o banco)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine)

# base para os modelos (tabelas)
Base = declarative_base()