# Backend Setup

## Estrutura Inicial
- APIs REST/async (FastAPI)
- Integração com LLM e RAG (OpenAI GPT-4o)
- Banco de dados vetorial (pgvector via Supabase) e relacional

## Tecnologias
- Python 3.9 + FastAPI + Uvicorn
- Supabase (PostgreSQL + pgvector)
- OpenAI (text-embedding-3-large, GPT-4o)
- Sentence-Transformers (Cross-Encoder para reranking)

## Próximos Passos
1. Configurar variáveis de ambiente (ver .env.example).
2. Instalar dependências: `pip install -r requirements.txt`.
3. Iniciar servidor: `uvicorn main:app --reload`.