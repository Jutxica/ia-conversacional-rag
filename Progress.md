# Progresso do Projeto - Dehon AI
*Última atualização: 14 de Maio de 2026*

Este documento registra os marcos alcançados no desenvolvimento do ecossistema Dehon AI, abrangendo interface, inteligência artificial e automação de desenvolvimento.

---

## 🏗️ 1. Frontend & Design (The Scholarly Gallery)
**Status:** ✅ Funcional e Refinado

- **Interface Premium:** Implementação completa da estética "Scholarly Gallery", focada em legibilidade acadêmica e sofisticação visual.
- **Componentização Modular:**
    - `Sidebar`: Gestão de histórico, navegação modular e funcionalidade de exclusão de conversas.
    - `ScholarlyHome`: Layout principal com painéis flutuantes e tipografia curada.
    - `ChatInput`: Interface de entrada com suporte a Glassmorphism e micro-animações.
- **Responsividade:** Ajustes específicos para mobile, incluindo espaçamento vertical otimizado e botões de ação (delete/edit) adaptados para touch.
- **Design Tokens:** Sistema de cores (Midnight/Antique Gold) e sombras multicamadas padronizados via CSS purista.

## 🧠 2. Backend & RAG (Retrieval-Augmented Generation)
**Status:** ✅ Estável e Operacional

- **Infraestrutura de Dados:** Migração concluída para **Supabase** utilizando a extensão `pgvector`.
- **Corpus Literário:** Indexação de ~5.100 fragmentos do acervo Dehoniano.
- **Motor de Busca Híbrida:** Integração de busca vetorial (semântica) com busca por palavras-chave (Full Text Search).
- **Estratégia de Chunking:** Fragmentação com sobreposição (overlap) para preservação de contexto histórico.
- **Threshold Dinâmico:** Implementação de limites de caracteres diferenciados para Cartas e Obras Gerais, otimizando a recuperação.

## 🤖 3. Automação e Orquestração (Archon & Claude Code)
**Status:** ✅ Configurado e Integrado

- **Claude Code:** Instalado e autenticado via Anthropic Console (API Billing).
- **Archon Framework:**
    - Servidor local ativo em `localhost:3090`.
    - Registro do projeto `rag-project` no banco de dados do Archon.
    - Configuração de binários e caminhos de sistema (`~/.zshrc`) para Bun e Claude.
- **Workflow Idea-to-PR:** Capacidade de orquestração automatizada para novas funcionalidades, garantindo ciclos de teste e segurança via branches Git.

---

## 🧪 4. Qualidade, Testes & Analytics (Atualizado em Maio/2026)
- **Query Intent Detection:** Sistema avançado de classificação de intenção (HISTORICAL, THEOLOGICAL, CITATION, GENERAL) com ajuste dinâmico de pesos de busca.
- **Dynamic Confidence Score:** Cálculo de confiança baseado no cross-encoder reranker, exposto no metadata do streaming.
- **RRF (Reciprocal Rank Fusion):** Nova função `hybrid_search_rrf` no Supabase que combina rankings vetorial e FTS de forma mais robusta.
- **Search Logs & Feedback:** Tabela `search_logs` para analytics de busca + endpoints de feedback (polegar para cima/baixo) e identificação de gaps de conhecimento.
- **Testes Automatizados:** Suite pytest com 24 testes para intent detector, concept processor e normalização.
- **Token Guard:** Sub-chunking por token no modo Thematic (bookmarks) + fragmentação de parágrafos gigantes.
- **Normalização Auditada:** Expansão de ligaduras, normalização Unicode NFC, remoção de HTML residual, padronização de aspas/hífens.

## 📈 Próximos Passos Imediatos
1.  ~~Implementação de **Cross-Encoder Re-ranker** para precisão cirúrgica.~~ ✅
2.  ~~Detecção de **Intenção de Query** (Historical vs Theological).~~ ✅
3.  ~~Exibição de **Confidence Score** na UI para o usuário final.~~ ✅
4.  **WebSocket para logs/admin** — notificar admin quando ingestão termina.
5.  **Threshold dinâmico auto-ajustável** — calibrar limites de confiança com dados reais.
