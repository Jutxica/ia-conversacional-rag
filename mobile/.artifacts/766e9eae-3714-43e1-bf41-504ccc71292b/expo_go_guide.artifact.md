# Guia de Acesso: Dehon AI no Expo Go

Para visualizar e testar o **Dehon AI** no seu dispositivo móvel usando o Expo Go, siga os passos abaixo. O Expo Go permite que você execute o app em tempo real sem precisar compilar o código nativo manualmente.

## 1. Preparação do Dispositivo

1.  **Instale o App:** No seu celular, baixe o aplicativo **Expo Go** na App Store (iOS) ou Google Play Store (Android).
2.  **Mesma Rede:** Certifique-se de que o seu computador e o seu celular estejam conectados à **mesma rede Wi-Fi**.

## 2. Iniciando o Servidor de Desenvolvimento

Abra o terminal na pasta raiz do projeto no Android Studio e execute o comando:

```bash
npx expo start
```

Isso abrirá o **Expo Dev Tools** no terminal e exibirá um **QR Code**.

## 3. Abrindo o App

### No Android:
1.  Abra o aplicativo **Expo Go**.
2.  Toque em **"Scan QR Code"** e aponte a câmera para o QR Code no terminal do seu computador.

### No iOS:
1.  Abra o aplicativo nativo de **Câmera**.
2.  Aponte para o QR Code no terminal.
3.  Toque na notificação do Expo que aparecerá no topo da tela.

## 4. Dicas de Uso no Expo Go

-   **Menu de Desenvolvedor:** Balance o celular ou pressione `Cmd + D` (iOS Simulator) / `Ctrl + M` (Android Emulator) para abrir o menu do Expo. Lá você pode recarregar o app (`Reload`) ou habilitar o `Remote Debugging`.
-   **Hot Reload:** Qualquer alteração que você fizer no código no Android Studio será refletida **instantaneamente** no celular após salvar o arquivo.

> [!WARNING]
> **Bibliotecas Nativas:** Como instalamos `expo-speech` e `expo-print` recentemente, se o Expo Go apresentar algum erro de "Module not found", tente iniciar o servidor com o cache limpo:
> `npx expo start -c`

## 5. Solução de Problemas de Conexão

Se o app não carregar:
1.  Verifique se o firewall do seu computador não está bloqueando o acesso.
2.  No terminal, você pode tentar forçar o modo túnel (útil se o Wi-Fi for restrito):
    `npx expo start --tunnel` (Isso pode exigir a instalação do pacote `@expo/ngrok`).

---
Agora você pode ver o **Dehon AI** ganhando vida no seu próprio celular!
