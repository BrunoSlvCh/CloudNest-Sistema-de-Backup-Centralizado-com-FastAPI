from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Depends
from schemas import UsuarioCreate, LoginRequest, BackupResponse
from models import Backup, Usuario
from database import SessionLocal
from security import hash_senha,verificar_senha
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import hashlib
import uuid

app = FastAPI()

def get_db():
    db = SessionLocal
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def criar_usuario(usuario: UsuarioCreate):

    db = SessionLocal()
    try:
        novo_usuario = Usuario(
            nome_usuario = usuario.nome_usuario,
            email = usuario.email,
            senha_hash = hash_senha(usuario.senha),
            data_criacao = datetime.now(),
            data_atualizacao = datetime.now()
        )

        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

        return {"mensagem": "Usuário criado com suesso!"}
    
    finally:
        db.close()

SECRET_KEY = "chave_secreta"
ALGORITHM  = "HS256"
ACESS_TOKEN_EXPIRE_MINUTES = 60

def criar_token(data: dict):
    dados = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)
    dados.update({"exp": expire})
    token = jwt.encode(dados, SECRET_KEY, algorithm = ALGORITHM)
    return token

@app.post("/login")
def login(dados: LoginRequest):

    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

        if not usuario:
            return {"erro":"Usuário não encontrado"}
        
        if not verificar_senha(dados.senha, usuario.senha_hash):
                return{"erro":"Senha incorreta"}

        token = criar_token({"sub": usuario.email})

        return {
            "access_token": token,
            "token_type": "Bearer"
        }
    
    finally:
        db.close()

security = HTTPBearer()

def get_usuario_logado(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):  
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code = 401, detail = "Token inválido")
        
        db = SessionLocal()
        usuario = db.query(Usuario).filter(Usuario.email == email).first()

        if usuario is None:
            raise HTTPException(status_code = 401, detail = "Usuário não encontrado")
        return usuario
    
        
    except JWTError:
        raise HTTPException(status_code = 401, detail = "Erro ao validar Token")
    
    finally:
        db.close()

@app.get("/auenticar Token")
def rota_protegida(usuario = Depends(get_usuario_logado)):
    return{
        "mesagem" : f"Olá {usuario.nome_usuario}, você está autenticado(a)."
    }

@app.post("/upload File")
def upload_backup(
    arquivo: UploadFile = File(...),
    usuario = Depends(get_usuario_logado)
):
    db = SessionLocal()
    try:
        
        conteudo = arquivo.file.read()

        tamanho_max = 5 * 1024 * 1024

        if len(conteudo) > tamanho_max:
            raise HTTPException(status_code = 400, detail = "Arquivo muito grande")

        hash_arquivo = hashlib.sha256(conteudo).hexdigest()

        nome_unico = f"{uuid.uuid4()}_{arquivo.filename}"

        pasta_usuario = f"uploads/{usuario.id_usuario}"
        os.makedirs(pasta_usuario, exist_ok=True)

        caminho = f"{pasta_usuario}/{nome_unico}"

        with open(caminho, "wb") as f:
            f.write(conteudo)
        
        novo_backup = Backup(
            nome_original = arquivo.filename,
            nome_armazenado = nome_unico,   
            caminho = caminho,
            tamanho = len(conteudo),
            tipo_mime = arquivo.content_type,
            hash_arquivo = hash_arquivo,
            data_upload = datetime.now(),
            data_atualizacao = datetime.now(),
            id_usuario = usuario.id_usuario
        )

        existe = db.query(Backup).filter(
            Backup.hash_arquivo == hash_arquivo,
            Backup.id_usuario == usuario.id_usuario).first()
        
        if existe:
            return{"Aviso": "Já existe um backup deste arquivo"}   

        db.add(novo_backup)
        db.commit()

        print(f"O usuário {usuario.nome_usuario} fez upload de {arquivo.filename}")

        return{
            "mensagem": "Backup realizado com sucesso"
        }
    
    finally:
        db.close()


@app.get("/backup/{backup_id}")
def dowload_backup(
    backup_id: int,
    usuario = Depends(get_usuario_logado)
):
    db = SessionLocal()

    try:

        backup = db.query(Backup).filter(
            Backup.id_backup == backup_id,
            Backup.id_usuario == usuario.id_usuario
        ).first()

        if not backup:
            raise HTTPException(status_code = 404, detail = "Arquivo não encontrado")
        
        if not os.path.exists(backup.caminho):
            raise HTTPException(status_code = 404, detail = "Arquivo não existe no servidor")
        
        return FileResponse (
            path = backup.caminho,
            filename = backup.nome_original
        )
    
    finally:
        db.close()

@app.get("/backups", response_model=list[BackupResponse])
def listar_backups(
    skip: int = 0,
    limit: int = 10,
    usuario = Depends(get_usuario_logado)
):
    db = SessionLocal()

    try:
        backups = db.query(Backup).filter(
            Backup.id_usuario == usuario.id_usuario
        ).order_by(
            Backup.data_upload.desc()
        ).offset(skip).limit(limit).all()

        return backups

    finally:
        db.close()

@app.delete("/delete/{backup_id}")
def deletar_backup(
    backup_id: int,
    usuario = Depends(get_usuario_logado)
):
    db = SessionLocal()

    try:
        backup = db.query(Backup).filter(
            Backup.id_backup == backup_id,
            Backup.id_usuario == usuario.id_usuario
        ).first()

        if not backup:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        if os.path.exists(backup.caminho):
            os.remove(backup.caminho)

        db.delete(backup)
        db.commit()

        return {"mensagem": "Backup deletado com sucesso "}

    finally:
        db.close()


