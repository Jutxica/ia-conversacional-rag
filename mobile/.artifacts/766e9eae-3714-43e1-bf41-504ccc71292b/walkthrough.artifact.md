# Walkthrough - Reestruturação Dehon AI

Concluí a reestruturação completa do projeto para um padrão modular e escalável. O aplicativo agora está organizado em uma estrutura `src/`, separando temas, tipos, serviços e componentes.

## Mudanças Realizadas

### 🏗️ Arquitetura e Organização
- **[NEW]** Criada estrutura de diretórios `src/` com subpastas: `components`, `services`, `features`, `hooks`, `theme`, `types`.
- **[NEW]** `src/theme/index.ts`: Centralização de cores e tipografia.
- **[NEW]** `src/types/chat.ts`: Definição rigorosa de interfaces TypeScript para Mensagens, Conversas e Citações.

### ⚙️ Camada de Serviços
- **[NEW]** `src/services/StorageService.ts`: Abstração do `AsyncStorage` para gerenciamento de persistência de forma limpa.
- **[NEW]** `src/services/ChatService.ts`: Encapsulamento da lógica complexa de streaming SSE (XMLHttpRequest), removendo-a do componente principal.

### 🎨 Componentização de UI
- **[NEW]** `src/components/SplashScreen.tsx`: Extraído do `App.tsx` para componente reutilizável.
- **[NEW]** `src/features/auth/screens/LoginScreen.tsx`: Tela de login isolada com lógica de configuração de API.
- **[NEW]** `src/features/chat/components/ChatMessage.tsx`: Lógica de renderização de mensagens e formatação básica de markdown.
- **[NEW]** `src/features/chat/components/CitationModal.tsx`: Modal detalhado para exibição de fontes teológicas.
- **[NEW]** `src/features/chat/components/Sidebar.tsx`: Gaveta de histórico com animações controladas.

### 🔄 Refatoração do `App.tsx`
- Reduzido drasticamente o tamanho do arquivo.
- Agora o `App.tsx` atua principalmente como um orquestrador de estado e navegação simples entre as telas de Login e Chat.

## Próximos Passos Sugeridos
1.  **Navegação Real:** Implementar `react-navigation` para gerenciar as rotas de forma nativa.
2.  **Markdown Profissional:** Adicionar a biblioteca `react-native-markdown-display` para suporte completo a tabelas e blocos de código.
3.  **Hilt/Context API:** Se o app crescer, podemos adicionar `Context API` para evitar o "prop drilling" de configurações de API.

> [!TIP]
> O app agora é muito mais fácil de testar, pois a lógica de API (`ChatService`) e Armazenamento (`StorageService`) pode ser mockada separadamente da UI.
