import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são necessários.")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def check(condition: bool, message: str):
    status = "✅" if condition else "❌"
    print(f"  {status} {message}")
    return condition


def main():
    print(f"{'='*60}")
    print("VALIDAÇÃO DE QUALIDADE DA INGESTÃO")
    print(f"{'='*60}\n")

    all_ok = True

    # 1. Total de chunks
    print("1. QUANTIDADE DE DADOS")
    count_resp = supabase.table("documents").select("id", count="exact").execute()
    total_chunks = count_resp.count if hasattr(count_resp, 'count') and count_resp.count else 0
    all_ok &= check(total_chunks > 0, f"{total_chunks} chunks no total")
    all_ok &= check(total_chunks >= 1000, f"Volume mínimo: {total_chunks} >= 1000 (ideal ~5000)")

    if total_chunks == 0:
        print("\n❌ Nenhum chunk encontrado. Execute a ingestão primeiro.")
        sys.exit(1)

    # 2. FTS column
    print("\n2. COLUNA FTS (FULL TEXT SEARCH)")
    null_fts = supabase.table("documents") \
        .select("id", count="exact") \
        .is_("fts", "null") \
        .execute()
    n_null_fts = null_fts.count if hasattr(null_fts, 'count') else 0
    all_ok &= check(n_null_fts == 0, f"Chunks sem FTS: {n_null_fts}")
    if n_null_fts > 0:
        print("    ⚠️ Execute no SQL Editor: UPDATE documents SET fts = setweight(to_tsvector('simple', COALESCE(content, '')), 'A');")

    # 3. Duplicatas & 4. Distribuição de siglas
    print("\n3. DUPLICATAS (source_id + chunk_index) & 4. DISTRIBUIÇÃO DE SIGLAS")
    try:
        # Buscamos dados essenciais dos metadados para as duas verificações de uma só vez
        meta_resp = supabase.table("documents") \
            .select("metadata->>sigla, metadata->>source_id, metadata->>chunk_index") \
            .execute()
        meta_data = meta_resp.data or []
    except Exception as e:
        print(f"    ❌ Erro ao buscar metadados: {e}")
        meta_data = []

    # Verificação de duplicatas
    seen = set()
    duplicates = []
    siglas = {}
    
    for row in meta_data:
        # Obter sigla, source_id, chunk_index
        s = row.get("sigla") or row.get("metadata->>sigla") or "desconhecida"
        siglas[s] = siglas.get(s, 0) + 1
        
        sid = row.get("source_id") or row.get("metadata->>source_id")
        cidx = row.get("chunk_index") or row.get("metadata->>chunk_index")
        
        if sid and cidx is not None:
            key = (sid, cidx)
            if key in seen:
                duplicates.append(key)
            seen.add(key)

    if duplicates:
        all_ok &= check(False, f"Duplicatas encontradas: {len(duplicates)} duplicados (amostra: {duplicates[:5]})")
    else:
        all_ok &= check(True, "Nenhuma duplicata (source_id + chunk_index)")

    print(f"\n4. DISTRIBUIÇÃO DE SIGLAS")
    print(f"    {len(siglas)} siglas únicas")
    for s, count in sorted(siglas.items(), key=lambda x: -x[1])[:10]:
        print(f"      {s}: {count} chunks")

    # 5. Chunks vazios ou muito pequenos
    print("\n5. CHUNKS VAZIOS OU MUITO PEQUENOS")
    try:
        content_resp = supabase.table("documents") \
            .select("id, content") \
            .execute()
        all_contents = content_resp.data or []
    except Exception as e:
        print(f"    ❌ Erro ao buscar conteúdos: {e}")
        all_contents = []

    small_chunks = [c for c in all_contents if c.get("content") and len(c.get("content", "").strip()) <= 50]
    n_small = len(small_chunks)
    all_ok &= check(n_small == 0, f"Chunks com <50 caracteres: {n_small}")
    if n_small > 0:
        for s in small_chunks[:5]:
            print(f"    ⚠️ ID {s['id']}: '{s['content'][:80]}...'")

    # 6. Chunks com HTML residual
    print("\n6. ARTEFATOS HTML")
    html_chunks = [c for c in all_contents if c.get("content") and "<p" in c.get("content")]
    n_html = len(html_chunks)
    all_ok &= check(n_html == 0, f"Chunks com tags HTML: {n_html}")
    if n_html > 0:
        for s in html_chunks[:5]:
            print(f"    ⚠️ ID {s['id']} contém HTML: '{s['content'][:80]}...'")

    # 7. Metadados
    print("\n7. METADADOS OBRIGATÓRIOS")
    no_title = supabase.table("documents") \
        .select("id", count="exact") \
        .is_("metadata->>title", "null") \
        .execute()
    n_no_title = no_title.count if hasattr(no_title, 'count') else 0
    all_ok &= check(n_no_title == 0, f"Chunks sem título: {n_no_title}")

    no_sigla = supabase.table("documents") \
        .select("id", count="exact") \
        .is_("metadata->>sigla", "null") \
        .execute()
    n_no_sigla = no_sigla.count if hasattr(no_sigla, 'count') else 0
    all_ok &= check(n_no_sigla == 0, f"Chunks sem sigla: {n_no_sigla}")

    no_source = supabase.table("documents") \
        .select("id", count="exact") \
        .is_("metadata->>source_id", "null") \
        .execute()
    n_no_source = no_source.count if hasattr(no_source, 'count') else 0
    all_ok &= check(n_no_source == 0, f"Chunks sem source_id: {n_no_source}")

    # 8. Embeddings
    print("\n8. EMBEDDINGS")
    sample = supabase.table("documents") \
        .select("embedding, content") \
        .limit(1) \
        .execute()
    if sample.data:
        emb = sample.data[0].get("embedding", [])
        if isinstance(emb, str):
            try:
                emb_list = json.loads(emb)
                dims = len(emb_list)
            except Exception:
                dims = len([x for x in emb.strip("[]").split(",") if x.strip()])
        else:
            dims = len(emb) if emb else 0
        all_ok &= check(dims == 2000, f"Dimensões do embedding: {dims} (esperado 2000)")

    # 9. Índice HNSW
    print("\n9. ÍNDICE HNSW")
    # Nota: Não é possível consultar tabelas do sistema como pg_indexes diretamente 
    # pelo cliente Supabase REST sem uma função RPC dedicada.
    # Assumimos que o índice HNSW existe se a busca híbrida puder ser executada com sucesso.
    try:
        dummy_vector = [0.0] * 2000
        search_test = supabase.rpc(
            "hybrid_search",
            {
                "query_text": "teste",
                "query_embedding": dummy_vector,
                "match_count": 1
            }
        ).execute()
        has_hnsw = True
    except Exception as e:
        print(f"    ⚠️ Erro ao testar busca híbrida (rpc): {e}")
        has_hnsw = False
    all_ok &= check(has_hnsw, "Índice HNSW (ou suporte a busca híbrida) operacional")

    # 10. Documentos únicos
    print("\n10. DOCUMENTOS ÚNICOS")
    docs_set = set()
    for row in (meta_data or []):
        sid = row.get("source_id") or row.get("metadata->>source_id")
        if sid:
            docs_set.add(sid)
    all_ok &= check(len(docs_set) > 0, f"{len(docs_set)} documentos únicos")

    print(f"\n{'='*60}")
    if all_ok:
        print("✅ VALIDAÇÃO COMPLETA: Tudo OK")
    else:
        print("⚠️  VALIDAÇÃO COMPLETA: Alguns problemas encontrados (veja acima)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
