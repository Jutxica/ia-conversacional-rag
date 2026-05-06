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

-- Cria o índice GIN para busca ultra-rápida
CREATE INDEX IF NOT EXISTS documents_fts_idx ON documents USING GIN (fts);

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
      (vector_weight * (1 - (d.embedding <=> query_embedding))) +
      (full_text_weight * ts_rank_cd(d.fts, websearch_to_tsquery('portuguese', query_text))) +
      -- Boost por Entidade (Se o nome estiver no campo people ou receivers)
      CASE 
        WHEN target_entities IS NOT NULL AND (
          d.metadata->'entities'->'people' ?| target_entities OR 
          d.metadata->'receivers' ?| target_entities OR
          d.metadata->>'destinatario' = ANY(target_entities)
        ) THEN 1.0 -- Boost massivo para garantir topo da lista
        ELSE 0 
      END
    ) AS similarity
  FROM documents d
  WHERE (filter_siglas IS NULL OR d.metadata->>'sigla' = ANY(filter_siglas))
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
