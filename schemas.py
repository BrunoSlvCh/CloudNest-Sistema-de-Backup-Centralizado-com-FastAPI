from pydantic import BaseModel
from datetime import datetime

class UsuarioCreate(BaseModel):
    nome_usuario: str
    email: str
    senha: str  

class LoginRequest(BaseModel):
    email: str
    senha: str

class BackupResponse(BaseModel):
    id_backup: int
    nome_original: str
    tamanho: int
    data_upload: datetime

class Config:
    from_attributes = True