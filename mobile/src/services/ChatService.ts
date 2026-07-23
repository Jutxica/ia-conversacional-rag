import { ChatHistoryPayload } from '../types/chat';

export interface ChatRequest {
  apiUrl: string;
  apiKey?: string;
  query: string;
  scope: string;
  history: ChatHistoryPayload[];
  conversationId?: string | null;
  onToken: (token: string) => void;
  onCitations: (citations: any[]) => void;
  onMetadata: (metadata: any) => void;
  onConversationId: (id: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export const ChatService = {
  sendStreamRequest({
    apiUrl,
    apiKey,
    query,
    scope,
    history,
    conversationId,
    onToken,
    onCitations,
    onMetadata,
    onConversationId,
    onDone,
    onError
  }: ChatRequest) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${apiUrl}/api/chat`, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    if (apiKey) {
      xhr.setRequestHeader('Authorization', `Bearer ${apiKey}`);
    }

    const payload = {
      query,
      scope,
      history,
      conversation_id: conversationId,
      categories: []
    };

    let position = 0;

    xhr.onreadystatechange = () => {
      if (xhr.readyState === 3 || xhr.readyState === 4) {
        const responseText = xhr.responseText;
        const newChunk = responseText.substring(position);
        position = responseText.length;

        const lines = newChunk.split('\n');
        for (let line of lines) {
          line = line.trim();
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'token':
                  onToken(data.content);
                  break;
                case 'citations':
                  onCitations(data.content);
                  break;
                case 'metadata':
                  onMetadata(data.content);
                  break;
                case 'conversation_id':
                  onConversationId(data.conversation_id || data.content);
                  break;
                case 'done':
                  onDone();
                  break;
              }
            } catch (e) {
              // Fragmento de linha incompleto
            }
          }
        }
      }

      if (xhr.readyState === 4) {
        if (xhr.status >= 400) {
          onError(`Erro do servidor: ${xhr.status}`);
        } else {
          onDone();
        }
      }
    };

    xhr.onerror = () => {
      onError("Erro ao conectar ao servidor. Verifique sua conexão ou a URL da API.");
    };

    xhr.send(JSON.stringify(payload));

    return xhr; // Permite cancelar se necessário
  }
};
