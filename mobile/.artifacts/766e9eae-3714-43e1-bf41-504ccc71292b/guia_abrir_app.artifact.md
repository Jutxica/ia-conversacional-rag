# Guia Definitivo: Como abrir o Dehon AI da melhor forma

Para garantir que o aplicativo carregue sem erros de cache ou conflitos de versão, siga este procedimento de "Inicialização Limpa".

## Passo 1: Limpeza de Processos
Certifique-se de que não existam outros servidores do Expo rodando em segundo plano.
- No terminal, você pode pressionar `Ctrl + C` para parar o processo atual.
- Se necessário, feche e abra o terminal do Android Studio novamente.

## Passo 2: O Comando de Inicialização Limpa
Sempre que fizermos alterações em dependências (como as que fizemos agora para corrigir o Babel), o ideal é usar a flag de limpeza de cache:

```bash
npx expo start -c
```
*O `-c` limpa o cache do Metro Bundler, garantindo que ele recompile tudo do zero com as novas correções.*

## Passo 3: Escolha do Ambiente de Visualização

Você tem três formas principais de visualizar o app:

### A. No seu Celular Físico (Recomendado)
1. Abra o app **Expo Go**.
2. No terminal, selecione a opção `s` se precisar reenviar o link ou apenas escaneie o **QR Code** que aparecerá.
3. Certifique-se de estar no **mesmo Wi-Fi**.

### B. No Emulador Android
1. Com o servidor rodando (após o comando do Passo 2), pressione a tecla **`a`** no seu teclado.
2. O Expo tentará abrir o emulador automaticamente e instalar o Expo Go nele.

### C. No Simulador iOS (Mac apenas)
1. Com o servidor rodando, pressione a tecla **`i`**.

## Passo 4: Dicas de Ouro para Desenvolvedores
- **Menu de Dev:** Se o app travar ou você quiser forçar um recarregamento, balance o celular (ou `Ctrl+M` no emulador) e clique em **Reload**.
- **Logs:** Fique de olho no terminal do Android Studio. Se algo der errado, o erro aparecerá lá com detalhes.
- **Modo Túnel:** Se o seu Wi-Fi for corporativo ou restrito e o QR Code não funcionar, use:
  ```bash
  npx expo start --tunnel
  ```

---
> [!TIP]
> Agora que corrigimos o `babel-preset-expo`, o app deve carregar todos os módulos (mais de 2000!) corretamente. A primeira carga pode demorar um pouco mais, mas as próximas serão instantâneas.
