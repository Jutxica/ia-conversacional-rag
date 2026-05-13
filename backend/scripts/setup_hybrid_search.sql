-- Habilita a extensão pg_trgm para busca por similaridade de texto se necessário
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Adiciona coluna de Full Text Search se não existir
ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts tsvector;

-- Função para converter JSONB array de entidades para texto para o FTS
CREATE OR REPLACE FUNCTION jsonb_array_to_text(arr jsonb) RETURNS text AS $$
SELECT string_agg(value::text, ' ') FROM jsonb_array_elements(arr);
$$ LANGUAGE sql IMMUTABLE;

-- Cria uma função para atualizar o tsvector automaticamente (Melhorada para Entidades)
CREATE OR REPLACE FUNCTION documents_fts_trigger() RETURNS trigger AS $$
BEGIN
  new.fts :=
    setweight(to_tsvector('portuguese', COALESCE(new.content, '')), 'A') ||
    setweight(to_tsvector('portuguese', COALESCE(new.metadata->>'title', '')), 'A') ||
    setweight(to_tsvector('portuguese', COALESCE(new.metadata->'entities'->>'people', '')), 'A') ||
    setweight(to_tsvector('portuguese', COALESCE(new.metadata->'entities'->>'places', '')), 'B') ||
    setweight(to_tsvector('portuguese', COALESCE(new.metadata->'entities'->>'concepts', '')), 'B');
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
-- O operador vector_cosine_ops é o mais indicado para embeddings da OpenAI
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Remove versões anteriores da função para evitar erro de ambiguidade (PGRST203)
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float);
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float, text[]);
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float, text[], text[]);

-- Função de Busca Híbrida (Vetor + FTS) com Suporte a Filtro de Entidades e Siglas
-- Versão 2.0: Adiciona boost massivo para entidades detectadas
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding VECTOR(2000), 
  match_count int,
  full_text_weight float DEFAULT 1.0,
  vector_weight float DEFAULT 1.2, -- Leve aumento no peso vetorial para capturar semântica
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
      -- Similaridade de Cosseno (1 - <=> )
      (vector_weight * (1 - (d.embedding <=> query_embedding))) +
      -- Rank do Full Text Search (Rankings FTS tendem a ser menores, então multiplicamos por um fator de ajuste)
      (full_text_weight * ts_rank_cd(d.fts, websearch_to_tsquery('portuguese', query_text))) +
      -- Boost por Entidade (Se o nome estiver no campo people ou receivers)
      CASE 
        WHEN target_entities IS NOT NULL AND (
          d.metadata->'entities'->'people' ?| target_entities OR 
          d.metadata->'receivers' ?| target_entities OR
          d.metadata->'entities'->'concepts' ?| target_entities OR
          d.metadata->>'destinatario' = ANY(target_entities)
        ) THEN 1.5 -- Boost massivo de 150% para garantir relevância de destinatários/conceitos
        ELSE 0 
      END
    ) AS similarity
  FROM documents d
  WHERE (filter_siglas IS NULL OR d.metadata->>'sigla' = ANY(filter_siglas))
    AND (1 - (d.embedding <=> query_embedding)) > 0.15 -- Threshold mínimo de segurança para evitar ruído
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
