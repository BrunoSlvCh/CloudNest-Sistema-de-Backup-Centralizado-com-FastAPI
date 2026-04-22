from passlib.context import CryptContext

pwb_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str):
    return pwb_context.hash(senha)

def verificar_senha(senha: str, hash: str):
    return pwb_context.verify(senha, hash)