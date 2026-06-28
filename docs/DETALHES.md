# Detalhes Técnicos e Credenciais

## Stack Tecnológica
- **Linguagem:** Python 3.9 (FastAPI)
- **Gestão de Ambiente:** `venv` (ou Pipenv). Localizado em `/backend/venv/`.
- **RAG Engine:** Oracle OCI Generative AI Agents API
- **Observabilidade:** Langfuse Cloud (SDK Python)
- **Feedback & DB:** Supabase & N8N

## Autenticação Oracle (OCI)
O sistema não usa o CLI global, usa o SDK de Python autenticado via `.env` no diretório backend. Chaves cruciais:
- `OCI_USER`, `OCI_FINGERPRINT`, `OCI_TENANCY`, `OCI_REGION`
- `OCI_KEY_FILE`: Aponta para um ficheiro `.pem` (ex: `oracle_key.pem`) no root do backend.
- *Cuidado:* As rotinas OCI sofrem de limitação de paginação (geralmente param nos 1000 items). Scripts personalizados estão na pasta `scratch/` ou `scripts/` para usar `list_objects(limit=1000)` e o token `next_start_with`.

## Telemetria (Langfuse)
As variáveis necessárias no `.env` do backend são:
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_HOST`

### Prompt Otimizado para o LLM-as-a-Judge (Langfuse)
Se for necessário recriar o Avaliador de Alucinações, use este Template exato no painel web:
```text
Atue como um Juiz perito em História da Igreja e especialista na vida do Padre Leão Dehon (fundador da Congregação dos Sacerdotes do Sagrado Coração de Jesus - SCJ).
A sua tarefa é avaliar a precisão e a utilidade da Resposta da IA perante a Pergunta do Utilizador.

Pergunta do Utilizador:
{{input}}

Resposta da IA:
{{output}}

Avalie a Resposta da IA com base nos seguintes critérios:
1. Alucinação: A IA inventou datas, nomes de cartas ou conceitos teológicos que não pertencem à espiritualidade Dehoniana?
2. Relevância: A resposta responde diretamente ao que o utilizador perguntou de forma clara e respeitosa?

Atribua uma nota de 0 (se a resposta for inútil, inventada ou errada) até 1 (se a resposta for excelente, precisa e segura).
Responda apenas com o valor numérico.
```
