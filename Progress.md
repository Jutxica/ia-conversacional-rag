# Progresso do Projeto - Dehon AI
*Última atualização: 29 de Maio de 2026*

Este documento registra os marcos alcançados no desenvolvimento do ecossistema Dehon AI, abrangendo interface, inteligência artificial e automação de desenvolvimento.

---

## 🏗️ 1. Frontend & Design (The Scholarly Gallery)
**Status:** ✅ Funcional e Refinado

- **Interface Premium:** Implementação completa da estética "Scholarly Gallery", focada em legibilidade acadêmica e sofisticação visual.
- **Carrossel de Autenticação Imersivo:** Carrossel de fotos históricas restauradas do Padre Dehon na tela de login/registro sob efeito Ken Burns (transição/zoom suaves) e design glassmorphic adaptado para mobile como background.
- **Configurações de Perfil:** Modal de usuário (`ProfileModal.tsx`) para alteração de nome de exibição e avatar, com saudações personalizadas na Home (ex: "Olá, João") e exibição do avatar customizado no chat.
- **Coleções e Categorias na UI:** Checkboxes integradas na barra lateral para filtragem dinâmica do escopo de busca, traduzindo categorias em siglas do corpus no backend.
- **Design de Títulos e Sugestões:** Subtítulo estilizado com a animação dinâmica `GooeyText` em negrito. Grade Bento-Grid de sugestões reordenadas para 2 colunas com larguras uniformes posicionadas acima da caixa de pesquisa.
- **Controle Manual de Citações:** Toggles no cabeçalho das respostas da IA para abrir e fechar a visualização do painel Bento-Grid de citações manualmente, desabilitando o comportamento auto-abrir intrusivo.
- **Splash Screen de Alta Velocidade:** Reduzido o tempo de splash delay no cliente para 2 segundos, removido o delay do admin, e introduzido um spinner de avatar com animação de pulso em substituição à barra linear.
- **Componentização Modular:**
    - `Sidebar`: Gestão de histórico, categorias de coleções, navegação modular e funcionalidade de exclusão de conversas.
    - `ScholarlyHome`: Layout principal com painéis flutuantes, GooeyText, Bento-Grid de sugestões e tipografia curada.
    - `ChatInput`: Interface de entrada com suporte a Glassmorphism e micro-animações.
- **Responsividade:** Ajustes específicos para mobile, incluindo espaçamento vertical otimizado e botões de ação (delete/edit) adaptados para touch.
- **Design Tokens:** Sistema de cores (Midnight/Antique Gold) e sombras modificadas padronizados via CSS purista.
- **Painel de Logs SSE:** Novo painel administrativo visual `LiveLogsPanel` para monitorar a ingestão de PDFs e URLs em tempo real.
- **Visualizador e Editor de Chunks:** Interface visual integrada na aba "Corpus" para inspecionar chunks e editar conteúdos manualmente com badge **EDITADO**.
- **Exportação Acadêmica:** Botão integrado de exportação que gera arquivos `.ris` compatíveis com gerenciadores (Zotero/Mendeley) e citações formatadas no padrão ABNT/APA prontas para copiar.
- **Estilo de Bolha de Chat:** Mensagens do usuário com estilo bubble à direita usando cores da identidade visual, com renderização defensiva via `safeRender`.

## 🧠 2. Backend & RAG (Retrieval-Augmented Generation)
**Status:** ✅ Estável e de Alta Performance

- **Infraestrutura de Dados:** Migração concluída para **Supabase** utilizando a extensão `pgvector`.
- **Corpus Literário:** Indexação de ~5.100 fragmentos do acervo Dehoniano.
- **Filtro de Coleções:** Integração de categorias enviadas pelo frontend na busca híbrida no Supabase, filtrando dinamicamente por siglas indexadas.
- **Resiliência e Conectividade:**
    - **get_env_clean:** Higienização de strings em variáveis de ambiente para mitigar falhas em deploys de cloud (como Render).
    - **CORS Estendido:** Permissão de acesso de origens locais e subdomínios do Render e da instituição Conventinho (`*.conventinho.org.br`).
    - **Fallbacks Seguros:** Fallbacks para credenciais Supabase e chaves internas de API caso variáveis estejam ausentes.
- **Motor de Busca Híbrida:** Integração de busca vetorial (semântica) com busca por palavras-chave (Full Text Search) com RRF.
- **Chunking Parent-Child (Dupla Camada):** Ingestão com fatiamento dual: chunks grandes (1000 tokens) para contexto semântico unificados a child chunks menores (200 tokens) para alta precisão de vetorização.
- **Robustez de Tokenização:** Algoritmo chunky de quebra por palavras que evita que sentenças ou parágrafos gigantes sem pontuação estourem o limite da API da OpenAI.
- **Record Manager & Ingestão Incremental:** Validação de integridade baseada em hashes SHA-256 para PDFs e URLs que pula documentos não modificados (`skipped`) e substitui de forma limpa os modificados.
- **Cache Semântico:** Implementação de `TTLCache` no backend para os embeddings das queries, reduzindo a latência e o consumo de tokens.

## 🤖 3. Automação e Orquestração (Archon & Claude Code)
**Status:** ✅ Configurado e Integrado

- **Claude Code:** Instalado e autenticado via Anthropic Console (API Billing).
- **Archon Framework:**
    - Servidor local ativo em `localhost:3090`.
    - Registro do projeto `rag-project` no banco de dados do Archon.
    - Configuração de binários e caminhos de sistema (`~/.zshrc`) para Bun e Claude.
- **Workflow Idea-to-PR:** Orquestração automatizada de novas branches e PRs para novas features com testes robustos.

---

## 🧪 4. Qualidade, Testes & Analytics
- **Query Intent Detection:** Classificação automática de intenção (HISTORICAL, THEOLOGICAL, CITATION, GENERAL) para pesos dinâmicos.
- **Dynamic Confidence Score:** Nível de confiança baseado no Cross-Encoder Reranker (`ms-marco-MiniLM-L-6-v2`) exposto na interface.
- **Logs SSE & Analytics:** Stream SSE em tempo real de logs de ingestão e página gerencial de Analytics no painel admin monitorando consumo do cache, total de chats e base vetorial.
- **Testes Automatizados:** Suíte do `pytest` estendida para **30 testes unitários** com 100% de sucesso, cobrindo intent detector, processor de conceitos, normalização, fatiamento Parent-Child robusto e Record Manager.

---

## 📈 Próximos Passos Imediatos
1.  **Reranking Híbrido Local:** Explorar compressão de pesos do cross-encoder para execução inteiramente local caso a latência aumente (via ONNX/WebGPU).
2.  **Visualizador de Embeddings 3D:** Desenvolver representação geométrica tridimensional dos chunks (t-SNE/UMAP).
