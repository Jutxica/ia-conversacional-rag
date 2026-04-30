# AVISO: ESTE SCRIPT ESTÁ DEPRECADO
# O sistema Dehon AI migrou para uma arquitetura Hybrid GraphRAG (Elite 2026) no Supabase.
# Para realizar a ingestão de documentos, utilize: backend/scripts/ingest_corpus.py
# 
# Diferenças Críticas:
# - Modelo: text-embedding-3-large (em vez de MiniLM)
# - Dimensões: 2000 (em vez de 384)
# - Banco: Supabase / PostgreSQL (em vez de Pinecone)
# - Lógica: Chunking Temático + NER GraphRAG

import sys

if __name__ == "__main__":
    print("\n" + "!"*60)
    print("ERRO: SCRIPT LEGADO DETECTADO")
    print("Este script (src/rag/ingest.py) NÃO deve ser utilizado.")
    print("Use o novo pipeline: python backend/scripts/ingest_corpus.py")
    print("!"*60 + "\n")
    sys.exit(1)
