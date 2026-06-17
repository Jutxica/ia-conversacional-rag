import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

def get_env_clean(key: str, fallback: str = "") -> str:
    val = os.getenv(key)
    if not val:
        return fallback
    val_clean = val.strip()
    if val_clean.lower() in ("undefined", "null", "placeholder", "none", "", "nan"):
        return fallback
    return val_clean

NEON_DB_URL = get_env_clean("NEON_DB_URL")

# Inicializa o pool de conexões (1 a 10 conexões)
if NEON_DB_URL:
    try:
        db_pool = SimpleConnectionPool(1, 10, NEON_DB_URL)
        print("Pool de conexões Neon DB inicializado com sucesso.")
    except Exception as e:
        print(f"ERRO ao inicializar pool do Neon DB: {e}")
        db_pool = None
else:
    print("AVISO: NEON_DB_URL não encontrado no ambiente.")
    db_pool = None

@contextmanager
def get_db_connection():
    """Context manager para obter e liberar conexões do pool de forma segura."""
    if not db_pool:
        raise Exception("O pool de banco de dados não foi inicializado.")
    
    conn = db_pool.getconn()
    try:
        # psycopg2 connection autocommit off by default (good for transactions)
        yield conn
    finally:
        db_pool.putconn(conn)
