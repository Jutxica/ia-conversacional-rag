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

    # 3. Duplicatas
    print("\n3. DUPLICATAS (source_id + chunk_index)")
    dup_resp = supabase.rpc("validate_no_duplicates").execute()
    if dup_resp.data:
        all_ok &= check(False, f"Duplicatas encontradas: {dup_resp.data}")
    else:
        all_ok &= check(True, "Nenhuma duplicata")

    # 4. Distribuição de siglas
    print("\n4. DISTRIBUIÇÃO DE SIGLAS")
    siglas_resp = supabase.table("documents") \
        .select("metadata->>sigla") \
        .execute()
    siglas = {}
    for row in (siglas_resp.data or []):
        s = row.get("sigla") or row.get("metadata->>sigla", "desconhecida")
        siglas[s] = siglas.get(s, 0) + 1
    print(f"    {len(siglas)} siglas únicas")
    for s, count in sorted(siglas.items(), key=lambda x: -x[1])[:10]:
        print(f"      {s}: {count} chunks")

    # 5. Chunks vazios ou muito pequenos
    print("\n5. CHUNKS VAZIOS OU MUITO PEQUENOS")
    small_chunks = supabase.table("documents") \
        .select("id, content") \
        .lte("length(content)", 50) \
        .execute()
    n_small = len(small_chunks.data or [])
    all_ok &= check(n_small == 0, f"Chunks com <50 caracteres: {n_small}")
    if n_small > 0:
        for s in (small_chunks.data or [])[:5]:
            print(f"    ⚠️ ID {s['id']}: '{s['content'][:80]}...'")

    # 6. Chunks com HTML residual
    print("\n6. ARTEFATOS HTML")
    html_chunks = supabase.table("documents") \
        .select("id, content") \
        .like("content", "%<p%") \
        .execute()
    n_html = len(html_chunks.data or [])
    all_ok &= check(n_html == 0, f"Chunks com tags HTML: {n_html}")

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
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    sample = supabase.table("documents") \
        .select("embedding, content") \
        .limit(1) \
        .execute()
    if sample.data:
        emb = sample.data[0].get("embedding", [])
        dims = len(emb) if emb else 0
        all_ok &= check(dims == 2000, f"Dimensões do embedding: {dims} (esperado 2000)")

    # 9. Índice HNSW
    print("\n9. ÍNDICE HNSW")
    try:
        idx_resp = supabase.query("SELECT indexname FROM pg_indexes WHERE tablename = 'documents' AND indexname = 'documents_embedding_idx'").execute()
        has_hnsw = bool(idx_resp.data)
    except Exception:
        has_hnsw = False
    all_ok &= check(has_hnsw, "Índice HNSW (documents_embedding_idx) existe")

    # 10. Documentos únicos
    print("\n10. DOCUMENTOS ÚNICOS")
    docs_set = set()
    for row in (siglas_resp.data or []):
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
