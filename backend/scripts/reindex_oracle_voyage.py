import os
import sys
import json
import array
import psycopg2
import oracledb
import requests
from dotenv import load_dotenv

# Carregar dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

NEON_DB_URL = os.getenv("NEON_DB_URL") or os.getenv("SUPABASE_DB_URL")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

if not NEON_DB_URL:
    print("ERRO: Nem NEON_DB_URL nem SUPABASE_DB_URL foram encontrados no ambiente do container.")
    sys.exit(1)

if not VOYAGE_API_KEY:
    print("ERRO: VOYAGE_API_KEY não encontrado no ambiente.")
    sys.exit(1)

# Configuração OCI/Oracle Cloud
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALLET_DIR = os.path.join(BASE_DIR, "wallet")
DB_USER = "admin"
DB_PASSWORD = "@Mualilissa22"
CONNECT_STRING = '(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.sa-saopaulo-1.oraclecloud.com))(connect_data=(service_name=g071d809dc36d2d_dehonai_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'

def get_voyage_embedding(text: str) -> list:
    text = text.replace("\n", " ")
    url = "https://api.voyageai.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VOYAGE_API_KEY}"
    }
    payload = {
        "input": [text],
        "model": "voyage-3-large",
        "output_dimension": 1024
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def main():
    print("Iniciando migração de embeddings para Voyage AI (1024 dimensões) no Oracle...")
    
    # 1. Conectar ao Neon PostgreSQL e buscar documentos
    print("Conectando ao Neon PostgreSQL...")
    pg_conn = psycopg2.connect(NEON_DB_URL)
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT content, metadata FROM documents")
    docs = pg_cur.fetchall()
    print(f"Total de documentos encontrados no Neon: {len(docs)}")
    
    # 2. Conectar ao Oracle Database
    print("Conectando ao Oracle Database...")
    oracle_conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=CONNECT_STRING,
        config_dir=WALLET_DIR,
        wallet_location=WALLET_DIR,
        wallet_password=DB_PASSWORD
    )
    oracle_cur = oracle_conn.cursor()
    
    # 3. Recriar tabela DOCUMENTS com vetor de 1024 dimensões
    print("Recriando tabela DOCUMENTS no Oracle com vetor de 1024 dimensões...")
    try:
        oracle_cur.execute("DROP TABLE documents CASCADE CONSTRAINTS")
        print("Tabela DOCUMENTS antiga dropada.")
    except Exception as e:
        print("Tabela DOCUMENTS não existia ou erro ao dropar (prosseguindo):", e)
        
    oracle_cur.execute("""
        CREATE TABLE documents (
            id VARCHAR2(36) DEFAULT sys_guid() PRIMARY KEY,
            content CLOB NOT NULL,
            embedding VECTOR(1024, FLOAT32),
            metadata CLOB
        )
    """)
    print("Nova tabela DOCUMENTS criada com VECTOR(1024, FLOAT32).")
    
    # 4. Processar e inserir documentos
    count = 0
    errors = 0
    for i, doc in enumerate(docs):
        content, metadata_dict = doc
        
        # Converter metadados para JSON string
        metadata_str = json.dumps(metadata_dict)
        
        try:
            # Gerar embedding Voyage
            emb = get_voyage_embedding(content)
            vec_array = array.array("f", emb)
            
            # Inserir no Oracle
            oracle_cur.execute(
                "INSERT INTO documents (content, embedding, metadata) VALUES (:content, :emb, :metadata)",
                content=content, emb=vec_array, metadata=metadata_str
            )
            count += 1
            if count % 50 == 0:
                print(f"Processados: {count}/{len(docs)}")
                oracle_conn.commit()
        except Exception as e:
            print(f"Erro no documento {i}: {e}")
            errors += 1
            
    oracle_conn.commit()
    print(f"\nMigração concluída! Sucesso: {count}, Erros: {errors}")
    
    # Fechar conexões
    pg_cur.close()
    pg_conn.close()
    oracle_cur.close()
    oracle_conn.close()

if __name__ == "__main__":
    main()
