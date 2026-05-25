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
- **Redução do `index.css`**: O arquivo atual possui 3900+ linhas. É necessário:
    - Extrair estilos específicos de componentes para arquivos `.module.css` ou usar variáveis CSS centralizadas.
    - Remover estilos legados de versões anteriores do design.

---

## 3. Funcionalidades de Alta Performance (RAG UI)

### 🧐 Visualização de Fontes Integrada ✅ CONCLUÍDO
- ~~Implementar um modal ou "side-drawer" que permita abrir o documento original (PDF ou texto bruto) ao clicar em uma citação, destacando o parágrafo exato que a IA usou.~~ (O painel lateral já está funcional no `App.tsx` usando `activeCitationMessageId`).

### 📊 Indicadores de Confiança ✅ CONCLUÍDO
- ~~Melhorar visualmente o `badge` de confiança, usando gradientes sutis em vez de cores sólidas, e adicionando um tooltip que explique *por que* a confiança está naquele nível.~~ (Implementado através do envio de metadados de confiança pelo backend via SSE).

### 🔄 Gestão de Estado de Contexto ✅ CONCLUÍDO
- ~~Corrigir a lacuna apontada nos testes (TC005): garantir que o `conversation_id` seja mantido no frontend para pesquisas de múltiplos turnos.~~ (O parâmetro `conversation_id` agora é armazenado e trafegado corretamente).

---

## 4. Checklist de Implementação (Fase 1) ✅ CONCLUÍDO

- [x] **Criar Estrutura de Pastas**: Organizar `src/components`, `src/hooks` e `src/styles`.
- [x] **Extrair Componentes do App.tsx**: Componentes de Layout e Chat já estão separados (embora o App.tsx precise de mais redução).
- [x] **Refinar Tipografia**: Aplicar `Lora` nas respostas da IA via `ReactMarkdown` (Prose + font-serif).
- [x] **Bento Grid de Citações**: Terminar de refinar o layout da `.citations-section` para cards estilo museu no painel e na grid (Bento-Grid implementado em `CitationGrid.tsx`).
- [x] **Feedback de Streaming**: Melhorar o cursor de digitação e o estado de "Thinking" (pensando).
- [x] **Limpeza de CSS**: Refatorar o `index.css` global para reduzir tamanho e usar classes utilitárias do Tailwind (Removidas ~430 linhas redundantes de código morto).

---

## 5. Checklist de Implementação (Fase 2) ✅ CONCLUÍDO

- [x] **Painel de Logs SSE (`LiveLogsPanel`)**: Implementação de visualizador de logs em tempo real para monitorar processos de ingestão e normalização de PDFs e URLs.
- [x] **Visualizador e Editor de Chunks**: Edição direta do conteúdo bruto dos fragmentos com recalculagem imediata de embeddings e marcação com badge `EDITADO`.
- [x] **Página de Analytics**: Cards informativos com estatísticas de chats ativos, contagem de vetores e eficiência do cache de embeddings.

---

> [!TIP]
> **Design Pro**: "Menos é mais". Na estética Scholarly, o espaço em branco (white space) é seu melhor amigo. Ele transmite autoridade e foco no conteúdo sagrado/acadêmico.
