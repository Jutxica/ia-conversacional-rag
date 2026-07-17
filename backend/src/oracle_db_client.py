import os
import oracledb
import json

# Defina a diretoria base (onde está o oracledb client e o wallet)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALLET_DIR = os.path.join(BASE_DIR, "wallet")

def get_oracle_connection():
    """Retorna uma ligação à Oracle Autonomous Database usando a Wallet."""
    # A password que o utilizador criou para a base de dados (e para a Wallet)
    user = "ADMIN"
    password = os.environ.get("ORACLE_DB_PASSWORD", "Mualilissa_2026!")
    dsn = "dehonai_high"

    # Inicializa o Oracle Client usando o diretório da Wallet
    # oracledb suporta Thin mode por predefinição, que consegue ler a Wallet diretamente (se a versão for 2.0.0+)
    try:
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn,
            config_dir=WALLET_DIR,
            wallet_location=WALLET_DIR,
            wallet_password=password
        )
        return connection
    except Exception as e:
        print(f"Erro ao ligar à Oracle DB: {e}")
        return None

def init_db():
    """Inicializa as tabelas necessárias na Oracle."""
    conn = get_oracle_connection()
    if not conn:
        print("Aviso: Oracle DB connection not established.")
        return
    try:
        cursor = conn.cursor()
        
        # Tabela documents
        cursor.execute("""
            DECLARE
               tbl_count NUMBER;
            BEGIN
               SELECT count(*) INTO tbl_count FROM dba_tables WHERE table_name = 'DOCUMENTS';
               IF tbl_count = 0 THEN
                  EXECUTE IMMEDIATE '
                  CREATE TABLE documents (
                      id VARCHAR2(36) DEFAULT sys_guid() PRIMARY KEY,
                      content CLOB NOT NULL,
                      embedding VECTOR(1536, FLOAT32),
                      metadata CLOB
                  )';
               END IF;
            END;
        """)
        
        # Tabela chats
        cursor.execute("""
            DECLARE
               tbl_count NUMBER;
            BEGIN
               SELECT count(*) INTO tbl_count FROM dba_tables WHERE table_name = 'CHATS';
               IF tbl_count = 0 THEN
                  EXECUTE IMMEDIATE '
                  CREATE TABLE chats (
                      id VARCHAR2(36) DEFAULT sys_guid() PRIMARY KEY,
                      messages CLOB,
                      created_at TIMESTAMP DEFAULT SYSTIMESTAMP
                  )';
               END IF;
            END;
        """)
        
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Erro ao inicializar base de dados Oracle: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de dados Oracle inicializada (se as tabelas não existissem).")
