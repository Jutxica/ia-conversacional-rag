import os
import sys
import json
import time
import array
import google.generativeai as genai

# Adicionar caminho base do backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.oracle_db_client import get_oracle_connection
from src.rag.search import get_env_clean

def populate_google_embeddings():
    api_key = get_env_clean("GEMINI_API_KEY")
    if not api_key:
        print("ERRO: GEMINI_API_KEY não encontrada no ambiente!")
        return

    genai.configure(api_key=api_key)

    conn = get_oracle_connection()
    if not conn:
        print("ERRO: Falha ao conectar ao banco Oracle DB!")
        return

    cursor = conn.cursor()
    
    # Contar total de registros pendentes
    cursor.execute("SELECT COUNT(*) FROM documents WHERE embedding_google IS NULL")
    total_pending = cursor.fetchone()[0]
    print(f"=== POPULANDO VETORES GOOGLE TEXT-EMBEDDING-004 (768D) ===")
    print(f"Total de registros pendentes: {total_pending}")

    if total_pending == 0:
        print("Todos os registros já possuem vetores do Google preenchidos!")
        conn.close()
        return

    # Buscar registros em lotes
    batch_size = 50
    processed = 0
    start_time = time.time()

    while True:
        cursor.execute("""
            SELECT ROWID, content 
            FROM documents 
            WHERE embedding_google IS NULL 
            FETCH FIRST :b ROWS ONLY
        """, b=batch_size)
        rows = cursor.fetchall()

        if not rows:
            break

        for rowid, content_clob in rows:
            try:
                text = content_clob.read() if hasattr(content_clob, "read") else content_clob
                if not text or not text.strip():
                    continue

                # Gerar embedding via Google text-embedding-004
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text.replace("\n", " "),
                    task_type="retrieval_document"
                )
                emb_list = res["embedding"]
                vec_array = array.array("f", emb_list)

                update_cursor = conn.cursor()
                update_cursor.execute(
                    "UPDATE documents SET embedding_google = :emb WHERE ROWID = :rid",
                    emb=vec_array, rid=rowid
                )
                update_cursor.close()
                processed += 1

                if processed % 10 == 0:
                    conn.commit()
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 1
                    remaining = (total_pending - processed) / rate if rate > 0 else 0
                    print(f"[GOOGLE EMBEDDINGS] Processados: {processed}/{total_pending} ({processed/total_pending*100:.1f}%) | Velocidade: {rate:.1f} docs/s | Restante est.: {remaining/60:.1f} min", flush=True)

            except Exception as e:
                print(f"[GOOGLE EMBEDDINGS] Erro ao processar registro: {e}")
                time.sleep(2)

        conn.commit()

    conn.close()
    print("=== FINALIZADO: Todos os vetores do Google foram preenchidos com sucesso! ===")

if __name__ == "__main__":
    populate_google_embeddings()
