-- Reset e Upgrade da Tabela para GraphRAG Elite 2026
DROP TABLE IF EXISTS documents;

CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT,
  metadata JSONB,
  embedding VECTOR(2000), -- Ajustado para o limite máximo do índice (2000)
  fts tsvector
);

-- Re-implementa busca híbrida e gatilhos conforme o setup_hybrid_search.sql anterior
-- (Assumindo que o usuário rodará ambos ou que este é o consolidado)

CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS documents_fts_idx ON documents USING GIN (fts);

-- Gatilho para FTS
CREATE OR REPLACE FUNCTION documents_fts_trigger() RETURNS trigger AS $$
BEGIN
  new.fts :=
    setweight(to_tsvector('portuguese', COALESCE(new.content, '')), 'A') ||
    setweight(to_tsvector('portuguese', COALESCE(new.metadata->>'title', '')), 'B');
  RETURN new;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_documents_fts BEFORE INSERT OR UPDATE
ON documents FOR EACH ROW EXECUTE FUNCTION documents_fts_trigger();
