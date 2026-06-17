# 🏛️ Plano de Evolução: Frontend Dehon AI
## Estética "The Scholarly Gallery"

Este documento detalha as sugestões e modificações propostas para elevar a interface da Biblioteca Dehoniana a um padrão editorial e acadêmico de alto nível.

---

## 1. Identidade Visual & Design System (The Scholarly Gallery)

O objetivo é criar uma experiência imersiva que remeta ao ato de pesquisar em um arquivo histórico físico, mas com a agilidade da IA.

### 🎨 Paleta de Cores & Texturas
- **Base (Papel de Arquivo)**: Substituir o `#fafaf9` atual por uma variação mais sutil de creme (`#F7F5F2`) com o efeito de grão (noise) que já existe, mas levemente mais nítido nas bordas.
- **Destaque (Azul Intelectual)**: Manter o azul royal, mas utilizá-lo apenas para ações primárias e links de fontes.
- **Tipografia**:
    - **Títulos**: `Outfit` ou `Lora` (Serif) para um ar clássico.
    - **Corpo da Resposta**: `Lora` (Serif) com `line-height: 1.7` para leitura prolongada.
    - **Interface/Sistema**: `Inter` (Sans) para clareza em botões e menus.

### ✨ Efeitos e Micro-interações
- **Glassmorphism**: Aumentar o efeito de vidro fosco no header e sidebar para dar profundidade.
- **Staggered Reveal**: Usar animações (CSS ou GSAP) para revelar citações uma a uma, como se estivessem sendo "colocadas na mesa".
- **Citações Bento-Grid**: Transformar a seção de evidências documentais em um grid de cards elegantes, inspirados em exposições de museus.

---

## 2. Refatoração e Limpeza de Código

O estado atual do projeto apresenta alta densidade em arquivos únicos, o que dificulta a manutenção.

### 🧱 Modularização (Componentização)
- **`src/components/layout/`**:
    - `Sidebar.tsx`: Gestão de histórico e busca.
    - `Header.tsx`: Ações globais, login/logout e status de sincronização.
- **`src/components/chat/`**:
    - `MessageList.tsx`: Orquestração das mensagens.
    - `MessageRow.tsx`: Lógica individual de cada mensagem (User vs Assistant).
    - `CitationsGrid.tsx`: Exibição visual das fontes citadas.
- **`src/components/home/`**:
    - `HomeView.tsx`: A tela inicial estilo "Manus" com sugestões.

### 🧹 CSS Optimization
- **Redução do `index.css`**: O arquivo original possuía 3900+ linhas. Foi refatorado reduzindo cerca de 430 linhas de código redundante e centralizando variáveis no tema global.

---

## 3. Funcionalidades de Alta Performance (RAG UI)

### 🧐 Visualização de Fontes Integrada ✅ CONCLUÍDO
- O painel lateral está funcional no `App.tsx` usando `activeCitationMessageId` e exibe as citações em formato Bento-Grid.

### 📊 Indicadores de Confiança ✅ CONCLUÍDO
- Badge de confiança e progresso baseado no score do cross-encoder do backend, exibido de forma fluida.

### 🔄 Gestão de Estado de Contexto ✅ CONCLUÍDO
- O parâmetro `conversation_id` é mantido para pesquisas multi-turno.

---

## 4. Checklist de Implementação (Fase 1) ✅ CONCLUÍDO

- [x] **Criar Estrutura de Pastas**: Organizar `src/components`, `src/hooks` e `src/styles`.
- [x] **Extrair Componentes do App.tsx**: Componentes de Layout e Chat já estão separados (App.tsx modular).
- [x] **Refinar Tipografia**: Aplicar `Lora` nas respostas da IA via `ReactMarkdown` (Prose + font-serif).
- [x] **Bento Grid de Citações**: Layout da `.citations-section` para cards estilo museu no painel e na grid (Bento-Grid implementado em `CitationGrid.tsx`).
- [x] **Feedback de Streaming**: Cursor de digitação e o estado de "Thinking" (pensando) dinâmicos.
- [x] **Limpeza de CSS**: Refatorar o `index.css` global para reduzir tamanho (Removidas ~430 linhas redundantes de código morto).

---

## 5. Checklist de Implementação (Fase 2) ✅ CONCLUÍDO

- [x] **Painel de Logs SSE (`LiveLogsPanel`)**: Implementação de visualizador de logs em tempo real para monitorar processos de ingestão e normalização de PDFs e URLs.
- [x] **Visualizador e Editor de Chunks**: Edição direta do conteúdo bruto dos fragmentos com recalculagem imediata de embeddings e marcação com badge `EDITADO`.
- [x] **Página de Analytics**: Cards informativos com estatísticas de chats ativos, contagem de vetores e eficiência do cache de embeddings.

---

## 6. Checklist de Implementação (Fase 3: Imersão e Polimento Visual) ✅ CONCLUÍDO

- [x] **Carrossel de Imagens Ken Burns na Autenticação:** Transição suave de fotos históricas restauradas de Padre Dehon no login, servindo de background responsivo em mobile. Card de auth em glassmorphism sem escudo no botão principal.
- [x] **Configurações e Gestão de Perfil:** Modal de configurações de perfil (`ProfileModal.tsx`) para o pesquisador alterar nome, avatar customizado e saudações dinâmicas personalizadas na Home (ex: "Olá, João").
- [x] **Animações no ScholarlyHome:** Novo subtítulo com animação dinâmica `GooeyText` em negrito e layout Bento-Grid de sugestões reordenadas para visualização limpa acima da caixa de pesquisa.
- [x] **Controle Manual de Citações Drawer:** Desabilitado o comportamento de auto-abrir a barra lateral de citações que interrompia a leitura. Adicionado um botão de toggle com ícone no cabeçalho das respostas do assistente.
- [x] **Aceleração do Splash Screen:** Reduzido o timeout de splash inicial para 2s no frontend e removido o timeout de 3.5s no admin, substituindo a barra de progresso por um spinner de avatar com animação de pulso.
- [x] **Formatação Visual do Chat:** Mensagens do usuário formatadas como balões arredondados e alinhados à direita. Renderização defensiva via `safeRender` no frontend.
- [x] **Filtros de Coleção/Escopo na UI:** Checkboxes de categorias na barra lateral enviadas para filtrar a busca híbrida no banco de dados.

---

> [!TIP]
> **Design Pro**: "Menos é mais". Na estética Scholarly, o espaço em branco (white space) é seu melhor amigo. Ele transmite autoridade e foco no conteúdo sagrado/acadêmico.
