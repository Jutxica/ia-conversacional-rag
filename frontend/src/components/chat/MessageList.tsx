import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './MessageList.css';
import { Book } from 'lucide-react';
import { magneticEffect } from '../../utils/transitions';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
  metadata?: {
    confidence: { level: string; percentage: number };
  };
}

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  session: any;
  onViewCitations?: (messageId: string) => void;
}

const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  isStreaming, 
  session,
  onViewCitations 
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
    // Apply magnetic effect to all view-citations buttons
    const buttons = document.querySelectorAll('.view-citations-btn');
    buttons.forEach(btn => magneticEffect(btn as HTMLElement));
  }, [messages, isStreaming]);

  return (
    <div className="message-list" ref={scrollRef}>
      {messages.map((m, idx) => (
        <div key={m.id} className={`message-row ${m.role} animate-fade-in`}>
          <div className="message-avatar-wrapper">
            {m.role === 'user' ? (
              <div className="avatar-circle user">
                {session?.user?.email?.[0].toUpperCase() || 'U'}
              </div>
            ) : (
              <div className="avatar-circle assistant">
                <img src="/Avatar.png" alt="Dehon AI" className="avatar-img" />
              </div>
            )}
          </div>

          <div className="message-content-wrapper">
            <div className="message-header">
              <span className="sender-name">
                {m.role === 'user' ? 'Pesquisador' : 'Padre Dehon'}
              </span>
              {m.role === 'assistant' && m.metadata && (
                <div className="metadata-badges">
                  <span className={`confidence-badge ${m.metadata.confidence.level.toLowerCase()}`}>
                    Confiança {m.metadata.confidence.percentage}%
                  </span>
                  {m.metadata.intent && (
                    <span className={`intent-badge ${m.metadata.intent.toLowerCase()}`}>
                      {m.metadata.intent}
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className={`message-bubble ${m.role}`}>
              {m.role === 'assistant' && m.content === '' && isStreaming && idx === messages.length - 1 ? (
                <div className="agentic-skeleton-wrapper">
                  <div className="shimmer-effect skeleton-line primary"></div>
                  <div className="shimmer-effect skeleton-line secondary"></div>
                  <div className="shimmer-effect skeleton-line tertiary"></div>
                  <span className="agent-status-text">Consultando o acervo dehoniano...</span>
                </div>
              ) : (
                <ReactMarkdown>{m.content}</ReactMarkdown>
              )}
              {isStreaming && m.content !== '' && idx === messages.length - 1 && (
                <span className="typing-cursor"></span>
              )}
            </div>

            {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
              <div className="sources-section">
                <button 
                  className="view-citations-btn"
                  onClick={() => onViewCitations?.(m.id)}
                >
                  <Book size={14} />
                  <span>Ver {m.citations.length} Referências no Painel</span>
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
