# Product Requirements Document (PRD) - Dehon AI

## 1. Visão Geral do Produto
**Nome do Produto:** Dehon AI  
**Descrição:** Uma plataforma de Inteligência Artificial Conversacional baseada em arquitetura RAG (Retrieval-Augmented Generation) desenhada para pesquisa, análise e diálogo com o acervo literário e histórico Dehoniano (arquivos, cartas, biografias e teologia associada ao Padre Dehon).  
**Público-Alvo:** Pesquisadores, acadêmicos, estudantes de teologia, congregações e entusiastas que buscam acesso rápido e contextualizado à vasta literatura da fundação Dehoniana.

## 2. Objetivos de Negócio e de Usuário
- **Acesso Democrático e Preciso:** Reduzir o tempo de pesquisa em documentos históricos de horas para segundos, entregando as fontes exatas de onde a informação foi extraída.
- **Experiência Premium (Scholarly Gallery):** Prover uma interface focada na leitura e imersão acadêmica, com design responsivo, elegante e limpo.
- **Preservação de Contexto Histórico:** Manter a semântica, a cronologia e a voz teológica através de estratégias avançadas de fragmentação (chunking) e boosting temático no backend.

## 3. Métricas de Sucesso (KPIs)
- **Acurácia da Resposta:** Taxa de aceitação das respostas pelos usuários (avaliada via botões de 👍/👎).
- **Fidelidade às Fontes (Hallucination Rate):** Porcentagem de respostas que citam fontes verificáveis e textuais vs. respostas excessivamente genéricas ou inferidas.
- **Engajamento Acadêmico:** Tempo médio de sessão e taxa de interação com as citações originais (uma sessão longa e cliques nas fontes indicam uma pesquisa profunda bem-sucedida).
- **Performance:** Tempo médio para o First Token (TTFT) e tempo total de resposta.

---

## 4. Histórias de Usuário (User Stories)
- *“Como pesquisador, quero clicar em uma citação na resposta e ser levado exatamente ao parágrafo do documento original no visualizador de PDF/Texto, para que eu possa validar o contexto.”*
- *“Como estudante, quero exportar o resumo de uma conversa formatado em normas ABNT/APA com as referências incluídas, para usar na minha tese.”*
- *“Como arquivista, quero ter a certeza de que a IA responderá no meu idioma (ex: Português), mesmo que o documento consultado esteja originalmente em Latim ou Francês.”*

---

## 5. Requisitos Funcionais (Core Features)

### 5.1. Interface de Conversação (Frontend)
- **Chat em Tempo Real:** Interface de mensagens semelhante aos principais LLMs do mercado, suportando streaming de texto (token a token).
- **Indicadores de Estado (Agentic UI):** Fornecer visibilidade total do estado da IA. Em vez de telas estáticas de "Carregando...", usar texturas "Shimmer" animadas e frases descritivas do processo atual (ex: *"Consultando o acervo dehoniano..."*).
- **Apresentação de Confiança e Fontes:** A resposta deve acompanhar um "Badge de Confiança" da pesquisa gerada e um botão claro de *Ver Referências no Painel* para acesso às citações e excertos originais.
- **Citações Inline e Download:** As citações devem aparecer no meio do texto (ex: [1], [2]) e serem clicáveis para abrir um "Side Panel" de pré-visualização. Se não houver restrições de direitos autorais, disponibilizar a opção de download da fonte.
- **Histórico de Conversas (Sidebar):** Uma barra lateral para navegação de conversas passadas e controle de perfil de usuário.

### 5.2. Motor de Busca e IA (Backend RAG)
- **Busca Híbrida Inteligente:** Utilização de vetores de alta precisão somados a buscas por palavras-chave (Full Text Search) para não perder nenhum detalhe nominal ou teológico.
- **Etapa de Re-ranking:** Implementação de um Reranker (como Cohere Rerank ou BGE-Reranker) após a busca híbrida inicial para garantir que os Top-N documentos passados para a LLM sejam estritamente os mais semanticamente relevantes.
- **Expansão de Contexto Automática:** Ao recuperar um trecho do texto, o backend deve ser capaz de olhar o parágrafo anterior e o seguinte (`chunk_index -1` e `+1`) para entregar à LLM um contexto coeso e não cortado.
- **Multilinguismo (Cross-lingual Support):** Capacidade de pesquisar e interpretar documentos originais em Latim, Francês, Italiano, etc., e retornar a resposta sintetizada no idioma da requisição do usuário.
- **Boosting de Relevância:** Aumentar a importância de respostas baseadas em metadados específicos (ex: datas, destinatários de cartas).

#### 5.2.1. Atribuição de Fontes
Cada resposta gerada deve obrigatoriamente retornar metadados contendo: `document_title`, `page_number`, `archive_url` e `snippet_preview`. A interface deve mapear esses IDs para renderizar links navegáveis.

---

## 6. Gestão de Dados (Data Pipeline)
- **Pipeline de Ingestão:** Previsão de um fluxo estruturado (futuro dashboard administrativo) para o upload contínuo de novos documentos (PDFs, TXTs, Scans).
- **Versionamento de Embeddings:** Manutenção e versionamento do índice de embeddings, prevendo re-indexações totais caso o modelo de embedding seja substituído futuramente.

---

## 7. Requisitos Não-Funcionais (Arquitetura e Performance)

### 7.1. Stack Tecnológico
- **Frontend:** React + TypeScript + Vite. 
- **Estilização:** CSS purista, sem dependência exagerada de frameworks terceiros pesados, focando em propriedades modernas (Glassmorphism, Flat 2.0, variáveis CSS dinâmicas para Dark/Light mode).
- **Backend:** Python + FastAPI (sugerido para alto desempenho em I/O e modelos de IA).
- **Banco de Dados / Vector Store:** PostgreSQL utilizando a extensão `pgvector` através do Supabase.

### 7.2. Especificações do Modelo RAG
- **Modelo de Embedding:** `text-embedding-3-large` da OpenAI (otimizado para o teto de 2000 dimensões para máxima performance com índices HNSW).
- **Geração de Texto:** Família Claude ou GPT compatível, configurada com um prompt de sistema (System Prompt) que respeite o *tone of voice* do acervo.

### 7.3. Escalabilidade e Segurança
- **Segurança de Tokens:** O script de ingestão e a janela de contexto de prompt deverão usar "Token Guards" para não ultrapassar os limites de requisição e diluir semântica.
- **Higienização de Texto OCR:** Tratamento contínuo dos textos históricos retirando resíduos de quebras de página, ligaturas mal formatadas e códigos HTML vazados.
- **Autenticação:** Proteção de uso da plataforma (limitando custos de API).

---

## 8. Casos de Borda e Limitações (Edge Cases)
- **Fallback Strategy:** Quando o índice vetorial não encontrar similaridade mínima (Threshold de Confiança baixo). A IA deve admitir a ausência de dados específicos no acervo e não alucinar uma resposta. Ex: *"Não encontrei informações específicas no acervo sobre isso, mas com base na biografia geral de Dehon..."*
- **Tratamento de Ambiguidade:** Em tópicos muito amplos (ex: "Amor" ou "Sagrado Coração"), a IA deve focar na visão teológica de Dehon ou iniciar um diálogo desambiguador (perguntando se o usuário quer saber sobre cartas, sermões ou publicações oficiais).

---

## 9. Diretrizes de Interface e Design (UI/UX)
- **Scholarly Gallery:** O design segue o conceito de galeria de estudos.
- **Dark Mode (Midnight):** O modo noturno não usa cores pretas puras em tudo, mas variações de pedras/cinzas escuros com acentos suaves de azul (Royal Blue) e dourado (Antique Gold).
- **Micro-interações:** Todos os botões primários contam com sombras de múltipla camada (`box-shadow`), e *hover states* com elevação ("bounce" magnético) de 0.2 segundos.

---

## 10. Fora de Escopo (Out of Scope - Fase 1)
Para evitar o *Scope Creep*, as seguintes funcionalidades **não** fazem parte do MVP atual:
- O Dehon AI **não** realizará análises de documentos externos enviados pelo usuário (upload de PDFs pessoais não relacionados ao acervo).
- A plataforma **não** substituirá o repositório oficial ou biblioteca física/digital, servindo apenas como uma camada inteligente de consulta e recuperação referencial.

---
*Este documento é uma entidade viva e deve ser atualizado à medida que o motor RAG avança em precisão e os componentes frontend são escalados.*
