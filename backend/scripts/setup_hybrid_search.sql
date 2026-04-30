-- Habilita a extensão pg_trgm para busca por similaridade de texto se necessário
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Adiciona coluna de Full Text Search se não existir
ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts tsvector;

-- Cria uma função para atualizar o tsvector automaticamente
CREATE OR REPLACE FUNCTION documents_fts_trigger() RETURNS trigger AS $$
BEGIN
  new.fts :=
    setweight(to_tsvector('portuguese', COALESCE(new.content, '')), 'A') ||
    setweight(to_tsvector('portuguese', COALESCE(new.metadata->>'title', '')), 'B');
  RETURN new;
END
$$ LANGUAGE plpgsql;

-- Cria o gatilho (trigger)
DROP TRIGGER IF EXISTS trg_documents_fts ON documents;
CREATE TRIGGER trg_documents_fts BEFORE INSERT OR UPDATE
ON documents FOR EACH ROW EXECUTE FUNCTION documents_fts_trigger();

-- Cria o índice GIN para busca ultra-rápida
CREATE INDEX IF NOT EXISTS documents_fts_idx ON documents USING GIN (fts);

-- Função de Busca Híbrida (Vetor + FTS) com Suporte a Filtro de Domínio
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding VECTOR(2000), -- Limite do índice HNSW
  match_count int,
  full_text_weight float DEFAULT 1.0,
  vector_weight float DEFAULT 1.0,
  filter_siglas TEXT[] DEFAULT NULL
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
      (full_text_weight * ts_rank_cd(d.fts, websearch_to_tsvector('portuguese', query_text)))
    ) AS similarity
  FROM documents d
  WHERE (filter_siglas IS NULL OR d.metadata->>'sigla' = ANY(filter_siglas))
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
