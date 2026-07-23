export interface CitationMetadata {
  title?: string;
  author?: string;
  page_number?: string | number;
  sigla?: string;
  [key: string]: any;
}

export interface Citation {
  content: string;
  metadata?: CitationMetadata;
}

export interface MessageMetadata {
  trust_score?: number;
  [key: string]: any;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
  metadata?: MessageMetadata;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  conversation_id?: string;
  scope?: string;
}

export interface ChatHistoryPayload {
  role: 'user' | 'assistant';
  content: string;
}
