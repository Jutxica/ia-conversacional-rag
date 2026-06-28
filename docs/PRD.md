# Product Requirements Document (PRD): Dehon AI

## 1. Visão Geral
O Dehon AI é um sistema de Inteligência Artificial conversacional focado no conhecimento teológico, histórico, sociológico e espiritual do Padre Leão Dehon e da Congregação dos Sacerdotes do Sagrado Coração de Jesus (SCJ). Utiliza arquitetura RAG (Retrieval-Augmented Generation) para responder a questões com base em documentos oficiais.

## 2. Público-Alvo
Estudiosos, investigadores, seminaristas, sacerdotes e leigos que pretendem explorar a fundo a espiritualidade e as obras do Padre Dehon.

## 3. Funcionalidades Principais (Core Features)
- **Agente Conversacional:** Oracle OCI Generative AI Agents acoplado a uma Knowledge Base (Base de Conhecimento).
- **Backend Estruturado:** Servidor construído em Python (FastAPI) para gestão das conversas, processamento de streaming de resposta e gestão de metadados.
- **Observabilidade Total:** Integração profunda com o Langfuse para monitorização (Traces), captura de métricas e Avaliação Baseada em IA (LLM-as-a-judge).
- **Gestão de Testes:** Datasets em código (Gold Standards) para testes de regressão sempre que os documentos base são atualizados.
- **Automação Integrada:** Workflows no N8N e base de dados no Supabase para gerir o feedback contínuo (Gosto / Não Gosto) na interface.
