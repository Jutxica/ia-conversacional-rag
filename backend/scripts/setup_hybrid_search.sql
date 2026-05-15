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
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 24, ef_construction = 128); -- Parâmetros ajustados para maior recall acadêmico

-- Remove versões anteriores da função
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float);
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float, text[]);
DROP FUNCTION IF EXISTS hybrid_search(text, vector, int, float, float, text[], text[]);

-- Função de Busca Híbrida (Vetor + FTS) Normalizada
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
      -- Normalização: divide o total pela soma dos pesos máximos possíveis
      (
        -- Similaridade de Cosseno está em [0, 1]
        (vector_weight * (1 - (d.embedding <=> query_embedding))) +
        
        -- Normaliza FTS: ts_rank_cd é pequeno (ex: 0.05). Multiplicar por 10 e limitar a 1.0 aproxima o FTS da escala [0, 1]
        (full_text_weight * LEAST(1.0, ts_rank_cd(d.fts, websearch_to_tsquery('simple', query_text)) * 10.0)) +
        
        -- Boost por Entidade Moderado (+0.2 máximo em vez de 1.5)
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
    AND (1 - (d.embedding <=> query_embedding)) > 0.15 -- Threshold mínimo de segurança
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
