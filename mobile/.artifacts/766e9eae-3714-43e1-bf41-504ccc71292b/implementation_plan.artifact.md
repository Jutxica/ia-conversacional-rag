# Plano de Melhoria e Estruturação - Dehon AI

Este plano visa transformar o protótipo atual em um aplicativo modular, escalável e profissional, seguindo as melhores práticas de desenvolvimento React Native com Expo.

## User Review Required

> [!IMPORTANT]
> A reestruturação moverá o código do `App.tsx` para uma pasta `src/`. Isso mudará a forma como o código é organizado, mas manterá todas as funcionalidades atuais.
>
> [!NOTE]
> Vou sugerir a adição de algumas bibliotecas para melhorar a experiência do usuário, como `react-native-markdown-display` para um renderização de mensagens mais rica.

## Proposed Changes

### 1. Estrutura de Pastas
Organizaremos o projeto da seguinte forma:
- `src/components/`: Componentes de UI reutilizáveis (Botões, Inputs, Cards).
- `src/features/`: Módulos específicos (Chat, Login, Config).
- `src/services/`: Lógica de API e Armazenamento.
- `src/hooks/`: Custom hooks para lógica compartilhada.
- `src/theme/`: Definições de cores, fontes e espaçamentos.
- `src/types/`: Definições de TypeScript.
- `src/constants/`: Configurações globais e chaves.

### 2. Componentização [MODIFY]
Vou extrair as seguintes partes do `App.tsx`:
- **[NEW]** `src/features/chat/components/ChatMessage.tsx`: Renderização de mensagens individuais.
- **[NEW]** `src/features/chat/components/CitationModal.tsx`: Detalhes das fontes.
- **[NEW]** `src/features/chat/components/Sidebar.tsx`: Histórico de conversas.
- **[NEW]** `src/features/auth/screens/LoginScreen.tsx`: Tela de login e configuração de API.
- **[NEW]** `src/components/SplashScreen.tsx`: Splash screen animada.

### 3. Camada de Serviço [NEW]
- **[NEW]** `src/services/ChatService.ts`: Centralizará a lógica de comunicação via SSE (XMLHttpRequest).
- **[NEW]** `src/services/StorageService.ts`: Centralizará o uso do `AsyncStorage`.

### 4. Melhorias de UI/UX
- **Tema Centralizado:** Criação de um arquivo de tema para que a cor `#9f1239` e outras constantes não fiquem espalhadas.
- **Markdown:** Melhorar a renderização de negritos, listas e links nas respostas do assistente.
- **Feedback Visual:** Melhores estados de carregamento e transições suaves.

## Verification Plan

### Automated Tests
- Verificação de tipos com `tsc`.
- Build do Expo para garantir que a nova estrutura não quebrou o bundle.

### Manual Verification
- Testar o fluxo completo: Splash -> Login -> Chat -> Histórico.
- Verificar se as mensagens continuam chegando via streaming corretamente.
- Validar se as configurações de API são salvas e aplicadas.
