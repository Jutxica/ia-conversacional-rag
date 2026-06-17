# Contexto do Sistema: Dehon AI (RAG)

## 1. Visão Geral
O **Dehon AI** é uma inteligência artificial especializada no pensamento, vida e obra do Padre Leão Dehon. Atua como um curador acadêmico, facilitando pesquisas teológicas, históricas e sociais com um alto grau de precisão, usando arquitetura RAG (Retrieval-Augmented Generation).

## 2. Arquitetura do Sistema

O sistema possui duas camadas principais:

### 2.1 Backend (Python / FastAPI)
- **Framework:** FastAPI
- **Banco de Dados:** Supabase (PostgreSQL com `pgvector`).
- **Embedding:** OpenAI `text-embedding-3-large` (reduzido a 2000 dimensões, otimizado para distância de cosseno).
- **LLM:** OpenAI `gpt-4o` para geração de respostas.
- **RAG Engine:** 
  - Busca Híbrida (Vetor + Full Text Search) com RRF (Reciprocal Rank Fusion).
  - Cross-Encoder Re-ranker (`ms-marco-MiniLM-L-6-v2`) para ordenar os melhores resultados.
  - Query Intent Detector (Detecta intenções: Histórica, Teológica, Citação, Geral) para ajustar dinamicamente os pesos da busca.
  - **Estratégia Parent-Child (Dupla Camada):** Ingestão divide documentos em chunks pais (Parent) de ~1000 tokens para contexto e chunks filhos (Child) de ~200 tokens para alta resolução vetorial. Os vetores filhos apontam para o texto do pai nos metadados (`parent_text`). A busca recupera o contexto do pai, com fallback para busca de vizinhos ordenados.
  - **Incremental Record Manager:** Ingestão com verificação de hashes SHA-256 (`file_hash` e `content_hash`). Ignora documentos idênticos (`skipped`) e remove de forma limpa chunks antigos antes de re-processar arquivos modificados.
  - **Semantic Query Cache:** Cache baseado em tempo (TTL) para os embeddings de queries frequentes, mitigando consumo de tokens e latência.
- **Ingestão:** Suporta upload de PDFs e URLs (via Firecrawl, PyMuPDF e BeautifulSoup). Inclui token-aware chunking (com overlap dinâmico e robustez para grandes blocos de texto sem pontuação).
- **Admin:** Endpoints protegidos por JWT para gestão do corpus, CRUD de siglários/respostas validadas, edição direta de chunks via `PUT /api/admin/chunks/{chunk_id}` com re-vetorização e marcação `edited: true`, e stream de logs de ingestão via SSE.
- **Configuração e Conectividade:**
  - **CORS Estendido:** Permite conexões do localhost, subdomínios do Render (`.onrender.com`) e domínios de produção da instituição Conventinho (`*.conventinho.org.br`).
  - **Ambiente Resiliente:** Higienização de strings em variáveis de ambiente via `get_env_clean()` para mitigar falhas de parseamento (como valores vazios ou aspas residuais) comuns em deploys como o Render.
  - **Fallbacks Seguros:** Fallbacks para credenciais do Supabase e chaves de API internas para garantir funcionamento estável em testes e produção.

### 2.2 Frontend (React / Vite)
- **Framework:** React com Vite, TypeScript.
- **Estilização:** CSS Vanilla (Foco em Glassmorphism e Variáveis Dinâmicas).
- **Design System:** Estética "The Scholarly Gallery", focada em leitura acadêmica, cores neutras (creme/papel), fontes Lora (Serif) e Inter.
- **Componentização:** A interface apresenta extração modular (ex: `Sidebar`, `ScholarlyHome`, `MessageList`, `CitationGrid`).
- **Autenticação:**
  - **Carrossel de Fotos Históricas:** Carrossel imersivo na tela de login/registro utilizando fotos reais e restauradas de alta fidelidade do Padre Dehon com efeito de zoom suave (Ken Burns effect).
  - **Adaptação Mobile:** O carrossel atua como plano de fundo desfocado em tela cheia nos dispositivos móveis sob o card de login em glassmorphism.
- **Perfil do Usuário:**
  - **Configurações Personalizadas:** Painel de perfil (`ProfileModal.tsx`) permitindo definir nome de usuário, avatar customizado e saudações personalizadas na Home (ex: "Olá, João").
- **Funcionalidades RAG UI:** 
  - **Controle Manual de Referências:** Toggles no cabeçalho das mensagens do assistente para abrir/fechar o Bento-Grid de citações manualmente, desabilitando o comportamento de auto-abrir para preservar o foco da leitura.
  - **Tipografia e Estilo:** Mensagens do usuário formatadas como balões arredondados e alinhados à direita. Fontes serifadas (Lora) e renderização defensiva via `safeRender` para evitar erros de renderização (React Error 31).
  - **Otimização de Splash Screens:** Redução do atraso inicial para 2 segundos no app, remoção de delays artificiais no admin e inclusão de um spinner customizado com animação ping de avatar.
  - **Logs e Analytics:** Painel lateral SSE (`LiveLogsPanel`) e página de Analytics mapeando chats, cache de embeddings e banco de vetores.
  - **Coleções/Escopo:** Filtros e checkboxes na barra lateral para restringir a busca semântica a categorias específicas (ex: apenas Cartas ou Diários) integradas diretamente nas chamadas de busca do backend.
  - **Visualizador e Editor de Chunks:** Interface integrada na aba "Corpus" para inspecionar, editar chunks de texto individualmente com salvamento no backend e exibição de badge `EDITADO`.

## 3. Fluxo de Dados (RAG Flow)
1. **Pergunta:** Usuário envia a query com um "scope" (ex: Geral, Espiritualidade) ou categorias específicas selecionadas.
2. **Intent Detection:** O backend detecta a intenção e define os pesos (Vector vs FTS).
3. **Retrieval:** O backend busca chunks no Supabase (`hybrid_search_rrf`), filtrando por siglas pertencentes ao escopo/categorias selecionadas e usando embeddings.
4. **Context Mapping:** Caso os chunks correspondam a "filhos", o RAG extrai o `parent_text` associado nos metadados. Se indisponível (legados), recupera os chunks vizinhos (`chunk_index ± 1`).
5. **Re-ranking:** Os resultados passam pelo Cross-Encoder, retornando um Score de Confiança exato.
6. **Geração:** O modelo `gpt-4o` generates a resposta baseada exclusivamente nas fontes recuperadas, aplicando regras de citação estritas.
7. **Streaming:** A resposta é transmitida para o Frontend junto com metadados (Citações e Nível de Confiança).

## 4. Estado Atual e Próximos Passos
- **Concluído:** Ingestão de documentos via painel Admin, busca híbrida avançada com RRF, Re-ranking, Intents de Busca, Gestão de Conversas (Histórico), Painel de citações bento-grid, layout com textura de papel, Ingestão Incremental (hashes), Ingestão Parent-Child (dupla camada), Cache Semântico de query, Edição inline de Chunks com badge `EDITADO`, Ingestão de Logs via SSE, Checkboxes de escopo/coleção na UI, Carrossel com efeito Ken Burns no login, Perfil do Usuário com avatar/saudação e controle manual de referências no cabeçalho das mensagens.
- **Pendente:**
  1. Reranking Híbrido Local (reduzir latência executando re-ranking no cliente).
  2. Visualizador de Embeddings 3D (representação geométrica dos chunks).
