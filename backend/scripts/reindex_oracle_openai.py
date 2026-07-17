import os
import sys
import json
import array
import psycopg2
import oracledb
from openai import OpenAI
from dotenv import load_dotenv

# Carregar dotenv da pasta do backend
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SOURCE_DB_URL = os.getenv("SUPABASE_DB_URL") or os.getenv("NEON_DB_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SOURCE_DB_URL:
    print("ERRO: Nem SUPABASE_DB_URL nem NEON_DB_URL foram encontrados no ambiente.")
    sys.exit(1)

if not OPENAI_API_KEY:
    print("ERRO: OPENAI_API_KEY não encontrado no ambiente.")
    sys.exit(1)

# Configuração OCI/Oracle Cloud
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALLET_DIR = os.path.join(BASE_DIR, "wallet")
DB_USER = os.getenv("ORACLE_DB_USER", "ADMIN")
DB_PASSWORD = os.getenv("ORACLE_DB_PASSWORD", "Mualilissa_2026!")
DSN_NAME = "dehonai_high"

# Inicializar cliente OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_openai_embeddings_batch(texts: list) -> list:
    """Obtém embeddings em lote da OpenAI (1536 dimensões)."""
    clean_texts = [t.replace("\n", " ") for t in texts]
    response = openai_client.embeddings.create(
        input=clean_texts,
        model="text-embedding-3-large",
        dimensions=1536
    )
    return [d.embedding for d in response.data]

def main():
    print("Iniciando migração de embeddings para OpenAI (1536 dimensões) no Oracle...")
    
    # 1. Conectar ao PostgreSQL (Neon/Supabase) e buscar documentos
    print("Conectando à base de dados original...")
    pg_conn = psycopg2.connect(SOURCE_DB_URL)
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT content, metadata FROM documents")
    docs = pg_cur.fetchall()
    print(f"Total de documentos encontrados na base original: {len(docs)}")
    
    if len(docs) == 0:
        print("Nenhum documento encontrado para migrar.")
        sys.exit(0)

    # 2. Conectar ao Oracle Database
    print("Conectando ao Oracle Database...")
    oracle_conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DSN_NAME,
        config_dir=WALLET_DIR,
        wallet_location=WALLET_DIR,
        wallet_password=DB_PASSWORD
    )
    oracle_cur = oracle_conn.cursor()
    
    # 3. Recriar tabela DOCUMENTS com vetor de 1536 dimensões
    print("Recriando tabela DOCUMENTS no Oracle com vetor de 1536 dimensões...")
    try:
        oracle_cur.execute("DROP TABLE documents CASCADE CONSTRAINTS")
        print("Tabela DOCUMENTS antiga dropada.")
    except Exception as e:
        print("Tabela DOCUMENTS não existia ou erro ao dropar (prosseguindo):", e)
        
    oracle_cur.execute("""
        CREATE TABLE documents (
            id VARCHAR2(36) DEFAULT sys_guid() PRIMARY KEY,
            content CLOB NOT NULL,
            embedding VECTOR(1536, FLOAT32),
            metadata CLOB
        )
    """)
    print("Nova tabela DOCUMENTS criada com VECTOR(1536, FLOAT32).")
    
    # 4. Processar e inserir documentos em lotes
    batch_size = 50
    count = 0
    errors = 0
    
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        batch_contents = [doc[0] for doc in batch]
        batch_metadatas = [json.dumps(doc[1]) for doc in batch]
        
        try:
            # Obter embeddings do lote
            embeddings = get_openai_embeddings_batch(batch_contents)
            
            # Inserir cada um no Oracle
            for content, emb_vec, metadata_str in zip(batch_contents, embeddings, batch_metadatas):
                vec_array = array.array("f", emb_vec)
                oracle_cur.execute(
                    "INSERT INTO documents (content, embedding, metadata) VALUES (:content, :emb, :metadata)",
                    content=content, emb=vec_array, metadata=metadata_str
                )
            
            count += len(batch)
            oracle_conn.commit()
            print(f"Processados e indexados: {count}/{len(docs)}")
            
        except Exception as e:
            print(f"Erro ao processar lote {i} a {i + len(batch)}: {e}")
            errors += len(batch)
            
    oracle_conn.commit()
    print(f"\nReindexação concluída! Sucesso: {count}, Erros (lotes falhos): {errors}")
    
    # Fechar conexões
    pg_cur.close()
    pg_conn.close()
    oracle_cur.close()
    oracle_conn.close()

if __name__ == "__main__":
    main()
