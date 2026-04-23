from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nome_usuario = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    data_criacao = Column(DateTime)
    data_atualizacao = Column(DateTime)


class Backup(Base):
    __tablename__ = "backups"

    id_backup = Column(Integer, primary_key = True, index = True)

    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))

    nome_original = Column(String(255), nullable=False)
    nome_armazenado = Column(String(255), unique=True, nullable=False)
    caminho = Column(String(255), nullable=False)
    tamanho = Column(BigInteger)
    tipo_mime = Column(String(100))
    hash_arquivo = Column(String(64))
    data_upload = Column(DateTime)
    data_atualizacao = Column(DateTime)

backups = relationship("Backup", back_populates="usuario")
    
