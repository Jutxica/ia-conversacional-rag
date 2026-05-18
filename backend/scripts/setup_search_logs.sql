-- =============================================================================
-- Tabela de Logs de Busca e Feedback para Analytics
-- =============================================================================
-- Permite rastrear quais queries estão sendo feitas, quantos resultados
-- retornam, e como os usuários avaliam as respostas (polegar para cima/baixo).
-- =============================================================================

CREATE TABLE IF NOT EXISTS search_logs (
  id BIGSERIAL PRIMARY KEY,
  query TEXT NOT NULL,
  intent TEXT DEFAULT 'GENERAL',
  num_citations INT DEFAULT 0,
  confidence_level TEXT DEFAULT 'Baixa',
  confidence_pct INT DEFAULT 0,
  response_preview TEXT DEFAULT '',
  feedback TEXT CHECK (feedback IN ('positivo', 'negativo', NULL)),
  feedback_comment TEXT DEFAULT NULL,
  conversation_id TEXT DEFAULT NULL,
  ip_hash TEXT DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para consultas frequentes de analytics
CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON search_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_logs_feedback ON search_logs (feedback) WHERE feedback IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_search_logs_intent ON search_logs (intent);
CREATE INDEX IF NOT EXISTS idx_search_logs_low_confidence ON search_logs (confidence_level) WHERE confidence_level = 'Baixa';

-- Função para obter termos de busca frequentes com baixa confiança
CREATE OR REPLACE FUNCTION get_gap_terms(min_count INT DEFAULT 3)
RETURNS TABLE (term TEXT, frequency INT, avg_confidence NUMERIC) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    query AS term,
    COUNT(*)::INT AS frequency,
    AVG(confidence_pct)::NUMERIC(5,2) AS avg_confidence
  FROM search_logs
  WHERE confidence_level = 'Baixa'
  GROUP BY query
  HAVING COUNT(*) >= min_count
  ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;
