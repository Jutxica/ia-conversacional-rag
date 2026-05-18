-- =============================================================================
-- VALIDAÇÃO DO ÍNDICE (execute estas queries no SQL Editor do Supabase)
-- =============================================================================
-- 
-- 1. Verificar se o índice HNSW existe com as dimensões corretas:
--    SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'documents';
--    Deve mostrar: "documents_embedding_idx" ON documents USING hnsw (embedding vector_cosine_ops)
--    com m=24, ef_construction=128
--
-- 2. Verificar dimensões do embedding:
--    SELECT vector_dims(embedding) FROM documents LIMIT 1;
--    Deve retornar 2000
--
-- 3. Verificar FTS está populado:
--    SELECT COUNT(*) FROM documents WHERE fts IS NULL;
--    Deve retornar 0
--
-- 4. Re-indexar FTS se necessário:
--    UPDATE documents SET fts = 
--      setweight(to_tsvector('simple', COALESCE(content, '')), 'A') ||
--      setweight(to_tsvector('simple', COALESCE(metadata->>'title', '')), 'A');
--
-- =============================================================================

-- Habilita a extensão pg_trgm para busca por similaridade de texto se necessário
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Adiciona coluna de Full Text Search se não existir
ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts tsvector;

-- Cria índice único para evitar duplicação de blocos
DROP INDEX IF EXISTS unique_source_chunk;
CREATE UNIQUE INDEX unique_source_chunk 
ON documents ((metadata->>'source_id'), (metadata->>'chunk_index'));

-- Função para converter JSONB array de entidades para texto para o FTS
CREATE OR REPLACE FUNCTION jsonb_array_to_text(arr jsonb) RETURNS text AS $$
SELECT string_agg(value::text, ' ') FROM jsonb_array_elements(arr);
$$ LANGUAGE sql IMMUTABLE;

-- Cria uma função para atualizar o tsvector automaticamente usando dicionário 'simple' (suporta Latim e Francês)
CREATE OR REPLACE FUNCTION documents_fts_trigger() RETURNS trigger AS $$
BEGIN
  new.fts :=
    setweight(to_tsvector('simple', COALESCE(new.content, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(new.metadata->>'title', '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(new.metadata->'entities'->>'people', '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(new.metadata->'entities'->>'places', '')), 'B') ||
    setweight(to_tsvector('simple', COALESCE(new.metadata->'entities'->>'concepts', '')), 'B');
  RETURN new;
END
$$ LANGUAGE plpgsql;

-- Cria o gatilho (trigger)
DROP TRIGGER IF EXISTS trg_documents_fts ON documents;
CREATE TRIGGER trg_documents_fts BEFORE INSERT OR UPDATE
ON documents FOR EACH ROW EXECUTE FUNCTION documents_fts_trigger();

-- Cria o índice GIN para busca ultra-rápida no texto
CREATE INDEX IF NOT EXISTS documents_fts_idx ON documents USING GIN (fts);

-- Cria o índice HNSW para busca vetorial de alta performance (text-embedding-3-large com 2000 dimensões)
-- Parâmetros: m=24 (conexões por nó), ef_construction=128 (qualidade do grafo)
DROP INDEX IF EXISTS documents_embedding_idx;
CREATE INDEX documents_embedding_idx ON documents 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 24, ef_construction = 128);

-- Remove versões anteriores das funções
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float);
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float, text[]);
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float, text[], text[]);
DROP FUNCTION IF EXISTS hybrid_search_rrf(text, vector, int, float, float, text[], text[]);
DROP FUNCTION IF EXISTS hybrid_search_rrf(text, vector, int, float, float, text[], text[], float);

-- ---------------------------------------------------------------------------
-- Função 1: Busca Híbrida Linear (Original)
-- Combinação ponderada de similaridade vetorial + FTS + boost de entidades.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding VECTOR(2000), 
  match_count int,
  full_text_weight float DEFAULT 1.0,
  vector_weight float DEFAULT 1.0,
  filter_siglas TEXT[] DEFAULT NULL,
  target_entities TEXT[] DEFAULT NULL
) RETURNS TABLE (
  id BIGINT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.content,
    d.metadata,
    (
      (
        (vector_weight * (1 - (d.embedding <=> query_embedding))) +
        (full_text_weight * LEAST(1.0, ts_rank_cd(d.fts, websearch_to_tsquery('simple', query_text)) * 10.0)) +
        CASE 
          WHEN target_entities IS NOT NULL AND (
            d.metadata->'entities'->'people' ?| target_entities OR 
            d.metadata->'receivers' ?| target_entities OR
            d.metadata->'entities'->'concepts' ?| target_entities OR
            d.metadata->>'destinatario' = ANY(target_entities)
          ) THEN 0.2
          ELSE 0.0 
        END
      ) / (vector_weight + full_text_weight + 0.2)
    )::FLOAT AS similarity
  FROM documents d
  WHERE (filter_siglas IS NULL OR d.metadata->>'sigla' = ANY(filter_siglas))
    AND (1 - (d.embedding <=> query_embedding)) > 0.15
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Função 2: Busca Híbrida com RRF (Reciprocal Rank Fusion)
-- Mais robusta que a combinação linear: não depende de escalas compatíveis
-- entre score vetorial e score FTS. k=60 é o valor padrão da literatura.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION hybrid_search_rrf(
  query_text TEXT,
  query_embedding VECTOR(2000), 
  match_count int,
  full_text_weight float DEFAULT 1.0,
  vector_weight float DEFAULT 1.0,
  filter_siglas TEXT[] DEFAULT NULL,
  target_entities TEXT[] DEFAULT NULL,
  rrf_k float DEFAULT 60.0
) RETURNS TABLE (
  id BIGINT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  WITH vector_results AS (
    SELECT d.id, d.content, d.metadata,
           row_number() OVER (ORDER BY (1 - (d.embedding <=> query_embedding)) DESC) AS rank
    FROM documents d
    WHERE (filter_siglas IS NULL OR d.metadata->>'sigla' = ANY(filter_siglas))
      AND (1 - (d.embedding <=> query_embedding)) > 0.15
    ORDER BY (1 - (d.embedding <=> query_embedding)) DESC
    LIMIT match_count * 3
  ),
  fts_results AS (
    SELECT d.id, d.content, d.metadata,
           row_number() OVER (ORDER BY ts_rank_cd(d.fts, websearch_to_tsquery('simple', query_text)) DESC) AS rank
    FROM documents d
    WHERE (filter_siglas IS NULL OR d.metadata->>'sigla' = ANY(filter_siglas))
      AND d.fts IS NOT NULL
    ORDER BY ts_rank_cd(d.fts, websearch_to_tsquery('simple', query_text)) DESC
    LIMIT match_count * 3
  ),
  combined AS (
    SELECT
      COALESCE(v.id, f.id) AS id,
      COALESCE(v.content, f.content) AS content,
      COALESCE(v.metadata, f.metadata) AS metadata,
      (COALESCE(1.0 / (rrf_k + v.rank), 0.0) * vector_weight +
       COALESCE(1.0 / (rrf_k + f.rank), 0.0) * full_text_weight +
       CASE WHEN target_entities IS NOT NULL AND (
         COALESCE(v.metadata, f.metadata)->'entities'->'people' ?| target_entities OR 
         COALESCE(v.metadata, f.metadata)->'receivers' ?| target_entities OR
         COALESCE(v.metadata, f.metadata)->'entities'->'concepts' ?| target_entities OR
         COALESCE(v.metadata, f.metadata)->>'destinatario' = ANY(target_entities)
       ) THEN 0.05 ELSE 0.0 END
      ) / (vector_weight + full_text_weight + 0.05) AS similarity
    FROM vector_results v
    FULL OUTER JOIN fts_results f ON v.id = f.id
  )
  SELECT c.id, c.content, c.metadata, c.similarity::FLOAT
  FROM combined c
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
